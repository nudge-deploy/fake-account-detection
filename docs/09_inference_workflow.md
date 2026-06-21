<!--
Purpose: Explain the detailed lifecycle inference workflow from extraction to prediction.
Used by: Developers, reviewers, and documentation readers who need to understand backend inference behavior.
Main dependencies: frontend inference page, API routes, feature builder, inference engine, ABT, and trained model artifacts.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Detailed Inference Workflow

Dokumen ini menjelaskan cara kerja inference dari awal sampai hasil prediksi keluar. Fokusnya adalah alur `extraction`, `feature building`, `masking`, dan `prediction`, termasuk perbedaan `existing user` dan `new user`.

## Gambaran Besar

Alur inference saat ini berjalan seperti ini:

1. Frontend mengirim input stage atau journey.
2. Backend menerima request dan membaca `customer_type`, `uid`, serta payload.
3. Feature builder menyusun feature sesuai stage dan tipe user.
4. Engine memotong feature yang belum tersedia pada stage tertentu.
5. Model membaca vektor feature dan mengeluarkan probabilitas fraud.
6. Rule score, fraud type, dan reasons dihitung sebagai output penjelas.

## Sumber Data Yang Dipakai

### Existing User

Untuk existing user, inference bisa memanfaatkan:

- ABT user yang sudah tersedia
- detail user dari lookup backend
- feature historis yang sudah terbentuk di data training/ABT

### New User

Untuk new user, inference hanya memakai:

- data yang diinput pada stage saat itu
- pada registrasi awal memakai 10 feature registrasi yang memang tersedia
- feature lain baru muncul di stage berikutnya jika data tersedia
- fallback nol untuk feature yang belum ada

New user tidak dipaksa punya feature selengkap training.

## Tahap 1: Frontend Extraction

Frontend berada di [frontend/src/app/inference/page.tsx](</D:/magang/fraud detection/frontend/src/app/inference/page.tsx>).

Di sini user memilih:

- `customer_type` -> `new` atau `existing`
- `stage` -> `registration`, `login`, `checkout`, `transaction_completed`
- data input yang sesuai stage

Frontend lalu membangun payload:

- `phone_number`
- `email`
- `device_id`
- `device_fingerprint`
- `referral_code`
- `full_name`
- `date_of_birth`
- `is_email_verified`
- `is_phone_verified`
- `ip_address`
- `login_count_1h`
- `login_count_24h`
- `accounts_on_same_ip`
- `address_id`
- `payment_identifier`
- `order_amount`
- `voucher_used`
- `promo_discount`
- `minutes_since_registration`

### Extraction Existing User

Kalau existing user dipilih:

- frontend mengambil daftar user existing
- `uid` user dipilih dari dropdown
- detail user diambil dari endpoint `getUserDetails`
- nomor telepon login otomatis diisi
- device, address, dan IP connected juga dipakai sebagai referensi

### Extraction New User

Kalau new user dipilih:

- frontend memakai input manual dari form signup
- field yang tidak relevan tidak dipaksa ada
- beberapa ID boleh digenerate di frontend atau backend sebagai simulasi
- status verifikasi email dan phone ikut dikirim sebagai checkbox input

## Tahap 2: API Routing

Frontend memanggil proxy route:

- `/api/inference/registration`
- `/api/inference/login`
- `/api/inference/checkout`
- `/api/inference/transaction-completed`
- `/api/inference/journey`

Proxy route kemudian meneruskan request ke backend:

- `/api/inference/lifecycle`
- `/api/inference/journey`

## Tahap 3: Backend Request Parsing

Backend menerima body dengan schema:

- `stage`
- `customer_type`
- `uid`
- `payload`

Schema utamanya ada di [backend/app/schemas/request_response.py](</D:/magang/fraud detection/backend/app/schemas/request_response.py>).

Setelah request masuk:

1. `customer_type` dibaca sebagai `new` atau `existing`.
2. `uid` dipakai jika tersedia.
3. `payload` dibersihkan dari field `None`.
4. request diteruskan ke `ContinuousInferenceService`.

## Tahap 4: Feature Extraction

Logic feature extraction berada di [backend/app/inference/feature_builder.py](</D:/magang/fraud detection/backend/app/inference/feature_builder.py>).

### A. Identity Feature Extraction

Feature identitas yang dibentuk:

- `email_len`
- `email_num_ratio`
- `email_rand`
- `disp_email`
- `phone_score`
- `full_name_len` untuk registrasi new user

Sumbernya:

- email input
- phone number input

### B. Device Feature Extraction

Feature device:

- `uniq_dev`
- `max_acc_dev`
- `shared_device_count`

Sumbernya:

- `device_id`
- `device_fingerprint`
- lookup `user_devices.csv` dan `devices.csv`

### C. Referral Feature Extraction

Feature referral:

- `ref_cnt`
- `ref_ring`

Sumbernya:

- `referral_code`
- `referrals.csv`

### D. Login Feature Extraction

Feature login:

- `max_acc_ip`
- `login_v1h`
- `login_v2h`
- `login_v3h`
- `login_v4h`
- `login_v5h`
- `login_v6h`
- `login_v12h`
- `login_v18h`
- `login_v24h`
- `shared_ip_count`

Sumbernya:

- `ip_address`
- `login_count_1h`
- `login_count_24h`
- `accounts_on_same_ip`
- lookup ABT jika `uid` existing tersedia

### E. Checkout Feature Extraction

Feature checkout:

- `uniq_addr`
- `max_acc_addr`
- `shared_address_count`
- `uniq_pay`
- `max_acc_pay`
- `shared_payment_count`

Sumbernya:

- `address_id`
- `payment_identifier`
- lookup `user_addresses.csv`, `addresses.csv`, `user_payments.csv`, `payments.csv`

### F. Transaction Feature Extraction

Feature transaksi:

- `promo_ratio`
- `reg2txn_min`
- `newuser_voucher`
- `txn_f1m`
- `amt_f1m`
- `avg_amt1m`
- `promo_f1m`
- `voucher_f1m`
- dan pasangan bulan 2 sampai 6 untuk histori yang lebih lengkap

Sumbernya:

- `order_amount`
- `voucher_used`
- `promo_discount`
- `minutes_since_registration`

### G. New-User Registration Feature Extraction

Untuk stage registrasi new user, backend sekarang menyiapkan 10 feature awal berikut:

- `email_len`
- `email_num_ratio`
- `email_rand`
- `disp_email`
- `phone_score`
- `full_name_len`
- `is_email_verified`
- `is_phone_verified`
- `age_years`
- `registration_hour`

Feature ini dipakai sebagai basis model new-user sebelum stage login, checkout, dan transaksi menambahkan sinyal perilaku.

## Tahap 5: Existing vs New User Handling

### Existing User

Jika `customer_type = existing` dan `uid` ditemukan:

1. sistem lookup ABT user
2. feature penuh diambil sebagai baseline
3. model memakai feature historis yang sudah lengkap

Ini paling dekat dengan training.

### New User

Jika `customer_type = new`:

1. feature hanya dibangun dari input saat itu
2. feature yang tidak tersedia tidak dipaksa lengkap
3. graph feature tidak menjadi bagian aktif jalur registrasi new user jika relasi historis belum ada
4. nilai kosong tetap fallback ke `0` agar model bisa jalan
5. stage registrasi menggunakan model new-user; stage lanjutan dapat memakai model full sesuai availability data

## Tahap 6: Stage Masking

Stage masking dilakukan di [backend/app/inference/engine.py](</D:/magang/fraud detection/backend/app/inference/engine.py>).

Tujuannya:

- menjaga feature yang tidak boleh muncul pada stage awal tetap tersembunyi
- membuat inference bertahap sesuai lifecycle
- meniru kesiapan data yang terjadi secara natural

### Contoh Masking

| Stage | Yang Boleh Muncul |
|---|---|
| `registration` | identity, device, referral |
| `login` | registration + login |
| `checkout` | registration + login + checkout |
| `transaction_completed` | semua stage sebelumnya + transaksi |

Untuk new user, jalur ini tetap incremental.
Untuk existing user, baseline ABT bisa membuat feature lebih lengkap.

## Tahap 7: Build Feature Vector

Sesudah masking, engine membentuk vektor feature dengan urutan kolom dari `models/feature_columns.json`.

Hal yang dilakukan:

1. ambil semua kolom model
2. isi nilai dari staged feature row
3. ubah `bool` menjadi `int`
4. isi `NaN` dengan `0`

Hasilnya adalah matrix input untuk model ML.

## Tahap 8: Model Prediction

Model kemudian menjalankan:

- `predict_proba`
- `predict`

Output utamanya:

- `model_probability`
- `model_prediction`

## Tahap 9: Rule Score Dan Reasons

Selain ML prediction, engine juga menghitung:

- `rule_score`
- `risk_category`
- `is_suspicious`
- `is_fraud`
- `primary_fraud_type`
- `suspected_fraud_types`
- `reasons`

Ini ada di:

- [backend/app/inference/scoring.py](</D:/magang/fraud detection/backend/app/inference/scoring.py>)
- [backend/app/inference/fraud_classifier.py](</D:/magang/fraud detection/backend/app/inference/fraud_classifier.py>)
- [backend/app/inference/reasons.py](</D:/magang/fraud detection/backend/app/inference/reasons.py>)

## Journey Mode

Kalau user menekan `Full Journey`:

1. frontend mengirim payload lengkap yang tersedia
2. backend menjalankan inference untuk tiap stage
3. hasil dikembalikan sebagai daftar stage
4. UI menampilkan perubahan skor per tahap

## Ringkasan Perbedaan Flow

| Aspek | Existing User | New User |
|---|---|---|
| Data awal | uid + ABT | input skenario |
| Feature | relatif lengkap | hanya yang ada di input |
| Graph | bisa tersedia | tidak dipaksakan |
| Histori | bisa dipakai | tidak diasumsikan ada |
| Output | paling dekat training | parsial dan stage-based |

## Kesimpulan

Inference project ini bekerja dengan pendekatan staged feature extraction lalu model prediction. Existing user memakai baseline data yang lebih lengkap, sedangkan new user hanya memakai data yang benar-benar tersedia pada saat stage itu berjalan. Dengan cara ini, inference tetap realistis, bertahap, dan tidak memalsukan feature historis yang belum ada.

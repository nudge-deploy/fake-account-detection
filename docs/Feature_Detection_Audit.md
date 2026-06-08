<!--
Purpose: Audit whether existing features can detect each configured fraud scenario.
Used by: Developers, reviewers, and model maintainers validating feature-to-scenario coverage.
Main dependencies: data/abt/fake_account_abt.csv, models/feature_columns.json, models/model_metrics.json, models/fake_account_model.pkl.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Feature Detection Audit

Dokumen ini mencatat apakah fitur yang ada sudah benar-benar menangkap skenario fraud yang dibuat di data generator dan dipakai di ABT/model.

## Ringkasan Jawaban

Secara ranking model, semua skenario fraud sudah bisa dibedakan dari normal dengan sangat baik. AUC model per skenario vs normal berada di kisaran `0.992` sampai `1.000`.

Namun pada threshold default `0.50`, tidak semua skenario tertangkap sama kuat. `shared_payment_abuse` dan `shared_address_abuse` paling kuat. `shared_device_abuse`, `voucher_farming`, dan `referral_abuse` masih punya recall praktis yang lebih rendah pada threshold default.

Artinya fitur sudah punya sinyal, tetapi threshold dan bobot model masih perlu dipakai dengan hati-hati untuk dashboard/API operasional.

## Distribusi Skenario

ABT final berisi `10,000` user dan `69` kolom.

| `ftype` | Jumlah | Fraud |
|---|---:|---:|
| `normal` | 7,000 | 0 |
| `shared_device_abuse` | 600 | 1 |
| `voucher_farming` | 600 | 1 |
| `shared_address_abuse` | 600 | 1 |
| `shared_payment_abuse` | 600 | 1 |
| `referral_abuse` | 600 | 1 |

## Performa Model Global

Champion model terbaru adalah `XGBoost`.

| Metric | Nilai |
|---|---:|
| Accuracy | 0.9673 |
| Precision | 0.9785 |
| Recall | 0.9111 |
| F1-score | 0.9436 |
| ROC-AUC | 0.9957 |

Confusion matrix test split:

| | Pred normal | Pred fraud |
|---|---:|---:|
| Actual normal | 2,082 | 18 |
| Actual fraud | 80 | 820 |

## Coverage per Skenario

### Model Ranking

AUC per skenario vs normal memakai probabilitas model:

| Skenario | Model AUC vs Normal | Interpretasi |
|---|---:|---|
| `shared_payment_abuse` | 1.000 | Sangat kuat |
| `shared_address_abuse` | 0.998 | Sangat kuat |
| `referral_abuse` | 0.994 | Ranking kuat |
| `voucher_farming` | 0.993 | Ranking kuat |
| `shared_device_abuse` | 0.992 | Ranking kuat |

### Recall Praktis pada Beberapa Threshold

Nilai di bawah adalah persentase user pada tiap skenario yang diprediksi fraud oleh model.

| Threshold | Normal false positive | Referral | Address | Device | Payment | Voucher |
|---|---:|---:|---:|---:|---:|---:|
| 0.30 | 0.7% | 85.5% | 92.3% | 81.3% | 100.0% | 75.3% |
| 0.40 | 0.2% | 81.3% | 90.0% | 77.3% | 97.7% | 67.8% |
| 0.50 | 0.0% | 74.8% | 84.7% | 64.7% | 93.2% | 59.5% |
| 0.60 | 0.0% | 65.8% | 78.3% | 48.3% | 89.5% | 49.5% |

Kesimpulan threshold:

- Threshold `0.50` sangat ketat dan menjaga false positive normal hampir nol.
- Threshold `0.30` menangkap lebih banyak fraud scenario dengan false positive normal masih rendah pada data ini.
- Untuk dashboard/API, threshold bisa dipisah dari training: model tetap sama, tetapi keputusan operasional bisa memakai risk band atau threshold lebih rendah.

## Audit Sinyal Fitur per Skenario

## Audit 64 Fitur Model

Audit ini memakai 64 fitur di `models/feature_columns.json`. Setiap fitur dicek terhadap tiap skenario fraud dibanding `normal` memakai:

- AUC univariate fitur vs normal.
- Perbedaan rata-rata fitur fraud scenario vs normal.
- Kesesuaian makna fitur terhadap skenario fraud.

Hasil ringkas:

| Kategori | Jumlah | Arti |
|---|---:|---|
| Direct scenario features | 18 | Fitur yang langsung menjelaskan skenario fraud tertentu. |
| Supporting/generic fraud features | 9 | Fitur yang membantu model, tetapi tidak spesifik ke satu skenario. |
| Weak/context features | 37 | Fitur yang lebih lemah secara individual atau hanya jadi konteks model. |

### Direct Scenario Features

Fitur berikut paling benar-benar menjelaskan skenario fraud yang dibuat:

| Fitur | Skenario yang Dianalisis | Alasan |
|---|---|---|
| `max_acc_pay` | `shared_payment_abuse` | Banyak account memakai payment yang sama. |
| `shared_payment_count` | `shared_payment_abuse` | Menghitung shared payment entity. |
| `max_acc_addr` | `shared_address_abuse` | Banyak account memakai address yang sama. |
| `shared_address_count` | `shared_address_abuse` | Menghitung shared address entity. |
| `max_acc_dev` | `shared_device_abuse` | Banyak account memakai device yang sama, tetapi sinyalnya lebih lemah dari payment/address. |
| `shared_device_count` | `shared_device_abuse` | Menghitung shared device entity, tetapi normal juga cukup sering share device. |
| `email_num_ratio` | `voucher_farming` | Voucher farming punya email lebih numerik/random. |
| `disp_email` | `voucher_farming` | Banyak account voucher farming memakai disposable email. |
| `newuser_voucher` | `voucher_farming` | Pemakaian voucher user baru jauh lebih tinggi. |
| `promo_ratio` | `voucher_farming` | Rasio transaksi promo lebih tinggi, meski sinyal individual tidak sekuat `newuser_voucher`. |
| `promo_f4m` | `voucher_farming` | Promo amount window panjang mulai naik. |
| `promo_f5m` | `voucher_farming` | Promo amount window panjang naik. |
| `promo_f6m` | `voucher_farming` | Promo amount window panjang paling kuat di kelompok promo amount. |
| `reg2txn_min` | `voucher_farming` | Pola waktu registrasi ke transaksi pertama berbeda. |
| `ref_cnt` | `referral_abuse` | Jumlah referral keluar naik. |
| `ref_ring` | `referral_abuse` | Cycle/ring referral terdeteksi. |
| `degree` | Fraud ring graph | User terhubung ke lebih banyak user/entity dalam graph projection. |
| `shared_ent` | Fraud ring graph | Total shared entity connection naik. |

### Supporting / Generic Fraud Features

Fitur berikut membantu model membaca pola fraud umum, terutama graph/login/IP behavior, tetapi tidak selalu menjelaskan satu skenario secara spesifik:

| Fitur | Dipakai Untuk | Catatan |
|---|---|---|
| `shared_ip_count` | Network/ring behavior | Sangat dominan di model, tetapi terlalu generic jika dipakai sendirian untuk menjelaskan skenario tertentu. |
| `max_acc_ip` | Network/IP sharing | Kuat untuk pola IP abnormal, tetapi arah sinyal bisa berbeda antar skenario. |
| `login_v5h` | Login burst/frequency | Mulai punya sinyal pada skenario graph tertentu. |
| `login_v6h` | Login burst/frequency | Supporting signal. |
| `login_v12h` | Login burst/frequency | Supporting signal lebih jelas. |
| `login_v18h` | Login burst/frequency | Supporting signal kuat. |
| `login_v24h` | Login daily frequency | Salah satu fitur model paling penting. |
| `cluster` | Fraud ring graph | Mirip `degree`, membantu membaca ukuran cluster sekitar user. |
| `comp_size` | Fraud ring graph | Masuk top model importance, tetapi secara univariate kurang spesifik karena component besar hampir menyeluruh. |

### Weak / Context Features

Fitur berikut tetap masuk 64 fitur model, tetapi secara individual tidak kuat untuk membedakan skenario tertentu dari normal pada data saat ini:

```text
email_len, email_rand, phone_score,
uniq_dev, uniq_addr, uniq_pay,
txn_f1m, amt_f1m, avg_amt1m, promo_f1m, voucher_f1m,
txn_f2m, amt_f2m, avg_amt2m, promo_f2m, voucher_f2m,
txn_f3m, amt_f3m, avg_amt3m, promo_f3m, voucher_f3m,
txn_f4m, amt_f4m, avg_amt4m, voucher_f4m,
txn_f5m, amt_f5m, avg_amt5m, voucher_f5m,
txn_f6m, amt_f6m, avg_amt6m, voucher_f6m,
login_v1h, login_v2h, login_v3h, login_v4h
```

Catatan:

- `login_v1h` termasuk top model importance, tetapi sebagai fitur tunggal tidak cukup spesifik untuk satu skenario. Ia berguna dalam kombinasi dengan IP/graph features.
- Fitur transaksi bulanan banyak yang menjadi konteks spending behavior, bukan detector utama fraud scenario.
- Fitur `uniq_*` lebih menjelaskan variasi jumlah entity user sendiri, bukan shared abuse langsung. Detector shared abuse yang lebih kuat adalah `max_acc_*` dan `shared_*_count`.

### `shared_payment_abuse`

Fitur yang paling jelas:

| Fitur | Normal Mean | Fraud Mean | Catatan |
|---|---:|---:|---|
| `max_acc_pay` | 1.400 | 5.500 | Sangat kuat |
| `shared_payment_count` | 0.400 | 4.500 | Sangat kuat |

Status: kuat. Skenario ini paling mudah dideteksi.

### `shared_address_abuse`

Fitur yang paling jelas:

| Fitur | Normal Mean | Fraud Mean | Catatan |
|---|---:|---:|---|
| `max_acc_addr` | 3.371 | 5.000 | Ada sinyal |
| `shared_address_count` | 2.371 | 4.000 | Ada sinyal |
| `degree` | 147.050 | 438.002 | Sinyal graph kuat |

Status: kuat, tetapi normal juga punya sharing address cukup tinggi sehingga fitur address tidak sebersih payment.

### `shared_device_abuse`

Fitur yang paling jelas:

| Fitur | Normal Mean | Fraud Mean | Catatan |
|---|---:|---:|---|
| `max_acc_dev` | 3.038 | 3.652 | Sinyal lemah-menengah |
| `shared_device_count` | 2.293 | 2.652 | Sinyal lemah |
| `degree` | 147.050 | 188.953 | Sinyal graph ada, tapi tidak besar |

Status: bisa dideteksi oleh model ranking, tetapi threshold default kurang agresif. Penyebab utamanya adalah normal data juga cukup banyak berbagi device.

### `voucher_farming`

Fitur yang paling jelas:

| Fitur | Normal Mean | Fraud Mean | Catatan |
|---|---:|---:|---|
| `disp_email` | 0.111 | 0.492 | Sinyal cukup kuat |
| `newuser_voucher` | 1.053 | 2.997 | Sinyal cukup kuat |
| `promo_ratio` | 0.555 | 0.696 | Sinyal menengah |

Status: bisa dibedakan, tetapi threshold default `0.50` hanya menangkap sekitar `59.5%`. Fitur voucher ada, tetapi bobot model lebih dominan ke IP/login graph.

### `referral_abuse`

Fitur yang paling jelas:

| Fitur | Normal Mean | Fraud Mean | Catatan |
|---|---:|---:|---|
| `ref_cnt` | 0.143 | 0.998 | Sinyal ada |
| `ref_ring` | 0.000 | 2.216 | Sinyal ada |
| `degree` | 147.050 | 288.112 | Sinyal graph ikut naik |

Status: ranking model kuat, tetapi threshold default `0.50` menangkap sekitar `74.8%`. Fitur referral masuk model, tetapi importance-nya masih kecil dibanding IP/login.

## Top Model Importance

Top feature importance champion model:

| Fitur | Importance |
|---|---:|
| `shared_ip_count` | 0.2480 |
| `login_v24h` | 0.2094 |
| `login_v1h` | 0.2050 |
| `max_acc_ip` | 0.1208 |
| `comp_size` | 0.0390 |
| `shared_payment_count` | 0.0276 |
| `reg2txn_min` | 0.0218 |
| `uniq_dev` | 0.0161 |
| `txn_f6m` | 0.0114 |
| `shared_address_count` | 0.0094 |
| `ref_cnt` | 0.0059 |
| `shared_device_count` | 0.0050 |
| `newuser_voucher` | 0.0046 |

Catatan penting:

- Model sangat mengandalkan IP/login behavior.
- Ini bagus untuk fraud network umum.
- Tetapi untuk menjelaskan skenario spesifik, dashboard/API sebaiknya tetap menampilkan fitur skenario seperti `max_acc_pay`, `shared_payment_count`, `newuser_voucher`, `ref_cnt`, dan `ref_ring`.

## Kesimpulan

Fitur yang ada sudah mencakup seluruh skenario yang dibuat:

| Skenario | Fitur Utama | Status |
|---|---|---|
| Shared device abuse | `max_acc_dev`, `shared_device_count`, `degree` | Ada, tapi sinyal relatif lemah |
| Shared address abuse | `max_acc_addr`, `shared_address_count`, `degree` | Kuat |
| Shared payment abuse | `max_acc_pay`, `shared_payment_count` | Sangat kuat |
| Voucher farming | `disp_email`, `newuser_voucher`, `promo_ratio` | Ada, threshold perlu hati-hati |
| Referral abuse | `ref_cnt`, `ref_ring` | Ada, threshold perlu hati-hati |
| Bot/login/network abuse umum | `login_v1h`, `login_v24h`, `max_acc_ip`, `shared_ip_count` | Sangat dominan |

## Rekomendasi Tanpa Menambah Kolom

Tidak perlu menambah kolom/feature baru untuk saat ini. Perbaikan yang bisa dilakukan tanpa mengubah kontrak fitur:

1. Gunakan threshold operasional `0.30` sampai `0.40` untuk fraud review queue, bukan hanya `0.50`.
2. Pertahankan model probability sebagai ranking score, lalu gunakan `risk_cat` untuk kategori tampilan.
3. Untuk explainability frontend, tampilkan fitur skenario spesifik:
   - payment: `max_acc_pay`, `shared_payment_count`
   - address: `max_acc_addr`, `shared_address_count`
   - device: `max_acc_dev`, `shared_device_count`
   - voucher: `disp_email`, `newuser_voucher`, `promo_ratio`
   - referral: `ref_cnt`, `ref_ring`
   - login/IP: `login_v1h`, `login_v24h`, `max_acc_ip`, `shared_ip_count`
4. Evaluasi ulang threshold pada test split atau validation split khusus sebelum dipakai sebagai keputusan final.
5. Jika ingin meningkatkan `shared_device_abuse` tanpa menambah fitur, perbaiki generator agar normal user tidak terlalu sering berbagi device, lalu regenerate ABT dan retrain.

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


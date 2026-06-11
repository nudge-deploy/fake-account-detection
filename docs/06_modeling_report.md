<!--
Purpose: Summarize the current training setup, evaluation, and deployment split for new-user and existing-user models.
Used by: Developers, reviewers, and analysts checking model quality and artifact lineage.
Main dependencies: scripts/generate_new_user_training_data.py, scripts/train_new_user_model.py, models/*, data/abt/fake_account_abt.csv.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# 06. Modeling Report

Dokumen ini merangkum kondisi modeling project saat ini. Fokusnya bukan lagi satu model besar untuk semua skenario, tetapi dua jalur inference yang dipisah agar lebih realistis:

1. **New user model** untuk registrasi awal.
2. **Existing user model** untuk user yang sudah punya histori dan feature lengkap.

## Ringkasan Artifact

| Artifact | Fungsi |
|---|---|
| `models/fake_account_model_new_user.pkl` | Model khusus registrasi new user. |
| `models/model_metrics_new_user.json` | Metrik evaluasi new-user model. |
| `models/feature_columns_new_user.json` | Urutan 10 feature registrasi new user. |
| `models/fake_account_model.pkl` | Model legacy / full feature untuk jalur existing user dan stage lanjutan. |
| `models/feature_columns.json` | Urutan 64 feature model full. |

## New-User Model

### Tujuan

Model ini dibuat untuk skenario registrasi user baru ketika feature perilaku masih sangat tipis. Model tidak dipaksa membaca 64 feature full karena data tersebut memang belum tersedia di tahap awal.

### Feature Input

Model new-user menggunakan 10 feature registrasi:

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

### Model yang Dipakai

Saat ini champion new-user adalah **Logistic Regression** dalam pipeline dengan standard scaling.

### Hasil Evaluasi Terakhir

| Metrik | Nilai |
|---|---:|
| Accuracy | 0.9867 |
| Precision | 0.9760 |
| Recall | 0.9980 |
| F1 Score | 0.9869 |
| ROC AUC | 0.9996 |
| Best threshold evaluasi | 0.55 |

### Confusion Matrix

| | Pred Normal | Pred Fraud |
|---|---:|---:|
| Actual Normal | 479 | 12 |
| Actual Fraud | 1 | 489 |

### Labeling Data Latih

New-user synthetic training set saat ini menandai fraud berdasarkan dua pola utama:

- disposable email domain
- suspicious phone pattern

Data latihnya sudah dibuat seimbang agar model tidak bias ke satu kelas saja.

## Existing-User / Full Model

Model full masih dipakai untuk jalur existing user dan stage lanjutan. Model ini membaca feature yang lebih lengkap dari ABT final, termasuk graph aggregate feature, login behavior, transaksi, referral, device sharing, address sharing, payment sharing, dan IP sharing.

## Kenapa Dipisah

Pemecahan model dilakukan karena konteks data berbeda:

- **New user** hanya punya data registrasi awal.
- **Existing user** sudah punya histori login, transaksi, graph, dan relasi entitas.

Kalau new user dipaksa masuk ke jalur full-feature, hasilnya mudah bias dan sering terlalu mencurigakan walau sinyalnya masih minim.

## Catatan Praktis

- Registrasi new user sekarang dirancang untuk fokus pada pola yang benar-benar tersedia saat signup.
- Stage berikutnya boleh menambah sinyal perilaku secara bertahap.
- Output inference tetap dikembalikan sebagai probabilitas fraud, label fraud / bukan fraud, dan alasan utama.


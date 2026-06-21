<!--
Purpose: Summarize model training setup, evaluation results, and artifact locations for both new-user and existing-user models.
Used by: Developers, reviewers, and analysts checking model quality and artifact lineage.
Main dependencies: scripts/train_model.py, scripts/train_new_user_model.py, models/existing_customer/*, models/new_customer/*
-->

# 07. Modeling Report

Sistem menggunakan **dua model terpisah** agar inference realistis di setiap titik lifecycle:

1. **New Customer Model** — hanya fitur registrasi (10 fitur), digunakan saat user baru mendaftar.
2. **Existing Customer Model** — fitur lengkap dari ABT (64 fitur), digunakan untuk user yang sudah punya histori.

---

## Artifact Model

| Artifact | Lokasi |
|----------|--------|
| Existing customer model | `models/existing_customer/model.pkl` |
| Existing customer features | `models/existing_customer/feature_columns.json` |
| Existing customer metrics | `models/existing_customer/model_metrics.json` |
| New customer model | `models/new_customer/model.pkl` |
| New customer features | `models/new_customer/feature_columns.json` |
| New customer metrics | `models/new_customer/metrics.json` |

---

## 1. Existing Customer Model

### Input

- **Data:** `data/abt/fake_account_abt.csv`
- **Fitur:** 64 fitur behavioral (device, address, payment, IP, login, transaksi, graph, referral)
- **Label:** `fraud` (0 = normal, 1 = fraud)
- **Split:** 70% train / 30% test (stratified, `random_state=42`)

### Pipeline

```
Raw Features (64) → StandardScaler → Classifier
```

### Hyperparameter Tuning (GridSearchCV, 5-Fold StratifiedKFold)

| Model | Best Params | CV F1 |
|-------|-------------|-------|
| Logistic Regression | C=1.0, penalty=l2 | 0.9307 |
| Random Forest | max_depth=5, min_samples_leaf=5, n_estimators=50 | 0.9131 |
| **XGBoost** | lr=0.05, max_depth=3, min_child_weight=5, subsample=0.7 | **0.9416** |

### Hasil Evaluasi — Champion: XGBoost

| Metrik | Nilai |
|--------|------:|
| Accuracy | 96.83% |
| Precision | 98.32% |
| Recall | 91.00% |
| **F1-Score** | **94.52%** |
| ROC-AUC | 99.62% |

### Top 5 Fitur Penting (XGBoost Feature Importance)

| Fitur | Importance |
|-------|------------|
| `login_v1h` | 0.1622 |
| `login_v24h` | 0.0959 |
| `shared_ip_count` | 0.0718 |
| `max_acc_ip` | 0.0670 |
| `shared_payment_count` | 0.0371 |

### Leakage Prevention

Fitur cross-user (`max_acc_dev`, `max_acc_ip`, dll) dihitung ulang **hanya dari training set** sebelum evaluasi test set, untuk mencegah data leakage.

---

## 2. New Customer Model

### Input

- **Data:** `data/processed/new_user_training_data.csv`
- **Fitur:** 10 fitur registrasi saja
- **Split:** 70/30 stratified

### 10 Fitur Registrasi

| Fitur | Deskripsi |
|-------|-----------|
| `email_len` | Panjang alamat email |
| `email_num_ratio` | Rasio digit dalam nama email |
| `email_rand` | Shannon entropy nama email |
| `disp_email` | Email dari domain disposable |
| `phone_score` | Skor pola nomor HP |
| `full_name_len` | Panjang nama lengkap |
| `is_email_verified` | Status verifikasi email |
| `is_phone_verified` | Status verifikasi HP |
| `age_years` | Usia dari tanggal lahir |
| `registration_hour` | Jam pendaftaran |

### Model: Logistic Regression (dengan threshold optimization)

```python
# Cari threshold F1 terbaik dari 17 kandidat (0.1 – 0.9)
best_threshold = argmax_f1(thresholds)
```

### Hasil Evaluasi

| Metrik | Nilai |
|--------|------:|
| **F1-Score** | **98.69%** |
| ROC-AUC | 99.96% |

---

## 3. Kenapa Dipisah

| Aspek | New Customer | Existing Customer |
|-------|-------------|-------------------|
| Data yang tersedia | Hanya data registrasi | Histori penuh (login, transaksi, graph) |
| Fitur | 10 | 64 |
| Model | Logistic Regression | XGBoost |
| Threshold prediksi | 0.80 (lebih ketat) | 0.50 |

Memaksa new user masuk ke model 64 fitur akan menghasilkan **false positive tinggi** karena fitur behavioral semuanya nol — model tidak bisa membedakan new user normal dengan fraud.

---

## 4. Threshold Prediksi per Stage

| Stage | Customer Type | Threshold |
|-------|--------------|-----------|
| Registration | New | 0.80 |
| Login, Checkout, Txn | New | 0.65 |
| Semua stage | Existing | 0.50 |

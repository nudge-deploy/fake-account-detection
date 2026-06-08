<!--
Purpose: Define ABT feature names, formulas, and business interpretation.
Used by: Model reviewers, backend developers, and feature lineage audits.
Main dependencies: scripts/build_abt.py, data/abt/fake_account_abt.csv, models/feature_columns.json.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Fraud Detection Feature Engineering Documentation

## 1. Overview

Dokumen ini menjelaskan seluruh fitur yang dihasilkan oleh modul `build_abt.py` dan digunakan sebagai Analytics Base Table (ABT) untuk Fraud Detection, Multi-Account Detection, Voucher Abuse Detection, Referral Abuse Detection, dan Fraud Ring Detection.

Kontrak final ABT:
- `fake_account_abt.csv` berisi 10.000 baris dan 69 kolom total.
- 64 kolom menjadi input model dan disimpan urutannya di `models/feature_columns.json`.
- 5 kolom tidak masuk model karena merupakan metadata/label: `uid`, `fraud`, `ftype`, `risk_score`, `risk_cat`.
- Fitur graph aggregate (`degree`, `comp_size`, `cluster`, `shared_ent`, dan shared counters) sudah menjadi bagian dari ABT final.

---

# 2. Identity Features

| Nama Fitur | Rumus Kode (Pandas / SQL Logic) | Definisi Teknis | Interpretasi Akhir (Bisnis) |
|------------|---------------------------------|-----------------|-----------------------------|
| email_len | len(email) | Panjang email | Email tidak wajar dapat mengindikasikan akun sintetis |
| email_num_ratio | digit_count / username_length | Rasio angka pada username email | Tinggi mengindikasikan email hasil generate otomatis |
| email_rand | calc_entropy(username) | Entropy karakter email | Semakin tinggi semakin acak |
| disp_email | domain in disposable_list | Apakah email disposable | Akun sekali pakai |
| phone_score | calc_phone_pattern_score(phone) | Skor pola nomor telepon | Tinggi menunjukkan pola tidak natural |

---

# 3. Device Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| uniq_dev | nunique(device_id) | Jumlah device unik | Banyak device menunjukkan perpindahan perangkat |
| max_acc_dev | max(users_per_device) | Maks akun pada device yang sama | Indikasi multi-account |

---

# 4. Address Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| uniq_addr | nunique(address_id) | Jumlah alamat unik | Pola pengiriman tidak normal |
| max_acc_addr | max(users_in_address) | Maks akun pada alamat yang sama | Shared address abuse |

---

# 5. Payment Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| uniq_pay | nunique(payment_id) | Jumlah payment unik | Akun tidak stabil |
| max_acc_pay | max(users_on_payment) | Maks akun pada payment sama | Shared payment abuse |

---

# 6. Transaction Features

## Core Transaction

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| promo_ratio | voucher_usage_count / total_transactions | Rasio transaksi promo | Promo farming |
| reg2txn_min | first_txn - registration_date | Menit dari registrasi ke transaksi pertama | Akun dibuat untuk promo |
| newuser_voucher | sum(is_new_user_promo) | Penggunaan voucher user baru | Abuse promo user baru |

## Monthly Transaction Frequency

txn_f1m sampai txn_f6m

- txn_f1m = transaksi ≤ 30 hari
- txn_f2m = transaksi ≤ 60 hari
- txn_f3m = transaksi ≤ 90 hari
- txn_f4m = transaksi ≤ 120 hari
- txn_f5m = transaksi ≤ 150 hari
- txn_f6m = transaksi ≤ 180 hari

Interpretasi:
Semakin tinggi menunjukkan aktivitas transaksi semakin intens.

## Monthly Transaction Amount

amt_f1m sampai amt_f6m

Rumus:
sum(order_amount)

Interpretasi:
Total nominal transaksi pada window waktu tertentu.

## Monthly Average Amount

avg_amt1m sampai avg_amt6m

Rumus:
mean(order_amount)

Interpretasi:
Rata-rata nilai transaksi user.

## Promo Usage

promo_f1m sampai promo_f6m

Rumus:
sum(promo_discount)

Interpretasi:
Total diskon promo yang digunakan.

## Voucher Usage

voucher_f1m sampai voucher_f6m

Rumus:
count(voucher_id)

Interpretasi:
Frekuensi penggunaan voucher.

---

# 7. Login Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| max_acc_ip | max(users_on_ip) | Maks akun pada IP sama | Fraud ring indicator |
| login_v1h | Maks login dari 00:00 sampai 01:00 pada hari tersibuk user | Daily login frequency bucket 1h | Burst login setelah tengah malam |
| login_v2h | Maks login dari 00:00 sampai 02:00 pada hari tersibuk user | Daily login frequency bucket 2h | Burst login setelah tengah malam |
| login_v3h | Maks login dari 00:00 sampai 03:00 pada hari tersibuk user | Daily login frequency bucket 3h | Burst login setelah tengah malam |
| login_v4h | Maks login dari 00:00 sampai 04:00 pada hari tersibuk user | Daily login frequency bucket 4h | Burst login setelah tengah malam |
| login_v5h | Maks login dari 00:00 sampai 05:00 pada hari tersibuk user | Daily login frequency bucket 5h | Burst login setelah tengah malam |
| login_v6h | Maks login dari 00:00 sampai 06:00 pada hari tersibuk user | Daily login frequency bucket 6h | Burst login setelah tengah malam |
| login_v12h | Maks login dari 00:00 sampai 12:00 pada hari tersibuk user | Daily login frequency bucket 12h | Aktivitas tinggi paruh hari |
| login_v18h | Maks login dari 00:00 sampai 18:00 pada hari tersibuk user | Daily login frequency bucket 18h | Aktivitas tinggi sebelum malam |
| login_v24h | Maks total login harian user | Daily login frequency bucket 24h | Intensitas login harian |

---

# 8. Referral Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| ref_cnt | count(referral_id) | Jumlah referral dibuat | Aktivitas referral |
| ref_ring | cycle_size atau descendants/2 | Keterlibatan dalam referral network | Referral ring abuse |

---

# 9. Graph Features (Fraud Ring)

| Nama Fitur | Rumus / Library | Definisi Teknis | Interpretasi Bisnis |
|------------|-----------------|-----------------|---------------------|
| graph_degree | `user_graph.degree()` | Jumlah koneksi langsung ke user lain karena berbagi entitas | Indikator awal keterlibatan dalam sindikat |
| connected_component_size | `len(component)` | Ukuran partisi jaringan tempat user berada | Mendeteksi *Fraud Ring* berskala masif |
| graph_cluster_size | `len(ego_graph)` | Ukuran lingkaran pertemanan terdekat user | Mendeteksi kelompok fraud yang sangat terpusat |
| shared_entity_count | *Aggregate* | Total seluruh hubungan berbagi entitas | Bukti tak terbantahkan manipulasi multi-akun |
| shared_device_count | *Bipartite Edge* | Koneksi antar user akibat berbagi *device* | Indikasi *Device Farming / Emulator* |
| shared_address_count | *Bipartite Edge* | Koneksi antar user akibat berbagi alamat | Sindikat pengiriman barang fiktif |
| shared_payment_count | *Bipartite Edge* | Koneksi antar user akibat metode bayar sama | Indikasi pencucian uang / *voucher farming* |
| shared_ip_count | *Bipartite Edge* | Koneksi antar user akibat IP yang sama | Serangan *bot* massal dari satu jaringan WiFi/VPN |

---

# 10. Rule Based Risk Scoring

## Scoring Rules

| Kondisi | Skor |
|----------|------|
| max_acc_dev > 5 | +40 |
| max_acc_dev > 2 | +15 |
| max_acc_addr > 5 | +20 |
| max_acc_ip > 5 | +15 |
| login_v1h > 10 | +40 |
| promo_ratio > 0.8 | +15 |
| reg2txn_min < 30 | +15 |
| newuser_voucher > 2 | +10 |

Maximum score = 100

## Risk Category

| Score | Category |
|---------|---------|
| 0 - 30 | Low |
| 31 - 60 | Medium |
| > 60 | High |

---

# 11. Output Dataset

Output file:

data/abt/fake_account_abt.csv

Total Feature:
63 Feature

Dataset ini akan digabung dengan Graph Features untuk membentuk Final Training Dataset Fraud Graph Ring Detection.

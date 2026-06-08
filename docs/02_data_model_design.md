<!--
Purpose: Describe the relational data model and final ABT contract.
Used by: Developers, reviewers, and Supabase schema maintainers.
Main dependencies: database_schema.sql, generated raw CSVs, fake_account_abt.csv.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Data Model Design

## 1. Entity Relationship Diagram (ERD) Deskripsi

Model data ini dirancang dengan **14 tabel (13 tabel raw data + 1 Analytics Base Table)** yang menyederhanakan dan mengabstraksi *User Journey* utama dari aplikasi retail mobile (seperti Alfagift) ke dalam struktur relasional. Hubungan antar tabel adalah sebagai berikut:

- **users**: Pusat dari sistem. Menggantikan data profil registrasi (nama, email, nomor HP yang diverifikasi OTP).
- **devices**: Perangkat fisik pengguna. Menyimpan metadata perangkat dan memetakan *device fingerprint*. Relasi `M:N` dengan `users` melalui tabel `user_devices`.
- **addresses**: Alamat fisik pengiriman (Delivery). Mencatat koordinat dan label alamat. Relasi `M:N` dengan `users` melalui tabel `user_addresses`.
- **payments**: Metode pembayaran digital (Transfer Bank, E-Wallet, CC, dll). Relasi `M:N` dengan `users` melalui tabel `user_payments`.
- **vouchers**: Kupon diskon dan promo (seperti promo pengguna baru atau gratis ongkir). Relasi `1:N` ke `transactions`.
- **transactions**: Transaksi pembelian yang mencakup status checkout, penggunaan voucher, dan perhitungan total belanja. Relasi `N:1` ke `users`, `vouchers`, `payments`, dan `addresses`.
- **transaction_items**: Rincian produk (groceries, electronics) di dalam keranjang belanja. Relasi `N:1` ke `transactions`.
- **login_sessions**: Riwayat aktivitas login yang merekam IP, geo-location, durasi sesi, dan `login_persona`. Relasi `N:1` ke `users` dan `devices`.
- **referrals**: Merepresentasikan program loyalty/referral. Mencatat akun yang mengundang dan diundang.
- **fraud_labels**: Ground truth label untuk fraud yang mencatat skenario kecurangan. Relasi `1:1` ke `users`.
- **fake_account_abt**: Analytics Base Table. Hasil ekstraksi fitur (*Feature Engineering*) dari seluruh tabel di atas yang siap diproses oleh model Machine Learning.

## 2. Fraud Pattern Mapping (Pemetaan Pola Fraud)

Bagaimana pola fraud direpresentasikan di dalam skema database:

| Fraud Pattern | Tabel yang Terlibat | Indikasi Data |
|---|---|---|
| **Shared Device Abuse** | `user_devices` | Satu `device_id` direferensikan oleh banyak (misal >5) `user_id` berbeda. |
| **Shared Payment Abuse** | `user_payments`, `transactions` | Banyak transaksi dari `user_id` berbeda menggunakan `payment_id` yang sama. |
| **Shared Address Abuse** | `user_addresses`, `addresses` | Penggunaan `address_id` fisik yang persis sama oleh puluhan akun berbeda secara serentak. |
| **Voucher Farming** | `transactions`, `vouchers` | `user_id` memiliki riwayat transaksi yang mayoritas memakai `voucher_id` tipe "new_user_promo", lalu tidak pernah bertransaksi lagi. |
| **Referral Rings** | `referrals` | Satu `referrer_user_id` mengundang banyak `referred_user_id`, dan `referred_user_id` tersebut segera melakukan klaim reward atau langsung tidak aktif (churn). |

## 3. Analytics Base Table (ABT)

Tabel `fake_account_abt` adalah hasil agregasi (Feature Engineering) dari semua tabel raw ditambah `user_graph_features.csv`. Setiap baris mewakili satu `user_id` dan berisi 69 kolom total: 64 fitur model dan 5 metadata/label.

- **Identity Features:** Panjang email, rasio numerik pada email, dll.
- **Device Features:** Jumlah device unik, jumlah pengguna maksimum per device, dll.
- **Transaction Features:** Rata-rata transaksi, rasio penggunaan promo, dll.
- **Login Features:** Frekuensi login harian sejak jam `00:00` (`login_v1h` sampai `login_v24h`), dll.
- **Graph/Network Features:** `degree`, `comp_size`, `cluster`, `shared_ent`, dan counter shared entity per jenis.
- **Metadata/Label:** `uid`, `fraud`, `ftype`, `risk_score`, `risk_cat`.

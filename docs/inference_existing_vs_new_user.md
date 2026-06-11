<!--
Purpose: Document the intended inference flow split between existing users and new users.
Used by: Developers, reviewers, and documentation readers who need to understand lifecycle inference behavior.
Main dependencies: backend inference engine, feature builder, ABT, and training feature schema.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Inference Flow: Existing User vs New User

Dokumen ini menjelaskan pemisahan inference antara `existing user` dan `new user` agar selaras dengan kondisi data yang benar-benar tersedia pada saat deteksi.

## Prinsip Utama

| Tipe User | Karakteristik Data | Cara Inferensi | Kedekatan ke Training |
|---|---|---|---|
| `existing user` | Sudah punya histori dan baris ABT | Lookup ABT / histori, lalu jalankan model full | Paling dekat |
| `new user` | Baru registrasi, data perilaku masih tipis | Jalankan model new-user dari feature registrasi yang memang ada | Parsial |

## Alur Existing User

1. User dipilih dari daftar existing customer.
2. Sistem mengambil `uid` dan detail user dari ABT / lookup data.
3. Feature historis yang sudah tersedia dipakai sebagai baseline.
4. Stage inference dapat dijalankan per tahap atau full journey.
5. Model membaca feature yang sudah lengkap atau hampir lengkap, termasuk graph aggregate feature jika tersedia.

### Ciri Existing User

| Aspek | Penjelasan |
|---|---|
| Input awal | `uid` dari user existing |
| Feature | Umumnya lengkap karena sudah ada histori |
| Graph feature | Bisa tersedia dari ABT atau lookup graph |
| Login / checkout / transaksi | Dapat mengacu pada histori user yang sudah ada |
| Output | Lebih stabil dan lebih dekat dengan proses training |

## Alur New User

1. User mengisi data minimum dari skenario.
2. Sistem memakai data yang memang tersedia dari input saat itu.
3. Tidak ada pemaksaan untuk melengkapi semua feature seperti data training full.
4. Jika stage lebih akhir punya input tambahan, feature baru boleh muncul dari input tersebut.
5. Stage registrasi new user memakai model khusus new-user, lalu stage lanjutan dapat memakai jalur full jika datanya sudah cukup.

### Ciri New User

| Aspek | Penjelasan |
|---|---|
| Input awal | Data dari form / app event registrasi |
| Feature | Parsial, fokus ke feature yang benar-benar tersedia di signup |
| Graph feature | Tidak dipaksakan saat registrasi jika belum ada relasi historis |
| Login / checkout / transaksi | Dibangun bertahap seiring skenario |
| Output | Lebih fleksibel, tetapi tidak selengkap training full |

## Feature Coverage by Stage

| Stage | Existing User | New User |
|---|---|---|
| `registration` | Feature dasar + histori jika tersedia | 10 feature registrasi new-user |
| `login` | Feature login + IP + histori penuh | Feature login yang bisa dihitung dari event login |
| `checkout` | Feature alamat dan pembayaran + histori | Feature alamat dan pembayaran yang tersedia |
| `transaction_completed` | Paling lengkap, hampir setara ABT | Paling lengkap untuk new user, tetapi tetap bisa belum penuh |

## Catatan Implementasi Saat Ini

- Model inference memakai dua jalur feature schema: 10 feature registrasi new-user dan 64 feature full untuk existing user / stage lengkap.
- Untuk `existing user`, feature builder bisa mengambil baris ABT sebagai baseline.
- Untuk `new user`, feature builder mengisi feature yang memang tersedia di signup; feature perilaku yang belum muncul tidak dipaksa diisi seperti data histori penuh.
- Backend sudah punya slot model terpisah lewat `NEW_USER_MODEL_PATH` dan `EXISTING_USER_MODEL_PATH`; stage `registration` untuk `new user` diarahkan ke model new-user, sedangkan jalur existing user tetap memakai model full.
- Tipe fraud utama yang dipakai project ini ada 5: `shared_device_abuse`, `shared_address_abuse`, `shared_payment_abuse`, `voucher_farming`, dan `referral_abuse`.
- Perbedaan ini memang sengaja, karena flow data existing dan new user tidak sama.

## Kesimpulan

`existing user` sebaiknya diproses dengan jalur full-feature baseline, sedangkan `new user` diproses dengan jalur incremental sesuai stage. Dengan pemisahan ini, inference tetap realistis, mudah dijelaskan, dan tidak memaksa data baru untuk terlihat seperti data historis lengkap.

<!--
Purpose: Capture business context and fraud abuse scenarios in a retail mobile app.
Used by: Reviewers understanding why the synthetic data and detection features exist.
Main dependencies: Project business assumptions and fraud scenario taxonomy.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Mobile App Exploration

## Application Name

Alfagift

## Application Overview

Alfagift merupakan aplikasi mobile retail milik Alfamart yang memungkinkan pelanggan melakukan pembelian produk kebutuhan sehari-hari secara online melalui metode delivery maupun pickup di toko. Aplikasi menyediakan fitur registrasi akun, login, voucher, promo, referral, loyalty point (A-Poin), membership, pembayaran digital, riwayat transaksi, program loyalitas, serta berbagai aktivitas engagement pelanggan.

---

## Main User Journey

### 1. Registration

Proses registrasi dilakukan menggunakan nomor handphone.

Flow registrasi:

1. User memasukkan nomor handphone.
2. User menyelesaikan CAPTCHA.
3. Sistem mengirimkan kode OTP melalui WhatsApp atau SMS.
4. User memasukkan kode OTP.
5. User mengisi data pribadi:
   * Nama lengkap
   * Email
   * Tanggal lahir
   * Jenis kelamin
   * Status pernikahan
6. User dapat memasukkan kode referral (opsional).
7. User menyetujui syarat dan ketentuan.
8. User membuat password.
9. Akun berhasil dibuat.
 
Ketentuan keamanan yang ditemukan:

* Verifikasi email tidak diwajibkan.
* Maksimal pengiriman OTP adalah 5 kali per hari di hp yang sama.
* CAPTCHA digunakan sebelum OTP dikirim untuk mengurangi bot registration.
* Nomor handphone wajib diverifikasi menggunakan OTP.


---

### 2. Login

User login menggunakan nomor handphone dan password.

---

### 3. Browse Product

User dapat:

* Melihat kategori produk.
* Mencari produk.
* Melihat produk promo.
* Menambahkan produk ke keranjang belanja.
* Melihat detail produk.

---

### 4. Apply Voucher

Voucher dapat digunakan pada halaman checkout.

Jenis voucher yang ditemukan:

* Voucher diskon.
* Voucher cashback.
* Voucher gratis ongkir.
* Voucher promo tertentu.

Ketentuan:

* Maksimal penggunaan voucher 3 kali dalam satu transaksi.
* Maksimal penggunaan voucher 5 kali dalam satu hari.

---

### 5. Checkout

#### Delivery

User wajib mengisi:

* Titik lokasi pada peta.
* Nama penerima.
* Nomor handphone penerima.
* Label alamat (Rumah, Kosan, Kantor, dan lainnya).
* Detail alamat (harus mengandung nomor rumah atau nomor jalan).
* Catatan alamat (opsional).

#### Pickup

User memilih:

* Lokasi toko Alfamart.
* Tanggal pengambilan.
* Jam pengambilan.

---

### 6. Payment

Metode pembayaran yang tersedia:

* Transfer Bank
* Virtual Account
* E-Wallet
* Credit Card
* Cash On Delivery (COD)

Flow pembayaran:

1. User memilih metode pembayaran.
2. Sistem menghasilkan nomor pembayaran atau menghubungkan ke payment provider.
3. User diberikan waktu pembayaran selama 15 menit.
4. Jika pembayaran tidak dilakukan dalam waktu tersebut maka transaksi otomatis gagal.

---

### 7. Delivery

Pada halaman ringkasan pesanan ditampilkan:

* Detail pesanan.
* Voucher yang digunakan.
* Estimasi A-Poin yang diperoleh.
* Alamat pengiriman.
* Catatan pesanan.
* Metode pembayaran.

---

### 8. Order Completion

Setelah barang diterima:

* User harus menekan tombol **Pesanan Selesai**.
* Pesanan dianggap selesai setelah dikonfirmasi oleh pengguna.
* A-Poin dan benefit loyalitas umumnya diberikan setelah transaksi berhasil diselesaikan.

---

### 9. Refund

Berdasarkan observasi:

* Pembatalan pesanan tersedia sebelum barang diterima oleh pengguna.

---

## Loyalty & Reward Features

### A-Poin

User memperoleh A-Poin dari transaksi yang berhasil.

A-Poin dapat digunakan untuk:

* Menukarkan voucher dan produk.
* Membeli pulsa dan paket data.

Untuk menggunakan A-Poin, pengguna wajib membuat PIN terlebih dahulu sebagai lapisan keamanan tambahan.

---

### Membership

Alfagift memiliki sistem membership bertingkat.

Semakin tinggi tier membership:

* Semakin besar bonus A-Poin.
* Semakin banyak benefit.
* Semakin banyak promo eksklusif.

Tier membership meningkat berdasarkan aktivitas belanja pengguna.

---

### Alfa Star

Alfa Star merupakan program loyalitas yang diperoleh dari pembelian produk sponsor tertentu selama periode program.

Benefit:

* Hadiah.
* Kupon undian.
* Produk eksklusif member.

---

### AlfaStamp

AlfaStamp merupakan program loyalitas berbasis stamp digital.

Benefit:

* Pengumpulan stamp dari pembelian produk tertentu.
* Riwayat stamp tersimpan dalam aplikasi.
* Stamp dapat ditukarkan dengan penawaran atau hadiah tertentu.

---

## Referral Program

Program referral memberikan reward berupa:

* 7.000 A-Poin.

Syarat program:

* Mengajak minimal 2 teman.
* Teman melakukan transaksi minimal Rp50.000.
* Nomor handphone belum pernah terdaftar.
* Perangkat belum pernah terdaftar.
* Maksimal 20 referral yang mendapatkan reward per akun.

---

## Promo Features

Aplikasi menyediakan halaman promo yang berisi:

* Produk diskon.
* Cashback.
* Voucher promosi.
* Promo member.
* Promo musiman.
* Produk sponsor program loyalitas.

---

## Potential Fraud Points

### 1. Multiple Accounts Using Same Device

Satu perangkat digunakan untuk membuat banyak akun baru guna memperoleh voucher, referral reward, atau promo pengguna baru.

### 2. Multiple Accounts Using Same Address

Banyak akun menggunakan alamat pengiriman yang sama untuk memperoleh promo pengguna baru berulang kali.

### 3. Voucher Farming

Pengguna membuat banyak akun hanya untuk memperoleh voucher pengguna baru dan berhenti bertransaksi setelah voucher digunakan.

### 4. Referral Abuse

Satu pengguna membuat banyak akun baru menggunakan kode referral miliknya sendiri untuk memperoleh A-Poin tambahan.

### 5. Free Shipping Abuse

Banyak akun dibuat untuk memanfaatkan promo gratis ongkir pada alamat yang sama.

### 6. Promo Abuse

Akun hanya aktif saat promo tertentu berlangsung dan tidak digunakan kembali setelah promo berakhir.

### 7. Shared Payment Abuse

Banyak akun menggunakan metode pembayaran yang sama untuk memperoleh benefit pengguna baru secara berulang.

### 8. Emulator Abuse

Banyak akun dibuat menggunakan emulator, perangkat yang dimodifikasi, atau perangkat yang memiliki aplikasi berbahaya.

### 9. A-Poin Farming

Pengguna membuat banyak akun untuk mengumpulkan A-Poin dan menukarkannya menjadi:

* Voucher atau barang.
* Pulsa.
* Paket data.

### 10. Membership Abuse

Pengguna membuat banyak akun untuk memperoleh benefit membership tertentu.

### 11. Alfa Star Farming

Pengguna membuat banyak akun untuk mengumpulkan Alfa Star dan memperoleh hadiah atau kupon undian.

### 12. AlfaStamp Farming

Pengguna membuat banyak akun untuk mengumpulkan stamp dan memperoleh reward tertentu.

### 13. Refund Abuse

Pengguna melakukan transaksi menggunakan voucher, promo, cashback, atau benefit lainnya kemudian mengajukan refund setelah barang diterima.

### 14. Referral & Registration Farming

Pelaku menggunakan banyak nomor handphone dan banyak perangkat untuk membuat akun baru secara massal guna memperoleh:

* Voucher pengguna baru.
* Referral reward.
* A-Poin.
* Promo tertentu.

Karena program referral mensyaratkan nomor handphone dan perangkat belum pernah terdaftar, pelaku biasanya akan berusaha menggunakan:

* Banyak SIM card.
* Banyak perangkat.
* Emulator atau device farm.
* Perangkat yang telah di-reset.

---

## Fraud Scenarios Relevant to Alfagift

### Scenario 1 — Shared Device Abuse

20 akun menggunakan perangkat yang sama.

Karakteristik:

* Akun dibuat dalam waktu berdekatan.
* Menggunakan voucher pengguna baru.
* Nomor handphone berbeda.
* Device fingerprint sama.

### Scenario 2 — Shared Address Abuse

30 akun menggunakan alamat pengiriman yang sama.

Karakteristik:

* Nama penerima berbeda.
* Nomor handphone berbeda.
* Lokasi pengiriman identik.
* Menggunakan promo pengguna baru.

### Scenario 3 — Shared Payment Abuse

15 akun menggunakan metode pembayaran yang sama.

Karakteristik:

* Nominal transaksi kecil.
* Menggunakan voucher.
* Pembayaran berasal dari sumber yang sama.

### Scenario 4 — Voucher Farming

Banyak akun baru dibuat hanya untuk menggunakan voucher pertama.

Karakteristik:

* Transaksi pertama dilakukan segera setelah registrasi.
* Selalu menggunakan voucher.
* Tidak aktif kembali setelah transaksi pertama.

### Scenario 5 — Referral Ring

Satu akun mereferensikan banyak akun baru yang sebenarnya dikendalikan oleh orang yang sama.

Karakteristik:

* Nomor handphone berbeda.
* Aktivitas transaksi serupa.
* Terhubung melalui perangkat, alamat, atau pembayaran yang sama.

### Scenario 6 — A-Poin Farming

Banyak akun melakukan transaksi minimum untuk memperoleh A-Poin.

Karakteristik:

* Fokus mengumpulkan A-Poin.
* Menukarkan A-Poin menjadi voucher belanja.
* Menukarkan A-Poin menjadi pulsa.
* Menukarkan A-Poin menjadi paket data.

### Scenario 7 — Alfa Star Farming

Banyak akun digunakan untuk membeli produk sponsor tertentu guna mengumpulkan Alfa Star.

### Scenario 8 — AlfaStamp Farming

Banyak akun digunakan untuk mengumpulkan stamp dalam jumlah besar dan menukarkannya menjadi reward.

### Scenario 9 — Emulator Abuse

Banyak akun dibuat menggunakan emulator atau perangkat yang memiliki aplikasi berbahaya.

Karakteristik:

* Device fingerprint mirip.
* Aktivitas registrasi tinggi.
* Banyak akun berasal dari perangkat yang sama.

### Scenario 10 — Refund Abuse

Banyak akun melakukan transaksi menggunakan promo kemudian mengajukan refund setelah barang diterima.

### Scenario 11 — Referral & Registration Farming

Pelaku menggunakan banyak nomor handphone dan banyak perangkat untuk membuat akun baru secara massal guna memperoleh voucher pengguna baru, referral reward, A-Poin, dan promo tertentu.

---

## Required Synthetic Data Tables

Dari hasil eksplorasi ekstensif di atas, kita membagi rancangan struktur *database* ke dalam dua kategori besar: **Tabel Inti yang Diimplementasikan** dan **Tabel Eksploratif Tambahan**.

### A. Implemented Core Data Tables (14 Tabel Inti)
Tabel-tabel di bawah ini adalah fokus utama yang **telah diwujudkan (di-generate)** di dalam *pipeline* proyek deteksi kecurangan ini. Tabel ini cukup merepresentasikan alur utama (*User Journey*) yang digunakan untuk membedakan antara pengguna asli dan sindikat penipu.

#### Core User, Device, & Login Tables

1. **users**

   * user_id
   * full_name
   * phone_number
   * email
   * birth_date
   * gender
   * marital_status
   * registration_date
   * referral_code
   * membership_tier
   * apoin_balance
   * account_status

2. **devices**

   * device_id
   * device_fingerprint
   * device_brand
   * device_model
   * os_type
   * os_version
   * emulator_flag
   * malicious_app_flag
   * first_seen_at

3. **user_devices**

   * user_device_id
   * user_id
   * device_id
   * linked_at

4. **login_sessions**

   * session_id
   * user_id
   * device_id
   * login_timestamp
   * logout_timestamp
   * ip_address
   * login_status

---

### Address & Delivery Tables

5. **addresses**

   * address_id
   * latitude
   * longitude
   * address_label
   * address_detail
   * recipient_name
   * recipient_phone

6. **user_addresses**

   * user_address_id
   * user_id
   * address_id
   * created_at

---

### Payment Tables

7. **payments**

   * payment_id
   * payment_type
   * payment_provider
   * payment_identifier
   * card_hash
   * wallet_id
   * bank_account_hash

8. **user_payments**

   * user_payment_id
   * user_id
   * payment_id
   * linked_at

---

### B. Exploratory / Deferred Tables (10 Tabel Ekstra)
Tabel-tabel berikut ini diidentifikasi selama fase observasi aplikasi, namun **tidak diikutsertakan** dalam simulasi *pipeline* akhir demi menjaga fokus dan efisiensi model (Mencegah *Feature Bloat*).

#### Product & Catalog Tables

9. **products**

   * product_id
   * product_name
   * category
   * brand
   * sponsor_flag
   * alfa_star_eligible
   * alfa_stamp_eligible
   * price

10. **stores**

* store_id
* store_name
* city
* province
* latitude
* longitude

---

### Voucher & Promotion Tables

11. **vouchers**

* voucher_id
* voucher_code
* voucher_type
* discount_value
* cashback_value
* free_shipping_flag
* start_date
* end_date

12. **voucher_redemptions**

* redemption_id
* voucher_id
* user_id
* transaction_id
* redeemed_at

13. **promotions**

* promotion_id
* promotion_name
* promotion_type
* start_date
* end_date

---

### Transaction Tables

14. **transactions**

* transaction_id
* user_id
* address_id
* payment_id
* store_id
* order_type
* transaction_amount
* voucher_discount
* cashback_amount
* apoin_earned
* transaction_status
* created_at

15. **transaction_items**

* transaction_item_id
* transaction_id
* product_id
* quantity
* unit_price
* subtotal

16. **transaction_status_history**

* history_id
* transaction_id
* status
* status_timestamp

---

### Loyalty Program Tables

17. **apoin_transactions**

* apoin_transaction_id
* user_id
* transaction_type
* points_amount
* source
* created_at

18. **membership_history**

* membership_history_id
* user_id
* membership_tier
* effective_date

19. **alfa_star_transactions**

* alfa_star_transaction_id
* user_id
* transaction_id
* star_amount
* created_at

20. **alfa_stamp_transactions**

* alfa_stamp_transaction_id
* user_id
* transaction_id
* stamp_amount
* created_at

---

### Referral Tables

21. **referrals**

* referral_id
* referrer_user_id
* referred_user_id
* referral_date
* referral_reward_points
* referral_status

---

### Refund Tables

22. **refunds**

* refund_id
* transaction_id
* user_id
* refund_reason
* refund_amount
* refund_status
* refund_created_at

---

### Fraud Label Tables

23. **fraud_labels**

* fraud_label_id
* user_id
* fraud_type
* fraud_scenario
* fraud_flag
* investigation_status

24. **fraud_links**

* fraud_link_id
* source_user_id
* linked_user_id
* link_type
* confidence_score



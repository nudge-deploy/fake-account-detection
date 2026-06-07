# 🌊 Cara Tabel Mentah Diolah Menjadi ABT

Dokumen ini menjelaskan **bagaimana persisnya logika perhitungan (manipulasi baris dan kolom)** yang dikenakan pada setiap tabel mentah Anda untuk menghasilkan fitur-fitur pendeteksi *fraud* di dalam **Analytics Base Table (ABT)**.

Semua proses di bawah ini terjadi di dalam *script* `build_abt.py` menggunakan pustaka **Pandas**.

---

## 🗺️ Visualisasi Alur Pemrosesan (*Data Processing Flow*)

Berikut adalah diagram visual yang merangkum bagaimana 5 grup tabel mentah dimanipulasi dengan operasi matematika hingga akhirnya digabung menjadi satu tabel ABT raksasa:

```mermaid
flowchart TD
    %% Input Tables
    T_Users[(1. users.csv)]
    T_Junc[(2. Junction Tables)]
    T_Trans[(3. transactions.csv)]
    T_Login[(4. login_sessions.csv)]
    T_Graph[(5. user_graph_features)]

    %% Operations
    Op_Text[Text Parsing & Shannon Entropy]
    Op_Group[Group-By Aset & Hitung Unique User]
    Op_Time[Sort by Waktu & Rolling Window]
    Op_Vel[Time Windowing 1h - 24h]

    %% Derived Features
    F_Id[Fitur Identitas<br/>email_rand, phone_score]
    F_Junc[Fitur Aset<br/>max_acc_dev, max_acc_addr]
    F_Trans[Fitur Transaksi<br/>reg2txn_min, txn_f1m]
    F_Login[Fitur Kecepatan<br/>login_f1h, max_acc_ip]
    F_Graph[Fitur Makro Graf<br/>graph_degree, comp_size]

    %% Flow
    T_Users --> Op_Text --> F_Id
    T_Junc --> Op_Group --> F_Junc
    T_Trans --> Op_Time --> F_Trans
    T_Login --> Op_Vel --> F_Login
    T_Graph --> F_Graph

    %% Merge
    Merge{Left Join <br/> berdasarkan user_id}
    
    F_Id --> Merge
    F_Junc --> Merge
    F_Trans --> Merge
    F_Login --> Merge
    F_Graph --> Merge

    %% Output
    Out([fake_account_abt.csv <br/> 1 Baris = 1 Pengguna = 64 Fitur])
    Merge ===> Out
    
    %% Styling
    style Out fill:#ffcccc,stroke:#ff0000,stroke-width:2px,color:#000
    style Merge fill:#ffffcc,stroke:#d4af37,stroke-width:2px,color:#000
```

---

## 🔬 Detail Logika Manipulasi (*Pandas Operations*)

### 1. Pengolahan Tabel Identitas (`users.csv`)
Tabel ini berisi profil dasar. Karena *bot* sering menggunakan nama palsu, kita harus mengekstrak keanehan pada teksnya.
*   **Manipulasi:** Membelah teks pada kolom `email` menjadi bagian *nama* dan *domain* (misal: `joko99@gmail.com` dibelah).
*   **Perhitungan Matematika:**
    *   **Shannon Entropy (`email_rand`):** Menghitung seberapa acak susunan huruf di nama email. Manusia biasanya punya pola huruf bisa dibaca, *bot* sering pakai huruf acak (seperti `asdfqwer`).
    *   **Rasio Angka (`email_num_ratio`):** Menghitung proporsi angka di dalam nama email. *Bot* sering memakai nomor urut.
    *   **Phone Score (`phone_score`):** Mencari pola angka repetitif (seperti `0811111111`) di kolom `phone_number`.

### 2. Pengolahan Tabel Aset / Junction (`user_devices.csv`, dll)
Sindikat penipu selalu menghemat biaya dengan cara menggunakan 1 *Handphone* atau 1 Alamat untuk puluhan akun palsu.
*   **Target Tabel:** `user_devices.csv`, `user_addresses.csv`, `user_payments.csv`.
*   **Manipulasi Pandas:** Melakukan **Group-By** berdasarkan ID Aset (contoh: `df.groupby('device_id')`).
*   **Perhitungan:** Mengkalkulasi jumlah akun unik (`nunique(user_id)`) yang menempel pada aset tersebut.
*   **Penggabungan (*Join*):** Nilai hasil hitungan tersebut ditempelkan kembali ke masing-masing pengguna.
*   **Hasil Fitur:** Terciptalah fitur `max_acc_dev` (Berapa akun maksimal yang menempel di perangkat orang ini?), `max_acc_addr`, dan `max_acc_pay`.

### 3. Pengolahan Tabel Log Transaksi (`transactions.csv` & `vouchers.csv`)
Pola belanja penipu sangat berbeda dengan pengguna organik. Penipu biasanya langsung memborong sesaat setelah mendaftar demi mengeksploitasi *voucher* pengguna baru.
*   **Manipulasi:** Mengurutkan tabel berdasarkan waktu (`transaction_date`), lalu melakukan **Join** dengan tabel `users` untuk membandingkan waktu daftar dengan waktu transaksi.
*   **Perhitungan Jarak Waktu (`reg2txn_min`):** Mengurangi cap waktu transaksi PERDANA dengan cap waktu pendaftaran (`registration_date`). Semakin kecil menitnya (contoh: transaksi 1 menit setelah daftar), semakin tinggi risiko *bot*.
*   **Perhitungan Mundur (*Rolling Window*):** Memfilter baris dari hari ini ditarik mundur ke 1 bulan hingga 6 bulan ke belakang. Lalu menghitung total transaksi (`txn_f1m`) dan rata-rata belanjanya (`avg_amt1m`).
*   **Perhitungan Promosi (`promo_ratio`):** Menghitung rasio berapa kali kolom `voucher_id` tidak kosong dibandingkan total seluruh transaksinya.

### 4. Pengolahan Tabel Aktivitas (`login_sessions.csv`)
*Bot* penipu dijalankan oleh skrip otomatis yang menyebabkan ratusan *login* terjadi dalam hitungan jam (biasanya tengah malam).
*   **Manipulasi Velocity:** Menggunakan fungsi jendela waktu (*Time Windowing*) untuk memfilter cap waktu `login_timestamp`.
*   **Perhitungan Kecepatan (`login_f1h`, `login_f24h`):** Menghitung agregasi jumlah baris sesi *login* dari pengguna tersebut murni hanya untuk 1 jam, 6 jam, 12 jam, dan 24 jam terakhir. Jika skor `login_f1h`-nya meledak tak wajar, ini adalah indikasi sindikat *farming*.
*   **Manipulasi IP:** Sama seperti perangkat, kita melakukan *Group-By* terhadap `ip_address` untuk melihat berapa akun yang *login* dari IP Wi-Fi yang persis sama (`max_acc_ip`).

### 5. Pengolahan Tabel Relasi Jaringan (`user_graph_features.csv`)
Fitur ini dihitung terlebih dahulu oleh `build_graph.py` menggunakan Ilmu Graf (NetworkX).
*   **Manipulasi Eksternal:** Mengubah tabel *junction* menjadi garis-garis koneksi (*Bipartite Graph*), lalu memproyeksikannya menjadi jaringan murni antar-manusia (*User-to-User*).
*   **Perhitungan Graf:**
    *   **Degree (`graph_degree`):** Menghitung berapa banyak akun lain yang terhubung secara fisik (lewat alat/alamat yang sama) dengan pengguna ini.
    *   **Component Size (`comp_size`):** Menelusuri rantai koneksi sampai ujung untuk menghitung ukuran total populasi sindikat tempat pengguna ini berada.
*   **Penggabungan:** Skrip `build_abt.py` tinggal melakukan *Left Join* satu-ke-satu pada `user_id` untuk memasukkan skor "mafia" ini ke baris ABT pengguna.

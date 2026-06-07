# Dokumentasi Proyek Deteksi Akun Palsu & Jaringan Sindikat (Fraud Detection)

Selamat datang di pusat dokumentasi *(knowledge base)* untuk Proyek Sistem Deteksi Fraud. Folder `docs` ini disusun secara terstruktur dari hulu ke hilir untuk mendokumentasikan keseluruhan proses pembuatan sistem, mulai dari eksplorasi logika bisnis hingga peluncuran model Artificial Intelligence ke dalam aplikasi terintegrasi.

---

## 📂 Daftar Isi Dokumentasi

Ikuti urutan dokumen di bawah ini untuk memahami secara bertahap bagaimana kami merancang solusi penanganan *fraud*:

### Fase 1: Perancangan Fondasi & Bisnis
1. 📖 **[01_mobile_app_exploration.md](01_mobile_app_exploration.md)**
   Eksplorasi awal untuk memetakan kelemahan sistem di dalam aplikasi Alfagift dan cara-cara yang dilakukan oleh sindikat penipu untuk mengeksploitasi celah bisnis tersebut (seperti *Voucher Farming* dan *Referral Abuse*).
   
2. 📖 **[02_data_model_design.md](02_data_model_design.md)**
   Merancang struktur basis data relasional (RDBMS) yang mengutamakan relasi antar-entitas untuk merekam perpindahan *device*, alamat IP, lokasi, dan pembayaran secara teliti.

### Fase 2: Pipeline Data & Artificial Intelligence
3. 📖 **[03_synthetic_data_generation.md](03_synthetic_data_generation.md)**
   Penjelasan teknis tentang *simulator* berbasis probabilitas yang digunakan untuk menciptakan 10.000 data fiktif secara serealistis mungkin (dengan menyuntikkan *Persona Bot* pada waktu *login* tertentu).

4. 📖 **[04_eda_report.md](04_eda_report.md)**
   Laporan Investigasi Data Eksploratori (EDA). Membedah secara statistik seperti apa wujud penipu vs pengguna normal dalam data yang telah disimulasikan.

5. 📖 **[05_feature_engineering.md](05_feature_engineering.md)**
   *(Sangat Krusial)* Menjelaskan bagaimana kami mengubah data relasional mentah menjadi **Analytics Base Table (ABT)**, serta konsep canggih **Bipartite Network Graph** untuk menyulap data tak terlihat menjadi angka-angka *Machine Learning*.

6. 📖 **[06_modeling_report.md](06_modeling_report.md)**
   Hasil uji coba komparasi performa algoritma Machine Learning (Logistic Regression, Random Forest, dan **XGBoost**). Termasuk cara kami mengatasi fenomena Kebocoran Data *(Data Leakage)*.

### Fase 3: Deployment & Sistem Produksi
7. 📖 **[07_system_architecture_and_api.md](07_system_architecture_and_api.md)**
   Rangkuman arsitektur penggabungan antara Model AI dengan **API Backend (FastAPI)** dan **Frontend Dashboard React**, di mana kami mengimplementasikan skema pertahanan berlapis ganda *(Hybrid Rule-Based + Machine Learning Engine)*.

---

### Lampiran Tambahan
- 📑 **[Feature_Engineering_Documentation.md](Feature_Engineering_Documentation.md)**: Daftar lengkap kamus fitur *(data dictionary)* secara terperinci.
- 📑 **[Feature_Lineage_Documentation.md](Feature_Lineage_Documentation.md)**: Asal-usul teknis (*lineage*) dari mana sebuah fitur diciptakan.
- 📑 **[Graph_Feature_Documentation.md](Graph_Feature_Documentation.md)**: Detail perhitungan teknis mengenai derajat graf, besaran komponen berantai, dan koneksi lintas *entitas*.

> Dokumentasi ini ditulis secara rapi agar mudah dibaca dan dievaluasi sebagai syarat pencapaian program Magang (*Internship*) Analisis Data & Fraud Detection.

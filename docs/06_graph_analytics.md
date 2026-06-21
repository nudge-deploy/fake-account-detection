<!--
Purpose: Explain graph analytics design, entity relationships, and fraud-ring detection logic.
Used by: Developers, reviewers, and documentation readers for graph-based fraud analysis.
Main dependencies: graph construction scripts, graph feature pipeline, and analytics outputs.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# 07. Graph Analytics Design

Dokumen ini menjelaskan arsitektur dan metodologi deteksi *Fraud Rings* (sindikat penipuan terorganisir) menggunakan analisis graf (*Network Analytics*).

## 1. Pendekatan Berbasis Graf
Dalam ekosistem e-commerce ritel, penipu yang mengeksploitasi *voucher* atau program *referral* jarang beroperasi sendirian. Mereka biasanya menggunakan banyak akun (ternak akun) namun seringkali berbagi atribut fisik atau digital yang sama karena keterbatasan *resource*.

Kami memodelkan setiap pengguna sebagai **Node (Simpul)** dan kesamaan atribut sebagai **Edge (Sisi)**.

## 2. Definisi *Edge* (Relasi Antar Akun)
Sebuah *Edge* akan terbentuk antara User A dan User B jika mereka berbagi salah satu dari atribut berikut:
- **Shared IP Address**: Kedua akun pernah *login* atau bertransaksi menggunakan IP publik yang sama.
- **Shared Device Fingerprint**: Kedua akun diakses melalui perangkat keras fisik atau emulator yang sama (terdeteksi via Device ID).
- **Shared Payment Method**: Kedua akun menggunakan nomor kartu kredit, akun *e-wallet*, atau nomor rekening bank yang sama untuk bertransaksi.
- **Shared Shipping Address**: Kedua akun mengirimkan barang pesanan ke alamat fisik yang sama persis (atau variasi teks yang sangat mirip).

## 3. Ekstraksi Fitur dari Jaringan (NetworkX)
Menggunakan pustaka `networkx` di Python, kami mengekstraksi metrik matematis dari bentuk graf yang terbentuk untuk setiap pengguna:
1. **Degree Centrality (`graph_degree`)**: Berapa banyak akun lain yang terhubung langsung dengan pengguna ini. Skor tinggi mengindikasikan akun tersebut adalah pusat dari sebuah sindikat (misal: satu *device* untuk 50 akun).
2. **Connected Component Size**: Ukuran total dari *cluster* tempat pengguna tersebut berada. Sindikat bot biasanya membentuk pulau jaringan berukuran besar (>10 node).
3. **Referral Ring Score**: Deteksi siklus berarah (*directed cycles*) pada data *referral*. Jika A merujuk B, B merujuk C, dan C merujuk A, ini adalah indikasi kuat penyalahgunaan *referral*.

## 4. Visualisasi Frontend
Di *dashboard*, kami menggunakan `react-force-graph-2d` untuk memproyeksikan graf ini ke layar pengguna. Algoritma *Force-Directed Graph* secara otomatis menarik *node* yang saling berhubungan menjadi saling berdekatan (membentuk *cluster*). 

- **Node Merah**: Akun terdeteksi sebagai Fraud (Berdasarkan *Machine Learning*).
- **Node Hijau**: Akun Normal.
- **Node Biru**: Entitas penghubung (Device, Payment, IP, Address).

Melalui panel "Informasi Node", analis *fraud* dapat melihat persis entitas apa yang menghubungkan satu akun ke akun lainnya, memungkinkan investigasi yang lebih komprehensif.

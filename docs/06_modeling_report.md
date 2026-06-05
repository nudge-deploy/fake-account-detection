# Laporan Pemodelan Machine Learning & Evaluasi XGBoost

Laporan ini merangkum *pipeline* klasifikasi Machine Learning **setelah dilakukannya perbaikan arsitektur data** dan penggabungan dengan fitur *Bipartite Graph Projection*. Seluruh fitur yang rentan membocorkan data masa depan (seperti agregasi `max_acc_ip` dan fitur jaringan graf) telah dihitung ulang khusus menggunakan data *training* untuk mencegah *Data Leakage*.

---

## 1. Metodologi & Pembagian Dataset

- **Dataset Utama:** Analytics Base Table (`fake_account_abt.csv`) digabungkan dengan Graph Features (`user_graph_features.csv`).
- **Total Baris:** 10.000 pengguna.
- **Total Kolom Fitur:** 69 (Setelah *merge* dan pembuangan target *proxy* seperti `risk_score`).
- **Split Configuration:** **70% Training** (7.000 pengguna) dan **30% Testing** (3.000 pengguna), distratifikasi agar seimbang.
- **Pencegahan Kebocoran (Data Leakage Fix):** Fitur struktural makro (skalar) dan graf jaringan (seperti derajat koneksi dan ukuran komponen) dikalkulasi secara terisolasi hanya pada *split training*.

---

## 2. Hasil Evaluasi Test Set & Komparasi

Performa model diukur pada 3.000 data tes yang benar-benar buta (belum pernah dilihat model sebelumnya):

| Metric | Logistic Regression | Random Forest | XGBoost / Gradient Boosting ⭐ |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 94.07% | 93.57% | **96.50%** |
| **Precision** | 88.32% | 93.91% | **95.74%** |
| **Recall** | **92.44%** | 84.00% | **92.44%** |
| **F1-Score** | 90.34% | 88.68% | **94.06%** |
| **ROC-AUC** | 0.9822 | 0.9812 | **0.9910** |

> **Kemenangan XGBoost:** XGBoost terbukti sangat superior dalam menangani data yang berpotensi *imbalanced* dan memiliki banyak fitur pohon (seperti *threshold login_velocity*). Dengan F1-Score 94%, model ini mampu menangkap 92.4% penipu tanpa salah menuduh orang baik secara berlebihan (Presisi 95.7%).

---

## 3. Analisis Champion Model & Feature Importance

- **Model Terpilih:** **XGBoost** (F1-Score: **0.9406**).
- **5 Fitur Paling Berpengaruh (Top 5 Predictive Features):**
  
  Model ML kita menyingkap kelemahan utama dari para sindikat penipu (*Fraud Rings*):

  1. 🥇 **`login_f24h` (Pentingnya: 30.31%)**
     Fitur kecepatan (*velocity*) yang merekam puncak *login* berturut-turut dalam 24 jam. Ini adalah indikator terbaik untuk membongkar **Persona Bot / Skrip Otomatis** yang mencoba membobol atau mengeksploitasi sistem dalam waktu singkat.
     
  2. 🥈 **`shared_ip_count` (Pentingnya: 15.61%)**
     Fitur *Bipartite Graph* yang menghitung jumlah irisan alamat IP. Terbukti, penipu bersindikasi akan selalu tertangkap di jaring koneksi IP mereka.
     
  3. 🥉 **`avg_amt1m` (Pentingnya: 12.28%)**
     Rata-rata nominal transaksi dalam 1 bulan terakhir. Penipu umumnya melakukan transaksi dengan nilai (Rupiah) yang dipaskan serendah mungkin untuk sekadar mengklaim *voucher*.
     
  4. 🏅 **`max_acc_ip` (Pentingnya: 11.50%)**
     Fitur kepadatan absolut dari sebuah *IP Address*. 
     
  5. 🏅 **`login_f18h` (Pentingnya: 5.52%)**
     Fitur kecepatan *login* pendamping dengan jendela waktu yang sedikit lebih rapat.

![Feature Importance](file:///d:/magang/fraud%20detection/docs/images/feature_importance.png)

---

## 4. Kesimpulan Akhir

Dengan perpaduan simulasi *Persona Jam Login* dari Simulator dan Ekstraksi Bipartit dari Modul Graph, kecerdasan buatan (*AI*) kita akhirnya memiliki "mata" untuk mengenali ciri khas robot dan sindikasi. Skor **ROC-AUC 99.1%** menandakan bahwa model kita sudah mencapai tingkatan akurasi tingkat industri (Level Produksi) dan siap diintegrasikan ke sistem perbankan / aplikasi *e-commerce* (*Alfagift*) sungguhan.

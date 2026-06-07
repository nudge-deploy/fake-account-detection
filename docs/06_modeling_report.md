# Laporan Pemodelan Machine Learning & Evaluasi XGBoost

Laporan ini merangkum *pipeline* klasifikasi Machine Learning **setelah dilakukannya perbaikan arsitektur data** dan penggabungan dengan fitur *Bipartite Graph Projection*. Seluruh fitur yang rentan membocorkan data masa depan (seperti agregasi `max_acc_ip` dan fitur jaringan graf) telah dihitung ulang khusus menggunakan data *training* untuk mencegah *Data Leakage*.

---

## 1. Metodologi & Pembagian Dataset

- **Dataset Utama:** Analytics Base Table (`fake_account_abt.csv`) digabungkan dengan Graph Features (`user_graph_features.csv`).
- **Total Baris:** 10.000 pengguna.
- **Total Kolom Fitur:** 64 Fitur Terpilih (Setelah seleksi fitur dan pembuangan label seperti `risk_score`).
- **Split Configuration:** **70% Training** (7.000 pengguna) dan **30% Testing** (3.000 pengguna), distratifikasi agar seimbang.
- **Pencegahan Kebocoran (Data Leakage Fix):** Fitur struktural makro (skalar) dan graf jaringan (seperti derajat koneksi dan ukuran komponen) dikalkulasi secara terisolasi hanya pada *split training*.

---

## 2. Hasil Evaluasi Test Set & Komparasi

Performa model diukur pada 3.000 data tes yang benar-benar buta (belum pernah dilihat model sebelumnya):

| Metric | Logistic Regression | Random Forest | XGBoost / Gradient Boosting ⭐ |
| :--- | :---: | :---: | :---: |
| **Accuracy** | 91.03% | 91.40% | **94.63%** |
| **Precision** | 82.22% | 95.72% | **96.01%** |
| **Recall** | **89.44%** | 74.66% | **85.66%** |
| **F1-Score** | 85.68% | 83.89% | **90.54%** |
| **ROC-AUC** | 0.9699 | 0.9787 | **0.9898** |

> **Kemenangan XGBoost:** XGBoost terbukti sangat superior dalam menangani data yang berpotensi *imbalanced* dan memiliki banyak fitur pohon (seperti *threshold login_velocity*). Dengan ROC-AUC nyaris sempurna (99%), XGBoost berhasil mengungguli Random Forest, terutama dalam aspek presisi (kemampuan untuk tidak salah menuduh/blokir pengguna asli) yang menembus angka 96.01%.

---

## 3. Analisis Champion Model & Feature Importance

- **Model Terpilih:** **XGBoost** (F1-Score: **0.9054**).
- **Interpretasi Kinerja:** 
  Dari semua tebakan fraud (Fake Account) oleh XGBoost, 96% di antaranya adalah benar-benar penipu (*Precision sangat tinggi*). Ini menandakan bahwa model sudah siap untuk masuk ke tahap Produksi tanpa menyebabkan banyak komplain (*False Positives*) dari *customer* Alfagift. 
  
- **Top Predictive Features:**
  Berdasarkan proses pelatihan model terakhir (setelah perbaikan *Data Leakage*), terjadi pergeseran metrik yang paling memengaruhi keputusan AI. Model kini tidak lagi bergantung pada kecepatan *login*, melainkan berfokus penuh pada **Jejak Relasi Sindikat (Graph Network)**. Berikut adalah Top 5 Fitur Utama:

  1. 🥇 **`shared_ip_count` (Pentingnya: 41.02%)**
     Fitur *Bipartite Graph* yang menghitung jumlah irisan alamat IP. Terbukti, penipu bersindikasi akan selalu tertangkap jaring karena mereka "memaksa" menggunakan alamat IP yang sama secara masif.
     
  2. 🥈 **`max_acc_ip` (Pentingnya: 14.31%)**
     Kepadatan absolut dari sebuah *IP Address* (berapa banyak akun yang masuk dari 1 titik IP internet).
     
  3. 🥉 **`comp_size` (Pentingnya: 8.16%)**
     Ukuran *Connected Component* dari graf jaringan. Makin besar kumpulannya, makin yakin AI bahwa ini adalah *Fraud Ring*.
     
  4. 🏅 **`shared_payment_count` (Pentingnya: 4.65%)**
     Penggunaan instrumen pembayaran yang sama secara berulang oleh berbagai akun.
     
  5. 🏅 **`reg2txn_min` (Pentingnya: 4.48%)**
     Waktu (dalam menit) dari mendaftar hingga melakukan transaksi pertama. Penipu umumnya bergerak instan layaknya robot.

![Feature Importance](file:///d:/magang/fraud%20detection/docs/images/feature_importance.png)

---

## 4. Kesimpulan Akhir

Dengan perpaduan simulasi *Persona Jam Login* dari Simulator dan Ekstraksi Bipartit dari Modul Graph, kecerdasan buatan (*AI*) kita akhirnya memiliki "mata" untuk mengenali ciri khas robot dan sindikasi. Skor **ROC-AUC 98.98%** menandakan bahwa model kita sudah mencapai tingkatan akurasi tingkat industri (Level Produksi) dan telah siap untuk dipadukan (Hybrid) dengan Rule-Based Engine di Backend FastAPI.

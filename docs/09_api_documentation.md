<!--
Purpose: Describe system architecture, backend API integration, and runtime flow.
Used by: Developers and reviewers validating end-to-end service wiring.
Main dependencies: FastAPI backend, Next.js frontend, model artifacts, ABT, graph JSON.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Arsitektur Sistem & Integrasi API

Dokumen ini merangkum penyatuan *(integration)* antara Model Machine Learning yang telah dilatih dengan antarmuka sistem nyata, membentuk siklus perlindungan *End-to-End*.

---

## 1. Topologi Arsitektur Sistem

Sistem deteksi penipuan ini terdiri dari tiga komponen utama:
1.  **Data & Model Engine (Python/Pandas/Scikit-Learn/XGBoost):** Skrip *offline* yang mensimulasikan data relasional, membuat *Network Graph*, menyusun *Analytics Base Table* (ABT final berisi raw features + graph aggregate features), melatih model, dan mengunggah data ke Supabase.
2.  **API Backend (FastAPI):** Mesin pelayan super cepat (berbasis *asynchronous*) yang melayani permintaan deteksi secara langsung (*real-time*). Backend memuat file `.pkl` dari *XGBoost* ke dalam memori server untuk menjamin latensi prediksi di bawah 50ms.
3.  **Frontend Dashboard (React/Next.js/Tailwind CSS):** Antarmuka grafis futuristik bergaya *Cyberpunk/Glassmorphism* untuk tim analis investigasi (Fraud/Risk Team) guna memonitor pergerakan akun-akun mencurigakan secara visual.

---

## 2. Paradigma "Hybrid Detection Engine"

Alih-alih hanya mengandalkan satu metode, *Backend FastAPI* kita memadukan dua paradigma pertahanan sekaligus:

### A. Rule-Based Score (Logika Kaku Manusia)
Logika tradisional yang menggunakan aturan eksplisit ("Jika X maka Y").
*   **Contoh:** `Jika 1 HP dipakai oleh > 5 akun, maka skor +40.`
*   **Kelebihan:** Sangat cepat, bisa dijelaskan di mata hukum (interpretasi 100%), dan secara instan mampu menendang penipu pemula (sangat agresif).
*   **Kelemahan:** Penipu pintar (sindikat terorganisir) akan menahan diri untuk tidak melebihi parameter batas agar lolos (Misal: Hanya membagi 2 akun per HP).

### B. Machine Learning Probability (Kecerdasan Buatan XGBoost)
Kalkulasi *Decision Tree* acak yang menilai korelasi rumit pada 64 fitur sekaligus.
*   **Contoh:** Menyadari bahwa meskipun 1 HP hanya dipakai 2 akun, namun jarak antara mendaftar dan memakai *voucher* hanya 1 menit + email yang digunakan 90% acak, maka probabilitasnya **74% Fake**.
*   **Kelebihan:** Mampu mendeteksi pola terselubung dan mutasi trik penipuan baru yang lolos dari *Rule-Based*.

> [!NOTE]
> **Integrasi Akhir:** Di Dashboard *Frontend*, sebuah akun akan ditandai berisiko tinggi apabila **salah satu** dari kedua mesin ini membunyikan alarm. (Kriteria curiga: `Rule Score >= 50` ATAU `ML Probability > 50%`).

---

## 3. Dynamic Prediction Feature (Pencegah Data Basi)

Dalam implementasi API `/api/user/{uid}`, sistem tidak sekadar membaca prediksi yang sudah tersimpan di *Database* (karena data tersebut bisa basi/kuno). 

Fungsi `predict_user()` di `model_service.py` akan **secara dinamis mengambil 64 indikator model dari ABT final**, memasukkannya ke dalam format *Pandas DataFrame*, dan menembakkannya secara langsung ke model champion yang ada di memori *Server*. Hal ini menjamin bahwa **Nilai Probabilitas (ML Probability)** yang dilihat oleh Tim Investigator di layar UI selaras dengan `feature_columns.json` terbaru.

---

## 4. Endpoints API Utama

1.  `GET /api/stats/overview`: Memberikan ringkasan metrik global (Total Akun, Fraud Rate, Persebaran Kategori, dsb).
2.  `GET /api/users`: Menyediakan *paginated table* lengkap dengan fungsi pengurutan (terutama mengurutkan probabilitas penipuan dari tertinggi) beserta filter pencarian spesifik (seperti filter Sindikat Alamat/Device).
3.  `GET /api/user/{uid}`: Mengembalikan data ultra-detail untuk keperluan "Laci Investigasi" *(Investigation Drawer)*, mencakup riwayat koneksi relasi IP, daftar *Device*, dan skor *Real-time Prediction*.
4.  `POST /api/chat`: Jalur akses asisten virtual (LLM Groq API) untuk mengobrol dan menganalisis anomali menggunakan bahasa natural (NLP).

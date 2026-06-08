# 10. Deployment Guide

Aplikasi Fraud Detection V-TEKI dibangun dengan arsitektur terpisah (*Decoupled Architecture*) antara antarmuka pengguna (Frontend) dan server logika inti (Backend). Proses *deployment* direkomendasikan menggunakan dua platform Cloud gratis/PaaS untuk kemudahan dan keandalan tinggi.

## 1. Backend API (Render.com)
Backend berbasis Python (FastAPI) membutuhkan *environment* yang mampu menjalankan uvicorn dan mengeksekusi skrip Python murni.

### Persiapan File
Pastikan repositori Anda memiliki dua file ini di *root* (folder terluar):
1. **`backend/requirements.txt`**: Daftar *libraries* (fastapi, scikit-learn, dll).
2. **`render.yaml`**: *Blueprint Configuration* untuk Render.
   ```yaml
   services:
     - type: web
       name: fraud-detection-backend
       env: python
       rootDir: backend
       buildCommand: "pip install -r requirements.txt"
       startCommand: "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   ```

### Langkah Deployment
1. Buat akun di [Render](https://render.com) dan sambungkan dengan GitHub.
2. Pilih menu **"New" -> "Blueprint"** di *dashboard*.
3. Render akan otomatis mendeteksi konfigurasi `render.yaml` dan membangun lingkungan Python.
4. Jangan lupa mengatur variabel lingkungan rahasia (contoh: `GROQ_API_KEY`) di menu *Environment* jika dibutuhkan.
5. Salin URL publik API Anda (misal: `https://fraud-backend.onrender.com`).

---

## 2. Frontend Dashboard (Vercel)
Antarmuka pengguna (Frontend) dibangun di atas framework Next.js, yang mana Vercel adalah *platform native* pengembangnya.

### Persiapan Konfigurasi
1. Karena kode Next.js kita berada di dalam sub-folder `frontend/`, beri tahu Vercel bahwa *Root Directory* aplikasi adalah folder tersebut.

### Langkah Deployment
1. Buat akun di [Vercel](https://vercel.com) dan sambungkan repositori GitHub Anda.
2. Klik **"Add New Project"** dan *import* *repository* Fraud Detection Anda.
3. Di bagian pengaturan *Build & Development*:
   - **Root Directory**: Ubah ke `frontend`
   - **Framework Preset**: Vercel otomatis mendeteksi Next.js
4. Di bagian **Environment Variables**, tambahkan:
   - Nama: `NEXT_PUBLIC_API_URL`
   - Value: URL dari Render di langkah 1 (tanpa slash di akhir, contoh: `https://fraud-backend.onrender.com`)
5. Klik **Deploy** dan tunggu proses *build*.

## 3. Deployment Server VPS Lokal (Alternatif)
Jika institusi mewajibkan *deployment On-Premise* di VPS Ubuntu/CentOS, Anda disarankan menggunakan **Docker**.

1. Buat `Dockerfile` terpisah di masing-masing folder `backend/` dan `frontend/`.
2. Gabungkan menggunakan `docker-compose.yml` di folder *root* untuk menghubungkan port `3000` (Frontend) dan `8000` (Backend) melalui jaringan lokal kontainer (*bridge network*).
3. Jalankan `docker-compose up -d --build`.

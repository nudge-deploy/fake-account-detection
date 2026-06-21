<!--
Purpose: Document the current backend API surface and how it connects to the frontend simulation.
Used by: Developers and reviewers validating end-to-end service wiring.
Main dependencies: FastAPI backend, Next.js frontend, model artifacts, ABT, graph data.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# 09. API Documentation

Dokumen ini merangkum integrasi antara backend FastAPI, model machine learning, dan frontend Next.js yang dipakai untuk simulasi fraud detection end-to-end.

## 1. Komponen Utama

1. **Data & Model Engine:** skrip offline yang mensimulasikan data relasional, membangun graph, menyusun ABT, dan melatih model.
2. **API Backend (FastAPI):** melayani permintaan prediksi dan chatbot secara langsung.
3. **Frontend Dashboard (Next.js):** antarmuka simulasi mobile app, analisis risiko, dan graph analytics.

## 2. Hybrid Detection

### Rule-Based Score

Rule score dipakai untuk memberi alasan yang mudah dibaca manusia, misalnya shared device, shared IP, atau referral ring.

### Machine Learning Probability

Model ML membaca feature yang tersedia pada stage saat itu.

- `new user registration` memakai model new-user
- `existing user` dan flow full memakai model full / legacy

## 3. Inference Flow

Frontend membangun payload dari halaman simulasi, lalu mengirimnya ke proxy route:

- `POST /api/inference/registration`
- `POST /api/inference/login`
- `POST /api/inference/checkout`
- `POST /api/inference/transaction-completed`
- `POST /api/inference/journey`

Proxy route meneruskan request ke backend lifecycle endpoint dan menampilkan error backend apa adanya agar debugging lebih mudah.

## 4. Core Backend Endpoints

### Dashboard

- `GET /api/stats/overview`
- `GET /api/users`
- `GET /api/user/{uid}`

### Chatbot

- `POST /api/chat`

## 5. Catatan Integrasi

- Frontend inference kini membedakan jalur new-user dan existing-user.
- New-user registration memakai feature registrasi yang memang tersedia saat signup.
- Existing-user tetap bisa memakai ABT dan histori yang lebih lengkap.
- Chatbot menggunakan Groq saat API key tersedia dan fallback rule-based saat tidak tersedia.


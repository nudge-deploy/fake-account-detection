<!--
Purpose: Document the hybrid chatbot architecture and fallback behavior.
Used by: Developers, reviewers, and readers understanding chatbot responses.
Main dependencies: backend chatbot service, LLM provider, regex/rule-based handlers.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# 08. Chatbot Hybrid Architecture Design

Aplikasi deteksi penipuan ini dilengkapi dengan Asisten AI (*Chatbot*) cerdas yang berfungsi membantu analis dalam membaca data fraud secara interaktif. Sistem chatbot ini dibangun menggunakan arsitektur **Hybrid** (LLaMA-3.1 + Regex Fallback).

## 1. Arsitektur Dual-Mode

Chatbot beroperasi di dua mode yang bergantian secara mulus (*graceful degradation*) bergantung pada ketersediaan API Key Eksternal.

### A. Mode AI Canggih (LLM)
Jika sistem mendeteksi keberadaan variabel `GROQ_API_KEY` di *environment*, backend akan menggunakan Groq Cloud untuk memanggil model **LLaMA-3.1 (70B/8B)**.
- **Konteks Dinamis**: Chatbot disuntikkan dengan instruksi sistem (*System Prompt*) yang menjelaskan tentang aturan *fraud* V-TEKI, definisi *ABT (Analytical Base Table)*, dan wewenangnya.
- **Natural Language Understanding**: Mampu menjawab pertanyaan yang sangat analitis, tidak beraturan, atau bahkan yang bersifat opini analitik seperti *"Apakah wajar jika satu perangkat dipakai 5 akun?"*
- **Streaming Response**: Mendukung respons asinkron (*streaming*) layaknya ChatGPT.

### B. Mode Fallback (Rule-Based / Regex)
Jika `GROQ_API_KEY` tidak tersedia, aplikasi tidak akan mogok (*crash*), melainkan beralih ke mesin pemrosesan bahasa berbasis pola (*Regex-based parser*).
- **Deteksi Niat (Intent Detection)**: Backend memindai pesan masuk untuk mencari kata kunci (contoh: "kenapa", "alasan", "U001", "statistik", "jumlah").
- **Ekstraksi Entitas**: Menggunakan *Reguler Expressions* (Regex) untuk mengekstrak ID pengguna, misalnya: `(USR\d+)`.
- **Query Langsung ke Data**: Setelah ID ditemukan, mesin akan mencari skor dan alasan *fraud* dari memori lokal (ABT), lalu menyusun balasan berbasis teks *template*.
- Meskipun kaku, mode ini menjamin bahwa fungsi dasar "Investigasi Pengguna Spesifik via Chat" tetap menyala kapanpun.

## 2. Diagram Alir Komunikasi (Flow)
1. **Frontend (React)** mengirim `POST /api/chat` berisi riwayat percakapan.
2. **Backend (FastAPI)** memeriksa ketersediaan Groq Client.
3. Jika *Client* ada: Meneruskan riwayat ke server Groq dan mengembalikan teks hasil inferensi LLM.
4. Jika *Client* tidak ada: 
   - Memecah pesan terakhir pengguna menjadi susunan kata.
   - Mencocokkannya dengan *Dictionary of Intents*.
   - Jika *Intent* = `User Query`, panggil fungsi *User Search*.
   - Bangun *string* statis dan kembalikan ke Frontend.

## 3. Keunggulan Arsitektur
Desain *Hybrid* ini dipilih karena sangat cocok untuk aplikasi portofolio skala *enterprise* yang membutuhkan tingkat keandalan (*reliability*) 100%. Tim analis tidak akan pernah kehilangan kapabilitas pengecekan data dasar, sembari tetap menikmati kecerdasan *Generative AI* jika infrastruktur mendukung.

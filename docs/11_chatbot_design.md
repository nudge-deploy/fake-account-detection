<!--
Purpose: Document the hybrid chatbot architecture and fallback behavior.
Used by: Developers, reviewers, and readers understanding chatbot responses.
Main dependencies: backend chatbot service, Groq client, rule-based handlers, ABT lookup.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# 08. Chatbot Hybrid Architecture Design

Aplikasi deteksi penipuan ini dilengkapi dengan asisten AI chatbot yang membantu analis membaca data fraud secara interaktif. Sistem chatbot dibangun dengan arsitektur hybrid: Groq Llama 3.1 + fallback rule-based.

## 1. Arsitektur Dual-Mode

### A. Mode AI Canggih (LLM)

Jika variabel `GROQ_API_KEY` tersedia di environment, backend akan memakai Groq Cloud untuk memanggil model `llama-3.1-8b-instant`.

Mode ini dipakai untuk pertanyaan yang butuh penjelasan natural, penalaran, dan ringkasan kontekstual.

### B. Mode Fallback (Rule-Based / Regex)

Jika `GROQ_API_KEY` tidak tersedia, aplikasi tidak berhenti. Backend beralih ke parser rule-based.

Fallback ini melakukan:

- deteksi intent sederhana
- ekstraksi entity seperti `USR12345`
- lookup data dari ABT / hasil inferensi
- menyusun jawaban template yang konsisten

## 2. Alur Komunikasi

1. Frontend mengirim `POST /api/chat`.
2. Backend memeriksa apakah Groq client tersedia.
3. Jika tersedia, request diteruskan ke Groq.
4. Jika tidak tersedia, backend memakai intent parser dan lookup lokal.
5. Jawaban dikembalikan ke frontend dalam format teks.

## 3. Kenapa Pendekatan Ini Dipakai

Pendekatan hybrid membuat chatbot tetap berguna walaupun API LLM tidak aktif. Dengan begitu, pertanyaan dasar seperti ringkasan risiko user, alasan fraud, atau referensi graph tetap bisa dijawab.


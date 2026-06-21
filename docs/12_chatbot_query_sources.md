<!--
Purpose: Map chatbot query types to their data source and fallback logic.
Used by: Developers, reviewers, and documentation writers explaining chatbot behavior.
Main dependencies: backend/app/services/chatbot_service.py, backend/app/services/model_service.py, backend/app/services/graph_service.py.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Chatbot Query -> Data Source Mapping

Dokumen ini menjelaskan dari mana jawaban chatbot berasal saat **bukan LLM**.  
Intinya, chatbot punya 3 sumber utama:

1. `ModelService` untuk data ABT, detail user, statistik, dan top risk.
2. `GraphService` untuk relasi graph dan koneksi antar akun.
3. Rule-based template/handler untuk penjelasan konsep umum.

## Ringkasan Alur

```text
User message
  -> rule-based parsing di chatbot_service.py
  -> masuk ke handler yang sesuai
  -> ambil data dari ModelService / GraphService / template teks
  -> jika GROQ_API_KEY ada, LLM merapikan jawaban
  -> jika tidak ada, fallback rule-based dipakai langsung
```

## Tabel Query -> Sumber Data

| Query / Intent | Contoh Pertanyaan | Sumber Data | Cara Jawab | Catatan |
|---|---|---|---|---|
| Detail user | `Detail U01519`, `Kenapa user USR00010 mencurigakan?` | `ModelService.get_user_details()` dari ABT + users | Ambil data user, risk score, ML probability, label asli, dan reasons | Ini jawaban berbasis data nyata, bukan definisi umum. |
| Top risk users | `Tampilkan top 10 akun paling mencurigakan` | `ModelService.get_top_risk_users()` | Ambil daftar user dengan risk score / ML probability tertinggi | Dipakai untuk ranking akun berisiko. |
| Statistik umum | `Berapa banyak akun high risk?` | `ModelService.get_overview_stats()` atau `df_merged` | Hitung total user, high/medium/low risk, fake/normal | Jawaban angka berasal dari dataframe / query data. |
| Common fraud pattern | `Apa pola fraud paling umum?` | `df_merged['ftype'].value_counts()` | Hitung distribusi `ftype` di ABT | Sumber utama adalah label ground truth dataset. |
| Device cluster | `Show fraud cluster related to device DVC001` | `GraphService.raw_edges` dan `GraphService.raw_nodes` | Cari node device lalu ambil user yang terhubung | Ini graph-based answer. |
| Shared device | `Device sharing yang paling banyak` | `GraphService.raw_edges` | Hitung device yang dipakai banyak user | Biasanya dari edge `uses_device`. |
| Shared address | `Alamat yang dipakai akun palsu` | `GraphService.raw_edges` + risk category user | Cari edge alamat lalu filter user berisiko tinggi | Dipakai untuk shared address abuse. |
| Shared payment | `Akun mana yang share payment?` | `GraphService.raw_edges` | Hitung payment yang terhubung ke banyak user | Dipakai untuk shared payment abuse. |
| Referral ring | `Apa referral ring?`, `User dengan referral ring tinggi` | `ModelService` + `GraphService` + `df_merged['ref_ring']` | Ambil ring score, referral count, dan koneksi graph | Biasanya gabungan data referral dan graph. |
| Voucher farming | `Jelaskan voucher farming` | Template rule-based `._handle_voucher_farming_concept()` | Jawab definisi umum dan sebut fitur pendukung | Ini penjelasan konsep, bukan query data khusus. |
| Shared device concept | `Apa itu shared device abuse?` | Template rule-based `._handle_shared_device_concept()` | Jawab definisi umum | Tidak selalu perlu query data. |
| Shared address concept | `Apa itu shared address abuse?` | Template rule-based `._handle_shared_address_concept()` | Jawab definisi umum | Penjelasan konseptual. |
| Shared payment concept | `Apa itu shared payment abuse?` | Template rule-based `._handle_shared_payment_concept()` | Jawab definisi umum | Penjelasan konseptual. |
| Referral ring concept | `Apa itu referral ring?` | Template rule-based `._handle_referral_ring_concept()` | Jawab definisi umum | Penjelasan konseptual. |
| Default general question | `Halo`, `bantu jelaskan sistemnya` | `_handle_default_fallback()` | Jawaban template umum tentang kemampuan assistant | Dipakai kalau query tidak cocok dengan pola lain. |

## Sumber Data per Komponen

| Komponen | Mengambil Dari | Isi Data |
|---|---|---|
| `ModelService.df_merged` | ABT lokal + users CSV atau Supabase fallback | Fitur final per user, risk score, risk category, ML prediction, label, dan profil user |
| `GraphService.raw_nodes` | `graph_nodes.json` | Node graph user/device/address/payment/IP/referral |
| `GraphService.raw_edges` | `graph_edges.json` | Edge graph seperti `uses_device`, `uses_address`, `uses_payment`, `uses_ip`, `referred_user` |
| Rule-based concept handlers | String template di `chatbot_service.py` | Penjelasan definisi/fungsi fitur |

## Catatan Penting

- Kalau pertanyaan berbentuk angka, daftar, atau detail user, chatbot biasanya membaca data nyata dari `ModelService` atau `GraphService`.
- Kalau pertanyaan berbentuk definisi, chatbot biasanya menjawab dari template rule-based.
- Kalau `GROQ_API_KEY` aktif, LLM dipakai hanya untuk merapikan jawaban dari konteks yang sudah dikumpulkan, bukan untuk mengganti sumber datanya.


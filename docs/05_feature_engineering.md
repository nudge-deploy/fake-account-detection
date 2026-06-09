<!--
Purpose: Define ABT feature names, formulas, and business interpretation.
Used by: Model reviewers, backend developers, and feature lineage audits.
Main dependencies: scripts/build_abt.py, data/abt/fake_account_abt.csv, models/feature_columns.json.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Fraud Detection Feature Engineering Documentation

## 1. Overview

Dokumen ini menjelaskan seluruh fitur yang dihasilkan oleh modul `build_abt.py` dan digunakan sebagai Analytics Base Table (ABT) untuk Fraud Detection, Multi-Account Detection, Voucher Abuse Detection, Referral Abuse Detection, dan Fraud Ring Detection.

Kontrak final ABT:
- `fake_account_abt.csv` berisi 10.000 baris dan 69 kolom total.
- 64 kolom menjadi input model dan disimpan urutannya di `models/feature_columns.json`.
- 5 kolom tidak masuk model karena merupakan metadata/label: `uid`, `fraud`, `ftype`, `risk_score`, `risk_cat`.
- Fitur graph aggregate (`degree`, `comp_size`, `cluster`, `shared_ent`, dan shared counters) sudah menjadi bagian dari ABT final.

---

# 2. Identity Features

| Nama Fitur | Rumus Kode (Pandas / SQL Logic) | Definisi Teknis | Interpretasi Akhir (Bisnis) |
|------------|---------------------------------|-----------------|-----------------------------|
| email_len | len(email) | Panjang email | Email tidak wajar dapat mengindikasikan akun sintetis |
| email_num_ratio | digit_count / username_length | Rasio angka pada username email | Tinggi mengindikasikan email hasil generate otomatis |
| email_rand | calc_entropy(username) | Entropy karakter email | Semakin tinggi semakin acak |
| disp_email | domain in disposable_list | Apakah email disposable | Akun sekali pakai |
| phone_score | calc_phone_pattern_score(phone) | Skor pola nomor telepon | Tinggi menunjukkan pola tidak natural |

## 2.1 Detail Perhitungan `email_rand` / Email Entropy

`email_rand` dipakai untuk membaca tingkat keacakan username email. Yang dihitung bukan seluruh email, tetapi hanya bagian sebelum `@`.

Contoh:

```text
email lengkap  = x9q7m2z@gmail.com
username email = x9q7m2z
domain email   = gmail.com
yang dihitung  = x9q7m2z
```

Alasannya: domain seperti `gmail.com`, `yahoo.com`, atau domain disposable tidak menggambarkan pola nama akun. Pola yang lebih penting ada pada username.

### Formula

```text
email_rand = -sum(p * log2(p))
```

Keterangan:

| Komponen | Arti |
|---|---|
| `p` | Probabilitas kemunculan setiap karakter di username email. |
| `log2(p)` | Log basis 2 dari probabilitas karakter. |
| `-sum(...)` | Menjumlahkan seluruh kontribusi karakter lalu dibuat positif. |

Kode konsep:

```python
def calc_entropy(text):
    if not text or not isinstance(text, str):
        return 0.0
    text_len = len(text)
    counts = Counter(text)
    entropy = 0.0
    for count in counts.values():
        p = count / text_len
        entropy -= p * math.log2(p)
    return entropy
```

### Analogi Sederhana

Bayangkan username email seperti isi kantong permen.

- Kalau semua permen warnanya sama, variasinya rendah.
- Kalau warnanya banyak dan seimbang, variasinya tinggi.

Username `aaaaaa` seperti kantong berisi satu warna saja. Entropy rendah.
Username `x9q7m2z` seperti kantong berisi banyak warna berbeda. Entropy tinggi.

### Contoh Pengerjaan 1: Username Repetitif

```text
username = aaaa
panjang  = 4
```

Kemunculan karakter:

| Karakter | Jumlah | Probabilitas |
|---|---:|---:|
| a | 4 | 4/4 = 1 |

Perhitungan:

```text
entropy = -(1 * log2(1))
entropy = -(1 * 0)
entropy = 0
```

Interpretasi:

```text
email_rand = 0
```

Artinya username sangat repetitif dan tidak acak.

### Contoh Pengerjaan 2: Username Bervariasi

```text
username = abcd
panjang  = 4
```

Kemunculan karakter:

| Karakter | Jumlah | Probabilitas |
|---|---:|---:|
| a | 1 | 1/4 = 0.25 |
| b | 1 | 1/4 = 0.25 |
| c | 1 | 1/4 = 0.25 |
| d | 1 | 1/4 = 0.25 |

Perhitungan:

```text
entropy = -4 * (0.25 * log2(0.25))
entropy = -4 * (0.25 * -2)
entropy = 2
```

Interpretasi:

```text
email_rand = 2
```

Artinya username lebih bervariasi dibanding `aaaa`.

### Cara Membaca

| Username | Pola | Makna |
|---|---|---|
| `aaaaaa` | Repetitif | Entropy rendah |
| `andi123` | Nama + angka | Entropy sedang |
| `x9q7m2z` | Acak | Entropy tinggi |

Interpretasi bisnis:

```text
email_rand tinggi + disp_email = 1 + newuser_voucher tinggi
```

Kombinasi di atas lebih mencurigakan untuk voucher farming dibanding `email_rand` tinggi sendirian.

Catatan penting:

- Email acak tidak otomatis fraud.
- Orang asli juga bisa punya email acak.
- Fitur ini harus dibaca bersama promo, voucher, device, IP, payment, dan graph features.

---

# 3. Device Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| uniq_dev | nunique(device_id) | Jumlah device unik | Banyak device menunjukkan perpindahan perangkat |
| max_acc_dev | max(users_per_device) | Maks akun pada device yang sama | Indikasi multi-account |

---

# 4. Address Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| uniq_addr | nunique(address_id) | Jumlah alamat unik | Pola pengiriman tidak normal |
| max_acc_addr | max(users_in_address) | Maks akun pada alamat yang sama | Shared address abuse |

---

# 5. Payment Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| uniq_pay | nunique(payment_id) | Jumlah payment unik | Akun tidak stabil |
| max_acc_pay | max(users_on_payment) | Maks akun pada payment sama | Shared payment abuse |

---

# 6. Transaction Features

## Core Transaction

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| promo_ratio | voucher_usage_count / total_transactions | Rasio transaksi promo | Promo farming |
| reg2txn_min | first_txn - registration_date | Menit dari registrasi ke transaksi pertama | Akun dibuat untuk promo |
| newuser_voucher | sum(is_new_user_promo) | Penggunaan voucher user baru | Abuse promo user baru |

## Monthly Transaction Frequency

txn_f1m sampai txn_f6m

- txn_f1m = transaksi ≤ 30 hari
- txn_f2m = transaksi ≤ 60 hari
- txn_f3m = transaksi ≤ 90 hari
- txn_f4m = transaksi ≤ 120 hari
- txn_f5m = transaksi ≤ 150 hari
- txn_f6m = transaksi ≤ 180 hari

Interpretasi:
Semakin tinggi menunjukkan aktivitas transaksi semakin intens.

## Monthly Transaction Amount

amt_f1m sampai amt_f6m

Rumus:
sum(order_amount)

Interpretasi:
Total nominal transaksi pada window waktu tertentu.

## Monthly Average Amount

avg_amt1m sampai avg_amt6m

Rumus:
mean(order_amount)

Interpretasi:
Rata-rata nilai transaksi user.

## Promo Usage

promo_f1m sampai promo_f6m

Rumus:
sum(promo_discount)

Interpretasi:
Total diskon promo yang digunakan.

## Voucher Usage

voucher_f1m sampai voucher_f6m

Rumus:
count(voucher_id)

Interpretasi:
Frekuensi penggunaan voucher.

---

# 7. Login Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| max_acc_ip | max(users_on_ip) | Maks akun pada IP sama | Fraud ring indicator |
| login_v1h | Maks login dari 00:00 sampai 01:00 pada hari tersibuk user | Daily login frequency bucket 1h | Burst login setelah tengah malam |
| login_v2h | Maks login dari 00:00 sampai 02:00 pada hari tersibuk user | Daily login frequency bucket 2h | Burst login setelah tengah malam |
| login_v3h | Maks login dari 00:00 sampai 03:00 pada hari tersibuk user | Daily login frequency bucket 3h | Burst login setelah tengah malam |
| login_v4h | Maks login dari 00:00 sampai 04:00 pada hari tersibuk user | Daily login frequency bucket 4h | Burst login setelah tengah malam |
| login_v5h | Maks login dari 00:00 sampai 05:00 pada hari tersibuk user | Daily login frequency bucket 5h | Burst login setelah tengah malam |
| login_v6h | Maks login dari 00:00 sampai 06:00 pada hari tersibuk user | Daily login frequency bucket 6h | Burst login setelah tengah malam |
| login_v12h | Maks login dari 00:00 sampai 12:00 pada hari tersibuk user | Daily login frequency bucket 12h | Aktivitas tinggi paruh hari |
| login_v18h | Maks login dari 00:00 sampai 18:00 pada hari tersibuk user | Daily login frequency bucket 18h | Aktivitas tinggi sebelum malam |
| login_v24h | Maks total login harian user | Daily login frequency bucket 24h | Intensitas login harian |

---

# 8. Referral Features

| Nama Fitur | Rumus Kode | Definisi Teknis | Interpretasi Bisnis |
|------------|------------|-----------------|---------------------|
| ref_cnt | `count(referral_id)` group by `referrer_user_id` | Jumlah referral langsung yang dibuat oleh user | User terlalu banyak mengundang akun lain dapat menjadi indikasi referral farming |
| ref_ring | `cycle_size` atau `descendants / 2` | Skor struktur jaringan referral berdasarkan cycle atau jaringan turunan besar | Nilai tinggi menunjukkan referral ring, circular referral, atau jaringan akun terorganisir |

## 8.1 Detail Perhitungan `ref_cnt`

`ref_cnt` menghitung berapa banyak user lain yang diundang langsung oleh satu user.

Contoh data:

| referral_id | referrer_user_id | referred_user_id |
|---|---|---|
| REF001 | U001 | U002 |
| REF002 | U001 | U003 |
| REF003 | U001 | U004 |
| REF004 | U002 | U005 |

Hasil:

| user_id | ref_cnt |
|---|---:|
| U001 | 3 |
| U002 | 1 |
| U003 | 0 |
| U004 | 0 |
| U005 | 0 |

Interpretasi:

```text
U001 membuat 3 referral langsung.
```

## 8.2 Detail Perhitungan `ref_ring`

`ref_ring` membaca apakah user berada dalam struktur referral yang mencurigakan.

Graph referral dibentuk sebagai graph berarah:

```text
referrer_user_id -> referred_user_id
```

Contoh:

```text
U001 -> U002
```

Artinya `U001` mengundang `U002`. Arah hubungan penting, karena bukan berarti `U002` mengundang `U001`.

### Istilah Penting: `cycle` dan `descendant`

Sebelum membaca rumus `ref_ring`, ada dua istilah yang wajib dipahami.

#### 1. Apa itu `cycle`?

`cycle` adalah pola referral yang membentuk lingkaran. Artinya, jalur referral bisa berjalan dari satu user lalu kembali lagi ke user awal.

Contoh cycle:

```text
U001 -> U002 -> U003 -> U001
```

Cara bacanya:

```text
U001 mengundang U002
U002 mengundang U003
U003 mengundang U001
```

Karena jalurnya balik lagi ke `U001`, maka ini disebut cycle.

Analogi sederhana:

```text
A ngajak B, B ngajak C, C balik ngajak A.
```

Di sistem referral normal, pola seperti ini tidak wajar karena referral biasanya bergerak satu arah dari user lama ke user baru. Kalau ada lingkaran, sistem menganggap ini sebagai sinyal referral ring.

Jika cycle berisi 3 user:

```text
U001 -> U002 -> U003 -> U001
```

Maka:

| user_id | ref_ring |
|---|---:|
| U001 | 3 |
| U002 | 3 |
| U003 | 3 |

Angka `3` berasal dari panjang cycle, karena lingkarannya terdiri dari 3 user.

#### 2. Apa itu `descendant`?

`descendant` adalah semua user turunan yang berada di bawah jalur referral seorang user, baik langsung maupun tidak langsung.

Contoh:

```text
U001 -> U002
U001 -> U003
U002 -> U004
U003 -> U005
```

Descendant dari `U001` adalah:

```text
U002, U003, U004, U005
```

Jumlah descendant `U001`:

```text
4 user
```

Kenapa `U004` dan `U005` ikut dihitung padahal bukan referral langsung dari `U001`?

Karena mereka masih berada di bawah jalur referral `U001`.

Analogi sederhana:

```text
U001 = orang tua
U002 dan U003 = anak langsung
U004 dan U005 = cucu
```

Dalam konsep descendant, anak dan cucu sama-sama dihitung sebagai turunan.

Bedanya dengan `ref_cnt`:

| Istilah | Yang Dihitung | Contoh |
|---|---|---|
| `ref_cnt` | Referral langsung saja | U001 langsung mengundang U002 dan U003, maka `ref_cnt = 2`. |
| `descendant` | Semua turunan, langsung dan tidak langsung | U001 punya U002, U003, U004, U005 di bawah jaringannya, maka `descendants = 4`. |

Kenapa descendant dipakai untuk `ref_ring`?

Karena referral abuse tidak selalu berbentuk lingkaran. Kadang fraudster membuat pola pohon besar: satu akun utama mengundang beberapa akun, lalu akun turunan mengundang akun lain lagi.

Contoh pola pohon:

```text
U010 -> U011
U010 -> U012
U011 -> U013
U011 -> U014
U012 -> U015
```

Descendant dari `U010`:

```text
U011, U012, U013, U014, U015 = 5 user
```

Karena `descendants > 3`, maka sistem memberi skor:

```text
ref_ring = descendants / 2
ref_ring = 5 / 2
ref_ring = 2.5
```

Artinya, walaupun tidak ada cycle, `U010` tetap punya sinyal referral network besar.

Ringkasnya:

```text
cycle      = jaringan referral muter balik ke user awal
                  contoh: U001 -> U002 -> U003 -> U001

descendant = semua user turunan di bawah user tertentu
                  contoh: anak, cucu, cicit dalam referral tree
```

### Formula / Logic

```text
Jika user masuk cycle referral:
    ref_ring = panjang cycle

Jika user tidak masuk cycle tetapi descendants > 3:
    ref_ring = descendants / 2

Jika tidak memenuhi keduanya:
    ref_ring = 0
```

Kode konsep:

```text
ref_graph = nx.DiGraph()
ref_graph.add_edge(referrer_user_id, referred_user_id)

cycles = nx.simple_cycles(ref_graph)
cycle_membership[node] = panjang_cycle

Untuk setiap user:
  ring_score = cycle_membership.get(user, 0)
  jika ring_score == 0:
      descendants = jumlah semua user turunan dari user itu
      jika descendants > 3:
          ring_score = descendants / 2
```

### Analogi Sederhana

Bayangkan referral seperti pohon keluarga.

- `ref_cnt` hanya menghitung anak langsung.
- `ref_ring` melihat apakah struktur keluarganya membentuk lingkaran aneh atau jaringan turunan besar.

Referral normal biasanya satu arah:

```text
U001 -> U002 -> U003
```

Referral mencurigakan bisa membentuk lingkaran:

```text
U001 -> U002 -> U003 -> U001
```

### Contoh Pengerjaan 1: Cycle Referral

Data:

| referrer_user_id | referred_user_id |
|---|---|
| U001 | U002 |
| U002 | U003 |
| U003 | U001 |

Bentuk graph:

```text
U001 -> U002 -> U003
 ^              |
 |--------------|
```

Karena ada cycle berisi 3 user:

| user_id | ref_ring |
|---|---:|
| U001 | 3 |
| U002 | 3 |
| U003 | 3 |

Interpretasi bisnis:

```text
Referral normal biasanya tidak saling memutar.
Kalau membentuk lingkaran, ini sinyal referral abuse.
```

### Contoh Pengerjaan 2: Referral Tree Besar

Data:

```text
U010 -> U011
U010 -> U012
U010 -> U013
U010 -> U014
U011 -> U015
U012 -> U016
```

Descendants dari `U010`:

```text
U011, U012, U013, U014, U015, U016 = 6 user
```

Karena `descendants > 3`:

```text
ref_ring = descendants / 2
ref_ring = 6 / 2
ref_ring = 3.0
```

Interpretasi bisnis:

```text
Walaupun tidak membentuk cycle, jaringan turunan besar tetap bisa menjadi sinyal referral farming.
```

### Cara Membaca di Dashboard

| Kondisi | Makna |
|---|---|
| `ref_cnt = 3`, `ref_ring = 178` | User hanya mengundang 3 langsung, tetapi berada dalam jaringan referral sangat besar. Lebih mencurigakan. |
| `ref_cnt = 3`, `ref_ring = 0` | User mengundang beberapa orang, tetapi belum ada bukti cycle atau jaringan turunan besar. |
| `ref_cnt = 0`, `ref_ring = 0` | Tidak ada sinyal referral abuse dari fitur referral. |

Catatan:

- `ref_ring` tidak membaca device, payment, address, atau IP.
- User masih bisa fraud dari shared entity walaupun `ref_ring = 0`.
- `ref_ring` kuat jika dibaca bersama `degree`, `shared_ent`, dan shared counters.

---

# 9. Graph Features (Fraud Ring)

Graph features membaca hubungan antar akun berdasarkan entity yang dipakai bersama.

Entity berarti jejak, alat, atau data yang bisa menghubungkan beberapa user.

| Entity | Bahasa Awam | Contoh |
|---|---|---|
| Device | HP/perangkat | `DEV_D001` |
| Address | Alamat pengiriman | `ADDR_A001` |
| Payment | Alat pembayaran | `PAY_P001` |
| IP | Alamat jaringan/login | `IP_103.10.66.5` |

Secara sederhana:

```text
Kalau beberapa user memakai entity yang sama,
maka user-user itu dianggap punya hubungan.
```

Contoh:

```text
U001 pakai device D001
U002 pakai device D001
```

Maka terbentuk hubungan:

```text
U001 -- U002
```

## 9.1 Ringkasan Fitur Graph

| Nama Fitur Final | Rumus / Logic | Definisi Teknis | Interpretasi Bisnis |
|---|---|---|---|
| degree | `user_graph.degree(uid)` | Jumlah user lain yang terhubung langsung ke user ini karena berbagi entity | Semakin tinggi, semakin banyak akun lain yang punya jejak sama dengan user |
| comp_size | Ukuran connected component dari `nx.connected_components(user_graph)` | Jumlah user dalam komponen jaringan yang sama | Menunjukkan ukuran jaringan/ring tempat user berada |
| cluster | `len(nx.ego_graph(user_graph, uid))` | Jumlah node dalam ego network user, yaitu user itu sendiri dan tetangga langsungnya | Mengukur seberapa besar lingkungan lokal user |
| shared_ent | `shared_counts[uid]` | Total kejadian user berbagi entity dengan akun lain | Semakin tinggi, semakin banyak jejak bersama yang dimiliki user |
| shared_device_count | `shared_by_type['device'][uid]` | Jumlah koneksi user ke akun lain karena device yang sama | Sinyal shared device abuse / emulator / device farming |
| shared_address_count | `shared_by_type['address'][uid]` | Jumlah koneksi user ke akun lain karena alamat yang sama | Sinyal shared address abuse |
| shared_payment_count | `shared_by_type['payment'][uid]` | Jumlah koneksi user ke akun lain karena payment yang sama | Sinyal shared payment abuse / voucher farming |
| shared_ip_count | `shared_by_type['ip'][uid]` | Jumlah koneksi user ke akun lain karena IP login yang sama | Sinyal network abuse, bot cluster, atau shared WiFi/VPN |

## 9.2 Cara Kerja Graph Projection

Graph mentah awalnya berbentuk user ke entity:

```text
User -> Device
User -> Address
User -> Payment
User -> IP
```

Lalu dibuat user-user projection:

```text
Jika dua user berbagi entity yang sama,
mereka dihubungkan menjadi user -- user.
```

Kode konsep:

```text
user_graph = nx.Graph()
shared_counts = Counter()
shared_by_type = {
    "device": Counter(),
    "address": Counter(),
    "payment": Counter(),
    "ip": Counter()
}

Untuk setiap entity:
  ambil semua user yang memakai entity itu
  jika jumlah user <= 1, skip
  jika jumlah user > 50, skip
  hubungkan semua pasangan user
  tambah shared_counts dan shared_by_type
```

Kenapa entity dengan user `<= 1` di-skip?

```text
Kalau entity hanya dipakai 1 user, entity itu tidak membuktikan hubungan dengan akun lain.
```

Kenapa entity dengan user `> 50` di-skip?

```text
Kalau entity dipakai terlalu banyak user, kemungkinan itu entity umum seperti IP publik, NAT kantor, kampus, atau WiFi umum.
Kalau tetap dihitung, graph bisa terlalu padat dan menghasilkan false connection.
```

## 9.3 Analogi Sederhana

Bayangkan user adalah orang, dan entity adalah barang yang mereka pakai bersama.

- Kalau 2 orang memakai HP yang sama, mereka punya hubungan.
- Kalau 2 orang memakai alamat pengiriman yang sama, mereka punya hubungan.
- Kalau 2 orang memakai kartu/rekening/payment yang sama, mereka punya hubungan.
- Kalau 2 orang login dari IP yang sama, mereka punya hubungan.

Semakin banyak hubungan dan semakin besar kelompoknya, semakin kuat sinyal bahwa akun-akun itu bukan akun independen.

## 9.4 Detail Setiap Fitur

### `degree`

```text
degree = jumlah user lain yang terhubung langsung dengan user ini
```

Contoh:

```text
U001 -- U002
U001 -- U003
```

Maka:

```text
degree U001 = 2
```

Interpretasi:

```text
U001 terhubung langsung ke 2 akun lain karena berbagi entity.
```

### `comp_size`

```text
comp_size = jumlah user dalam satu jaringan besar yang masih tersambung
```

Contoh:

```text
U001 -- U002 -- U003 -- U004
```

Walaupun `U001` tidak langsung terhubung ke `U004`, semuanya masih satu jaringan.

Maka:

```text
comp_size U001 = 4
comp_size U002 = 4
comp_size U003 = 4
comp_size U004 = 4
```

Interpretasi:

```text
User berada dalam jaringan/ring berisi 4 akun.
```

### `cluster`

```text
cluster = jumlah user dalam ego network
```

Ego network adalah user itu sendiri + tetangga langsungnya.

Contoh:

```text
U002
 |
U001 -- U003
```

Untuk `U001`:

```text
cluster = U001 + U002 + U003 = 3
```

Interpretasi:

```text
Lingkungan dekat U001 berisi 3 akun.
```

Perbedaan penting:

| Fitur | Yang Dilihat |
|---|---|
| `cluster` | Lingkungan dekat user saja |
| `comp_size` | Seluruh jaringan besar yang masih tersambung |

### `shared_ent`

```text
shared_ent = total semua koneksi shared entity
```

Kalau user berbagi device dan IP dengan akun yang sama, keduanya tetap dihitung.

Contoh:

```text
U001 berbagi device dengan U002 = +1
U001 berbagi IP dengan U002     = +1
U001 berbagi payment dengan U003 = +1
```

Maka:

```text
shared_ent U001 = 3
```

Interpretasi:

```text
U001 punya 3 jejak bersama dengan akun lain.
```

### `shared_device_count`

```text
shared_device_count = jumlah koneksi karena device yang sama
```

Contoh:

```text
U001 pakai D001
U002 pakai D001
```

Maka:

```text
shared_device_count U001 = 1
shared_device_count U002 = 1
```

Interpretasi:

```text
Ada indikasi akun dibuat/dipakai dari device yang sama.
```

### `shared_address_count`

```text
shared_address_count = jumlah koneksi karena alamat yang sama
```

Contoh:

```text
U001 pakai ADDR_A
U002 pakai ADDR_A
U003 pakai ADDR_A
```

Pasangan yang terbentuk:

```text
U001 -- U002
U001 -- U003
U002 -- U003
```

Maka untuk setiap user:

```text
shared_address_count = 2
```

Interpretasi:

```text
Banyak akun memakai alamat pengiriman yang sama.
Ini bisa normal untuk keluarga/kos, tetapi mencurigakan jika dikombinasikan dengan voucher/promo/payment/IP yang sama.
```

### `shared_payment_count`

```text
shared_payment_count = jumlah koneksi karena payment yang sama
```

Contoh:

```text
U001 pakai PAY_01
U002 pakai PAY_01
U003 pakai PAY_02
```

Maka:

```text
shared_payment_count U001 = 1
shared_payment_count U002 = 1
shared_payment_count U003 = 0
```

Interpretasi:

```text
Beberapa akun memakai alat pembayaran yang sama.
Ini kuat untuk membaca voucher farming, multi-account, atau payment abuse.
```

### `shared_ip_count`

```text
shared_ip_count = jumlah koneksi karena IP login yang sama
```

Contoh:

```text
U001 login dari IP_A
U002 login dari IP_A
U003 login dari IP_B
```

Maka:

```text
shared_ip_count U001 = 1
shared_ip_count U002 = 1
shared_ip_count U003 = 0
```

Interpretasi:

```text
Beberapa akun login dari jaringan yang sama.
Perlu hati-hati karena IP publik, WiFi kantor, kampus, kos, atau NAT bisa dipakai banyak user normal.
```

## 9.5 Contoh Pengerjaan Lengkap

Data input sederhana:

| user_id | device_id | address_id | payment_id | ip_address |
|---|---|---|---|---|
| U001 | D001 | A001 | P001 | IP_A |
| U002 | D001 | A002 | P002 | IP_A |
| U003 | D002 | A003 | P001 | IP_B |

Graph mentah:

```text
U001 -> DEV_D001
U002 -> DEV_D001
U001 -> PAY_P001
U003 -> PAY_P001
U001 -> IP_IP_A
U002 -> IP_IP_A
```

Karena berbagi entity:

```text
U001 terhubung dengan U002 karena shared device D001 dan shared IP IP_A
U001 terhubung dengan U003 karena shared payment P001
```

User-user projection:

```text
U002
 |
 |
U001 -- U003
```

Hasil fitur untuk `U001`:

| Feature | Nilai | Penjelasan |
|---|---:|---|
| degree | 2 | U001 terhubung ke U002 dan U003 |
| shared_device_count | 1 | U001 berbagi device D001 dengan U002 |
| shared_address_count | 0 | Tidak ada address yang sama |
| shared_payment_count | 1 | U001 berbagi payment P001 dengan U003 |
| shared_ip_count | 1 | U001 berbagi IP_A dengan U002 |
| shared_ent | 3 | Total shared entity: device + payment + IP |
| cluster | 3 | Ego network U001 berisi U001, U002, U003 |
| comp_size | 3 | Connected component berisi 3 user |

Hasil fitur untuk `U002`:

| Feature | Nilai | Penjelasan |
|---|---:|---|
| degree | 1 | U002 hanya terhubung ke U001 |
| shared_device_count | 1 | U002 berbagi device D001 dengan U001 |
| shared_address_count | 0 | Tidak ada address yang sama |
| shared_payment_count | 0 | U002 tidak berbagi payment |
| shared_ip_count | 1 | U002 berbagi IP_A dengan U001 |
| shared_ent | 2 | Total shared entity: device + IP |
| cluster | 2 | Ego network U002 berisi U002 dan U001 |
| comp_size | 3 | Tetap 3 karena U002 masih satu jaringan dengan U001 dan U003 |

## 9.6 Cara Membaca Kasus Nyata

Contoh:

```text
shared_payment_count = 4
max_acc_pay = 5
```

Artinya user punya payment yang dipakai bersama beberapa akun lain. Ini kuat untuk shared payment abuse.

Contoh:

```text
shared_ip_count = 100
degree = 100
```

Artinya user terkoneksi ke banyak akun melalui IP/entity. Ini mencurigakan, tetapi harus dicek apakah IP tersebut public/NAT atau benar-benar cluster fraud.

Contoh:

```text
ref_ring = 178
degree = 103
```

Artinya user punya pola referral besar dan juga terhubung ke banyak akun di graph. Ini lebih kuat daripada hanya salah satu fitur saja.

## 9.7 Ringkasan Cara Baca Graph Feature

| Jika Nilai Tinggi Pada | Kemungkinan Makna |
|---|---|
| degree | User terhubung ke banyak akun lain |
| comp_size | User berada dalam jaringan besar |
| cluster | Lingkungan dekat user ramai/terpusat |
| shared_ent | Banyak jejak bersama dengan akun lain |
| shared_device_count | Banyak hubungan karena device yang sama |
| shared_address_count | Banyak hubungan karena alamat yang sama |
| shared_payment_count | Banyak hubungan karena alat pembayaran yang sama |
| shared_ip_count | Banyak hubungan karena IP yang sama |

Catatan:

- Satu fitur tinggi tidak otomatis berarti fraud.
- Fraud lebih kuat jika beberapa fitur saling mendukung.
- Graph feature bagus untuk mencari hubungan antar akun.
- Entity terlalu umum seperti IP publik besar bisa menyebabkan false positive, maka ada filter super node.

---

# 10. Rule Based Risk Scoring

## Scoring Rules

| Kondisi | Skor |
|----------|------|
| max_acc_dev > 5 | +40 |
| max_acc_dev > 2 | +15 |
| max_acc_addr > 5 | +20 |
| max_acc_ip > 5 | +15 |
| login_v1h > 10 | +40 |
| promo_ratio > 0.8 | +15 |
| reg2txn_min < 30 | +15 |
| newuser_voucher > 2 | +10 |

Maximum score = 100

## Risk Category

| Score | Category |
|---------|---------|
| 0 - 30 | Low |
| 31 - 60 | Medium |
| > 60 | High |

---

# 11. Output Dataset

Output file:

data/abt/fake_account_abt.csv

Total Feature:
63 Feature

Dataset ini akan digabung dengan Graph Features untuk membentuk Final Training Dataset Fraud Graph Ring Detection.

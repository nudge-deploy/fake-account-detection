# Fake Account Detection System — Dokumentasi Teknis Lengkap

> Platform deteksi akun palsu untuk Alfagift, mencakup pipeline data sintetik, feature engineering, model ML, rule-based scoring, graph analytics, dan deployment.

---

## Daftar Isi

1. [Arsitektur Sistem](#1-arsitektur-sistem)
2. [Generasi Data Sintetik](#2-generasi-data-sintetik)
3. [Penjahitan Data (ABT Building)](#3-penjahitan-data-abt-building)
4. [Feature Engineering](#4-feature-engineering)
5. [Graph Feature Building](#5-graph-feature-building)
6. [Model Training](#6-model-training)
7. [Rule-Based Scoring Engine](#7-rule-based-scoring-engine)
8. [Inference Pipeline](#8-inference-pipeline)
9. [Graph Analytics & Visualisasi](#9-graph-analytics--visualisasi)
10. [API Reference](#10-api-reference)
11. [Deployment](#11-deployment)

---

## 1. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA PIPELINE                            │
│                                                                 │
│  generate_data.py → data/raw/*.csv                             │
│         ↓                                                       │
│  build_graph.py → graph_nodes.json, graph_edges.csv            │
│         ↓                                                       │
│  extract_graph_features.py → user_graph_features.csv           │
│         ↓                                                       │
│  build_abt.py → data/abt/fake_account_abt.csv (ABT)           │
│         ↓                                                       │
│  train_model.py → models/existing_customer/model.pkl           │
│  train_new_user_model.py → models/new_customer/model.pkl       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      INFERENCE RUNTIME                          │
│                                                                 │
│  Event Payload (registration/login/checkout/transaction)        │
│         ↓                                                       │
│  feature_builder.py → Feature Vector (stage-masked)            │
│         ↓                          ↓                           │
│  ML Model (XGBoost/LR)      scoring.py (Rule Engine)          │
│         ↓                          ↓                           │
│  ml_probability             rule_score + critical_trigger      │
│         └──────────────────────────┘                           │
│                       ↓                                         │
│              compute_final_risk()                               │
│              → HIGH / MEDIUM / LOW                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        TECH STACK                               │
│                                                                 │
│  Backend : FastAPI + Uvicorn (Python 3.11)                     │
│  Frontend: Next.js 14 (App Router, TypeScript)                 │
│  Graph   : react-force-graph-2d (ForceGraph2D)                 │
│  Charts  : Recharts                                             │
│  ML      : scikit-learn, XGBoost                               │
│  Infra   : Docker, Nginx, Let's Encrypt SSL, Vercel            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Generasi Data Sintetik

**Script:** `scripts/generate_data.py`  
**Output:** `data/raw/*.csv` (11 tabel)

### Tabel yang Dihasilkan

| Tabel | Deskripsi | Jumlah Baris |
|-------|-----------|--------------|
| `users.csv` | Profil pengguna | 10.000 |
| `devices.csv` | Perangkat yang digunakan | ~8.000 |
| `user_devices.csv` | Mapping user ↔ device | ~12.000 |
| `addresses.csv` | Alamat pengiriman | ~15.000 |
| `user_addresses.csv` | Mapping user ↔ alamat | ~18.000 |
| `payments.csv` | Metode pembayaran | ~12.000 |
| `user_payments.csv` | Mapping user ↔ payment | ~14.000 |
| `transactions.csv` | Riwayat transaksi | ~230.000 |
| `login_sessions.csv` | Riwayat login | ~80.000 |
| `referrals.csv` | Kode referral | ~5.000 |
| `fraud_labels.csv` | Label ground truth | 10.000 |

### Distribusi Fraud

| Label | Jumlah | Persentase |
|-------|--------|------------|
| Normal | 7.000 | 70% |
| Fake / Fraud | 3.000 | 30% |

### Tipe Fraud yang Disimulasikan

| Kode | Deskripsi |
|------|-----------|
| `shared_device_abuse` | Banyak akun berbagi satu perangkat |
| `shared_address_abuse` | Banyak akun berbagi satu alamat |
| `shared_payment_abuse` | Banyak akun berbagi satu metode bayar |
| `voucher_farming` | Klaim voucher new user berulang |
| `referral_abuse` | Membuat jaringan referral palsu |

### Realisme Data

Generator menggunakan data referensi Indonesia asli:

- **Nomor telepon:** Prefix operator Indonesia (Telkomsel 45%, Indosat 20%, XL 15%, Tri 10%, Smartfren 5%)
- **Model HP:** Samsung Galaxy A-series (35%), Xiaomi/Redmi (25%), OPPO A-series (20%), Vivo Y-series (10%), Realme (10%)
- **Metode pembayaran:** E-wallet (45%), transfer bank (25%), QRIS (15%), debit (8%), COD (5%), kartu kredit (2%)
- **Kategori produk & harga:** Groceries (Rp 8K–80K), Electronics (Rp 150K–2M), dll
- **Locale:** Faker `id_ID` untuk nama, kota, provinsi Indonesia

---

## 3. Penjahitan Data (ABT Building)

**Script:** `scripts/build_abt.py`  
**Output:** `data/abt/fake_account_abt.csv` (Analytical Base Table)

### Alur Penjahitan

```
users.csv ──────────────────────────────────────────────────────┐
user_devices.csv + devices.csv ─→ device sharing features       │
user_addresses.csv ─────────────→ address sharing features      │
user_payments.csv ──────────────→ payment sharing features      │
login_sessions.csv ─────────────→ login frequency features      │
transactions.csv ───────────────→ transaction behavior features  │
referrals.csv ──────────────────→ referral network features     │
fraud_labels.csv ───────────────→ label (fraud, ftype)          │
user_graph_features.csv (opt) ──→ graph topology features       │
                                                                  │
                    ↓ LEFT JOIN semua ke users.uid               │
                                                                  │
              fake_account_abt.csv (1 baris per user)  ◄────────┘
```

### Output ABT

- **Dimensi:** 10.000 baris × 69 kolom
- **Granularity:** 1 baris = 1 user
- **Key:** `uid`

---

## 4. Feature Engineering

Total **64 fitur** dibagi menjadi 5 grup:

### 4.1 Identity Features (5 fitur)

| Fitur | Cara Hitung | Tujuan |
|-------|-------------|--------|
| `email_len` | `len(email)` | Email sangat panjang/pendek = anomali |
| `email_num_ratio` | `digits / len(email_name)` | Banyak angka = email bot |
| `email_rand` | Shannon entropy dari nama email | Entropy tinggi = karakter acak |
| `disp_email` | `1` jika domain ∈ {mailinator.com, yopmail.com, tempmail.com} | Email sekali pakai |
| `phone_score` | `(1 - unique_ratio) × 0.7 + (consecutive / len) × 0.3` | Pola nomor HP mencurigakan |

**Rumus Shannon Entropy:**
```
H = -Σ (p_i × log2(p_i))
```
Nilai tinggi = karakter bervariasi → email lebih random (bot-like).

### 4.2 Device Sharing Features (3 fitur)

| Fitur | Deskripsi |
|-------|-----------|
| `uniq_dev` | Jumlah device unik milik user |
| `max_acc_dev` | Maks akun lain yang pakai device yang sama |
| `shared_device_count` | `max_acc_dev - 1` |

### 4.3 Address & Payment Sharing (6 fitur)

| Fitur | Deskripsi |
|-------|-----------|
| `uniq_addr` | Jumlah alamat unik |
| `max_acc_addr` | Maks akun yang pakai alamat yang sama |
| `shared_address_count` | `max_acc_addr - 1` |
| `uniq_pay` | Jumlah payment method unik |
| `max_acc_pay` | Maks akun yang pakai payment yang sama |
| `shared_payment_count` | `max_acc_pay - 1` |

### 4.4 Login Frequency Features (11 fitur)

Login dihitung per jendela waktu:

| Fitur | Window |
|-------|--------|
| `max_acc_ip` | Maks akun yang login dari IP yang sama |
| `login_v1h` | Login dalam 1 jam terakhir |
| `login_v2h` – `login_v6h` | Login dalam 2–6 jam |
| `login_v12h`, `login_v18h` | Login dalam 12 dan 18 jam |
| `login_v24h` | Login dalam 24 jam |
| `shared_ip_count` | `max_acc_ip - 1` |

### 4.5 Transaction Behavior Features (39 fitur)

Per jendela waktu f1m (bulan ke-1) hingga f6m (bulan ke-6):

| Fitur | Deskripsi |
|-------|-----------|
| `txn_f1m` – `txn_f6m` | Jumlah transaksi |
| `amt_f1m` – `amt_f6m` | Total nilai transaksi (Rupiah) |
| `avg_amt1m` – `avg_amt6m` | Rata-rata nilai transaksi |
| `promo_f1m` – `promo_f6m` | Total diskon promo |
| `voucher_f1m` – `voucher_f6m` | Penggunaan voucher |
| `promo_ratio` | Total promo / total transaksi |
| `reg2txn_min` | Menit dari registrasi ke transaksi pertama |
| `newuser_voucher` | Jumlah klaim voucher new user |

### 4.6 Graph Topology Features (4 fitur)

Dihitung dari `extract_graph_features.py` menggunakan NetworkX:

| Fitur | Deskripsi |
|-------|-----------|
| `degree` | Jumlah koneksi langsung (device, IP, payment, address) |
| `cluster` | Koefisien clustering — seberapa saling terhubung tetangga |
| `comp_size` | Ukuran connected component yang berisikan user ini |
| `shared_ent` | Jumlah entitas yang dibagi dengan user lain |

### 4.7 Referral Network Features (2 fitur)

| Fitur | Deskripsi |
|-------|-----------|
| `ref_cnt` | Jumlah user yang direferral oleh user ini |
| `ref_ring` | Score ring referral — seberapa besar jaringan referral melingkar |

---

## 5. Graph Feature Building

**Scripts:** `scripts/build_graph.py` → `scripts/extract_graph_features.py`

### 5.1 Konstruksi Graf

Graf dibangun sebagai **undirected bipartite graph**:

```
User ←→ Device
User ←→ IP Address
User ←→ Payment Method
User ←→ Delivery Address
User ←→ User (via referral)
```

**Node Types:**

| Tipe | Warna UI | Deskripsi |
|------|----------|-----------|
| `user` | Merah/Kuning/Hijau (by risk) | Akun pengguna |
| `device` | Biru | Perangkat mobile |
| `ip` | Cyan | Alamat IP |
| `payment` | Pink | Metode pembayaran |
| `address` | Ungu | Alamat pengiriman |

### 5.2 Fraud Ring Detection

**Algoritma:** BFS Connected Components

```python
# Pseudocode
for each unvisited user_node:
    component = bfs(user_node, graph)
    user_nodes_in_component = [n for n in component if type(n) == 'user']
    if len(user_nodes_in_component) >= 2:
        fraud_rings.append(component)
```

Sebuah **fraud ring** = kelompok pengguna yang terhubung (langsung atau tidak langsung) melalui entitas yang dibagikan.

### 5.3 Ego-Network (User-Centric Graph)

Untuk investigasi satu user, digunakan BFS depth-limited:

```python
def _bfs_ego_network(start_id, hop_depth=2, max_nodes=1500):
    visited = {start_id}
    queue = [(start_id, 0)]
    while queue:
        node, depth = queue.pop(0)
        if depth >= hop_depth:
            continue
        for neighbor in adjacency[node]:
            if neighbor not in visited and len(visited) < max_nodes:
                visited.add(neighbor)
                queue.append((neighbor, depth + 1))
    return visited
```

**Konfigurasi hop depth:**
- **1-Hop:** Hanya entitas yang langsung terhubung ke user
- **2-Hop (default):** Entitas + user lain yang berbagi entitas yang sama
- **3-Hop:** Memperluas ke jaringan yang lebih jauh

### 5.4 Leakage Prevention saat Training

Masalah: Fitur cross-user (max_acc_dev, max_acc_ip, dll) dihitung dari semua 10.000 user. Jika test set masuk dalam perhitungan, model "melihat masa depan."

**Solusi yang diimplementasikan:**

```python
# 1. Split data DULU
X_train, X_test = stratified_split(abt, test_size=0.3)

# 2. Hitung entity counts HANYA dari training set
for entity_col in ['device_id', 'ip_address', 'payment_id', 'address_id']:
    entity_count_map = X_train.groupby(entity_col)['uid'].count().to_dict()
    X_train[f'max_acc_{entity}'] = X_train[entity_col].map(entity_count_map)

# 3. Test set lookup ke training graph (bukan test graph)
X_test[f'max_acc_{entity}'] = X_test[entity_col].map(entity_count_map).fillna(1)

# Safety cap: max 50 user per entitas (mencegah O(n²) edge explosion)
entity_count_map = {k: min(v, 50) for k, v in entity_count_map.items()}
```

---

## 6. Model Training

### 6.1 Existing Customer Model

**Script:** `scripts/train_model.py`  
**Model output:** `models/existing_customer/model.pkl`

#### Input
- **Data:** `data/abt/fake_account_abt.csv`
- **Fitur:** 64 fitur (semua kecuali uid, fraud, ftype, risk_cat, risk_score)
- **Label:** `fraud` (0/1)
- **Split:** 70% train / 30% test (stratified, random_state=42)

#### Pipeline

```
Raw Features (64)
      ↓
StandardScaler (z-score normalization)
      ↓
Classifier (XGBoost / Random Forest / Logistic Regression)
```

#### Hyperparameter Tuning (GridSearchCV)

| Model | Parameter Grid |
|-------|---------------|
| **Logistic Regression** | C: [0.001, 0.01, 0.1, 1.0], penalty: l2 |
| **Random Forest** | n_estimators: [50, 100], max_depth: [3, 5], min_samples_leaf: [5, 10] |
| **XGBoost** | learning_rate: [0.01, 0.05], max_depth: [2, 3], subsample: [0.7, 0.8], min_child_weight: [5, 10] |

- **CV:** 5-Fold StratifiedKFold
- **Scoring:** F1-Score
- **Champion:** Model dengan F1 tertinggi di test set

#### Hasil Training (Champion: XGBoost)

| Metrik | Nilai |
|--------|-------|
| Accuracy | 96.8% |
| Precision | 98.3% |
| Recall | 91.0% |
| **F1-Score** | **94.52%** |
| ROC-AUC | 99.62% |

#### Top 5 Fitur Penting (XGBoost)

| Fitur | Importance |
|-------|-----------|
| `login_v1h` | 0.1622 |
| `login_v24h` | 0.0959 |
| `shared_ip_count` | 0.0718 |
| `max_acc_ip` | 0.0670 |
| `shared_payment_count` | 0.0371 |

### 6.2 New Customer Model

**Script:** `scripts/train_new_user_model.py`  
**Model output:** `models/new_customer/model.pkl`

#### Perbedaan dengan Existing Customer

| Aspek | Existing Customer | New Customer |
|-------|-------------------|--------------|
| Fitur | 64 (full behavioral) | 10 (registration only) |
| Model | XGBoost (champion) | Logistic Regression |
| Data sumber | ABT lengkap | `new_user_training_data.csv` |
| Threshold prediksi | 0.50 | 0.80 (lebih ketat) |

#### 10 Fitur New Customer

```
email_len, email_num_ratio, email_rand, disp_email, phone_score,
full_name_len, is_email_verified, is_phone_verified,
age_years, registration_hour
```

#### Threshold Optimization

```python
def best_f1_threshold(model, X_val, y_val):
    thresholds = np.linspace(0.1, 0.9, 17)
    best_t, best_f1 = 0.5, 0.0
    for t in thresholds:
        y_pred = (model.predict_proba(X_val)[:,1] >= t).astype(int)
        f1 = f1_score(y_val, y_pred)
        if f1 > best_f1:
            best_f1, best_t = f1, t
    return best_t
```

#### Hasil Training

| Metrik | Nilai |
|--------|-------|
| **F1-Score** | **98.69%** |
| ROC-AUC | 99.96% |

---

## 7. Rule-Based Scoring Engine

**File:** `backend/app/inference/scoring.py`

Rule-based scoring berjalan **independen** dari ML model dan menghasilkan skor 0–100 berdasarkan aturan eksplisit yang dapat diaudit.

### 7.1 Prinsip Tiered Rules

Untuk fitur dengan threshold bertingkat, **hanya ambil poin tertinggi** (tidak dijumlahkan):

```python
# BENAR (tiered — hanya +50, bukan +10+30+50)
if max_acc_dev > 10:
    add(50, "Device sharing sangat ekstrem")
elif max_acc_dev > 5:
    add(30, "Device sharing ekstrem")
elif max_acc_dev > 2:
    add(10, "Device sharing mencurigakan")
```

### 7.2 Kategori & Aturan Scoring

#### A. Account Creation Abuse

| Kondisi | Poin | Keterangan |
|---------|------|------------|
| `disp_email = 1` | +15 | Email disposable |
| `reg2txn_min < 5` | +25 | Transaksi < 5 menit setelah registrasi |
| `reg2txn_min < 30` | +15 | Transaksi < 30 menit setelah registrasi |
| `newuser_voucher > 2` | +10 | Klaim voucher new user berlebihan |

#### B. Identity Sharing

| Fitur | Kondisi | Poin | Critical? |
|-------|---------|------|-----------|
| `max_acc_dev` | > 10 akun/device | +50 | ✓ |
| `max_acc_dev` | > 5 akun/device | +30 | |
| `max_acc_dev` | > 2 akun/device | +10 | |
| `max_acc_pay` | > 5 akun/payment | +60 | ✓ |
| `max_acc_pay` | > 2 akun/payment | +30 | |
| `max_acc_addr` | > 10 akun/alamat | +35 | |
| `max_acc_addr` | > 5 akun/alamat | +20 | |
| `max_acc_ip` | > 100 akun/IP | +40 | |
| `max_acc_ip` | > 50 akun/IP | +20 | |
| `max_acc_ip` | > 20 akun/IP | +10 | |

#### C. Behavioral Abuse

| Kondisi | Poin | Critical? |
|---------|------|-----------|
| `login_v1h > 20` | +60 | ✓ |
| `login_v1h > 10` | +40 | |
| `promo_ratio = 100%` AND `txn_count ≥ 5` | +15 | |
| `promo_ratio > 80%` AND `txn_count ≥ 5` | +10 | |

#### D. Network Fraud

| Kondisi | Poin | Critical? |
|---------|------|-----------|
| `ref_ring > 100` | +60 | ✓ |
| `ref_ring > 3` | +25 | |
| `ref_cnt ≥ 3` | +10 | |

**Total poin di-cap ke 100.**

### 7.3 Critical Trigger

Jika salah satu kondisi berikut terpenuhi, **Final Risk otomatis = HIGH** terlepas dari skor ML:

- `max_acc_pay > 5` (payment sharing sangat ekstrem)
- `max_acc_dev > 10` (device sharing sangat ekstrem)
- `ref_ring > 100` (referral ring ekstrem)
- `login_v1h > 20` (login anomali ekstrem)

### 7.4 Final Risk Decision

```python
def compute_final_risk(rule_score, ml_probability, critical_trigger):
    if critical_trigger or rule_score >= 70 or ml_probability >= 0.85:
        return "High"
    elif rule_score >= 40 or ml_probability >= 0.60:
        return "Medium"
    else:
        return "Low"
```

### 7.5 Conflict Detection

```python
# Sinyal tidak konsisten — perlu investigasi manual
conflict = (rule_score < 40 and ml_probability >= 0.85) or \
           (rule_score >= 70 and ml_probability < 0.60)
```

---

## 8. Inference Pipeline

### 8.1 Dua Mode Inference

| Mode | Endpoint | Data Source | Kasus Penggunaan |
|------|----------|-------------|------------------|
| **Real-time** | `POST /api/predict/lifecycle` | Event payload saja | Deteksi saat kejadian (registrasi, login, checkout) |
| **Investigation** | `GET /api/user/{uid}` | ABT historis (semua fitur) | Investigasi akun yang sudah ada |

### 8.2 Lifecycle Stages

```
REGISTRATION → LOGIN → CHECKOUT → TRANSACTION_COMPLETED
```

| Stage | Fitur Tersedia | Kepercayaan |
|-------|---------------|-------------|
| REGISTRATION | 14 fitur (identity + device) | Rendah |
| LOGIN | +11 fitur (IP + login frequency) | Sedang |
| CHECKOUT | +6 fitur (address + payment) | Baik |
| TRANSACTION_COMPLETED | +39 fitur (semua behavioral) | Penuh |

### 8.3 Feature Masking

Fitur yang belum tersedia di stage saat ini di-set ke 0:

```python
STAGE_FEATURES = {
    LifecycleStage.REGISTRATION: {
        'email_len', 'email_num_ratio', 'email_rand', 'disp_email',
        'phone_score', 'uniq_dev', 'max_acc_dev', 'shared_device_count',
        'ref_cnt', 'ref_ring', 'degree', 'comp_size', 'cluster', 'shared_ent'
    },
    LifecycleStage.LOGIN: {
        # + semua dari REGISTRATION
        'max_acc_ip', 'login_v1h', ..., 'login_v24h', 'shared_ip_count'
    },
    # dst...
}
```

### 8.4 Alur Prediksi Lengkap

```
Event Payload
      ↓
feature_builder.build(stage, customer_type, payload, uid)
      ↓
Feature Vector (64 atau 10 fitur, ter-mask sesuai stage)
      ↓
      ├─→ ML Model.predict_proba() → ml_probability
      │         ↓
      │   Threshold decision:
      │   - New user, registration:  threshold = 0.80
      │   - New user, post-reg:      threshold = 0.65
      │   - Existing user:           threshold = 0.50
      │
      └─→ explain_rule_score(features)
               ↓
          rule_score, breakdown, critical_trigger, raw_points
      
      ↓
compute_final_risk(rule_score, ml_probability, critical_trigger)
      ↓
InferenceResult {
    uid, stage, customer_type,
    ml_probability, ml_prediction,
    rule_score, risk_category,
    is_suspicious, is_fraud,
    primary_fraud_type, reasons,
    breakdown (per-rule contribution),
    critical_trigger, score_conflict,
    combined_risk_category
}
```

### 8.5 Fraud Type Classification

Sistem mengklasifikasikan tipe fraud berdasarkan kombinasi fitur yang dipicu:

| Fraud Type | Indikator Utama |
|-----------|-----------------|
| `shared_device_abuse` | `max_acc_dev > 2` |
| `shared_payment_abuse` | `max_acc_pay > 2` |
| `shared_address_abuse` | `max_acc_addr > 2` |
| `voucher_farming` | `newuser_voucher > 2` atau `promo_ratio > 0.8` |
| `referral_abuse` | `ref_ring > 3` atau `ref_cnt >= 3` |
| `login_anomaly` | `login_v1h > 10` |

### 8.6 Confidence Notes per Stage

```
REGISTRATION: "Kepercayaan terbatas — hanya identitas & device. 
               Pantau setelah login/transaksi."

LOGIN:        "Kepercayaan sedang — pola login & IP tersedia. 
               Skor dapat berubah setelah checkout."

CHECKOUT:     "Kepercayaan baik — alamat & pembayaran disertakan. 
               Konfirmasi setelah transaksi."

TRANSACTION:  "Kepercayaan penuh — semua fitur behavioral tersedia."
```

---

## 9. Graph Analytics & Visualisasi

**Library:** `react-force-graph-2d` v1.29.1  
**File:** `frontend/src/app/graph/page.tsx`

### 9.1 Arsitektur Komponen

```
GraphAnalyticsPage
├── Left Panel
│   ├── KPI Stats Bar (total_users, high_risk, fraud_rings, networks)
│   ├── Search Input (by user_id)
│   ├── Hop Depth Selector (1 / 2 / 3)
│   ├── Risk Category Filter
│   ├── Max Nodes Slider (50–1500)
│   ├── Risk Threshold Slider (0–100)
│   └── Color Legend
│
├── Center Canvas (ForceGraph2D)
│   ├── Node rendering (canvas)
│   ├── Edge rendering (canvas)
│   └── Interaction (click, hover, zoom, pan)
│
└── Right Panel
    ├── UserDetailPanel (ketika node user diklik)
    │   ├── Final Risk Verdict
    │   ├── Critical Trigger Banner (jika aktif)
    │   ├── Conflict Warning (jika rule ≠ ML)
    │   ├── Rule Score + ML Probability bars
    │   ├── Rule Breakdown by Category
    │   └── Graph Connections (device/IP/payment/address)
    │
    └── EntityDetailPanel (ketika node entitas diklik)
        ├── Entity type & ID
        ├── Total connections count
        └── Connected users list (clickable)
```

### 9.2 Node Rendering

```javascript
// User nodes — ukuran berdasarkan risk score
const radius = type === 'user'
    ? 5 + Math.min(9, riskScore / 10)  // 5–14px
    : 4;                                 // entitas: ukuran tetap

// Warna berdasarkan tipe dan risk
const colors = {
    user: {
        High:   '#ef4444',  // merah
        Medium: '#f59e0b',  // amber
        Low:    '#10b981',  // hijau
    },
    device:  '#3b82f6',  // biru
    ip:      '#06b6d4',  // cyan
    payment: '#ec4899',  // pink
    address: '#8b5cf6',  // ungu
};

// Selected node: tambahkan halo
if (node.id === selectedNodeId) {
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, radius + 4, 0, 2 * Math.PI);
    ctx.stroke();
}
```

### 9.3 Edge Rendering

```javascript
// Edge yang terhubung ke node terpilih: tebal + biru
const isHighlighted = selectedNodeId &&
    (link.source.id === selectedNodeId || link.target.id === selectedNodeId);

ctx.strokeStyle = isHighlighted ? '#3b82f6' : '#e2e8f0';
ctx.lineWidth   = isHighlighted ? 2.5 : 1;
```

### 9.4 KPI Stats (dari backend)

```json
{
    "total_users": 10000,
    "high_risk_users": 1096,
    "medium_risk_users": 2847,
    "low_risk_users": 6057,
    "fraud_rings": 1,
    "largest_ring_size": 10000,
    "shared_device_networks": 847,
    "shared_ip_networks": 1203,
    "shared_payment_networks": 612,
    "shared_address_networks": 934,
    "total_nodes": 33906,
    "total_edges": 128944
}
```

### 9.5 Frontend Filtering Logic

Filter diterapkan di sisi client setelah fetch data:

```typescript
const filteredNodes = nodes.filter(node => {
    if (node.type !== 'user') return true;  // entitas selalu ditampilkan
    if (highRiskOnly && node.risk_category !== 'High') return false;
    if (selectedFraudType && node.ftype !== selectedFraudType) return false;
    if (node.risk_score < riskThreshold) return false;
    return true;
});

// Hanya tampilkan edge jika kedua endpoint lolos filter
const filteredEdges = edges.filter(e =>
    filteredNodeIds.has(getId(e.source)) &&
    filteredNodeIds.has(getId(e.target))
);
```

---

## 10. API Reference

### Endpoints Utama

| Method | Path | Deskripsi |
|--------|------|-----------|
| `GET` | `/api/stats/overview` | Statistik ringkasan fraud |
| `GET` | `/api/users` | Daftar user dengan filter & pagination |
| `GET` | `/api/user/{uid}` | Detail investigasi satu user |
| `POST` | `/api/predict/lifecycle` | Real-time lifecycle inference |
| `GET` | `/api/graph` | Data graf (nodes + edges) |
| `GET` | `/api/graph/stats` | KPI statistik graf |
| `GET` | `/api/graph/entity/{entity_id}` | Detail entitas dalam graf |
| `GET` | `/api/risk/top-users` | Top user berdasarkan risk score |
| `POST` | `/api/chat` | AI Chatbot (via Groq) |

### Contoh Request: Lifecycle Inference

```bash
curl -X POST https://api.v-teki.com/api/predict/lifecycle \
  -H "Content-Type: application/json" \
  -d '{
    "stage": "registration",
    "customer_type": "new",
    "payload": {
        "email": "user123@gmail.com",
        "phone_number": "081234567890",
        "full_name": "Budi Santoso",
        "date_of_birth": "1995-05-15",
        "is_email_verified": true,
        "is_phone_verified": true
    }
  }'
```

### Contoh Response: User Investigation

```json
{
    "uid": "USR07424",
    "risk_score_rule_based": 80.0,
    "raw_rule_points": 80.0,
    "ml_probability": 0.917,
    "combined_risk_category": "High",
    "critical_trigger": true,
    "score_conflict": false,
    "model_type": "existing",
    "risk_score_breakdown": [
        {
            "category": "Identity Sharing",
            "label": "Payment sharing sangat ekstrem (6 akun/payment)",
            "points": 60,
            "value": 6
        },
        {
            "category": "Identity Sharing",
            "label": "IP sharing ekstrem (90 akun/IP)",
            "points": 20,
            "value": 90
        }
    ]
}
```

---

## 11. Deployment

### Infrastruktur

```
Internet
    ↓
fakeaccountdetection.v-teki.com (Vercel)
    ↓ NEXT_PUBLIC_API_URL
api.v-teki.com (Nginx + SSL/TLS)
    ↓ proxy_pass
localhost:8080 (Docker Container)
    ↓
FastAPI + Uvicorn (backend)
    ↓
models/ + data/ (volume mount)
```

### Docker Setup

**`Dockerfile`:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get install -y gcc g++
COPY backend/requirements.txt .
RUN pip install -r requirements.txt && pip install xgboost
COPY backend/ ./backend/
COPY data/ ./data/
COPY models/ ./models/
ENV PYTHONPATH=/app
CMD ["python3", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**`docker-compose.yml`:**
```yaml
services:
  backend:
    build: .
    restart: always
    ports: ["8080:8080"]
    volumes:
      - ./models:/app/models
      - ./data:/app/data
```

### Commands Deploy

```bash
# Di VPS
cd /opt/fake-account-detection
git pull origin main
docker-compose up -d --build

# Cek status
docker-compose ps
docker-compose logs -f backend
```

### SSL Certificate

Dikelola otomatis via **Let's Encrypt + Certbot**. Auto-renew setiap 90 hari:
```bash
certbot renew --dry-run  # test
certbot renew            # renew manual
```

### Environment Variables

| Variable | Lokasi | Nilai |
|----------|--------|-------|
| `NEXT_PUBLIC_API_URL` | Vercel | `https://api.v-teki.com` |
| `PYTHONPATH` | Docker | `/app` |

---

*Dokumentasi ini mencakup sistem pada versi dengan XGBoost champion model (F1=94.52%) dan weighted rule scoring engine.*

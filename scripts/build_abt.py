import os
import sys
import math
import numpy as np
import pandas as pd
import networkx as nx
from collections import Counter

# Konfigurasi path file
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
ABT_DIR = os.path.join(BASE_DIR, 'data', 'abt')
os.makedirs(ABT_DIR, exist_ok=True)

print("Memulai Feature Engineering & Pembuatan ABT...")

# Memuat CSV mentah
try:
    df_users = pd.read_csv(os.path.join(RAW_DIR, 'users.csv'))
    df_devices = pd.read_csv(os.path.join(RAW_DIR, 'devices.csv'))
    df_user_devices = pd.read_csv(os.path.join(RAW_DIR, 'user_devices.csv'))
    df_addresses = pd.read_csv(os.path.join(RAW_DIR, 'addresses.csv'))
    df_user_addresses = pd.read_csv(os.path.join(RAW_DIR, 'user_addresses.csv'))
    df_payments = pd.read_csv(os.path.join(RAW_DIR, 'payments.csv'))
    df_user_payments = pd.read_csv(os.path.join(RAW_DIR, 'user_payments.csv'))
    df_vouchers = pd.read_csv(os.path.join(RAW_DIR, 'vouchers.csv'))
    df_transactions = pd.read_csv(os.path.join(RAW_DIR, 'transactions.csv'))
    df_login_sessions = pd.read_csv(os.path.join(RAW_DIR, 'login_sessions.csv'))
    df_referrals = pd.read_csv(os.path.join(RAW_DIR, 'referrals.csv'))
    df_fraud_labels = pd.read_csv(os.path.join(RAW_DIR, 'fraud_labels.csv'))
    print("Berhasil memuat semua file CSV mentah.")
except Exception as e:
    print(f"Terjadi kesalahan saat memuat file CSV mentah: {e}")
    sys.exit(1)

# Memastikan tipe data timestamp (waktu) di-parsing dengan benar
df_users['registration_date'] = pd.to_datetime(df_users['registration_date'])
df_transactions['transaction_date'] = pd.to_datetime(df_transactions['transaction_date'])
df_login_sessions['login_timestamp'] = pd.to_datetime(df_login_sessions['login_timestamp'])

# --- Fungsi Bantuan (Helpers) ---
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

def calc_phone_pattern_score(phone):
    if not phone or not isinstance(phone, str):
        return 0.0
    # Bersihkan karakter non-digit
    digits = [c for c in phone if c.isdigit()]
    if not digits:
        return 0.0
    # Skor repetisi: rasio angka unik yang rendah relatif terhadap panjang nomor
    unique_ratio = len(set(digits)) / len(digits)
    # Cek angka yang berulang secara berurutan
    consecutive_repeats = sum(1 for i in range(len(digits)-1) if digits[i] == digits[i+1])
    consecutive_ratio = consecutive_repeats / len(digits)
    
    # Skor gabungan (semakin tinggi semakin mencurigakan)
    return (1.0 - unique_ratio) * 0.7 + consecutive_ratio * 0.3

# --- 1. Fitur Identitas (Identity Features) ---
print("Menghitung Fitur Identitas...")
email_features = []
for idx, row in df_users.iterrows():
    email = row['email']
    email_len = len(str(email))
    
    # Pisahkan nama dan domain email
    email_name = str(email).split('@')[0] if '@' in str(email) else str(email)
    email_domain = str(email).split('@')[1] if '@' in str(email) else ''
    
    num_digits = sum(c.isdigit() for c in email_name)
    email_numeric_ratio = num_digits / len(email_name) if len(email_name) > 0 else 0.0
    email_randomness = calc_entropy(email_name)
    
    disposable_domains = ['mailinator.com', 'yopmail.com', 'tempmail.com']
    is_disposable = email_domain in disposable_domains
    
    phone = row['phone_number']
    phone_pattern = calc_phone_pattern_score(str(phone))
    
    email_features.append({
        'user_id': row['user_id'],
        'email_length': email_len,
        'email_numeric_ratio': email_numeric_ratio,
        'email_randomness_score': email_randomness,
        'is_disposable_email_domain': is_disposable,
        'phone_pattern_score': phone_pattern
    })
df_identity_feats = pd.DataFrame(email_features)


# --- 2. Fitur Perangkat (Device Features) ---
print("Menghitung Fitur Perangkat...")
# Petakan jumlah user per fingerprint device
users_per_device = df_user_devices.groupby('device_id')['user_id'].nunique().to_dict()

device_agg = df_user_devices.copy()
device_agg['users_on_device'] = device_agg['device_id'].map(users_per_device)

# Gabungkan dengan detail perangkat (dihapus karena tidak ada is_emulator/is_rooted)

# Agregasi data untuk tiap user
user_device_feats = device_agg.groupby('user_id').agg(
    unique_devices=('device_id', 'nunique'),
    accounts_per_device_max=('users_on_device', 'max')
).reset_index()


# --- 3. Fitur Alamat (Address Features) ---
print("Menghitung Fitur Alamat...")
# Hitung penggunaan per ID alamat
users_per_address = df_user_addresses.groupby('address_id')['user_id'].nunique().to_dict()
df_addr_merged = df_user_addresses.copy()
df_addr_merged['users_in_address'] = df_addr_merged['address_id'].map(users_per_address)

user_address_feats = df_addr_merged.groupby('user_id').agg(
    unique_addresses=('address_id', 'nunique'),
    accounts_per_address_max=('users_in_address', 'max')
).reset_index()
user_address_feats['address_reuse_flag'] = user_address_feats['accounts_per_address_max'] > 1


# --- 4. Fitur Pembayaran (Payment Features) ---
print("Menghitung Fitur Pembayaran...")
users_per_payment = df_user_payments.groupby('payment_id')['user_id'].nunique().to_dict()
df_pay_merged = df_user_payments.copy()
df_pay_merged['users_on_payment'] = df_pay_merged['payment_id'].map(users_per_payment)

user_payment_feats = df_pay_merged.groupby('user_id').agg(
    unique_payments=('payment_id', 'nunique'),
    accounts_per_payment_max=('users_on_payment', 'max')
).reset_index()
user_payment_feats['payment_reuse_flag'] = user_payment_feats['accounts_per_payment_max'] > 1

# --- 5. Fitur Transaksi (Transaction Features) ---
print("Menghitung Fitur Transaksi...")
# Hitung penggunaan jenis voucher per transaksi
df_txn_merged = df_transactions.merge(df_vouchers[['voucher_id', 'promo_category']], on='voucher_id', how='left')

df_txn_merged['is_new_user_promo'] = df_txn_merged['promo_category'] == 'new_user_promo'
df_txn_merged['is_free_shipping'] = df_txn_merged['promo_category'] == 'free_shipping'

# Hitung tanggal referensi untuk jendela waktu (time windows)
global_max_date = df_transactions['transaction_date'].max()
if pd.isnull(global_max_date):
    global_max_date = pd.to_datetime('today')
df_txn_merged['days_since_txn'] = (global_max_date - df_txn_merged['transaction_date']).dt.days

# Agregasi transaksi pengguna (Keseluruhan / Overall)
user_txn_feats = df_txn_merged.groupby('user_id').agg(
    total_transactions=('transaction_id', 'count'),
    total_order_amount=('order_amount', 'sum'),
    avg_order_amount=('order_amount', 'mean'),
    total_promo_discount=('promo_discount', 'sum'),
    voucher_usage_count=('voucher_id', 'count'),
    new_user_voucher_usage=('is_new_user_promo', 'sum'),
    free_shipping_usage=('is_free_shipping', 'sum')
).reset_index()

# Window Bulanan: 1 sampai 6 bulan terakhir
# 1m=30 hari, 2m=60 hari, 3m=90 hari, 4m=120 hari, 5m=150 hari, 6m=180 hari
month_windows = {
    1: 30,
    2: 60,
    3: 90,
    4: 120,
    5: 150,
    6: 180
}

for m, days in month_windows.items():
    txn_window = df_txn_merged[df_txn_merged['days_since_txn'] <= days]

    user_txn_window = txn_window.groupby('user_id').agg(
        **{
            f'total_transactions_last_{m}m': ('transaction_id', 'count'),
            f'total_order_amount_last_{m}m': ('order_amount', 'sum'),
            f'avg_order_amount_last_{m}m': ('order_amount', 'mean'),
            f'total_promo_discount_last_{m}m': ('promo_discount', 'sum'),
            f'voucher_usage_count_last_{m}m': ('voucher_id', 'count')
        }
    ).reset_index()

    user_txn_feats = user_txn_feats.merge(
        user_txn_window,
        on='user_id',
        how='left'
    )

# Hitung rasio penggunaan promo
user_txn_feats['promo_order_ratio'] = user_txn_feats['voucher_usage_count'] / user_txn_feats['total_transactions']
user_txn_feats.loc[user_txn_feats['total_transactions'] == 0, 'promo_order_ratio'] = 0.0

# Hitung waktu (dalam menit) dari mendaftar hingga transaksi pertama
first_txn = df_transactions.groupby('user_id')['transaction_date'].min().reset_index()
first_txn.columns = ['user_id', 'first_transaction_date']
df_user_reg = df_users[['user_id', 'registration_date']].merge(first_txn, on='user_id', how='left')
df_user_reg['signup_to_first_transaction_minutes'] = (df_user_reg['first_transaction_date'] - df_user_reg['registration_date']).dt.total_seconds() / 60.0
# Isi nilai kosong NaN (untuk user yang belum pernah transaksi) dengan angka besar agar tidak memicu aturan instan
df_user_reg['signup_to_first_transaction_minutes'] = df_user_reg['signup_to_first_transaction_minutes'].fillna(999999).astype(int)


# --- 6. Fitur Login (Login Features) ---
print("Menghitung Fitur Login...")
# Petakan jumlah user per IP
users_per_ip = df_login_sessions.groupby('ip_address')['user_id'].nunique().to_dict()
df_logins_merged = df_login_sessions.copy()
df_logins_merged['users_on_ip'] = df_logins_merged['ip_address'].map(users_per_ip)

# Fungsi frekuensi login: jumlah login dalam N jam terakhir dari tanggal referensi.
# Ini BUKAN velocity window.
# Frequency = count login pada periode terakhir, misalnya 1 jam terakhir, 2 jam terakhir, dst.
login_reference_time = df_login_sessions['login_timestamp'].max()
if pd.isnull(login_reference_time):
    login_reference_time = pd.to_datetime('today')

def get_login_frequency_windows(group):
    windows_hours = [1, 2, 3, 4, 5, 6, 12, 18, 24]
    results = {f'login_frequency_{h}h': 0 for h in windows_hours}

    if group.empty:
        return pd.Series(results)

    time_diff_hours = (login_reference_time - group['login_timestamp']).dt.total_seconds() / 3600.0

    for h in windows_hours:
        results[f'login_frequency_{h}h'] = int((time_diff_hours <= h).sum())

    return pd.Series(results)

# Hitung frekuensi login untuk berbagai jendela waktu terakhir
frequency_data = df_login_sessions.groupby('user_id').apply(get_login_frequency_windows).reset_index()

# Agregasi fitur login lainnya
user_login_feats = df_logins_merged.groupby('user_id').agg(
    login_count=('session_id', 'count'),
    unique_ip_addresses=('ip_address', 'nunique'),
    accounts_per_ip_max=('users_on_ip', 'max')
).reset_index()

user_login_feats = user_login_feats.merge(frequency_data, on='user_id', how='left')


# --- 7. Fitur Referral (Referral Features) ---
print("Menghitung Fitur Referral...")
# Hitung jumlah referral yang dibuat
referral_counts = df_referrals.groupby('referrer_user_id')['referral_id'].count().to_dict()
# Tanda (flag) apakah user diundang oleh orang lain
referred_users = set(df_referrals['referred_user_id'].tolist())

# Skor lingkaran referral (referral ring) menggunakan deteksi siklus (cycle) atau analisis jalur
# Mari buat graf jaringan referral berarah (directed) menggunakan NetworkX
ref_graph = nx.DiGraph()
for idx, row in df_referrals.iterrows():
    ref_graph.add_edge(row['referrer_user_id'], row['referred_user_id'])

# Cari siklus/lingkaran setan
cycles = list(nx.simple_cycles(ref_graph))
cycle_membership = {}
for cycle in cycles:
    for node in cycle:
        cycle_membership[node] = len(cycle)

referral_feats = []
for idx, row in df_users.iterrows():
    u_id = row['user_id']
    count = referral_counts.get(u_id, 0)
    is_referred = u_id in referred_users
    
    # Skor ring: ukuran siklus jika user bagian dari siklus, jika tidak 0
    ring_score = float(cycle_membership.get(u_id, 0))
    # Jika tidak dalam siklus, periksa apakah mereka terhubung ke simpul (node) siklus
    if ring_score == 0:
        # Berikan skor fraksional jika mereka berada di bawah jaringan referral ukuran > 3
        # Mari hitung jumlah keturunan jaringan (descendants)
        try:
            descendants = len(nx.descendants(ref_graph, u_id))
            if descendants > 3:
                ring_score = float(descendants) / 2.0
        except:
            pass
            
    referral_feats.append({
        'user_id': u_id,
        'referral_count': count,
        'referred_by_user_flag': is_referred,
        'referral_ring_score': ring_score
    })
df_referral_feats = pd.DataFrame(referral_feats)


# --- 8. Fitur Graf/Jaringan (Dihilangkan, akan diproses terpisah) ---



# --- 9. Merakit Tabel Dasar Analitik (Analytics Base Table / ABT) ---
print("Merakit ABT Final...")
# Gabungkan semua kerangka data (dataframes)
df_abt = df_users[['user_id', 'registration_date']].copy()

# Proses Penggabungan (Merges)
df_abt = df_abt.merge(df_identity_feats, on='user_id', how='left')
df_abt = df_abt.merge(user_device_feats, on='user_id', how='left')
df_abt = df_abt.merge(user_address_feats, on='user_id', how='left')
df_abt = df_abt.merge(user_payment_feats, on='user_id', how='left')
df_abt = df_abt.merge(user_txn_feats, on='user_id', how='left')
df_abt = df_abt.merge(df_user_reg[['user_id', 'signup_to_first_transaction_minutes']], on='user_id', how='left')
df_abt = df_abt.merge(user_login_feats, on='user_id', how='left')
df_abt = df_abt.merge(df_referral_feats, on='user_id', how='left')

# Hitung fitur-fitur umum
max_date = df_transactions['transaction_date'].max()
if pd.isnull(max_date):
    max_date = pd.to_datetime('today')
df_abt['account_age_days'] = (max_date - df_abt['registration_date']).dt.days

# hari sejak login terakhir (days_since_last_login)
last_login = df_login_sessions.groupby('user_id')['login_timestamp'].max().reset_index()
last_login.columns = ['user_id', 'last_login_date']
df_abt = df_abt.merge(last_login, on='user_id', how='left')
df_abt['days_since_last_login'] = (max_date - df_abt['last_login_date']).dt.days
# Isi data login yang kosong dengan umur akun (atau maksimal)
df_abt['days_since_last_login'] = df_abt['days_since_last_login'].fillna(df_abt['account_age_days'])

# Isi sisa data kosong (NaN) dengan angka nol sesuai kebutuhan
fill_zero_cols = [
    'total_transactions', 'total_order_amount', 'avg_order_amount',
    'total_promo_discount', 'promo_order_ratio', 'voucher_usage_count',
    'new_user_voucher_usage', 'free_shipping_usage',
    'total_transactions_last_1m', 'total_order_amount_last_1m', 'avg_order_amount_last_1m', 'total_promo_discount_last_1m', 'voucher_usage_count_last_1m',
    'total_transactions_last_2m', 'total_order_amount_last_2m', 'avg_order_amount_last_2m', 'total_promo_discount_last_2m', 'voucher_usage_count_last_2m',
    'total_transactions_last_3m', 'total_order_amount_last_3m', 'avg_order_amount_last_3m', 'total_promo_discount_last_3m', 'voucher_usage_count_last_3m',
    'total_transactions_last_4m', 'total_order_amount_last_4m', 'avg_order_amount_last_4m', 'total_promo_discount_last_4m', 'voucher_usage_count_last_4m',
    'total_transactions_last_5m', 'total_order_amount_last_5m', 'avg_order_amount_last_5m', 'total_promo_discount_last_5m', 'voucher_usage_count_last_5m',
    'total_transactions_last_6m', 'total_order_amount_last_6m', 'avg_order_amount_last_6m', 'total_promo_discount_last_6m', 'voucher_usage_count_last_6m',
    'unique_devices',
    'accounts_per_device_max', 'unique_addresses', 'accounts_per_address_max',
    'unique_payments', 'accounts_per_payment_max', 'unique_ip_addresses',
    'accounts_per_ip_max', 'login_count',
    'login_frequency_1h', 'login_frequency_2h', 'login_frequency_3h',
    'login_frequency_4h', 'login_frequency_5h', 'login_frequency_6h',
    'login_frequency_12h', 'login_frequency_18h', 'login_frequency_24h',
    'referral_count', 'referral_ring_score'
]
for col in fill_zero_cols:
    if col not in df_abt.columns:
        df_abt[col] = 0
    else:
        df_abt[col] = df_abt[col].fillna(0)

# Isi data Boolean yang kosong
fill_bool_cols = [
    'is_disposable_email_domain', 
    'address_reuse_flag', 'payment_reuse_flag', 'referred_by_user_flag'
]
df_abt[fill_bool_cols] = df_abt[fill_bool_cols].fillna(False)

# Konversi kolom boolean menjadi boolean asli (native) Python
for col in fill_bool_cols:
    df_abt[col] = df_abt[col].astype(bool)

# --- 10. Kategori & Skor Risiko Berbasis Aturan (Rule-based Risk Score) ---
print("Menghitung Kategori & Skor Risiko Berbasis Aturan...")
def compute_risk_score(row):
    score = 0
    # Perangkat
    if row['accounts_per_device_max'] > 5: score += 40
    elif row['accounts_per_device_max'] > 2: score += 15
    
    # Alamat & Jaringan
    if row['accounts_per_address_max'] > 5: score += 20
    if row['accounts_per_ip_max'] > 5: score += 15
    
    # Frequency
    if row['login_frequency_1h'] > 10: score += 40
    
    # Vouchers dan Waktu
    if row['promo_order_ratio'] > 0.8: score += 15
    if 0 <= row['signup_to_first_transaction_minutes'] < 30: score += 15
    if row['new_user_voucher_usage'] > 2: score += 10
    
    # Koneksi Graf Jaringan (Dinonaktifkan sementara)
    # if row.get('graph_degree', 0) > 10: score += 20
    # if row.get('connected_component_size', 0) > 5: score += 10
    
    return min(100, score)

df_abt['risk_score_rule_based'] = df_abt.apply(compute_risk_score, axis=1)

def categorize_risk(score):
    if score > 60:
        return 'High'
    elif score > 30:
        return 'Medium'
    else:
        return 'Low'

df_abt['risk_category'] = df_abt['risk_score_rule_based'].apply(categorize_risk)

# Gabungkan kembali dengan label asli dari fraud_labels untuk keperluan evaluasi/training model
df_abt = df_abt.merge(df_fraud_labels[['user_id', 'is_fake_account', 'fraud_type']], on='user_id', how='left')

# Menyaring seluruh fitur hasil ekstraksi (Hapus kolom tanggal mentah)
columns_to_keep = [
    # Meta & Labels
    'user_id', 'is_fake_account', 'fraud_type', 'risk_score_rule_based', 'risk_category',

    # Identity
    'email_length', 'email_numeric_ratio', 'email_randomness_score', 'is_disposable_email_domain', 'phone_pattern_score',

    # Devices, Addresses, Payments
    'unique_devices', 'accounts_per_device_max',
    'unique_addresses', 'accounts_per_address_max',
    'unique_payments', 'accounts_per_payment_max',

    # Transactions
    'promo_order_ratio', 'signup_to_first_transaction_minutes', 'new_user_voucher_usage',

    # Time Window Transactions: 1m sampai 6m
    'total_transactions_last_1m', 'total_order_amount_last_1m', 'avg_order_amount_last_1m', 'total_promo_discount_last_1m', 'voucher_usage_count_last_1m',
    'total_transactions_last_2m', 'total_order_amount_last_2m', 'avg_order_amount_last_2m', 'total_promo_discount_last_2m', 'voucher_usage_count_last_2m',
    'total_transactions_last_3m', 'total_order_amount_last_3m', 'avg_order_amount_last_3m', 'total_promo_discount_last_3m', 'voucher_usage_count_last_3m',
    'total_transactions_last_4m', 'total_order_amount_last_4m', 'avg_order_amount_last_4m', 'total_promo_discount_last_4m', 'voucher_usage_count_last_4m',
    'total_transactions_last_5m', 'total_order_amount_last_5m', 'avg_order_amount_last_5m', 'total_promo_discount_last_5m', 'voucher_usage_count_last_5m',
    'total_transactions_last_6m', 'total_order_amount_last_6m', 'avg_order_amount_last_6m', 'total_promo_discount_last_6m', 'voucher_usage_count_last_6m',

    # Login & IP
    'accounts_per_ip_max',
    'login_frequency_1h', 'login_frequency_2h', 'login_frequency_3h',
    'login_frequency_4h', 'login_frequency_5h', 'login_frequency_6h',
    'login_frequency_12h', 'login_frequency_18h', 'login_frequency_24h',

    # Referral
    'referral_count', 'referral_ring_score'
]
# Pastikan tipe data hitungan & rupiah adalah integer agar tidak jadi .0 (menghindari bug baca Excel)
int_cols = [
    'signup_to_first_transaction_minutes', 'new_user_voucher_usage',
    'total_transactions_last_1m', 'total_order_amount_last_1m', 'avg_order_amount_last_1m', 'total_promo_discount_last_1m', 'voucher_usage_count_last_1m',
    'total_transactions_last_2m', 'total_order_amount_last_2m', 'avg_order_amount_last_2m', 'total_promo_discount_last_2m', 'voucher_usage_count_last_2m',
    'total_transactions_last_3m', 'total_order_amount_last_3m', 'avg_order_amount_last_3m', 'total_promo_discount_last_3m', 'voucher_usage_count_last_3m',
    'total_transactions_last_4m', 'total_order_amount_last_4m', 'avg_order_amount_last_4m', 'total_promo_discount_last_4m', 'voucher_usage_count_last_4m',
    'total_transactions_last_5m', 'total_order_amount_last_5m', 'avg_order_amount_last_5m', 'total_promo_discount_last_5m', 'voucher_usage_count_last_5m',
    'total_transactions_last_6m', 'total_order_amount_last_6m', 'avg_order_amount_last_6m', 'total_promo_discount_last_6m', 'voucher_usage_count_last_6m',
]
for col in int_cols:
    if col in df_abt.columns:
        df_abt[col] = df_abt[col].astype(int)

# Pastikan hanya menggunakan kolom fitur yang relevan (Total 63 kolom)
df_abt = df_abt[[col for col in columns_to_keep if col in df_abt.columns]]

# Rename kolom hanya untuk output CSV.
# Logika internal di atas tetap memakai nama panjang.
output_col_map = {
    'user_id': 'uid',
    'is_fake_account': 'fraud',
    'fraud_type': 'ftype',
    'risk_score_rule_based': 'risk_score',
    'risk_category': 'risk_cat',
    'email_length': 'email_len',
    'email_numeric_ratio': 'email_num_ratio',
    'email_randomness_score': 'email_rand',
    'is_disposable_email_domain': 'disp_email',
    'phone_pattern_score': 'phone_score',
    'unique_devices': 'uniq_dev',
    'accounts_per_device_max': 'max_acc_dev',
    'unique_addresses': 'uniq_addr',
    'accounts_per_address_max': 'max_acc_addr',
    'unique_payments': 'uniq_pay',
    'accounts_per_payment_max': 'max_acc_pay',
    'promo_order_ratio': 'promo_ratio',
    'signup_to_first_transaction_minutes': 'reg2txn_min',
    'new_user_voucher_usage': 'newuser_voucher',
    'accounts_per_ip_max': 'max_acc_ip',
    'login_frequency_1h': 'login_f1h',
    'login_frequency_2h': 'login_f2h',
    'login_frequency_3h': 'login_f3h',
    'login_frequency_4h': 'login_f4h',
    'login_frequency_5h': 'login_f5h',
    'login_frequency_6h': 'login_f6h',
    'login_frequency_12h': 'login_f12h',
    'login_frequency_18h': 'login_f18h',
    'login_frequency_24h': 'login_f24h',
    'referral_count': 'ref_cnt',
    'referral_ring_score': 'ref_ring',
    'total_transactions_last_1m': 'txn_f1m',
    'total_order_amount_last_1m': 'amt_f1m',
    'avg_order_amount_last_1m': 'avg_amt1m',
    'total_promo_discount_last_1m': 'promo_f1m',
    'voucher_usage_count_last_1m': 'voucher_f1m',
    'total_transactions_last_2m': 'txn_f2m',
    'total_order_amount_last_2m': 'amt_f2m',
    'avg_order_amount_last_2m': 'avg_amt2m',
    'total_promo_discount_last_2m': 'promo_f2m',
    'voucher_usage_count_last_2m': 'voucher_f2m',
    'total_transactions_last_3m': 'txn_f3m',
    'total_order_amount_last_3m': 'amt_f3m',
    'avg_order_amount_last_3m': 'avg_amt3m',
    'total_promo_discount_last_3m': 'promo_f3m',
    'voucher_usage_count_last_3m': 'voucher_f3m',
    'total_transactions_last_4m': 'txn_f4m',
    'total_order_amount_last_4m': 'amt_f4m',
    'avg_order_amount_last_4m': 'avg_amt4m',
    'total_promo_discount_last_4m': 'promo_f4m',
    'voucher_usage_count_last_4m': 'voucher_f4m',
    'total_transactions_last_5m': 'txn_f5m',
    'total_order_amount_last_5m': 'amt_f5m',
    'avg_order_amount_last_5m': 'avg_amt5m',
    'total_promo_discount_last_5m': 'promo_f5m',
    'voucher_usage_count_last_5m': 'voucher_f5m',
    'total_transactions_last_6m': 'txn_f6m',
    'total_order_amount_last_6m': 'amt_f6m',
    'avg_order_amount_last_6m': 'avg_amt6m',
    'total_promo_discount_last_6m': 'promo_f6m',
    'voucher_usage_count_last_6m': 'voucher_f6m',
}

df_abt = df_abt.rename(columns=output_col_map)

# Simpan ke dalam file CSV
OUTPUT_PATH = os.path.join(ABT_DIR, 'fake_account_abt.csv')
df_abt.to_csv(OUTPUT_PATH, index=False)

print(f"\n--- Pembuatan ABT Selesai! ---")
print(f"Total Baris (Users): {len(df_abt)}")
print(f"Total Kolom: {len(df_abt.columns)}")
print(f"ABT disimpan di: {OUTPUT_PATH}")
print(f"Distribusi Fraud di ABT: {df_abt['fraud'].value_counts(normalize=True).to_dict()}")
print(f"Kategori Risiko: {df_abt['risk_cat'].value_counts().to_dict()}")

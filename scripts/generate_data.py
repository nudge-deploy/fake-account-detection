"""Purpose: Generate synthetic fraud-detection raw CSV tables.
Used by: Manual data pipeline before graph/ABT/model scripts.
Depends on: Faker, pandas, numpy, local data/raw directory.
Public functions: random_id_phone, session_duration, realistic_address.
Side effects: Writes raw CSV files under data/raw.
"""

import os
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker
import math

# Set seeds for reproducibility
random.seed(42)
np.random.seed(42)
fake = Faker(locale='id_ID')
Faker.seed(42)

# ── #1 Prefix Nomor Telepon Operator Indonesia Asli ───────────────────────
# Sumber: Rencana penomoran telekomunikasi Indonesia (Kominfo)
ID_PHONE_PREFIXES = [
    # Telkomsel (dominant ~45%)
    '0811', '0812', '0813', '0821', '0822', '0823', '0851', '0852', '0853',
    # Indosat Ooredoo (~20%)
    '0814', '0815', '0816', '0855', '0856', '0857', '0858',
    # XL Axiata (~15%)
    '0817', '0818', '0819', '0859', '0877', '0878',
    # Tri (3) (~10%)
    '0895', '0896', '0897', '0898', '0899',
    # Smartfren (~5%)
    '0881', '0882', '0883', '0884', '0885', '0886', '0887', '0888', '0889',
]
# Pembobotan: Telkomsel lebih sering muncul, diikuti Indosat, XL, Tri, dan Smartfren
ID_PHONE_WEIGHTS = [5]*9 + [3]*7 + [2]*6 + [2]*5 + [1]*9

def random_id_phone():
    """Mengembalikan nomor handphone Indonesia yang realistis."""
    prefix = random.choices(ID_PHONE_PREFIXES, weights=ID_PHONE_WEIGHTS, k=1)[0]
    suffix_len = 7 if prefix in ('0811', '0856') else 8
    suffix = str(random.randint(10**(suffix_len-1), 10**suffix_len - 1))
    return prefix + suffix

# ── #2 Nama Model Perangkat Asli ──────────────────────────────────────────
# Pasar Indonesia: Didominasi oleh HP kelas menengah Samsung & Xiaomi
ANDROID_MODELS = [
    # Samsung A-series (heaviest weight ~35%)
    'Samsung Galaxy A14', 'Samsung Galaxy A24', 'Samsung Galaxy A34',
    'Samsung Galaxy A54', 'Samsung Galaxy A15', 'Samsung Galaxy A25',
    # Xiaomi / Redmi (~25%)
    'Xiaomi Redmi 12', 'Xiaomi Redmi 12C', 'Xiaomi Redmi Note 12',
    'Xiaomi Redmi Note 13', 'POCO M5', 'POCO M6 Pro',
    # OPPO A-series (~20%)
    'OPPO A18', 'OPPO A38', 'OPPO A58', 'OPPO A78', 'OPPO A17',
    # Vivo Y-series (~10%)
    'Vivo Y16', 'Vivo Y17s', 'Vivo Y22', 'Vivo Y27', 'Vivo Y36',
    # Realme (~10%)
    'Realme C55', 'Realme C53', 'Realme 11', 'Realme narzo N55',
]
ANDROID_MODEL_WEIGHTS = [6]*6 + [5]*6 + [4]*5 + [2]*5 + [2]*4

IOS_MODELS = [
    # Older iPhones dominate in Indonesia (price)
    'iPhone 11', 'iPhone 12', 'iPhone 12 mini', 'iPhone 13', 'iPhone 13 mini',
    'iPhone 14', 'iPhone 14 Plus', 'iPhone 15', 'iPhone SE (3rd gen)',
]
IOS_MODEL_WEIGHTS = [3, 4, 2, 4, 2, 3, 2, 2, 2]

def random_device_model(dtype):
    if dtype == 'android':
        return random.choices(ANDROID_MODELS, weights=ANDROID_MODEL_WEIGHTS, k=1)[0]
    return random.choices(IOS_MODELS, weights=IOS_MODEL_WEIGHTS, k=1)[0]

# ── #3 Distribusi Tipe Pembayaran Berdasarkan Pasar ────────────────────────
# Sumber: Laporan pembayaran digital Bank Indonesia & riset pasar GoPay/OVO
PAYMENT_TYPE_POOL = ['ewallet', 'bank_transfer', 'qris', 'debit_card', 'cod', 'credit_card']
PAYMENT_TYPE_WEIGHTS = [45, 25, 15, 8, 5, 2]

def random_payment_type():
    return random.choices(PAYMENT_TYPE_POOL, weights=PAYMENT_TYPE_WEIGHTS, k=1)[0]

# ── #4 Rentang Harga Satuan Berdasarkan Kategori (Rupiah) ──────────────────
CATEGORY_PRICE_RANGES = {
    'Groceries':    (8_000,   80_000),
    'Beverages':    (5_000,   50_000),
    'Fresh Food':  (15_000,  120_000),
    'Personal Care':(20_000, 200_000),
    'Baby Care':   (30_000,  300_000),
    'Home Living': (50_000,  500_000),
    'Electronics': (150_000, 2_000_000),
}

def category_unit_price(category):
    lo, hi = CATEGORY_PRICE_RANGES.get(category, (10_000, 200_000))
    # Log-uniform so mid-range values are more common than extremes
    log_lo, log_hi = math.log(lo), math.log(hi)
    return round(math.exp(random.uniform(log_lo, log_hi)) / 500) * 500

# ── #5 Pembobotan Jalur Pendaftaran (Google/Email/HP) ──────────────────────
REG_CHANNEL_POOL    = ['google', 'phone', 'email', 'facebook']
REG_CHANNEL_WEIGHTS = [40, 30, 20, 10]

def random_reg_channel():
    return random.choices(REG_CHANNEL_POOL, weights=REG_CHANNEL_WEIGHTS, k=1)[0]

# ── #6 Durasi Sesi Login Menggunakan Distribusi Log-Normal ─────────────────
def session_duration(is_fraud=False, fraud_type=None):
    """Mengembalikan durasi sesi dalam satuan detik dengan distribusi realistis."""
    if not is_fraud:
        # Pengguna normal: rata-rata sekitar 11 menit (maksimal 2 jam)
        dur = int(np.random.lognormal(mean=6.5, sigma=0.7))
        return max(60, min(dur, 7200))
    if fraud_type == 'voucher_farming':
        # Voucher farmers: just enough to check out
        return random.randint(60, 400)
    # Other fraud: moderately short
    return random.randint(60, 900)

# ── #7 Pembuat Prefix Alamat Indonesia (Jalan, Gang, Blok) ─────────────────
_ADDR_PREFIXES = ['Jl. ', 'Jalan ', 'Gang ', 'Gg. ', 'Komp. ', 'Perum. ', 'Blok ']
_ADDR_PREFIX_WEIGHTS = [40, 20, 15, 10, 7, 5, 3]

def realistic_address():
    prefix = random.choices(_ADDR_PREFIXES, weights=_ADDR_PREFIX_WEIGHTS, k=1)[0]
    return prefix + fake.street_name() + f" No. {random.randint(1, 200)}, RT {random.randint(1,15):02d}/RW {random.randint(1,10):02d}"

# ── #9 Bias Hari (Akhir Pekan vs Hari Kerja) ───────────────────────────────
# Indeks: 0=Senin … 6=Minggu (Akhir pekan lebih ramai transaksi)
NORMAL_DOW_WEIGHTS = [8, 8, 9, 10, 14, 16, 14]   # Fri/Sat/Sun heavy
FRAUD_DOW_WEIGHTS  = [14, 14, 14, 14, 14, 15, 15]  # Nearly flat, slight weekend

def biased_day_offset(base_date, day_offset_range, is_fraud=False):
    """Pick a day within the offset range, weighted by day-of-week."""
    lo, hi = day_offset_range
    if hi <= lo:
        hi = lo + 1
    # Sample candidate days and pick one weighted by dow
    candidate_days = list(range(lo, min(hi, lo + 60) + 1))
    if not candidate_days:
        candidate_days = [lo]
    dow_weights_choice = FRAUD_DOW_WEIGHTS if is_fraud else NORMAL_DOW_WEIGHTS
    day_weights = [dow_weights_choice[(base_date + timedelta(days=d)).weekday()] for d in candidate_days]
    chosen_offset = random.choices(candidate_days, weights=day_weights, k=1)[0]
    return chosen_offset

# Directory output configuration
try:
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
except NameError:
    BASE_DIR = os.getcwd()

OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'raw')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Target counts
NUM_USERS = 10000
NUM_DEVICES = 7000
NUM_ADDRESSES = 8000
NUM_PAYMENTS = 9000
NUM_VOUCHERS = 500
NUM_TRANSACTIONS = 50000
NUM_LOGINS = 100000

# Date range: 6 months ago to today
END_DATE = datetime.now()
START_DATE = END_DATE - timedelta(days=180)

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

# ── Pembantu Realisme Waktu (Temporal) ────────────────────────────────
# Pengguna normal: aktif siang hari; fraud bisa aktif dini hari / burst.
NORMAL_HOUR_WEIGHTS = [
    1, 1, 1, 1, 1, 2,
    4, 8, 10, 12, 12, 14,
    14, 10, 10, 10, 12, 14,
    16, 18, 16, 12, 8, 4
]

FRAUD_HOUR_WEIGHTS = [
    18, 18, 16, 14, 12, 10,
    6, 4, 4, 4, 4, 4,
    4, 4, 4, 4, 4, 4,
    4, 4, 6, 8, 10, 14
]

# Persona login dibuat supaya fitur login frequency berbasis bucket harian
# seperti 00:00-01:00, 00:00-02:00, ..., 00:00-24:00 bisa menghasilkan nilai 0.
# Contoh user yang login jam 07:00, 12:00, 18:00:
# login_v1h=0, login_v6h=0, login_v12h=2, login_v18h=3, login_v24h=3.
LOGIN_PERSONA_HOUR_WEIGHTS = {
    # Normal user yang mayoritas baru aktif pagi-siang-malam.
    # Hampir tidak ada login 00-05 sehingga bucket awal bisa 0.
    'morning_worker': [
        0, 0, 0, 0, 0, 1,
        10, 16, 16, 10, 6, 4,
        6, 4, 3, 3, 3, 4,
        6, 6, 4, 2, 1, 0
    ],
    'office_worker': [
        0, 0, 0, 0, 0, 1,
        4, 10, 12, 8, 5, 4,
        8, 5, 4, 4, 4, 5,
        10, 12, 10, 6, 3, 1
    ],
    'evening_user': [
        0, 0, 0, 0, 0, 0,
        1, 2, 3, 3, 3, 4,
        5, 5, 5, 5, 6, 8,
        14, 18, 18, 14, 8, 3
    ],
    'low_activity': [
        0, 0, 0, 0, 0, 0,
        2, 3, 4, 4, 4, 5,
        8, 6, 5, 5, 4, 5,
        8, 10, 8, 5, 2, 1
    ],
    # Fraud night/bot: banyak login dini hari sehingga bucket 1h-6h bisa tinggi.
    'fraud_night': [
        20, 20, 18, 16, 14, 10,
        6, 4, 3, 3, 3, 3,
        3, 3, 3, 3, 3, 3,
        4, 5, 6, 8, 10, 12
    ],
    # Fraud yang meniru user normal agar tidak terlalu mudah dibedakan.
    'fraud_mimic': [
        0, 0, 0, 0, 1, 1,
        5, 8, 8, 7, 6, 5,
        6, 6, 5, 5, 5, 6,
        10, 12, 10, 8, 4, 2
    ],
}

def weighted_hour(weights):
    return random.choices(range(24), weights=weights, k=1)[0]

def random_minute_second():
    return random.randint(0, 59), random.randint(0, 59)

def choose_login_persona(is_fraud=False, fraud_type='normal'):
    """Pilih persona jam login per user agar timestamp lebih realistis dan bervariasi."""
    if not is_fraud:
        return random.choices(
            ['morning_worker', 'office_worker', 'evening_user', 'low_activity'],
            weights=[30, 35, 25, 10],
            k=1
        )[0]

    if fraud_type == 'voucher_farming':
        return random.choices(
            ['fraud_mimic', 'low_activity', 'fraud_night'],
            weights=[45, 30, 25],
            k=1
        )[0]

    if fraud_type in ('shared_device_abuse', 'referral_abuse'):
        return random.choices(
            ['fraud_night', 'fraud_mimic', 'office_worker'],
            weights=[45, 35, 20],
            k=1
        )[0]

    return random.choices(
        ['fraud_mimic', 'fraud_night', 'office_worker'],
        weights=[45, 35, 20],
        k=1
    )[0]

def realistic_datetime(base_date, day_offset_range=(0, 150), is_fraud=False):
    """Return a datetime with realistic hour AND day-of-week distribution."""
    weights = FRAUD_HOUR_WEIGHTS if is_fraud else NORMAL_HOUR_WEIGHTS
    day_off = biased_day_offset(base_date, day_offset_range, is_fraud=is_fraud)
    d = base_date + timedelta(days=day_off)
    minute, second = random_minute_second()
    d = d.replace(
        hour=weighted_hour(weights),
        minute=minute,
        second=second
    )
    if d < base_date:
        d = base_date + timedelta(minutes=random.randint(1, 30))
    return min(d, END_DATE - timedelta(minutes=1))

def persona_login_datetime(base_date, day_offset_range=(0, 150), persona='office_worker', is_fraud=False):
    """Generate login timestamp berbasis persona jam aktivitas.

    Ini yang membuat data sintetis punya pola:
    - normal user sering login pagi/siang/malam
    - bucket awal 00:00-01:00 sampai 00:00-06:00 bisa bernilai 0
    - fraud tertentu bisa login dini hari atau burst
    """
    day_off = biased_day_offset(base_date, day_offset_range, is_fraud=is_fraud)
    d = base_date + timedelta(days=day_off)

    weights = LOGIN_PERSONA_HOUR_WEIGHTS.get(persona, LOGIN_PERSONA_HOUR_WEIGHTS['office_worker'])
    hour = weighted_hour(weights)
    minute, second = random_minute_second()

    d = d.replace(hour=hour, minute=minute, second=second)

    if d < base_date:
        d = base_date + timedelta(minutes=random.randint(1, 30))

    return min(d, END_DATE - timedelta(minutes=1))

# ── Rentang IP Datacenter/Hosting (Indikator kuat adanya bot) ────────
DATACENTER_IP_PREFIXES = [
    '45.76.', '139.59.', '165.22.',   # DigitalOcean
    '54.179.', '52.74.', '13.250.',   # AWS Singapore
    '34.101.', '35.198.',             # GCP Southeast Asia
    '104.21.', '172.67.',             # Cloudflare/hosting
]

def datacenter_ip():
    prefix = random.choice(DATACENTER_IP_PREFIXES)
    return prefix + str(random.randint(1, 254)) + '.' + str(random.randint(1, 254))

# ── Indonesian city/IP map (defined early — used in user gen & login gen) ──
indonesian_cities_ips = [
    {'city': 'Jakarta',    'province': 'DKI Jakarta',      'ip': '103.10.66.'},
    {'city': 'Surabaya',   'province': 'Jawa Timur',        'ip': '114.125.12.'},
    {'city': 'Bandung',    'province': 'Jawa Barat',        'ip': '180.244.35.'},
    {'city': 'Medan',      'province': 'Sumatera Utara',    'ip': '202.152.41.'},
    {'city': 'Semarang',   'province': 'Jawa Tengah',       'ip': '125.163.77.'},
    {'city': 'Makassar',   'province': 'Sulawesi Selatan',  'ip': '103.28.115.'},
    {'city': 'Yogyakarta', 'province': 'DI Yogyakarta',     'ip': '180.252.97.'},
    {'city': 'Denpasar',   'province': 'Bali',              'ip': '182.253.18.'},
]

print("Generating synthetic data with EXTREME noise & overlaps...")

# --- 1. MEMBUAT DATA VOUCHER ---
print("Generating Vouchers...")
vouchers = []
promo_categories = ['new_user_promo', 'free_shipping', 'cashback', 'flash_sale', 'loyalty_reward', 'referral_reward']

# Create special new user voucher
vouchers.append({
    'voucher_id': 'VCH00001',
    'voucher_code': 'NEWUSER50',
    'voucher_type': 'fixed_amount',
    'discount_amount': 50000.0,
    'discount_percentage': 0.0,
    'min_purchase_amount': 100000.0,
    'start_date': START_DATE,
    'end_date': END_DATE + timedelta(days=30),
    'max_usage': 10000,
    'promo_category': 'new_user_promo'
})

for i in range(2, NUM_VOUCHERS + 1):
    v_type = random.choice(['percentage', 'fixed_amount'])
    promo_cat = random.choice(promo_categories)
    
    disc_pct = 0.0
    disc_amt = 0.0
    min_purchase = float(random.choice([0, 50000, 100000, 150000]))
    
    if v_type == 'percentage':
        disc_pct = float(random.choice([5, 10, 15, 20, 25]))
    else:
        disc_amt = float(random.choice([10000, 20000, 50000, 75000]))
        
    vouchers.append({
        'voucher_id': f"VCH{i:05d}",
        'voucher_code': f"{promo_cat.upper()}_{random.randint(100, 999)}_{i}",
        'voucher_type': v_type,
        'discount_amount': disc_amt,
        'discount_percentage': disc_pct,
        'min_purchase_amount': min_purchase,
        'start_date': START_DATE,
        'end_date': END_DATE + timedelta(days=30),
        'max_usage': random.choice([50, 100, 500, 1000]),
        'promo_category': promo_cat
    })
df_vouchers = pd.DataFrame(vouchers)


# --- 2. MEMBUAT PENGGUNA & LABEL FRAUD ---
print("Generating Users & Fraud Labels...")
users = []
fraud_labels = []

# Target: ~30% fake accounts (~3000 fake accounts)
fraud_assignments = {}
shuffled_user_indices = list(range(1, NUM_USERS + 1))
random.shuffle(shuffled_user_indices)

# Allocate indices to scenarios
sc1_indices = set(shuffled_user_indices[:600])
sc2_indices = set(shuffled_user_indices[600:1200])
sc3_indices = set(shuffled_user_indices[1200:1800])
sc4_indices = set(shuffled_user_indices[1800:2400])
sc5_indices = set(shuffled_user_indices[2400:3000])

for uid_int in range(1, NUM_USERS + 1):
    user_id = f"USR{uid_int:05d}"
    
    is_fake = False
    f_type = 'normal'
    f_reason = ''
    label_src = 'rule_based'
    
    if uid_int in sc1_indices:
        is_fake = True
        f_type = 'shared_device_abuse'
        f_reason = 'Multiple accounts registered and logging in from the same device fingerprint'
    elif uid_int in sc2_indices:
        is_fake = True
        f_type = 'shared_address_abuse'
        f_reason = 'Multiple accounts sharing the same physical delivery address'
    elif uid_int in sc3_indices:
        is_fake = True
        f_type = 'shared_payment_abuse'
        f_reason = 'Multiple accounts linked to the same default payment token'
    elif uid_int in sc4_indices:
        is_fake = True
        f_type = 'voucher_farming'
        f_reason = 'Account registered solely to exploit new user discount and has zero subsequent logins'
    elif uid_int in sc5_indices:
        is_fake = True
        f_type = 'referral_abuse'
        f_reason = 'Part of a circular referral ring sharing IP addresses and device fingerprints'
        
    # --- NOISE INTRODUCED HERE: 20% of fraud cases look extremely normal in their reasons ---
    if is_fake and random.random() < 0.20:
        f_reason = 'Looks like a regular user; transaction and setup behaviors overlap with normal profiles'
        
    fraud_assignments[user_id] = {
        'is_fake_account': is_fake,
        'fraud_type': f_type,
        'fraud_reason': f_reason,
        'label_source': label_src
    }
    
    # Profile field generations (with noise)
    # 15% of normal users have suspicious/complex random looking emails (Lazy naming)
    # 40% of fake users have clean, standard free emails and verified phone numbers
    is_suspicious_profile = (is_fake and f_type in ['voucher_farming'] and random.random() < 0.60) or (not is_fake and random.random() < 0.15)
    
    if is_suspicious_profile:
        first_name = fake.first_name()
        last_name = str(random.randint(100, 99999))
        full_name = f"{first_name} {last_name}"
        email_domain = random.choice(['mailinator.com', 'yopmail.com', 'tempmail.com', 'gmail.com'])
        email = f"{first_name.lower()}{last_name}@{email_domain}"
        phone_number = random_id_phone()  # #1: realistic operator prefix
        is_email_verified = random.choice([True, False])
        is_phone_verified = random.choice([True, False])
    else:
        full_name = fake.name()
        email = fake.free_email()
        phone_number = random_id_phone()  # #1: realistic operator prefix
        is_email_verified = True
        is_phone_verified = True
        
    reg_date = random_date(START_DATE, END_DATE)
    
    if is_fake and f_type == 'shared_device_abuse':
        cluster_id = uid_int % 100 # reduced cluster concentration
        base_reg = START_DATE + timedelta(days=cluster_id * 1.5)
        reg_date = random_date(base_reg, base_reg + timedelta(days=4))
        
    status = 'active'
    if is_fake and random.random() < 0.3:
        status = random.choice(['active', 'suspended', 'banned'])

    # ── Geographic consistency ──────────────────────────────────────────
    # Normal users: pick ONE consistent city/province for their profile & logins
    # Fraudster: profile city may mismatch login geo (geo-hopping)
    home_loc = random.choice(indonesian_cities_ips if 'indonesian_cities_ips' in dir() else [
        {'city': 'Jakarta', 'province': 'DKI Jakarta', 'ip': '103.10.66.'}
    ])
    reg_city     = home_loc['city']
    reg_province = home_loc['province']

    users.append({
        'user_id': user_id,
        'full_name': full_name,
        'email': email,
        'phone_number': phone_number,
        'registration_date': reg_date,
        'registration_channel': random_reg_channel(),  # #5: weighted channels
        'date_of_birth': fake.date_of_birth(minimum_age=17, maximum_age=60),
        'gender': random.choice(['Male', 'Female']),
        'city': reg_city,
        'province': reg_province,
        'is_email_verified': is_email_verified,
        'is_phone_verified': is_phone_verified,
        'account_status': status
    })
    
    fraud_labels.append({
        'user_id': user_id,
        'is_fake_account': is_fake,
        'fraud_type': f_type,
        'fraud_reason': f_reason,
        'label_source': label_src
    })

df_users = pd.DataFrame(users)
df_fraud_labels = pd.DataFrame(fraud_labels)


# --- 3. MEMBUAT DATA PERANGKAT (DEVICES) ---
print("Generating Devices...")
devices = []
for i in range(1, NUM_DEVICES + 1):
    dev_id = f"DEV{i:05d}"
    dtype = random.choice(['android', 'ios'])
    
    if dtype == 'android':
        os_name = 'Android'
        os_ver = random.choice(['10.0', '11.0', '12.0', '13.0', '14.0'])
        app_ver = random.choice(['3.12.0', '3.13.1', '3.14.0'])
    else:
        os_name = 'iOS'
        os_ver = random.choice(['15.5', '16.2', '17.0', '17.3'])
        app_ver = random.choice(['3.12.0', '3.13.0', '3.14.0'])

    # #2: embed real model name inside fingerprint string
    model_name = random_device_model(dtype)
    model_slug = model_name.replace(' ', '_').replace('(', '').replace(')', '')

    first_seen = random_date(START_DATE, END_DATE)
    last_seen = min(first_seen + timedelta(days=random.randint(1, 150)), END_DATE - timedelta(minutes=1))

    devices.append({
        'device_id': dev_id,
        'device_fingerprint': f"FP_{model_slug}_{random.getrandbits(64):016x}",
        'device_type': dtype,
        'os': os_name,
        'os_version': os_ver,
        'app_version': app_ver,
        'first_seen_date': first_seen,
        'last_seen_date': last_seen
    })
df_devices = pd.DataFrame(devices)

# Link User Devices (user_devices.csv)
print("Linking User Devices...")
user_devices = []
user_to_device_map = {}

normal_users = df_fraud_labels[~df_fraud_labels['is_fake_account']]['user_id'].tolist()
fake_users = df_fraud_labels[df_fraud_labels['is_fake_account']]['user_id'].tolist()

# Let's map normal users: mostly 1-to-1 or 1-to-2 devices
# NOISE: 25% of normal users share device fingerprints in small groups of 2-4 users (family sharing)
dev_idx = 0
for u_idx, u_id in enumerate(normal_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    
    if u_idx < int(len(normal_users) * 0.25):
        # Share a device in groups of 3 (increased to 25%)
        d_id = f"DEV{(u_idx // 3) + 1:05d}"
        linked_devs = [d_id]
    else:
        num_devs = 1 if random.random() < 0.75 else 2
        linked_devs = []
        for _ in range(num_devs):
            d_id = f"DEV{(dev_idx % 4000) + 1:05d}" # Leave rest for fraud and noise
            dev_idx += 1
            linked_devs.append(d_id)
            
    for d_id in linked_devs:
        user_devices.append({
            'user_id': u_id,
            'device_id': d_id,
            'first_login_date': u_reg_date,
            'last_login_date': min(u_reg_date + timedelta(days=random.randint(1, 150)), END_DATE - timedelta(minutes=1)),
            'login_count': random.randint(5, 50)
        })
    user_to_device_map[u_id] = linked_devs

# Scenario 1 (Shared Device Abuse) fake users share the same device:
# 500 fake users. 3-5 users share 1 device. So ~120 shared devices needed (pool 4501 to 4700).
# This overlaps heavily with normal family sharing (size 3)!
sc1_users = df_fraud_labels[df_fraud_labels['fraud_type'] == 'shared_device_abuse']['user_id'].tolist()
for idx, u_id in enumerate(sc1_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    # NOISE: 30% dari sc1 pakai device unik sendiri — mirip normal family sharing
    if random.random() < 0.30:
        d_id = f"DEV{random.randint(1, 4000):05d}"  # device normal, bukan shared pool
    else:
        dev_pool_id = 4500 + (idx % 120) + 1
        d_id = f"DEV{dev_pool_id:05d}"

    user_devices.append({
        'user_id': u_id,
        'device_id': d_id,
        'first_login_date': u_reg_date,
        'last_login_date': min(u_reg_date + timedelta(days=random.randint(0, 30)), END_DATE - timedelta(minutes=1)),
        'login_count': random.randint(1, 20)
    })
    user_to_device_map[u_id] = [d_id]

# Emulator Abuse dihapus: skenario fraud hanya 5 tipe utama tanpa emulator.

# Handle remaining fake users
other_fake_users = [u for u in fake_users if u not in sc1_users]
for idx, u_id in enumerate(other_fake_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    d_id = f"DEV{5200 + (idx % 1500) + 1:05d}"
    user_devices.append({
        'user_id': u_id,
        'device_id': d_id,
        'first_login_date': u_reg_date,
        'last_login_date': min(u_reg_date + timedelta(days=random.randint(1, 60)), END_DATE - timedelta(minutes=1)),
        'login_count': random.randint(1, 20)
    })
    user_to_device_map[u_id] = [d_id]

df_user_devices = pd.DataFrame(user_devices)


# --- 4. MEMBUAT DATA ALAMAT PENGIRIMAN ---
print("Generating Addresses...")
addresses = []
for i in range(1, NUM_ADDRESSES + 1):
    # #7: realistic Indonesian address with street prefix
    city_loc = random.choice(indonesian_cities_ips)
    addresses.append({
        'address_id': f"ADR{i:05d}",
        'address_text': realistic_address(),
        'city': city_loc['city'],
        'province': city_loc['province'],
        'postal_code': fake.postcode(),
        'latitude': float(fake.latitude()),
        'longitude': float(fake.longitude())
    })
df_addresses = pd.DataFrame(addresses)

# Link User Addresses (user_addresses.csv)
print("Linking User Addresses...")
user_addresses = []
user_to_address_map = {}

# Normal users
# NOISE: 20% of normal users share address clusters of size 3-10 (offices, apartments, residential blocks)
addr_idx = 0
for u_idx, u_id in enumerate(normal_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    
    if u_idx < int(len(normal_users) * 0.20):
        # 20% share a corporate/apartment group (size 8)
        a_id = f"ADR{(u_idx // 8) + 1:05d}"
    else:
        a_id = f"ADR{(addr_idx % 5000) + 1:05d}"
        addr_idx += 1
        
    user_addresses.append({
        'user_id': u_id,
        'address_id': a_id,
        'is_default_address': True,
        'created_at': u_reg_date
    })
    user_to_address_map[u_id] = [a_id]

# Scenario 2 (Shared Address Abuse):
# 500 fake users. 3-5 users share similar addresses. So ~120 base addresses (5001 to 5120).
sc2_users = df_fraud_labels[df_fraud_labels['fraud_type'] == 'shared_address_abuse']['user_id'].tolist()
shared_address_base_ids = list(range(5001, 5121))

for idx, u_id in enumerate(sc2_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    base_addr_idx = shared_address_base_ids[idx % 120]
    a_id = f"ADR{base_addr_idx:05d}"
    
    user_addresses.append({
        'user_id': u_id,
        'address_id': a_id,
        'is_default_address': True,
        'created_at': u_reg_date
    })
    user_to_address_map[u_id] = [a_id]

# Other fake users
other_fake_users = [u for u in fake_users if u not in sc2_users]
for idx, u_id in enumerate(other_fake_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    a_id = f"ADR{5200 + (idx % 2500) + 1:05d}"
    user_addresses.append({
        'user_id': u_id,
        'address_id': a_id,
        'is_default_address': True,
        'created_at': u_reg_date
    })
    user_to_address_map[u_id] = [a_id]

df_user_addresses = pd.DataFrame(user_addresses)


# --- 5. MEMBUAT DATA PEMBAYARAN (PAYMENTS) ---
print("Generating Payments...")
payments = []
payment_providers = {
    'ewallet': ['GoPay', 'OVO', 'Dana', 'LinkAja', 'ShopeePay'],
    'bank_transfer': ['BCA', 'Mandiri', 'BNI', 'BRI'],
    'credit_card': ['Visa', 'Mastercard', 'JCB'],
    'debit_card': ['BCA Debit', 'Mandiri Debit'],
    'cod': ['Cash On Delivery'],
    'qris': ['QRIS National']
}

for i in range(1, NUM_PAYMENTS + 1):
    ptype = random_payment_type()  # #3: market-weighted
    provider = random.choice(payment_providers[ptype])
    masked = "XXXX-XXXX-" + str(random.randint(1000, 9999))
    token = f"TOK_PAY_{random.getrandbits(64):016x}"

    payments.append({
        'payment_id': f"PMT{i:05d}",
        'payment_type': ptype,
        'payment_provider': provider,
        'masked_payment_number': masked,
        'payment_token': token,
        'created_at': random_date(START_DATE, END_DATE)
    })
df_payments = pd.DataFrame(payments)

# Link User Payments (user_payments.csv)
print("Linking User Payments...")
user_payments = []
user_to_payment_map = {}

# Normal users
# NOISE: 10% of normal users share payment tokens (shared credit card, family bank transfer)
pay_idx = 0
for u_idx, u_id in enumerate(normal_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    
    if u_idx < int(len(normal_users) * 0.10):
        # 10% share a payment token (size 3)
        p_id = f"PMT{(u_idx // 3) + 1:05d}"
    else:
        p_id = f"PMT{(pay_idx % 6500) + 1:05d}"
        pay_idx += 1
        
    user_payments.append({
        'user_id': u_id,
        'payment_id': p_id,
        'linked_at': u_reg_date,
        'is_default_payment': True
    })
    user_to_payment_map[u_id] = [p_id]

# Scenario 3 (Shared Payment Abuse):
# 400 fake users. 3-4 users share payment. So ~110 base payments (6501 to 6610).
sc3_users = df_fraud_labels[df_fraud_labels['fraud_type'] == 'shared_payment_abuse']['user_id'].tolist()
shared_payment_ids = [f"PMT{x:05d}" for x in range(6501, 6611)]

for idx, u_id in enumerate(sc3_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    p_id = shared_payment_ids[idx % 110]
    user_payments.append({
        'user_id': u_id,
        'payment_id': p_id,
        'linked_at': u_reg_date,
        'is_default_payment': True
    })
    user_to_payment_map[u_id] = [p_id]

# Other fake users
other_fake_users = [u for u in fake_users if u not in sc3_users]
for idx, u_id in enumerate(other_fake_users):
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    p_id = f"PMT{6620 + (idx % 2300) + 1:05d}"
    user_payments.append({
        'user_id': u_id,
        'payment_id': p_id,
        'linked_at': u_reg_date,
        'is_default_payment': True
    })
    user_to_payment_map[u_id] = [p_id]

df_user_payments = pd.DataFrame(user_payments)


# --- 6. MEMBUAT DATA REFERRAL (UNDANGAN) ---
print("Generating Referrals...")
referrals = []
ref_count = 0

sc5_users = df_fraud_labels[df_fraud_labels['fraud_type'] == 'referral_abuse']['user_id'].tolist()
sc5_users_sorted = df_users[df_users['user_id'].isin(sc5_users)].sort_values('registration_date')['user_id'].tolist()
for idx, u_id in enumerate(sc5_users_sorted):
    if idx == 0:
        continue
    referrer = sc5_users_sorted[(idx - 1) // 3] # tree-structure
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    
    ref_count += 1
    referrals.append({
        'referral_id': f"REF{ref_count:05d}",
        'referrer_user_id': referrer,
        'referred_user_id': u_id,
        'referral_date': u_reg_date - timedelta(minutes=random.randint(1, 30)),
        'reward_amount': 25000.0,
        'reward_claimed': True
    })

# Add normal referrals
normal_users_sorted = df_users[df_users['user_id'].isin(normal_users)].sort_values('registration_date')['user_id'].tolist()
normal_referrers = normal_users_sorted[:1000]
normal_referred = normal_users_sorted[-1000:]

for idx, referrer in enumerate(normal_referrers):
    ref_count += 1
    referred = normal_referred[idx]
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == referred, 'registration_date'].values[0])
    
    referrals.append({
        'referral_id': f"REF{ref_count:05d}",
        'referrer_user_id': referrer,
        'referred_user_id': referred,
        'referral_date': u_reg_date - timedelta(minutes=random.randint(10, 60)),
        'reward_amount': 25000.0,
        'reward_claimed': random.choice([True, False])
    })
df_referrals = pd.DataFrame(referrals)


# --- 7. MEMBUAT DATA TRANSAKSI BELANJA ---
print("Generating Transactions...")
transactions = []
txn_items = []

txn_count = 0
txn_item_count = 0
product_categories = ['Groceries', 'Electronics', 'Personal Care', 'Home Living', 'Beverages', 'Fresh Food', 'Baby Care']
products = {cat: [f"PROD_{cat[:3].upper()}_{random.randint(100, 999)}" for _ in range(20)] for cat in product_categories}

user_txn_distribution = {}
total_desired_txns = NUM_TRANSACTIONS

# Fake transactions distribution
# NOISE AGRESIF: majority fake users sekarang punya transaksi lebih banyak
for u_id in fake_users:
    f_type = fraud_assignments[u_id]['fraud_type']
    if f_type == 'voucher_farming':
        # Dulu: 60% punya 1 transaksi — terlalu clean
        # Sekarang: hanya 35% yang punya 1 transaksi, sisanya aktif seperti normal churn
        if random.random() < 0.35:
            user_txn_distribution[u_id] = 1
        else:
            user_txn_distribution[u_id] = random.randint(2, 10)
    elif f_type in ('shared_device_abuse', 'shared_address_abuse', 'shared_payment_abuse'):
        # Punya transaksi normal — sinyal utama mereka adalah sharing, bukan volume
        user_txn_distribution[u_id] = random.choices(
            [1, 2, 3, 4, 5, 6, 7, 8],
            weights=[5, 10, 15, 20, 20, 15, 10, 5], k=1)[0]
    else:
        user_txn_distribution[u_id] = random.choice([1, 2, 3, 4, 5])

fake_txn_total = sum(user_txn_distribution.values())
remaining_txns = total_desired_txns - fake_txn_total

# NOISE AGRESIF: 45% normal users punya hanya 1 transaksi (churn)
# DAN 30% dari yang churn itu sesekali punya 2-5 transaksi agar tidak terlalu bersih
normal_churn_users = set(normal_users[:int(len(normal_users) * 0.45)])
remaining_normal_users = [u for u in normal_users if u not in normal_churn_users]

for u_id in normal_churn_users:
    # 30% churn user ternyata beli lagi 1-4x — blur boundary dengan voucher farming
    user_txn_distribution[u_id] = 1 if random.random() < 0.70 else random.randint(2, 5)

remaining_txns -= len(normal_churn_users)

# #8: Poisson-dispersed transaction counts for active normal users
# Use negative-binomial-like sampling (Poisson with Gamma-mixed mean)
normal_active_count = len(remaining_normal_users)
poisson_lam = remaining_txns / normal_active_count
# Add overdispersion: sample the Poisson lambda from a Gamma to get NegBin shape
gamma_means = np.random.gamma(shape=2.0, scale=poisson_lam / 2.0, size=normal_active_count)
normal_txn_counts = np.array([max(1, int(np.random.poisson(lam=m))) for m in gamma_means])
# Scale so total matches remaining_txns closely
scale_factor = remaining_txns / max(1, normal_txn_counts.sum())
normal_txn_counts = np.clip(np.round(normal_txn_counts * scale_factor).astype(int), 1, 30)
for i, u_id in enumerate(remaining_normal_users):
    user_txn_distribution[u_id] = int(normal_txn_counts[i])

# Generate transactions
for u_id, count in user_txn_distribution.items():
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    is_fake = fraud_assignments[u_id]['is_fake_account']
    f_type = fraud_assignments[u_id]['fraud_type']
    
    u_addrs = user_to_address_map.get(u_id, ['ADR00001'])
    u_pmts = user_to_payment_map.get(u_id, ['PMT00001'])
    
    for c in range(count):
        txn_count += 1
        txn_id = f"TXN{txn_count:05d}"
        
        # ── Timing with temporal realism ─────────────────────────────
        if is_fake:
            if random.random() < 0.30:   # 30% space out to look normal
                txn_date = realistic_datetime(u_reg_date,
                                             day_offset_range=(1, 25),
                                             is_fraud=False)
            else:
                txn_date = realistic_datetime(u_reg_date,
                                             day_offset_range=(0, 2),
                                             is_fraud=True)
        else:
            txn_date = realistic_datetime(u_reg_date,
                                         day_offset_range=(c * 5, c * 20 + 1),
                                         is_fraud=False)
            
        if txn_date > END_DATE:
            txn_date = END_DATE - timedelta(minutes=random.randint(1, 100))
            
        # #4: Category-aware pricing — build cart first, derive order_amount from it
        num_items = random.randint(1, 4) if not is_fake else random.randint(1, 2)
        cart = []
        for _ in range(num_items):
            cat = random.choice(product_categories)
            prod = random.choice(products[cat])
            qty = random.randint(1, 3)
            unit_price = float(category_unit_price(cat))
            cart.append({'cat': cat, 'prod': prod, 'qty': qty, 'unit_price': unit_price})

        cart_total = sum(item['unit_price'] * item['qty'] for item in cart)
        cart_total = max(cart_total, 10_000.0)

        # NOISE: 55% of normal transactions utilize vouchers
        # NOISE: 30% of fake transactions are clean (no vouchers)
        use_voucher = False
        if is_fake:
            use_voucher = random.random() < 0.70  # 70% use voucher (30% clean)
        else:
            use_voucher = random.random() < 0.55  # 55% use voucher (high overlap)

        if use_voucher:
            order_amount = float(cart_total)
            if f_type == 'voucher_farming' or c == 0:
                v_id = 'VCH00001'  # NEWUSER50
                promo_discount = min(50000.0, order_amount)
            else:
                v_id = f"VCH{random.randint(2, 80):05d}"
                promo_discount = float(random.choice([10000, 20000]))
        else:
            order_amount = float(cart_total)
            v_id = None
            promo_discount = 0.0

        shipping_fee = float(random.choice([0, 10000, 15000, 20000]))
        final_amount = max(0.0, order_amount + shipping_fee - promo_discount)

        order_status    = 'completed'
        delivery_status = 'delivered'
        payment_status  = 'paid'

        # ── Refund-after-promo abuse (voucher farming) ─────
        if is_fake and f_type == 'voucher_farming' and use_voucher and c == 0 and random.random() < 0.35:
            order_status    = 'cancelled'
            delivery_status = 'cancelled'
            payment_status  = 'refunded'
        elif not is_fake and random.random() < 0.03:  # normal cancel rate ~3%
            order_status    = 'cancelled'
            delivery_status = 'cancelled'
            payment_status  = 'refunded'

        transactions.append({
            'transaction_id': txn_id,
            'user_id': u_id,
            'transaction_date': txn_date,
            'order_amount': order_amount,
            'promo_discount': promo_discount,
            'shipping_fee': shipping_fee,
            'final_amount': final_amount,
            'voucher_id': v_id,
            'payment_id': random.choice(u_pmts),
            'address_id': random.choice(u_addrs),
            'order_status': order_status,
            'delivery_status': delivery_status,
            'payment_status': payment_status
        })

        # Emit cart items
        for item in cart:
            txn_item_count += 1
            subtotal = item['unit_price'] * item['qty']
            txn_items.append({
                'transaction_item_id': f"TXI{txn_item_count:06d}",
                'transaction_id': txn_id,
                'product_id': item['prod'],
                'product_category': item['cat'],
                'quantity': item['qty'],
                'unit_price': item['unit_price'],
                'subtotal': subtotal
            })

df_transactions = pd.DataFrame(transactions)
df_transaction_items = pd.DataFrame(txn_items)


# --- 8. MEMBUAT DATA SESI LOGIN ---
print("Generating Login Sessions...")
login_sessions = []

user_login_counts = {}
for u_id in fake_users:
    f_type = fraud_assignments[u_id]['fraud_type']
    
    # NOISE AGRESIF: distribusi login fake users jauh lebih bervariasi
    if f_type == 'voucher_farming':
        # Dulu 60% login 1x — sekarang hanya 30%
        # Sisanya punya login normal agar mirip real churn user
        if random.random() < 0.30:
            user_login_counts[u_id] = 1
        elif random.random() < 0.50:
            user_login_counts[u_id] = random.randint(2, 8)
        else:
            user_login_counts[u_id] = random.randint(8, 25)  # beberapa aktif banget
    elif f_type in ('shared_device_abuse', 'referral_abuse'):
        # Punya aktivitas login yang cukup normal
        user_login_counts[u_id] = random.randint(3, 20)
    else:
        # shared_address, shared_payment: login normal
        user_login_counts[u_id] = random.randint(5, 30)

fake_login_total = sum(user_login_counts.values())
remaining_logins = NUM_LOGINS - fake_login_total

# Distribute remaining to normal users using random variance instead of absolute division
normal_user_count = len(normal_users)
# Use a random distribution for normal users' login count (Poisson or Negative Binomial shape)
normal_logins = np.random.poisson(lam=(remaining_logins / normal_user_count), size=normal_user_count)
# Clamp at minimum 1 login session
normal_logins = np.clip(normal_logins, 1, 40).astype(int)

# Sesuaikan total login agar mendekati/tepat NUM_LOGINS tanpa membuat user 0 login.
current_total = fake_login_total + int(normal_logins.sum())
diff = NUM_LOGINS - current_total

if diff > 0:
    for _ in range(diff):
        idx_add = random.randrange(normal_user_count)
        normal_logins[idx_add] += 1
elif diff < 0:
    # Kurangi login dari user yang punya >1 sampai total tepat.
    removable_indices = [i for i, v in enumerate(normal_logins) if v > 1]
    for _ in range(abs(diff)):
        if not removable_indices:
            break
        idx_sub = random.choice(removable_indices)
        normal_logins[idx_sub] -= 1
        if normal_logins[idx_sub] <= 1:
            removable_indices.remove(idx_sub)

for idx, u_id in enumerate(normal_users):
    user_login_counts[u_id] = int(normal_logins[idx])

# indonesian_cities_ips already defined at top of file

# Build per-user home location map (used for geo consistency in sessions)
user_home_loc = {}
for row in df_users.itertuples():
    matched = next(
        (loc for loc in indonesian_cities_ips if loc['city'] == row.city),
        random.choice(indonesian_cities_ips)
    )
    user_home_loc[row.user_id] = matched

session_count = 0
for u_id, count in user_login_counts.items():
    u_reg_date = pd.to_datetime(df_users.loc[df_users['user_id'] == u_id, 'registration_date'].values[0])
    is_fake   = fraud_assignments[u_id]['is_fake_account']
    f_type    = fraud_assignments[u_id]['fraud_type']
    u_devs    = user_to_device_map.get(u_id, ['DEV00001'])

    # Home location — normal users are geographically consistent
    home_loc  = user_home_loc.get(u_id, random.choice(indonesian_cities_ips))

    # Persona jam login per user.
    # Ini sumber utama agar login frequency bucket 1/2/3/4/5/6/12/18/24 bisa 0.
    login_persona = choose_login_persona(is_fraud=is_fake, fraud_type=f_type)

    # Fraud tertentu dibuat burst supaya tetap ada sinyal velocity/ring yang kuat.
    is_burst_mode = False
    burst_base_time = None
    if is_fake and count >= 3 and random.random() < 0.35:
        is_burst_mode = True
        burst_base_time = persona_login_datetime(
            u_reg_date,
            day_offset_range=(0, 2),
            persona='fraud_night',
            is_fraud=True
        )

    for c in range(count):
        session_count += 1
        session_id = f"SES{session_count:06d}"

        # ── Temporal realism: timestamp login berbasis persona ──
        if is_burst_mode:
            # Burst ditumpuk dalam 45 menit dari base time.
            login_time = burst_base_time + timedelta(seconds=random.randint(5, 2700))
        elif is_fake:
            if random.random() < 0.25:
                # Sebagian fake meniru pola normal.
                login_time = persona_login_datetime(
                    u_reg_date,
                    day_offset_range=(c, c + 5),
                    persona='fraud_mimic',
                    is_fraud=False
                )
            else:
                # Sebagian fake aktif di jam rawan/dini hari.
                login_time = persona_login_datetime(
                    u_reg_date,
                    day_offset_range=(0, max(1, c)),
                    persona=login_persona,
                    is_fraud=True
                )
        else:
            # Normal user: login menyebar antar hari, tetapi jamnya mengikuti persona.
            login_time = persona_login_datetime(
                u_reg_date,
                day_offset_range=(c * 1, c * 15 + 1),
                persona=login_persona,
                is_fraud=False
            )

        dur = session_duration(is_fraud=is_fake, fraud_type=f_type)
        logout_time = login_time + timedelta(seconds=dur)

        # ── IP address & geographic consistency ───────────────────────
        if not is_fake:
            # Normal users: variatif — campuran WiFi rumah, mobile data, kantor
            roll = random.random()
            if c > 0 and roll < 0.55:
                ip       = home_loc['ip'] + str(random.randint(2, 50))
                geo_city = home_loc['city']
                geo_prov = home_loc['province']
            elif roll < 0.80:
                alt_loc  = random.choice(indonesian_cities_ips)
                ip       = alt_loc['ip'] + str(random.randint(51, 200))
                geo_city = home_loc['city']
                geo_prov = home_loc['province']
            else:
                ip       = home_loc['ip'] + str(random.randint(100, 254))
                geo_city = home_loc['city']
                geo_prov = home_loc['province']

        else:
            if f_type == 'shared_device_abuse':
                roll = random.random()
                if roll < 0.40:
                    ip       = '103.110.12.' + str((hash(u_id) % 25) + 1)
                    geo_city = home_loc['city']
                    geo_prov = home_loc['province']
                elif roll < 0.75:
                    ip       = home_loc['ip'] + str(random.randint(1, 254))
                    geo_city = home_loc['city']
                    geo_prov = home_loc['province']
                else:
                    drift_loc = random.choice(indonesian_cities_ips)
                    ip        = drift_loc['ip'] + str(random.randint(1, 254))
                    geo_city  = drift_loc['city']
                    geo_prov  = drift_loc['province']
            else:
                # shared_address, shared_payment, referral, voucher_farming
                if random.random() < 0.50:
                    ip       = home_loc['ip'] + str(random.randint(1, 254))
                    geo_city = home_loc['city']
                    geo_prov = home_loc['province']
                else:
                    drift_loc = random.choice(indonesian_cities_ips)
                    ip        = drift_loc['ip'] + str(random.randint(1, 254))
                    geo_city  = drift_loc['city']
                    geo_prov  = drift_loc['province']

        login_sessions.append({
            'session_id':              session_id,
            'user_id':                 u_id,
            'device_id':               random.choice(u_devs),
            'ip_address':              ip,
            'login_timestamp':         login_time,
            'logout_timestamp':        logout_time,
            'session_duration_seconds': dur,
            'geo_city':                geo_city,
            'geo_province':            geo_prov,
            'login_persona':           login_persona
        })
df_login_sessions = pd.DataFrame(login_sessions)


# --- 9. MENYIMPAN KE DALAM CSV ---
print("Saving all CSV files to data/raw/...")

df_vouchers.to_csv(os.path.join(OUTPUT_DIR, 'vouchers.csv'), index=False)
df_users.to_csv(os.path.join(OUTPUT_DIR, 'users.csv'), index=False)
df_devices.to_csv(os.path.join(OUTPUT_DIR, 'devices.csv'), index=False)
df_user_devices.to_csv(os.path.join(OUTPUT_DIR, 'user_devices.csv'), index=False)
df_addresses.to_csv(os.path.join(OUTPUT_DIR, 'addresses.csv'), index=False)
df_user_addresses.to_csv(os.path.join(OUTPUT_DIR, 'user_addresses.csv'), index=False)
df_payments.to_csv(os.path.join(OUTPUT_DIR, 'payments.csv'), index=False)
df_user_payments.to_csv(os.path.join(OUTPUT_DIR, 'user_payments.csv'), index=False)
df_referrals.to_csv(os.path.join(OUTPUT_DIR, 'referrals.csv'), index=False)
df_transactions.to_csv(os.path.join(OUTPUT_DIR, 'transactions.csv'), index=False)
df_transaction_items.to_csv(os.path.join(OUTPUT_DIR, 'transaction_items.csv'), index=False)
df_login_sessions.to_csv(os.path.join(OUTPUT_DIR, 'login_sessions.csv'), index=False)
df_fraud_labels.to_csv(os.path.join(OUTPUT_DIR, 'fraud_labels.csv'), index=False)

print("\n--- Generation complete with extreme noise! ---")
print(f"Users generated: {len(df_users)}")
print(f"Transactions generated: {len(df_transactions)}")
print(f"Fraud ratio: {df_fraud_labels['is_fake_account'].mean() * 100:.2f}%")

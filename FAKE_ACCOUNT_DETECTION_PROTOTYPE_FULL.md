# TASK INTERN — FAKE ACCOUNT DETECTION PROTOTYPE UNTUK MOBILE RETAIL APP

> Full Markdown conversion from the original PDF. No project requirement details were intentionally removed.

TASK INTERN — FAKE ACCOUNT
DETECTION PROTOTYPE UNTUK
MOBILE RETAIL APP
1. Objective
Minggu ini kamu diminta membuat end-to-end prototype untuk fake account
detection pada aplikasi mobile retail/e-commerce, dengan studi eksplorasi
mengacu pada salah satu aplikasi retail yang memiliki fitur seperti:

    •    registrasi user
    •    login
    •    promo/voucher
    •    transaksi
    •    pembayaran
    •    alamat pengiriman
    •    loyalty/reward
    •    referral jika ada
    •    history order
    •    device/session activity

Prototype ini harus mencakup:

    1. eksplorasi aplikasi mobile retail,
    2. synthetic data generation selama 6 bulan,
    3. feature engineering untuk fake account detection,
    4. analytics base table final untuk training dan testing,
    5. model machine learning untuk mendeteksi fake account,
    6. visualisasi graph analytics dari analytics base table,
    7. chatbot yang bisa menjawab pertanyaan berdasarkan analytics base table,
    8. API untuk inference model,
    9. deployment frontend ke Vercel,
    10. dokumentasi standar backend, frontend, model, API, dan deployment.


2. Expected Final Deliverables
Pada akhir minggu, output yang wajib dikumpulkan adalah:

A. Documentation

  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

Buat folder /docs berisi:

    1. 01_mobile_app_exploration.md
    2. 02_data_model_design.md
    3. 03_synthetic_data_generation.md
    4. 04_eda_report.md
    5. 05_feature_engineering.md
    6. 06_modeling_report.md
    7. 07_graph_analytics_design.md
    8. 08_chatbot_design.md
    9. 09_api_documentation.md
    10. 10_deployment_guide.md
    11. README.md


B. Source Code
Struktur repository wajib seperti ini:

fake-account-detection-retail/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │    ├── prediction.py
│   │   │    ├── graph.py
│   │   │    └── chatbot.py
│   │   ├── services/
│   │   │    ├── model_service.py
│   │   │    ├── graph_service.py
│   │   │    └── chatbot_service.py
│   │   ├── schemas/
│   │   │    └── request_response.py
│   │   └── utils/
│   │        └── config.py
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── pages/
│   ├── lib/
│   ├── package.json
│   └── README.md
│
├── data/
│   ├── raw/
│   ├── processed/


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

│   └── abt/
│
├── notebooks/
│   ├── 01_generate_synthetic_data.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_model_training.ipynb
│   └── 05_graph_analytics.ipynb
│
├── models/
│   ├── fake_account_model.pkl
│   ├── feature_columns.json
│   └── model_metrics.json
│
├── scripts/
│   ├── generate_data.py
│   ├── build_abt.py
│   ├── train_model.py
│   └── run_inference.py
│
├── docs/
│
└── README.md


3. Step 1 — Explore Mobile Retail
Application
Pilih satu aplikasi mobile retail sebagai referensi. Contoh:

    •    Alfagift
    •    Klik Indomaret
    •    Tokopedia
    •    Shopee
    •    Blibli
    •    Lazada
    •    aplikasi retail sejenis

Tujuan eksplorasi adalah memahami flow aplikasi, bukan mengambil data asli.

Yang harus dieksplorasi
Catat fitur-fitur berikut:

    1.   proses registrasi user,
    2.   data apa saja yang diminta saat registrasi,
    3.   login method,
    4.   OTP atau tidak,


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

    5. fitur voucher,
    6. fitur promo,
    7. fitur referral jika ada,
    8. fitur loyalty/reward,
    9. proses checkout,
    10. pilihan pembayaran,
    11. alamat pengiriman,
    12. order history,
    13. transaksi gagal/sukses,
    14. refund/cancel order jika ada,
    15. behaviour user yang bisa menjadi indikasi abuse.

Output
Buat dokumen:

/docs/01_mobile_app_exploration.md

Isi minimal:

# Mobile App Exploration

## Application Name
...

## Main User Journey
1. Registration
2. Login
3. Browse Product
4. Apply Voucher
5. Checkout
6. Payment
7. Delivery

## Potential Fraud Points
1. Multiple accounts using same device
2. Multiple accounts using same address
3. Voucher farming
4. Referral abuse
5. Free shipping abuse
6. Promo abuse

## Required Synthetic Data Tables
1. users
2. devices
3. user_devices
4. addresses
5. user_addresses
6. payments
7. user_payments
8. vouchers


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

9. transactions
10. transaction_items
11. logins
12. sessions
13. referrals
14. fraud_labels


4. Step 2 — Synthetic Data Generation
Buat synthetic data yang menyerupai data aplikasi retail mobile.

Durasi data:

6 bulan

Jumlah minimum data:

users: 10,000
transactions: 50,000
devices: 7,000
addresses: 8,000
payments: 9,000
vouchers: 500
login/session logs: 100,000

Data tidak boleh menggunakan data asli customer.

Gunakan Python Faker.

Install library:

pip install pandas numpy faker scikit-learn networkx fastapi
uvicorn joblib xgboost python-dotenv


5. Required Tables
5.1 users.csv
Kolom:

user_id
full_name
email
phone_number
registration_date


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

registration_channel
date_of_birth
gender
city
province
is_email_verified
is_phone_verified
account_status

Tambahkan pola fake account:

    •    email random,
    •    phone mirip,
    •    banyak akun dibuat dalam waktu berdekatan,
    •    akun tanpa verifikasi,
    •    akun hanya aktif saat promo.


5.2 devices.csv
Kolom:

device_id
device_fingerprint
device_type
os
os_version
app_version
is_emulator
is_rooted
first_seen_date
last_seen_date

Fake pattern:

    •    1 device dipakai banyak user,
    •    emulator,
    •    rooted device,
    •    fingerprint sama.


5.3 user_devices.csv
Kolom:

user_id
device_id


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

first_login_date
last_login_date
login_count

Fake pattern:

    •    1 device terhubung ke 5–50 user.


5.4 addresses.csv
Kolom:

address_id
address_text
city
province
postal_code
latitude
longitude
address_similarity_group

Fake pattern:

    •    banyak user pakai alamat yang sama,
    •    alamat mirip dengan variasi penulisan.


5.5 user_addresses.csv
Kolom:

user_id
address_id
is_default_address
created_at


5.6 payments.csv
Kolom:

payment_id
payment_type
payment_provider
masked_payment_number


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

payment_token
created_at

Payment type:

ewallet
bank_transfer
credit_card
debit_card
cod
qris

Fake pattern:

    •    1 payment dipakai banyak akun,
    •    payment token sama,
    •    banyak akun memakai e-wallet sama.


5.7 user_payments.csv
Kolom:

user_id
payment_id
linked_at
is_default_payment


5.8 vouchers.csv
Kolom:

voucher_id
voucher_code
voucher_type
discount_amount
discount_percentage
min_purchase_amount
start_date
end_date
max_usage
promo_category

Promo category:

new_user_promo
free_shipping


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

cashback
flash_sale
loyalty_reward
referral_reward


5.9 transactions.csv
Kolom:

transaction_id
user_id
transaction_date
order_amount
promo_discount
shipping_fee
final_amount
voucher_id
payment_id
address_id
order_status
delivery_status
payment_status

Fake pattern:

    •    akun baru langsung transaksi,
    •    transaksi selalu pakai voucher,
    •    order kecil hanya untuk mengambil promo,
    •    banyak akun transaksi ke alamat sama.


5.10 transaction_items.csv
Kolom:

transaction_item_id
transaction_id
product_id
product_category
quantity
unit_price
subtotal


5.11 login_sessions.csv
Kolom:


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

session_id
user_id
device_id
ip_address
login_timestamp
logout_timestamp
session_duration_seconds
is_vpn
is_proxy
geo_city
geo_province

Fake pattern:

    •    IP sama dipakai banyak user,
    •    VPN/proxy,
    •    banyak login dalam waktu pendek.


5.12 referrals.csv
Kolom:

referral_id
referrer_user_id
referred_user_id
referral_date
reward_amount
reward_claimed

Fake pattern:

    •    referral ring,
    •    1 akun refer banyak fake account,
    •    akun saling mereferensikan.


5.13 fraud_labels.csv
Kolom:

user_id
is_fake_account
fraud_type
fraud_reason
label_source


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

Fraud type:

shared_device_abuse
shared_payment_abuse
shared_address_abuse
voucher_farming
referral_abuse
emulator_abuse
promo_abuse
normal


6. Synthetic Fraud Scenarios
Data synthetic harus mengandung beberapa skenario fake account.

Scenario 1 — Shared Device Abuse
Contoh:

20 user menggunakan device_id yang sama.
Semua akun dibuat dalam 2 hari.
Semua menggunakan voucher new user promo.


Scenario 2 — Shared Address Abuse
Contoh:

30 user menggunakan alamat sama atau alamat mirip.
Masing-masing mengambil promo new user.


Scenario 3 — Shared Payment Abuse
Contoh:

15 user menggunakan payment token yang sama.
Transaksi nominal kecil.
Semua memakai voucher.


Scenario 4 — Voucher Farming
Contoh:


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

Banyak akun baru dibuat hanya untuk mengambil voucher.
Akun tidak aktif setelah transaksi pertama.


Scenario 5 — Referral Ring
Contoh:

User A mereferensikan User B, C, D, E.
User B mereferensikan User F, G, H.
Akun saling terhubung melalui device, alamat, atau payment.


Scenario 6 — Emulator Abuse
Contoh:

Banyak akun login dari emulator.
Device rooted.
IP address sama.


7. Analytics Base Table Final
Buat final table untuk modeling:

/data/abt/fake_account_abt.csv

Level data:

1 row = 1 user

Kolom minimum:

user_id
account_age_days
days_since_last_login
total_transactions
total_order_amount
avg_order_amount
total_promo_discount
promo_order_ratio
voucher_usage_count
new_user_voucher_usage
free_shipping_usage
unique_devices
accounts_per_device_max
unique_addresses


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

accounts_per_address_max
unique_payments
accounts_per_payment_max
unique_ip_addresses
accounts_per_ip_max
login_count
login_velocity_24h
is_emulator_used
is_rooted_device_used
vpn_login_ratio
proxy_login_ratio
signup_to_first_transaction_minutes
referral_count
referred_by_user_flag
referral_ring_score
graph_degree
graph_cluster_size
risk_score_rule_based
is_fake_account
fraud_type

Target label:

is_fake_account


8. Feature Engineering
Buat script:

/scripts/build_abt.py

Feature yang wajib dibuat:

Identity Features
email_length
email_numeric_ratio
email_randomness_score
is_disposable_email_domain
phone_pattern_score


Device Features
unique_devices
accounts_per_device_max
is_emulator_used
is_rooted_device_used


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

Address Features
unique_addresses
accounts_per_address_max
address_reuse_flag


Payment Features
unique_payments
accounts_per_payment_max
payment_reuse_flag


Transaction Features
total_transactions
avg_order_amount
total_order_amount
promo_order_ratio
voucher_usage_count
signup_to_first_transaction_minutes


Login Features
login_count
unique_ip_addresses
accounts_per_ip_max
vpn_login_ratio
proxy_login_ratio
login_velocity_24h


Referral Features
referral_count
referred_by_user_flag
referral_ring_score


Graph Features
graph_degree
graph_cluster_size
connected_component_size
shared_entity_count


9. EDA

 Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                             Info@v-teki.com |www.v-teki.com


---

Buat notebook:

/notebooks/02_eda.ipynb

Minimal analisis:

    1. total users,
    2. total transactions,
    3. fake vs normal distribution,
    4. fraud type distribution,
    5. account age distribution,
    6. promo usage distribution,
    7. accounts per device,
    8. accounts per address,
    9. accounts per payment,
    10. transactions by month,
    11. top suspicious devices,
    12. top suspicious addresses,
    13. top suspicious payments,
    14. correlation between features and fake account label.

Visualisasi wajib:

bar chart
histogram
boxplot
correlation heatmap
time series monthly transaction


10. Modeling
Buat notebook:

/notebooks/04_model_training.ipynb

Buat script:

/scripts/train_model.py

Model minimal:

    1. Logistic Regression,
    2. Random Forest,
    3. XGBoost atau LightGBM.


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

Kalau XGBoost belum bisa, gunakan Random Forest dulu.

Train-test split:

train: 70%
test: 30%

Metric wajib:

accuracy
precision
recall
f1-score
roc-auc
confusion matrix
classification report
feature importance

Karena fraud detection lebih penting menangkap fraud, prioritaskan:

recall untuk fake account
precision untuk mengurangi false positive
f1-score sebagai balance

Output model:

/models/fake_account_model.pkl
/models/feature_columns.json
/models/model_metrics.json


11. Rule-Based Risk Score
Selain ML model, buat juga rule-based score.

Contoh logic:

accounts_per_device_max > 5 = +25
accounts_per_payment_max > 3 = +20
accounts_per_address_max > 5 = +20
promo_order_ratio > 0.8 = +10
is_emulator_used = +15
vpn_login_ratio > 0.5 = +10
signup_to_first_transaction_minutes < 30 = +10

Risk category:

0–30 = Low Risk
31–60 = Medium Risk
61–100 = High Risk


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

Tambahkan ke ABT:

risk_score_rule_based
risk_category


12. Graph Analytics
Buat notebook:

/notebooks/05_graph_analytics.ipynb

Buat graph dari analytics base table dan relational data.

Node:

User
Device
Address
Payment
IP
Voucher

Edge:

User uses Device
User uses Payment
User ships to Address
User login from IP
User redeems Voucher

Graph metrics:

degree centrality
connected component size
community detection
shared entity count
fraud cluster size

Output graph data untuk frontend:

/data/processed/graph_nodes.json
/data/processed/graph_edges.json

Format nodes:

{
    "id": "U001",
    "label": "User U001",


    Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                                Info@v-teki.com |www.v-teki.com


---

    "type": "user",
    "risk_score": 85,
    "risk_category": "High"
}

Format edges:

{
    "source": "U001",
    "target": "DVC001",
    "relationship": "uses_device"
}


13. Frontend Dashboard
Gunakan:

Next.js
React
Tailwind CSS
Vercel

Library graph:

react-force-graph-2d

Dashboard minimal memiliki halaman:

1. Overview Page
Isi:

total users
total fake accounts
fake account rate
total transactions
total promo discount
estimated promo abuse amount
high risk users


2. Risk Scoring Page
Tabel user:

user_id
risk_score


    Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                                Info@v-teki.com |www.v-teki.com


---

risk_category
prediction
fraud_type
top_reason

Filter:

risk_category
fraud_type
city
device
payment
address


3. Graph Analytics Page
Tampilkan graph:

User - Device - Address - Payment - IP - Voucher

Fitur:

zoom
search user_id
filter high risk only
filter by fraud type
click node to see detail

Saat klik node user, tampilkan:

user_id
risk_score
fraud_type
connected devices
connected payments
connected addresses
connected IPs
model prediction
top suspicious reasons


4. Model Inference Page
Form input manual:

accounts_per_device_max
accounts_per_payment_max
accounts_per_address_max
promo_order_ratio


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

is_emulator_used
vpn_login_ratio
signup_to_first_transaction_minutes

Output:

prediction: fake / normal
probability score
risk category
top reasons


5. Chatbot Page
Chatbot bisa menjawab pertanyaan dari analytics base table.

Contoh pertanyaan:

Why is user U001 suspicious?
Show top 10 high risk users.
Which devices are shared by many accounts?
Which addresses are used by multiple fake accounts?
How many fake accounts use emulator?
What is the most common fraud pattern?
Show fraud cluster related to device DVC001.


14. Backend API
Gunakan:

FastAPI

Buat endpoint:

Health Check
GET /health

Response:

{
    "status": "ok"
}


Predict Single User

    Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                                Info@v-teki.com |www.v-teki.com


---

POST /predict

Request:

{
    "accounts_per_device_max": 8,
    "accounts_per_payment_max": 3,
    "accounts_per_address_max": 5,
    "promo_order_ratio": 0.9,
    "is_emulator_used": 1,
    "vpn_login_ratio": 0.7,
    "signup_to_first_transaction_minutes": 10
}

Response:

{
    "prediction": "fake_account",
    "probability": 0.91,
    "risk_category": "High",
    "top_reasons": [
      "Device is shared by many accounts",
      "High promo usage ratio",
      "Emulator detected"
    ]
}


Get User Risk Detail
GET /user/{user_id}

Response:

{
    "user_id": "U001",
    "risk_score": 88,
    "prediction": "fake_account",
    "fraud_type": "shared_device_abuse",
    "top_reasons": [
      "User shares device with 15 accounts",
      "User used new user voucher",
      "Signup to first transaction below 30 minutes"
    ]
}


Get Top Risk Users
GET /risk/top-users


    Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                                Info@v-teki.com |www.v-teki.com


---

Get Graph Data
GET /graph

Response:

{
    "nodes": [],
    "edges": []
}


Chatbot
POST /chat

Request:

{
    "question": "Why is user U001 suspicious?"
}

Response:

{
  "answer": "User U001 is suspicious because it shares the same
device with 15 other accounts, has a promo order ratio of 100%,
and completed the first transaction 12 minutes after signup."
}


15. Chatbot Requirement
Untuk tahap awal, chatbot boleh dibuat rule-based/RAG sederhana dari analytics
base table.

Tidak perlu LLM kompleks dulu.

Minimum chatbot logic:

      1.   load fake_account_abt.csv,
      2.   parse question sederhana,
      3.   jika ada user_id, ambil data user,
      4.   jika pertanyaan top risk, tampilkan top 10,
      5.   jika pertanyaan fraud type, hitung distribusi,
      6.   jika pertanyaan device/address/payment, tampilkan shared entity.


    Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                                Info@v-teki.com |www.v-teki.com


---

Contoh jawaban:

User U001 is classified as high risk because:
1. It shares device DVC001 with 18 other accounts.
2. It uses payment PAY001 used by 9 other accounts.
3. It redeemed new user voucher within 10 minutes after
registration.
4. Its rule-based risk score is 92.
5. The ML model predicts fake account with probability 0.94.


16. Deployment
Frontend
Deploy ke:

Vercel

Frontend harus memiliki:

.env.local
NEXT_PUBLIC_API_URL=


Backend
Backend boleh dijalankan lokal dulu, atau deploy ke:

Render
Railway
Fly.io
Hugging Face Spaces

Jika belum deploy backend, minimal frontend tetap bisa membaca static
JSON/CSV sample.


17. README Requirement
README wajib berisi:

# Fake Account Detection Retail App Prototype

## Objective
## Features


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

## Architecture
## Folder Structure
## Dataset Description
## How to Generate Synthetic Data
## How to Build Analytics Base Table
## How to Train Model
## How to Run API
## How to Run Frontend
## How to Deploy to Vercel
## API Documentation
## Example Inference
## Graph Analytics Explanation
## Chatbot Usage
## Future Improvements


18. Development Standard
Backend Standard
Wajib:

FastAPI
modular folder
requirements.txt
clear endpoint documentation
error handling
config using .env

Run command:

cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload


Frontend Standard
Wajib:

Next.js
Tailwind CSS
component-based structure
responsive dashboard
clean UI

Run command:

cd frontend


 Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                             Info@v-teki.com |www.v-teki.com


---

npm install
npm run dev

Deploy:

vercel


Data Science Standard
Wajib:

notebooks clean
scripts reusable
random seed fixed
train-test split clear
metrics saved
model saved
feature list saved


Git Standard
Commit minimal per progress:

init project structure
add synthetic data generator
add EDA notebook
add feature engineering
add model training
add FastAPI backend
add frontend dashboard
add graph visualization
add chatbot
add documentation


19. Timeline
Day 1 — Mobile App Exploration + Data Model
Output:

mobile app exploration document
data table design
ERD simple


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

Day 2 — Synthetic Data Generation
Output:

all CSV tables generated
6 months synthetic data
fraud scenarios embedded


Day 3 — EDA + Feature Engineering
Output:

EDA notebook
feature engineering script
analytics base table final


Day 4 — Model Training + API
Output:

trained model
model metrics
FastAPI inference endpoint


Day 5 — Graph Analytics + Dashboard + Chatbot
Output:

graph nodes/edges
frontend dashboard
chatbot page
Vercel deployment
final documentation


20. Acceptance Criteria
Project dianggap selesai jika:

    1. synthetic data berhasil dibuat untuk 6 bulan,
    2. minimal 10.000 users dan 50.000 transactions,
    3. semua tabel utama tersedia dalam CSV,


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

    4. analytics base table final tersedia,
    5. minimal 20 feature fake account tersedia,
    6. model berhasil dilatih,
    7. model metrics tersedia,
    8. API /predict bisa dites,
    9. graph analytics bisa divisualisasikan,
    10. chatbot bisa menjawab minimal 5 jenis pertanyaan,
    11. frontend berhasil deploy ke Vercel,
    12. README lengkap,
    13. dokumentasi backend, frontend, data, model, API, dan deployment
        lengkap.


21. Minimum Demo Scenario
Saat demo, pastikan bisa menunjukkan:

Demo 1 — Model Prediction
Input user risk feature ke halaman inference.

Output:

Fake account probability: 91%
Risk category: High
Reason: shared device, high promo usage, emulator detected


Demo 2 — Graph Analytics
Tampilkan cluster:

20 users connected to same device
10 users connected to same payment
15 users connected to same address


Demo 3 — Chatbot
Tanya:

Why is user U001 suspicious?

Jawaban:


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

User U001 is suspicious because it shares the same device with 18
accounts, uses a payment method shared by 9 accounts, has a promo
order ratio of 100%, and completed the first transaction 12
minutes after registration.


22. Notes
Prototype ini tidak menggunakan data asli customer. Semua data harus synthetic.

Tujuan project ini adalah membangun proof-of-concept bahwa fake account
detection bisa dilakukan melalui kombinasi:

rule-based scoring
machine learning
graph analytics
chatbot explanation

Fokus utama bukan hanya model accuracy, tetapi juga explainability dan business
usability.


  Treasury Tower, 6th Floor Unit F, District 8 Building, SCBD Lot 28 Jl. Jend. Sudirman Kav. 52–53 Jakarta Selatan 12190
                                              Info@v-teki.com |www.v-teki.com


---

-- Purpose: Define Supabase PostgreSQL tables for the fraud detection prototype.
-- Used by: upload scripts and backend Supabase fallback queries.
-- Main dependencies: Generated raw CSVs, ABT CSV, Supabase PostgreSQL.
-- Public/main objects: users, devices, graph source tables, fake_account_abt.
-- Side effects: Drops existing prototype tables, then recreates the current schema.

DROP TABLE IF EXISTS fake_account_abt;
DROP TABLE IF EXISTS fraud_labels;
DROP TABLE IF EXISTS referrals;
DROP TABLE IF EXISTS login_sessions;
DROP TABLE IF EXISTS transaction_items;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS vouchers;
DROP TABLE IF EXISTS user_payments;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS user_addresses;
DROP TABLE IF EXISTS addresses;
DROP TABLE IF EXISTS user_devices;
DROP TABLE IF EXISTS devices;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    user_id         VARCHAR PRIMARY KEY,
    full_name       VARCHAR,
    email           VARCHAR,
    phone_number    VARCHAR,
    registration_date TIMESTAMP,
    registration_channel VARCHAR,  -- email | google | facebook | phone
    date_of_birth   DATE,
    gender          VARCHAR,
    city            VARCHAR,
    province        VARCHAR,
    is_email_verified BOOLEAN,
    is_phone_verified BOOLEAN,
    account_status  VARCHAR        -- active | suspended | banned
);

CREATE TABLE devices (
    device_id           VARCHAR PRIMARY KEY,
    device_fingerprint  VARCHAR,
    device_type         VARCHAR,   -- android | ios
    os                  VARCHAR,
    os_version          VARCHAR,
    app_version         VARCHAR,
    first_seen_date     TIMESTAMP,
    last_seen_date      TIMESTAMP
);

CREATE TABLE user_devices (
    user_id         VARCHAR REFERENCES users(user_id),
    device_id       VARCHAR REFERENCES devices(device_id),
    first_login_date TIMESTAMP,
    last_login_date  TIMESTAMP,
    login_count      INTEGER,
    PRIMARY KEY (user_id, device_id)
);

CREATE TABLE addresses (
    address_id              VARCHAR PRIMARY KEY,
    address_text            TEXT,
    city                    VARCHAR,
    province                VARCHAR,
    postal_code             VARCHAR,
    latitude                DECIMAL(9,6),
    longitude               DECIMAL(9,6)
);

CREATE TABLE user_addresses (
    user_id            VARCHAR REFERENCES users(user_id),
    address_id         VARCHAR REFERENCES addresses(address_id),
    is_default_address BOOLEAN,
    created_at         TIMESTAMP,
    PRIMARY KEY (user_id, address_id)
);

CREATE TABLE payments (
    payment_id             VARCHAR PRIMARY KEY,
    payment_type           VARCHAR,   -- ewallet | bank_transfer | credit_card | debit_card | cod | qris
    payment_provider       VARCHAR,
    masked_payment_number  VARCHAR,
    payment_token          VARCHAR,
    created_at             TIMESTAMP
);

CREATE TABLE user_payments (
    user_id            VARCHAR REFERENCES users(user_id),
    payment_id         VARCHAR REFERENCES payments(payment_id),
    linked_at          TIMESTAMP,
    is_default_payment BOOLEAN,
    PRIMARY KEY (user_id, payment_id)
);

CREATE TABLE vouchers (
    voucher_id           VARCHAR PRIMARY KEY,
    voucher_code         VARCHAR UNIQUE,
    voucher_type         VARCHAR,    -- percentage | fixed_amount
    discount_amount      DECIMAL,
    discount_percentage  DECIMAL,
    min_purchase_amount  DECIMAL,
    start_date           TIMESTAMP,
    end_date             TIMESTAMP,
    max_usage            INTEGER,
    promo_category       VARCHAR     -- new_user_promo | free_shipping | cashback | flash_sale | loyalty_reward | referral_reward
);

CREATE TABLE transactions (
    transaction_id   VARCHAR PRIMARY KEY,
    user_id          VARCHAR REFERENCES users(user_id),
    transaction_date TIMESTAMP,
    order_amount     DECIMAL,
    promo_discount   DECIMAL,
    shipping_fee     DECIMAL,
    final_amount     DECIMAL,
    voucher_id       VARCHAR REFERENCES vouchers(voucher_id),
    payment_id       VARCHAR REFERENCES payments(payment_id),
    address_id       VARCHAR REFERENCES addresses(address_id),
    order_status     VARCHAR,
    delivery_status  VARCHAR,
    payment_status   VARCHAR
);

CREATE TABLE transaction_items (
    transaction_item_id VARCHAR PRIMARY KEY,
    transaction_id      VARCHAR REFERENCES transactions(transaction_id),
    product_id          VARCHAR,
    product_category    VARCHAR,
    quantity            INTEGER,
    unit_price          DECIMAL,
    subtotal            DECIMAL
);

CREATE TABLE login_sessions (
    session_id              VARCHAR PRIMARY KEY,
    user_id                 VARCHAR REFERENCES users(user_id),
    device_id               VARCHAR REFERENCES devices(device_id),
    ip_address              VARCHAR,
    login_timestamp         TIMESTAMP,
    logout_timestamp        TIMESTAMP,
    session_duration_seconds INTEGER,
    geo_city                VARCHAR,
    geo_province            VARCHAR,
    login_persona           VARCHAR
);

CREATE TABLE referrals (
    referral_id       VARCHAR PRIMARY KEY,
    referrer_user_id  VARCHAR REFERENCES users(user_id),
    referred_user_id  VARCHAR REFERENCES users(user_id),
    referral_date     TIMESTAMP,
    reward_amount     DECIMAL,
    reward_claimed    BOOLEAN
);

CREATE TABLE fraud_labels (
    user_id       VARCHAR PRIMARY KEY REFERENCES users(user_id),
    is_fake_account BOOLEAN,
    fraud_type    VARCHAR,   -- shared_device_abuse | shared_payment_abuse | shared_address_abuse | voucher_farming | referral_abuse | emulator_abuse | promo_abuse | normal
    fraud_reason  TEXT,
    label_source  VARCHAR    -- rule_based | manual | ml_model
);

CREATE TABLE fake_account_abt (
    uid                              VARCHAR PRIMARY KEY,
    fraud                            BOOLEAN,
    ftype                            VARCHAR,
    risk_score                       INTEGER,
    risk_cat                         VARCHAR,
    email_len                        INTEGER,
    email_num_ratio                  DECIMAL,
    email_rand                       DECIMAL,
    disp_email                       BOOLEAN,
    phone_score                      DECIMAL,
    uniq_dev                         INTEGER,
    max_acc_dev                      INTEGER,
    uniq_addr                        INTEGER,
    max_acc_addr                     INTEGER,
    uniq_pay                         INTEGER,
    max_acc_pay                      INTEGER,
    promo_ratio                      DECIMAL,
    reg2txn_min                      INTEGER,
    newuser_voucher                  INTEGER,
    txn_f1m                          INTEGER,
    amt_f1m                          DECIMAL,
    avg_amt1m                        DECIMAL,
    promo_f1m                        DECIMAL,
    voucher_f1m                      INTEGER,
    txn_f2m                          INTEGER,
    amt_f2m                          DECIMAL,
    avg_amt2m                        DECIMAL,
    promo_f2m                        DECIMAL,
    voucher_f2m                      INTEGER,
    txn_f3m                          INTEGER,
    amt_f3m                          DECIMAL,
    avg_amt3m                        DECIMAL,
    promo_f3m                        DECIMAL,
    voucher_f3m                      INTEGER,
    txn_f4m                          INTEGER,
    amt_f4m                          DECIMAL,
    avg_amt4m                        DECIMAL,
    promo_f4m                        DECIMAL,
    voucher_f4m                      INTEGER,
    txn_f5m                          INTEGER,
    amt_f5m                          DECIMAL,
    avg_amt5m                        DECIMAL,
    promo_f5m                        DECIMAL,
    voucher_f5m                      INTEGER,
    txn_f6m                          INTEGER,
    amt_f6m                          DECIMAL,
    avg_amt6m                        DECIMAL,
    promo_f6m                        DECIMAL,
    voucher_f6m                      INTEGER,
    max_acc_ip                       INTEGER,
    login_f1h                        INTEGER,
    login_f2h                        INTEGER,
    login_f3h                        INTEGER,
    login_f4h                        INTEGER,
    login_f5h                        INTEGER,
    login_f6h                        INTEGER,
    login_f12h                       INTEGER,
    login_f18h                       INTEGER,
    login_f24h                       INTEGER,
    ref_cnt                          INTEGER,
    ref_ring                         DECIMAL,
    degree                           INTEGER,
    comp_size                        INTEGER,
    cluster                          INTEGER,
    shared_ent                       INTEGER,
    shared_device_count              INTEGER,
    shared_address_count             INTEGER,
    shared_payment_count             INTEGER,
    shared_ip_count                  INTEGER
);

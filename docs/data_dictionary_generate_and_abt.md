<!--
Purpose: Document generated raw-table columns and ABT columns with one sample row each.
Used by: Developers, reviewers, and analysts checking data generation and ABT build output.
Main dependencies: data/raw/*.csv and data/abt/fake_account_abt.csv.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Data Dictionary: Generate Output and ABT

Dokumen ini berisi nama kolom tiap hasil data generate dan ABT build, plus 1 contoh row untuk masing-masing file.

## Raw Data Tables

### `data/raw/addresses.csv`
| Columns | Sample Row |
|---|---|
| `address_id`, `address_text`, `city`, `province`, `postal_code`, `latitude`, `longitude` | `ADR00001`, `Jalan Gg. Stasiun Wonokromo No. 88, RT 06/RW 03`, `Jakarta`, `DKI Jakarta`, `51088`, `72.75759`, `-98.270915` |

### `data/raw/devices.csv`
| Columns | Sample Row |
|---|---|
| `device_id`, `device_fingerprint`, `device_type`, `os`, `os_version`, `app_version`, `first_seen_date`, `last_seen_date` | `DEV00001`, `FP_Vivo_Y27_9d94bdeaa1e75c56`, `android`, `Android`, `13.0`, `3.13.1`, `2026-05-11 20:16:54.779221`, `2026-06-07 00:19:47.779221` |

### `data/raw/fraud_labels.csv`
| Columns | Sample Row |
|---|---|
| `user_id`, `is_fake_account`, `fraud_type`, `fraud_reason`, `label_source` | `USR00001`, `False`, `normal`, ``, `rule_based` |

### `data/raw/login_sessions.csv`
| Columns | Sample Row |
|---|---|
| `session_id`, `user_id`, `device_id`, `ip_address`, `login_timestamp`, `logout_timestamp`, `session_duration_seconds`, `geo_city`, `geo_province`, `login_persona` | `SES000001`, `USR00004`, `DEV03503`, `182.253.18.42`, `2025-12-18 02:01:44.779221`, `2025-12-18 02:14:09.779221`, `745`, `Denpasar`, `Bali`, `fraud_night` |

### `data/raw/payments.csv`
| Columns | Sample Row |
|---|---|
| `payment_id`, `payment_type`, `payment_provider`, `masked_payment_number`, `payment_token`, `created_at` | `PMT00001`, `ewallet`, `Dana`, `XXXX-XXXX-4328`, `TOK_PAY_e0dd7cced1fe782d`, `2026-03-22 10:58:55.779221` |

### `data/raw/referrals.csv`
| Columns | Sample Row |
|---|---|
| `referral_id`, `referrer_user_id`, `referred_user_id`, `referral_date`, `reward_amount`, `reward_claimed` | `REF00001`, `USR05080`, `USR01519`, `2025-12-09 12:47:36.779221`, `25000.0`, `True` |

### `data/raw/transaction_items.csv`
| Columns | Sample Row |
|---|---|
| `transaction_item_id`, `transaction_id`, `product_id`, `product_category`, `quantity`, `unit_price`, `subtotal` | `TXI000001`, `TXN00001`, `PROD_GRO_490`, `Groceries`, `3`, `22500.0`, `67500.0` |

### `data/raw/transactions.csv`
| Columns | Sample Row |
|---|---|
| `transaction_id`, `user_id`, `transaction_date`, `order_amount`, `promo_discount`, `shipping_fee`, `final_amount`, `voucher_id`, `payment_id`, `address_id`, `order_status`, `delivery_status`, `payment_status` | `TXN00001`, `USR00004`, `2025-12-19 03:31:32.779221`, `67500.0`, `0.0`, `15000.0`, `82500.0`, ``, `PMT06621`, `ADR05201`, `completed`, `delivered`, `paid` |

### `data/raw/user_addresses.csv`
| Columns | Sample Row |
|---|---|
| `user_id`, `address_id`, `is_default_address`, `created_at` | `USR00001`, `ADR00001`, `True`, `2026-01-21 19:14:11.779221` |

### `data/raw/user_devices.csv`
| Columns | Sample Row |
|---|---|
| `user_id`, `device_id`, `first_login_date`, `last_login_date`, `login_count` | `USR00001`, `DEV00001`, `2026-01-21 19:14:11.779221`, `2026-02-04 19:14:11.779221`, `8` |

### `data/raw/user_payments.csv`
| Columns | Sample Row |
|---|---|
| `user_id`, `payment_id`, `linked_at`, `is_default_payment` | `USR00001`, `PMT00001`, `2026-01-21 19:14:11.779221`, `True` |

### `data/raw/users.csv`
| Columns | Sample Row |
|---|---|
| `user_id`, `full_name`, `email`, `phone_number`, `registration_date`, `registration_channel`, `date_of_birth`, `gender`, `city`, `province`, `is_email_verified`, `is_phone_verified`, `account_status` | `USR00001`, `Balidin Dongoran, S.T.`, `ivanmandala@hotmail.com`, `081448398260`, `2026-01-21 19:14:11.779221`, `email`, `1972-05-28`, `Female`, `Medan`, `Sumatera Utara`, `True`, `True`, `active` |

### `data/raw/vouchers.csv`
| Columns | Sample Row |
|---|---|
| `voucher_id`, `voucher_code`, `voucher_type`, `discount_amount`, `discount_percentage`, `min_purchase_amount`, `start_date`, `end_date`, `max_usage`, `promo_category` | `VCH00001`, `NEWUSER50`, `fixed_amount`, `50000.0`, `0.0`, `100000.0`, `2025-12-09 00:20:47.779221`, `2026-07-07 00:20:47.779221`, `10000`, `new_user_promo` |

## ABT Output

### `data/abt/fake_account_abt.csv`
| Columns | Sample Row |
|---|---|
| `uid`, `fraud`, `ftype`, `risk_score`, `risk_cat`, `email_len`, `email_num_ratio`, `email_rand`, `disp_email`, `phone_score`, `uniq_dev`, `max_acc_dev`, `uniq_addr`, `max_acc_addr`, `uniq_pay`, `max_acc_pay`, `promo_ratio`, `reg2txn_min`, `newuser_voucher`, `txn_f1m`, `amt_f1m`, `avg_amt1m`, `promo_f1m`, `voucher_f1m`, `txn_f2m`, `amt_f2m`, `avg_amt2m`, `promo_f2m`, `voucher_f2m`, `txn_f3m`, `amt_f3m`, `avg_amt3m`, `promo_f3m`, `voucher_f3m`, `txn_f4m`, `amt_f4m`, `avg_amt4m`, `promo_f4m`, `voucher_f4m`, `txn_f5m`, `amt_f5m`, `avg_amt5m`, `promo_f5m`, `voucher_f5m`, `txn_f6m`, `amt_f6m`, `avg_amt6m`, `promo_f6m`, `voucher_f6m`, `max_acc_ip`, `login_v1h`, `login_v2h`, `login_v3h`, `login_v4h`, `login_v5h`, `login_v6h`, `login_v12h`, `login_v18h`, `login_v24h`, `ref_cnt`, `ref_ring`, `degree`, `comp_size`, `cluster`, `shared_ent`, `shared_device_count`, `shared_address_count`, `shared_payment_count`, `shared_ip_count` | `USR00001`, `False`, `normal`, `50`, `Medium`, `23`, `0.0`, `2.5503407095463886`, `False`, `0.21818181818181817`, `1`, `5`, `1`, `10`, `1`, `4`, `0.0`, `970`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `1`, `370500`, `370500`, `0`, `0`, `1`, `370500`, `370500`, `0`, `0`, `102`, `0`, `0`, `0`, `0`, `0`, `0`, `0`, `1`, `1`, `0`, `0.0`, `79`, `9979`, `80`, `84`, `4`, `9`, `3`, `68` |

## New-User Training Data

File `data/processed/new_user_training_data.csv` dipakai untuk melatih model registrasi new user. Dataset ini hanya memakai feature yang tersedia saat signup dan label fraud yang lebih spesifik.

### Feature Utama

| Column | Sample Meaning |
|---|---|
| `email_len` | Panjang email. |
| `email_num_ratio` | Rasio angka pada username email. |
| `email_rand` | Keacakan username email. |
| `disp_email` | Apakah domain email disposable. |
| `phone_score` | Skor pola nomor telepon. |
| `full_name_len` | Panjang nama lengkap. |
| `is_email_verified` | Status verifikasi email. |
| `is_phone_verified` | Status verifikasi phone. |
| `age_years` | Umur pengguna. |
| `registration_hour` | Jam registrasi. |

### Label New-User Dataset

- `disposable_email`
- `suspicious_phone_pattern`
- `normal`

Dataset ini sengaja dibuat seimbang agar model new-user tidak bias ke kelas normal atau fraud tertentu.

## Notes
- Kolom dan sample row di atas diambil dari file generate dan ABT yang sedang aktif di project.
- Kalau kamu generate ulang data atau rebuild ABT, nilai sample row bisa berubah, tetapi nama kolom tetap mengikuti schema pipeline.

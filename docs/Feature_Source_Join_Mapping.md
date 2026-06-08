<!--
Purpose: Map each ABT feature group to source data, join keys, transformations, and output tables.
Used by: Developers, reviewers, and database maintainers auditing feature lineage.
Main dependencies: scripts/build_abt.py, scripts/build_graph.py, scripts/extract_graph_features.py, scripts/export_graph_api.py.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Feature Source, Join, and Output Mapping

Dokumen ini menjelaskan relasi fitur end-to-end: fitur dibuat dari data apa, memakai join/agregasi apa, menghasilkan fitur apa, dan masuk ke tabel/file output mana.

## Daftar Singkatan

| Singkatan | Kepanjangan | Arti di Project |
|---|---|---|
| `ABT` | Analytical Base Table | Tabel final per user untuk training dan API. Isinya raw-derived features + graph aggregate features. |
| `API` | Application Programming Interface | Endpoint backend yang dipakai frontend untuk membaca user, statistik, prediksi, dan graph. |
| `uid` | User ID | Nama final kolom ID user di ABT, berasal dari `users.user_id`. |
| `txn` | Transaction | Prefix fitur transaksi, misalnya `txn_f1m` berarti jumlah transaksi pada window 1 bulan. |
| `amt` | Amount | Prefix nominal transaksi, misalnya `amt_f1m` berarti total nilai transaksi pada window 1 bulan. |
| `avg_amt` | Average Amount | Rata-rata nilai transaksi pada window tertentu. |
| `promo` | Promotion | Fitur diskon/promo/voucher dari transaksi dan voucher. |
| `reg2txn` | Registration to Transaction | Selisih waktu dari registrasi user ke transaksi pertama. |
| `dev` | Device | Perangkat yang dipakai user. Contoh node graph: `DEV_DEV10`. |
| `addr` | Address | Alamat pengiriman/alamat user. Contoh node graph: `ADDR_ADR07`. |
| `pay` | Payment | Metode/instrumen pembayaran. Contoh node graph: `PAY_PMT99`. |
| `ip` | Internet Protocol Address | Alamat IP dari login session. Contoh node graph: `IP_103.10.66.5`. |
| `v` pada `login_v*` | velocity bucket | Jumlah login dari `00:00` sampai batas jam bucket harian. Contoh `login_v12h`. |
| `f` pada `txn_f*`, `promo_f*`, `voucher_f*` | Feature window | Window fitur berbasis bulan. Contoh `txn_f1m` = transaksi 1 bulan terakhir. |
| `m` pada `1m..6m` | Month | Window bulan: `1m` sampai `6m`. |
| `cnt` | Count | Jumlah hitungan. Contoh `ref_cnt` = jumlah referral. |
| `ent` | Entity | Entitas graph seperti device, address, payment, atau IP. |
| `comp` | Component | Connected component pada graph. |
| `ftype` | Fraud Type | Jenis fraud/label kategori fraud dari data label atau enrichment risiko. |
| `cat` | Category | Kategori, misalnya `risk_cat` untuk kategori risiko. |

## Ringkasan Output

| Output | Isi | Dibuat Oleh | Keterangan |
|---|---|---|---|
| `data/processed/graph_nodes.csv` | Node graph mentah: user, device, address, payment, IP | `build_graph.py` | Input graph feature extraction |
| `data/processed/graph_edges.csv` | Edge graph mentah: user ke device/address/payment/IP | `build_graph.py` | Input graph feature extraction |
| `data/processed/user_graph_features.csv` | Agregat graph per user | `extract_graph_features.py` | Di-join ke ABT final |
| `data/abt/fake_account_abt.csv` | ABT final: 69 kolom total | `build_abt.py` | 64 fitur model + 5 metadata/label |
| `models/feature_columns.json` | Urutan 64 fitur model | `train_model.py` | Metadata input model |
| `data/processed/graph_nodes.json` | Node graph API dengan `risk_score`, `risk_category`, `ftype` | `export_graph_api.py` | Dipakai backend/frontend graph |
| `data/processed/graph_edges.json` | Edge graph API dengan `relationship` | `export_graph_api.py` | Dipakai backend/frontend graph |

## Mapping Fitur ABT

| Grup Fitur | Sumber Data | Join / Agregasi Utama | Fitur Internal | Nama Final di ABT | Output Table/File |
|---|---|---|---|---|---|
| Metadata user | `users.csv`, `fraud_labels.csv` | `users.user_id` left join `fraud_labels.user_id` | `user_id`, `is_fake_account`, `fraud_type` | `uid`, `fraud`, `ftype` | `fake_account_abt.csv` |
| Rule risk metadata | Semua fitur ABT sebelum rename | Rule scoring di `compute_risk_score(row)` | `risk_score_rule_based`, `risk_category` | `risk_score`, `risk_cat` | `fake_account_abt.csv` |
| Identity | `users.csv` | Tanpa join; parsing per `user_id` | `email_length`, `email_numeric_ratio`, `email_randomness_score`, `is_disposable_email_domain`, `phone_pattern_score` | `email_len`, `email_num_ratio`, `email_rand`, `disp_email`, `phone_score` | `fake_account_abt.csv` |
| Device sharing | `user_devices.csv` | Group by `device_id` hitung `nunique(user_id)`, map balik ke setiap `user_id`, lalu group by `user_id` | `unique_devices`, `accounts_per_device_max` | `uniq_dev`, `max_acc_dev` | `fake_account_abt.csv` |
| Address sharing | `user_addresses.csv` | Group by `address_id` hitung `nunique(user_id)`, map balik ke setiap `user_id`, lalu group by `user_id` | `unique_addresses`, `accounts_per_address_max` | `uniq_addr`, `max_acc_addr` | `fake_account_abt.csv` |
| Payment sharing | `user_payments.csv` | Group by `payment_id` hitung `nunique(user_id)`, map balik ke setiap `user_id`, lalu group by `user_id` | `unique_payments`, `accounts_per_payment_max` | `uniq_pay`, `max_acc_pay` | `fake_account_abt.csv` |
| Promo category enrichment | `transactions.csv`, `vouchers.csv` | `transactions.voucher_id` left join `vouchers.voucher_id` untuk mengambil `promo_category` | `is_new_user_promo`, `is_free_shipping` | Dipakai sebagai intermediate | Tidak keluar sebagai kolom final |
| Promo ratio | `transactions.csv`, `vouchers.csv` | Setelah join voucher, group by `user_id`; `voucher_usage_count / total_transactions` | `promo_order_ratio` | `promo_ratio` | `fake_account_abt.csv` |
| Signup-to-first transaction | `users.csv`, `transactions.csv` | Group by `transactions.user_id` ambil min `transaction_date`, join ke `users.registration_date` | `signup_to_first_transaction_minutes` | `reg2txn_min` | `fake_account_abt.csv` |
| New user voucher | `transactions.csv`, `vouchers.csv` | Setelah join voucher, group by `user_id`, sum `is_new_user_promo` | `new_user_voucher_usage` | `newuser_voucher` | `fake_account_abt.csv` |
| Monthly transaction windows | `transactions.csv` | Pakai `global_max_date`; filter `days_since_txn <= 30/60/90/120/150/180`, lalu group by `user_id` | `total_transactions_last_Nm`, `total_order_amount_last_Nm`, `avg_order_amount_last_Nm`, `total_promo_discount_last_Nm`, `voucher_usage_count_last_Nm` | `txn_fNm`, `amt_fNm`, `avg_amtNm`, `promo_fNm`, `voucher_fNm` untuk N=1..6 | `fake_account_abt.csv` |
| IP sharing | `login_sessions.csv` | Group by `ip_address` hitung `nunique(user_id)`, map balik ke session, lalu group by `user_id` | `accounts_per_ip_max` | `max_acc_ip` | `fake_account_abt.csv` |
| Login frequency buckets | `login_sessions.csv` | Per `user_id`, ubah `login_timestamp` ke jam sejak `00:00`; untuk tiap bucket `1,2,3,4,5,6,12,18,24`, hitung maksimum jumlah login dari `00:00` sampai batas jam pada hari tersibuk | `login_frequency_1h`, `login_frequency_2h`, `login_frequency_3h`, `login_frequency_4h`, `login_frequency_5h`, `login_frequency_6h`, `login_frequency_12h`, `login_frequency_18h`, `login_frequency_24h` | `login_v1h`, `login_v2h`, `login_v3h`, `login_v4h`, `login_v5h`, `login_v6h`, `login_v12h`, `login_v18h`, `login_v24h` | `fake_account_abt.csv` |
| Referral count | `referrals.csv` | Group by `referrer_user_id` count `referral_id`, map ke `users.user_id` | `referral_count` | `ref_cnt` | `fake_account_abt.csv` |
| Referral ring score | `referrals.csv` | Bangun directed graph `referrer_user_id -> referred_user_id`; deteksi cycle dan descendant count | `referral_ring_score` | `ref_ring` | `fake_account_abt.csv` |
| Graph degree | `graph_nodes.csv`, `graph_edges.csv` | Build graph user-entity; hitung degree user | `graph_degree` | `degree` | `user_graph_features.csv`, lalu `fake_account_abt.csv` |
| Graph component size | `graph_nodes.csv`, `graph_edges.csv` | Build connected components; map ukuran komponen ke user | `connected_component_size` | `comp_size` | `user_graph_features.csv`, lalu `fake_account_abt.csv` |
| Graph cluster size | `graph_nodes.csv`, `graph_edges.csv` | Hitung ukuran ego/cluster sekitar user | `graph_cluster_size` | `cluster` | `user_graph_features.csv`, lalu `fake_account_abt.csv` |
| Shared entity count | `graph_nodes.csv`, `graph_edges.csv` | Hitung total shared neighbors/entity connections user | `shared_entity_count` | `shared_ent` | `user_graph_features.csv`, lalu `fake_account_abt.csv` |
| Shared entity counters | `graph_nodes.csv`, `graph_edges.csv` | Hitung shared entity per tipe: device, address, payment, IP | `shared_device_count`, `shared_address_count`, `shared_payment_count`, `shared_ip_count` | `shared_device_count`, `shared_address_count`, `shared_payment_count`, `shared_ip_count` | `user_graph_features.csv`, lalu `fake_account_abt.csv` |

## Join Urutan ABT

`build_abt.py` memakai `users.user_id` sebagai anchor utama:

```text
users
  left join identity_features on user_id
  left join user_device_features on user_id
  left join user_address_features on user_id
  left join user_payment_features on user_id
  left join user_transaction_features on user_id
  left join signup_to_first_transaction on user_id
  left join user_login_features on user_id
  left join referral_features on user_id
  left join fraud_labels on user_id
  left join user_graph_features on user_id
  -> fake_account_abt.csv
```

## Graph Output Mapping

| Output Graph | Sumber Data | Transformasi | Field Output |
|---|---|---|---|
| `graph_nodes.csv` | `users.csv`, `devices.csv`, `addresses.csv`, `payments.csv`, `login_sessions.csv` | Deduplicate entity IDs menjadi node typed | `node_id`, `node_type` |
| `graph_edges.csv` | `user_devices.csv`, `user_addresses.csv`, `user_payments.csv`, `login_sessions.csv` | Buat edge `user -> entity` | `source`, `target`, `edge_type` |
| `graph_nodes.json` | `graph_nodes.csv`, `fake_account_abt.csv` | Enrich user node dari ABT | `id`, `label`, `type`, `risk_score`, `risk_category`, `ftype` |
| `graph_edges.json` | `graph_edges.csv` | Rename `edge_type` untuk API | `source`, `target`, `relationship` |

## Contoh Graph dari Penggabungan Tabel

Graph di project ini adalah graph **user-entity**. User menjadi node pusat, lalu user dihubungkan ke device, address, payment, dan IP yang pernah dipakai. Saat ini `transactions.csv` tidak langsung menjadi edge graph; transaksi dipakai untuk fitur ABT seperti `promo_ratio`, `txn_f1m`, `amt_f1m`, dan seterusnya. Relasi payment di graph berasal dari `user_payments.csv`, bukan dari `transactions.csv`.

### Contoh Data Mentah

`users.csv`

| user_id |
|---|
| USR001 |
| USR002 |

`user_devices.csv`

| user_id | device_id |
|---|---|
| USR001 | DEV10 |
| USR002 | DEV10 |

`user_addresses.csv`

| user_id | address_id |
|---|---|
| USR001 | ADR07 |
| USR002 | ADR08 |

`user_payments.csv`

| user_id | payment_id |
|---|---|
| USR001 | PMT99 |
| USR002 | PMT99 |

`login_sessions.csv`

| user_id | ip_address |
|---|---|
| USR001 | 103.10.66.5 |
| USR002 | 103.10.66.5 |

`transactions.csv`

| transaction_id | user_id | payment_id | voucher_id |
|---|---|---|---|
| TXN001 | USR001 | PMT99 | VCR01 |
| TXN002 | USR002 | PMT99 | VCR01 |

### Hasil `graph_nodes.csv`

| node_id | node_type | Asal |
|---|---|---|
| USR001 | user | `users.user_id` |
| USR002 | user | `users.user_id` |
| DEV_DEV10 | device | `user_devices.device_id` |
| ADDR_ADR07 | address | `user_addresses.address_id` |
| ADDR_ADR08 | address | `user_addresses.address_id` |
| PAY_PMT99 | payment | `user_payments.payment_id` |
| IP_103.10.66.5 | ip | `login_sessions.ip_address` |

### Hasil `graph_edges.csv`

| source | target | edge_type | Asal Tabel |
|---|---|---|---|
| USR001 | DEV_DEV10 | uses_device | `user_devices` |
| USR002 | DEV_DEV10 | uses_device | `user_devices` |
| USR001 | ADDR_ADR07 | uses_address | `user_addresses` |
| USR002 | ADDR_ADR08 | uses_address | `user_addresses` |
| USR001 | PAY_PMT99 | uses_payment | `user_payments` |
| USR002 | PAY_PMT99 | uses_payment | `user_payments` |
| USR001 | IP_103.10.66.5 | uses_ip | `login_sessions` |
| USR002 | IP_103.10.66.5 | uses_ip | `login_sessions` |

### Bentuk Graph

```text
        DEV_DEV10
        /       \
   USR001     USR002
      | \       / |
      |  PAY_PMT99
      |      |
 ADDR_ADR07  ADDR_ADR08
      \      /
   IP_103.10.66.5
```

### Hasil Feature Graph per User

Karena `USR001` dan `USR002` berbagi device, payment, dan IP:

| user_id | graph_degree | shared_device_count | shared_payment_count | shared_ip_count | shared_address_count |
|---|---:|---:|---:|---:|---:|
| USR001 | 1 | 1 | 1 | 1 | 0 |
| USR002 | 1 | 1 | 1 | 1 | 0 |

Interpretasi:

- `graph_degree = 1`: user ini terkoneksi ke 1 user lain dalam user-user projection.
- `shared_device_count = 1`: ada 1 shared device yang menghubungkan user ini ke user lain.
- `shared_payment_count = 1`: ada 1 shared payment yang menghubungkan user ini ke user lain.
- `shared_ip_count = 1`: ada 1 shared IP yang menghubungkan user ini ke user lain.
- `shared_address_count = 0`: alamat tidak sama, jadi tidak ada shared address.

### Hasil Graph API JSON

Setelah ABT selesai, `export_graph_api.py` memperkaya user node dengan metadata risiko dari `fake_account_abt.csv`.

`graph_nodes.json`

```json
{
  "id": "USR001",
  "label": "USR001",
  "type": "user",
  "risk_score": 65,
  "risk_category": "High",
  "ftype": "shared_payment_abuse"
}
```

`graph_edges.json`

```json
{
  "source": "USR001",
  "target": "PAY_PMT99",
  "relationship": "uses_payment"
}
```

## Catatan Kontrak

- ABT final punya 69 kolom total.
- Model memakai 64 fitur.
- Kolom metadata/label yang tidak masuk model: `uid`, `fraud`, `ftype`, `risk_score`, `risk_cat`.
- `login_v*` adalah frequency bucket harian dari `00:00`, bukan rolling velocity.
- Tidak ada kolom `is_emulator`, `is_rooted`, `address_similarity_group`, `is_vpn`, atau `is_proxy` di kontrak final.

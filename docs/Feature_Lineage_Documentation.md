# Feature Lineage Documentation

## Overview

Dokumentasi lineage untuk pipeline:

generate_data.py -> build_abt.py -> generate_graph_data.py -> extract_graph_features.py -> train_model.py -> run_inference.py

## End-to-End Data Flow

```text
generate_data.py
        ↓
data/raw/*.csv
        ↓
build_abt.py
        ↓
data/abt/fake_account_abt.csv
        ↓
generate_graph_data.py
        ↓
graph_nodes.csv + graph_edges.csv
        ↓
extract_graph_features.py
        ↓
user_graph_features.csv
        ↓
train_model.py
        ↓
fake_account_model.pkl
        ↓
run_inference.py
        ↓
Fraud Prediction
```

## Feature Lineage

### Identity Features
- email_len
- email_num_ratio
- email_rand
- disp_email
- phone_score

### Device Features
- uniq_dev
- max_acc_dev

### Address Features
- uniq_addr
- max_acc_addr

### Payment Features
- uniq_pay
- max_acc_pay

### Transaction Features
- promo_ratio
- reg2txn_min
- newuser_voucher
- txn_f1m sampai txn_f6m
- amt_1m sampai amt_6m
- avg_amt1m sampai avg_amt6m
- voucher_f1m sampai voucher_f6m

### Login Features
- max_acc_ip
- login_f1h sampai login_f24h

### Referral Features
- ref_cnt
- ref_ring

### Graph Features
- graph_degree
- connected_component_size
- graph_cluster_size
- shared_entity_count
- shared_device_count
- shared_address_count
- shared_payment_count
- shared_ip_count

## Final Dataset

fake_account_abt.csv + user_graph_features.csv -> train_model.py -> model

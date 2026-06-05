# Synthetic Data Generation Documentation

This document describes the design, implementation, and output statistics of the synthetic data generation engine for the Fake Account Detection Retail App Prototype.

## Overview
To build a high-fidelity model without accessing real customer data, we built an Indonesian-localized synthetic data generator using Python's `Faker` library. The data spans a **6-month duration** and features highly realistic relational data structures that mimic a **retail mobile application (inspired by Alfagift)**. It captures the core *User Journey* from registration, login, product browsing, applying vouchers, checkout, payment, up to delivery completion.

## Data Generation Engine Design

- **Locale & Localization:** `Faker(locale='id_ID')` is used to generate Indonesian-specific names, phone numbers, addresses, and geographic locations.
- **Reproducibility:** A fixed seed of `42` is set for both `random`, `numpy`, and `Faker` to ensure that identical datasets are created on every execution.
- **Relational Integrity:** Timestamps of transaction activities, device links, login sessions, and referral milestones are sequentially bounded to match realistic event lifecycles (e.g., registration date $\rightarrow$ login session $\rightarrow$ transaction).

## Dataset Volume & Compliance

Below is the summary of the generated dataset:

| Table Name | Output Count (Target) | Output Count (Actual) | Notes / Columns |
| :--- | :--- | :--- | :--- |
| **users** | 10,000 | 10,000 | Indonesian names, localized phone numbers, registration dates, demographics. |
| **devices** | 7,000 | 7,000 | Operating systems, app versions, emulator status, jailbreak/rooted status. |
| **user_devices** | — | 10,922 | Maps device interactions and login timestamps. |
| **addresses** | 8,000 | 8,000 | Physical shipping address, coordinates, and similarity clustering. |
| **user_addresses** | — | 10,000 | Maps shipping addresses to user profiles. |
| **payments** | 9,000 | 9,000 | Payment types (ewallet, bank transfer, CC), providers, and tokens. |
| **user_payments** | — | 10,000 | Links user payment profiles. |
| **vouchers** | 500 | 500 | Discount types, new user promo vouchers, max limits. |
| **transactions** | 50,000 | 50,000 | Simulates checkouts, voucher usage, and delivery states. |
| **transaction_items**| — | 116,634 | Line items per transaction including unit prices and quantities. |
| **login_sessions** | 100,000 | 100,005 | IP logs, VPN/proxy detection, session duration, and geo-locations. |
| **referrals** | — | 1,499 | User-to-user referral tree structures. |
| **fraud_labels** | 10,000 | 10,000 | Binary target label (`is_fake_account`), fraud reason, and classification type. |

**Final Fraud Ratio:** **30.00%** (3,000 fake accounts / 7,000 normal accounts).

---

## Simulated Fraud Scenarios

Based on the mobile app exploration, 11 potential fraud points were identified (Promo Abuse, A-Poin Farming, Refund Abuse, etc.). For the purpose of this dataset and modeling, these have been abstracted and synthesized into **six core simulated fraud behaviors** that capture the fundamental data anomalies (shared entities, high velocity, and relational graphs) common to all those scenarios:

### 1. Shared Device Abuse
- **Description:** A single physical device fingerprint is linked to a large number of accounts.
- **Simulation Pattern:** 20 users share the exact same `device_id` and register within a narrow 48-hour window. These accounts immediately transact using the `NEWUSER50` voucher.
- **Target Count:** ~500 users.

### 2. Shared Address Abuse
- **Description:** Multiple users register different accounts but share the same physical delivery address to maximize new user voucher redemptions.
- **Simulation Pattern:** Clusters of 30 fake accounts register and share similar coordinates or address strings containing minor typographic variations.
- **Target Count:** ~500 users.

### 3. Shared Payment Abuse
- **Description:** Multiple accounts share a single funding instrument (e.g., e-wallet tokens or credit card numbers).
- **Simulation Pattern:** 15 accounts link to the same default payment token and run nominal checkouts to exploit vouchers.
- **Target Count:** ~400 users.

### 4. Voucher Farming
- **Description:** Single-use accounts created exclusively to exploit promotional vouchers.
- **Simulation Pattern:** Accounts register, execute exactly **1 transaction** utilizing the new user discount code (`NEWUSER50`), and never log in or interact with the platform again.
- **Target Count:** ~600 users.

### 5. Referral Ring (Referral Abuse)
- **Description:** Group of malicious accounts referencing each other in chain-like networks to harvest referral bonuses.
- **Simulation Pattern:** A tree structure of referrals is created where User A refers users B, C, D, E; User B then refers F, G, H, etc., with connections via shared login IPs or fingerprints.
- **Target Count:** ~500 users.

### 6. Emulator Abuse
- **Description:** Professional fraud rings utilizing device emulators and virtual environments to create accounts.
- **Simulation Pattern:** Accounts log in consistently from devices flagged as `is_emulator = True` and `is_rooted = True` using proxy IPs or shared local local-network subnets (e.g., `192.168.1.100` to `192.168.1.105`).
- **Target Count:** ~500 users.

> [!NOTE]
> **Data Noise and Overlap:** To prevent model overfitting and simulate real-world ambiguity, random noise was introduced in the final dataset. Therefore, the actual maximum sharing counts in the final dataset are lower (Device sharing max: 7, Address sharing max: 10, Payment sharing max: 4) and overlap significantly with legitimate usage.

---


## Execution Guide

### Local Generation
To regenerate the synthetic data locally:
```bash
python scripts/generate_data.py
```
This writes the CSV files to `data/raw/`.

### Uploading to Supabase
If you want to sync the generated raw CSVs to your Supabase tables:
1. Ensure your database tables have been set up via `database_schema.sql`.
2. Configure `.env` with your active `SUPABASE_URL` and `SUPABASE_KEY`.
3. Run the uploader:
```bash
python scripts/upload_to_supabase.py
```
*Note: The upload script automatically chunks operations (batch size = 500) to respect rate limits and handles missing values (`NaN`) gracefully.*

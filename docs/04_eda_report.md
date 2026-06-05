# Exploratory Data Analysis (EDA) Report

This report summarizes the results of the Exploratory Data Analysis performed on the raw dimension tables and the compiled Analytics Base Table (ABT) for the Fake Account Detection Prototype.

---

## 1. Dataset Overview
- **Total Users:** 10,000
- **Total Transactions:** 50,000
- **Time Duration:** 6 months (Historical data)
- **Target Variable:** `is_fake_account` (True / False)

---

## 2. Label & Fraud Distributions

### Fake vs Normal Accounts
The synthetic dataset was engineered with a strict **30.00% fraud ratio** representing high-risk or fake accounts, with the remaining 70.00% acting as standard legitimate customers.

![Fake vs Normal Distribution](file:///d:/magang/fraud%20detection%20&%20abuse/docs/images/fake_vs_normal.png)

### Distribution of Fraud Types
The 3,000 fake accounts are divided into 6 distinct behavioral patterns:
- **voucher_farming (Voucher Farming):** ~600 users (Accounts registering solely to redeem a voucher and immediately becoming inactive).
- **shared_device_abuse (Shared Device Abuse):** ~500 users (A pool of accounts sharing device fingerprints/IDs).
- **shared_address_abuse (Shared Address Abuse):** ~500 users (Multiple accounts sharing shipping addresses).
- **referral_abuse (Referral Ring):** ~500 users (Chains of malicious accounts referring each other).
- **emulator_abuse (Emulator Abuse):** ~500 users (Logins from emulators, rooted devices, and shared local IPs).
- **shared_payment_abuse (Shared Payment Abuse):** ~400 users (Shared payment tokens/funding instruments).

![Distribution of Fraud Types](file:///d:/magang/fraud%20detection%20&%20abuse/docs/images/fraud_types.png)

---

## 3. Demographics and Behavioral Analysis

### Account Age
Normal users have a wide distribution of account ages spanning the entire 180-day observation window. Fraudulent users, particularly those involved in burst scenarios (like shared device registration or voucher farming), tend to have much newer accounts.

![Account Age Boxplot](file:///d:/magang/fraud%20detection%20&%20abuse/docs/images/account_age_boxplot.png)

### Entity Sharing Behavior
With the introduction of realistic noise (shared family devices, residential subnets, and office/apartment addresses), entity sharing has more overlap between normal and fake accounts:
- **Device Sharing:** Standard normal users average exactly 1 device, but due to network/family sharing, some devices link up to 6-7 accounts (both normal and fake).
- **Address Sharing:** Normal address groups can show clusters of up to 10 accounts sharing the same address/apartment block, showing significant overlap with fraud.
- **Payment Sharing:** Multi-account usage of a single e-wallet or card token is low, with a maximum of 4 accounts sharing a single payment instrument.

> [!NOTE]
> **Rule-Based Limitations:** Due to the added noise (e.g. residential IP sharing, shared family devices, apartments), simple rule-based thresholds (like blocking if >5 accounts share a device or address) would trigger massive false positives for legitimate users. This highlights the necessity of a machine learning model that looks at combinations of features rather than single thresholds.


![Entity Sharing Histograms](file:///d:/magang/fraud%20detection%20&%20abuse/docs/images/entity_sharing_histograms.png)

---

## 4. Transaction Trends
Legitimate user transactions are distributed normally over the 6-month observation period, reflecting organic buying patterns.

![Monthly Transactions](file:///d:/magang/fraud%20detection%20&%20abuse/docs/images/monthly_transactions.png)

---

## 5. Feature Correlation Analysis
A correlation heatmap was calculated for the primary engineered features against the target label `is_fake_account`:
- **Strongest Positive Correlations:**
  - `days_since_last_login` (+0.34)
  - `login_count` (+0.25)
  - `login_velocity_24h` (+0.23)
  - `unique_ip_addresses` (+0.21)
  - `promo_order_ratio` (+0.20)
  - `new_user_voucher_usage` (+0.16)
  - `vpn_login_ratio` (+0.15)
- **Strongest Negative Correlations:**
  - `accounts_per_ip_max` (-0.46)
  - `connected_component_size` (-0.38)
  - `accounts_per_device_max` (-0.34)
  - `shared_entity_count` (-0.28)
  - `graph_degree` (-0.27)
  - `graph_cluster_size` (-0.27)
  - `unique_devices` (-0.25)
  - `total_order_amount` (-0.25)
  - `accounts_per_address_max` (-0.25)
  - `avg_order_amount` (-0.20)
  - `total_transactions` (-0.15)

> [!NOTE]
> **Interpretation of Negative Correlations:**
> In this regenerated dataset with realistic noise, normal users (which constitute 70% of the dataset) are naturally constrained to a small set of residential/home IP addresses (simulating real residential areas). This causes massive legitimate IP sharing and high connectivity in the shared-entity graph, leading to large values for `accounts_per_ip_max`, `connected_component_size`, and graph metrics for standard accounts. Conversely, fake accounts utilize highly distributed datacenter IPs, proxies, and VPNs, resulting in significantly lower IP sharing rates and smaller graph degree/cluster sizes, creating strong negative correlations with the fraud label.


![Correlation Heatmap](file:///d:/magang/fraud%20detection%20&%20abuse/docs/images/correlation_heatmap.png)

# Feature Engineering Documentation

This document details the feature engineering process used to build the Analytics Base Table (ABT) `data/abt/fake_account_abt.csv` from raw transactional and activity logs.

---

## 1. Feature Categories

### 1.1 Identity Features
Calculated from the `users` dimension table:
- **`email_length`:** Character length of the user's email address.
- **`email_numeric_ratio`:** Ratio of digits to total characters in the email local part (before `@`). High numbers of digits often indicate auto-generated emails (e.g., `rizki18274@gmail.com`).
- **`email_randomness_score`:** Shannon entropy of characters in the email local part:
  $$H(X) = - \sum_{i=1}^{n} P(x_i) \log_2 P(x_i)$$
  Higher entropy indicates more random character sequences (common in machine-generated fraud).
- **`is_disposable_email_domain`:** Boolean flag identifying temporary or disposable email domains (e.g., `mailinator.com`, `yopmail.com`).
- **`phone_pattern_score`:** suspicious digit pattern scoring. Calculated as:
  $$\text{Phone Pattern Score} = (1.0 - \text{Unique Digit Ratio}) \times 0.7 + (\text{Consecutive Repeats Ratio}) \times 0.3$$

### 1.2 Device Features
Calculated from `devices` and `user_devices` tables:
- **`unique_devices`:** Number of unique device IDs logged in by the user.
- **`accounts_per_device_max`:** Maximum number of accounts linked to any device the user has logged in from.
- **`is_emulator_used`:** True if any device fingerprint associated with the user is flagged as an emulator.
- **`is_rooted_device_used`:** True if any device associated with the user is flagged as rooted or jailbroken.

### 1.3 Address Features
Calculated from `addresses` and `user_addresses` tables:
- **`unique_addresses`:** Count of unique delivery addresses linked to the user.
- **`accounts_per_address_max`:** Maximum number of unique user accounts linked to the user's delivery addresses (using the address similarity cluster ID).
- **`address_reuse_flag`:** True if the user shares a delivery address similarity group with at least one other user.

### 1.4 Payment Features
Calculated from `payments` and `user_payments` tables:
- **`unique_payments`:** Count of unique payment methods linked to the user.
- **`accounts_per_payment_max`:** Maximum number of accounts sharing any payment token linked to the user.
- **`payment_reuse_flag`:** True if the user's payment token is linked to other users.

### 1.5 Transaction Features
Calculated from the `transactions` table:
- **`total_transactions`:** Total order count for the user.
- **`total_order_amount`:** Total sum of order values.
- **`avg_order_amount`:** Mean order value.
- **`total_promo_discount`:** Sum of voucher and promo discounts.
- **`promo_order_ratio`:** Ratio of voucher-discounted orders to total transactions.
- **`voucher_usage_count`:** Count of voucher redemptions.
- **`new_user_voucher_usage`:** Count of redemptions for the new user voucher code (`NEWUSER50`).
- **`free_shipping_usage`:** Count of free shipping voucher uses.
- **`signup_to_first_transaction_minutes`:** Minutes elapsed between the user registration timestamp and their first checkout. Filled with `-1` for users who never transacted.

### 1.6 Login Features
Calculated from `login_sessions` table:
- **`login_count`:** Total login logs for the user.
- **`unique_ip_addresses`:** Count of unique IP addresses.
- **`accounts_per_ip_max`:** Maximum number of accounts sharing any of the user's logged IP addresses.
- **`vpn_login_ratio`:** Ratio of logins flagged as using a VPN.
- **`proxy_login_ratio`:** Ratio of logins flagged as using a proxy.
- **`login_velocity_24h`:** Maximum number of logins by the user within any sliding 24-hour window.

### 1.7 Referral Features
Calculated from the `referrals` table:
- **`referral_count`:** Number of new users invited/referred by this user.
- **`referred_by_user_flag`:** True if this user was registered using another user's referral code.
- **`referral_ring_score`:** Measures cycle structures or path lengths in directed referral chains using NetworkX.

### 1.8 Graph Features
Extracted by constructing a projection graph of shared entities (User $\leftrightarrow$ Device, User $\leftrightarrow$ Address, User $\leftrightarrow$ Payment) using `NetworkX`:
- **`graph_degree`:** Total number of edges connecting the user to other users sharing devices, payments, or addresses.
- **`graph_cluster_size`:** Ego network cluster node size (how many users are tightly connected to this node).
- **`connected_component_size`:** Size of the independent component (network partition) the user belongs to.
- **`shared_entity_count`:** Total raw weight of shared connections (total shared devices + shared addresses + shared payments).

---

## 2. Rule-Based Risk Scoring & Categorization

To validate the features prior to training machine learning models, a rule-based expert heuristic score was built:

### 2.1 Points Mapping
- **Emulator Used:** +30 points
- **Rooted/Jailbroken Device:** +20 points
- **Device sharing > 5 accounts:** +25 points (sharing > 2 accounts: +10 points)
- **Address sharing > 5 accounts:** +20 points
- **Payment token sharing > 3 accounts:** +20 points
- **IP sharing > 5 accounts:** +15 points
- **Disposable Email Domain:** +15 points
- **Email Numeric Ratio > 0.4:** +10 points
- **Email Randomness Entropy > 4.2:** +10 points
- **Phone Pattern Repetition > 0.7:** +10 points
- **VPN Login Ratio > 0.5:** +15 points
- **Proxy Login Ratio > 0.5:** +15 points
- **Voucher Promo Ratio > 90% (with at least 1 transaction):** +15 points
- **Instant Signup to Checkout (< 5 minutes):** +10 points
- **Referral Ring Cycle detected:** +20 points
- **Graph Degree > 10:** +20 points

*All scores are capped at a maximum of 100.*

### 2.2 Risk Category Definitions
- **High Risk:** Score $\ge 50$ (Most likely fake accounts)
- **Medium Risk:** $20 \le \text{Score} < 50$ (Suspicious, requires verification)
- **Low Risk:** Score $< 20$ (Legitimate normal users)

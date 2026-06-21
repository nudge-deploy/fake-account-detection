from typing import Any


def categorize_risk(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def explain_rule_score(
    row: dict[str, Any], stage_features: set[str] | None = None
) -> tuple[float, list[dict[str, Any]], bool, float]:
    """Return (rule_score_0_100, breakdown, critical_trigger, raw_points).

    Tiered rules on the same feature take only the highest matching tier.
    breakdown entries: {category, label, points, value}
    """
    def _use(feature: str) -> bool:
        return stage_features is None or feature in stage_features

    breakdown: list[dict[str, Any]] = []
    critical_trigger = False
    raw_points = 0.0

    def _add(category: str, points: float, label: str, value: Any = None) -> None:
        nonlocal raw_points
        raw_points += points
        entry: dict[str, Any] = {"category": category, "label": label, "points": int(points)}
        if value is not None:
            entry["value"] = value
        breakdown.append(entry)

    # ── A. Account Creation Abuse ────────────────────────────────────────────
    if _use("disp_email") and (row.get("disp_email") is True or row.get("disp_email") == 1):
        _add("Account Creation Abuse", 15, "Email disposable/temporer terdeteksi")

    if _use("reg2txn_min"):
        reg2txn = float(row.get("reg2txn_min", 999999) or 999999)
        if 0 <= reg2txn < 5:
            _add("Account Creation Abuse", 25,
                 f"Transaksi pertama sangat cepat setelah registrasi ({int(reg2txn)} menit)", int(reg2txn))
        elif reg2txn < 30:
            _add("Account Creation Abuse", 15,
                 f"Transaksi pertama terlalu cepat setelah registrasi ({int(reg2txn)} menit)", int(reg2txn))

    if _use("newuser_voucher"):
        voucher = float(row.get("newuser_voucher", 0) or 0)
        if voucher > 2:
            _add("Account Creation Abuse", 10,
                 f"Klaim voucher new user berlebihan ({int(voucher)}x)", int(voucher))

    # ── B. Identity Sharing (tiered: take highest per feature) ──────────────
    if _use("max_acc_dev"):
        max_dev = float(row.get("max_acc_dev", 0) or 0)
        if max_dev > 10:
            _add("Identity Sharing", 50,
                 f"Device sharing sangat ekstrem ({int(max_dev)} akun/device)", int(max_dev))
            critical_trigger = True
        elif max_dev > 5:
            _add("Identity Sharing", 30,
                 f"Device sharing ekstrem ({int(max_dev)} akun/device)", int(max_dev))
        elif max_dev > 2:
            _add("Identity Sharing", 10,
                 f"Device sharing mencurigakan ({int(max_dev)} akun/device)", int(max_dev))

    if _use("max_acc_pay"):
        max_pay = float(row.get("max_acc_pay", 0) or 0)
        if max_pay > 5:
            _add("Identity Sharing", 60,
                 f"Payment sharing sangat ekstrem ({int(max_pay)} akun/payment)", int(max_pay))
            critical_trigger = True
        elif max_pay > 2:
            _add("Identity Sharing", 30,
                 f"Payment sharing mencurigakan ({int(max_pay)} akun/payment)", int(max_pay))

    if _use("max_acc_addr"):
        max_addr = float(row.get("max_acc_addr", 0) or 0)
        if max_addr > 10:
            _add("Identity Sharing", 35,
                 f"Address sharing sangat ekstrem ({int(max_addr)} akun/alamat)", int(max_addr))
        elif max_addr > 5:
            _add("Identity Sharing", 20,
                 f"Address sharing ekstrem ({int(max_addr)} akun/alamat)", int(max_addr))

    if _use("max_acc_ip"):
        max_ip = float(row.get("max_acc_ip", 0) or 0)
        if max_ip > 100:
            _add("Identity Sharing", 40,
                 f"IP sharing sangat ekstrem ({int(max_ip)} akun/IP)", int(max_ip))
        elif max_ip > 50:
            _add("Identity Sharing", 20,
                 f"IP sharing ekstrem ({int(max_ip)} akun/IP)", int(max_ip))
        elif max_ip > 20:
            _add("Identity Sharing", 10,
                 f"IP sharing mencurigakan ({int(max_ip)} akun/IP)", int(max_ip))

    # ── C. Behavioral Abuse (tiered: take highest for login_v1h) ────────────
    if _use("login_v1h"):
        login_1h = float(row.get("login_v1h", 0) or 0)
        if login_1h > 20:
            _add("Behavioral Abuse", 60,
                 f"Login anomali ekstrem: {int(login_1h)}x dalam 1 jam", int(login_1h))
            critical_trigger = True
        elif login_1h > 10:
            _add("Behavioral Abuse", 40,
                 f"Login anomali: {int(login_1h)}x dalam 1 jam", int(login_1h))

    if _use("promo_ratio"):
        promo = float(row.get("promo_ratio", 0) or 0)
        txn_count = float(row.get("txn_f1m", 0) or 0)
        if promo >= 1.0 and txn_count >= 5:
            _add("Behavioral Abuse", 15,
                 f"Semua transaksi menggunakan promo (100%, {int(txn_count)} transaksi)", "100%")
        elif promo > 0.8 and txn_count >= 5:
            _add("Behavioral Abuse", 10,
                 f"Rasio promo sangat tinggi ({promo * 100:.0f}%, {int(txn_count)} transaksi)",
                 f"{promo * 100:.0f}%")

    # ── D. Network Fraud (tiered: take highest for ref_ring) ────────────────
    if _use("ref_ring"):
        ref_ring = float(row.get("ref_ring", 0) or 0)
        if ref_ring > 100:
            _add("Network Fraud", 60,
                 f"Referral ring ekstrem (score: {ref_ring:.1f})", round(ref_ring, 1))
            critical_trigger = True
        elif ref_ring > 3:
            _add("Network Fraud", 25,
                 f"Referral ring mencurigakan (score: {ref_ring:.1f})", round(ref_ring, 1))

    if _use("ref_cnt"):
        ref_cnt = float(row.get("ref_cnt", 0) or 0)
        if ref_cnt >= 3:
            _add("Network Fraud", 10, f"Jumlah referral tinggi ({int(ref_cnt)})", int(ref_cnt))

    rule_score = min(100.0, raw_points)
    return rule_score, breakdown, critical_trigger, raw_points


def compute_rule_score(row: dict[str, Any], stage_features: set[str] | None = None) -> float:
    total, _, _, _ = explain_rule_score(row, stage_features)
    return total


def compute_final_risk(rule_score: float, ml_probability: float, critical_trigger: bool) -> tuple[str, bool]:
    """Return (final_risk_category, score_conflict).

    HIGH   : rule >= 70 OR ml >= 0.85 OR critical_trigger
    MEDIUM : rule >= 40 OR ml >= 0.60
    LOW    : otherwise

    Conflict: (rule < 40 AND ml >= 0.85) OR (rule >= 70 AND ml < 0.60)
    """
    if critical_trigger or rule_score >= 70 or ml_probability >= 0.85:
        category = "High"
    elif rule_score >= 40 or ml_probability >= 0.60:
        category = "Medium"
    else:
        category = "Low"

    conflict = (rule_score < 40 and ml_probability >= 0.85) or (rule_score >= 70 and ml_probability < 0.60)
    return category, conflict

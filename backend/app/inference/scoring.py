from typing import Any


def categorize_risk(score: float) -> str:
    if score > 60:
        return "High"
    if score > 30:
        return "Medium"
    return "Low"


def compute_rule_score(row: dict[str, Any], stage_features: set[str] | None = None) -> float:
    def _use(feature: str) -> bool:
        return stage_features is None or feature in stage_features

    score = 0.0

    if _use("disp_email") and (row.get("disp_email") is True or row.get("disp_email") == 1):
        score += 15

    if _use("max_acc_dev"):
        max_dev = float(row.get("max_acc_dev", 0) or 0)
        if max_dev > 5:
            score += 40
        elif max_dev > 2:
            score += 15

    if _use("max_acc_addr"):
        if float(row.get("max_acc_addr", 0) or 0) > 5:
            score += 20

    if _use("max_acc_ip"):
        if float(row.get("max_acc_ip", 0) or 0) > 5:
            score += 15

    if _use("login_v1h"):
        if float(row.get("login_v1h", 0) or 0) > 10:
            score += 40

    if _use("promo_ratio"):
        if float(row.get("promo_ratio", 0) or 0) > 0.8:
            score += 15

    if _use("reg2txn_min"):
        reg2txn = float(row.get("reg2txn_min", 999999) or 999999)
        if 0 <= reg2txn < 30:
            score += 15

    if _use("newuser_voucher"):
        if float(row.get("newuser_voucher", 0) or 0) > 2:
            score += 10

    if _use("ref_ring"):
        ref_ring = float(row.get("ref_ring", 0) or 0)
        if ref_ring > 100:
            score += 40
        elif ref_ring > 3:
            score += 25

    if _use("ref_cnt"):
        if float(row.get("ref_cnt", 0) or 0) >= 3:
            score += 10

    return min(100.0, score)

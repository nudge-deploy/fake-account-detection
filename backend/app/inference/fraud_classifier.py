"""
Purpose: Classify the most likely fraud type from available inference signals.
Used by: Backend lifecycle inference engine and API responses.
Main dependencies: rule-derived feature rows and fraud label mapping.
Public/main functions: classify_fraud_types.
Side effects: None.
"""

from typing import Any

FRAUD_TYPE_LABELS = {
    "unknown_fraud": "Fraud terdeteksi",
    "normal": "Bukan fraud",
    "shared_device_abuse": "Shared Device Abuse - banyak akun di perangkat sama",
    "shared_address_abuse": "Shared Address Abuse - banyak akun di alamat pengiriman sama",
    "shared_payment_abuse": "Shared Payment Abuse - banyak akun pakai metode bayar sama",
    "voucher_farming": "Voucher Farming - eksploitasi voucher/promo pengguna baru",
    "referral_abuse": "Referral Abuse - pola referral ring / farming",
}


def _signal_scores(row: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}

    max_dev = float(row.get("max_acc_dev", 0) or 0)
    if max_dev > 2:
        scores["shared_device_abuse"] = max_dev * 10

    max_addr = float(row.get("max_acc_addr", 0) or 0)
    if max_addr > 3:
        scores["shared_address_abuse"] = max_addr * 8

    max_pay = float(row.get("max_acc_pay", 0) or 0)
    if max_pay > 2:
        scores["shared_payment_abuse"] = max_pay * 9

    promo_ratio = float(row.get("promo_ratio", 0) or 0)
    txn_f1m = float(row.get("txn_f1m", 0) or 0)
    newuser_voucher = float(row.get("newuser_voucher", 0) or 0)
    reg2txn = float(row.get("reg2txn_min", 999999) or 999999)
    if (promo_ratio > 0.8 and txn_f1m > 0) or (newuser_voucher > 0 and reg2txn < 60):
        scores["voucher_farming"] = promo_ratio * 50 + newuser_voucher * 5

    ref_ring = float(row.get("ref_ring", 0) or 0)
    ref_cnt = float(row.get("ref_cnt", 0) or 0)
    if ref_ring > 3 or ref_cnt >= 3:
        scores["referral_abuse"] = ref_ring * 5 + ref_cnt * 3

    return scores


def classify_fraud_types(
    row: dict[str, Any],
    is_suspicious: bool,
) -> tuple[str, list[tuple[str, str, float]]]:
    scores = _signal_scores(row)
    ranked = sorted(
        [(key, FRAUD_TYPE_LABELS[key], score) for key, score in scores.items()],
        key=lambda x: x[2],
        reverse=True,
    )

    if not ranked:
        primary = "normal" if not is_suspicious else "unknown_fraud"
        label = FRAUD_TYPE_LABELS.get(primary, "Tidak diklasifikasikan")
        return primary, [(primary, label, 0.0)]

    return ranked[0][0], ranked

from typing import Any, Optional

from .stages import CustomerType, LifecycleStage, features_available_at_stage, features_available_for_customer


def generate_reasons(
    row: dict[str, Any],
    stage: LifecycleStage | None = None,
    customer_type: Optional[CustomerType] = None,
) -> list[str]:
    if customer_type == CustomerType.NEW and stage:
        available = features_available_for_customer(stage, customer_type)
    elif stage:
        available = features_available_at_stage(stage)
    else:
        available = None
    reasons: list[str] = []

    def _can_use(feature: str) -> bool:
        return available is None or feature in available

    if _can_use("max_acc_dev"):
        max_dev = float(row.get("max_acc_dev", 0) or 0)
        if max_dev > 5:
            reasons.append(
                f"Extreme device sharing ({int(max_dev)} akun memakai fingerprint perangkat sama)"
            )
        elif max_dev > 2:
            reasons.append(
                f"Multiple accounts ({int(max_dev)} akun) memakai fingerprint perangkat sama"
            )

    if _can_use("disp_email") and (row.get("disp_email") is True or row.get("disp_email") == 1):
        reasons.append("Email domain disposable/temporary terdeteksi saat registrasi")

    if _can_use("email_rand"):
        email_rand = float(row.get("email_rand", 0) or 0)
        if email_rand > 3.5:
            reasons.append(f"Nama email terlihat acak/generated (entropi {email_rand:.2f})")

    if _can_use("phone_score"):
        phone_score = float(row.get("phone_score", 0) or 0)
        if phone_score > 0.7:
            reasons.append(f"Pola nomor HP mencurigakan (skor {phone_score:.2f})")

    if _can_use("is_email_verified") and row.get("is_email_verified") == 0:
        reasons.append("Email belum diverifikasi saat registrasi")

    if _can_use("is_phone_verified") and row.get("is_phone_verified") == 0:
        reasons.append("Nomor HP belum diverifikasi saat registrasi")

    if _can_use("max_acc_addr"):
        max_addr = float(row.get("max_acc_addr", 0) or 0)
        if max_addr > 5:
            reasons.append(
                f"Extreme address sharing ({int(max_addr)} akun di grup alamat pengiriman sama)"
            )

    if _can_use("max_acc_pay"):
        max_pay = float(row.get("max_acc_pay", 0) or 0)
        if max_pay > 3:
            reasons.append(
                f"Suspicious payment sharing ({int(max_pay)} akun memakai metode bayar sama)"
            )

    if _can_use("promo_ratio") and _can_use("txn_f1m"):
        promo_ratio = float(row.get("promo_ratio", 0) or 0)
        txn_f1m = float(row.get("txn_f1m", 0) or 0)
        if promo_ratio > 0.9 and txn_f1m > 0:
            reasons.append(
                f"Indikasi eksploitasi voucher ({promo_ratio * 100:.1f}% transaksi pakai promo)"
            )

    if _can_use("ref_ring"):
        ref_ring = float(row.get("ref_ring", 0) or 0)
        if ref_ring > 3:
            reasons.append(
                f"Skor referral ring tinggi ({ref_ring:.2f}) - struktur referral melingkar"
            )

    if _can_use("degree"):
        degree = float(row.get("degree", 0) or 0)
        if degree > 10:
            reasons.append(f"Terhubung tinggi di graf jaringan (degree={int(degree)})")

    if _can_use("shared_ip_count"):
        shared_ip = float(row.get("shared_ip_count", 0) or 0)
        if shared_ip > 3:
            reasons.append(
                f"IP sharing tinggi ({int(shared_ip)} IP dibagi dengan node lain)"
            )

    if _can_use("login_v1h"):
        login_v1h = float(row.get("login_v1h", 0) or 0)
        if login_v1h > 10:
            reasons.append(f"Frekuensi login abnormal ({int(login_v1h)}x dalam jam pertama hari)")

    if _can_use("reg2txn_min") and _can_use("newuser_voucher"):
        reg2txn = float(row.get("reg2txn_min", 999999) or 999999)
        newuser_voucher = float(row.get("newuser_voucher", 0) or 0)
        if 0 <= reg2txn < 30 and newuser_voucher > 0:
            reasons.append(
                f"Transaksi pertama sangat cepat ({int(reg2txn)} menit setelah registrasi) + voucher baru"
            )

    if not reasons and float(row.get("risk_score", 0) or 0) >= 20:
        reasons.append(
            f"Skor risiko terkumpul ({int(row['risk_score'])}) dari beberapa sinyal minor"
        )

    return reasons

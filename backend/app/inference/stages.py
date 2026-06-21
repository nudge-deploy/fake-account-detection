"""
Purpose: Define lifecycle stages, customer types, and stage-specific feature availability rules.
Used by: Backend inference engine, feature builder, and API lifecycle services.
Main dependencies: None besides Python enums and local feature group constants.
Public/main functions: LifecycleStage, CustomerType, features_available_at_stage, features_available_for_customer.
Side effects: None.
"""

from enum import Enum


class LifecycleStage(str, Enum):
    REGISTRATION = "registration"
    LOGIN = "login"
    CHECKOUT = "checkout"
    TRANSACTION_COMPLETED = "transaction_completed"

    @classmethod
    def ordered(cls):
        return [
            cls.REGISTRATION,
            cls.LOGIN,
            cls.CHECKOUT,
            cls.TRANSACTION_COMPLETED,
        ]

    def index(self) -> int:
        return self.ordered().index(self)


class CustomerType(str, Enum):
    NEW = "new"
    EXISTING = "existing"


STAGE_FEATURE_GROUPS = {
    LifecycleStage.REGISTRATION: [
        "email_len", "email_num_ratio", "email_rand", "disp_email", "phone_score",
        "uniq_dev", "max_acc_dev", "shared_device_count",
        "ref_cnt", "ref_ring", "degree", "comp_size", "cluster", "shared_ent",
    ],
    LifecycleStage.LOGIN: [
        "max_acc_ip", "login_v1h", "login_v2h", "login_v3h", "login_v4h",
        "login_v5h", "login_v6h", "login_v12h", "login_v18h", "login_v24h",
        "shared_ip_count",
    ],
    LifecycleStage.CHECKOUT: [
        "uniq_addr", "max_acc_addr", "shared_address_count",
        "uniq_pay", "max_acc_pay", "shared_payment_count",
    ],
    LifecycleStage.TRANSACTION_COMPLETED: [
        "promo_ratio", "reg2txn_min", "newuser_voucher",
        "txn_f1m", "amt_f1m", "avg_amt1m", "promo_f1m", "voucher_f1m",
        "txn_f2m", "amt_f2m", "avg_amt2m", "promo_f2m", "voucher_f2m",
        "txn_f3m", "amt_f3m", "avg_amt3m", "promo_f3m", "voucher_f3m",
        "txn_f4m", "amt_f4m", "avg_amt4m", "promo_f4m", "voucher_f4m",
        "txn_f5m", "amt_f5m", "avg_amt5m", "promo_f5m", "voucher_f5m",
        "txn_f6m", "amt_f6m", "avg_amt6m", "promo_f6m", "voucher_f6m",
    ],
}

NEW_USER_REGISTRATION_FEATURES = [
    "email_len", "email_num_ratio", "email_rand", "disp_email", "phone_score",
    "full_name_len", "is_email_verified", "is_phone_verified", "age_years", "registration_hour",
]

STAGE_FEATURE_GROUPS_NEW = {
    LifecycleStage.REGISTRATION: NEW_USER_REGISTRATION_FEATURES,
    LifecycleStage.LOGIN: NEW_USER_REGISTRATION_FEATURES
    + STAGE_FEATURE_GROUPS[LifecycleStage.LOGIN],
    LifecycleStage.CHECKOUT: NEW_USER_REGISTRATION_FEATURES
    + STAGE_FEATURE_GROUPS[LifecycleStage.LOGIN]
    + STAGE_FEATURE_GROUPS[LifecycleStage.CHECKOUT],
    LifecycleStage.TRANSACTION_COMPLETED: NEW_USER_REGISTRATION_FEATURES
    + STAGE_FEATURE_GROUPS[LifecycleStage.LOGIN]
    + STAGE_FEATURE_GROUPS[LifecycleStage.CHECKOUT]
    + STAGE_FEATURE_GROUPS[LifecycleStage.TRANSACTION_COMPLETED],
}


def features_available_at_stage(stage: LifecycleStage) -> set[str]:
    available = set()
    for s in LifecycleStage.ordered():
        available.update(STAGE_FEATURE_GROUPS[s])
        if s == stage:
            break
    return available


def features_available_for_customer(stage: LifecycleStage, customer_type: CustomerType) -> set[str]:
    if customer_type == CustomerType.EXISTING:
        return features_available_at_stage(stage)

    available = set()
    for s in LifecycleStage.ordered():
        available.update(STAGE_FEATURE_GROUPS_NEW[s])
        if s == stage:
            break
    return available


STAGE_LABELS_ID = {
    LifecycleStage.REGISTRATION: "Setelah Registrasi (post-OTP)",
    LifecycleStage.LOGIN: "Setelah Login",
    LifecycleStage.CHECKOUT: "Saat Checkout (alamat & pembayaran)",
    LifecycleStage.TRANSACTION_COMPLETED: "Setelah Transaksi Selesai",
}

CONFIDENCE_NOTES = {
    LifecycleStage.REGISTRATION: (
        "Kepercayaan terbatas - hanya data identitas & perangkat. "
        "Pantau ulang setelah login dan transaksi."
    ),
    LifecycleStage.LOGIN: (
        "Kepercayaan sedang - pola login & IP tersedia. "
        "Skor dapat berubah setelah checkout/transaksi."
    ),
    LifecycleStage.CHECKOUT: (
        "Kepercayaan cukup - alamat & metode pembayaran sudah masuk. "
        "Konfirmasi akhir setelah transaksi selesai."
    ),
    LifecycleStage.TRANSACTION_COMPLETED: (
        "Kepercayaan penuh - seluruh fitur perilaku transaksi tersedia."
    ),
}

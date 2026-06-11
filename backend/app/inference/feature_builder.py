"""
Purpose: Build lifecycle feature vectors for Alfagift inference from staged app inputs.
Used by: ContinuousInferenceService and backend lifecycle inference routes.
Main dependencies: raw reference CSVs, ABT lookup, and stage/customer-type rules.
Public/main functions: calc_entropy, calc_phone_pattern_score, identity_features, AlfagiftFeatureBuilder.build.
Side effects: Reads local raw CSVs and ABT when building inference features.
"""

from __future__ import annotations

import math
import os
from collections import Counter
from typing import Any, Optional

import pandas as pd

from app.utils.config import BASE_DIR, ABT_PATH
from .stages import CustomerType, LifecycleStage


DISPOSABLE_DOMAINS = {"mailinator.com", "yopmail.com", "tempmail.com"}


def calc_entropy(text: str) -> float:
    if not text or not isinstance(text, str):
        return 0.0
    counts = Counter(text)
    text_len = len(text)
    return sum(-(c / text_len) * math.log2(c / text_len) for c in counts.values())


def calc_phone_pattern_score(phone: str) -> float:
    if not phone or not isinstance(phone, str):
        return 0.0
    digits = [c for c in phone if c.isdigit()]
    if not digits:
        return 0.0
    unique_ratio = len(set(digits)) / len(digits)
    consecutive = sum(1 for i in range(len(digits) - 1) if digits[i] == digits[i + 1])
    return (1.0 - unique_ratio) * 0.7 + (consecutive / len(digits)) * 0.3


def identity_features(email: str, phone: str) -> dict[str, Any]:
    email = str(email or "")
    phone = str(phone or "")
    email_name = email.split("@")[0] if "@" in email else email
    email_domain = email.split("@")[1] if "@" in email else ""
    num_digits = sum(c.isdigit() for c in email_name)
    return {
        "email_len": len(email),
        "email_num_ratio": num_digits / len(email_name) if email_name else 0.0,
        "email_rand": calc_entropy(email_name),
        "disp_email": int(email_domain.lower() in DISPOSABLE_DOMAINS),
        "phone_score": calc_phone_pattern_score(phone),
    }


class AlfagiftFeatureBuilder:
    """Hitung fitur model dari payload event Alfagift + data referensi populasi."""

    def __init__(self, feature_columns: list[str]):
        self.feature_columns = feature_columns
        self.raw_dir = os.path.join(BASE_DIR, "data", "raw")
        self.df_abt: Optional[pd.DataFrame] = None
        self._reference: dict[str, pd.DataFrame] = {}
        self._load_reference_data()

    def _load_reference_data(self) -> None:
        if os.path.exists(ABT_PATH):
            self.df_abt = pd.read_csv(ABT_PATH)
            self.df_abt["uid"] = self.df_abt["uid"].astype(str)

        for name in (
            "devices",
            "user_devices",
            "addresses",
            "user_addresses",
            "payments",
            "user_payments",
            "referrals",
        ):
            path = os.path.join(self.raw_dir, f"{name}.csv")
            if os.path.exists(path):
                self._reference[name] = pd.read_csv(path)

    def _empty_features(self) -> dict[str, Any]:
        return {col: 0 for col in self.feature_columns}

    def _abt_row_for_uid(self, uid: str) -> Optional[dict[str, Any]]:
        if self.df_abt is None:
            return None
        matches = self.df_abt[self.df_abt["uid"] == str(uid)]
        if matches.empty:
            return None
        return matches.iloc[0].to_dict()

    def _device_sharing(self, device_id: Optional[str], device_fingerprint: Optional[str]) -> dict[str, int]:
        df_ud = self._reference.get("user_devices")
        df_dev = self._reference.get("devices")
        if df_ud is None:
            return {"uniq_dev": 1, "max_acc_dev": 1, "shared_device_count": 0}

        resolved_id = device_id
        if not resolved_id and device_fingerprint and df_dev is not None:
            match = df_dev[df_dev["device_fingerprint"] == device_fingerprint]
            if not match.empty:
                resolved_id = match.iloc[0]["device_id"]

        if not resolved_id:
            return {"uniq_dev": 1, "max_acc_dev": 1, "shared_device_count": 0}

        users_on_device = df_ud[df_ud["device_id"] == resolved_id]["user_id"].nunique()
        return {
            "uniq_dev": 1,
            "max_acc_dev": int(users_on_device),
            "shared_device_count": max(0, int(users_on_device) - 1),
        }

    def _address_sharing(self, address_id: Optional[str]) -> dict[str, int]:
        df_ua = self._reference.get("user_addresses")
        if df_ua is None or not address_id:
            return {"uniq_addr": 0, "max_acc_addr": 0, "shared_address_count": 0}

        users_on_addr = df_ua[df_ua["address_id"] == address_id]["user_id"].nunique()
        return {
            "uniq_addr": 1,
            "max_acc_addr": int(users_on_addr),
            "shared_address_count": max(0, int(users_on_addr) - 1),
        }

    def _payment_sharing(self, payment_id: Optional[str], payment_identifier: Optional[str]) -> dict[str, int]:
        df_up = self._reference.get("user_payments")
        df_pay = self._reference.get("payments")
        if df_up is None:
            return {"uniq_pay": 0, "max_acc_pay": 0, "shared_payment_count": 0}

        resolved_id = payment_id
        if not resolved_id and payment_identifier and df_pay is not None:
            for col in ("payment_identifier", "masked_payment_number", "payment_token", "wallet_id", "card_hash", "bank_account_hash"):
                if col in df_pay.columns:
                    match = df_pay[df_pay[col].astype(str) == str(payment_identifier)]
                    if not match.empty:
                        resolved_id = match.iloc[0]["payment_id"]
                        break

        if not resolved_id:
            return {"uniq_pay": 0, "max_acc_pay": 0, "shared_payment_count": 0}

        users_on_pay = df_up[df_up["payment_id"] == resolved_id]["user_id"].nunique()
        return {
            "uniq_pay": 1,
            "max_acc_pay": int(users_on_pay),
            "shared_payment_count": max(0, int(users_on_pay) - 1),
        }

    def _referral_features(self, uid: Optional[str], referral_code: Optional[str]) -> dict[str, float]:
        df_ref = self._reference.get("referrals")
        if df_ref is None:
            return {"ref_cnt": 0, "ref_ring": 0.0}

        ref_cnt = 0
        if uid:
            ref_cnt = int(df_ref[df_ref["referrer_user_id"] == uid].shape[0])

        ref_ring = 0.0
        if uid and uid in df_ref.get("referred_user_id", pd.Series()).values:
            ref_ring = 1.0

        if referral_code:
            ref_cnt = 1

        return {"ref_cnt": ref_cnt, "ref_ring": ref_ring}

    def _login_features(self, payload: dict[str, Any], uid: Optional[str]) -> dict[str, Any]:
        login_v1h = int(payload.get("login_count_1h") or payload.get("login_v1h") or 1)
        login_v24h = int(payload.get("login_count_24h") or payload.get("login_v24h") or login_v1h)
        max_acc_ip = int(payload.get("accounts_on_same_ip") or 1)

        if uid and self.df_abt is not None:
            row = self._abt_row_for_uid(uid)
            if row:
                return {
                    "max_acc_ip": int(row.get("max_acc_ip", max_acc_ip)),
                    "login_v1h": int(row.get("login_v1h", login_v1h)),
                    "login_v2h": int(row.get("login_v2h", login_v1h)),
                    "login_v3h": int(row.get("login_v3h", login_v1h)),
                    "login_v4h": int(row.get("login_v4h", login_v1h)),
                    "login_v5h": int(row.get("login_v5h", login_v1h)),
                    "login_v6h": int(row.get("login_v6h", login_v1h)),
                    "login_v12h": int(row.get("login_v12h", login_v24h)),
                    "login_v18h": int(row.get("login_v18h", login_v24h)),
                    "login_v24h": int(row.get("login_v24h", login_v24h)),
                    "shared_ip_count": int(row.get("shared_ip_count", 0)),
                }

        return {
            "max_acc_ip": max_acc_ip,
            "login_v1h": login_v1h,
            "login_v2h": login_v1h,
            "login_v3h": login_v1h,
            "login_v4h": login_v1h,
            "login_v5h": login_v1h,
            "login_v6h": login_v1h,
            "login_v12h": login_v24h,
            "login_v18h": login_v24h,
            "login_v24h": login_v24h,
            "shared_ip_count": max(0, max_acc_ip - 1),
        }

    def _transaction_features(self, payload: dict[str, Any]) -> dict[str, Any]:
        order_amount = float(payload.get("order_amount") or 0)
        voucher_used = bool(payload.get("voucher_used"))
        new_user_voucher = int(payload.get("new_user_voucher") or (1 if voucher_used else 0))
        reg2txn = int(payload.get("minutes_since_registration") or payload.get("reg2txn_min") or 999999)
        promo_ratio = float(payload.get("promo_ratio") or (1.0 if voucher_used else 0.0))

        txn_count = 1 if order_amount > 0 else 0
        return {
            "promo_ratio": promo_ratio,
            "reg2txn_min": reg2txn,
            "newuser_voucher": new_user_voucher,
            "txn_f1m": txn_count,
            "amt_f1m": int(order_amount),
            "avg_amt1m": int(order_amount),
            "promo_f1m": int(payload.get("promo_discount") or 0),
            "voucher_f1m": 1 if voucher_used else 0,
        }

    def _graph_features(self, uid: Optional[str]) -> dict[str, Any]:
        if not uid:
            return {}
        row = self._abt_row_for_uid(uid)
        if not row:
            return {}
        return {
            k: row.get(k, 0)
            for k in ("degree", "comp_size", "cluster", "shared_ent")
            if k in self.feature_columns
        }

    def build(
        self,
        stage: LifecycleStage,
        customer_type: CustomerType,
        payload: dict[str, Any],
        uid: Optional[str] = None,
    ) -> tuple[dict[str, Any], str]:
        """
        Returns (feature_row, resolved_uid).
        """
        resolved_uid = str(uid or payload.get("uid") or f"GUEST_{payload.get('phone_number', 'unknown')[-4:]}")

        if customer_type == CustomerType.EXISTING and uid:
            abt_row = self._abt_row_for_uid(uid)
            if abt_row:
                features = self._empty_features()
                for col in self.feature_columns:
                    val = abt_row.get(col, 0)
                    features[col] = 0 if pd.isna(val) else val
                return features, resolved_uid

        features = self._empty_features()
        stage_idx = stage.index()
        is_new_user = customer_type == CustomerType.NEW

        if stage_idx >= LifecycleStage.REGISTRATION.index():
            email = payload.get("email", "")
            phone = payload.get("phone_number", "")
            if is_new_user:
                identity = identity_features(email, phone)
                features["email_len"] = identity.get("email_len", 0)
                features["email_num_ratio"] = identity.get("email_num_ratio", 0)
                features["email_rand"] = identity.get("email_rand", 0)
                features["disp_email"] = identity.get("disp_email", 0)
                features["phone_score"] = identity.get("phone_score", 0)
                features["full_name_len"] = len(str(payload.get("full_name") or ""))
                features["is_email_verified"] = int(bool(payload.get("is_email_verified", False)))
                features["is_phone_verified"] = int(bool(payload.get("is_phone_verified", False)))
                dob = payload.get("date_of_birth")
                reg_hour = payload.get("registration_hour")
                if reg_hour is None:
                    reg_hour = pd.Timestamp.now().hour
                features["registration_hour"] = int(reg_hour)
                if dob:
                    try:
                        dob_dt = pd.to_datetime(dob)
                        features["age_years"] = (pd.Timestamp.now() - dob_dt).days / 365.25
                    except Exception:
                        features["age_years"] = 0
            else:
                features.update(identity_features(email, phone))
                features.update(
                    self._device_sharing(
                        payload.get("device_id"),
                        payload.get("device_fingerprint"),
                    )
                )
                features.update(self._referral_features(uid, payload.get("referral_code")))
                features.update(self._graph_features(uid))

        if stage_idx >= LifecycleStage.LOGIN.index():
            features.update(self._login_features(payload, uid))

        if stage_idx >= LifecycleStage.CHECKOUT.index():
            features.update(self._address_sharing(payload.get("address_id")))
            features.update(
                self._payment_sharing(
                    payload.get("payment_id"),
                    payload.get("payment_identifier"),
                )
            )

        if stage_idx >= LifecycleStage.TRANSACTION_COMPLETED.index():
            features.update(self._transaction_features(payload))

        return features, resolved_uid

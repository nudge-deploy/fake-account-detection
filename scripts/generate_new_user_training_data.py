"""
Purpose: Generate a balanced registration-only dataset for the new-user fraud model.
Used by: New-user model training workflow and documentation audits.
Main dependencies: users.csv, fake_account_abt.csv, pandas, numpy.
Public/main functions: generate_new_user_training_data.
Side effects: Writes a balanced CSV to data/processed/new_user_training_data.csv.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
USERS_PATH = os.path.join(BASE_DIR, "data", "raw", "users.csv")
ABT_PATH = os.path.join(BASE_DIR, "data", "abt", "fake_account_abt.csv")
OUT_PATH = os.path.join(BASE_DIR, "data", "processed", "new_user_training_data.csv")

DISPOSABLE_DOMAINS = {"mailinator.com", "yopmail.com", "tempmail.com"}
FRAUD_PHONE_THRESHOLD = 0.42


def calc_entropy(text: str) -> float:
    if not text or not isinstance(text, str):
        return 0.0
    counts = text and {c: text.count(c) for c in set(text)}
    n = len(text)
    return float(sum(-(c / n) * np.log2(c / n) for c in counts.values()))


def calc_phone_pattern_score(phone: str) -> float:
    if not phone or not isinstance(phone, str):
        return 0.0
    digits = [c for c in phone if c.isdigit()]
    if not digits:
        return 0.0
    unique_ratio = len(set(digits)) / len(digits)
    consecutive = sum(1 for i in range(len(digits) - 1) if digits[i] == digits[i + 1])
    return float((1.0 - unique_ratio) * 0.7 + (consecutive / len(digits)) * 0.3)


def build_registration_features(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    email = df["email"].fillna("").astype(str)
    phone = df["phone_number"].fillna("").astype(str)
    full_name = df["full_name"].fillna("").astype(str)
    username = email.str.split("@").str[0].fillna("")
    domain = email.str.split("@").str[1].fillna("")

    out["uid"] = df["uid"].astype(str)
    out["email_len"] = email.str.len()
    out["email_num_ratio"] = username.apply(lambda x: sum(ch.isdigit() for ch in x) / len(x) if x else 0.0)
    out["email_rand"] = username.apply(calc_entropy)
    out["disp_email"] = domain.str.lower().isin(DISPOSABLE_DOMAINS).astype(int)
    out["phone_score"] = phone.apply(calc_phone_pattern_score)
    out["full_name_len"] = full_name.str.len()
    out["is_email_verified"] = df["is_email_verified"].fillna(False).astype(int)
    out["is_phone_verified"] = df["is_phone_verified"].fillna(False).astype(int)
    out["age_years"] = (
        pd.to_datetime(df["registration_date"]) - pd.to_datetime(df["date_of_birth"])
    ).dt.days / 365.25
    out["registration_hour"] = pd.to_datetime(df["registration_date"]).dt.hour
    out["registration_channel"] = df["registration_channel"].fillna("unknown").astype(str)
    out["city"] = df["city"].fillna("unknown").astype(str)
    out["province"] = df["province"].fillna("unknown").astype(str)
    return out


def assign_new_user_label(row: pd.Series) -> tuple[int, str]:
    if int(row.get("disp_email", 0)) == 1:
        return 1, "disposable_email"
    if float(row.get("phone_score", 0) or 0) >= FRAUD_PHONE_THRESHOLD:
        return 1, "suspicious_phone_pattern"
    return 0, "normal"


def generate_new_user_training_data():
    users = pd.read_csv(USERS_PATH)
    abt = pd.read_csv(ABT_PATH)

    df = users.rename(columns={"user_id": "uid"}).merge(
        abt[["uid", "fraud", "ftype"]],
        on="uid",
        how="left",
    )
    df["fraud"] = df["fraud"].fillna(False).astype(int)
    df["ftype"] = df["ftype"].fillna("normal").astype(str)

    feats = build_registration_features(df)
    labels = feats.apply(assign_new_user_label, axis=1, result_type="expand")
    feats["fraud"] = labels[0].astype(int)
    feats["ftype"] = labels[1].astype(str)

    fraud = feats[feats["fraud"] == 1].copy()
    normal = feats[feats["fraud"] == 0].copy()

    if fraud.empty or normal.empty:
        raise ValueError("Need both fraud and normal rows to build balanced dataset.")

    target_n = min(len(fraud), len(normal))
    fraud_sample = fraud.sample(n=target_n, random_state=42, replace=len(fraud) < target_n)
    normal_sample = normal.sample(n=target_n, random_state=42, replace=len(normal) < target_n)

    balanced = pd.concat([fraud_sample, normal_sample], ignore_index=True)
    balanced = balanced.sample(frac=1.0, random_state=42).reset_index(drop=True)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    balanced.to_csv(OUT_PATH, index=False)
    print(f"Saved balanced new-user dataset: {OUT_PATH}")
    print(f"Rows: {len(balanced)} | Fraud: {balanced['fraud'].sum()} | Normal: {(balanced['fraud'] == 0).sum()}")


if __name__ == "__main__":
    generate_new_user_training_data()

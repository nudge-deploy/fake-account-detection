"""Purpose: Upload generated CSV tables into an empty Supabase project.
Used by: Manual data loading after running database_schema.sql.
Depends on: .env SUPABASE_URL/SUPABASE_KEY, pandas, supabase client, generated CSVs.
Public functions: main, upload_csv_table, normalize_dataframe, normalize_value.
Side effects: Upserts rows into Supabase tables over HTTP.
"""

import os
import sys
import math
from typing import Iterable

import pandas as pd
from dotenv import load_dotenv
from supabase import Client, create_client


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
ABT_DIR = os.path.join(BASE_DIR, "data", "abt")
BATCH_SIZE = 500

TABLE_LOAD_ORDER = [
    ("users", os.path.join(RAW_DIR, "users.csv")),
    ("devices", os.path.join(RAW_DIR, "devices.csv")),
    ("addresses", os.path.join(RAW_DIR, "addresses.csv")),
    ("payments", os.path.join(RAW_DIR, "payments.csv")),
    ("vouchers", os.path.join(RAW_DIR, "vouchers.csv")),
    ("user_devices", os.path.join(RAW_DIR, "user_devices.csv")),
    ("user_addresses", os.path.join(RAW_DIR, "user_addresses.csv")),
    ("user_payments", os.path.join(RAW_DIR, "user_payments.csv")),
    ("transactions", os.path.join(RAW_DIR, "transactions.csv")),
    ("transaction_items", os.path.join(RAW_DIR, "transaction_items.csv")),
    ("login_sessions", os.path.join(RAW_DIR, "login_sessions.csv")),
    ("referrals", os.path.join(RAW_DIR, "referrals.csv")),
    ("fraud_labels", os.path.join(RAW_DIR, "fraud_labels.csv")),
    ("fake_account_abt", os.path.join(ABT_DIR, "fake_account_abt.csv")),
]

BOOLEAN_COLUMNS = {
    "users": ["is_email_verified", "is_phone_verified"],
    "user_addresses": ["is_default_address"],
    "user_payments": ["is_default_payment"],
    "referrals": ["reward_claimed"],
    "fraud_labels": ["is_fake_account"],
    "fake_account_abt": ["fraud", "disp_email"],
}


def chunked(records: list[dict], size: int) -> Iterable[list[dict]]:
    for idx in range(0, len(records), size):
        yield records[idx : idx + size]


def normalize_dataframe(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    df = df.astype(object).where(pd.notna(df), None)

    for column in BOOLEAN_COLUMNS.get(table_name, []):
        if column in df.columns:
            df[column] = df[column].map(lambda value: None if value is None else bool(value))

    return df


def normalize_value(value):
    if value is None:
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if pd.isna(value):
        return None
    return value


def upload_csv_table(supabase: Client, table_name: str, csv_path: str) -> None:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found for {table_name}: {csv_path}")

    df = normalize_dataframe(table_name, pd.read_csv(csv_path))
    records = [
        {key: normalize_value(value) for key, value in record.items()}
        for record in df.to_dict(orient="records")
    ]

    print(f"Uploading {len(records)} rows into {table_name}...")
    for idx, batch in enumerate(chunked(records, BATCH_SIZE), start=1):
        supabase.table(table_name).upsert(batch).execute()
        print(f"  {table_name}: batch {idx} ({len(batch)} rows)")


def main() -> None:
    load_dotenv(os.path.join(BASE_DIR, ".env"))

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("[ERROR] SUPABASE_URL and SUPABASE_KEY must be set in .env")
        sys.exit(1)

    supabase = create_client(url, key)

    for table_name, csv_path in TABLE_LOAD_ORDER:
        upload_csv_table(supabase, table_name, csv_path)

    print("Supabase upload completed successfully.")


if __name__ == "__main__":
    main()

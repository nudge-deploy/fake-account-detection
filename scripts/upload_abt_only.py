"""Purpose: Upload only the final ABT CSV into Supabase.
Used by: Manual reloads when raw relational tables are already loaded.
Depends on: .env SUPABASE_URL/SUPABASE_KEY, pandas, supabase client.
Public functions: None; script entry point executes upload.
Side effects: Upserts rows into fake_account_abt over HTTP.
"""

import os
import sys
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("[ERROR] Supabase credentials not found in '.env' file!")
    sys.exit(1)

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"[ERROR] Failed to initialize Supabase client: {e}")
    sys.exit(1)

ABT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'abt', 'fake_account_abt.csv')

if not os.path.exists(ABT_PATH):
    print(f"[ERROR] ABT file not found at: {ABT_PATH}")
    sys.exit(1)

print(f"Reading ABT data from {ABT_PATH}...")
df = pd.read_csv(ABT_PATH)

# Replace NaN values with None for PostgreSQL compatibility
df = df.replace({np.nan: None})

records = df.to_dict('records')
total_records = len(records)
BATCH_SIZE = 500

print(f"Uploading {total_records} rows to Supabase table 'fake_account_abt'...")
for i in range(0, total_records, BATCH_SIZE):
    chunk = records[i:i + BATCH_SIZE]
    try:
        supabase.table('fake_account_abt').upsert(chunk).execute()
        print(f"  Uploaded chunk {i} to {i + len(chunk)}...")
    except Exception as e:
        print(f"[ERROR] Failed to upload chunk starting at {i}: {e}")
        sys.exit(1)

print("\nSuccessfully finished uploading 'fake_account_abt' table!")

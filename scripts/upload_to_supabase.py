import os
import json
import joblib
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import math

def main():
    print("Loading environment variables...")
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return
        
    print("Initializing Supabase client...")
    supabase: Client = create_client(url, key)
    
    # Paths
    BASE_DIR = os.path.join(os.path.dirname(__file__), '..')
    USERS_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'users.csv')
    ABT_PATH = os.path.join(BASE_DIR, 'data', 'abt', 'fake_account_abt.csv')
    GRAPH_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'user_graph_features.csv')
    MODEL_PATH = os.path.join(BASE_DIR, 'models', 'fake_account_model.pkl')
    FEAT_COLS_PATH = os.path.join(BASE_DIR, 'models', 'feature_columns.json')
    
    print("Loading Data...")
    df_users = pd.read_csv(USERS_PATH)
    df_abt = pd.read_csv(ABT_PATH)
    
    if os.path.exists(GRAPH_PATH):
        df_graph = pd.read_csv(GRAPH_PATH)
        df_graph = df_graph.rename(columns={
            'user_id': 'uid',
            'graph_degree': 'degree',
            'graph_cluster_size': 'cluster',
            'connected_component_size': 'comp_size',
            'shared_entity_count': 'shared_ent'
        })
        if 'degree' not in df_abt.columns:
            df_abt = df_abt.merge(df_graph, on='uid', how='left')
    
    df_abt = df_abt.fillna(0)
    
    # Load ML Model
    print("Running ML Predictions...")
    model = joblib.load(MODEL_PATH)
    with open(FEAT_COLS_PATH, 'r') as f:
        feature_cols = json.load(f)
        
    for col in feature_cols:
        if col not in df_abt.columns:
            df_abt[col] = 0
            
    X = df_abt[feature_cols]
    df_abt['ml_probability'] = model.predict_proba(X)[:, 1]
    df_abt['ml_prediction'] = model.predict(X)
    
    print("Uploading users to Supabase in batches...")
    df_users = df_users.fillna("") # Replace NaN with empty string for JSON serialization
    users_records = df_users.to_dict(orient='records')
    
    batch_size = 1000
    for i in range(0, len(users_records), batch_size):
        batch = users_records[i:i+batch_size]
        # Clean boolean columns
        for row in batch:
            row['is_email_verified'] = bool(row['is_email_verified'])
            row['is_phone_verified'] = bool(row['is_phone_verified'])
        
        try:
            supabase.table('users').upsert(batch).execute()
            print(f"  Uploaded users {i} to {i+len(batch)}")
        except Exception as e:
            print(f"Error uploading users batch: {e}")
            
    print("Uploading ABT to Supabase in batches...")
    # Convert numpy types to native python types for JSON
    for col in df_abt.columns:
        if df_abt[col].dtype in ['int64', 'int32']:
            df_abt[col] = df_abt[col].astype(int)
        elif df_abt[col].dtype in ['float64', 'float32']:
            df_abt[col] = df_abt[col].astype(float)
            
    df_abt = df_abt.fillna("")
    abt_records = df_abt.to_dict(orient='records')
    
    for i in range(0, len(abt_records), batch_size):
        batch = abt_records[i:i+batch_size]
        # Clean types
        for row in batch:
            row['disp_email'] = bool(row['disp_email'])
            row['fraud'] = bool(row['fraud'])
            
        try:
            supabase.table('fake_account_abt').upsert(batch).execute()
            print(f"  Uploaded ABT {i} to {i+len(batch)}")
        except Exception as e:
            print(f"Error uploading ABT batch: {e}")
            
    print("Migration to Supabase completed successfully!")

if __name__ == "__main__":
    main()

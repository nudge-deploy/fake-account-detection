"""Purpose: Build raw graph CSV artifacts from raw user/entity/referral tables.
Used by: extract_graph_features.py and export_graph_api.py.
Depends on: raw users, user_devices, user_addresses, user_payments, login_sessions, referrals CSVs.
Public functions: build_graph_csv.
Side effects: Writes data/processed/graph_nodes.csv and graph_edges.csv.
"""

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
NODES_CSV_PATH = os.path.join(PROCESSED_DIR, "graph_nodes.csv")
EDGES_CSV_PATH = os.path.join(PROCESSED_DIR, "graph_edges.csv")

def build_graph_csv():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df_users = pd.read_csv(os.path.join(RAW_DIR, 'users.csv'))
    df_user_devices = pd.read_csv(os.path.join(RAW_DIR, 'user_devices.csv'))
    df_user_addresses = pd.read_csv(os.path.join(RAW_DIR, 'user_addresses.csv'))
    df_user_payments = pd.read_csv(os.path.join(RAW_DIR, 'user_payments.csv'))
    df_login_sessions = pd.read_csv(os.path.join(RAW_DIR, 'login_sessions.csv'))
    df_referrals = pd.read_csv(os.path.join(RAW_DIR, 'referrals.csv'))

    nodes = []
    edges = []

    print("Creating User Nodes...")
    for uid in df_users['user_id'].unique():
        nodes.append({
            'node_id': uid,
            'node_type': 'user'
        })

    print("Creating Device Nodes & Edges...")
    for _, row in df_user_devices.iterrows():
        dev_id = row['device_id']
        nodes.append({
            'node_id': f'DEV_{dev_id}',
            'node_type': 'device'
        })
        edges.append({
            'source': row['user_id'],
            'target': f'DEV_{dev_id}',
            'edge_type': 'uses_device'
        })

    print("Creating Address Nodes & Edges...")
    for _, row in df_user_addresses.iterrows():
        addr_id = row['address_id']
        nodes.append({
            'node_id': f'ADDR_{addr_id}',
            'node_type': 'address'
        })
        edges.append({
            'source': row['user_id'],
            'target': f'ADDR_{addr_id}',
            'edge_type': 'uses_address'
        })

    print("Creating Payment Nodes & Edges...")
    for _, row in df_user_payments.iterrows():
        pay_id = row['payment_id']
        nodes.append({
            'node_id': f'PAY_{pay_id}',
            'node_type': 'payment'
        })
        edges.append({
            'source': row['user_id'],
            'target': f'PAY_{pay_id}',
            'edge_type': 'uses_payment'
        })

    print("Creating IP Nodes & Edges...")
    for _, row in df_login_sessions.iterrows():
        if pd.isna(row['ip_address']):
            continue
        ip = str(row['ip_address'])
        nodes.append({
            'node_id': f'IP_{ip}',
            'node_type': 'ip'
        })
        edges.append({
            'source': row['user_id'],
            'target': f'IP_{ip}',
            'edge_type': 'uses_ip'
        })

    print("Creating Referral Edges...")
    for _, row in df_referrals.iterrows():
        if pd.isna(row['referrer_user_id']) or pd.isna(row['referred_user_id']):
            continue
        edges.append({
            'source': row['referrer_user_id'],
            'target': row['referred_user_id'],
            'edge_type': 'referred_user'
        })

    nodes_df = pd.DataFrame(nodes).drop_duplicates(subset=['node_id'])
    edges_df = pd.DataFrame(edges).drop_duplicates()

    nodes_df.to_csv(NODES_CSV_PATH, index=False)
    edges_df.to_csv(EDGES_CSV_PATH, index=False)

    print(f"Nodes : {len(nodes_df)}")
    print(f"Edges : {len(edges_df)}")
    print("Graph CSV data saved")

if __name__ == "__main__":
    build_graph_csv()

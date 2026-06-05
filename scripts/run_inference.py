import os
import sys
import argparse
import joblib
import pandas as pd
import json

# Setup paths relative to script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'fake_account_model.pkl')
FEATURE_COLUMNS_PATH = os.path.join(BASE_DIR, 'models', 'feature_columns.json')
ABT_PATH = os.path.join(BASE_DIR, 'data', 'abt', 'fake_account_abt.csv')

def generate_reasons(row):
    reasons = []
    
    if row.get('max_acc_dev', 0) > 5:
        reasons.append(f"Extreme device sharing ({int(row['max_acc_dev'])} accounts share the same device fingerprint)")
    elif row.get('max_acc_dev', 0) > 2:
        reasons.append(f"Multiple accounts ({int(row['max_acc_dev'])} accounts) share the same device fingerprint")
        
    if row.get('disp_email') == True or row.get('disp_email') == 1:
        reasons.append("Registered using a temporary/disposable email address domain")
        
    if row.get('phone_score', 0) > 0.7:
        reasons.append(f"Phone number displays suspicious pattern score of {row['phone_score']:.2f}")
        
    if row.get('max_acc_addr', 0) > 5:
        reasons.append(f"Extreme address sharing ({int(row['max_acc_addr'])} accounts share the same shipping address group)")
        
    if row.get('max_acc_pay', 0) > 3:
        reasons.append(f"Suspicious payment sharing ({int(row['max_acc_pay'])} accounts share the same payment method)")
        
    if row.get('promo_ratio', 0) > 0.9 and row.get('txn_f1m', 0) > 0:
        reasons.append(f"Voucher exploitation indicator ({row['promo_ratio'] * 100:.1f}% of transactions used a voucher/promo)")
        
    if row.get('ref_ring', 0) > 3:
        reasons.append(f"High referral ring score of {row['ref_ring']:.2f} (deep network structure of circular referrals)")
        
    if row.get('degree', 0) > 10:
        reasons.append(f"Highly connected in network graph (degree={int(row['degree'])}: shares IPs, devices, address, or payments)")
        
    if row.get('shared_ip_count', 0) > 3:
        reasons.append(f"High IP sharing detected ({int(row['shared_ip_count'])} shared IPs with other network nodes)")
        
    return reasons

def main():
    parser = argparse.ArgumentParser(description="CLI tool to run model inference on a User from ABT.")
    parser.add_argument("--uid", type=str, help="User ID (uid) to look up in the ABT and predict.")
    args = parser.parse_args()

    # Load Model
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}")
        sys.exit(1)
    
    # Load Feature Columns
    if not os.path.exists(FEATURE_COLUMNS_PATH):
        print(f"Error: Feature columns file not found at {FEATURE_COLUMNS_PATH}")
        sys.exit(1)
        
    # Load ABT
    if not os.path.exists(ABT_PATH):
        print(f"Error: ABT not found at {ABT_PATH}")
        sys.exit(1)

    print("Loading model and features...")
    model = joblib.load(MODEL_PATH)
    with open(FEATURE_COLUMNS_PATH, 'r') as f:
        feature_cols = json.load(f)
        
    print("Loading ABT data...")
    df_abt = pd.read_csv(ABT_PATH)
    
    # Check if graph features exist and merge if needed
    PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
    graph_path = os.path.join(PROCESSED_DIR, 'user_graph_features.csv')
    if os.path.exists(graph_path):
        df_graph = pd.read_csv(graph_path)
        df_graph = df_graph.rename(columns={
            'user_id': 'uid',
            'graph_degree': 'degree',
            'graph_cluster_size': 'cluster',
            'connected_component_size': 'comp_size',
            'shared_entity_count': 'shared_ent'
        })
        if 'degree' not in df_abt.columns:
            df_abt = df_abt.merge(df_graph, on='uid', how='left')
            df_abt.fillna(0, inplace=True)

    # Resolve user_id
    if args.uid:
        user_id = args.uid
        matches = df_abt[df_abt['uid'] == user_id]
        if matches.empty:
            print(f"Error: User {user_id} not found in ABT.")
            sys.exit(1)
        row = matches.iloc[0]
    else:
        # Default to a random high-risk user or first user
        high_risk_users = df_abt[df_abt['risk_cat'] == 'High']
        if not high_risk_users.empty:
            row = high_risk_users.sample(1, random_state=42).iloc[0]
        else:
            row = df_abt.iloc[0]
        user_id = row['uid']
        print(f"No uid specified. Defaulting to sample user: {user_id}")

    # Prepare features
    # Ensure missing columns are filled with 0
    X_dict = row.to_dict()
    for col in feature_cols:
        if col not in X_dict:
            X_dict[col] = 0
            
    X = pd.DataFrame([{col: X_dict[col] for col in feature_cols}])
    X = X.fillna(0)

    # Run Prediction
    prob = float(model.predict_proba(X)[:, 1][0])
    pred = int(model.predict(X)[0])

    rule_score = float(row.get('risk_score', 0))
    risk_cat = row.get('risk_cat', 'Low')
    reasons = generate_reasons(row)

    print("\n" + "="*55)
    print(f" INFERENCE RESULTS FOR USER: {user_id}")
    print("="*55)
    print(f"ML Model Prediction      : {'FAKE ACCOUNT (1)' if pred == 1 else 'NORMAL (0)'}")
    print(f"ML Fraud Probability     : {prob*100:.2f}%")
    print(f"Rule-Based Risk Score    : {rule_score:.1f}/100")
    print(f"Risk Category            : {risk_cat}")
    print(f"Ground Truth Label       : {'FAKE ACCOUNT' if row.get('fraud') else 'NORMAL'} ({row.get('ftype', 'normal')})")
    
    print("\nSuspicion Indicators:")
    if reasons:
        for idx, reason in enumerate(reasons, 1):
            print(f" {idx}. {reason}")
    else:
        print("  None (No major suspicious behavior detected)")
    print("="*55)

if __name__ == "__main__":
    main()

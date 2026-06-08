import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

import warnings
warnings.filterwarnings('ignore')

sns.set_theme(style="whitegrid")

# Directories configuration
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
ABT_DIR = os.path.join(BASE_DIR, 'data', 'abt')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')
IMG_DIR = os.path.join(BASE_DIR, 'docs', 'images')
os.makedirs(IMG_DIR, exist_ok=True)

print("Starting EDA Image Generation...")

# Load datasets
try:
    df_txns = pd.read_csv(os.path.join(RAW_DIR, 'transactions.csv'))
    df_abt = pd.read_csv(os.path.join(ABT_DIR, 'fake_account_abt.csv'))
    
    # Merge graph features for EDA if exists
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
        df_abt = df_abt.merge(df_graph, on='uid', how='left')
        df_abt.fillna(0, inplace=True)
        
    print("Datasets loaded successfully.")
except Exception as e:
    print(f"Error loading datasets: {e}")
    exit(1)

# 1. Fake vs Normal Distribution
plt.figure(figsize=(6, 4))
sns.countplot(x='fraud', data=df_abt, palette='viridis')
plt.title('Fake vs Normal Account Distribution')
plt.xlabel('Is Fake Account')
plt.ylabel('Count')
plt.savefig(os.path.join(IMG_DIR, 'fake_vs_normal.png'), bbox_inches='tight')
plt.close()

# 2. Fraud Type Distribution
plt.figure(figsize=(10, 5))
fraud_counts = df_abt[df_abt['fraud'] == True]['ftype'].value_counts()
sns.barplot(x=fraud_counts.values, y=fraud_counts.index, palette='magma')
plt.title('Distribution of Fraud Types')
plt.xlabel('Count')
plt.ylabel('Fraud Type')
plt.savefig(os.path.join(IMG_DIR, 'fraud_types.png'), bbox_inches='tight')
plt.close()

# 3. Account Age Distribution (Boxplot)
plt.figure(figsize=(8, 4))
if 'account_age_days' in df_abt.columns:
    sns.boxplot(x='fraud', y='account_age_days', data=df_abt, palette='Set2')
    plt.title('Account Age in Days: Normal vs Fake')
    plt.xlabel('Is Fake Account')
    plt.ylabel('Account Age (Days)')
    plt.savefig(os.path.join(IMG_DIR, 'account_age_boxplot.png'), bbox_inches='tight')
plt.close()

# 4. Accounts per Device, Address, and Payment (Histogram)
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

if 'max_acc_dev' in df_abt.columns:
    sns.histplot(ax=axes[0], data=df_abt, x='max_acc_dev', hue='fraud', multiple='stack', bins=10, palette='coolwarm')
    axes[0].set_title('Max Accounts per Device')

if 'max_acc_addr' in df_abt.columns:
    sns.histplot(ax=axes[1], data=df_abt, x='max_acc_addr', hue='fraud', multiple='stack', bins=10, palette='coolwarm')
    axes[1].set_title('Max Accounts per Address Group')

if 'max_acc_pay' in df_abt.columns:
    sns.histplot(ax=axes[2], data=df_abt, x='max_acc_pay', hue='fraud', multiple='stack', bins=10, palette='coolwarm')
    axes[2].set_title('Max Accounts per Payment Token')

plt.savefig(os.path.join(IMG_DIR, 'entity_sharing_histograms.png'), bbox_inches='tight')
plt.close()

# 5. Transactions by Month
df_txns['transaction_date'] = pd.to_datetime(df_txns['transaction_date'])
df_txns['month'] = df_txns['transaction_date'].dt.to_period('M')
monthly_counts = df_txns.groupby('month')['transaction_id'].count()

plt.figure(figsize=(10, 4))
monthly_counts.plot(kind='line', marker='o', color='purple', linewidth=2)
plt.title('Monthly Transaction Volume')
plt.xlabel('Month')
plt.ylabel('Transaction Count')
plt.savefig(os.path.join(IMG_DIR, 'monthly_transactions.png'), bbox_inches='tight')
plt.close()

# 6. Correlation Heatmap
numeric_cols = [
    'max_acc_dev', 'max_acc_addr', 'max_acc_pay', 'max_acc_ip',
    'login_v24h', 'email_len', 'email_num_ratio', 'email_rand', 'phone_score',
    'degree', 'cluster', 'comp_size', 'shared_ent', 'shared_ip_count', 'fraud'
]

numeric_cols = [c for c in numeric_cols if c in df_abt.columns]

if len(numeric_cols) > 1:
    corr_matrix = df_abt[numeric_cols].corr()
    plt.figure(figsize=(16, 12))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap='coolwarm', cbar=True, square=True)
    plt.title('Correlation Matrix of Engineered Features and Target Label')
    plt.savefig(os.path.join(IMG_DIR, 'correlation_heatmap.png'), bbox_inches='tight')
    plt.close()

print("EDA Images Generated Successfully in 'docs/images/'.")

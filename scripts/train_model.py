import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from collections import Counter

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, 
    confusion_matrix, roc_curve, precision_recall_curve, auc
)

# Directories configuration
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ABT_PATH = os.path.join(BASE_DIR, 'data', 'abt', 'fake_account_abt.csv')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
IMG_DIR = os.path.join(BASE_DIR, 'docs', 'images')
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

print("Starting Advanced Model Training & GridSearchCV Tuning...")

# 1. Load ABT
if not os.path.exists(ABT_PATH):
    print(f"[ERROR] ABT file not found at: {ABT_PATH}. Please run scripts/build_abt.py first.")
    sys.exit(1)
    
df_abt = pd.read_csv(ABT_PATH)

# --- 1.5. Merge Graph Features ---
graph_path = os.path.join(BASE_DIR, 'data', 'processed', 'user_graph_features.csv')
if os.path.exists(graph_path):
    df_graph = pd.read_csv(graph_path)
    # Sesuaikan tata nama dengan skema ABT terbaru
    df_graph = df_graph.rename(columns={
        'user_id': 'uid',
        'graph_degree': 'degree',
        'graph_cluster_size': 'cluster',
        'connected_component_size': 'comp_size',
        'shared_entity_count': 'shared_ent'
    })
    df_abt = df_abt.merge(df_graph, on='uid', how='left')
    # Isi nilai kosong untuk antisipasi
    df_abt.fillna(0, inplace=True)
    print(f"Berhasil menggabungkan Fitur Graf. Total kolom sekarang: {df_abt.shape[1]}")
else:
    print(f"[WARNING] Fitur graf tidak ditemukan di {graph_path}. Melewati penggabungan.")

print(f"Loaded ABT containing {df_abt.shape[0]} rows and {df_abt.shape[1]} columns.")

# 2. Separate Features and Label
drop_cols = ['uid', 'fraud', 'ftype', 'risk_cat', 'risk_score']
X = df_abt.drop(columns=drop_cols, errors='ignore')
y = df_abt['fraud'].astype(int)
feature_names = X.columns.tolist()

# 3. Train-Test Split (70-30 split, stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42, stratify=y
)
print(f"Split completed: Train size = {X_train.shape[0]}, Test size = {X_test.shape[0]}")

# =================================================================
# LEAKAGE FIX: Recompute cross-user aggregation & graph features
# using ONLY training user records so test-set users cannot
# inflate entity-sharing counts that the model learns from.
# =================================================================
print("\n[LEAKAGE FIX] Recomputing cross-user features from training data only...")
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')

# --- Load raw relational tables ---
df_ud_raw   = pd.read_csv(os.path.join(RAW_DIR, 'user_devices.csv'))
df_ua_raw   = pd.read_csv(os.path.join(RAW_DIR, 'user_addresses.csv'))
df_up_raw   = pd.read_csv(os.path.join(RAW_DIR, 'user_payments.csv'))
df_ls_raw   = pd.read_csv(os.path.join(RAW_DIR, 'login_sessions.csv'))

df_ua_full = df_ua_raw.copy()

# --- Identify user IDs in each split (df_abt index aligns with X) ---
train_user_ids = set(df_abt.loc[X_train.index, 'uid'])
test_user_ids  = set(df_abt.loc[X_test.index,  'uid'])

# --- Filter raw tables to training users only ---
tr_logins = df_ls_raw[df_ls_raw['user_id'].isin(train_user_ids)]
tr_dev    = df_ud_raw[df_ud_raw['user_id'].isin(train_user_ids)]
tr_addr   = df_ua_full[df_ua_full['user_id'].isin(train_user_ids)]
tr_pay    = df_up_raw[df_up_raw['user_id'].isin(train_user_ids)]

# --- Build train-only entity-count maps (entity -> # training users) ---
train_ip_count   = tr_logins.groupby('ip_address')['user_id'].nunique()
train_dev_count  = tr_dev.groupby('device_id')['user_id'].nunique()
train_addr_count = tr_addr.groupby('address_id')['user_id'].nunique()
train_pay_count  = tr_pay.groupby('payment_id')['user_id'].nunique()

def compute_max_per_user(all_records, entity_col, user_col, entity_count_map):
    """Apply a train-only entity count map to all users (train + test).
    Entities unseen in training get count = 1 (only the user themselves)."""
    df = all_records[[user_col, entity_col]].copy()
    df['cnt'] = df[entity_col].map(entity_count_map).fillna(1).astype(int)
    return df.groupby(user_col)['cnt'].max().to_dict()

ip_max_map   = compute_max_per_user(df_ls_raw,  'ip_address',              'user_id', train_ip_count)
dev_max_map  = compute_max_per_user(df_ud_raw,  'device_id',               'user_id', train_dev_count)
addr_max_map = compute_max_per_user(df_ua_full, 'address_id', 'user_id', train_addr_count)
pay_max_map  = compute_max_per_user(df_up_raw,  'payment_id',              'user_id', train_pay_count)

# ---- Rebuild entity graph using ONLY training users ----------------
print("[LEAKAGE FIX] Rebuilding entity graph from training users only...")
G_train = nx.Graph()
G_train.add_nodes_from(train_user_ids)
shared_counts_train = Counter()

def add_shared_edges(G, sc, records_df, entity_col, user_col):
    """Add edges between users sharing the same entity; accumulate shared counts.

    Safety cap: groups larger than 50 users are skipped to avoid O(n^2) edge
    explosion from very popular shared entities (e.g., a datacenter IP used by
    hundreds of bots). Large clusters are still captured via accounts_per_ip_max.
    """
    _MAX_GROUP = 50
    # Use DataFrameGroupBy (avoids deprecated SeriesGroupBy tuple unpacking)
    for _entity_val, group_df in records_df.groupby(entity_col):
        users = group_df[user_col].tolist()
        if len(users) < 2 or len(users) > _MAX_GROUP:
            continue
        for i in range(len(users)):
            for j in range(i + 1, len(users)):
                G.add_edge(users[i], users[j])
                sc[(users[i], users[j])] += 1
                sc[(users[j], users[i])] += 1

add_shared_edges(G_train, shared_counts_train, tr_dev,  'device_id',               'user_id')
add_shared_edges(G_train, shared_counts_train, tr_addr, 'address_id', 'user_id')
add_shared_edges(G_train, shared_counts_train, tr_pay,  'payment_id',              'user_id')

# Component sizes in the training-only graph
comp_map_train = {
    node: len(comp)
    for comp in nx.connected_components(G_train)
    for node in comp
}

# Graph features for TRAINING users
graph_feats = {}
for u_id in train_user_ids:
    nbrs = list(G_train.neighbors(u_id))
    graph_feats[u_id] = {
        'degree':                   G_train.degree(u_id),
        'cluster':                  len(nx.ego_graph(G_train, u_id)),
        'comp_size':                comp_map_train.get(u_id, 1),
        'shared_ent':               sum(shared_counts_train[(u_id, n)] for n in nbrs),
    }

# Graph features for TEST users (computed relative to the training graph only)
# Precompute: entity -> list of training users that use it
dev_to_tr  = tr_dev.groupby('device_id')['user_id'].apply(list).to_dict()
addr_to_tr = tr_addr.groupby('address_id')['user_id'].apply(list).to_dict()
pay_to_tr  = tr_pay.groupby('payment_id')['user_id'].apply(list).to_dict()

te_dev  = df_ud_raw[df_ud_raw['user_id'].isin(test_user_ids)]
te_addr = df_ua_full[df_ua_full['user_id'].isin(test_user_ids)]
te_pay  = df_up_raw[df_up_raw['user_id'].isin(test_user_ids)]

te_user_devs  = te_dev.groupby('user_id')['device_id'].apply(list).to_dict()
te_user_addrs = te_addr.groupby('user_id')['address_id'].apply(list).to_dict()
te_user_pays  = te_pay.groupby('user_id')['payment_id'].apply(list).to_dict()

print("[LEAKAGE FIX] Computing test-user graph features relative to training graph...")
for u_id in test_user_ids:
    tr_nbrs = set()
    shared  = Counter()
    for dev in te_user_devs.get(u_id, []):
        for cu in dev_to_tr.get(dev, []):
            tr_nbrs.add(cu); shared[cu] += 1
    for grp in te_user_addrs.get(u_id, []):
        for cu in addr_to_tr.get(grp, []):
            tr_nbrs.add(cu); shared[cu] += 1
    for pay in te_user_pays.get(u_id, []):
        for cu in pay_to_tr.get(pay, []):
            tr_nbrs.add(cu); shared[cu] += 1
    graph_feats[u_id] = {
        'degree':                   len(tr_nbrs),
        'cluster':                  len(tr_nbrs) + 1,
        'comp_size':                max((comp_map_train.get(n, 1) for n in tr_nbrs), default=1),
        'shared_ent':               sum(shared.values()),
    }

# ---- Apply all corrections to X_train and X_test ------------------
leaky_scalar_maps = {
    'max_acc_ip':      ip_max_map,
    'max_acc_dev':     dev_max_map,
    'max_acc_addr':    addr_max_map,
    'max_acc_pay':     pay_max_map,
}
graph_feat_names = ['degree', 'cluster', 'comp_size', 'shared_ent']

for split_X in (X_train, X_test):
    uid_series = df_abt.loc[split_X.index, 'uid']
    # Scalar cross-user features
    for feat, mapping in leaky_scalar_maps.items():
        if feat in split_X.columns:
            split_X[feat] = uid_series.map(mapping).fillna(1).astype(int).values
    # Graph features
    for gfeat in graph_feat_names:
        if gfeat in split_X.columns:
            split_X[gfeat] = uid_series.map(
                lambda uid, gf=gfeat: graph_feats.get(uid, {}).get(gf, 0)
            ).values

print("[LEAKAGE FIX] Complete. Corrected 8 features:")
print("  Scalar : max_acc_ip, max_acc_dev, max_acc_addr, max_acc_pay")
print("  Graph  : degree, cluster, comp_size, shared_ent")

# 4. Define Base Models
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Random Forest': RandomForestClassifier(random_state=42, n_jobs=1)
}

# Try importing xgboost, fallback to GradientBoostingClassifier
try:
    import xgboost as xgb
    models['XGBoost'] = xgb.XGBClassifier(random_state=42, n_jobs=1, eval_metric='logloss')
    print("XGBoost loaded successfully.")
except ImportError:
    print("[WARNING] xgboost failed to load. Falling back to scikit-learn GradientBoostingClassifier.")
    models['XGBoost'] = GradientBoostingClassifier(random_state=42)

# 5. Define GridSearchCV Hyperparameter Grids
# XGBoost grid switches based on whether the real xgboost or the sklearn
# GradientBoostingClassifier fallback is in use (they have different param names).
_xgb_is_real = not isinstance(models['XGBoost'], GradientBoostingClassifier)
if _xgb_is_real:
    _xgb_grid = {
        'classifier__learning_rate': [0.01, 0.05],
        'classifier__max_depth': [2, 3],
        'classifier__subsample': [0.7, 0.8],
        'classifier__min_child_weight': [5, 10]
    }
else:
    # GradientBoostingClassifier-compatible params
    _xgb_grid = {
        'classifier__learning_rate': [0.01, 0.05],
        'classifier__max_depth': [2, 3],
        'classifier__subsample': [0.7, 0.8],
        'classifier__min_samples_leaf': [5, 10]
    }

param_grids = {
    'Logistic Regression': {
        'classifier__C': [0.001, 0.01, 0.1, 1.0],
        'classifier__penalty': ['l2']
    },
    'Random Forest': {
        'classifier__n_estimators': [50, 100],
        'classifier__max_depth': [3, 5],
        'classifier__min_samples_leaf': [5, 10]
    },
    'XGBoost': _xgb_grid
}

# 6. Setup cross-validation strategy
cv_strategy = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

model_metrics = {}
best_estimators = {}

# Prep diagnostic plotting lists
plt.figure(figsize=(10, 8))
fig_roc, ax_roc = plt.subplots(figsize=(10, 8))
fig_pr, ax_pr = plt.subplots(figsize=(10, 8))

for model_name, clf in models.items():
    print(f"\nTuning hyperparameters for {model_name}...")
    
    # Create training pipeline
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', clf)
    ])
    
    # Run Grid Search CV
    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grids[model_name],
        cv=cv_strategy,
        scoring='f1',
        n_jobs=1
    )
    
    grid_search.fit(X_train, y_train)
    best_pipeline = grid_search.best_estimator_
    best_estimators[model_name] = best_pipeline
    
    print(f"  Best Params: {grid_search.best_params_}")
    print(f"  Best CV F1-Score: {grid_search.best_score_:.4f}")
    
    # Evaluate on the Test Set
    y_pred = best_pipeline.predict(X_test)
    y_prob = best_pipeline.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    auc_val = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    # Save metrics
    model_metrics[model_name] = {
        'best_params': grid_search.best_params_,
        'best_cv_f1': float(grid_search.best_score_),
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1_score': float(f1),
        'roc_auc': float(auc_val),
        'confusion_matrix': cm
    }
    
    print(f"  Test Metrics -> Acc: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} | ROC-AUC: {auc_val:.4f}")
    
    # Plot ROC curve for this model
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    roc_auc = auc(fpr, tpr)
    ax_roc.plot(fpr, tpr, label=f'{model_name} (AUC = {roc_auc:.4f})')
    
    # Plot PR curve for this model
    precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = auc(recall_curve, precision_curve)
    ax_pr.plot(recall_curve, precision_curve, label=f'{model_name} (AUC = {pr_auc:.4f})')

# Finalize and Save Diagnostic Plots
# ROC Plot
ax_roc.plot([0, 1], [0, 1], 'k--', label='Random Guess')
ax_roc.set_title('ROC Curves - Model Comparison')
ax_roc.set_xlabel('False Positive Rate')
ax_roc.set_ylabel('True Positive Rate')
ax_roc.legend(loc='lower right')
fig_roc.savefig(os.path.join(IMG_DIR, 'roc_curves.png'), bbox_inches='tight')
plt.close(fig_roc)

# PR Plot
ax_pr.set_title('Precision-Recall Curves - Model Comparison')
ax_pr.set_xlabel('Recall')
ax_pr.set_ylabel('Precision')
ax_pr.legend(loc='lower left')
fig_pr.savefig(os.path.join(IMG_DIR, 'pr_curves.png'), bbox_inches='tight')
plt.close(fig_pr)

# 7. Plot Confusion Matrices Side-by-Side
fig_cm, axes_cm = plt.subplots(1, 3, figsize=(18, 5))
for idx, (model_name, metrics) in enumerate(model_metrics.items()):
    cm_arr = np.array(metrics['confusion_matrix'])
    sns.heatmap(
        cm_arr, annot=True, fmt='d', cmap='Blues', cbar=False, ax=axes_cm[idx],
        xticklabels=['Legitimate', 'Fake'], yticklabels=['Legitimate', 'Fake']
    )
    axes_cm[idx].set_title(f'{model_name} Confusion Matrix')
    axes_cm[idx].set_xlabel('Predicted Label')
    axes_cm[idx].set_ylabel('True Label')
fig_cm.savefig(os.path.join(IMG_DIR, 'confusion_matrices.png'), bbox_inches='tight')
plt.close(fig_cm)

# 8. Save Metrics JSON
metrics_output_path = os.path.join(MODELS_DIR, 'model_metrics.json')
with open(metrics_output_path, 'w') as f:
    json.dump(model_metrics, f, indent=4)
print(f"\nSaved all metrics to: {metrics_output_path}")

# 9. Select Champion Model based on F1-Score on Test Set
champion_name = max(model_metrics, key=lambda k: model_metrics[k]['f1_score'])
champion_pipeline = best_estimators[champion_name]
print(f"\n[CHAMPION] Champion Model Selected: {champion_name} (F1-Score: {model_metrics[champion_name]['f1_score']:.4f})")

# 10. Save Champion Model & Feature Columns List
model_output_path = os.path.join(MODELS_DIR, 'fake_account_model.pkl')
joblib.dump(champion_pipeline, model_output_path)
print(f"Saved champion pipeline to: {model_output_path}")

features_output_path = os.path.join(MODELS_DIR, 'feature_columns.json')
with open(features_output_path, 'w') as f:
    json.dump(feature_names, f, indent=4)
print(f"Saved feature names list to: {features_output_path}")

# 11. Plot Feature Importances / Coefficients for Champion
champion_clf = champion_pipeline.named_steps['classifier']
importances = None
if hasattr(champion_clf, 'feature_importances_'):
    importances = champion_clf.feature_importances_
elif hasattr(champion_clf, 'coef_'):
    importances = np.abs(champion_clf.coef_[0])

if importances is not None:
    feat_imp_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importances
    }).sort_values(by='importance', ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x='importance', y='feature', data=feat_imp_df.head(15), palette='viridis')
    plt.title(f'Top 15 Feature Importances ({champion_name})')
    plt.xlabel('Importance/Weight')
    plt.ylabel('Feature')
    plt.savefig(os.path.join(IMG_DIR, 'feature_importance.png'), bbox_inches='tight')
    plt.close()
    print("Saved feature importance chart to: docs/images/feature_importance.png")
    
    print("\nTop 5 Predictive Features:")
    for idx, row in feat_imp_df.head(5).iterrows():
        print(f"  - {row['feature']}: {row['importance']:.4f}")

print("\n--- Model training & diagnostics completed! ---")

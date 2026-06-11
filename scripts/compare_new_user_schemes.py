"""Purpose: Compare registration-only training schemes for the new-user fraud model.
Used by: Manual model selection for the new-user inference branch.
Main dependencies: fake_account_abt.csv, users.csv, scikit-learn, joblib.
Public/main functions: train_and_compare.
Side effects: Writes new-user experiment metrics to models/new_user_scheme_comparison.json.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

BASE_DIR = r'D:\magang\fraud detection'
ABT_PATH = os.path.join(BASE_DIR, 'data', 'abt', 'fake_account_abt.csv')
USERS_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'users.csv')
OUT_PATH = os.path.join(BASE_DIR, 'models', 'new_user_scheme_comparison.json')


def calc_entropy(text):
    if not text or not isinstance(text, str):
        return 0.0
    from collections import Counter
    import math
    counts = Counter(text)
    n = len(text)
    return sum(-(c / n) * math.log2(c / n) for c in counts.values())


def calc_phone_pattern_score(phone):
    if not phone or not isinstance(phone, str):
        return 0.0
    digits = [c for c in phone if c.isdigit()]
    if not digits:
        return 0.0
    unique_ratio = len(set(digits)) / len(digits)
    consecutive = sum(1 for i in range(len(digits)-1) if digits[i] == digits[i+1])
    return (1.0 - unique_ratio) * 0.7 + (consecutive / len(digits)) * 0.3


def build_features(df):
    out = pd.DataFrame(index=df.index)
    email = df['email'].fillna('').astype(str)
    phone = df['phone_number'].fillna('').astype(str)
    full_name = df['full_name'].fillna('').astype(str)
    username = email.str.split('@').str[0].fillna('')
    domain = email.str.split('@').str[1].fillna('')

    out['email_len'] = email.str.len()
    out['email_num_ratio'] = username.apply(lambda x: sum(ch.isdigit() for ch in x) / len(x) if x else 0.0)
    out['email_rand'] = username.apply(calc_entropy)
    out['disp_email'] = domain.str.lower().isin({'mailinator.com', 'yopmail.com', 'tempmail.com'}).astype(int)
    out['phone_score'] = phone.apply(calc_phone_pattern_score)
    out['full_name_len'] = full_name.str.len()
    out['is_email_verified'] = df['is_email_verified'].astype(int)
    out['is_phone_verified'] = df['is_phone_verified'].astype(int)
    out['age_years'] = (pd.to_datetime(df['registration_date']) - pd.to_datetime(df['date_of_birth'])).dt.days / 365.25
    out['registration_hour'] = pd.to_datetime(df['registration_date']).dt.hour
    out['registration_channel'] = df['registration_channel'].fillna('unknown')
    out['city'] = df['city'].fillna('unknown')
    out['province'] = df['province'].fillna('unknown')
    return out


def evaluate(name, X, y, num_cols, cat_cols):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

    pre = ColumnTransformer([
        ('num', Pipeline([('imp', SimpleImputer(strategy='median')), ('scaler', StandardScaler())]), num_cols),
        ('cat', Pipeline([('imp', SimpleImputer(strategy='most_frequent')), ('ohe', OneHotEncoder(handle_unknown='ignore'))]), cat_cols),
    ])

    models = {
        'lr': LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42),
        'rf': RandomForestClassifier(n_estimators=200, max_depth=5, min_samples_leaf=10, class_weight='balanced', random_state=42, n_jobs=1),
    }

    results = {}
    for mname, clf in models.items():
        pipe = Pipeline([('pre', pre), ('clf', clf)])
        pipe.fit(X_train, y_train)
        prob = pipe.predict_proba(X_test)[:, 1]
        pred = (prob >= 0.45).astype(int)
        results[mname] = {
            'accuracy': float(accuracy_score(y_test, pred)),
            'precision': float(precision_score(y_test, pred, zero_division=0)),
            'recall': float(recall_score(y_test, pred, zero_division=0)),
            'f1': float(f1_score(y_test, pred, zero_division=0)),
            'roc_auc': float(roc_auc_score(y_test, prob)),
        }
    best = max(results.items(), key=lambda kv: kv[1]['f1'])
    return {
        'scheme': name,
        'best_model': best[0],
        'best_metrics': best[1],
        'all': results,
    }


def main():
    df_abt = pd.read_csv(ABT_PATH)
    df_users = pd.read_csv(USERS_PATH)
    df = df_abt[['uid', 'fraud']].merge(df_users, left_on='uid', right_on='user_id', how='left')
    y = df['fraud'].astype(int)

    reg = build_features(df)

    schemes = {
        '5_core': (reg[['email_len','email_num_ratio','email_rand','disp_email','phone_score']], [], ['email_len','email_num_ratio','email_rand','disp_email','phone_score']),
        'core_plus_checks': (reg[['email_len','email_num_ratio','email_rand','disp_email','phone_score','full_name_len','is_email_verified','is_phone_verified','age_years','registration_hour']], [], ['email_len','email_num_ratio','email_rand','disp_email','phone_score','full_name_len','is_email_verified','is_phone_verified','age_years','registration_hour']),
        'core_plus_checks_cat': (reg[['email_len','email_num_ratio','email_rand','disp_email','phone_score','full_name_len','is_email_verified','is_phone_verified','age_years','registration_hour','registration_channel','city','province']], ['registration_channel','city','province'], ['email_len','email_num_ratio','email_rand','disp_email','phone_score','full_name_len','is_email_verified','is_phone_verified','age_years','registration_hour']),
    }

    out = {'generated_at': datetime.utcnow().isoformat(), 'results': []}
    for name, (X, cat_cols, num_cols) in schemes.items():
        res = evaluate(name, X, y, num_cols, cat_cols)
        out['results'].append(res)
        print(name, res['best_model'], res['best_metrics'])

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print(f'Saved comparison -> {OUT_PATH}')


if __name__ == '__main__':
    main()

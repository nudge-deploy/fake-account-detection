"""
Purpose: Train a dedicated new-user fraud model from registration-only features.
Used by: Manual training workflow and backend new-user inference artifact loading.
Main dependencies: fake_account_abt.csv, scikit-learn, joblib, models/new_customer/feature_columns.json.
Public/main functions: train, evaluate_model, save_artifacts.
Side effects: Writes new-user model and metric artifacts to the models directory.
"""

from __future__ import annotations

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ABT_PATH = os.path.join(BASE_DIR, "data", "abt", "fake_account_abt.csv")
MODELS_DIR = os.path.join(BASE_DIR, "models", "new_customer")
FEATURE_COLUMNS_PATH = os.path.join(MODELS_DIR, "feature_columns.json")
MODEL_PATH = os.path.join(MODELS_DIR, "model.pkl")
METRICS_PATH = os.path.join(MODELS_DIR, "metrics.json")
TRAIN_DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "new_user_training_data.csv")

FEATURES = [
    "email_len",
    "email_num_ratio",
    "email_rand",
    "disp_email",
    "phone_score",
    "full_name_len",
    "is_email_verified",
    "is_phone_verified",
    "age_years",
    "registration_hour",
]


def best_f1_threshold(y_true, y_prob):
    thresholds = np.linspace(0.1, 0.9, 17)
    best_threshold = 0.5
    best_f1 = -1.0
    for threshold in thresholds:
        y_pred = (y_prob >= threshold).astype(int)
        score = f1_score(y_true, y_pred, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_threshold = float(threshold)
    return best_threshold, best_f1


def train():
    source_path = TRAIN_DATA_PATH if os.path.exists(TRAIN_DATA_PATH) else ABT_PATH
    if not os.path.exists(source_path):
        print(f"[ERROR] Training file not found at {source_path}")
        sys.exit(1)

    df = pd.read_csv(source_path)
    missing = [c for c in FEATURES if c not in df.columns]
    if missing:
        print(f"[ERROR] Missing required new-user features: {missing}")
        sys.exit(1)
    if "fraud" not in df.columns:
        print("[ERROR] Missing fraud label in ABT.")
        sys.exit(1)

    X = df[FEATURES].copy().fillna(0)
    y = df["fraud"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=2000, random_state=42, class_weight=None),
    }

    param_grids = {
        "Logistic Regression": {
            "classifier__C": [0.03, 0.05, 0.1, 0.2],
            "classifier__penalty": ["l2"],
        },
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    results = {}
    best_name = None
    best_f1 = -1.0
    best_estimator = None

    for name, clf in models.items():
        pipe = Pipeline([("scaler", StandardScaler()), ("classifier", clf)])
        search = GridSearchCV(
            estimator=pipe,
            param_grid=param_grids[name],
            cv=cv,
            scoring="f1",
            n_jobs=1,
        )
        search.fit(X_train, y_train)
        estimator = search.best_estimator_
        y_pred = estimator.predict(X_test)
        y_prob = estimator.predict_proba(X_test)[:, 1]
        tuned_threshold, tuned_f1 = best_f1_threshold(y_test.to_numpy(), y_prob)
        tuned_pred = (y_prob >= tuned_threshold).astype(int)
        result = {
            "best_params": search.best_params_,
            "best_cv_f1": float(search.best_score_),
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, y_prob)),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "best_threshold": tuned_threshold,
            "best_threshold_f1": float(tuned_f1),
            "threshold_confusion_matrix": confusion_matrix(y_test, tuned_pred).tolist(),
        }
        results[name] = result
        print(f"{name}: f1={result['f1_score']:.4f}, auc={result['roc_auc']:.4f}")
        if result["f1_score"] > best_f1:
            best_f1 = result["f1_score"]
            best_name = name
            best_estimator = estimator

    os.makedirs(MODELS_DIR, exist_ok=True)
    with open(FEATURE_COLUMNS_PATH, "w", encoding="utf-8") as f:
        json.dump(FEATURES, f, indent=4)
    print(f"Training source: {source_path}")
    joblib.dump(best_estimator, MODEL_PATH)
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump({"best_model": best_name, "results": results}, f, indent=4)

    print(f"Saved best model: {best_name}")
    print(f"Model path: {MODEL_PATH}")
    print(f"Metrics path: {METRICS_PATH}")


if __name__ == "__main__":
    train()

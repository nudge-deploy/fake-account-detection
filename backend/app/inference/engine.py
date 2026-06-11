"""
Purpose: Run lifecycle fraud inference from staged feature rows for Alfagift.
Used by: ContinuousInferenceService and backend API lifecycle endpoints.
Main dependencies: separate new-user and existing-user model artifacts, feature columns schema, ABT, and fraud classification helpers.
Public/main functions: InferenceResult, ContinuousInferenceEngine.predict, predict_from_features, run_journey.
Side effects: Loads model and ABT artifacts from disk when not injected.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional

import joblib
import pandas as pd

from app.utils.config import (
    BASE_DIR,
    ABT_PATH,
    EXISTING_USER_MODEL_PATH,
    FEATURE_COLUMNS_PATH,
    NEW_USER_FEATURE_COLUMNS_PATH,
    NEW_USER_MODEL_PATH,
    MODEL_PATH,
)
from .fraud_classifier import FRAUD_TYPE_LABELS, classify_fraud_types
from .reasons import generate_reasons
from .scoring import categorize_risk, compute_rule_score
from .stages import (
    CONFIDENCE_NOTES,
    STAGE_LABELS_ID,
    CustomerType,
    LifecycleStage,
    features_available_at_stage,
    features_available_for_customer,
)


@dataclass
class InferenceResult:
    uid: str
    stage: str
    stage_label: str
    customer_type: str
    ml_prediction: int
    ml_probability: float
    rule_score: float
    risk_category: str
    is_suspicious: bool
    is_fraud: bool
    primary_fraud_type: str
    primary_fraud_label: str
    suspected_fraud_types: list[dict[str, Any]] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    features_available: int = 0
    features_total: int = 0
    confidence_note: str = ""
    ground_truth_fraud: Optional[bool] = None
    ground_truth_ftype: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "uid": self.uid,
            "stage": self.stage,
            "stage_label": self.stage_label,
            "customer_type": self.customer_type,
            "model_prediction": self.ml_prediction,
            "model_probability": round(self.ml_probability, 4),
            "rule_based_score": round(self.rule_score, 1),
            "risk_category": self.risk_category,
            "is_suspicious": self.is_suspicious,
            "is_fraud": self.is_fraud,
            "primary_fraud_type": self.primary_fraud_type,
            "primary_fraud_label": self.primary_fraud_label,
            "suspected_fraud_types": self.suspected_fraud_types,
            "reasons": self.reasons,
            "features_available": self.features_available,
            "features_total": self.features_total,
            "confidence_note": self.confidence_note,
            "ground_truth_fraud": self.ground_truth_fraud,
            "ground_truth_ftype": self.ground_truth_ftype,
        }


class ContinuousInferenceEngine:
    def __init__(
        self,
        new_user_model=None,
        existing_user_model=None,
        feature_columns: list[str] | None = None,
        new_user_feature_columns: list[str] | None = None,
        df_abt: pd.DataFrame | None = None,
    ):
        self.new_user_model = new_user_model
        self.existing_user_model = existing_user_model
        self.feature_columns = feature_columns or []
        self.new_user_feature_columns = new_user_feature_columns or []
        self.df_abt = df_abt

        self.new_user_model = self._load_model(
            self.new_user_model,
            NEW_USER_MODEL_PATH,
            fallback_path=MODEL_PATH,
            label="new user",
        )
        self.existing_user_model = self._load_model(
            self.existing_user_model,
            EXISTING_USER_MODEL_PATH,
            fallback_path=MODEL_PATH,
            label="existing user",
        )
        if not self.feature_columns:
            with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
                self.feature_columns = json.load(f)
        if not self.new_user_feature_columns:
            if os.path.exists(NEW_USER_FEATURE_COLUMNS_PATH):
                with open(NEW_USER_FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
                    self.new_user_feature_columns = json.load(f)
            else:
                self.new_user_feature_columns = [
                    "email_len",
                    "email_num_ratio",
                    "email_rand",
                    "disp_email",
                    "phone_score",
                ]
        if self.df_abt is None and os.path.exists(ABT_PATH):
            self.df_abt = pd.read_csv(ABT_PATH)
            self.df_abt["uid"] = self.df_abt["uid"].astype(str)
            graph_path = os.path.join(BASE_DIR, "data", "processed", "user_graph_features.csv")
            if os.path.exists(graph_path) and "degree" not in self.df_abt.columns:
                df_graph = pd.read_csv(graph_path).rename(
                    columns={
                        "user_id": "uid",
                        "graph_degree": "degree",
                        "graph_cluster_size": "cluster",
                        "connected_component_size": "comp_size",
                        "shared_entity_count": "shared_ent",
                    }
                )
                df_graph["uid"] = df_graph["uid"].astype(str)
                self.df_abt = self.df_abt.merge(df_graph, on="uid", how="left")
                self.df_abt.fillna(0, inplace=True)

    def _model_feature_names(self, model) -> list[str]:
        names = getattr(model, "feature_names_in_", None)
        if names is None:
            return []
        return [str(name) for name in list(names)]

    def _load_model(self, model, preferred_path: str, fallback_path: str, label: str):
        if model is not None:
            return model

        for path in (preferred_path, fallback_path):
            if not path or not os.path.exists(path):
                continue
            try:
                return joblib.load(path)
            except Exception as exc:
                print(f"Warning: failed to load {label} model from {path}: {exc}")
        return None

    def _select_model(self, customer_type: CustomerType, stage: LifecycleStage):
        if customer_type == CustomerType.NEW and stage == LifecycleStage.REGISTRATION:
            return self.new_user_model
        return self.existing_user_model or self.new_user_model

    def _decision_threshold(self, customer_type: CustomerType, stage: LifecycleStage) -> float:
        if customer_type == CustomerType.NEW and stage == LifecycleStage.REGISTRATION:
            return 0.80
        if customer_type == CustomerType.NEW:
            return 0.65
        return 0.50

    def get_user_row(self, uid: str) -> dict[str, Any]:
        if self.df_abt is None:
            raise ValueError("ABT tidak tersedia.")
        matches = self.df_abt[self.df_abt["uid"] == str(uid)]
        if matches.empty:
            raise ValueError(f"User {uid} tidak ditemukan di ABT.")
        return matches.iloc[0].to_dict()

    def _mask_features_for_stage(
        self,
        full_row: dict[str, Any],
        stage: LifecycleStage,
        customer_type: CustomerType,
    ) -> dict[str, Any]:
        row = dict(full_row)
        available = (
            set(self.feature_columns)
            if customer_type == CustomerType.EXISTING
            else (
                set(self.new_user_feature_columns)
                if stage == LifecycleStage.REGISTRATION
                else features_available_for_customer(stage, customer_type)
            )
        )
        for col in self.feature_columns:
            if col not in available:
                row[col] = 0
        return row

    def _build_feature_vector(self, row: dict[str, Any], columns: list[str] | None = None) -> pd.DataFrame:
        columns = columns or self.feature_columns
        X_dict = {col: row.get(col, 0) for col in columns}
        X = pd.DataFrame([X_dict]).fillna(0)
        for col in X.columns:
            if X[col].dtype == bool:
                X[col] = X[col].astype(int)
        return X

    def _run_prediction_core(
        self,
        uid: str,
        stage: LifecycleStage,
        customer_type: CustomerType,
        full_row: dict[str, Any],
        ground_truth_row: dict[str, Any] | None = None,
    ) -> InferenceResult:
        staged_row = self._mask_features_for_stage(full_row, stage, customer_type)
        available_set = (
            set(self.feature_columns)
            if customer_type == CustomerType.EXISTING
            else (
                set(self.new_user_feature_columns)
                if stage == LifecycleStage.REGISTRATION
                else features_available_for_customer(stage, customer_type)
            )
        )

        model = self._select_model(customer_type, stage)
        selected_columns = self._model_feature_names(model)
        if not selected_columns:
            selected_columns = (
                self.new_user_feature_columns
                if customer_type == CustomerType.NEW and stage == LifecycleStage.REGISTRATION
                else self.feature_columns
            )

        X = self._build_feature_vector(staged_row, selected_columns)
        if model is not None:
            prob = float(model.predict_proba(X)[:, 1][0])
            pred = int(model.predict(X)[0])
        else:
            prob = 0.0
            pred = 0

        rule_score = compute_rule_score(staged_row, available_set)
        risk_cat = categorize_risk(rule_score)
        decision_threshold = self._decision_threshold(customer_type, stage)
        is_suspicious = (prob >= decision_threshold) or (rule_score >= 50.0)
        is_fraud = pred == 1 or is_suspicious

        staged_row["risk_score"] = rule_score
        reasons = generate_reasons(staged_row, stage)
        primary_type, ranked = classify_fraud_types(staged_row, is_suspicious)

        if not is_suspicious and primary_type == "unknown_fraud":
            primary_type = "normal"

        primary_label = FRAUD_TYPE_LABELS.get(primary_type, "Tidak diklasifikasikan")
        suspected = [{"type": t, "label": label, "score": round(score, 2)} for t, label, score in ranked]

        gt_source = ground_truth_row or full_row
        gt_fraud = gt_source.get("fraud")
        gt_fraud = None if pd.isna(gt_fraud) else bool(gt_fraud)
        gt_ftype = gt_source.get("ftype")
        gt_ftype = None if pd.isna(gt_ftype) or gt_ftype == "" else str(gt_ftype)

        return InferenceResult(
            uid=str(uid),
            stage=stage.value,
            stage_label=STAGE_LABELS_ID[stage],
            customer_type=customer_type.value,
            ml_prediction=pred,
            ml_probability=prob,
            rule_score=rule_score,
            risk_category=risk_cat,
            is_suspicious=is_suspicious,
            is_fraud=is_fraud,
            primary_fraud_type=primary_type,
            primary_fraud_label=primary_label,
            suspected_fraud_types=suspected,
            reasons=reasons,
            features_available=len(available_set),
            features_total=len(selected_columns),
            confidence_note=CONFIDENCE_NOTES[stage],
            ground_truth_fraud=gt_fraud,
            ground_truth_ftype=gt_ftype,
        )

    def predict(
        self,
        uid: str,
        stage: LifecycleStage,
        customer_type: CustomerType = CustomerType.NEW,
        full_row: dict[str, Any] | None = None,
    ) -> InferenceResult:
        if full_row is None:
            full_row = self.get_user_row(uid)
        return self._run_prediction_core(uid, stage, customer_type, full_row)

    def predict_from_features(
        self,
        uid: str,
        stage: LifecycleStage,
        customer_type: CustomerType,
        feature_row: dict[str, Any],
        ground_truth_row: dict[str, Any] | None = None,
    ) -> InferenceResult:
        return self._run_prediction_core(
            uid, stage, customer_type, feature_row, ground_truth_row
        )

    def run_journey(
        self,
        uid: str,
        customer_type: CustomerType = CustomerType.NEW,
        up_to_stage: LifecycleStage | None = None,
        full_row: dict[str, Any] | None = None,
    ) -> list[InferenceResult]:
        if full_row is None:
            full_row = self.get_user_row(uid)
        results: list[InferenceResult] = []
        for stage in LifecycleStage.ordered():
            results.append(self.predict(uid, stage, customer_type, full_row))
            if up_to_stage and stage == up_to_stage:
                break
        return results

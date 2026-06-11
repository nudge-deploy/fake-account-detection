"""
Purpose: Orchestrate lifecycle inference requests and route them to stage-aware model execution.
Used by: API prediction routes and frontend inference endpoints.
Main dependencies: feature builder, lifecycle engine, and model service metadata.
Public/main functions: predict_lifecycle, predict_journey.
Side effects: Builds staged feature rows and loads model artifacts through the engine.
"""

from typing import Any, Optional

from app.inference.engine import ContinuousInferenceEngine, InferenceResult
from app.inference.feature_builder import AlfagiftFeatureBuilder
from app.inference.stages import CustomerType, LifecycleStage
from app.services.model_service import ModelService


class ContinuousInferenceService:
    def __init__(self, model_service: ModelService):
        self.model_service = model_service
        df_abt = None
        if model_service.df_merged is not None:
            df_abt = model_service.df_merged.copy()

        self.engine = ContinuousInferenceEngine(
            feature_columns=model_service.feature_columns,
            df_abt=df_abt,
        )
        self.feature_builder = AlfagiftFeatureBuilder(model_service.feature_columns)

    def _ground_truth_row(self, uid: Optional[str]) -> Optional[dict[str, Any]]:
        if not uid or self.engine.df_abt is None:
            return None
        try:
            return self.engine.get_user_row(uid)
        except ValueError:
            return None

    def predict_lifecycle(
        self,
        stage: str,
        customer_type: str,
        payload: dict[str, Any],
        uid: Optional[str] = None,
    ) -> InferenceResult:
        stage_enum = LifecycleStage(stage)
        customer_enum = CustomerType(customer_type)
        gt_row = self._ground_truth_row(uid)

        feature_row, resolved_uid = self.feature_builder.build(
            stage_enum, customer_enum, payload, uid
        )

        return self.engine.predict_from_features(
            resolved_uid,
            stage_enum,
            customer_enum,
            feature_row,
            ground_truth_row=gt_row,
        )

    def predict_journey(
        self,
        customer_type: str,
        payload: dict[str, Any],
        uid: Optional[str] = None,
        up_to_stage: Optional[str] = None,
    ) -> list[InferenceResult]:
        customer_enum = CustomerType(customer_type)
        gt_row = self._ground_truth_row(uid)
        up_to = LifecycleStage(up_to_stage) if up_to_stage else None
        results: list[InferenceResult] = []

        for stage in LifecycleStage.ordered():
            feature_row, resolved_uid = self.feature_builder.build(
                stage, customer_enum, payload, uid
            )
            results.append(
                self.engine.predict_from_features(
                    resolved_uid,
                    stage,
                    customer_enum,
                    feature_row,
                    ground_truth_row=gt_row,
                )
            )
            if up_to and stage == up_to:
                break

        return results

"""
CLI inferensi berkelanjutan Alfagift — customer baru & lama.

Contoh:
  # Simulasi journey customer baru (registrasi → login → checkout → selesai)
  python scripts/run_inference.py --uid USR00421 --journey --customer-type new

  # Inferensi sekali di tahap login (customer lama)
  python scripts/run_inference.py --uid USR00421 --stage login --customer-type existing

  # Inferensi legacy (satu kali, semua fitur)
  python scripts/run_inference.py --uid USR00421 --legacy
"""

from __future__ import annotations

import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from app.inference.engine import ContinuousInferenceEngine, InferenceResult
from app.inference.stages import CustomerType, LifecycleStage


def _print_result(result: InferenceResult, verbose: bool = False) -> None:
    fraud_label = "FRAUD / MENCURIGAKAN" if result.is_fraud else "NORMAL"
    pred_label = "FAKE ACCOUNT (1)" if result.ml_prediction == 1 else "NORMAL (0)"

    print("\n" + "=" * 60)
    print(f" INFERENSI ALFAGIFT - USER: {result.uid}")
    print(f" Tahap: {result.stage_label}")
    print(f" Tipe pelanggan: {result.customer_type.upper()}")
    print("=" * 60)
    print(f"Status                   : {fraud_label}")
    print(f"ML Prediction            : {pred_label}")
    print(f"ML Fraud Probability     : {result.ml_probability * 100:.2f}%")
    print(f"Rule-Based Risk Score    : {result.rule_score:.1f}/100")
    print(f"Risk Category            : {result.risk_category}")
    print(f"Jenis Fraud (terduga)    : {result.primary_fraud_label}")

    ranked = [
        item
        for item in result.suspected_fraud_types
        if item["type"] not in ("normal", "unknown_fraud") and item["score"] > 0
    ]
    if ranked:
        print("\nKemungkinan jenis fraud (ranking):")
        for idx, item in enumerate(ranked[:5], 1):
            print(f"  {idx}. {item['label']} (skor sinyal: {item['score']})")

    print(f"\nFitur tersedia           : {result.features_available}/{result.features_total}")
    print(f"Catatan kepercayaan      : {result.confidence_note}")

    print("\nIndikator Mencurigakan:")
    if result.reasons:
        for idx, reason in enumerate(result.reasons, 1):
            print(f"  {idx}. {reason}")
    else:
        print("  Tidak ada indikator utama pada tahap ini.")

    if result.ground_truth_fraud is not None:
        gt = "FAKE ACCOUNT" if result.ground_truth_fraud else "NORMAL"
        print(f"\nGround Truth (evaluasi)  : {gt} ({result.ground_truth_ftype or 'normal'})")

    print("=" * 60)

    if verbose:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


def _run_legacy(engine: ContinuousInferenceEngine, uid: str | None) -> None:
    """Mode kompatibilitas: inferensi penuh seperti versi sebelumnya."""
    if uid:
        row = engine.get_user_row(uid)
        user_id = uid
    else:
        import pandas as pd

        df = engine.df_abt
        high_risk = df[df["risk_cat"] == "High"]
        if not high_risk.empty:
            row = high_risk.sample(1, random_state=42).iloc[0].to_dict()
        else:
            row = df.iloc[0].to_dict()
        user_id = row["uid"]
        print(f"Tidak ada uid. Menggunakan sampel user: {user_id}")

    result = engine.predict(
        str(user_id),
        LifecycleStage.TRANSACTION_COMPLETED,
        CustomerType.EXISTING,
        row,
    )
    _print_result(result)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inferensi fraud berkelanjutan Alfagift (customer baru & lama)."
    )
    parser.add_argument("--uid", type=str, help="User ID untuk diuji.")
    parser.add_argument(
        "--stage",
        type=str,
        choices=[s.value for s in LifecycleStage],
        default="registration",
        help="Tahap lifecycle (default: registration).",
    )
    parser.add_argument(
        "--customer-type",
        type=str,
        choices=[c.value for c in CustomerType],
        default="new",
        help="new = fitur bertahap; existing = seluruh historis tersedia.",
    )
    parser.add_argument(
        "--journey",
        action="store_true",
        help="Jalankan inferensi di semua tahap secara berurutan.",
    )
    parser.add_argument(
        "--up-to",
        type=str,
        choices=[s.value for s in LifecycleStage],
        help="Batasi journey sampai tahap tertentu.",
    )
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Mode lama: satu inferensi penuh (semua fitur).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output tambahan dalam format JSON.",
    )
    args = parser.parse_args()

    try:
        engine = ContinuousInferenceEngine()
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        sys.exit(1)

    if args.legacy:
        _run_legacy(engine, args.uid)
        return

    if not args.uid and not args.journey:
        print("Error: --uid wajib (kecuali --legacy tanpa uid untuk sampel acak).")
        sys.exit(1)

    customer_type = CustomerType(args.customer_type)
    up_to = LifecycleStage(args.up_to) if args.up_to else None

    if args.journey:
        uid = args.uid
        if not uid:
            import pandas as pd

            fraud_users = engine.df_abt[engine.df_abt["fraud"] == True]
            if not fraud_users.empty:
                uid = str(fraud_users.sample(1, random_state=42).iloc[0]["uid"])
            else:
                uid = str(engine.df_abt.iloc[0]["uid"])
            print(f"Journey demo — user: {uid}")

        print(f"\n>>> MEMULAI JOURNEY INFERENSI ({customer_type.value.upper()}) <<<")
        results = engine.run_journey(uid, customer_type, up_to)

        for i, result in enumerate(results):
            if i > 0:
                prev = results[i - 1]
                delta_prob = (result.ml_probability - prev.ml_probability) * 100
                delta_rule = result.rule_score - prev.rule_score
                print(
                    f"\n--- Perubahan dari tahap sebelumnya: "
                    f"ML {delta_prob:+.1f}%, Rule {delta_rule:+.1f} ---"
                )
            _print_result(result, verbose=args.json)

        if args.json:
            print("\n" + json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False))
        return

    stage = LifecycleStage(args.stage)
    result = engine.predict(args.uid, stage, customer_type)
    _print_result(result, verbose=args.json)


if __name__ == "__main__":
    main()

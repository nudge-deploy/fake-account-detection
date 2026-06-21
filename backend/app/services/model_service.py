"""
Purpose: Load ABT/user artifacts and serve overview, risk list, and user detail predictions.
Used by: backend prediction API routes for /users, /user/{uid}, /predict, and overview stats.
Main dependencies: Supabase, ABT CSV, user CSV, and the loaded fraud model artifact.
Public/main functions: ModelService.load_artifacts, predict_user, predict_raw_features, get_user_details, get_top_risk_users, get_overview_stats, generate_reasons.
Side effects: Loads model/data from disk and queries Supabase when fallback reads are needed.
"""

import os
import json
import joblib
import pandas as pd
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

from app.utils.config import (
    EXISTING_USER_MODEL_PATH,
    FEATURE_COLUMNS_PATH,
    ABT_PATH,
    USERS_CSV_PATH,
)
from app.inference.scoring import compute_rule_score, categorize_risk
from app.schemas.request_response import PredictionResponse, UserDetailResponse, TopRiskUser, TopRiskUsersResponse

load_dotenv()


class ModelService:
    def __init__(self):
        self.model = None
        self.feature_columns = []
        self.supabase: Client = None
        self.df_merged = None

        self._init_supabase()
        self.load_artifacts()

    def _init_supabase(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if url and key:
            self.supabase = create_client(url, key)
            print("Successfully initialized Supabase client.")
        else:
            print("WARNING: Supabase credentials not found in .env")

    def load_artifacts(self):
        # 1. Load existing-user model
        if os.path.exists(EXISTING_USER_MODEL_PATH):
            try:
                self.model = joblib.load(EXISTING_USER_MODEL_PATH)
                print(f"Successfully loaded model from {EXISTING_USER_MODEL_PATH}")
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print(f"Model not found at {EXISTING_USER_MODEL_PATH}")

        # 2. Load feature columns
        if os.path.exists(FEATURE_COLUMNS_PATH):
            try:
                with open(FEATURE_COLUMNS_PATH, 'r') as f:
                    self.feature_columns = json.load(f)
                print(f"Successfully loaded feature columns ({len(self.feature_columns)} columns)")
            except Exception as e:
                print(f"Error loading feature columns: {e}")
        else:
            print(f"Feature columns not found at {FEATURE_COLUMNS_PATH}")

        # 3. Load ABT + Users → df_merged
        try:
            if os.path.exists(ABT_PATH) and os.path.exists(USERS_CSV_PATH):
                df_abt = pd.read_csv(ABT_PATH)
                df_users = pd.read_csv(USERS_CSV_PATH)

                if 'user_id' in df_users.columns:
                    df_users = df_users.rename(columns={'user_id': 'uid'})

                df_abt['uid'] = df_abt['uid'].astype(str)
                df_users['uid'] = df_users['uid'].astype(str)
                self.df_merged = pd.merge(df_abt, df_users, on='uid', how='left')

                if self.model is not None and self.feature_columns:
                    print("Batch predicting ML probabilities for df_merged...")
                    X = self.df_merged.reindex(columns=self.feature_columns, fill_value=0)
                    self.df_merged['ml_probability'] = self.model.predict_proba(X)[:, 1]
                    self.df_merged['ml_prediction'] = self.model.predict(X)

                print(f"Successfully loaded {len(self.df_merged)} rows into df_merged")
            else:
                print(f"ABT or Users CSV not found. ABT: {ABT_PATH}, Users: {USERS_CSV_PATH}")
        except Exception as e:
            print(f"Error loading df_merged: {e}")

    def generate_reasons(self, row: dict) -> List[str]:
        reasons = []
        if row.get('max_acc_dev', 0) > 5:
            reasons.append(f"Extreme device sharing ({int(row['max_acc_dev'])} accounts share the same device fingerprint)")
        elif row.get('max_acc_dev', 0) > 2:
            reasons.append(f"Multiple accounts ({int(row['max_acc_dev'])} accounts) share the same device fingerprint")
        if row.get('disp_email') == True or row.get('disp_email') == 1:
            reasons.append("Registered using a temporary/disposable email address domain")
        if row.get('phone_score', 0) > 0.7:
            reasons.append(f"Phone number displays suspicious pattern score of {float(row['phone_score']):.2f}")
        if row.get('max_acc_addr', 0) > 5:
            reasons.append(f"Extreme address sharing ({int(row['max_acc_addr'])} accounts share the same shipping address group)")
        if row.get('max_acc_pay', 0) > 3:
            reasons.append(f"Suspicious payment sharing ({int(row['max_acc_pay'])} accounts share the same payment method)")
        if row.get('promo_ratio', 0) > 0.9 and row.get('txn_f1m', 0) > 0:
            reasons.append(f"Voucher exploitation indicator ({float(row['promo_ratio']) * 100:.1f}% of transactions used a voucher/promo)")
        if row.get('ref_ring', 0) > 3:
            reasons.append(f"High referral ring score of {float(row['ref_ring']):.2f} (deep network structure of circular referrals)")
        if row.get('degree', 0) > 10:
            reasons.append(f"Highly connected in network graph (degree={int(row['degree'])})")
        if row.get('shared_ip_count', 0) > 3:
            reasons.append(f"High IP sharing detected ({int(row['shared_ip_count'])} shared IPs with other network nodes)")
        if not reasons and row.get('risk_score', 0) >= 20:
            reasons.append(f"Elevated risk score ({int(row['risk_score'])}) based on multiple cumulative minor flags.")
        return reasons

    def predict_user(self, uid: str) -> Optional[PredictionResponse]:
        if not self.supabase:
            return None
        res = self.supabase.table('fake_account_abt').select('*').eq('uid', uid).execute()
        if not res.data:
            return None
        row = res.data[0]

        X_dict = {col: row.get(col, 0) for col in self.feature_columns}
        X = pd.DataFrame([X_dict]).fillna(0)

        if self.model is not None:
            prob = float(self.model.predict_proba(X)[:, 1][0])
            pred = int(self.model.predict(X)[0])
        else:
            prob = float(row.get('ml_probability', 0.0))
            pred = int(row.get('ml_prediction', 0))

        rule_score = float(row.get('risk_score', 0))
        risk_cat = row.get('risk_cat', 'Low')
        is_suspicious = (prob > 0.5) or (rule_score >= 50.0)
        reasons = self.generate_reasons(row)

        return PredictionResponse(
            uid=uid,
            model_prediction=pred,
            model_probability=prob,
            rule_based_score=rule_score,
            risk_category=risk_cat,
            is_suspicious=is_suspicious,
            reasons=reasons,
        )

    def predict_raw_features(self, features: Dict[str, Any]) -> PredictionResponse:
        input_data = {}
        for col in self.feature_columns:
            val = features.get(col, 0)
            if isinstance(val, bool):
                val = 1 if val else 0
            input_data[col] = val

        X = pd.DataFrame([input_data])

        if self.model is not None:
            prob = float(self.model.predict_proba(X)[:, 1][0])
            pred = int(self.model.predict(X)[0])
        else:
            prob = 0.0
            pred = 0

        rule_score = compute_rule_score(input_data)
        risk_cat = categorize_risk(rule_score)
        is_suspicious = (prob > 0.5) or (rule_score >= 50.0)

        input_data['risk_score'] = rule_score
        reasons = self.generate_reasons(input_data)

        return PredictionResponse(
            uid=None,
            model_prediction=pred,
            model_probability=prob,
            rule_based_score=rule_score,
            risk_category=risk_cat,
            is_suspicious=is_suspicious,
            reasons=reasons,
        )

    def get_user_details(self, uid: str) -> Optional[UserDetailResponse]:
        if self.df_merged is not None:
            user_rows = self.df_merged[self.df_merged['uid'] == uid]
            if user_rows.empty:
                return None
            row = user_rows.iloc[0].to_dict()

            features = {}
            for col in self.feature_columns:
                val = row.get(col, 0)
                if pd.isna(val):
                    val = 0
                features[col] = float(val) if isinstance(val, (int, float)) else val

            rule_score = float(row.get('risk_score', 0))
            fraud_val = bool(row.get('fraud')) if not pd.isna(row.get('fraud')) else None
            ftype_val = str(row.get('ftype')) if not pd.isna(row.get('ftype')) else None
            live_prediction = self.predict_user(uid)
            ml_pred_val = live_prediction.model_prediction if live_prediction else (int(row.get('ml_prediction')) if not pd.isna(row.get('ml_prediction')) else None)
            ml_prob_val = live_prediction.model_probability if live_prediction else (float(row.get('ml_probability')) if not pd.isna(row.get('ml_probability')) else None)
            reasons = self.generate_reasons(row)

            return UserDetailResponse(
                uid=uid,
                full_name=row.get('full_name') if not pd.isna(row.get('full_name')) else None,
                email=row.get('email') if not pd.isna(row.get('email')) else None,
                phone_number=str(row.get('phone_number')) if not pd.isna(row.get('phone_number')) else None,
                registration_date=str(row.get('registration_date')) if not pd.isna(row.get('registration_date')) else None,
                registration_channel=str(row.get('registration_channel')) if not pd.isna(row.get('registration_channel')) else None,
                city=str(row.get('city')) if not pd.isna(row.get('city')) else None,
                province=str(row.get('province')) if not pd.isna(row.get('province')) else None,
                account_status=str(row.get('account_status')) if not pd.isna(row.get('account_status')) else None,
                features=features,
                risk_score_rule_based=rule_score,
                risk_category=str(row.get('risk_cat', 'Low')),
                fraud=fraud_val,
                ftype=ftype_val,
                ml_prediction=ml_pred_val,
                ml_probability=ml_prob_val,
                reasons=reasons,
            )

        if not self.supabase:
            return None

        abt_res = self.supabase.table('fake_account_abt').select('*').eq('uid', uid).execute()
        if not abt_res.data:
            return None
        abt_row = abt_res.data[0]

        user_res = self.supabase.table('users').select('*').eq('user_id', uid).execute()
        user_row = user_res.data[0] if user_res.data else {}

        features = {}
        for col in self.feature_columns:
            val = abt_row.get(col, 0)
            if val == "":
                val = 0
            features[col] = val

        rule_score = float(abt_row.get('risk_score', 0))
        fraud = abt_row.get('fraud')
        fraud_val = bool(fraud) if fraud != "" else None
        ftype = abt_row.get('ftype')
        ftype_val = str(ftype) if ftype != "" else None
        ml_pred = abt_row.get('ml_prediction')
        ml_pred_val = int(ml_pred) if ml_pred != "" else None
        ml_prob = abt_row.get('ml_probability')
        ml_prob_val = float(ml_prob) if ml_prob != "" else None
        reasons = self.generate_reasons(abt_row)

        return UserDetailResponse(
            uid=uid,
            full_name=user_row.get('full_name'),
            email=user_row.get('email'),
            phone_number=user_row.get('phone_number'),
            registration_date=user_row.get('registration_date'),
            registration_channel=user_row.get('registration_channel'),
            city=user_row.get('city'),
            province=user_row.get('province'),
            account_status=user_row.get('account_status'),
            features=features,
            risk_score_rule_based=rule_score,
            risk_category=str(abt_row.get('risk_cat', 'Low')),
            fraud=fraud_val,
            ftype=ftype_val,
            ml_prediction=ml_pred_val,
            ml_probability=ml_prob_val,
            reasons=reasons,
        )

    def get_top_risk_users(self, limit: int = 10, risk_category: Optional[str] = None) -> TopRiskUsersResponse:
        if self.df_merged is not None:
            df = self.df_merged.copy()
            if risk_category:
                df = df[df['risk_cat'].str.lower() == risk_category.strip().lower()]

            if 'ml_probability' in df.columns:
                df = df.sort_values(by=['ml_probability', 'risk_score'], ascending=[False, False])
            else:
                df = df.sort_values(by='risk_score', ascending=False)

            top_rows = df.head(limit)
            total_suspicious = len(df[df['risk_score'] > 30])

            users_list = []
            for _, row in top_rows.iterrows():
                users_list.append(TopRiskUser(
                    uid=row['uid'],
                    full_name=row.get('full_name') if not pd.isna(row.get('full_name')) else None,
                    email=row.get('email') if not pd.isna(row.get('email')) else None,
                    risk_score_rule_based=float(row.get('risk_score', 0)),
                    risk_category=str(row.get('risk_cat', 'Low')),
                    ml_probability=float(row.get('ml_probability', 0.0)) if not pd.isna(row.get('ml_probability')) else None,
                    ftype=str(row.get('ftype')) if not pd.isna(row.get('ftype')) else None,
                ))
            return TopRiskUsersResponse(total_suspicious=total_suspicious, users=users_list)

        if not self.supabase:
            return TopRiskUsersResponse(total_suspicious=0, users=[])

        query = self.supabase.table('fake_account_abt').select('uid, risk_score, risk_cat, ml_probability, ftype')
        if risk_category:
            query = query.eq('risk_cat', risk_category.capitalize())
        res = query.order('ml_probability', desc=True).order('risk_score', desc=True).limit(limit).execute()
        top_rows = res.data
        if not top_rows:
            return TopRiskUsersResponse(total_suspicious=0, users=[])

        count_res = self.supabase.table('fake_account_abt').select('uid', count='exact').gt('risk_score', 30).execute()
        total_suspicious = count_res.count if count_res.count else 0

        uids = [r['uid'] for r in top_rows]
        user_res = self.supabase.table('users').select('user_id, full_name, email').in_('user_id', uids).execute()
        user_map = {u['user_id']: u for u in user_res.data} if user_res.data else {}

        users_list = []
        for row in top_rows:
            u_info = user_map.get(row['uid'], {})
            users_list.append(TopRiskUser(
                uid=row['uid'],
                full_name=u_info.get('full_name'),
                email=u_info.get('email'),
                risk_score_rule_based=float(row.get('risk_score', 0)),
                risk_category=str(row.get('risk_cat', 'Low')),
                ml_probability=float(row.get('ml_probability', 0.0)) if row.get('ml_probability') != "" else None,
                ftype=str(row.get('ftype')) if row.get('ftype') != "" else None,
            ))

        return TopRiskUsersResponse(total_suspicious=total_suspicious, users=users_list)

    def get_overview_stats(self) -> Dict[str, Any]:
        if self.df_merged is not None:
            df = self.df_merged
            total_users = len(df)
            total_fake = int(df['fraud'].sum())
            total_high_risk = len(df[df['risk_cat'].str.lower() == 'high'])

            txn_cols = [c for c in df.columns if c.startswith('txn_f') and c.endswith('m')]
            total_transactions = int(df[txn_cols].sum().sum()) if txn_cols else 0

            promo_cols = [c for c in df.columns if c.startswith('promo_f') and c.endswith('m')]
            total_promo_discount = float(df[promo_cols].sum().sum()) if promo_cols else 0.0

            if promo_cols:
                abuse_df = df[df['fraud'] == True]
                estimated_promo_abuse_amount = float(abuse_df[promo_cols].sum().sum())
            else:
                estimated_promo_abuse_amount = 0.0

            return {
                "total_users": total_users,
                "total_fake_accounts": total_fake,
                "fake_account_rate": float(total_fake / total_users) if total_users > 0 else 0.0,
                "total_transactions": total_transactions,
                "total_promo_discount": total_promo_discount,
                "estimated_promo_abuse_amount": estimated_promo_abuse_amount,
                "high_risk_users": total_high_risk,
            }

        if not self.supabase:
            return {}

        try:
            total_users_res = self.supabase.table('fake_account_abt').select('uid', count='exact').limit(1).execute()
            total_users = total_users_res.count or 0
            fake_res = self.supabase.table('fake_account_abt').select('uid', count='exact').eq('fraud', True).execute()
            total_fake = fake_res.count or 0
            high_risk_res = self.supabase.table('fake_account_abt').select('uid', count='exact').eq('risk_cat', 'High').execute()
            total_high_risk = high_risk_res.count or 0

            return {
                "total_users": total_users,
                "total_fake_accounts": total_fake,
                "fake_account_rate": float(total_fake / total_users) if total_users > 0 else 0.0,
                "total_transactions": 0,
                "total_promo_discount": 0.0,
                "estimated_promo_abuse_amount": 0.0,
                "high_risk_users": total_high_risk,
            }
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return {}

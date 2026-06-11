"""Purpose: Provide Groq-backed fraud assistant replies and targeted raw-data lookups.
Used by: chatbot API router.
Depends on: ModelService, GraphService, raw CSV files, optional Groq API client.
Public functions: ChatbotService.process_message, prompt router helpers, lookup helpers, and graph/statistics handlers.
Side effects: Optional HTTP call to Groq and CSV reads from data/raw when lookups or prompt routing are requested.
"""

import re
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

import pandas as pd
from app.services.model_service import ModelService
from app.services.graph_service import GraphService
from app.schemas.request_response import ChatResponse

# Try importing groq SDK
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class ChatbotService:
    def __init__(self, model_service: ModelService, graph_service: GraphService):
        self.model_service = model_service
        self.graph_service = graph_service
        self.base_dir = Path(__file__).resolve().parents[3]
        self.raw_dir = self.base_dir / "data" / "raw"

    def _normalize_chat_topic(self, message: str) -> str:
        text = self._normalize_text(message)
        if any(token in text for token in ["berapa", "jumlah", "persen", "statistik", "rata", "distribution", "total"]):
            return "statistics"
        if any(token in text for token in ["detail", "investigasi", "kenapa", "mengapa", "dicurigai", "akun", "top risk", "mencurigakan"]):
            return "account_investigation"
        if any(token in text for token in ["ringkasan", "executive", "eksekutif", "overview", "summary", "gambaran"]):
            return "executive_summary"
        if any(token in text for token in ["tabel", "table", "kolom", "baris", "analisis tabel"]):
            return "table_analysis"
        return "general"

    def _build_system_prompt(self, topic: str) -> str:
        base_rules = (
            "You are a helpful Fraud Analyst Assistant on a platform that detects fake accounts and promo abuse "
            "(such as shared devices, shared addresses, shared payments, referral rings, and voucher farming).\n"
            "Your job is to analyze accounts and answer user queries professionally in Indonesian.\n"
            "Use the provided context data to answer the user's question.\n"
            "If the user asks about a specific user, explain their suspicious indicators and risk category clearly based on the provided context and reasons.\n"
            "Do not make up facts or user data.\n"
            "Speak naturally, professionally, and clearly.\n"
            "Format your output nicely using Markdown.\n"
            "Do not use greetings, self-references like 'aku', or direct addresses like 'kamu' unless the user explicitly asks for a casual style.\n"
            "Keep responses concise, warm, and easy to understand.\n"
        )
        if topic == "statistics":
            return (
                base_rules
                + "This answer is a statistics response.\n"
                + "Prioritize counts, percentages, totals, and distributions.\n"
                + "If the answer contains a list of 3 or more items, use a markdown table.\n"
                + "If the answer is explanatory, use short bullet points.\n"
                + "End with a short factual conclusion."
            )
        if topic == "account_investigation":
            return (
                base_rules
                + "This answer is an account investigation response.\n"
                + "Prioritize account identity, risk score, fraud probability, risk category, and supporting evidence.\n"
                + "If there are 3 or more supporting facts, present them as a markdown table.\n"
                + "Otherwise use bullet points for indicators and concise narrative for the conclusion.\n"
                + "If there are multiple evidence items, list them clearly.\n"
                + "Do not over-explain unrelated metrics."
            )
        if topic == "executive_summary":
            return (
                base_rules
                + "This answer is an executive summary response.\n"
                + "Prioritize the most important numbers, risk trends, and business implications.\n"
                + "Keep the tone concise, polished, and decision-oriented.\n"
                + "Use a short summary followed by a few key bullets and one conclusion."
            )
        if topic == "table_analysis":
            return (
                base_rules
                + "This answer is a table analysis response.\n"
                + "If the context contains table-like data, present findings in a markdown table.\n"
                + "Then provide a short interpretation with bullet points.\n"
                + "Highlight patterns, extremes, anomalies, and comparisons.\n"
                + "Keep the analysis grounded in the observed data."
            )
        return (
            base_rules
            + "This answer is a general fraud analysis response.\n"
            + "If the answer is naturally tabular or contains a list of 3 or more items, format it as a clear markdown table.\n"
            + "If the answer is explanatory, use short bullet points or numbered points.\n"
            + "Do not mix table and long prose in the same answer unless needed for clarity.\n"
            + "Keep the answer aligned with the user's question and the available context."
        )

    def _format_reply_block(
        self,
        title: str,
        summary: str,
        lines: List[str],
        footer: Optional[str] = None,
    ) -> str:
        parts = [f"### {title}", ""]
        if summary.strip():
            parts.append(summary.strip())
            parts.append("")
        parts.extend(lines)
        if footer and footer.strip():
            parts.append("")
            parts.append(footer.strip())
        return "\n".join(parts).strip()

    def get_graph_edges(self) -> List[Dict[str, Any]]:
        return self.graph_service.raw_edges

    def get_graph_nodes(self) -> List[Dict[str, Any]]:
        return self.graph_service.raw_nodes

    def _load_raw_csv(self, filename: str) -> Optional[pd.DataFrame]:
        path = self.raw_dir / filename
        if not path.exists():
            return None
        try:
            return pd.read_csv(path)
        except Exception:
            return None

    def _safe_str(self, value: Any, default: str = "N/A") -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        return str(value)

    def _normalize_text(self, text: str) -> str:
        text = str(text or "").lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        text = re.sub(r'\b(hj|h\.j|haji|hj\.|bu|bapak|ibu|pak|ny|ny\.)\b', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _extract_user_id(self, msg: str) -> Optional[str]:
        patterns = [
            r'\b(usr\d+)\b',
            r'\b(u\d+)\b',
            r'\buser\s*(?:id)?\s*(usr\d+)\b',
            r'\buser\s*(?:id)?\s*(\d{1,6})\b',
            r'\bid\s*(?:user\s*)?(usr\d+)\b',
            r'\bid\s*(?:user\s*)?(\d{1,6})\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, msg)
            if not match:
                continue
            token = match.group(1).upper()
            if token.startswith("USR"):
                return token
            if token.startswith("U") and token[1:].isdigit():
                return f"USR{int(token[1:]):05d}"
            if token.isdigit():
                return f"USR{int(token):05d}"
        return None

    def _name_contains_tokens(self, candidate_name: str, target_tokens: list[str]) -> bool:
        name_tokens = set(candidate_name.split())
        return all(tok in name_tokens or tok in candidate_name for tok in target_tokens)

    def _extract_name_tokens(self, text: str) -> list[str]:
        stopwords = {
            "alamat", "address", "yang", "terkait", "untuk", "dari",
            "di", "ke", "pada", "dimana", "mana", "berada", "tolong",
            "user", "pengguna", "nama", "siapa", "atas"
        }
        normalized = self._normalize_text(text)
        tokens = [tok for tok in normalized.split() if len(tok) > 1 and tok not in stopwords]
        return tokens

    def _detect_intent_with_llm(self, message: str) -> Optional[str]:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not (GROQ_AVAILABLE and groq_api_key):
            return None

        try:
            client = Groq(api_key=groq_api_key)
            prompt = (
                "Classify the user's message into exactly one intent label.\n"
                "Return only the label, no extra words.\n\n"
                "Allowed labels:\n"
                "device_cluster\n"
                "address_lookup\n"
                "address_by_user_name\n"
                "transaction_lookup\n"
                "user_detail\n"
                "top_risk\n"
                "stats\n"
                "shared_device\n"
                "shared_address\n"
                "shared_payment\n"
                "referral_ring\n"
                "voucher_farming\n"
                "common_pattern\n"
                "general\n\n"
                "Message:\n"
                f"{message}"
            )
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a strict intent classifier."},
                    {"role": "user", "content": prompt},
                ],
                model="llama-3.1-8b-instant",
                temperature=0.0,
                max_tokens=20,
            )
            label = resp.choices[0].message.content.strip().lower()
            allowed = {
                "device_cluster",
                "address_lookup",
                "address_by_user_name",
                "transaction_lookup",
                "user_detail",
                "top_risk",
                "stats",
                "shared_device",
                "shared_address",
                "shared_payment",
                "referral_ring",
                "voucher_farming",
                "common_pattern",
                "general",
            }
            return label if label in allowed else None
        except Exception:
            return None

    def _handle_address_lookup(self, msg: str) -> ChatResponse:
        df_user_addresses = self._load_raw_csv("user_addresses.csv")
        df_addresses = self._load_raw_csv("addresses.csv")
        df_users = self._load_raw_csv("users.csv")

        if df_user_addresses is None or df_addresses is None:
            return ChatResponse(reply="Maaf, data alamat belum tersedia di raw CSV.")

        merged = df_user_addresses.merge(df_addresses, on="address_id", how="left")
        if df_users is not None:
            user_cols = [c for c in ["user_id", "full_name", "email", "phone_number"] if c in df_users.columns]
            merged = merged.merge(df_users[user_cols], on="user_id", how="left")

        address_match = re.search(r'\b(adr\d+)\b', msg)
        if address_match:
            address_id = address_match.group(1).upper()
            filtered = merged[merged["address_id"].astype(str).str.upper() == address_id]
            if filtered.empty:
                return ChatResponse(reply=f"Alamat **{address_id}** tidak ditemukan di data raw.")
            rows = [
                (
                    f"- {self._safe_str(row.get('address_text'))} "
                    f"({self._safe_str(row.get('city'))}, {self._safe_str(row.get('province'))}) | "
                    f"ID: `{self._safe_str(row.get('address_id'))}` | "
                    f"User: `{self._safe_str(row.get('user_id'))}` | "
                    f"Nama: {self._safe_str(row.get('full_name'))}"
                )
                for _, row in filtered.head(10).iterrows()
            ]
            reply = self._format_reply_block(
                title="Alamat Terkait",
                summary=f"Hasil pencarian untuk **{address_id}**:",
                lines=rows,
            )
            return ChatResponse(reply=reply, data={"addresses": filtered.head(10).to_dict(orient="records")})

        grouped = (
            merged.groupby(["address_id", "address_text", "city", "province"], dropna=False)["user_id"]
            .nunique()
            .reset_index(name="user_count")
            .sort_values(by=["user_count", "address_id"], ascending=[False, True])
        )

        if grouped.empty:
            return ChatResponse(reply="Belum ada data alamat yang bisa dibaca.")

        top_rows = grouped.head(5)
        rows = [
            (
                f"- {self._safe_str(row['address_text'])} "
                f"({self._safe_str(row['city'])}, {self._safe_str(row['province'])}) | "
                f"ID: `{self._safe_str(row['address_id'])}` | "
                f"{int(row['user_count'])} user"
            )
            for _, row in top_rows.iterrows()
        ]
        reply = self._format_reply_block(
            title="Alamat yang Paling Sering Dipakai",
            summary="Ringkasan alamat yang paling banyak dipakai user:",
            lines=rows,
            footer="Kalau mau, aku juga bisa rincikan user dan transaksi untuk salah satu alamat tersebut.",
        )
        return ChatResponse(reply=reply, data={"addresses": top_rows.to_dict(orient="records")})

    def _handle_transaction_lookup(self, msg: str) -> ChatResponse:
        df_txn = self._load_raw_csv("transactions.csv")
        df_users = self._load_raw_csv("users.csv")
        df_addresses = self._load_raw_csv("addresses.csv")
        df_payments = self._load_raw_csv("payments.csv")
        df_vouchers = self._load_raw_csv("vouchers.csv")

        if df_txn is None:
            return ChatResponse(reply="Maaf, data transaksi belum tersedia di raw CSV.")

        if df_users is not None and "user_id" in df_users.columns:
            df_txn = df_txn.merge(df_users[[c for c in ["user_id", "full_name", "email"] if c in df_users.columns]], on="user_id", how="left")
        if df_addresses is not None and "address_id" in df_txn.columns:
            df_txn = df_txn.merge(df_addresses[[c for c in ["address_id", "address_text", "city", "province"] if c in df_addresses.columns]], on="address_id", how="left")
        if df_payments is not None and "payment_id" in df_txn.columns:
            df_txn = df_txn.merge(df_payments[[c for c in ["payment_id", "payment_type", "payment_provider"] if c in df_payments.columns]], on="payment_id", how="left")
        if df_vouchers is not None and "voucher_id" in df_txn.columns:
            df_txn = df_txn.merge(df_vouchers[[c for c in ["voucher_id", "voucher_code", "voucher_type", "promo_category"] if c in df_vouchers.columns]], on="voucher_id", how="left")

        txn_match = re.search(r'\b(txn\d+)\b', msg)
        address_match = re.search(r'\b(adr\d+)\b', msg)
        user_match = re.search(r'\b(usr\d+)\b', msg)

        filtered = df_txn.copy()
        if txn_match:
            txn_id = txn_match.group(1).upper()
            filtered = filtered[filtered["transaction_id"].astype(str).str.upper() == txn_id]
        elif address_match:
            address_id = address_match.group(1).upper()
            filtered = filtered[filtered["address_id"].astype(str).str.upper() == address_id]
        elif user_match:
            user_id = user_match.group(1).upper()
            filtered = filtered[filtered["user_id"].astype(str).str.upper() == user_id]

        if filtered.empty:
            return ChatResponse(reply="Tidak ada transaksi yang cocok dengan permintaan itu.")

        rows = []
        for _, row in filtered.head(10).iterrows():
            voucher_value = row.get("voucher_code") or row.get("voucher_id")
            rows.append(
                f"- Transaksi `{self._safe_str(row.get('transaction_id'))}` | "
                f"User: `{self._safe_str(row.get('user_id'))}` | "
                f"Jumlah: `{self._safe_str(row.get('order_amount'))}` | "
                f"Final: `{self._safe_str(row.get('final_amount'))}` | "
                f"Alamat: {self._safe_str(row.get('address_text'))} | "
                f"Metode bayar: {self._safe_str(row.get('payment_type') or row.get('payment_id'))} | "
                f"Voucher: `{self._safe_str(voucher_value)}`"
            )

        reply = self._format_reply_block(
            title="Transaksi yang Terkait",
            summary="Aku menemukan transaksi yang cocok dengan permintaanmu:",
            lines=rows,
            footer="Kalau kamu mau, aku bisa lanjut jelaskan transaksi tertentu satu per satu.",
        )
        return ChatResponse(reply=reply, data={"transactions": filtered.head(10).to_dict(orient="records")})

    def _handle_user_name_address_lookup(self, msg: str, user_id_token: Optional[str] = None) -> ChatResponse:
        df_users = self._load_raw_csv("users.csv")
        df_user_addresses = self._load_raw_csv("user_addresses.csv")
        df_addresses = self._load_raw_csv("addresses.csv")

        if df_users is None or df_user_addresses is None or df_addresses is None:
            return ChatResponse(reply="Maaf, data user/alamat belum tersedia lengkap di raw CSV.")

        if "full_name" not in df_users.columns:
            return ChatResponse(reply="Maaf, kolom nama user tidak tersedia di data raw.")

        raw_name = msg.strip()
        matched_users = df_users.iloc[0:0]
        if user_id_token:
            matched_users = df_users[df_users["user_id"].astype(str).str.upper() == user_id_token]

        if matched_users.empty:
            name_match = re.search(r'(?:pengguna|user|nama)\s+(.+)', msg)
            raw_name = name_match.group(1).strip() if name_match else raw_name
            raw_name = re.sub(r'^(alamat|address|yang|terkait|untuk|dari)\s+', '', raw_name).strip()
            raw_name = re.sub(r'^(di|ke|pada)\s+', '', raw_name).strip()
            raw_name = re.sub(r'\b(alamat|address)\b', '', raw_name).strip()

            if not raw_name:
                return ChatResponse(reply="Sebutkan nama user yang ingin ditelusuri, misalnya: alamat terkait pengguna Alika Farida.")

            df_users_local = df_users.copy()
            df_users_local["_name_norm"] = df_users_local["full_name"].astype(str).map(self._normalize_text)
            target_tokens = self._extract_name_tokens(raw_name)
            if not target_tokens:
                return ChatResponse(reply="Sebutkan nama user yang ingin ditelusuri dengan lebih jelas.")

            matched_users = df_users_local[df_users_local["_name_norm"].apply(lambda name: self._name_contains_tokens(name, target_tokens))]

        if matched_users.empty:
            return ChatResponse(reply=f"Saya tidak menemukan user dengan nama mirip **{raw_name}** di data raw.")

        merged = df_user_addresses.merge(df_addresses, on="address_id", how="left")
        merged = merged.merge(matched_users[["user_id", "full_name"]], on="user_id", how="inner")

        if merged.empty:
            return ChatResponse(reply=f"User **{matched_users.iloc[0]['full_name']}** ada di data user, tetapi belum punya relasi alamat yang tersimpan.")

        grouped = (
            merged.groupby(["user_id", "full_name", "address_id", "address_text", "city", "province"], dropna=False)
            .size()
            .reset_index(name="relation_count")
            .sort_values(by=["relation_count", "address_id"], ascending=[False, True])
        )

        reply = f"### Alamat Terkait Pengguna: **{matched_users.iloc[0]['full_name']}**\n\n"
        for _, row in grouped.head(10).iterrows():
            reply += (
                f"- **{self._safe_str(row.get('address_id'))}** | "
                f"{self._safe_str(row.get('address_text'))} | "
                f"{self._safe_str(row.get('city'))}, {self._safe_str(row.get('province'))}\n"
            )

        return ChatResponse(
            reply=reply,
            data={
                "_response_mode": "direct",
                "matched_users": matched_users[["user_id", "full_name"]].head(10).to_dict(orient="records"),
                "addresses": grouped.head(10).to_dict(orient="records"),
            },
        )

    def _build_modular_context(self, message: str) -> tuple[str, Optional[dict[str, Any]]]:
        msg = message.strip().lower()
        raw_msg = message.strip()
        detected_intent = self._detect_intent_with_llm(raw_msg) or "general"
        user_id_token = self._extract_user_id(msg)
        device_match = re.search(r'\b(dvc\d+)\b', msg)

        if detected_intent in {"address_lookup", "address_by_user_name"}:
            res = self._handle_user_name_address_lookup(raw_msg, user_id_token=user_id_token)
            return res.reply, res.data

        if detected_intent == "transaction_lookup":
            res = self._handle_transaction_lookup(msg)
            return res.reply, res.data

        if detected_intent == "device_cluster" or device_match:
            dvc_id = device_match.group(1).upper() if device_match else "N/A"
            edges = self.get_graph_edges()
            nodes = self.get_graph_nodes()
            connected_users = []
            for edge in edges:
                if str(edge.get("target")).upper() == dvc_id or str(edge.get("source")).upper() == dvc_id:
                    other = edge.get("source") if str(edge.get("target")).upper() == dvc_id else edge.get("target")
                    if str(other).upper().startswith("USR"):
                        connected_users.append(other)
            user_info = []
            for u in connected_users:
                node_details = next((n for n in nodes if n["id"] == u), None)
                risk = node_details.get("risk_category", "Low") if node_details else "Low"
                score = node_details.get("risk_score", 0) if node_details else 0
                user_info.append(f"- {u}: kategori {risk}, skor {score}/100")
            context = (
                f"Device cluster for {dvc_id}\n"
                f"Connected users: {len(connected_users)}\n"
                f"Details:\n" + ("\n".join(user_info) if user_info else "- no direct users linked")
            )
            return context, {"device_id": dvc_id, "connected_users": connected_users}

        if detected_intent == "shared_device":
            df = self.model_service.df_merged
            if df is None or df.empty:
                return "ABT belum tersedia.", None
            fake_emu = df[(df["fraud"] == 1) & (df["max_acc_dev"] > 2)]
            total_fake = df[df["fraud"] == 1]
            pct = (len(fake_emu) / len(total_fake) * 100) if len(total_fake) else 0
            context = (
                f"ABT summary for shared-device abuse:\n"
                f"Fake accounts using emulator/shared device: {len(fake_emu)} of {len(total_fake)} ({pct:.1f}%)."
            )
            return context, {"count_fake_emulator": len(fake_emu), "total_fake": len(total_fake), "percentage": pct}

        if detected_intent == "shared_address":
            edges = self.get_graph_edges()
            nodes = self.get_graph_nodes()
            address_fake_users = {}
            for edge in edges:
                if edge.get("relationship") == "ships_to_address":
                    adr = edge.get("target")
                    usr = edge.get("source")
                    address_fake_users.setdefault(adr, set()).add(usr)
            shared_addresses = sorted(address_fake_users.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            context = "Shared addresses across connected users:\n" + "\n".join(
                [f"{adr}: {len(usrs)} users -> {list(usrs)}" for adr, usrs in shared_addresses]
            )
            return context, {"shared_addresses": [{a: list(u)} for a, u in shared_addresses]}

        if detected_intent == "common_pattern":
            df = self.model_service.df_merged
            if df is None or "ftype" not in df.columns:
                return "ABT belum punya kolom ftype.", None
            counts = df["ftype"].value_counts().to_dict()
            context = "Fraud type distribution in ABT:\n" + "\n".join([f"{k}: {v}" for k, v in counts.items()])
            return context, {"fraud_patterns": counts}

        if detected_intent == "user_detail" or user_id_token:
            user_id = user_id_token
            details = self.model_service.get_user_details(user_id)
            if not details:
                return f"User ID {user_id} tidak ditemukan.", None
            prediction = self.model_service.predict_user(user_id)
            reasons_str = "\n".join([f"- {r}" for r in (prediction.reasons if prediction else [])])
            context = (
                f"Full Name: {details.full_name}\n"
                f"User ID: {user_id}\n"
                f"Email: {details.email}\n"
                f"Phone: {details.phone_number}\n"
                f"City/Province: {details.city}, {details.province}\n"
                f"Risk Category: {details.risk_category}\n"
                f"Rule Score: {details.risk_score_rule_based}/100\n"
                f"ML Probability: {details.ml_probability*100:.2f}%\n"
                f"ML Prediction: {'FAKE' if details.ml_prediction == 1 else 'NORMAL'}\n"
                f"Ground Truth: {'FAKE' if details.fraud else 'NORMAL'} ({details.ftype})\n"
                f"Reasons:\n{reasons_str}\n"
            )
            return context, {"user_details": details.model_dump()}

        if detected_intent == "top_risk":
            top_risk = self.model_service.get_top_risk_users(limit=5)
            context = "Top suspicious users:\n" + "\n".join(
                [
                    f"{idx}. {u.full_name or 'N/A'} (User ID: {u.uid}): rule {u.risk_score_rule_based}/100, ml {u.ml_probability*100:.1f}%"
                    for idx, u in enumerate(top_risk.users, 1)
                ]
            )
            return context, {"top_users": [u.model_dump() for u in top_risk.users]}

        if detected_intent == "stats":
            stats_res = self._handle_stats_query()
            return stats_res.reply, stats_res.data

        if detected_intent == "shared_payment":
            return self._handle_shared_payment_concept(), None
        if detected_intent == "referral_ring":
            return self._handle_referral_ring_concept(), None
        if detected_intent == "voucher_farming":
            return self._handle_voucher_farming_concept(), None

        return (
            "General context: Fraud & Fake Account Detection prototype with ABT, graph features, and model outputs.",
            None,
        )

    def process_message(self, message: str) -> ChatResponse:
        context_data, structured_data = self._build_modular_context(message)
        if structured_data and structured_data.get("_response_mode") == "direct":
            structured_data = {k: v for k, v in structured_data.items() if k != "_response_mode"}
            return ChatResponse(reply=context_data, data=structured_data)

        topic = self._normalize_chat_topic(message)

        groq_api_key = os.getenv("GROQ_API_KEY")
        if GROQ_AVAILABLE and groq_api_key:
            try:
                client = Groq(api_key=groq_api_key)
                system_prompt = self._build_system_prompt(topic)
                user_content = f"Context data:\n{context_data}\n\nUser Question: {message}"
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    model="llama-3.1-8b-instant",
                    temperature=0.2,
                    max_tokens=1000,
                )
                llm_reply = chat_completion.choices[0].message.content.strip()
                return ChatResponse(reply=llm_reply, data=structured_data)
            except Exception as e:
                print(f"Error calling Groq API: {e}.")
                return ChatResponse(reply="Maaf, AI chatbot sedang tidak tersedia saat ini. Silakan coba lagi nanti.", data=structured_data)

        return ChatResponse(reply="Maaf, AI chatbot memerlukan koneksi LLM untuk menjawab saat ini.", data=structured_data)

    def _handle_top_risk_query(self) -> ChatResponse:
        top_risk = self.model_service.get_top_risk_users(limit=5)
        reply_lines = []

        for idx, u in enumerate(top_risk.users, 1):
            ml_prob_str = f"{u.ml_probability*100:.1f}% ML Prob" if u.ml_probability is not None else "N/A"
            reply_lines.append(
                f"{idx}. **{u.uid}** - {u.full_name or 'N/A'} | "
                f"Email: `{u.email or 'N/A'}` | "
                f"Rule: `{u.risk_score_rule_based}/100` | ML: {ml_prob_str} | "
                f"Tipe: `{u.ftype or 'N/A'}`"
            )
        reply = self._format_reply_block(
            title="Top 5 Akun Paling Mencurigakan",
            summary="Berdasarkan analisis gabungan ML dan rule-based:",
            lines=reply_lines,
            footer="Anda bisa mengetik `Detail [User ID]` untuk membedah riwayat indikator lengkap dari user tersebut.",
        )
        return ChatResponse(reply=reply, data={"top_users": [u.model_dump() for u in top_risk.users]})

    def _handle_stats_query(self) -> ChatResponse:
        df = self.model_service.df_merged
        if df is None or df.empty:
            return ChatResponse(reply="Maaf, data ABT belum tersedia di memori.")

        total_users = len(df)
        risk_col = 'risk_cat' if 'risk_cat' in df.columns else 'risk_category'
        categories = df[risk_col].value_counts().to_dict() if risk_col in df.columns else {}
        high_count = int(categories.get('High', 0))
        med_count = int(categories.get('Medium', 0))
        low_count = int(categories.get('Low', 0))

        ground_truth_col = 'fraud' if 'fraud' in df.columns else None
        ground_truth_fake = int(df[ground_truth_col].fillna(False).astype(bool).sum()) if ground_truth_col else 0
        ground_truth_normal = int(total_users - ground_truth_fake)

        model_pred_col = 'ml_prediction' if 'ml_prediction' in df.columns else None
        model_pred_fake = int(df[model_pred_col].fillna(0).astype(int).sum()) if model_pred_col else 0
        model_pred_normal = int(total_users - model_pred_fake)

        model_prob_col = 'ml_probability' if 'ml_probability' in df.columns else None
        avg_model_prob = float(df[model_prob_col].fillna(0).mean()) if model_prob_col else 0.0

        rule_high_count = int((df['risk_score'] >= 50).sum()) if 'risk_score' in df.columns else 0

        reply = self._format_reply_block(
            title="Statistik Deteksi Akun Palsu",
            summary=f"Ringkasan singkat dari data ABT. Total pengguna di sini ada **{total_users:,}** akun.",
            lines=[
                "**1) Label asli dataset (ground truth)**",
                f"- Fraud: `{ground_truth_fake:,}` akun ({ground_truth_fake/total_users*100:.1f}%)",
                f"- Normal: `{ground_truth_normal:,}` akun ({ground_truth_normal/total_users*100:.1f}%)",
                "",
                "**2) Prediksi model ML**",
                f"- Fraud terdeteksi model: `{model_pred_fake:,}` akun ({model_pred_fake/total_users*100:.1f}%)",
                f"- Normal menurut model: `{model_pred_normal:,}` akun ({model_pred_normal/total_users*100:.1f}%)",
                f"- Rata-rata probabilitas fraud model: `{avg_model_prob*100:.1f}%`",
                "",
                "**3) Kategori risiko rule-based**",
                f"- High: `{high_count:,}` akun ({high_count/total_users*100:.1f}%)",
                f"- Medium: `{med_count:,}` akun ({med_count/total_users*100:.1f}%)",
                f"- Low: `{low_count:,}` akun ({low_count/total_users*100:.1f}%)",
                f"- Rule score >= 50: `{rule_high_count:,}` akun ({rule_high_count/total_users*100:.1f}%)",
            ],
            footer="Kalau kamu mau, aku juga bisa jelaskan bedanya angka ground truth, prediksi model, dan rule-based dengan bahasa yang lebih sederhana.",
        )
        return ChatResponse(
            reply=reply,
            data={
                "statistics": {
                    "total_users": total_users,
                    "ground_truth_fake": int(ground_truth_fake),
                    "ground_truth_normal": int(ground_truth_normal),
                    "ml_predicted_fake": int(model_pred_fake),
                    "ml_predicted_normal": int(model_pred_normal),
                    "ml_avg_probability": round(avg_model_prob, 4),
                    "high_risk": int(high_count),
                    "medium_risk": int(med_count),
                    "low_risk": int(low_count),
                    "rule_high": int(rule_high_count),
                }
            }
        )

    def _handle_shared_device_concept(self) -> str:
        return (
            "ðŸ”´ **Shared Device Abuse (Penyalahgunaan Perangkat Bersama)**\n\n"
            "Ini adalah skenario fraud di mana banyak akun (seringkali puluhan) mendaftar dan login dari "
            "satu perangkat fisik yang sama. Pola ini menandakan pendaftaran massal menggunakan emulator "
            "atau bot.\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `max_acc_dev` (jumlah akun maksimum yang berbagi perangkat)\n"
            "- `shared_device_count` (jumlah koneksi berbagi perangkat di graph)"
        )

    def _handle_shared_address_concept(self) -> str:
        return (
            "ðŸ”´ **Shared Address Abuse (Penyalahgunaan Alamat Pengiriman Bersama)**\n\n"
            "Skenario ini terjadi ketika banyak akun melakukan transaksi dengan mengirimkan barang ke "
            "satu alamat pengiriman yang sama atau sangat mirip (shared address ring). Ini biasanya "
            "digunakan untuk menyedot promo/voucher pengguna baru ke satu penimbun.\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `max_acc_addr` (jumlah akun maksimum yang berbagi alamat)\n"
            "- `shared_address_count` (jumlah koneksi berbagi alamat di graph)"
        )

    def _handle_shared_payment_concept(self) -> str:
        return (
            "ðŸ”´ **Shared Payment Abuse (Penyalahgunaan Alat Pembayaran Bersama)**\n\n"
            "Skenario di mana beberapa akun menggunakan kartu kredit, nomor e-wallet, atau rekening bank "
            "yang sama untuk bertransaksi. Ini merupakan indikator kuat adanya satu pelaku yang mengendalikan "
            "banyak akun palsu (Sybil attack) untuk memanfaatkan promo cashback.\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `max_acc_pay` (jumlah akun maksimum yang berbagi metode pembayaran)\n"
            "- `shared_payment_count` (jumlah koneksi berbagi pembayaran di graph)"
        )

    def _handle_referral_ring_concept(self) -> str:
        return (
            "ðŸ”´ **Referral Ring Abuse (Pola Rantai Referal Melingkar)**\n\n"
            "Dalam skenario ini, fraudster membuat akun A, yang mereferensikan akun B, yang mereferensikan C, "
            "dan akhirnya membentuk siklus melingkar kembali ke A untuk mencairkan bonus referral secara ilegal.\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `referral_ring_score` (skor terdeteksinya siklus rujukan)\n"
            "- `referral_count` (jumlah referral yang diajak)"
        )

    def _handle_voucher_farming_concept(self) -> str:
        return (
            "ðŸ”´ **Voucher Farming (Eksploitasi Promo)**\n\n"
            "Akun palsu dibuat secara massal hanya untuk mengklaim voucher belanja (seperti promo pengguna baru atau "
            "gratis ongkir). Akun-akun ini biasanya memiliki `promo_order_ratio` yang sangat mendekati 100% dan langsung "
            "ditinggalkan setelah voucher habis (`days_since_last_login` tinggi).\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `promo_order_ratio` (rasio transaksi dengan voucher)\n"
            "- `new_user_voucher_usage` (penggunaan voucher pengguna baru)\n"
            "- `days_since_last_login` (hari sejak login terakhir)"
        )

    def _handle_default_fallback(self) -> ChatResponse:
        reply = (
            "Halo! Saya adalah **Fraud Assistant**. Saya dapat membantu Anda meneliti jaringan akun palsu "
            "dan mendeteksi pola abuse pada platform.\n\n"
            "Silakan coba tanyakan hal-family berikut:\n"
            "1. ðŸ‘¤ **Informasi User**: *'Kenapa user USR00010 mencurigakan?'* atau *'Detail user USR00048'*.\n"
            "2. ðŸ“ˆ **Top Risk**: *'Tampilkan daftar akun paling mencurigakan (top risk)'*.\n"
            "3. ðŸ” **Statistik**: *'Berapa banyak akun High Risk yang terdeteksi?'*.\n"
            "4. ðŸ”´ **Pola Abuse**: *'Jelaskan tentang shared device abuse'* atau *'Apa itu referral ring?'*."
        )
        return ChatResponse(reply=reply)



import re
import os
from typing import Dict, Any, List, Optional
from app.services.model_service import ModelService
from app.schemas.request_response import ChatResponse

# Try importing groq SDK
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class ChatbotService:
    def __init__(self, model_service: ModelService):
        self.model_service = model_service

    def get_graph_edges(self) -> List[Dict[str, Any]]:
        from app.utils.config import GRAPH_EDGES_PATH
        import json
        if os.path.exists(GRAPH_EDGES_PATH):
            try:
                with open(GRAPH_EDGES_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading graph edges in chatbot: {e}")
        return []

    def get_graph_nodes(self) -> List[Dict[str, Any]]:
        from app.utils.config import GRAPH_NODES_PATH
        import json
        if os.path.exists(GRAPH_NODES_PATH):
            try:
                with open(GRAPH_NODES_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading graph nodes in chatbot: {e}")
        return []

    def process_message(self, message: str) -> ChatResponse:
        msg = message.strip().lower()
        
        # Gather context and structured data for the query
        context_data = ""
        structured_data = None
        fallback_reply = ""

        # Match Device Cluster query first, e.g., "Show fraud cluster related to device DVC001."
        device_match = re.search(r'\b(dvc\d+)\b', msg)
        
        # Match User ID, e.g., "Why is user U001 suspicious?" or "USR00010"
        user_match = re.search(r'\b(?:usr|u)(\d+)\b', msg)

        # 1. Device cluster query
        if device_match:
            dvc_id = device_match.group(1).upper()
            edges = self.get_graph_edges()
            nodes = self.get_graph_nodes()
            
            connected_users = []
            for edge in edges:
                if str(edge.get('target')).upper() == dvc_id or str(edge.get('source')).upper() == dvc_id:
                    other = edge.get('source') if str(edge.get('target')).upper() == dvc_id else edge.get('target')
                    if str(other).upper().startswith('USR'):
                        connected_users.append(other)
            
            user_info = []
            for u in connected_users:
                node_details = next((n for n in nodes if n['id'] == u), None)
                risk = node_details.get('risk_category', 'Low') if node_details else 'Low'
                score = node_details.get('risk_score', 0) if node_details else 0
                user_info.append(f"- 👤 **{u}**: Kategori Risiko **{risk}** (Skor {score}/100)")
            
            fallback_reply = (
                f"### 🕸️ Analisis Klaster Perangkat: **{dvc_id}**\n\n"
                f"Perangkat ini terbagi/digunakan oleh **{len(connected_users)}** akun:\n\n"
            )
            if user_info:
                fallback_reply += "\n".join(user_info)
            else:
                fallback_reply += "*Tidak ada akun pengguna yang terhubung langsung dengan perangkat ini.*"
                
            fallback_reply += (
                f"\n\n**Analisis Risiko:** Jika terdapat beberapa akun berisiko tinggi (High Risk) pada perangkat yang sama, "
                f"ini mengindikasikan adanya modus kecurangan **Device Sharing** (seperti peternakan bot/emulator untuk menyedot promo)."
            )
            context_data = fallback_reply
            structured_data = {"device_id": dvc_id, "connected_users": connected_users}

        # 2. How many fake accounts use emulator / shared device?
        elif "emulator" in msg and ("how many" in msg or "berapa banyak" in msg or "jumlah" in msg):
            df = self.model_service.df_merged
            if df is not None:
                fake_emu = df[(df['fraud'] == 1) & (df['max_acc_dev'] > 2)]
                total_fake = df[df['fraud'] == 1]
                count_fake_emu = len(fake_emu)
                count_total_fake = len(total_fake)
                pct = (count_fake_emu / count_total_fake * 100) if count_total_fake > 0 else 0
                
                fallback_reply = (
                    f"### 📱 Hasil Analisis Penggunaan Emulator:\n\n"
                    f"- **{count_fake_emu}** dari **{count_total_fake}** total akun palsu (*fake accounts*) terdeteksi menggunakan emulator.\n"
                    f"- Rasio Penggunaan Emulator: **{pct:.1f}%** dari total akun palsu.\n\n"
                    f"Penggunaan emulator sangat berkorelasi dengan aktivitas pendaftaran massal otomatis (bot/farming)."
                )
                context_data = fallback_reply
                structured_data = {"count_fake_emulator": count_fake_emu, "total_fake": count_total_fake, "percentage": pct}
            else:
                fallback_reply = "Maaf, data tabel ABT tidak dapat dimuat di memori."

        # 3. Which devices are shared by many accounts?
        elif "device" in msg and ("shared" in msg or "many" in msg or "multiple" in msg or "berbagi" in msg or "paling banyak" in msg):
            edges = self.get_graph_edges()
            device_users = {}
            for edge in edges:
                if edge.get('relationship') == 'uses_device':
                    dvc = edge.get('target')
                    usr = edge.get('source')
                    if dvc not in device_users:
                        device_users[dvc] = set()
                    device_users[dvc].add(usr)
                    
            shared_devices = sorted(device_users.items(), key=lambda x: len(x[1]), reverse=True)
            
            fallback_reply = "### 📱 Daftar Perangkat dengan Jumlah Akun Terbanyak (*Device Sharing*):\n\n"
            for idx, (dvc, usrs) in enumerate(shared_devices[:5], 1):
                fallback_reply += f"{idx}. 🖥️ **{dvc}** - Digunakan oleh **{len(usrs)}** akun unik\n"
                fallback_reply += f"   - Contoh Akun: `{', '.join(list(usrs)[:4])}`"
                if len(usrs) > 4:
                    fallback_reply += " (dan lainnya)"
                fallback_reply += "\n"
            
            fallback_reply += "\nPerangkat yang terhubung dengan lebih dari 2 akun dianggap sangat mencurigakan dan berpotensi digunakan untuk klaster kecurangan."
            context_data = fallback_reply
            structured_data = {"shared_devices": [{d: list(u)} for d, u in shared_devices[:10]]}

        # 4. Which addresses are used by multiple fake accounts?
        elif "address" in msg and ("shared" in msg or "multiple" in msg or "berbagi" in msg or "alamat" in msg or "paling banyak" in msg):
            edges = self.get_graph_edges()
            nodes = self.get_graph_nodes()
            user_risk = {n['id']: n.get('risk_category') for n in nodes if n.get('type') == 'user'}
            
            address_fake_users = {}
            for edge in edges:
                if edge.get('relationship') == 'ships_to_address':
                    adr = edge.get('target')
                    usr = edge.get('source')
                    if user_risk.get(usr) == 'High':
                        if adr not in address_fake_users:
                            address_fake_users[adr] = set()
                        address_fake_users[adr].add(usr)
                        
            shared_addresses = sorted(address_fake_users.items(), key=lambda x: len(x[1]), reverse=True)
            
            fallback_reply = "### 🏠 Alamat Pengiriman yang Paling Sering Digunakan Akun Palsu (High Risk):\n\n"
            for idx, (adr, usrs) in enumerate(shared_addresses[:5], 1):
                fallback_reply += f"{idx}. 📍 **{adr}** - Digunakan oleh **{len(usrs)}** akun palsu berisiko tinggi\n"
                fallback_reply += f"   - Daftar Akun: `{', '.join(list(usrs))}`\n"
            
            fallback_reply += "\nPengiriman massal ke alamat yang sama mengindikasikan modus penimbunan hadiah voucher belanja (*voucher farming*)."
            context_data = fallback_reply
            structured_data = {"shared_addresses": [{a: list(u)} for a, u in shared_addresses[:10]]}

        # 5. What is the most common fraud pattern?
        elif "common" in msg or "pattern" in msg or "pola" in msg or "jenis fraud" in msg:
            df = self.model_service.df_merged
            if df is not None and 'ftype' in df.columns:
                counts = df['ftype'].value_counts().to_dict()
                fallback_reply = "### 🚨 Pola Fraud Paling Umum Terdeteksi (Ground Truth):\n\n"
                for idx, (ftype, count) in enumerate(counts.items(), 1):
                    # Capitalize fraud type
                    f_name = str(ftype).replace('_', ' ').title()
                    fallback_reply += f"{idx}. 🔴 **{f_name}**: **{count}** akun\n"
                fallback_reply += "\nPola kecurangan utama didominasi oleh penyalahgunaan voucher belanja (voucher farming) dan manipulasi tautan rujukan (referral rings)."
                context_data = fallback_reply
                structured_data = {"fraud_patterns": counts}
            else:
                fallback_reply = "Dataframe tidak tersedia."

        # 6. Specific user query (U001 / USR00001)
        elif user_match:
            num = int(user_match.group(1))
            user_id = f"USR{num:05d}"
            details = self.model_service.get_user_details(user_id)
            if details:
                prediction = self.model_service.predict_user(user_id)
                reasons_str = "\n".join([f"- {r}" for r in (prediction.reasons if prediction else [])])
                context_data = (
                    f"User ID: {user_id}\n"
                    f"Full Name: {details.full_name}\n"
                    f"Email: {details.email}\n"
                    f"Phone Number: {details.phone_number}\n"
                    f"Registration Channel: {details.registration_channel}\n"
                    f"City/Province: {details.city}, {details.province}\n"
                    f"Account Status: {details.account_status}\n"
                    f"Risk Category: {details.risk_category}\n"
                    f"Rule-Based Risk Score: {details.risk_score_rule_based}/100\n"
                    f"ML Model Fraud Probability: {details.ml_probability*100:.2f}%\n"
                    f"ML Model Classification: {'FAKE' if details.ml_prediction == 1 else 'NORMAL'}\n"
                    f"Ground Truth (Actual Label): {'FAKE' if details.fraud else 'NORMAL'} (Type: {details.ftype})\n"
                    f"Suspicious Indicators/Reasons:\n{reasons_str}\n"
                )
                structured_data = {"user_details": details.model_dump()}
                fallback_res = self._handle_user_query(user_id)
                fallback_reply = fallback_res.reply
            else:
                context_data = f"User ID {user_id} was not found in our database."
                fallback_reply = f"Maaf, saya tidak dapat menemukan user dengan ID **{user_id}** di database."

        # 7. Top Risk users query (e.g., Show top 10 high risk users)
        elif "top" in msg and ("risk" in msg or "suspicious" in msg or "user" in msg or "akun" in msg):
            num_match = re.search(r'\b(?:top|tampilkan|daftar)\s+(\d+)\b', msg)
            limit = int(num_match.group(1)) if num_match else 5
            limit = max(1, min(limit, 25)) # Clamp to reasonable range
            
            top_risk = self.model_service.get_top_risk_users(limit=limit)
            context_data = f"Top {limit} most suspicious users currently in system:\n"
            for idx, u in enumerate(top_risk.users, 1):
                ml_prob_str = f"{u.ml_probability*100:.1f}% ML Prob" if u.ml_probability is not None else "N/A"
                context_data += f"{idx}. {u.uid} - {u.full_name}: Rule Score {u.risk_score_rule_based}/100, ML: {ml_prob_str}, Ground Truth Type: {u.ftype}\n"
            
            structured_data = {"top_users": [u.model_dump() for u in top_risk.users]}
            
            # Generate custom response
            fallback_reply = f"Berikut adalah **Top {limit} Akun Paling Mencurigakan** berdasarkan analisis ML & Rule-Based:\n\n"
            for idx, u in enumerate(top_risk.users, 1):
                ml_prob_str = f"({u.ml_probability*100:.1f}% ML Prob)" if u.ml_probability is not None else ""
                fallback_reply += (
                    f"{idx}. 🔴 **{u.uid}** - {u.full_name or 'N/A'}\n"
                    f"   - Email: `{u.email or 'N/A'}`\n"
                    f"   - Rule Score: `{u.risk_score_rule_based}/100` | ML: {ml_prob_str}\n"
                    f"   - Tipe Kecurigaan: `{u.ftype or 'N/A'}`\n\n"
                )
            fallback_reply += "Anda bisa mengetik **'Detail [User ID]'** (misalnya `Detail U001`) untuk meneliti detail indikator akun tersebut."
            
        # Check Stats/Count query
        elif ("how many" in msg or "berapa banyak" in msg or "jumlah" in msg) and ("suspicious" in msg or "risk" in msg or "fraud" in msg or "fake" in msg or "mencurigakan" in msg):
            stats_res = self._handle_stats_query()
            if stats_res.data and "statistics" in stats_res.data:
                stats = stats_res.data["statistics"]
                context_data = (
                    f"Overall Fraud Statistics:\n"
                    f"- Total users analyzed: {stats['total_users']}\n"
                    f"- High Risk accounts: {stats['high_risk']} ({stats['high_risk']/stats['total_users']*100:.1f}%)\n"
                    f"- Medium Risk accounts: {stats['medium_risk']} ({stats['medium_risk']/stats['total_users']*100:.1f}%)\n"
                    f"- Low Risk accounts: {stats['low_risk']} ({stats['low_risk']/stats['total_users']*100:.1f}%)\n"
                    f"- Ground Truth Actual Fakes: {stats['ground_truth_fake']}\n"
                    f"- Ground Truth Actual Normals: {stats['ground_truth_normal']}\n"
                    f"- ML Model Predicted Fakes: {stats['ml_predicted_fake']}\n"
                )
                structured_data = stats_res.data
            fallback_reply = stats_res.reply
            
        # Check Shared Device
        elif "shared device" in msg or "device sharing" in msg or "berbagi hp" in msg or "perangkat sama" in msg:
            context_data = (
                "Concept: Shared Device Abuse occurs when multiple accounts register/login from the same physical device "
                "fingerprint. It is key for detecting botnets/emulators."
            )
            fallback_reply = self._handle_shared_device_concept()
            
        # Check Shared Address
        elif "shared address" in msg or "address sharing" in msg or "berbagi alamat" in msg or "alamat sama" in msg:
            context_data = (
                "Concept: Shared Address Abuse occurs when many accounts ship to identical addresses or address groups. "
                "Often used by voucher penimbun to direct all purchases to one warehouse."
            )
            fallback_reply = self._handle_shared_address_concept()
            
        # Check Shared Payment
        elif "shared payment" in msg or "payment sharing" in msg or "kartu sama" in msg or "rekening sama" in msg:
            context_data = (
                "Concept: Shared Payment Abuse occurs when multiple accounts share payment instruments (credit cards, bank numbers, "
                "e-wallets), indicating a single controller running a Sybil campaign."
            )
            fallback_reply = self._handle_shared_payment_concept()
            
        # Check Referral Ring
        elif "referral" in msg or "referral ring" in msg or "circular referral" in msg:
            context_data = (
                "Concept: Referral Ring Abuse occurs when circular referral patterns (A invites B invites C invites A) "
                "are set up to harvest referral commissions."
            )
            fallback_reply = self._handle_referral_ring_concept()
            
        # Check Voucher Farming
        elif "voucher" in msg or "promo" in msg or "farming" in msg:
            context_data = (
                "Concept: Voucher Farming occurs when users register multiple accounts solely to claim new user vouchers/cashbacks, "
                "characterized by high promo_order_ratio, new user promo usage, and dormancy afterward."
            )
            fallback_reply = self._handle_voucher_farming_concept()
            
        else:
            # Default General context
            context_data = (
                "General: The project is a Fraud & Fake Account Detection Prototype. "
                "Best ML model trained is Logistic Regression (99.83% F1 score), closely followed by Random Forest (99.78% F1) and XGBoost. "
                "Feature engineering includes network graph properties (degree, clustering size) computed via NetworkX."
            )
            fallback_res = self._handle_default_fallback()
            fallback_reply = fallback_res.reply
            structured_data = fallback_res.data

        # 2. Query Groq API if key is available
        groq_api_key = os.getenv("GROQ_API_KEY")
        if GROQ_AVAILABLE and groq_api_key:
            try:
                client = Groq(api_key=groq_api_key)
                
                system_prompt = (
                    "You are a helpful Fraud Analyst Assistant on a platform that detects fake accounts and promo abuse "
                    "(like shared devices, shared addresses, shared payments, referral rings, and voucher farming).\n"
                    "Your job is to analyze accounts and answer user queries professionally in Indonesian.\n"
                    "Use the provided context data to answer the user's question. If the user asks about a specific user, "
                    "explain their suspicious indicators and risk category clearly based on the context reasons.\n"
                    "Do not make up facts or user data. Speak naturally, professionally, and clearly. Format your output nicely using markdown."
                )
                
                user_content = f"Context data:\n{context_data}\n\nUser Question: {message}"
                
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    model="llama-3.1-8b-instant",  # Standard high-speed Groq model
                    temperature=0.2,
                    max_tokens=1000
                )
                
                llm_reply = chat_completion.choices[0].message.content.strip()
                return ChatResponse(reply=llm_reply, data=structured_data)
                
            except Exception as e:
                print(f"Error calling Groq API: {e}. Falling back to rule-based response.")
                # Fallback on exception
                return ChatResponse(reply=fallback_reply, data=structured_data)
                
        # 3. Fallback to rule-based if Groq not available/configured
        return ChatResponse(reply=fallback_reply, data=structured_data)

    # --- Fallback Generators ---
    def _handle_user_query(self, user_id: str) -> ChatResponse:
        details = self.model_service.get_user_details(user_id)
        if not details:
            return ChatResponse(reply=f"Maaf, user {user_id} tidak ditemukan.")
            
        prediction = self.model_service.predict_user(user_id)
        risk_color = "🔴" if details.risk_category == "High" else "🟡" if details.risk_category == "Medium" else "🟢"
        
        reply = (
            f"### Detail Analisis Fraud: **{user_id}**\n"
            f"👤 **Nama**: {details.full_name or 'N/A'}\n"
            f"📧 **Email**: `{details.email or 'N/A'}`\n"
            f"📍 **Lokasi**: {details.city or 'N/A'}, {details.province or 'N/A'}\n\n"
            f"--- \n\n"
            f"### 🛡️ Status Risiko:\n"
            f"- **Kategori Risiko**: {risk_color} **{details.risk_category}**\n"
            f"- **Skor Berbasis Aturan (Rule-Based)**: `{details.risk_score_rule_based}/100`\n"
        )
        
        if details.ml_probability is not None:
            reply += f"- **Probabilitas Machine Learning**: `{details.ml_probability*100:.2f}%`\n"
            ml_pred_str = "FAKE ACCOUNT 🚨" if details.ml_prediction == 1 else "NORMAL ACCOUNT ✅"
            reply += f"- **Klasifikasi ML**: **{ml_pred_str}**\n"

        if details.fraud is not None:
            ground_truth = "FAKE ACCOUNT 🔴" if details.fraud else "NORMAL ACCOUNT 🟢"
            reply += f"- **Label Asli (Ground Truth)**: **{ground_truth}** (Tipe: `{details.ftype or 'normal'}`)\n"

        reply += "\n### 🚨 Indikator Kecurigaan Utama:\n"
        if prediction and prediction.reasons:
            for r in prediction.reasons:
                reply += f"- {r}\n"
        else:
            reply += "- Tidak ada indikator kecurigaan utama yang signifikan (akun terlihat normal).\n"

        return ChatResponse(reply=reply, data={"user_details": details.model_dump()})

    def _handle_top_risk_query(self) -> ChatResponse:
        top_risk = self.model_service.get_top_risk_users(limit=5)
        reply = "Berikut adalah **Top 5 Akun Paling Mencurigakan** berdasarkan analisis gabungan ML & Rule-Based:\n\n"
        
        for idx, u in enumerate(top_risk.users, 1):
            ml_prob_str = f"({u.ml_probability*100:.1f}% ML Prob)" if u.ml_probability is not None else ""
            reply += (
                f"{idx}. 🔴 **{u.uid}** - {u.full_name or 'N/A'}\n"
                f"   - Email: `{u.email or 'N/A'}`\n"
                f"   - Rule Score: `{u.risk_score_rule_based}/100` | ML: {ml_prob_str}\n"
                f"   - Tipe Kecurigaan: `{u.ftype or 'N/A'}`\n\n"
            )
        reply += "Anda bisa mengetik **'Detail [User ID]'** untuk membedah riwayat indikator lengkap dari user tersebut."
        return ChatResponse(reply=reply, data={"top_users": [u.model_dump() for u in top_risk.users]})

    def _handle_stats_query(self) -> ChatResponse:
        df = self.model_service.df_merged
        total_users = len(df)
        categories = df['risk_category'].value_counts().to_dict()
        high_count = categories.get('High', 0)
        med_count = categories.get('Medium', 0)
        low_count = categories.get('Low', 0)
        
        fake_counts = df['fraud'].value_counts().to_dict()
        total_fake = fake_counts.get(1, 0)
        total_normal = fake_counts.get(0, 0)

        ml_fake = df['ml_prediction'].value_counts().to_dict().get(1, 0) if 'ml_prediction' in df.columns else 0
        
        reply = (
            f"### 📊 Statistik Deteksi Akun Palsu:\n\n"
            f"Total Pengguna Teranalisis: **{total_users:,}**\n\n"
            f"**🛡️ Kategori Risiko (Rule-Based):**\n"
            f"- 🔴 **High Risk**: `{high_count:,}` akun ({high_count/total_users*100:.1f}%)\n"
            f"- 🟡 **Medium Risk**: `{med_count:,}` akun ({med_count/total_users*100:.1f}%)\n"
            f"- 🟢 **Low Risk**: `{low_count:,}` akun ({low_count/total_users*100:.1f}%)\n\n"
            f"**🧬 Hasil Ground Truth Dataset:**\n"
            f"- 🔴 **Total Akun Palsu (Fake)**: `{total_fake:,}` akun\n"
            f"- 🟢 **Total Akun Normal**: `{total_normal:,}` akun\n\n"
        )
        if ml_fake > 0:
            reply += (
                f"**🤖 Hasil Klasifikasi Model ML:**\n"
                f"- 🚨 **Prediksi Fake**: `{ml_fake:,}` akun\n"
                f"- ✅ **Prediksi Normal**: `{total_users - ml_fake:,}` akun\n"
            )
        return ChatResponse(
            reply=reply, 
            data={
                "statistics": {
                    "total_users": total_users,
                    "high_risk": int(high_count),
                    "medium_risk": int(med_count),
                    "low_risk": int(low_count),
                    "ground_truth_fake": int(total_fake),
                    "ground_truth_normal": int(total_normal),
                    "ml_predicted_fake": int(ml_fake)
                }
            }
        )

    def _handle_shared_device_concept(self) -> str:
        return (
            "🔴 **Shared Device Abuse (Penyalahgunaan Perangkat Bersama)**\n\n"
            "Ini adalah skenario fraud di mana banyak akun (seringkali puluhan) mendaftar dan login dari "
            "satu perangkat fisik yang sama. Pola ini menandakan pendaftaran massal menggunakan emulator "
            "atau bot.\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `accounts_per_device_max` (jumlah akun per perangkat)\n"
            "- `is_emulator_used` (deteksi penggunaan emulator)"
        )

    def _handle_shared_address_concept(self) -> str:
        return (
            "🔴 **Shared Address Abuse (Penyalahgunaan Alamat Pengiriman Bersama)**\n\n"
            "Skenario ini terjadi ketika banyak akun melakukan transaksi dengan mengirimkan barang ke "
            "satu alamat pengiriman yang sama atau sangat mirip (shared address ring). Ini biasanya "
            "digunakan untuk menyedot promo/voucher pengguna baru ke satu penimbun.\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `accounts_per_address_max` (jumlah akun per kelompok alamat)\n"
            "- `address_reuse_flag` (apakah alamat digunakan bersama)"
        )

    def _handle_shared_payment_concept(self) -> str:
        return (
            "🔴 **Shared Payment Abuse (Penyalahgunaan Alat Pembayaran Bersama)**\n\n"
            "Skenario di mana beberapa akun menggunakan kartu kredit, nomor e-wallet, atau rekening bank "
            "yang sama untuk bertransaksi. Ini merupakan indikator kuat adanya satu pelaku yang mengendalikan "
            "banyak akun palsu (Sybil attack) untuk memanfaatkan promo cashback.\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `accounts_per_payment_max` (jumlah akun per alat pembayaran)\n"
            "- `payment_reuse_flag` (apakah instrumen pembayaran digunakan kembali)"
        )

    def _handle_referral_ring_concept(self) -> str:
        return (
            "🔴 **Referral Ring Abuse (Pola Rantai Referal Melingkar)**\n\n"
            "Dalam skenario ini, fraudster membuat akun A, yang mereferensikan akun B, yang mereferensikan C, "
            "dan akhirnya membentuk siklus melingkar kembali ke A untuk mencairkan bonus referral secara ilegal.\n\n"
            "**Fitur Deteksi Utama:**\n"
            "- `referral_ring_score` (skor terdeteksinya siklus rujukan)\n"
            "- `referral_count` (jumlah referral yang diajak)"
        )

    def _handle_voucher_farming_concept(self) -> str:
        return (
            "🔴 **Voucher Farming (Eksploitasi Promo)**\n\n"
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
            "1. 👤 **Informasi User**: *'Kenapa user USR00010 mencurigakan?'* atau *'Detail user USR00048'*.\n"
            "2. 📈 **Top Risk**: *'Tampilkan daftar akun paling mencurigakan (top risk)'*.\n"
            "3. 🔍 **Statistik**: *'Berapa banyak akun High Risk yang terdeteksi?'*.\n"
            "4. 🔴 **Pola Abuse**: *'Jelaskan tentang shared device abuse'* atau *'Apa itu referral ring?'*."
        )
        return ChatResponse(reply=reply)

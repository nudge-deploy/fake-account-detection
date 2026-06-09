<!--
Purpose: Main project entry point with overview, run instructions, and documentation links.
Used by: Developers, reviewers, and contributors working on the fraud detection prototype.
Main dependencies: Python scripts, FastAPI backend, Next.js frontend, Supabase, and model artifacts.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Fake Account Detection Retail App Prototype

Prototype ini menggabungkan synthetic data generation, graph analytics, machine learning, dan chatbot hybrid untuk mendeteksi fake account, voucher abuse, dan fraud ring di retail e-commerce mobile.

## Summary
- **Data layer:** menghasilkan raw CSV dan ABT untuk training serta inference.
- **Graph layer:** membangun relasi user-entity dan fitur graph untuk deteksi pola jaringan.
- **Model layer:** melatih model ML dan menyimpan artefak `.pkl` / `.json`.
- **Backend:** FastAPI untuk endpoint prediksi, graph, dan chatbot.
- **Frontend:** Next.js dashboard untuk analisis risiko dan visualisasi graph.

## Folder Structure
```text
.
|-- backend/     FastAPI app, services, and API routes
|-- data/        Raw data, processed graph data, and ABT
|-- docs/        Documentation and design notes
|-- frontend/    Next.js dashboard
|-- models/      Trained model artifacts and feature metadata
|-- notebooks/   Analysis notebooks
|-- scripts/     Data generation, feature engineering, graph, and training scripts
```

## Data Sources
- `users.csv`: identitas akun
- `devices.csv`, `addresses.csv`, `payments.csv`: entity yang bisa dipakai bersama
- `transactions.csv`, `vouchers.csv`: aktivitas transaksi dan voucher
- `login_sessions.csv`: pola login dan frekuensi
- `referrals.csv`: relasi referral dan siklus jaringan
- `fraud_labels.csv`: label target untuk supervised learning

## How to Generate Synthetic Data
To simulate a realistic retail environment with standard users and automated bot attacks, run the synthetic data generator script. This will populate the `data/raw/` folder with multiple relational tables.
```bash
python scripts/generate_data.py
```

## How to Build Analytics Base Table
After generating the raw data and graph edge tables, you must extract the necessary network features and build the final Analytical Base Table (ABT) which will be used for model training.
```bash
python scripts/build_graph.py
python scripts/extract_graph_features.py
python scripts/build_abt.py
python scripts/export_graph_api.py
```

## How to Train Model
Train the machine learning models, resolve data leakages, and export the Champion Model metrics, feature lists, and pickle files:
```bash
python scripts/train_model.py
```

## How to Run API
Navigate to the backend directory, install requirements, and start the FastAPI modular server:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
*Note: Ensure you have python 3.9+ installed and a `.env` configured if necessary.*

## How to Run Frontend
Navigate to the frontend directory, install dependencies, and start the Next.js development server:
```bash
cd frontend
npm install
npm run dev
```
*Note: The frontend dashboard will be accessible at `http://localhost:3000`.*

## How to Deploy to Vercel
1. Push the entire project to a GitHub repository.
2. Log in to Vercel and import the repository.
3. Configure the **Root Directory** to `frontend`.
4. The **Framework Preset** will automatically detect Next.js.
5. Add the necessary Environment Variables (e.g., `NEXT_PUBLIC_API_URL` pointing to your deployed Render backend URL).
6. Click **Deploy**.

## API Documentation
When the FastAPI backend is running locally, visit the interactive Swagger UI for full endpoint testing:
- **URL:** `http://localhost:8000/docs`

Available REST Endpoints:
- `GET /health` : System health check.
- `GET /api/stats/overview` : Dashboard top-level stats.
- `POST /api/predict` : Single user manual inference.
- `GET /api/users` : Retrieve paginated risk-scoring list.
- `GET /api/user/{uid}` : Get detailed risk profile.
- `GET /api/graph` : Fetch network visualization data.
- `POST /api/chat` : Chatbot interface.

## Documentation Index
The main documentation index lives in:
- [docs/README.md](./docs/README.md)

Useful deep-dive docs:
- [docs/05_feature_engineering.md](./docs/05_feature_engineering.md)
- [docs/chatbot_query_data_source.md](./docs/chatbot_query_data_source.md)

## Example Inference
You can test the manual prediction endpoint using `curl` or Postman:
```bash
curl -X POST "http://localhost:8000/api/predict" \
     -H "Content-Type: application/json" \
     -d '{
           "features": {
             "max_acc_dev": 8,
             "max_acc_pay": 3,
             "max_acc_addr": 5,
             "promo_ratio": 0.9,
             "login_v1h": 5,
             "login_v24h": 20,
             "reg2txn_min": 10
           }
         }'
```

## Graph Analytics Explanation
The graph network creates an edge (connection) between any two users who share identical Device IDs, IP Addresses, Payment methods, or Shipping Addresses. By calculating metrics like cluster sizes (`connected_component_size`) and node connections (`graph_degree`), the system visually and mathematically isolates highly organized **fraud rings** that traditional tabular ML might fail to detect.

## Chatbot Usage
The dashboard includes a dedicated AI Assistant tab.
- **LLM Mode (Advanced):** Supply a `GROQ_API_KEY` in the backend `.env` file to use LLaMA-3.1. This allows for deep, contextual, and dynamic Q&A about fraud patterns.
- **Rule-Based Mode (Fallback):** If no API key is provided, the chatbot seamlessly falls back to a regex-based parser. It can answer fixed-format questions like *"Why is user U001 suspicious?"* by directly parsing rules and ABT values.

## Future Improvements
- **Database Migration:** Transition from static CSV stores to a robust relational database (e.g., PostgreSQL).
- **Graph Database Integration:** Implement a real-time Graph Database (e.g., Neo4j) to calculate network features instantaneously without holding the entire graph in RAM.
- **Streaming Pipeline:** Integrate Apache Kafka or AWS Kinesis to enable real-time streaming ML predictions on every incoming login/transaction event.

## Notes
- Pastikan file model dan data hasil generate sudah tersedia sebelum menjalankan backend.
- Jika ingin membaca detail feature engineering, buka `docs/05_feature_engineering.md`.

## Demo
Live demo frontend tersedia di:
- [https://fake-acccount-detection.vercel.app](https://fake-acccount-detection.vercel.app)

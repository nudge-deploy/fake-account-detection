<!--
Purpose: Project overview and local development workflow.
Used by: Developers running the data, backend, and frontend pipeline.
Main dependencies: Python scripts, FastAPI backend, Next.js frontend, Supabase schema.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Fake Account Detection Retail App Prototype

## Objective
To build a prototype machine learning and rule-based hybrid system capable of detecting fake accounts, voucher abusers, and organized fraud rings in a mobile retail e-commerce ecosystem.

## Features
- **Synthetic Data Generation:** Simulates realistic e-commerce traffic and fraudulent behaviors.
- **Graph Network Analytics:** Identifies shared entities (Fraud Rings) through NetworkX.
- **Machine Learning Pipeline:** Trains predictive models (Logistic Regression, Random Forest, XGBoost).
- **Dual-Layer Inference:** Combines ML Probabilities with Rule-Based Scoring logic.
- **FastAPI Backend:** Serves high-performance REST endpoints and acts as an LLM bridge.
- **Next.js Dashboard:** Premium dark-mode UI with Tailwind CSS and `react-force-graph-2d`.
- **Hybrid AI Chatbot:** Utilizes LLaMA-3.1 (via Groq) for conversational analytics, with a fully functional Rule-Based/Regex fallback system.

## Architecture
- **Data Layer:** Python scripts generating raw CSVs and transforming them into an Analytical Base Table (ABT).
- **Model Layer:** Scikit-learn algorithms coupled with standard scalers, exporting artifacts (`.pkl` and `.json`).
- **Backend API:** Built on FastAPI (Python) for robust, async model inference and data serving.
- **Frontend Dashboard:** Built on React and Next.js, handling state management, metrics display, and dynamic graph rendering.

## Folder Structure
```text
.
├── backend/            # FastAPI application and service logic
├── data/               # Raw relational CSVs and generated datasets (ABT)
├── docs/               # Documentation and analytical plots/images
├── frontend/           # Next.js web application dashboard
├── models/             # Trained machine learning model artifacts (.pkl, .json)
├── notebooks/          # Jupyter notebooks for interactive analysis and EDA
├── scripts/            # Python scripts for data generation and ML training
```

## Dataset Description
The dataset simulates 10,000 user accounts with features distributed across multiple tables:
- `users.csv`: Core identity (Email, Phone, Registration).
- `devices.csv`, `addresses.csv`, `payments.csv`: Connected physical and financial entities.
- `transactions.csv`, `vouchers.csv`: E-commerce purchasing activity.
- `login_sessions.csv`: Login frequency buckets from 00:00, persona timing, and network IP activity.
- `referrals.csv`: Referral chains and cyclical rings.
- `fraud_labels.csv`: Ground truth labels for supervised learning.

## Running the Full Pipeline

If you want to regenerate all artifacts from scratch, keep this order. The ABT is the final training table and contains raw-derived features plus per-user aggregate graph features.

```bash
# 1. Generate Raw Data
python scripts/generate_data.py

# 2. Generate Graph CSV for feature extraction
python scripts/build_graph.py

# 3. Extract Graph Features
python scripts/extract_graph_features.py

# 4. Build final ABT
python scripts/build_abt.py

# 5. Generate Graph JSON for API/Frontend
python scripts/export_graph_api.py

# 6. Train Model
python scripts/train_model.py

# 7. Upload current CSV/ABT data to Supabase
python scripts/upload_to_supabase.py
```

## How to Train Model
Train the machine learning models, resolve data leakages, and export the Champion Model:
```bash
python scripts/train_model.py
```

## How to Run API
Navigate to the backend directory, install requirements, and start the FastAPI server:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
*Note: Ensure you have python 3.9+ installed.*

## How to Run Frontend
Navigate to the frontend directory, install dependencies, and start the Next.js development server:
```bash
cd frontend
npm install
npm run dev
```
*Note: The frontend will be accessible at `http://localhost:3000`.*

## How to Deploy to Vercel
1. Push the entire project (or specifically the `frontend/` directory) to a GitHub repository.
2. Log in to Vercel and import the repository.
3. Configure the **Root Directory** to `frontend`.
4. Add the necessary Environment Variables (e.g., `NEXT_PUBLIC_API_URL` pointing to your deployed backend URL).
5. Click **Deploy**. Vercel will automatically detect the Next.js framework and build the project.

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

## Data Lineage Documentation
For the full relation between source tables, joins, feature outputs, graph outputs, and abbreviation meanings, see:
- `docs/Feature_Source_Join_Mapping.md`

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

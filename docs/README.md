<!--
Purpose: Documentation index for the fraud detection project.
Used by: Developers, reviewers, and report writers looking for project docs.
-->

# Documentation Index

| # | Dokumen | Isi |
|---|---------|-----|
| 01 | `01_mobile_app_exploration.md` | Konteks aplikasi Alfagift dan pola fraud yang dipetakan |
| 02 | `02_data_model_design.md` | Desain 14 tabel raw + ABT dan relasinya |
| 03 | `03_synthetic_data_generation.md` | Cara generate 10.000 user dengan noise realistis |
| 04 | `04_eda_report.md` | Ringkasan EDA dan distribusi label |
| 05 | `05_feature_engineering.md` | 64 fitur model: formula, business meaning, contoh nilai |
| 06 | `06_graph_analytics.md` | Graph fraud ring detection, ego-network BFS, graph features |
| 07 | `07_modeling_report.md` | Training XGBoost (F1=94.52%) & Logistic Regression (F1=98.69%) |
| 08 | `08_inference_model_selection.md` | Perbedaan jalur inference new user vs existing user |
| 09 | `09_inference_workflow.md` | Alur detail dari payload event ke output prediksi |
| 10 | `10_api_documentation.md` | Semua endpoint FastAPI + contoh request/response |
| 11 | `11_chatbot_design.md` | Arsitektur chatbot hybrid Groq + fallback rule-based |
| 12 | `12_chatbot_query_sources.md` | Mapping intent chatbot ke sumber data (ModelService/GraphService) |
| 13 | `13_deployment_guide.md` | Deploy: VPS + Docker + Nginx + SSL + Vercel |
| 14 | `14_data_dictionary.md` | Dictionary semua kolom tabel raw dan ABT |
| — | `SYSTEM_DOCUMENTATION.md` | **Dokumen terpadu** — ringkasan seluruh pipeline end-to-end |

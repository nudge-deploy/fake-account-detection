<!--
Purpose: Documentation index for the fraud detection project.
Used by: Developers and reviewers looking for data, model, API, and lineage docs.
Main dependencies: Markdown files in docs/.
Public/main functions: N/A documentation only.
Side effects: None.
-->

# Documentation Index

Dokumen utama project:

| Dokumen | Isi |
|---|---|
| `01_mobile_app_exploration.md` | Eksplorasi konteks mobile retail app dan skenario fraud. |
| `02_data_model_design.md` | Desain data model dan relasi tabel raw. |
| `03_synthetic_data_generation.md` | Proses generate synthetic data. |
| `04_eda_report.md` | Ringkasan EDA dan insight data. |
| `06_modeling_report.md` | Ringkasan training, evaluasi model, dan artifact model. |
| `07_system_architecture_and_api.md` | Arsitektur backend/frontend dan API. |
| `ABT_Processing_Flow.md` | Urutan pemrosesan ABT dari raw data sampai fitur final. |
| `Feature_Engineering_Documentation.md` | Definisi fitur dan logika feature engineering. |
| `Feature_Lineage_Documentation.md` | Lineage fitur dari source menuju ABT/model. |
| `Feature_Source_Join_Mapping.md` | Mapping source table, join/agregasi, output fitur, graph, dan daftar singkatan. |

Catatan kontrak terbaru:

- ABT final berisi raw-derived features + aggregate graph features.
- Login bucket memakai `login_v*`, dihitung sebagai frequency dari `00:00` sampai batas jam bucket harian.
- Graph API memakai `build_graph.py` untuk CSV dan `export_graph_api.py` untuk JSON frontend/API.

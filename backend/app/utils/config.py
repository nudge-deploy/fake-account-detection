"""
Purpose: Resolve project paths and environment-based artifact locations for backend services.
Used by: backend APIs, inference services, model loaders, and data pipelines.
Main dependencies: .env values, project root path resolution.
Public/main functions: resolve_path and module-level constants for model/data paths.
Side effects: Loads environment variables and prints resolved config paths at import time.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# BASE_DIR = project root (fake-account-detection/)
# __file__ is backend/app/utils/config.py → go up 4 levels
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def resolve_path(env_key, default_rel_path):
    val = os.getenv(env_key)
    if val:
        if os.path.isabs(val):
            return val
        return os.path.abspath(os.path.join(BASE_DIR, val))
    return os.path.abspath(os.path.join(BASE_DIR, default_rel_path))


# --- Model artifacts ---
# New customer model: models/new_customer/
NEW_USER_MODEL_PATH = resolve_path(
    'NEW_USER_MODEL_PATH', 'models/new_customer/model.pkl'
)
NEW_USER_FEATURE_COLUMNS_PATH = resolve_path(
    'NEW_USER_FEATURE_COLUMNS_PATH', 'models/new_customer/feature_columns.json'
)

# Existing customer model: models/existing_customer/
EXISTING_USER_MODEL_PATH = resolve_path(
    'EXISTING_USER_MODEL_PATH', 'models/existing_customer/model.pkl'
)
FEATURE_COLUMNS_PATH = resolve_path(
    'FEATURE_COLUMNS_PATH', 'models/existing_customer/feature_columns.json'
)

# --- Data artifacts ---
ABT_PATH = resolve_path('ABT_PATH', 'data/abt/fake_account_abt.csv')
GRAPH_NODES_PATH = resolve_path('GRAPH_NODES_PATH', 'data/processed/graph_nodes.json')
GRAPH_EDGES_PATH = resolve_path('GRAPH_EDGES_PATH', 'data/processed/graph_edges.csv')
USERS_CSV_PATH = resolve_path('USERS_CSV_PATH', 'data/raw/users.csv')

if __name__ != "__main__":
    print("Config loaded:")
    print(f"  NEW_USER_MODEL_PATH:           {NEW_USER_MODEL_PATH}")
    print(f"  NEW_USER_FEATURE_COLUMNS_PATH: {NEW_USER_FEATURE_COLUMNS_PATH}")
    print(f"  EXISTING_USER_MODEL_PATH:      {EXISTING_USER_MODEL_PATH}")
    print(f"  FEATURE_COLUMNS_PATH:          {FEATURE_COLUMNS_PATH}")
    print(f"  ABT_PATH:                      {ABT_PATH}")
    print(f"  GRAPH_NODES_PATH:              {GRAPH_NODES_PATH}")
    print(f"  GRAPH_EDGES_PATH:              {GRAPH_EDGES_PATH}")
    print(f"  USERS_CSV_PATH:                {USERS_CSV_PATH}")

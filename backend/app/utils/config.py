"""
Purpose: Resolve project paths and environment-based artifact locations for backend services.
Used by: backend APIs, inference services, model loaders, and data pipelines.
Main dependencies: .env values, project root path resolution.
Public/main functions: resolve_path and module-level constants for model/data paths.
Side effects: Loads environment variables and prints resolved config paths at import time.
"""

import os
from dotenv import load_dotenv

# Load root .env file if it exists
load_dotenv()

# Base directory represents the root of the project (i.e. 'fraud detection & abuse')
# __file__ is in 'backend/app/utils/config.py', so going up 3 levels reaches root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def resolve_path(env_key, default_rel_path):
    val = os.getenv(env_key)
    if val:
        # If absolute path, use it directly
        if os.path.isabs(val):
            return val
        # Otherwise, resolve relative to root
        return os.path.abspath(os.path.join(BASE_DIR, val))
    return os.path.abspath(os.path.join(BASE_DIR, default_rel_path))

MODEL_PATH = resolve_path('MODEL_PATH', 'models/fake_account_model.pkl')
NEW_USER_MODEL_PATH = resolve_path('NEW_USER_MODEL_PATH', 'models/fake_account_model_new_user.pkl')
EXISTING_USER_MODEL_PATH = resolve_path('EXISTING_USER_MODEL_PATH', 'models/fake_account_model_existing_user.pkl')
FEATURE_COLUMNS_PATH = resolve_path('FEATURE_COLUMNS_PATH', 'models/feature_columns.json')
NEW_USER_FEATURE_COLUMNS_PATH = resolve_path('NEW_USER_FEATURE_COLUMNS_PATH', 'models/feature_columns_new_user.json')
GRAPH_NODES_PATH = resolve_path('GRAPH_NODES_PATH', 'data/processed/graph_nodes.json')
GRAPH_EDGES_PATH = resolve_path('GRAPH_EDGES_PATH', 'data/processed/graph_edges.csv')
ABT_PATH = resolve_path('ABT_PATH', 'data/abt/fake_account_abt.csv')
USERS_CSV_PATH = resolve_path('USERS_CSV_PATH', 'data/raw/users.csv')

print("Config loaded:")
print(f"  MODEL_PATH: {MODEL_PATH}")
print(f"  NEW_USER_MODEL_PATH: {NEW_USER_MODEL_PATH}")
print(f"  EXISTING_USER_MODEL_PATH: {EXISTING_USER_MODEL_PATH}")
print(f"  FEATURE_COLUMNS_PATH: {FEATURE_COLUMNS_PATH}")
print(f"  NEW_USER_FEATURE_COLUMNS_PATH: {NEW_USER_FEATURE_COLUMNS_PATH}")
print(f"  GRAPH_NODES_PATH: {GRAPH_NODES_PATH}")
print(f"  GRAPH_EDGES_PATH: {GRAPH_EDGES_PATH}")
print(f"  ABT_PATH: {ABT_PATH}")
print(f"  USERS_CSV_PATH: {USERS_CSV_PATH}")

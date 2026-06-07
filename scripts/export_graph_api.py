"""Purpose: Export JSON artifacts for API Visualization from existing CSVs.
Used by: Frontend Dashboard
"""

import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ABT_PATH = os.path.join(BASE_DIR, "data", "abt", "fake_account_abt.csv")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
NODES_CSV_PATH = os.path.join(PROCESSED_DIR, "graph_nodes.csv")
EDGES_CSV_PATH = os.path.join(PROCESSED_DIR, "graph_edges.csv")
NODES_JSON_PATH = os.path.join(PROCESSED_DIR, "graph_nodes.json")
EDGES_JSON_PATH = os.path.join(PROCESSED_DIR, "graph_edges.json")

def node_label(node_id: str, node_type: str) -> str:
    if node_type == "user":
        return node_id
    return f"{node_type.title()} {node_id}"

def load_user_metadata() -> dict:
    if not os.path.exists(ABT_PATH):
        return {}

    df_abt = pd.read_csv(ABT_PATH)
    metadata = {}
    for _, row in df_abt.iterrows():
        uid = row.get("uid")
        if pd.isna(uid):
            continue
        metadata[str(uid)] = {
            "risk_score": int(row.get("risk_score", 0)) if not pd.isna(row.get("risk_score", 0)) else 0,
            "risk_category": row.get("risk_cat") if not pd.isna(row.get("risk_cat")) else "Low",
            "ftype": row.get("ftype") if not pd.isna(row.get("ftype")) else None,
        }
    return metadata

def export_graph_api():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    if not os.path.exists(NODES_CSV_PATH) or not os.path.exists(EDGES_CSV_PATH):
        print("Error: graph_nodes.csv or graph_edges.csv not found. Run build_graph.py first.")
        return

    df_nodes = pd.read_csv(NODES_CSV_PATH)
    df_edges = pd.read_csv(EDGES_CSV_PATH)
    user_metadata = load_user_metadata()

    nodes = []
    for _, row in df_nodes.iterrows():
        node_id = row["node_id"]
        node_type = row["node_type"]
        node = {
            "id": node_id,
            "label": node_label(node_id, node_type),
            "type": node_type,
        }
        if node_type == "user":
            node.update(user_metadata.get(node_id, {
                "risk_score": 0,
                "risk_category": "Low",
                "ftype": None,
            }))
        nodes.append(node)

    edges = [
        {
            "source": row["source"],
            "target": row["target"],
            "relationship": row["edge_type"],
        }
        for _, row in df_edges.iterrows()
    ]

    with open(NODES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False)

    with open(EDGES_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(edges, f, ensure_ascii=False)

    print(f"Graph API nodes: {len(nodes)}")
    print(f"Graph API edges: {len(edges)}")
    print("Graph API JSON data saved")

if __name__ == "__main__":
    export_graph_api()

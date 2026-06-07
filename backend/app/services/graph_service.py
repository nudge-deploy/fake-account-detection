"""Purpose: Load and filter graph artifacts for API graph responses.
Used by: graph API router, prediction API user detail enrichment, chatbot service.
Depends on: graph_nodes.json, graph_edges.csv/json, fraud_labels.csv, response schemas.
Public functions: GraphService.load_graph_data, build_adjacency, get_graph_data.
Side effects: Reads graph/data files into memory at service startup.
"""

import os
import json
from typing import Dict, Any, List, Optional
from app.utils.config import GRAPH_NODES_PATH, GRAPH_EDGES_PATH
from app.schemas.request_response import GraphNode, GraphEdge, GraphDataResponse

class GraphService:
    def __init__(self):
        self.raw_nodes = []
        self.raw_edges = []
        self.nodes_dict = {}
        self.adj_list = {}
        self.load_graph_data()

    def load_graph_data(self):
        # 1. Load Nodes
        if os.path.exists(GRAPH_NODES_PATH):
            try:
                with open(GRAPH_NODES_PATH, 'r', encoding='utf-8') as f:
                    self.raw_nodes = json.load(f)
                self.nodes_dict = {n['id']: n for n in self.raw_nodes}
                print(f"Successfully loaded {len(self.raw_nodes)} graph nodes.")
            except Exception as e:
                print(f"Error loading graph nodes from {GRAPH_NODES_PATH}: {e}")
        else:
            print(f"Graph nodes file does not exist: {GRAPH_NODES_PATH}")

        # 2. Load Edges
        if os.path.exists(GRAPH_EDGES_PATH):
            try:
                import csv
                self.raw_edges = []
                with open(GRAPH_EDGES_PATH, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.raw_edges.append({
                            'source': row.get('source'),
                            'target': row.get('target'),
                            'relationship': row.get('edge_type')
                        })
                print(f"Successfully loaded {len(self.raw_edges)} graph edges.")
            except Exception as e:
                print(f"Error loading graph edges from {GRAPH_EDGES_PATH}: {e}")
        else:
            print(f"Graph edges file does not exist: {GRAPH_EDGES_PATH}")

        # 3. Build adjacency list for neighborhood lookups
        self.build_adjacency()

        # 4. Load fraud types for users
        self.user_fraud_types = {}
        import csv
        from app.utils.config import BASE_DIR
        labels_path = os.path.join(BASE_DIR, 'data/raw/fraud_labels.csv')
        if os.path.exists(labels_path):
            try:
                with open(labels_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.user_fraud_types[row['user_id']] = row['fraud_type']
            except Exception as e:
                print(f"Error loading fraud labels in graph service: {e}")

    def build_adjacency(self):
        self.adj_list = {}
        for edge in self.raw_edges:
            s = edge['source']
            t = edge['target']
            if s not in self.adj_list:
                self.adj_list[s] = []
            if t not in self.adj_list:
                self.adj_list[t] = []
            self.adj_list[s].append(t)
            self.adj_list[t].append(s)

    def get_graph_data(
        self, 
        user_id: Optional[str] = None, 
        risk_category: Optional[str] = None,
        min_degree: int = 0,
        max_nodes: int = 1500
    ) -> GraphDataResponse:
        """
        Retrieves graph data with flexible filtering:
        - If user_id is provided, returns the ego-network (1-hop or 2-hop neighborhood) around that user.
        - If risk_category is provided, returns all users in that category and their connected entities.
        - Otherwise returns a sample/subset of the graph, prioritizing high-risk connections.
        """
        # If no nodes loaded, return empty
        if not self.raw_nodes:
            return GraphDataResponse(nodes=[], edges=[])

        selected_node_ids = set()

        if user_id:
            # --- EGO NETWORK CASE ---
            # Center around user_id
            if user_id in self.nodes_dict:
                selected_node_ids.add(user_id)
                # Add 1st hop neighbors (e.g. devices, payments, IPs, vouchers used by the user)
                neighbors = self.adj_list.get(user_id, [])
                for n1 in neighbors:
                    selected_node_ids.add(n1)
                    # Add 2nd hop neighbors (other users using those same devices, payments, etc.)
                    # This reveals shared entities and fraud rings
                    for n2 in self.adj_list.get(n1, []):
                        # Limit neighborhood size to prevent explosion
                        if len(selected_node_ids) < max_nodes:
                            selected_node_ids.add(n2)
        
        elif risk_category:
            # --- RISK CATEGORY CASE ---
            # Select all users matching risk category
            target_cat = risk_category.lower()
            matching_users = [
                n_id for n_id, n in self.nodes_dict.items() 
                if n.get('type') == 'user' and str(n.get('risk_category', 'Low')).lower() == target_cat
            ]
            
            # Add matching users and their immediate neighbors (devices, payments, etc.)
            for u in matching_users:
                selected_node_ids.add(u)
                for nbr in self.adj_list.get(u, []):
                    selected_node_ids.add(nbr)
                    if len(selected_node_ids) >= max_nodes:
                        break
                if len(selected_node_ids) >= max_nodes:
                    break
        
        else:
            # --- GENERAL OVERVIEW CASE (PRIORITIZE HIGH RISK) ---
            # Pick all High risk users and some Medium risk users
            high_risk_users = [
                n_id for n_id, n in self.nodes_dict.items()
                if n.get('type') == 'user' and n.get('risk_category') == 'High'
            ]
            medium_risk_users = [
                n_id for n_id, n in self.nodes_dict.items()
                if n.get('type') == 'user' and n.get('risk_category') == 'Medium'
            ]
            
            # Take all high risk users (up to max_nodes/2) and their connected entities
            for u in high_risk_users:
                selected_node_ids.add(u)
                for nbr in self.adj_list.get(u, []):
                    selected_node_ids.add(nbr)
                if len(selected_node_ids) >= max_nodes // 2:
                    break
            
            # If still have space, add medium risk users
            if len(selected_node_ids) < max_nodes:
                for u in medium_risk_users:
                    selected_node_ids.add(u)
                    for nbr in self.adj_list.get(u, []):
                        selected_node_ids.add(nbr)
                    if len(selected_node_ids) >= max_nodes:
                        break

        # If min_degree filter is requested, compute degree within the selected subset
        # and filter out low degree nodes (optional further filter)
        # For simplicity, we just filter edges and reconstruct nodes based on edges.
        
        # Filter edges where both source and target are in our selected nodes
        filtered_edges = []
        for edge in self.raw_edges:
            s = edge['source']
            t = edge['target']
            if s in selected_node_ids and t in selected_node_ids:
                filtered_edges.append(
                    GraphEdge(source=s, target=t, relationship=edge['relationship'])
                )

        # Re-collect nodes that actually have edges to avoid floating orphan nodes
        active_node_ids = set()
        for edge in filtered_edges:
            active_node_ids.add(edge.source)
            active_node_ids.add(edge.target)

        # If we selected a single user who has no neighbors (isolated), keep them
        if user_id and user_id in selected_node_ids:
            active_node_ids.add(user_id)

        # Build GraphNode list
        filtered_nodes = []
        for node_id in active_node_ids:
            node = self.nodes_dict.get(node_id)
            if node:
                node_type = node.get('type', 'user' if str(node_id).startswith('USR') else 'entity')
                filtered_nodes.append(
                    GraphNode(
                        id=node['id'],
                        label=node.get('label', node['id']),
                        type=node_type,
                        risk_score=node.get('risk_score'),
                        risk_category=node.get('risk_category'),
                        ftype=node.get('ftype') or (self.user_fraud_types.get(node_id) if node_type == 'user' else None)
                    )
                )

        return GraphDataResponse(nodes=filtered_nodes, edges=filtered_edges)

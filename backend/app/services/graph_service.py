"""Purpose: Load and filter graph artifacts for API graph responses.
Used by: graph API router, prediction API user detail enrichment, chatbot service.
Depends on: graph_nodes.json, graph_edges.csv/json, fraud_labels.csv, response schemas.
Public functions: GraphService.load_graph_data, build_adjacency, get_graph_data, get_stats, get_entity_detail.
Side effects: Reads graph/data files into memory at service startup and caches fraud rings.
"""

import os
import json
import csv
from typing import Dict, Any, List, Optional
from app.utils.config import GRAPH_NODES_PATH, GRAPH_EDGES_PATH, BASE_DIR
from app.schemas.request_response import GraphNode, GraphEdge, GraphDataResponse


class GraphService:
    def __init__(self):
        self.raw_nodes: List[Dict] = []
        self.raw_edges: List[Dict] = []
        self.nodes_dict: Dict[str, Dict] = {}
        self.adj_list: Dict[str, List[str]] = {}
        self.user_fraud_types: Dict[str, str] = {}
        self._fraud_rings: List[List[str]] = []
        self._stats_cache: Optional[Dict] = None
        self.load_graph_data()

    def load_graph_data(self):
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

        if os.path.exists(GRAPH_EDGES_PATH):
            try:
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

        self.build_adjacency()

        labels_path = os.path.join(BASE_DIR, 'data/raw/fraud_labels.csv')
        if os.path.exists(labels_path):
            try:
                with open(labels_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        self.user_fraud_types[row['user_id']] = row['fraud_type']
            except Exception as e:
                print(f"Error loading fraud labels in graph service: {e}")

        # Cache fraud rings at startup (BFS over full graph)
        self._fraud_rings = self._compute_fraud_rings()
        print(f"Computed {len(self._fraud_rings)} fraud rings (connected user clusters).")

    def build_adjacency(self):
        self.adj_list = {}
        for edge in self.raw_edges:
            s, t = edge['source'], edge['target']
            self.adj_list.setdefault(s, []).append(t)
            self.adj_list.setdefault(t, []).append(s)

    def _compute_fraud_rings(self) -> List[List[str]]:
        """BFS over full graph; returns components with 2+ user nodes."""
        user_set = {n['id'] for n in self.raw_nodes if n.get('type') == 'user'}
        visited: set = set()
        rings: List[List[str]] = []

        for start_id in self.nodes_dict:
            if start_id in visited:
                continue
            component_users: List[str] = []
            stack = [start_id]
            while stack:
                curr = stack.pop()
                if curr in visited:
                    continue
                visited.add(curr)
                if curr in user_set:
                    component_users.append(curr)
                for nbr in self.adj_list.get(curr, []):
                    if nbr not in visited:
                        stack.append(nbr)
            if len(component_users) >= 2:
                rings.append(component_users)

        return rings

    def _bfs_ego_network(self, start_id: str, hop_depth: int, max_nodes: int) -> set:
        """BFS from start_id up to hop_depth hops, respecting max_nodes limit."""
        visited = {start_id}
        frontier = [start_id]
        for _ in range(hop_depth):
            next_frontier = []
            for node_id in frontier:
                for nbr in self.adj_list.get(node_id, []):
                    if nbr not in visited:
                        visited.add(nbr)
                        next_frontier.append(nbr)
                        if len(visited) >= max_nodes:
                            return visited
            frontier = next_frontier
            if not frontier:
                break
        return visited

    def get_stats(self) -> Dict[str, Any]:
        if self._stats_cache:
            return self._stats_cache

        user_nodes = [n for n in self.raw_nodes if n.get('type') == 'user']
        high = sum(1 for n in user_nodes if n.get('risk_category') == 'High')
        medium = sum(1 for n in user_nodes if n.get('risk_category') == 'Medium')
        low = len(user_nodes) - high - medium

        def _shared_count(node_type: str) -> int:
            return sum(
                1 for n in self.raw_nodes
                if n.get('type') == node_type and len(self.adj_list.get(n['id'], [])) >= 2
            )

        ring_sizes = [len(r) for r in self._fraud_rings]
        self._stats_cache = {
            "total_users": len(user_nodes),
            "high_risk_users": high,
            "medium_risk_users": medium,
            "low_risk_users": low,
            "fraud_rings": len(self._fraud_rings),
            "largest_ring_size": max(ring_sizes, default=0),
            "avg_ring_size": round(sum(ring_sizes) / len(ring_sizes), 1) if ring_sizes else 0,
            "shared_device_networks": _shared_count('device'),
            "shared_ip_networks": _shared_count('ip'),
            "shared_payment_networks": _shared_count('payment'),
            "shared_address_networks": _shared_count('address'),
            "total_nodes": len(self.raw_nodes),
            "total_edges": len(self.raw_edges),
        }
        return self._stats_cache

    def get_entity_detail(self, entity_id: str) -> Optional[Dict[str, Any]]:
        entity = self.nodes_dict.get(entity_id)
        if not entity:
            return None

        neighbors = self.adj_list.get(entity_id, [])
        connected_users = []
        for nbr_id in neighbors:
            nbr = self.nodes_dict.get(nbr_id)
            if nbr and nbr.get('type') == 'user':
                connected_users.append({
                    "uid": nbr_id,
                    "label": nbr.get('label', nbr_id),
                    "risk_category": nbr.get('risk_category', 'Low'),
                    "risk_score": nbr.get('risk_score', 0),
                    "ftype": nbr.get('ftype') or self.user_fraud_types.get(nbr_id),
                })

        # Sort by risk score descending
        connected_users.sort(key=lambda u: u.get('risk_score') or 0, reverse=True)

        return {
            "entity_id": entity_id,
            "entity_type": entity.get('type', 'entity'),
            "label": entity.get('label', entity_id),
            "total_connections": len(neighbors),
            "connected_users": connected_users,
        }

    def get_graph_data(
        self,
        user_id: Optional[str] = None,
        risk_category: Optional[str] = None,
        min_degree: int = 0,
        max_nodes: int = 1500,
        hop_depth: int = 2,
    ) -> GraphDataResponse:
        if not self.raw_nodes:
            return GraphDataResponse(nodes=[], edges=[])

        selected_node_ids: set = set()

        if user_id:
            if user_id in self.nodes_dict:
                selected_node_ids = self._bfs_ego_network(user_id, hop_depth, max_nodes)
            else:
                selected_node_ids = set()

        elif risk_category:
            target_cat = risk_category.lower()
            matching_users = [
                n_id for n_id, n in self.nodes_dict.items()
                if n.get('type') == 'user' and str(n.get('risk_category', 'Low')).lower() == target_cat
            ]
            for u in matching_users:
                selected_node_ids.add(u)
                for nbr in self.adj_list.get(u, []):
                    selected_node_ids.add(nbr)
                    if len(selected_node_ids) >= max_nodes:
                        break
                if len(selected_node_ids) >= max_nodes:
                    break

        else:
            high_risk_users = [
                n_id for n_id, n in self.nodes_dict.items()
                if n.get('type') == 'user' and n.get('risk_category') == 'High'
            ]
            medium_risk_users = [
                n_id for n_id, n in self.nodes_dict.items()
                if n.get('type') == 'user' and n.get('risk_category') == 'Medium'
            ]
            for u in high_risk_users:
                selected_node_ids.add(u)
                for nbr in self.adj_list.get(u, []):
                    selected_node_ids.add(nbr)
                if len(selected_node_ids) >= max_nodes // 2:
                    break
            if len(selected_node_ids) < max_nodes:
                for u in medium_risk_users:
                    selected_node_ids.add(u)
                    for nbr in self.adj_list.get(u, []):
                        selected_node_ids.add(nbr)
                    if len(selected_node_ids) >= max_nodes:
                        break

        filtered_edges = []
        for edge in self.raw_edges:
            s, t = edge['source'], edge['target']
            if s in selected_node_ids and t in selected_node_ids:
                filtered_edges.append(GraphEdge(source=s, target=t, relationship=edge['relationship']))

        active_node_ids: set = set()
        for edge in filtered_edges:
            active_node_ids.add(edge.source)
            active_node_ids.add(edge.target)

        if user_id and user_id in selected_node_ids:
            active_node_ids.add(user_id)

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

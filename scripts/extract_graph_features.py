import os
import pandas as pd
import networkx as nx
from collections import Counter

PROCESSED_DIR = 'data/processed'

NODES_PATH = os.path.join(PROCESSED_DIR, 'graph_nodes.csv')
EDGES_PATH = os.path.join(PROCESSED_DIR, 'graph_edges.csv')
OUTPUT_PATH = os.path.join(PROCESSED_DIR, 'user_graph_features.csv')


def extract_graph_features():
    print("Loading graph data...")

    df_nodes = pd.read_csv(NODES_PATH)
    df_edges = pd.read_csv(EDGES_PATH)

    user_nodes = df_nodes[df_nodes['node_type'] == 'user']['node_id'].tolist()

    print("Building bipartite graph...")
    B = nx.Graph()

    for _, row in df_nodes.iterrows():
        B.add_node(row['node_id'], node_type=row['node_type'])

    for _, row in df_edges.iterrows():
        B.add_edge(
            row['source'],
            row['target'],
            edge_type=row['edge_type']
        )

    print("Building user-user projection...")

    user_graph = nx.Graph()
    user_graph.add_nodes_from(user_nodes)

    shared_counts = Counter()
    shared_by_type = {
        'device': Counter(),
        'address': Counter(),
        'payment': Counter(),
        'ip': Counter()
    }

    entity_to_users = {}

    for entity_node in df_nodes[df_nodes['node_type'] != 'user']['node_id']:
        neighbors = [
            n for n in B.neighbors(entity_node)
            if n in user_nodes
        ]

        if len(neighbors) <= 1:
            continue
            
        # [PERBAIKAN SUPER NODE]: Jika sebuah entitas (misal IP) dipakai oleh > 50 user,
        # kemungkinan besar itu adalah Public WiFi / NAT biasa, bukan Sindikat Penipuan.
        # Menghubungkan semuanya akan menciptakan "Hairball" yang membuat proses membeku.
        if len(neighbors) > 50:
            continue

        entity_to_users[entity_node] = neighbors

        entity_type = B.nodes[entity_node].get('node_type')

        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                u1 = neighbors[i]
                u2 = neighbors[j]

                user_graph.add_edge(u1, u2)

                shared_counts[u1] += 1
                shared_counts[u2] += 1

                if entity_type in shared_by_type:
                    shared_by_type[entity_type][u1] += 1
                    shared_by_type[entity_type][u2] += 1

    print("Calculating graph metrics...")

    component_sizes = {}
    for comp in nx.connected_components(user_graph):
        size = len(comp)
        for node in comp:
            component_sizes[node] = size

    features = []

    for uid in user_nodes:
        features.append({
            'user_id': uid,
            'graph_degree': user_graph.degree(uid),
            'connected_component_size': component_sizes.get(uid, 1),
            'graph_cluster_size': len(nx.ego_graph(user_graph, uid)),
            'shared_entity_count': shared_counts.get(uid, 0),
            'shared_device_count': shared_by_type['device'].get(uid, 0),
            'shared_address_count': shared_by_type['address'].get(uid, 0),
            'shared_payment_count': shared_by_type['payment'].get(uid, 0),
            'shared_ip_count': shared_by_type['ip'].get(uid, 0)
        })

    df_features = pd.DataFrame(features)

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    df_features.to_csv(OUTPUT_PATH, index=False)

    print("Graph feature extraction complete.")
    print(f"Users: {len(df_features)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == '__main__':
    extract_graph_features()
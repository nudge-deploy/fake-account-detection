# Graph Feature Documentation

## Overview

Dokumen ini menjelaskan fitur-fitur graph yang dihasilkan oleh modul `extract_graph_features.py`.

Graph dibangun menggunakan pendekatan **User-Entity Bipartite Graph**, di mana setiap user terhubung ke berbagai entitas yang digunakan dalam aktivitas transaksi dan login, seperti:

* Device
* Address
* Payment Method
* IP Address

Selanjutnya dilakukan proses **User Projection Graph**, yaitu menghubungkan dua user apabila mereka berbagi satu atau lebih entitas yang sama.

---

## Graph Construction Flow

```text
User
 ├── Device
 ├── Address
 ├── Payment
 └── IP

        ↓

User Projection Graph

User A ─── User B
    │         │
    └─────────┘
   Shared Device
```

---

# Graph Feature Dictionary

| Nama Fitur               | Rumus Kode (Pandas / NetworkX Logic)                        | Definisi Teknis                                                             | Interpretasi Akhir (Bisnis)                                                             |
| ------------------------ | ----------------------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| user_id                  | `df_nodes[df_nodes['node_type']=='user']['node_id']`        | Identitas unik pengguna pada graph                                          | Akun yang sedang dianalisis                                                             |
| graph_degree             | `user_graph.degree(uid)`                                    | Jumlah koneksi langsung user terhadap user lain pada graph hasil projection | Semakin tinggi menunjukkan semakin banyak akun lain yang berbagi entitas dengan user    |
| connected_component_size | `len(component)` dari `nx.connected_components(user_graph)` | Jumlah total user yang berada pada cluster graph yang sama                  | Cluster besar dapat mengindikasikan fraud ring atau jaringan akun yang saling terhubung |
| graph_cluster_size       | `len(nx.ego_graph(user_graph, uid))`                        | Jumlah node dalam ego network user (user dan tetangga langsung)             | Menggambarkan ukuran lingkungan langsung user dalam jaringan                            |
| shared_entity_count      | `shared_counts.get(uid,0)`                                  | Total seluruh hubungan berbasis entitas bersama                             | Semakin tinggi berarti semakin banyak bukti hubungan dengan akun lain                   |
| shared_device_count      | `shared_by_type['device'].get(uid,0)`                       | Jumlah hubungan user-user akibat penggunaan device yang sama                | Tinggi menunjukkan indikasi shared device abuse atau multi-account                      |
| shared_address_count     | `shared_by_type['address'].get(uid,0)`                      | Jumlah hubungan user-user akibat penggunaan alamat yang sama                | Tinggi menunjukkan kemungkinan penyalahgunaan alamat pengiriman                         |
| shared_payment_count     | `shared_by_type['payment'].get(uid,0)`                      | Jumlah hubungan user-user akibat penggunaan metode pembayaran yang sama     | Tinggi menunjukkan kemungkinan satu metode pembayaran digunakan oleh banyak akun        |
| shared_ip_count          | `shared_by_type['ip'].get(uid,0)`                           | Jumlah hubungan user-user akibat penggunaan IP Address yang sama            | Tinggi menunjukkan kemungkinan login massal dari jaringan yang sama                     |

---

# Contoh Perhitungan

Misalkan terdapat data berikut:

| User | Device |
| ---- | ------ |
| U001 | D001   |
| U002 | D001   |
| U003 | D001   |

Projection Graph:

```text
U001 ── U002
 │  \     │
 │   \    │
 └────U003
```

Maka:

| User | shared_device_count |
| ---- | ------------------- |
| U001 | 2                   |
| U002 | 2                   |
| U003 | 2                   |

Karena setiap user memiliki hubungan dengan dua user lain melalui penggunaan device yang sama.

---

# Interpretasi Fraud Ring

## Risiko Rendah

Karakteristik:

```text
graph_degree = 0
shared_entity_count = 0
connected_component_size = 1
```

Interpretasi:

User berdiri sendiri dan tidak memiliki hubungan dengan akun lain pada graph.

---

## Risiko Menengah

Karakteristik:

```text
graph_degree = 3
shared_ip_count = 2
shared_device_count = 1
```

Interpretasi:

User memiliki beberapa hubungan dengan akun lain yang masih mungkin disebabkan oleh penggunaan jaringan atau perangkat bersama yang wajar.

---

## Risiko Tinggi

Karakteristik:

```text
graph_degree = 25
connected_component_size = 80
shared_device_count = 18
shared_ip_count = 20
shared_payment_count = 12
```

Interpretasi:

User berada dalam cluster besar dengan banyak entitas bersama. Pola seperti ini sering ditemukan pada kasus fraud ring, multi-account abuse, voucher abuse, maupun cashback abuse.

---

# Output Dataset

File hasil:

```text
data/processed/user_graph_features.csv
```

Struktur output:

```csv
user_id,
graph_degree,
connected_component_size,
graph_cluster_size,
shared_entity_count,
shared_device_count,
shared_address_count,
shared_payment_count,
shared_ip_count
```

Dataset ini selanjutnya di-merge dengan Analytical Base Table (ABT) utama untuk membentuk final training dataset yang digunakan pada model **Fraud Graph Ring Detection**.

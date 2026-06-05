"""
Generate standalone graph_preview.html dengan data JSON yang sudah di-embed langsung.
Tidak memerlukan server/fetch — bisa dibuka langsung di browser.
"""
import json, os, collections

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROC_DIR = os.path.join(BASE_DIR, 'data', 'processed')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')

print("Loading graph data...")
with open(os.path.join(PROC_DIR, 'graph_nodes.json'), encoding='utf-8') as f:
    all_nodes = json.load(f)
with open(os.path.join(PROC_DIR, 'graph_edges.json'), encoding='utf-8') as f:
    all_edges = json.load(f)

# Stats
type_count = collections.Counter(n['type'] for n in all_nodes)
edge_count = collections.Counter(e['relationship'] for e in all_edges)
user_nodes = [n for n in all_nodes if n['type'] == 'user']
risk_dist  = collections.Counter(n.get('risk_category', '?') for n in user_nodes)
high_risk  = [n for n in user_nodes if n.get('risk_score', 0) >= 50]

print(f"Total Nodes: {len(all_nodes):,}")
print(f"Total Edges: {len(all_edges):,}")
print(f"High Risk Users: {len(high_risk):,}")
print(f"Risk distribution: {dict(risk_dist)}")

# Build subgraph: top 50 high-risk users + 1-hop neighbors
print("\nBuilding preview subgraph (top 50 high-risk + neighbors)...")
top_users = sorted(high_risk, key=lambda x: x.get('risk_score', 0), reverse=True)[:50]
top_ids   = {n['id'] for n in top_users}

relevant_edges = [e for e in all_edges if e['source'] in top_ids]
neighbor_ids   = {e['target'] for e in relevant_edges} - top_ids
node_map       = {n['id']: n for n in all_nodes}

preview_nodes = []
for n in top_users:
    n2 = dict(n); n2['highlight'] = True; preview_nodes.append(n2)
for nid in neighbor_ids:
    if nid in node_map:
        preview_nodes.append(dict(node_map[nid]))

stats = {
    "total_nodes": len(all_nodes),
    "total_edges": len(all_edges),
    "total_users": len(user_nodes),
    "high_risk_users": len(high_risk),
    "preview_nodes": len(preview_nodes),
    "preview_edges": len(relevant_edges),
    "risk_distribution": dict(risk_dist),
    "node_types": dict(type_count),
}

print(f"Preview nodes: {len(preview_nodes):,}")
print(f"Preview edges: {len(relevant_edges):,}")

# Embed as JS variable in HTML
nodes_json = json.dumps(preview_nodes, separators=(',', ':'))
edges_json = json.dumps(relevant_edges, separators=(',', ':'))
stats_json = json.dumps(stats, separators=(',', ':'))

html = f"""<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <title>Fraud Graph Preview</title>
  <script src="https://unpkg.com/cytoscape@3.28.1/dist/cytoscape.min.js"></script>
  <style>
    *{{margin:0;padding:0;box-sizing:border-box}}
    body{{font-family:'Segoe UI',sans-serif;background:#0f1117;color:#e2e8f0;display:flex;flex-direction:column;height:100vh;overflow:hidden}}
    header{{background:#1a1d2e;border-bottom:1px solid #2d3748;padding:12px 20px;display:flex;align-items:center;gap:16px;flex-shrink:0}}
    header h1{{font-size:1rem;font-weight:700;color:#f97316}}
    header p{{font-size:.75rem;color:#94a3b8}}
    #stats-bar{{background:#141828;border-bottom:1px solid #2d3748;padding:8px 20px;display:flex;gap:24px;flex-shrink:0;flex-wrap:wrap}}
    .stat{{display:flex;flex-direction:column}}
    .stat-label{{font-size:.65rem;color:#64748b;text-transform:uppercase;letter-spacing:.05em}}
    .stat-value{{font-size:1rem;font-weight:700;color:#f8fafc}}
    .stat-value.red{{color:#f87171}} .stat-value.amber{{color:#fbbf24}} .stat-value.green{{color:#34d399}}
    #main{{display:flex;flex:1;overflow:hidden}}
    #cy{{flex:1;background:#0d1117}}
    #sidebar{{width:280px;background:#1a1d2e;border-left:1px solid #2d3748;display:flex;flex-direction:column;overflow:hidden;flex-shrink:0}}
    #sidebar h2{{font-size:.8rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;padding:12px 14px;border-bottom:1px solid #2d3748}}
    #node-info{{padding:14px;font-size:.78rem;color:#94a3b8;flex:1;overflow-y:auto}}
    .placeholder{{color:#4a5568;font-style:italic}}
    .info-row{{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1e2436}}
    .info-label{{color:#64748b}} .info-value{{color:#e2e8f0;font-weight:600;max-width:130px;text-align:right;word-break:break-all}}
    .badge{{display:inline-block;padding:2px 8px;border-radius:9999px;font-size:.7rem;font-weight:700}}
    .badge-high{{background:#7f1d1d;color:#fca5a5}} .badge-medium{{background:#78350f;color:#fde68a}} .badge-low{{background:#14532d;color:#6ee7b7}}
    .badge-device{{background:#1e3a5f;color:#93c5fd}} .badge-address{{background:#2d1b5e;color:#c4b5fd}}
    .badge-payment{{background:#1a3a2a;color:#6ee7b7}} .badge-ip{{background:#3a1a1a;color:#fca5a5}} .badge-voucher{{background:#3a2a1a;color:#fde68a}}
    #legend{{padding:12px 14px;border-top:1px solid #2d3748;font-size:.72rem}}
    #legend h3{{color:#64748b;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px;font-size:.65rem}}
    .legend-item{{display:flex;align-items:center;gap:8px;margin-bottom:5px;color:#94a3b8}}
    .dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
    .dot-high{{background:#f87171;box-shadow:0 0 6px #f87171}} .dot-medium{{background:#fbbf24}} .dot-low{{background:#34d399}}
    .dot-device{{background:#60a5fa;border-radius:2px}} .dot-address{{background:#a78bfa;border-radius:2px}}
    .dot-payment{{background:#4ade80;border-radius:2px}} .dot-ip{{background:#f87171;border-radius:2px}} .dot-voucher{{background:#fde68a;border-radius:2px}}
  </style>
</head>
<body>
<header>
  <div>
    <h1>🕸️ Fraud Graph Preview</h1>
    <p>Top 50 high-risk users + 1-hop connections — click a node for details</p>
  </div>
</header>
<div id="stats-bar">
  <div class="stat"><span class="stat-label">Preview Nodes</span><span class="stat-value" id="s-nodes">—</span></div>
  <div class="stat"><span class="stat-label">Preview Edges</span><span class="stat-value" id="s-edges">—</span></div>
  <div class="stat"><span class="stat-label">High Risk Users</span><span class="stat-value red" id="s-high">—</span></div>
  <div class="stat"><span class="stat-label">Full Graph Nodes</span><span class="stat-value" id="s-all-nodes">—</span></div>
  <div class="stat"><span class="stat-label">Full Graph Edges</span><span class="stat-value" id="s-all-edges">—</span></div>
</div>
<div id="main">
  <div id="cy"></div>
  <div id="sidebar">
    <h2>Selected Node</h2>
    <div id="node-info"><p class="placeholder">Click any node to see its details.</p></div>
    <div id="legend">
      <h3>Legend</h3>
      <div class="legend-item"><div class="dot dot-high"></div> High Risk User</div>
      <div class="legend-item"><div class="dot dot-medium"></div> Medium Risk User</div>
      <div class="legend-item"><div class="dot dot-low"></div> Low Risk User</div>
      <div class="legend-item"><div class="dot dot-device"></div> Device</div>
      <div class="legend-item"><div class="dot dot-address"></div> Address</div>
      <div class="legend-item"><div class="dot dot-payment"></div> Payment</div>
      <div class="legend-item"><div class="dot dot-ip"></div> IP Address</div>
      <div class="legend-item"><div class="dot dot-voucher"></div> Voucher</div>
    </div>
  </div>
</div>
<script>
const NODES = {nodes_json};
const EDGES = {edges_json};
const STATS = {stats_json};

const colorMap = {{
  user_High:'#f87171', user_Medium:'#fbbf24', user_Low:'#34d399',
  device:'#60a5fa', address:'#a78bfa', payment:'#4ade80', ip:'#f87171', voucher:'#fde68a',
}};
function nodeColor(d){{return d.type==='user'?colorMap['user_'+(d.risk_category||'Low')]:colorMap[d.type]||'#64748b'}}
function nodeSize(d){{return d.type==='user'?Math.max(16,Math.min(40,14+(d.risk_score||0)/4)):10}}
function nodeShape(d){{
  const m={{user:'ellipse',device:'rectangle',address:'diamond',payment:'pentagon',ip:'triangle',voucher:'hexagon'}};
  return m[d.type]||'ellipse';
}}
function badgeClass(d){{
  if(d.type==='user')return 'badge badge-'+(d.risk_category||'Low').toLowerCase();
  return 'badge badge-'+d.type;
}}
function renderInfo(d){{
  let rows=`<div class="info-row"><span class="info-label">ID</span><span class="info-value">${{d.id}}</span></div>
  <div class="info-row"><span class="info-label">Type</span><span class="info-value"><span class="${{badgeClass(d)}}">${{d.type}}</span></span></div>`;
  if(d.type==='user'){{
    rows+=`<div class="info-row"><span class="info-label">Risk Score</span><span class="info-value">${{d.risk_score??'—'}}</span></div>
    <div class="info-row"><span class="info-label">Risk Category</span><span class="info-value"><span class="${{badgeClass(d)}}">${{d.risk_category??'—'}}</span></span></div>`;
  }}
  document.getElementById('node-info').innerHTML=rows;
}}

document.getElementById('s-nodes').textContent=NODES.length.toLocaleString();
document.getElementById('s-edges').textContent=EDGES.length.toLocaleString();
document.getElementById('s-high').textContent=(STATS.high_risk_users||'—').toLocaleString();
document.getElementById('s-all-nodes').textContent=(STATS.total_nodes||'—').toLocaleString();
document.getElementById('s-all-edges').textContent=(STATS.total_edges||'—').toLocaleString();

const elements=[];
NODES.forEach(n=>elements.push({{group:'nodes',data:{{id:n.id,...n}}}}));
EDGES.forEach(e=>elements.push({{group:'edges',data:{{id:e.source+'_'+e.target+'_'+e.relationship,source:e.source,target:e.target,rel:e.relationship}}}}));

const cy=cytoscape({{
  container:document.getElementById('cy'),
  elements,
  style:[
    {{selector:'node',style:{{
      'background-color':ele=>nodeColor(ele.data()),
      'width':ele=>nodeSize(ele.data()),
      'height':ele=>nodeSize(ele.data()),
      'shape':ele=>nodeShape(ele.data()),
      'label':ele=>{{
        const d=ele.data();
        if(d.type==='user')return d.id+'\\n'+(d.risk_score??'');
        return d.id.substring(0,12);
      }},
      'font-size':'7px','color':'#cbd5e1',
      'text-halign':'center','text-valign':'bottom','text-margin-y':3,'text-wrap':'wrap',
      'border-width':ele=>ele.data('highlight')?2:0,'border-color':'#f97316',
    }}}},
    {{selector:'edge',style:{{'line-color':'#2d3748','width':1,'curve-style':'bezier','opacity':0.5}}}},
    {{selector:':selected',style:{{'border-width':3,'border-color':'#f97316'}}}},
  ],
  layout:{{name:'cose',animate:false,randomize:true,nodeRepulsion:()=>8000,idealEdgeLength:()=>60,padding:30}},
  minZoom:0.1, maxZoom:4,
}});

cy.on('tap','node',evt=>renderInfo(evt.target.data()));
cy.on('tap',evt=>{{
  if(evt.target===cy)document.getElementById('node-info').innerHTML='<p class="placeholder">Click any node to see its details.</p>';
}});
</script>
</body>
</html>"""

out_path = os.path.join(DOCS_DIR, 'graph_preview.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ Standalone HTML saved: {out_path}")
print("   Open this file directly in your browser (no server needed).")

"use client";

import { useEffect, useState, useRef, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import {
  getGraphData, getUserDetails, getGraphStats, getEntityDetail,
  GraphData, UserDetails, GraphStats, EntityDetail,
} from '@/lib/api';

const COMBINED_STYLE: Record<string, { badge: string; bar: string }> = {
  High:   { badge: 'bg-red-100 text-red-700 border-red-300',    bar: 'bg-red-500' },
  Medium: { badge: 'bg-amber-100 text-amber-700 border-amber-300', bar: 'bg-amber-400' },
  Low:    { badge: 'bg-emerald-100 text-emerald-700 border-emerald-300', bar: 'bg-emerald-500' },
};
import dynamic from 'next/dynamic';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

const ENTITY_TYPE_LABELS: Record<string, string> = {
  device: 'Device Fingerprint',
  ip: 'IP Address',
  payment: 'Payment Method',
  address: 'Shipping Address',
  voucher: 'Voucher',
};

const ENTITY_COLORS: Record<string, string> = {
  device: '#3b82f6',
  address: '#8b5cf6',
  payment: '#ec4899',
  ip: '#06b6d4',
  voucher: '#eab308',
};

const RISK_BADGE: Record<string, string> = {
  High: 'bg-red-100 text-red-700 border border-red-200',
  Medium: 'bg-amber-100 text-amber-700 border border-amber-200',
  Low: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
};

function KpiCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-center">
      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{label}</p>
      <p className="text-base font-black text-slate-800 mt-0.5">{value}</p>
      {sub && <p className="text-[9px] text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function GraphContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const urlUserId = searchParams.get('user_id');

  // Control states
  const [searchUserId, setSearchUserId] = useState(urlUserId || '');
  const [riskCategoryFilter, setRiskCategoryFilter] = useState('');
  const [maxNodes, setMaxNodes] = useState(800);
  const [hopDepth, setHopDepth] = useState(2);
  const [riskThreshold, setRiskThreshold] = useState(0);
  const [highRiskOnly, setHighRiskOnly] = useState(false);
  const [selectedFraudType, setSelectedFraudType] = useState('');

  // Data states
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [filteredData, setFilteredData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
  const [graphStats, setGraphStats] = useState<GraphStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected node states
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeType, setSelectedNodeType] = useState<string | null>(null);
  const [userDetail, setUserDetail] = useState<UserDetails | null>(null);
  const [entityDetail, setEntityDetail] = useState<EntityDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const graphRef = useRef<any>(null);

  // Fetch stats once on mount
  useEffect(() => {
    getGraphStats().then(setGraphStats).catch(console.error);
  }, []);

  // Fetch graph data when query params change
  const fetchGraph = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getGraphData({
        user_id: searchUserId || undefined,
        risk_category: riskCategoryFilter || undefined,
        max_nodes: maxNodes,
        hop_depth: hopDepth,
      });
      setGraphData(data);
    } catch {
      setError('Gagal memuat data jaringan dari API backend.');
    } finally {
      setLoading(false);
    }
  }, [searchUserId, riskCategoryFilter, maxNodes, hopDepth]);

  useEffect(() => { fetchGraph(); }, [fetchGraph]);

  // Apply frontend filters
  useEffect(() => {
    if (!graphData) { setFilteredData({ nodes: [], links: [] }); return; }

    const nodes = [...graphData.nodes];
    const edges = [...graphData.edges];
    const userNodeIds = new Set(nodes.filter(n => n.type === 'user').map(n => n.id));

    let usersToKeep = new Set(userNodeIds);

    if (highRiskOnly) {
      usersToKeep = new Set(Array.from(usersToKeep).filter(uid => {
        const node = nodes.find(n => n.id === uid);
        return node?.risk_category === 'High';
      }));
    }
    if (selectedFraudType) {
      usersToKeep = new Set(Array.from(usersToKeep).filter(uid => {
        const node = nodes.find(n => n.id === uid);
        return (node?.ftype || 'normal').toLowerCase() === selectedFraudType.toLowerCase();
      }));
    }
    if (riskThreshold > 0) {
      usersToKeep = new Set(Array.from(usersToKeep).filter(uid => {
        const node = nodes.find(n => n.id === uid);
        return (node?.risk_score || 0) >= riskThreshold;
      }));
    }

    const filteredEdges = edges.filter(edge => {
      const srcId = typeof edge.source === 'object' ? (edge.source as any).id : edge.source;
      const tgtId = typeof edge.target === 'object' ? (edge.target as any).id : edge.target;
      if (userNodeIds.has(srcId) && !usersToKeep.has(srcId)) return false;
      if (userNodeIds.has(tgtId) && !usersToKeep.has(tgtId)) return false;
      return true;
    });

    const activeNodeIds = new Set<string>();
    filteredEdges.forEach(edge => {
      const srcId = typeof edge.source === 'object' ? (edge.source as any).id : edge.source;
      const tgtId = typeof edge.target === 'object' ? (edge.target as any).id : edge.target;
      activeNodeIds.add(srcId);
      activeNodeIds.add(tgtId);
    });
    if (searchUserId && userNodeIds.has(searchUserId)) activeNodeIds.add(searchUserId);

    setFilteredData({
      nodes: nodes.filter(n => activeNodeIds.has(n.id)),
      links: filteredEdges,
    });
  }, [graphData, highRiskOnly, selectedFraudType, riskThreshold, searchUserId]);

  // Fetch node details when selection changes
  useEffect(() => {
    if (!selectedNodeId) { setUserDetail(null); setEntityDetail(null); return; }

    const node = filteredData.nodes.find(n => n.id === selectedNodeId);
    if (!node) return;

    setSelectedNodeType(node.type);
    setUserDetail(null);
    setEntityDetail(null);

    async function fetchDetails() {
      setDetailLoading(true);
      try {
        if (node!.type === 'user') {
          const data = await getUserDetails(selectedNodeId!);
          setUserDetail(data);
        } else {
          const data = await getEntityDetail(selectedNodeId!);
          setEntityDetail(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setDetailLoading(false);
      }
    }
    fetchDetails();
  }, [selectedNodeId]);

  const handleClearSearch = () => { setSearchUserId(''); router.replace('/graph'); };

  // Node canvas rendering — size by risk score
  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const isSelected = node.id === selectedNodeId;
    let radius = 4;
    let color = '#94a3b8';

    if (node.type === 'user') {
      const riskScore = node.risk_score || 0;
      radius = 5 + Math.min(9, riskScore / 10);
      if (node.risk_category === 'High') color = '#ef4444';
      else if (node.risk_category === 'Medium') color = '#f59e0b';
      else color = '#10b981';
    } else {
      color = ENTITY_COLORS[node.type] || '#94a3b8';
      radius = 4;
    }

    if (isSelected) {
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(51,65,85,0.15)';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI);
      ctx.strokeStyle = '#334155';
      ctx.lineWidth = 1.5 / globalScale;
      ctx.stroke();
    }

    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
    ctx.fillStyle = color;
    ctx.fill();

    if (globalScale > 1.5 || isSelected) {
      const fontSize = Math.min(10, 10 / globalScale);
      ctx.font = `${isSelected ? 'bold ' : ''}${fontSize}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = '#475569';
      const text = node.label || node.id;
      ctx.fillText(text.length > 14 ? text.slice(0, 13) + '…' : text, node.x, node.y + radius + 2);
    }
  }, [selectedNodeId]);

  const highRiskInView = filteredData.nodes.filter(n => n.type === 'user' && n.risk_category === 'High').length;

  return (
    <div className="flex flex-col lg:flex-row gap-4 min-h-[calc(100vh-8rem)]">

      {/* ── Left Controls ── */}
      <div className="w-full lg:w-72 flex-shrink-0 flex flex-col gap-4 overflow-y-auto max-h-[calc(100vh-8rem)]">

        {/* KPI Stats */}
        {graphStats && (
          <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Statistik Jaringan</h3>
            <div className="grid grid-cols-2 gap-2">
              <KpiCard label="Total Users" value={graphStats.total_users.toLocaleString()} />
              <KpiCard label="High Risk" value={graphStats.high_risk_users.toLocaleString()} />
              <KpiCard label="Fraud Rings" value={graphStats.fraud_rings.toLocaleString()} sub={`terbesar: ${graphStats.largest_ring_size} user`} />
              <KpiCard label="Shared Devices" value={graphStats.shared_device_networks.toLocaleString()} />
              <KpiCard label="Shared IPs" value={graphStats.shared_ip_networks.toLocaleString()} />
              <KpiCard label="Shared Payments" value={graphStats.shared_payment_networks.toLocaleString()} />
            </div>
          </div>
        )}

        {/* Search & Filters */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
          <div>
            <h2 className="text-base font-bold text-slate-900">Fraud Investigation</h2>
            <p className="text-[10px] text-slate-500 mt-0.5">Visualisasi jaringan untuk investigasi fraud ring.</p>
          </div>

          {/* Search */}
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Cari User ID / Ego-Network</label>
            <div className="flex gap-1.5">
              <input
                type="text"
                value={searchUserId}
                onChange={(e) => setSearchUserId(e.target.value)}
                placeholder="Contoh: USR00010"
                className="flex-1 px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-800"
              />
              {searchUserId && (
                <button onClick={handleClearSearch} className="px-2 py-1 text-[10px] border border-slate-300 rounded-lg hover:bg-slate-100 text-slate-600 font-bold">
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Hop Depth */}
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
              Kedalaman Ego-Network
            </label>
            <div className="flex gap-1.5">
              {[1, 2, 3].map(h => (
                <button
                  key={h}
                  onClick={() => setHopDepth(h)}
                  className={`flex-1 py-1.5 text-xs font-bold rounded-lg border transition-colors ${
                    hopDepth === h
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'bg-white text-slate-600 border-slate-300 hover:border-blue-400'
                  }`}
                >
                  {h}-Hop
                </button>
              ))}
            </div>
            <p className="text-[9px] text-slate-400 mt-1">
              {hopDepth === 1 ? 'User + entitas langsung' : hopDepth === 2 ? 'User + entitas + user lain yang berbagi' : 'Jaringan luas 3 lapis (hati-hati: banyak node)'}
            </p>
          </div>

          {/* Risk Category */}
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Pusatkan pada Risk Category</label>
            <select
              value={riskCategoryFilter}
              onChange={(e) => setRiskCategoryFilter(e.target.value)}
              className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-700"
            >
              <option value="">Semua (Acak)</option>
              <option value="High">High Risk Only</option>
              <option value="Medium">Medium Risk Only</option>
              <option value="Low">Low Risk Only</option>
            </select>
          </div>

          {/* Max Nodes */}
          <div>
            <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">Maks Node: {maxNodes}</label>
            <input type="range" min="50" max="1500" step="50" value={maxNodes}
              onChange={(e) => setMaxNodes(parseInt(e.target.value))}
              className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          {/* Display Filters */}
          <div className="pt-2 border-t border-slate-100 space-y-2.5">
            <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">Filter Tampilan</span>

            {/* Risk Threshold */}
            <div>
              <label className="block text-[10px] text-slate-500 font-semibold mb-1">
                Min. Risk Score: <span className="text-slate-800 font-bold">{riskThreshold > 0 ? `≥ ${riskThreshold}` : 'Semua'}</span>
              </label>
              <input type="range" min="0" max="100" step="5" value={riskThreshold}
                onChange={(e) => setRiskThreshold(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-orange-500"
              />
            </div>

            <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-600">
              <input type="checkbox" checked={highRiskOnly} onChange={(e) => setHighRiskOnly(e.target.checked)}
                className="rounded border-slate-300 text-blue-600 focus:ring-blue-500 h-4 w-4"
              />
              Hanya Akun High Risk
            </label>

            <div>
              <label className="block text-[9px] font-bold text-slate-500 uppercase mb-1">Tipe Fraud</label>
              <select value={selectedFraudType} onChange={(e) => setSelectedFraudType(e.target.value)}
                className="w-full px-2 py-1 text-[11px] border border-slate-300 rounded focus:outline-none bg-white text-slate-600"
              >
                <option value="">Semua Tipe</option>
                <option value="normal">Normal</option>
                <option value="shared_device_abuse">Shared Device Abuse</option>
                <option value="shared_address_abuse">Shared Address Abuse</option>
                <option value="shared_payment_abuse">Shared Payment Abuse</option>
                <option value="voucher_farming">Voucher Farming</option>
                <option value="referral_abuse">Referral Abuse</option>
              </select>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm">
          <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2.5">Legenda</h4>
          <div className="space-y-1.5 text-xs font-semibold text-slate-600">
            <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">User Nodes (ukuran = risk score)</p>
            {[
              { color: 'bg-red-500', label: 'User – High Risk' },
              { color: 'bg-amber-500', label: 'User – Medium Risk' },
              { color: 'bg-emerald-500', label: 'User – Low Risk' },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-2">
                <span className={`h-3 w-3 rounded-full ${color} flex-shrink-0`}></span>
                <span>{label}</span>
              </div>
            ))}
            <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mt-2 mb-1">Entitas (klik untuk detail)</p>
            {[
              { color: 'bg-blue-500', label: 'Device' },
              { color: 'bg-purple-500', label: 'Address' },
              { color: 'bg-pink-500', label: 'Payment' },
              { color: 'bg-cyan-500', label: 'IP Address' },
              { color: 'bg-yellow-400', label: 'Voucher' },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${color} flex-shrink-0`}></span>
                <span>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Graph Canvas ── */}
      <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm relative overflow-hidden flex flex-col min-h-[500px]">
        {loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-white/90 z-10">
            <div className="h-10 w-10 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
            <p className="text-slate-500 text-sm font-semibold animate-pulse">Menghitung hubungan graf…</p>
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center text-red-600 font-medium">{error}</div>
        ) : (
          <div className="flex-1 relative">
            {/* Stats overlay */}
            <div className="absolute top-3 left-3 bg-white/95 text-slate-700 text-xs px-3 py-2 rounded-lg z-10 shadow border border-slate-200 pointer-events-none space-y-0.5">
              <p className="font-bold">Node: <strong>{filteredData.nodes.length}</strong> &nbsp;|&nbsp; Edge: <strong>{filteredData.links.length}</strong></p>
              <p className="text-[10px] text-slate-500">High Risk di layar: <strong className="text-red-600">{highRiskInView}</strong></p>
              <p className="text-[9px] text-slate-400">Klik node untuk investigasi detail</p>
            </div>

            {/* Hop depth indicator */}
            <div className="absolute top-3 right-3 bg-blue-600 text-white text-[10px] font-bold px-2.5 py-1 rounded-lg z-10 shadow">
              {hopDepth}-HOP {searchUserId ? `· ${searchUserId}` : ''}
            </div>

            <ForceGraph2D
              ref={graphRef}
              graphData={filteredData}
              nodeCanvasObject={nodeCanvasObject}
              nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
                const radius = node.type === 'user' ? 5 + Math.min(9, (node.risk_score || 0) / 10) : 4;
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(node.x, node.y, radius + 6, 0, 2 * Math.PI);
                ctx.fill();
              }}
              nodeLabel={(node: any) => {
                const typeLabel = node.type === 'user' ? `User · ${node.risk_category || '?'} Risk · Score ${node.risk_score ?? '?'}` : (ENTITY_TYPE_LABELS[node.type] || node.type);
                return `${node.id}\n${typeLabel}`;
              }}
              linkDirectionalParticles={1}
              linkDirectionalParticleSpeed={0.005}
              linkColor={(link: any) => {
                const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
                return (srcId === selectedNodeId || tgtId === selectedNodeId) ? '#3b82f6' : '#e2e8f0';
              }}
              linkWidth={(link: any) => {
                const srcId = typeof link.source === 'object' ? link.source.id : link.source;
                const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
                return (srcId === selectedNodeId || tgtId === selectedNodeId) ? 2.5 : 1;
              }}
              onNodeClick={(node: any) => setSelectedNodeId(prev => prev === node.id ? null : node.id)}
              onBackgroundClick={() => setSelectedNodeId(null)}
            />
          </div>
        )}
      </div>

      {/* ── Right Investigation Panel ── */}
      {selectedNodeId && (
        <div className="w-full lg:w-88 xl:w-96 flex-shrink-0 bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col overflow-hidden max-h-[calc(100vh-8rem)]">
          {/* Header */}
          <div className="flex justify-between items-start p-4 border-b border-slate-100 flex-shrink-0">
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                {selectedNodeType === 'user' ? 'Investigasi Akun' : ENTITY_TYPE_LABELS[selectedNodeType || ''] || 'Detail Entitas'}
              </p>
              <p className="font-bold text-slate-800 text-sm font-mono mt-0.5">{selectedNodeId}</p>
            </div>
            <button onClick={() => setSelectedNodeId(null)}
              className="text-xs font-bold text-slate-400 hover:text-slate-700 hover:bg-slate-100 p-1.5 rounded-lg transition-colors"
            >
              ✕
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {detailLoading ? (
              <div className="py-20 flex flex-col items-center justify-center gap-3">
                <div className="h-8 w-8 border-4 border-slate-200 border-t-blue-600 rounded-full animate-spin"></div>
                <span className="text-slate-400 text-xs">Memuat data…</span>
              </div>
            ) : selectedNodeType === 'user' && userDetail ? (
              <UserDetailPanel userDetail={userDetail} />
            ) : selectedNodeType !== 'user' && entityDetail ? (
              <EntityDetailPanel entityDetail={entityDetail} onUserClick={setSelectedNodeId} />
            ) : (
              <div className="text-slate-400 text-xs text-center py-10">Gagal memuat detail.</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function UserDetailPanel({ userDetail }: { userDetail: UserDetails }) {
  return (
    <div className="space-y-4 text-xs">
      {/* Profile */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-1.5">
        <div className="flex justify-between items-center">
          <span className="font-bold text-slate-900 text-sm">{userDetail.full_name || 'N/A'}</span>
          <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] uppercase ${RISK_BADGE[userDetail.risk_category] || RISK_BADGE.Low}`}>
            {userDetail.risk_category} Risk
          </span>
        </div>
        {userDetail.email && <p className="text-slate-500">Email: <span className="font-semibold text-slate-700">{userDetail.email}</span></p>}
        {(userDetail.city || userDetail.province) && (
          <p className="text-slate-500">Lokasi: <span className="font-semibold text-slate-700">{[userDetail.city, userDetail.province].filter(Boolean).join(', ')}</span></p>
        )}
        {userDetail.ftype && userDetail.ftype !== 'normal' && (
          <p className="text-slate-500">Fraud Type: <span className="font-semibold text-red-600">{userDetail.ftype}</span></p>
        )}
        <span className={`inline-block text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${userDetail.model_type === 'new' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'}`}>
          {userDetail.model_type === 'new' ? 'New Customer Model' : 'Existing Customer Model'}
        </span>
      </div>

      {/* Unified Risk Assessment */}
      {(() => {
        const combined = userDetail.combined_risk_category || userDetail.risk_category || 'Low';
        const style = COMBINED_STYLE[combined] || COMBINED_STYLE.Low;
        const mlPct = userDetail.ml_probability != null ? userDetail.ml_probability * 100 : null;
        const rulePct = userDetail.risk_score_rule_based;
        return (
          <div className="space-y-2">
            {/* Verdict */}
            <div className={`rounded-lg border p-3 ${style.badge}`}>
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-bold uppercase tracking-widest opacity-60">Penilaian Akhir</span>
                <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full border ${style.badge}`}>{combined} RISK</span>
              </div>
              <p className="text-[10px] mt-1 opacity-70 leading-relaxed">
                {combined === 'High' ? 'Sinyal risiko tinggi — perlu investigasi.'
                  : combined === 'Medium' ? 'Pola mencurigakan — perlu pemantauan.'
                  : 'Tidak ada sinyal risiko signifikan.'}
              </p>
            </div>

            {/* Conflict */}
            {userDetail.score_conflict && (
              <div className="flex gap-1.5 bg-amber-50 border border-amber-200 rounded-lg p-2 text-[10px] text-amber-800">
                <span className="flex-shrink-0">⚠</span>
                <p><span className="font-bold">Sinyal tidak konsisten</span> — Rule-based dan ML berbeda. Investigasi manual diperlukan.</p>
              </div>
            )}

            {/* Two pillars */}
            <div className="grid grid-cols-2 gap-2">
              <div className="border border-slate-200 rounded-lg p-2.5 bg-white">
                <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">Rule Score</p>
                <p className="text-xl font-black text-slate-900 leading-none">{rulePct}<span className="text-xs text-slate-400">/100</span></p>
                <div className="mt-1.5 h-1 bg-slate-100 rounded-full">
                  <div className={`h-full rounded-full ${style.bar}`} style={{ width: `${Math.min(100, rulePct)}%` }} />
                </div>
                <p className="text-[9px] text-slate-400 mt-1">Aturan eksplisit</p>
              </div>
              <div className="border border-slate-200 rounded-lg p-2.5 bg-white">
                <p className="text-[9px] font-bold text-slate-400 uppercase mb-1">ML Probability</p>
                <p className={`text-xl font-black leading-none ${mlPct != null && mlPct >= 50 ? 'text-red-600' : mlPct != null && mlPct >= 30 ? 'text-amber-600' : 'text-slate-700'}`}>
                  {mlPct != null ? `${mlPct.toFixed(1)}%` : 'N/A'}
                </p>
                {mlPct != null && (
                  <div className="mt-1.5 h-1 bg-slate-100 rounded-full">
                    <div className={`h-full rounded-full ${mlPct >= 50 ? 'bg-red-500' : mlPct >= 30 ? 'bg-amber-400' : 'bg-emerald-500'}`}
                      style={{ width: `${Math.min(100, mlPct)}%` }} />
                  </div>
                )}
                <p className="text-[9px] text-slate-400 mt-1">{userDetail.model_type === 'new' ? 'New' : 'Existing'} model</p>
              </div>
            </div>

            {/* Breakdown */}
            {userDetail.risk_score_breakdown?.length > 0 && (
              <div>
                <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Penyebab Rule Score Tinggi</p>
                <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 bg-white">
                  {userDetail.risk_score_breakdown.map((item, i) => (
                    <div key={i} className="flex justify-between items-center px-2.5 py-1.5 gap-2">
                      <span className="text-slate-600 text-[10px] leading-tight">{item.label}</span>
                      <span className="font-bold text-orange-600 whitespace-nowrap text-[10px]">+{item.points}</span>
                    </div>
                  ))}
                  <div className="flex justify-between px-2.5 py-1.5 bg-slate-50">
                    <span className="font-bold text-slate-700 text-[10px]">Total</span>
                    <span className="font-black text-slate-900 text-[10px]">{rulePct}/100</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })()}

      {/* Suspicion Factors */}
      {userDetail.reasons?.length > 0 && (
        <div>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Faktor Kecurigaan</p>
          <div className="space-y-1">
            {userDetail.reasons.map((r, i) => (
              <div key={i} className="flex gap-2 text-[11px] text-red-700 bg-red-50 border border-red-100 p-2 rounded-lg leading-relaxed">
                <span className="flex-shrink-0">⚠</span>
                <span>{r}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Graph Connections */}
      <div>
        <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Relasi Graph</p>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Devices', value: userDetail.connected_devices.length, ids: userDetail.connected_devices },
            { label: 'Payments', value: userDetail.connected_payments.length, ids: userDetail.connected_payments },
            { label: 'Addresses', value: userDetail.connected_addresses.length, ids: userDetail.connected_addresses },
            { label: 'IP Addresses', value: userDetail.connected_ips.length, ids: userDetail.connected_ips },
          ].map(({ label, value, ids }) => (
            <div key={label} className="bg-slate-50 border border-slate-200 p-2 rounded-lg">
              <p className="text-[9px] text-slate-500 font-semibold">{label}</p>
              <p className="font-black text-slate-800 mt-0.5">{value}</p>
              {ids.length > 0 && (
                <p className="text-[9px] text-slate-400 mt-0.5 truncate">{ids.slice(0, 2).join(', ')}{ids.length > 2 ? '…' : ''}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function EntityDetailPanel({ entityDetail, onUserClick }: { entityDetail: EntityDetail; onUserClick: (uid: string) => void }) {
  const typeLabel = ENTITY_TYPE_LABELS[entityDetail.entity_type] || entityDetail.entity_type;
  const dotColor = ENTITY_COLORS[entityDetail.entity_type] || '#94a3b8';
  const highRiskCount = entityDetail.connected_users.filter(u => u.risk_category === 'High').length;

  return (
    <div className="space-y-4 text-xs">
      {/* Entity summary */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2">
        <div className="flex items-center gap-2">
          <span className="h-4 w-4 rounded-full flex-shrink-0" style={{ backgroundColor: dotColor }}></span>
          <span className="font-bold text-slate-800 text-sm">{typeLabel}</span>
        </div>
        <p className="text-slate-500">ID: <span className="font-mono font-bold text-slate-700">{entityDetail.entity_id}</span></p>
        <div className="flex gap-3 pt-1">
          <div className="text-center">
            <p className="text-lg font-black text-slate-900">{entityDetail.connected_users.length}</p>
            <p className="text-[9px] text-slate-400 uppercase">Akun Terhubung</p>
          </div>
          {highRiskCount > 0 && (
            <div className="text-center">
              <p className="text-lg font-black text-red-600">{highRiskCount}</p>
              <p className="text-[9px] text-slate-400 uppercase">High Risk</p>
            </div>
          )}
        </div>
        {entityDetail.connected_users.length >= 2 && (
          <div className="flex items-center gap-1.5 mt-1 bg-red-50 border border-red-100 rounded px-2 py-1">
            <span className="text-red-500">⚠</span>
            <span className="text-[10px] text-red-700 font-semibold">
              {typeLabel} ini digunakan bersama oleh {entityDetail.connected_users.length} akun
            </span>
          </div>
        )}
      </div>

      {/* Connected users list */}
      {entityDetail.connected_users.length > 0 && (
        <div>
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">
            Akun yang Menggunakan Entitas Ini
          </p>
          <div className="space-y-1.5">
            {entityDetail.connected_users.map(u => (
              <button
                key={u.uid}
                onClick={() => onUserClick(u.uid)}
                className="w-full flex items-center justify-between gap-2 bg-white border border-slate-200 hover:border-blue-400 hover:bg-blue-50 p-2.5 rounded-lg text-left transition-colors"
              >
                <div className="min-w-0">
                  <p className="font-bold text-slate-800 font-mono text-[11px]">{u.uid}</p>
                  {u.ftype && u.ftype !== 'normal' && (
                    <p className="text-[9px] text-slate-400 truncate">{u.ftype}</p>
                  )}
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <span className="text-[9px] text-slate-400">{u.risk_score ?? 0}</span>
                  <span className={`px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase ${RISK_BADGE[u.risk_category] || RISK_BADGE.Low}`}>
                    {u.risk_category}
                  </span>
                  <span className="text-slate-300 text-xs">›</span>
                </div>
              </button>
            ))}
          </div>
          {entityDetail.connected_users.length === 0 && (
            <p className="text-slate-400 italic text-[11px]">Tidak ada user terhubung di graph.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function GraphAnalyticsPage() {
  return (
    <Suspense fallback={
      <div className="flex flex-col items-center justify-center min-h-[70vh] gap-4">
        <div className="h-12 w-12 rounded-full border-4 border-slate-300 border-t-blue-600 animate-spin"></div>
        <p className="text-slate-500 font-medium animate-pulse">Memasang modul visualisasi jaringan…</p>
      </div>
    }>
      <GraphContent />
    </Suspense>
  );
}

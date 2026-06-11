"use client";

/**
 * Purpose: Render interactive fraud graph analytics and node detail panel.
 * Used by: /graph route in the Next.js app.
 * Depends on: backend graph/user APIs, react-force-graph-2d, Next navigation.
 * Public functions: GraphAnalyticsPage default export.
 * Side effects: Fetches graph and user details from the backend API.
 */

import { useEffect, useState, useRef, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { getGraphData, getUserDetails, GraphData, UserDetails } from '@/lib/api';
import dynamic from 'next/dynamic';

// Load react-force-graph-2d dynamically to avoid SSR errors
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
 ssr: false,
});

function GraphContent() {
 const searchParams = useSearchParams();
 const router = useRouter();
 const urlUserId = searchParams.get('user_id');

 // API query states
 const [searchUserId, setSearchUserId] = useState(urlUserId || '');
 const [riskCategoryFilter, setRiskCategoryFilter] = useState('');
 const [maxNodes, setMaxNodes] = useState(800);

 // Filter states (Frontend filtering)
 const [highRiskOnly, setHighRiskOnly] = useState(false);
 const [selectedFraudType, setSelectedFraudType] = useState('');

 // Graph data states
 const [graphData, setGraphData] = useState<GraphData | null>(null);
 const [filteredData, setFilteredData] = useState<{ nodes: any[]; links: any[] }>({ nodes: [], links: [] });
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 // Selected Node/User Details states
 const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
 const [userDetail, setUserDetail] = useState<UserDetails | null>(null);
 const [detailLoading, setDetailLoading] = useState(false);

 const graphRef = useRef<any>(null);

 // Fetch Graph Data from backend
 const fetchGraph = async () => {
 try {
 setLoading(true);
 setError(null);

 const data = await getGraphData({
 user_id: searchUserId || undefined,
 risk_category: riskCategoryFilter || undefined,
 max_nodes: maxNodes,
 });

 setGraphData(data);
 } catch (err) {
 console.error(err);
 setError('Gagal memuat data jaringan dari API backend.');
 } finally {
 setLoading(false);
 }
 };

 // Fetch graph on API filter changes
 useEffect(() => {
 fetchGraph();
 }, [searchUserId, riskCategoryFilter, maxNodes]);

 // Apply frontend filters whenever graphData, highRiskOnly, or selectedFraudType changes
 useEffect(() => {
 if (!graphData) {
 setFilteredData({ nodes: [], links: [] });
 return;
 }

 const nodes = [...graphData.nodes];
 const edges = [...graphData.edges];

 const userNodes = nodes.filter(n => n.type === 'user');
 const userNodeIds = new Set(userNodes.map(n => n.id));

 const isUserHighRisk = new Map<string, boolean>();
 userNodes.forEach(n => {
 isUserHighRisk.set(n.id, n.risk_category === 'High');
 });

 let usersToKeep = new Set(userNodeIds);
 if (highRiskOnly) {
 usersToKeep = new Set(
 Array.from(usersToKeep).filter(uid => isUserHighRisk.get(uid) === true)
 );
 }
 if (selectedFraudType) {
 usersToKeep = new Set(
 Array.from(usersToKeep).filter(uid => {
 const node = userNodes.find(n => n.id === uid);
 const nodeFraudType = node?.ftype || 'normal';
 return nodeFraudType.toLowerCase() === selectedFraudType.toLowerCase();
 })
 );
 }

 const filteredEdges = edges.filter(edge => {
 const srcId = typeof edge.source === 'object' ? (edge.source as any).id : edge.source;
 const tgtId = typeof edge.target === 'object' ? (edge.target as any).id : edge.target;

 const isSrcUser = userNodeIds.has(srcId);
 const isTgtUser = userNodeIds.has(tgtId);

 if (isSrcUser && !usersToKeep.has(srcId)) return false;
 if (isTgtUser && !usersToKeep.has(tgtId)) return false;

 return true;
 });

 const activeNodeIds = new Set<string>();
 filteredEdges.forEach(edge => {
 const srcId = typeof edge.source === 'object' ? (edge.source as any).id : edge.source;
 const tgtId = typeof edge.target === 'object' ? (edge.target as any).id : edge.target;
 activeNodeIds.add(srcId);
 activeNodeIds.add(tgtId);
 });

 if (searchUserId && userNodeIds.has(searchUserId)) {
 activeNodeIds.add(searchUserId);
 }

 const filteredNodes = nodes.filter(n => activeNodeIds.has(n.id));

 const filteredLinks = filteredEdges.map(edge => ({
 ...edge,
 source: edge.source,
 target: edge.target
 }));

 setFilteredData({
 nodes: filteredNodes,
 links: filteredLinks,
 });
 }, [graphData, highRiskOnly, selectedFraudType, searchUserId]);

 // Fetch User Details when node clicked
 useEffect(() => {
 if (!selectedNodeId) {
 setUserDetail(null);
 return;
 }

 const isUser = filteredData.nodes.some(n => n.id === selectedNodeId && n.type === 'user');
 if (!isUser) {
 setUserDetail(null);
 return;
 }

 async function fetchDetails() {
 try {
 setDetailLoading(true);
 const data = await getUserDetails(selectedNodeId!);
 setUserDetail(data);
 } catch (err) {
 console.error(err);
 } finally {
 setDetailLoading(false);
 }
 }

 fetchDetails();
 }, [selectedNodeId, filteredData.nodes]);

 const handleClearSearch = () => {
 setSearchUserId('');
 router.replace('/graph');
 };

 // Node rendering helper inside Canvas
 const nodeCanvasObject = (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
 const fontSize = 10 / globalScale;
 ctx.font = `${fontSize}px sans-serif`;

 let radius = 6;
 let color = '#94a3b8';

 if (node.type === 'user') {
 radius = 8;
 if (node.risk_category === 'High') color = '#ef4444';
 else if (node.risk_category === 'Medium') color = '#f59e0b';
 else color = '#10b981';
 } else if (node.type === 'device') {
 radius = 5; color = '#3b82f6';
 } else if (node.type === 'address') {
 radius = 5; color = '#8b5cf6';
 } else if (node.type === 'payment') {
 radius = 5; color = '#ec4899';
 } else if (node.type === 'ip') {
 radius = 5; color = '#06b6d4';
 } else if (node.type === 'voucher') {
 radius = 5; color = '#eab308';
 }

 ctx.beginPath();
 ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
 ctx.fillStyle = color;
 ctx.fill();

 if (node.id === selectedNodeId) {
 ctx.beginPath();
 ctx.arc(node.x, node.y, radius + 3, 0, 2 * Math.PI, false);
 ctx.strokeStyle = '#334155';
 ctx.lineWidth = 1.5;
 ctx.stroke();
 }

 if (globalScale > 1.2) {
 const text = node.label || node.id;
 ctx.textAlign = 'center';
 ctx.textBaseline = 'top';
 ctx.fillStyle = '#475569';
 ctx.fillText(text, node.x, node.y + radius + 2);
 }
 };

 return (
 <div className="flex flex-col lg:flex-row min-h-[calc(100vh-8rem)] gap-6 px-4">

 {/* ── Left Control Panel ── */}
 <div className="w-full lg:w-80 flex-shrink-0 flex flex-col gap-6">

 {/* Filters card */}
 <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
 <div>
 <h2 className="text-xl font-bold text-slate-900">Graph Analytics</h2>
 <p className="text-xs text-slate-500 mt-1">Gunakan visualisasi peta hubungan untuk melacak ring fraud.</p>
 </div>

 <div className="space-y-3">
 {/* Search user ID */}
 <div>
 <label className="block text-xs font-semibold text-slate-500 mb-1">Cari Ego-Network (User ID)</label>
 <div className="flex gap-2">
 <input
 type="text"
 value={searchUserId}
 onChange={(e) => setSearchUserId(e.target.value)}
 placeholder="Contoh: USR00010"
 className="flex-1 px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-v-blue bg-white text-slate-800"
 />
 {searchUserId && (
 <button
 onClick={handleClearSearch}
 className="px-2.5 py-1 text-xs border border-slate-300 rounded-lg hover:bg-slate-100 text-slate-600 font-semibold"
 >
 Clear
 </button>
 )}
 </div>
 </div>

 {/* Risk Category Filter */}
 <div>
 <label className="block text-xs font-semibold text-slate-500 mb-1">Center on Risk Category</label>
 <select
 value={riskCategoryFilter}
 onChange={(e) => setRiskCategoryFilter(e.target.value)}
 className="w-full px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-v-blue bg-white text-slate-700"
 >
 <option value="">Semua (Pusatkan Acak)</option>
 <option value="High">High Risk Only</option>
 <option value="Medium">Medium Risk Only</option>
 <option value="Low">Low Risk Only</option>
 </select>
 </div>

 {/* Max Nodes */}
 <div>
 <label className="block text-xs font-semibold text-slate-500 mb-1">Maksimum Node di Layar: {maxNodes}</label>
 <input
 type="range"
 min="50"
 max="1500"
 step="50"
 value={maxNodes}
 onChange={(e) => setMaxNodes(parseInt(e.target.value))}
 className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-v-blue"
 />
 </div>

 {/* Frontend Filters */}
 <div className="pt-2 border-t border-slate-200 space-y-2">
 <span className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Saringan Tampilan</span>

 <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-600">
 <input
 type="checkbox"
 checked={highRiskOnly}
 onChange={(e) => setHighRiskOnly(e.target.checked)}
 className="rounded border-slate-300 text-v-blue focus:ring-v-blue h-4 w-4"
 />
 <span>Hanya Tampilkan Akun High Risk</span>
 </label>

 <div>
 <label className="block text-[10px] font-semibold text-slate-500 mb-1 mt-1">Saring berdasarkan Tipe Fraud</label>
 <select
 value={selectedFraudType}
 onChange={(e) => setSelectedFraudType(e.target.value)}
 className="w-full px-2 py-1 text-[11px] border border-slate-300 rounded focus:outline-none bg-white font-medium text-slate-600"
 >
 <option value="">Semua Tipe (Normal & Fraud)</option>
 <option value="normal">Normal (Bukan Fraud)</option>
 <option value="shared_device_abuse">Shared Device Abuse</option>
 <option value="shared_address_abuse">Shared Address Abuse</option>
 <option value="shared_payment_abuse">Shared Payment Abuse</option>
 <option value="voucher_farming">Voucher Farming</option>
 <option value="referral_abuse">Referral Abuse</option>
 </select>
 </div>
 </div>
 </div>
 </div>

 {/* Legend Panel */}
 <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
 <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Legenda Entitas</h4>
 <div className="grid grid-cols-2 gap-2 text-xs font-semibold text-slate-600">
 {[
 { color: 'bg-red-500', label: 'User (High)' },
 { color: 'bg-amber-500', label: 'User (Medium)' },
 { color: 'bg-emerald-500', label: 'User (Low)' },
 { color: 'bg-blue-500', label: 'Device' },
 { color: 'bg-purple-500', label: 'Address' },
 { color: 'bg-pink-500', label: 'Payment' },
 { color: 'bg-cyan-500', label: 'IP Address' },
 { color: 'bg-yellow-500', label: 'Voucher' },
 ].map(({ color, label }) => (
 <div key={label} className="flex items-center gap-2">
 <span className={`h-3.5 w-3.5 rounded-full ${color} inline-block`}></span>
 <span>{label}</span>
 </div>
 ))}
 </div>
 </div>
 </div>

 {/* ── Graph Visualizer Panel ── */}
 <div className="flex-1 bg-white border border-slate-200 rounded-xl shadow-sm relative overflow-hidden flex flex-col min-h-[500px]">
 {loading ? (
 <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-white/80 z-10">
 <div className="h-10 w-10 border-4 border-slate-200 border-t-v-blue rounded-full animate-spin"></div>
 <p className="text-slate-500 text-sm font-semibold animate-pulse">Menghitung hubungan graf...</p>
 </div>
 ) : error ? (
 <div className="flex-1 flex items-center justify-center text-red-600 font-medium">{error}</div>
 ) : (
 <div className="flex-1 relative">
 {/* Stats overlay badge — text gelap di bg putih */}
 <div className="absolute top-4 left-4 bg-white/95 text-slate-700 text-xs px-3 py-1.5 rounded-lg z-10 shadow border border-slate-200 pointer-events-none">
 <p className="font-semibold">Node: <strong>{filteredData.nodes.length}</strong> | Edge: <strong>{filteredData.links.length}</strong></p>
 <p className="text-[10px] text-slate-500 mt-0.5">Tip: Klik node User untuk membuka detail panel</p>
 </div>

 <ForceGraph2D
 ref={graphRef}
 graphData={filteredData}
 nodeCanvasObject={nodeCanvasObject}
 nodePointerAreaPaint={(node: any, color: string, ctx: CanvasRenderingContext2D) => {
 const radius = node.type === 'user' ? 8 : 5;
 ctx.fillStyle = color;
 ctx.beginPath();
 ctx.arc(node.x, node.y, radius + 6, 0, 2 * Math.PI, false);
 ctx.fill();
 }}
 nodeLabel={(node: any) => `${node.type.toUpperCase()}: ${node.id}`}
 linkDirectionalParticles={1}
 linkDirectionalParticleSpeed={0.005}
 linkColor={() => '#cbd5e1'}
 linkWidth={(link: any) => {
 const srcId = typeof link.source === 'object' ? link.source.id : link.source;
 const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
 return (srcId === selectedNodeId || tgtId === selectedNodeId) ? 2.5 : 1;
 }}
 onNodeClick={(node: any) => setSelectedNodeId(node.id)}
 />
 </div>
 )}
 </div>

 {/* ── Selected Node Details Side Panel ── */}
 {selectedNodeId && (
 <div className="w-full lg:w-96 flex-shrink-0 bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col gap-4">
 <div className="flex justify-between items-center border-b border-slate-100 pb-3">
 <div>
 <h3 className="font-bold text-slate-900 text-lg">Informasi Node</h3>
 <p className="text-xs text-slate-500 font-mono mt-0.5">{selectedNodeId}</p>
 </div>
 <button
 onClick={() => setSelectedNodeId(null)}
 className="text-xs font-bold text-slate-500 hover:text-slate-700 bg-slate-50 border border-slate-200 px-2 py-1 rounded"
 >
 Tutup
 </button>
 </div>

 {/* If selected node is a User, display full detailed profile */}
 {filteredData.nodes.find(n => n.id === selectedNodeId)?.type === 'user' ? (
 detailLoading ? (
 <div className="py-20 flex flex-col items-center justify-center gap-3">
 <div className="h-8 w-8 border-4 border-slate-200 border-t-v-blue rounded-full animate-spin"></div>
 <span className="text-slate-500 text-xs font-semibold animate-pulse">Menghubungkan profil...</span>
 </div>
 ) : userDetail ? (
 <div className="space-y-4 text-xs pr-1">
 {/* Profile Widget */}
 <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
 <div className="flex justify-between items-center mb-2.5">
 <span className="font-bold text-slate-900 text-sm">{userDetail.full_name || 'N/A'}</span>
 <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] uppercase ${
 userDetail.risk_category === 'High' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
 }`}>
 {userDetail.risk_category} Risk
 </span>
 </div>
 <p className="text-slate-500">Email: <span className="font-bold text-slate-700">{userDetail.email}</span></p>
 <p className="text-slate-500 mt-1">Kota: <span className="font-bold text-slate-700">{userDetail.city}, {userDetail.province}</span></p>
 </div>

 {/* Risk Indicators */}
 <div className="space-y-1">
 <span className="block font-bold text-slate-500 uppercase tracking-wider text-[10px]">Indikator Risiko</span>
 {userDetail.reasons && userDetail.reasons.length > 0 ? (
 userDetail.reasons.map((r, i) => (
 <div key={i} className="text-red-700 bg-red-50 border border-red-100 p-2 rounded text-[11px] leading-relaxed">
 🚨 {r}
 </div>
 ))
 ) : (
 <span className="text-slate-500 italic">Tidak ada pemicu risiko khusus.</span>
 )}
 </div>

 {/* Connected network items */}
 <div className="space-y-1.5">
 <span className="block font-bold text-slate-500 uppercase tracking-wider text-[10px]">Relasi Peta Jaringan</span>
 <div className="grid grid-cols-2 gap-2 text-[11px]">
 {[
 { label: 'Shared Devices', value: `${userDetail.connected_devices.length} Perangkat` },
 { label: 'Shared Payments', value: `${userDetail.connected_payments.length} Alat` },
 { label: 'Shared Addresses', value: `${userDetail.connected_addresses.length} Alamat` },
 { label: 'Shared IPs', value: `${userDetail.connected_ips.length} IP Address` },
 ].map(({ label, value }) => (
 <div key={label} className="bg-slate-50 border border-slate-200 p-2 rounded">
 <p className="text-slate-500">{label}</p>
 <p className="font-bold text-slate-800 mt-0.5">{value}</p>
 </div>
 ))}
 </div>
 </div>
 </div>
 ) : (
 <div className="text-slate-500 text-center py-10">Gagal mengambil informasi profil user.</div>
 )
 ) : (
 /* Selected Node is NOT a User */
 <div className="text-xs space-y-4">
 <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
 <p className="text-slate-500 uppercase font-bold text-[10px]">Tipe Entitas</p>
 <p className="text-sm font-bold text-slate-800 mt-0.5 uppercase">
 {filteredData.nodes.find(n => n.id === selectedNodeId)?.type}
 </p>

 <p className="text-slate-500 uppercase font-bold text-[10px] mt-4">Hubungan Terhubung</p>
 <p className="text-slate-700 font-medium mt-0.5">
 Entitas ini terhubung dengan <span className="font-bold">{
 filteredData.links.filter(edge => {
 const srcId = typeof edge.source === 'object' ? (edge.source as any).id : edge.source;
 const tgtId = typeof edge.target === 'object' ? (edge.target as any).id : edge.target;
 return srcId === selectedNodeId || tgtId === selectedNodeId;
 }).length
 }</span> akun atau entitas lainnya dalam graf di layar.
 </p>
 </div>
 </div>
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
 <div className="h-12 w-12 rounded-full border-4 border-slate-300 border-t-v-blue animate-spin"></div>
 <p className="text-slate-500 font-medium animate-pulse">Memasang modul visualisasi jaringan...</p>
 </div>
 }>
 <GraphContent />
 </Suspense>
 );
}

"use client";

/**
 * Purpose: Render risk scoring table, filters, pagination, and user detail drawer.
 * Used by: /risk route in the Next.js app.
 * Depends on: backend user/detail APIs from src/lib/api and Next Link.
 * Public functions: RiskScoringPage default export.
 * Side effects: Fetches filtered users and selected user details from the backend API.
 */

import { useEffect, useState } from 'react';
import { listUsers, getUserDetails, RiskUser, UserDetails } from '@/lib/api';

function combinedCategory(ruleScore: number, mlProb: number | null, criticalTrigger = false): string {
  if (criticalTrigger || ruleScore >= 70 || (mlProb != null && mlProb >= 0.85)) return 'High';
  if (ruleScore >= 40 || (mlProb != null && mlProb >= 0.60)) return 'Medium';
  return 'Low';
}

function isConflict(ruleScore: number, mlProb: number | null): boolean {
  if (mlProb == null) return false;
  return (ruleScore < 40 && mlProb >= 0.85) || (ruleScore >= 70 && mlProb < 0.60);
}

const COMBINED_STYLE: Record<string, { badge: string; bar: string; text: string }> = {
  High:   { badge: 'bg-red-100 text-red-700 border border-red-300',    bar: 'bg-red-500',    text: 'text-red-700' },
  Medium: { badge: 'bg-amber-100 text-amber-700 border border-amber-300', bar: 'bg-amber-400', text: 'text-amber-700' },
  Low:    { badge: 'bg-emerald-100 text-emerald-700 border border-emerald-300', bar: 'bg-emerald-500', text: 'text-emerald-700' },
};

const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string; dot: string }> = {
  'Account Creation Abuse': { bg: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200', dot: 'bg-orange-400' },
  'Identity Sharing':       { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200', dot: 'bg-purple-400' },
  'Behavioral Abuse':       { bg: 'bg-red-50',    text: 'text-red-700',    border: 'border-red-200',    dot: 'bg-red-400'    },
  'Network Fraud':          { bg: 'bg-rose-50',   text: 'text-rose-700',   border: 'border-rose-200',   dot: 'bg-rose-400'   },
};

function RiskAssessmentBlock({ userDetail }: { userDetail: UserDetails }) {
  const combined = userDetail.combined_risk_category || userDetail.risk_category || 'Low';
  const style = COMBINED_STYLE[combined] || COMBINED_STYLE.Low;
  const mlPct = userDetail.ml_probability !== null && userDetail.ml_probability !== undefined
    ? userDetail.ml_probability * 100 : null;
  const rulePct = userDetail.risk_score_rule_based;
  const rawPts  = userDetail.raw_rule_points ?? rulePct;
  const hasCritical = userDetail.critical_trigger ?? false;

  // Group breakdown by category
  const grouped: Record<string, typeof userDetail.risk_score_breakdown> = {};
  for (const item of (userDetail.risk_score_breakdown || [])) {
    const cat = item.category || 'Other';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(item);
  }

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Hasil Assessment Risiko</h4>

      {/* Final verdict */}
      <div className={`rounded-xl border p-4 ${style.badge}`}>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] font-bold uppercase tracking-widest opacity-70">Penilaian Akhir</span>
          <span className={`text-xs font-black uppercase tracking-wider px-2 py-0.5 rounded-full ${style.badge}`}>
            {combined} RISK
          </span>
        </div>
        <p className="text-[11px] opacity-80 leading-relaxed">
          {combined === 'High'
            ? 'Akun ini memiliki sinyal risiko tinggi. Perlu investigasi segera.'
            : combined === 'Medium'
            ? 'Akun ini menunjukkan pola mencurigakan. Perlu pemantauan lebih lanjut.'
            : 'Tidak ada sinyal risiko signifikan yang terdeteksi.'}
        </p>
      </div>

      {/* Critical trigger banner */}
      {hasCritical && (
        <div className="flex gap-2 bg-red-50 border border-red-300 rounded-lg p-3 text-xs text-red-800">
          <span className="flex-shrink-0 font-bold text-red-500">&#9888;</span>
          <div>
            <p className="font-bold">Critical Trigger Aktif</p>
            <p className="mt-0.5 opacity-80">
              Salah satu sinyal ekstrem terdeteksi (device sharing &gt;10, payment sharing &gt;5, referral ring &gt;100, atau login &gt;20x/jam). Risiko otomatis dikategorikan HIGH.
            </p>
          </div>
        </div>
      )}

      {/* Conflict warning */}
      {userDetail.score_conflict && (
        <div className="flex gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800">
          <span className="flex-shrink-0 text-amber-500">&#9888;</span>
          <div>
            <p className="font-bold">Sinyal Tidak Konsisten</p>
            <p className="mt-0.5 opacity-80">
              Rule-based dan ML model memberikan sinyal yang bertentangan. Perlu investigasi manual.
            </p>
          </div>
        </div>
      )}

      {/* Two pillars */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {/* Rule score */}
        <div className="border border-slate-200 rounded-lg p-3 bg-white">
          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">Rule Score</p>
          <p className="text-2xl font-black text-slate-900 font-mono leading-none">
            {rulePct}<span className="text-sm font-bold text-slate-400">/100</span>
          </p>
          {rawPts > 100 && (
            <p className="text-[9px] text-slate-400 mt-0.5">Raw poin: {Math.round(rawPts)} (di-cap 100)</p>
          )}
          <div className="mt-2 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div className={`h-full rounded-full ${rulePct >= 70 ? 'bg-red-500' : rulePct >= 40 ? 'bg-amber-400' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, rulePct)}%` }} />
          </div>
          <p className="text-[9px] text-slate-400 mt-1.5">HIGH ≥ 70 · MED ≥ 40</p>
        </div>

        {/* ML score */}
        <div className="border border-slate-200 rounded-lg p-3 bg-white">
          <p className="text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1">ML Probability</p>
          <p className={`text-2xl font-black font-mono leading-none ${mlPct !== null && mlPct >= 85 ? 'text-red-600' : mlPct !== null && mlPct >= 60 ? 'text-amber-600' : 'text-slate-700'}`}>
            {mlPct !== null ? `${mlPct.toFixed(1)}%` : 'N/A'}
          </p>
          {mlPct !== null && (
            <div className="mt-2 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${mlPct >= 85 ? 'bg-red-500' : mlPct >= 60 ? 'bg-amber-400' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(100, mlPct)}%` }} />
            </div>
          )}
          <p className="text-[9px] text-slate-400 mt-1.5">
            <span className={`font-bold px-1 py-0.5 rounded ${userDetail.model_type === 'new' ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-500'}`}>
              {userDetail.model_type === 'new' ? 'New' : 'Existing'} model
            </span>
            {' '}HIGH ≥ 85%
          </p>
        </div>
      </div>

      {/* Breakdown by category */}
      {Object.keys(grouped).length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Rule Breakdown</p>
            <p className="text-[9px] text-slate-400">
              Rule Score dihitung dari bobot tertinggi per fitur, di-cap 100
            </p>
          </div>
          {Object.entries(grouped).map(([cat, items]) => {
            const cc = CATEGORY_COLORS[cat] || { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200', dot: 'bg-slate-400' };
            const catTotal = items.reduce((s, r) => s + r.points, 0);
            return (
              <div key={cat} className={`rounded-lg border ${cc.border} overflow-hidden`}>
                {/* Category header */}
                <div className={`flex items-center justify-between px-3 py-1.5 ${cc.bg}`}>
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${cc.dot}`} />
                    <span className={`text-[10px] font-bold ${cc.text}`}>{cat}</span>
                  </div>
                  <span className={`text-[10px] font-black ${cc.text}`}>+{catTotal} pts</span>
                </div>
                {/* Rules */}
                <div className="divide-y divide-slate-100 bg-white">
                  {items.map((item, i) => (
                    <div key={i} className="flex items-center justify-between px-3 py-2 gap-2">
                      <span className="text-slate-600 text-[11px] leading-tight flex-1">{item.label}</span>
                      <span className="font-bold text-orange-600 whitespace-nowrap text-xs">+{item.points}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

          {/* Total row */}
          <div className="flex justify-between items-center px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="text-[11px] text-slate-600">
              <span className="font-bold text-slate-800">Total Rule Score</span>
              {rawPts > 100 && <span className="text-[9px] text-slate-400 ml-1">(raw {Math.round(rawPts)} pts → cap 100)</span>}
            </div>
            <span className="font-black text-slate-900 text-sm">{rulePct}<span className="text-xs text-slate-400">/100</span></span>
          </div>
        </div>
      )}
    </div>
  );
}

export default function RiskScoringPage() {
 // Filter States
 const [search, setSearch] = useState('');
 const [riskCategory, setRiskCategory] = useState('');
 const [fraudType, setFraudType] = useState('');
 const [city, setCity] = useState('');
 const [deviceAbuse, setDeviceAbuse] = useState<boolean | null>(null);
 const [paymentAbuse, setPaymentAbuse] = useState<boolean | null>(null);
 const [addressAbuse, setAddressAbuse] = useState<boolean | null>(null);

 // Pagination & Loading
 const [users, setUsers] = useState<RiskUser[]>([]);
 const [total, setTotal] = useState(0);
 const [page, setPage] = useState(1);
 const [limit] = useState(15);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 // Selected User Detail Drawer State
 const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
 const [userDetail, setUserDetail] = useState<UserDetails | null>(null);
 const [detailLoading, setDetailLoading] = useState(false);

 // Fetch Users
 const fetchUserData = async () => {
 try {
 setLoading(true);
 setError(null);
 const data = await listUsers({
 page,
 limit,
 search: search || undefined,
 risk_category: riskCategory || undefined,
 fraud_type: fraudType || undefined,
 city: city || undefined,
 device_abuse: deviceAbuse !== null ? deviceAbuse : undefined,
 payment_abuse: paymentAbuse !== null ? paymentAbuse : undefined,
 address_abuse: addressAbuse !== null ? addressAbuse : undefined,
 });
 setUsers(data.users);
 setTotal(data.total);
 } catch (err: any) {
 console.error(err);
 setError('Gagal mengambil data pengguna dari backend.');
 } finally {
 setLoading(false);
 }
 };

 useEffect(() => {
 // Debounce/Fetch on filter/page changes
 const timer = setTimeout(() => {
 fetchUserData();
 }, 300);

 return () => clearTimeout(timer);
 }, [page, search, riskCategory, fraudType, city, deviceAbuse, paymentAbuse, addressAbuse]);

 // Fetch User Details when selected
 useEffect(() => {
 if (!selectedUserId) {
 setUserDetail(null);
 return;
 }

 async function fetchDetails() {
 try {
 setDetailLoading(true);
 const data = await getUserDetails(selectedUserId!);
 setUserDetail(data);
 } catch (err) {
 console.error(err);
 } finally {
 setDetailLoading(false);
 }
 }

 fetchDetails();
 }, [selectedUserId]);

 // Handle page resets on filter change
 const handleFilterChange = (updater: () => void) => {
 updater();
 setPage(1);
 };

 const totalPages = Math.ceil(total / limit);

 return (
 <div className="space-y-6 px-4 relative min-h-[80vh]">
 {/* Page Header */}
 <div>
 <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Risk Scoring & User Investigation</h1>
 <p className="text-slate-500 mt-1">Tinjau daftar risiko kecurangan setiap akun beserta indikator detailnya.</p>
 </div>

 {/* Filter Card */}
 <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
 <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Pencarian & Penyaringan</h3>
 
 <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
 {/* Search Box */}
 <div className="md:col-span-2">
 <label className="block text-xs font-semibold text-slate-500 mb-1">Cari Akun (ID, Nama, Email)</label>
 <input
 type="text"
 value={search}
 onChange={(e) => handleFilterChange(() => setSearch(e.target.value))}
 placeholder="Contoh: USR00010 atau rizki..."
 className="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-v-blue focus:border-v-blue"
 />
 </div>

 {/* Risk Category */}
 <div>
 <label className="block text-xs font-semibold text-slate-500 mb-1">Kategori Risiko</label>
 <select
 value={riskCategory}
 onChange={(e) => handleFilterChange(() => setRiskCategory(e.target.value))}
 className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-v-blue focus:border-v-blue bg-white "
 >
 <option value="">Semua Kategori</option>
 <option value="High">High Risk</option>
 <option value="Medium">Medium Risk</option>
 <option value="Low">Low Risk</option>
 </select>
 </div>

 {/* Fraud Type */}
 <div>
 <label className="block text-xs font-semibold text-slate-500 mb-1">Tipe Fraud (Dataset)</label>
 <select
 value={fraudType}
 onChange={(e) => handleFilterChange(() => setFraudType(e.target.value))}
 className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-v-blue focus:border-v-blue bg-white "
 >
 <option value="">Semua Label</option>
 <option value="normal">Normal (Bukan Fraud)</option>
 <option value="shared_device_abuse">Shared Device Abuse</option>
 <option value="shared_address_abuse">Shared Address Abuse</option>
 <option value="shared_payment_abuse">Shared Payment Abuse</option>
 <option value="voucher_farming">Voucher Farming</option>
 <option value="referral_abuse">Referral Abuse</option>
 </select>
 </div>
 </div>

 <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
 {/* City Filter */}
 <div>
 <label className="block text-xs font-semibold text-slate-500 mb-1">Kota Asal</label>
 <input
 type="text"
 value={city}
 onChange={(e) => handleFilterChange(() => setCity(e.target.value))}
 placeholder="Contoh: Jakarta Selatan"
 className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-v-blue focus:border-v-blue"
 />
 </div>

 {/* Device Abuse Switch */}
 <div className="flex flex-col justify-end">
 <label className="inline-flex items-center gap-2 cursor-pointer pb-2.5">
 <input
 type="checkbox"
 checked={deviceAbuse === true}
 onChange={(e) => handleFilterChange(() => setDeviceAbuse(e.target.checked ? true : null))}
 className="rounded border-slate-300 text-v-blue focus:ring-v-blue h-4.5 w-4.5"
 />
 <span className="text-xs font-semibold text-slate-500 ">Penyalahgunaan HP (Emulator/Sharing)</span>
 </label>
 </div>

 {/* Payment Abuse Switch */}
 <div className="flex flex-col justify-end">
 <label className="inline-flex items-center gap-2 cursor-pointer pb-2.5">
 <input
 type="checkbox"
 checked={paymentAbuse === true}
 onChange={(e) => handleFilterChange(() => setPaymentAbuse(e.target.checked ? true : null))}
 className="rounded border-slate-300 text-v-blue focus:ring-v-blue h-4.5 w-4.5"
 />
 <span className="text-xs font-semibold text-slate-500 ">Sharing Alat Pembayaran</span>
 </label>
 </div>

 {/* Address Abuse Switch */}
 <div className="flex flex-col justify-end">
 <label className="inline-flex items-center gap-2 cursor-pointer pb-2.5">
 <input
 type="checkbox"
 checked={addressAbuse === true}
 onChange={(e) => handleFilterChange(() => setAddressAbuse(e.target.checked ? true : null))}
 className="rounded border-slate-300 text-v-blue focus:ring-v-blue h-4.5 w-4.5"
 />
 <span className="text-xs font-semibold text-slate-500 ">Sharing Alamat Pengiriman</span>
 </label>
 </div>
 </div>
 </div>

 {/* Main Table Card */}
 <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
 {loading ? (
 <div className="py-20 flex flex-col items-center justify-center gap-4">
 <div className="h-10 w-10 border-4 border-slate-200 border-t-v-blue rounded-full animate-spin"></div>
 <p className="text-slate-500 text-sm font-medium animate-pulse">Menyaring data...</p>
 </div>
 ) : error ? (
 <div className="py-12 text-center text-red-500 font-medium px-4">{error}</div>
 ) : users.length === 0 ? (
 <div className="py-20 text-center text-slate-500 ">Tidak ada pengguna yang cocok dengan kriteria filter Anda.</div>
 ) : (
 <div>
 <div className="overflow-x-auto">
 <table className="min-w-full divide-y divide-slate-200 text-sm text-left">
 <thead>
 <tr className="text-slate-600 font-semibold bg-slate-50 text-xs">
 <th className="px-6 py-3">User ID</th>
 <th className="px-6 py-3">Nama Lengkap</th>
 <th className="px-6 py-3">Kota</th>
 <th className="px-6 py-3">
 <span className="block">Skor Aturan</span>
 <span className="block text-[10px] text-slate-400 font-normal">Rule-based (0–100)</span>
 </th>
 <th className="px-6 py-3">
 <span className="block">Kategori</span>
 <span className="block text-[10px] text-slate-400 font-normal">Gabungan ML + Aturan</span>
 </th>
 <th className="px-6 py-3">
 <span className="block">Prediksi Model</span>
 <span className="block text-[10px] text-slate-400 font-normal">ML – Existing Customer</span>
 </th>
 <th className="px-6 py-3">Indikator Teratas</th>
 <th className="px-6 py-3 text-right">Aksi</th>
 </tr>
 </thead>
 <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
 {users.map((user) => (
 <tr
 key={user.uid}
 className="hover:bg-slate-50 transition-colors cursor-pointer"
 onClick={() => setSelectedUserId(user.uid)}
 >
 <td className="px-6 py-4 font-bold text-slate-900 ">{user.uid}</td>
 <td className="px-6 py-4">{user.full_name || 'N/A'}</td>
 <td className="px-6 py-4 text-slate-500">{user.city || 'N/A'}</td>
 <td className="px-6 py-4">
 <span className="bg-slate-100 text-slate-800 px-2 py-0.5 rounded text-xs font-mono font-bold">
 {user.risk_score_rule_based}/100
 </span>
 </td>
 <td className="px-6 py-4">
 {(() => {
 const cat = combinedCategory(user.risk_score_rule_based, user.ml_probability);
 const conflict = isConflict(user.risk_score_rule_based, user.ml_probability);
 return (
 <div className="flex items-center gap-1.5">
 <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
 cat === 'High' ? 'bg-red-100 text-red-800'
 : cat === 'Medium' ? 'bg-amber-100 text-amber-800'
 : 'bg-emerald-100 text-emerald-800'
 }`}>
 {cat}
 </span>
 {conflict && (
 <span title="Rule-based dan ML tidak sinkron — perlu investigasi manual" className="text-amber-500 cursor-help text-sm leading-none">⚠</span>
 )}
 </div>
 );
 })()}
 </td>
 <td className="px-6 py-4">
 <span className={`inline-flex items-center gap-1.5 text-xs ${
 user.ml_prediction === 1 ? 'text-red-600 font-bold' : 'text-emerald-600'
 }`}>
 <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${user.ml_prediction === 1 ? 'bg-red-600' : 'bg-emerald-600'}`}></span>
 {user.ml_prediction === 1 ? 'Fake' : 'Normal'}
 {user.ml_probability !== null && (
 <span className="text-slate-500 font-normal">({(user.ml_probability * 100).toFixed(0)}%)</span>
 )}
 </span>
 </td>
 <td className="px-6 py-4 text-slate-500 max-w-xs truncate">{user.top_reason || '-'}</td>
 <td className="px-6 py-4 text-right">
 <button className="text-xs font-semibold text-v-blue hover:text-blue-700 bg-blue-50 hover:bg-blue-100/50 px-2.5 py-1 rounded transition-colors">
 Investigasi
 </button>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>

 {/* Pagination UI */}
 <div className="bg-slate-50 px-6 py-4 border-t border-slate-200 flex items-center justify-between text-slate-500 text-xs font-semibold">
 <span>Menampilkan <span className="font-bold">{(page - 1) * limit + 1}</span> - <span className="font-bold">{Math.min(page * limit, total)}</span> dari <span className="font-bold">{total.toLocaleString()}</span> pengguna</span>
 <div className="flex gap-2">
 <button
 onClick={() => setPage((p) => Math.max(1, p - 1))}
 disabled={page === 1}
 className="px-3 py-1.5 border border-slate-300 rounded bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
 >
 Sebelumnya
 </button>
 <span className="flex items-center px-2 text-slate-700 font-bold">Halaman {page} dari {totalPages || 1}</span>
 <button
 onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
 disabled={page === totalPages || totalPages === 0}
 className="px-3 py-1.5 border border-slate-300 rounded bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
 >
 Selanjutnya
 </button>
 </div>
 </div>
 </div>
 )}
 </div>

 {/* Slide-over Detail Drawer Panel */}
 {selectedUserId && (
 <div className="fixed inset-0 overflow-hidden z-50">
 <div className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm transition-opacity" onClick={() => setSelectedUserId(null)} />
 
 <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
 <div className="pointer-events-auto w-screen max-w-md transform transition-all duration-300 ease-in-out bg-white shadow-2xl flex flex-col h-full border-l border-slate-200 ">
 
 {/* Drawer Header */}
 <div className="bg-white border-b border-slate-100 p-6 flex justify-between items-center">
 <div>
 <h2 className="text-xl font-bold tracking-tight">Investigasi Akun</h2>
 <p className="text-xs text-slate-500 mt-1">Detail kecurigaan dan relasi sistem</p>
 </div>
 <button
 onClick={() => setSelectedUserId(null)}
 className="text-slate-500 hover:bg-slate-200 hover:text-slate-900 rounded bg-slate-100 p-1.5 transition-colors focus:outline-none"
 >
 ✕
 </button>
 </div>

 {/* Drawer Content */}
 <div className="flex-1 overflow-y-auto p-6 space-y-6">
 {detailLoading ? (
 <div className="h-full flex flex-col items-center justify-center gap-4">
 <div className="h-10 w-10 border-4 border-slate-200 border-t-v-blue rounded-full animate-spin"></div>
 <p className="text-slate-500 text-xs font-semibold animate-pulse">Menghubungkan data relasi...</p>
 </div>
 ) : userDetail ? (
 <div className="space-y-6">
 {/* User profile */}
 <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 ">
 <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Informasi Profil</h4>
 <div className="grid grid-cols-2 gap-y-3 text-xs">
 <div>
 <p className="text-slate-500 ">User ID</p>
 <p className="font-bold text-slate-900 ">{userDetail.uid}</p>
 </div>
 <div>
 <p className="text-slate-500 ">Nama Lengkap</p>
 <p className="font-bold text-slate-900 ">{userDetail.full_name || 'N/A'}</p>
 </div>
 <div>
 <p className="text-slate-500 ">Email</p>
 <p className="font-bold text-slate-900 break-all">{userDetail.email || 'N/A'}</p>
 </div>
 <div>
 <p className="text-slate-500 ">Telepon</p>
 <p className="font-bold text-slate-900 ">{userDetail.phone_number || 'N/A'}</p>
 </div>
 <div>
 <p className="text-slate-500 ">Lokasi</p>
 <p className="font-bold text-slate-900 ">{userDetail.city || 'N/A'}, {userDetail.province || 'N/A'}</p>
 </div>
 <div>
 <p className="text-slate-500 ">Tanggal Registrasi</p>
 <p className="font-bold text-slate-900 ">{userDetail.registration_date?.split('T')[0] || 'N/A'}</p>
 </div>
 </div>
 </div>

 {/* Fraud Assessment */}
 <RiskAssessmentBlock userDetail={userDetail} />

 {/* Suspect indicators */}
 <div className="space-y-2">
 <div>
 <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Faktor Pemicu Kecurigaan</h4>
 <p className="text-[10px] text-slate-400 mt-0.5">Berdasarkan analisis pola fitur akun (bukan output model ML)</p>
 </div>
 {userDetail.reasons && userDetail.reasons.length > 0 ? (
 <div className="space-y-1.5">
 {userDetail.reasons.map((r, i) => (
 <div key={i} className="flex gap-2 text-xs text-red-700 bg-red-50 border border-red-100 p-2.5 rounded-lg leading-relaxed">
 <span>🚨</span>
 <span>{r}</span>
 </div>
 ))}
 </div>
 ) : (
 <p className="text-xs text-slate-500 italic">Tidak ada pemicu kecurigaan utama.</p>
 )}
 </div>

 {/* Graph Connections */}
 <div className="space-y-3">
 <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Relasi Sistem (Graph Connections)</h4>
 
 <div className="grid grid-cols-2 gap-3 text-xs">
 <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg">
 <p className="text-slate-500 font-semibold mb-1">Perangkat Bersama (Device)</p>
 <p className="font-bold text-slate-900 text-sm">{userDetail.connected_devices.length} Perangkat</p>
 {userDetail.connected_devices.length > 0 && (
 <p className="text-[10px] text-slate-500 mt-1 truncate">{userDetail.connected_devices.join(', ')}</p>
 )}
 </div>
 <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg">
 <p className="text-slate-500 font-semibold mb-1">Pembayaran Bersama</p>
 <p className="font-bold text-slate-900 text-sm">{userDetail.connected_payments.length} Alat</p>
 {userDetail.connected_payments.length > 0 && (
 <p className="text-[10px] text-slate-500 mt-1 truncate">{userDetail.connected_payments.join(', ')}</p>
 )}
 </div>
 <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg">
 <p className="text-slate-500 font-semibold mb-1">Alamat Bersama (Shipping)</p>
 <p className="font-bold text-slate-900 text-sm">{userDetail.connected_addresses.length} Alamat</p>
 {userDetail.connected_addresses.length > 0 && (
 <p className="text-[10px] text-slate-500 mt-1 truncate">{userDetail.connected_addresses.join(', ')}</p>
 )}
 </div>
 <div className="bg-slate-50 border border-slate-200 p-3 rounded-lg">
 <p className="text-slate-500 font-semibold mb-1">IP Login Bersama</p>
 <p className="font-bold text-slate-900 text-sm">{userDetail.connected_ips.length} IP Address</p>
 {userDetail.connected_ips.length > 0 && (
 <p className="text-[10px] text-slate-500 mt-1 truncate">{userDetail.connected_ips.join(', ')}</p>
 )}
 </div>
 </div>
 </div>

 {/* Key Behavioral Features */}
 <div className="space-y-2">
 <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Metrik Perilaku Utama</h4>
 <div className="border border-slate-200 rounded-lg divide-y divide-slate-100 text-xs bg-white shadow-sm">
 <div className="flex justify-between px-3 py-2">
 <span className="text-slate-500">Akun per Device Fingerprint</span>
 <span className="font-bold text-slate-700 ">{userDetail.features.max_acc_dev}</span>
 </div>
 <div className="flex justify-between px-3 py-2">
 <span className="text-slate-500">Akun per Shipping Address</span>
 <span className="font-bold text-slate-700 ">{userDetail.features.max_acc_addr}</span>
 </div>
 <div className="flex justify-between px-3 py-2">
 <span className="text-slate-500">Rasio Order dengan Promo/Voucher</span>
 <span className="font-bold text-slate-700 ">{(userDetail.features.promo_ratio * 100).toFixed(0)}%</span>
 </div>
 <div className="flex justify-between px-3 py-2">
 <span className="text-slate-500">Frekuensi Login (1 Jam / 24 Jam)</span>
 <span className="font-bold text-slate-700 ">{userDetail.features.login_v1h}x / {userDetail.features.login_v24h}x</span>
 </div>
 <div className="flex justify-between px-3 py-2">
 <span className="text-slate-500">Registrasi s.d Transaksi Pertama</span>
 <span className="font-bold text-slate-700 ">{userDetail.features.reg2txn_min.toFixed(0)} menit</span>
 </div>
 <div className="flex justify-between px-3 py-2">
 <span className="text-slate-500">Referral Ring Score</span>
 <span className="font-bold text-slate-700 ">{userDetail.features.ref_ring.toFixed(2)}</span>
 </div>
 </div>
 </div>
 </div>
 ) : (
 <div className="text-center text-slate-500 mt-20">Gagal memuat detail akun.</div>
 )}
 </div>

 {/* Drawer Footer */}
 <div className="bg-slate-50 border-t border-slate-200 p-4 flex gap-3">
 <button
 onClick={() => setSelectedUserId(null)}
 className="w-full border border-slate-300 hover:bg-slate-100 text-slate-700 hover:text-slate-900 font-bold text-xs py-3 rounded-lg transition-colors"
 >
 Tutup Panel
 </button>
 </div>

 </div>
 </div>
 </div>
 )}
 </div>
 );
}

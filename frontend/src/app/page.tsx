"use client";

import { useEffect, useState } from 'react';
import { getOverviewStats, listUsers, OverviewStats, RiskUser } from '@/lib/api';
import Link from 'next/link';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts';

export default function OverviewPage() {
 const [stats, setStats] = useState<OverviewStats | null>(null);
 const [topUsers, setTopUsers] = useState<RiskUser[]>([]);
 const [loading, setLoading] = useState(true);
 const [error, setError] = useState<string | null>(null);

 useEffect(() => {
 async function fetchData() {
 try {
 setLoading(true);
 const [overviewData, usersData] = await Promise.all([
 getOverviewStats(),
 listUsers({ limit: 5 })
 ]);
 setStats(overviewData);
 setTopUsers(usersData.users);
 } catch (err: any) {
 console.error(err);
 setError('Gagal memuat data dari server backend. Pastikan koneksi ke API tersedia.');
 } finally {
 setLoading(false);
 }
 }

 fetchData();
 }, []);

 if (loading) {
 return (
 <div className="flex flex-col items-center justify-center min-h-[70vh] gap-4">
 <div className="h-12 w-12 rounded-full border-4 border-slate-200 border-t-v-blue animate-spin"></div>
 <p className="text-slate-500 font-medium animate-pulse">Memuat dashboard data...</p>
 </div>
 );
 }

 if (error) {
 return (
 <div className="p-6 max-w-4xl mx-auto my-12 bg-red-50 border border-red-200 text-red-700 rounded-lg shadow-sm flex flex-col gap-4">
 <h3 className="text-xl font-bold flex items-center gap-2">⚠️ Gangguan Koneksi API</h3>
 <p className="text-sm leading-relaxed">{error}</p>
 </div>
 );
 }

 if (!stats) return null;

 const formatIDR = (value: number) => {
 return new Intl.NumberFormat('id-ID', {
 style: 'currency',
 currency: 'IDR',
 minimumFractionDigits: 0,
 maximumFractionDigits: 0
 }).format(value);
 };

 const accountData = [
 { name: 'Normal Accounts', value: stats.total_users - stats.total_fake_accounts },
 { name: 'Fake Accounts', value: stats.total_fake_accounts },
 ];
 const promoData = [
 { name: 'Safe Promo Usage', amount: stats.total_promo_discount - stats.estimated_promo_abuse_amount },
 { name: 'Abused Promo (Fakes)', amount: stats.estimated_promo_abuse_amount },
 ];

 return (
 <div className="flex flex-col w-full font-sans bg-slate-50 text-slate-900 pb-24 transition-colors duration-300">
 
 {/* Hero Section (Clean White with Blue Accents) */}
 <section className="bg-white border-b border-slate-200 pt-16 pb-32 px-4 relative overflow-hidden transition-colors duration-300">
 <div className="absolute top-0 right-0 w-96 h-96 bg-blue-50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3"></div>
 
 <div className="max-w-7xl mx-auto relative z-10">
 <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
 <div>
 <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-slate-900 max-w-4xl leading-tight">
 Fraud & Fake Account <span className="text-v-blue">Detection</span> Dashboard
 </h1>
 <p className="mt-4 text-lg text-slate-500 max-w-2xl leading-relaxed">
 Ringkasan Eksekutif Hasil Analisis Kecurangan Mobile App Retail Alfagift
 </p>
 </div>
 
 {/* Status Badge */}
 <div className="flex items-center gap-2 text-sm bg-emerald-50 border border-emerald-200 text-emerald-800 px-4 py-2 rounded-full self-start shadow-sm">
 <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
 <span className="font-semibold">Sistem Aktif & Terlindungi</span>
 </div>
 </div>
 </div>
 </section>

 {/* Floating Stats Card (Clean White card) */}
 <section className="max-w-7xl mx-auto px-4 w-full -mt-16 relative z-20">
 <div className="bg-white rounded-2xl shadow-lg p-6 md:p-8 flex flex-col md:flex-row items-center justify-between gap-6 md:gap-4 border border-slate-100 transition-colors duration-300">
 
 <div className="flex flex-col items-center text-center w-full">
 <span className="text-3xl md:text-5xl font-black text-v-blue tracking-tight">
 {stats.total_users.toLocaleString('id-ID')}
 </span>
 <span className="text-xs font-bold text-slate-500 tracking-wider uppercase mt-2">Total Users</span>
 <span className="text-[10px] text-slate-400 mt-1">Berdasarkan ABT terpadu</span>
 </div>
 
 <div className="hidden md:block w-px h-16 bg-slate-200"></div>
 
 <div className="flex flex-col items-center text-center w-full">
 <span className="text-3xl md:text-5xl font-black text-red-500 tracking-tight">
 {stats.total_fake_accounts.toLocaleString('id-ID')}
 </span>
 <span className="text-xs font-bold text-slate-500 tracking-wider uppercase mt-2">Total Akun Palsu (Fake)</span>
 <span className="text-[10px] text-red-500 mt-1 font-semibold">Rasio: {(stats.fake_account_rate * 100).toFixed(1)}%</span>
 </div>
 
 <div className="hidden md:block w-px h-16 bg-slate-200"></div>

 <div className="flex flex-col items-center text-center w-full">
 <span className="text-3xl md:text-5xl font-black text-amber-500 tracking-tight">
 {stats.high_risk_users.toLocaleString('id-ID')}
 </span>
 <span className="text-xs font-bold text-slate-500 tracking-wider uppercase mt-2">Akun Risiko Tinggi</span>
 <span className="text-[10px] text-slate-400 mt-1">Rule-Based Score &gt; 60</span>
 </div>

 <div className="hidden md:block w-px h-16 bg-slate-200"></div>

 <div className="flex flex-col items-center text-center w-full">
 <span className="text-3xl md:text-5xl font-black text-emerald-500 tracking-tight">
 {stats.total_transactions.toLocaleString('id-ID')}
 </span>
 <span className="text-xs font-bold text-slate-500 tracking-wider uppercase mt-2">Total Transaksi Belanja</span>
 <span className="text-[10px] text-slate-400 mt-1">Data transaksi terekam</span>
 </div>

 </div>
 </section>

 {/* Main Content Area */}
 <section className="max-w-7xl mx-auto px-4 w-full mt-12 space-y-8">
 
 {/* Financial Exposure Section */}
 <div className="bg-white border border-slate-200 rounded-2xl p-6 md:p-8 text-slate-900 shadow-sm relative overflow-hidden flex flex-col md:flex-row gap-8 transition-colors duration-300">
 <div className="absolute top-0 right-0 w-64 h-64 bg-red-50 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 opacity-60"></div>
 
 <div className="flex-1 relative z-10">
 <p className="text-xs font-bold text-red-500 uppercase tracking-wider">Total Subsidi Promo Diskon</p>
 <p className="text-4xl font-extrabold mt-2 tracking-tight">{formatIDR(stats.total_promo_discount)}</p>
 <p className="text-slate-500 text-sm mt-3 leading-relaxed max-w-md">
 Akumulasi nilai seluruh potongan harga dan voucher belanja yang disalurkan ke pengguna terdaftar.
 </p>
 </div>

 <div className="flex-1 border-t md:border-t-0 md:border-l border-slate-200 pt-6 md:pt-0 md:pl-8 flex flex-col justify-between relative z-10">
 <div>
 <p className="text-xs font-bold text-red-600 uppercase tracking-wider flex items-center gap-1.5">
 <span className="h-2 w-2 rounded-full bg-red-500 animate-ping"></span>
 Estimasi Eksploitasi Voucher (Abuse)
 </p>
 <p className="text-4xl font-extrabold text-red-600 mt-2 tracking-tight">
 {formatIDR(stats.estimated_promo_abuse_amount)}
 </p>
 </div>
 <div className="bg-red-50 border border-red-100 rounded-lg p-3 mt-4 flex items-center justify-between text-sm text-red-700">
 <span className="font-medium">Persentase Bocor:</span>
 <span className="font-bold text-lg">{((stats.estimated_promo_abuse_amount / stats.total_promo_discount) * 100).toFixed(1)}%</span>
 </div>
 </div>
 </div>

 {/* Charts Grid */}
 <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
 {/* Chart 1: Distribution */}
 <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm transition-colors duration-300">
 <h3 className="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
 <span className="w-1 h-5 rounded-full bg-emerald-500"></span>
 Distribusi Keamanan Akun
 </h3>
 <p className="text-slate-500 text-sm mb-8">Proporsi akun yang aman dibandingkan dengan akun palsu yang terdeteksi oleh sistem AI.</p>
 
 <div className="h-64">
 <ResponsiveContainer width="100%" height="100%">
 <PieChart>
 <Pie
 data={accountData}
 cx="50%"
 cy="50%"
 innerRadius={70}
 outerRadius={90}
 paddingAngle={5}
 dataKey="value"
 stroke="none"
 >
 <Cell fill="#10B981" />
 <Cell fill="#EF4444" />
 </Pie>
 <Tooltip 
 contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', backgroundColor: '#ffffff', color: '#111827' }} 
 formatter={(value) => [`${Number(value).toLocaleString('id-ID')} Akun`, '']}
 />
 </PieChart>
 </ResponsiveContainer>
 </div>
 </div>

 {/* Chart 2: Promo Exposure */}
 <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm transition-colors duration-300">
 <h3 className="text-xl font-bold text-slate-900 mb-2 flex items-center gap-2">
 <span className="w-1 h-5 rounded-full bg-v-blue"></span>
 Paparan Risiko Finansial
 </h3>
 <p className="text-slate-500 text-sm mb-8">Perbandingan subsidi promo yang dimanfaatkan pengguna asli vs dieksploitasi oleh botnet.</p>
 
 <div className="h-64">
 <ResponsiveContainer width="100%" height="100%">
 <BarChart data={promoData} barSize={40} margin={{ left: 20 }}>
 <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#64748b', fontSize: 12}} dy={10} />
 <YAxis axisLine={false} tickLine={false} tickFormatter={(v) => `Rp${v/1000000}M`} tick={{fill: '#94a3b8', fontSize: 11}} />
 <Tooltip 
 cursor={{fill: 'rgba(148, 163, 184, 0.1)'}} 
 contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', backgroundColor: '#ffffff', color: '#111827' }} 
 formatter={(value) => [formatIDR(Number(value)), 'Amount']}
 />
 <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
 <Cell fill="#2563EB" />
 <Cell fill="#EF4444" />
 </Bar>
 </BarChart>
 </ResponsiveContainer>
 </div>
 </div>
 </div>

 {/* Quick Suspicious User Summary Table */}
 <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden transition-colors duration-300">
 <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
 <div>
 <h3 className="text-xl font-bold text-slate-900">Daftar Teratas Akun Mencurigakan</h3>
 <p className="text-sm text-slate-500 mt-1">Daftar pengguna dengan tingkat kecurigaan tertinggi berdasarkan skoring</p>
 </div>
 <Link
 href="/risk"
 className="text-sm font-bold text-v-blue hover:text-blue-700 bg-blue-50 hover:bg-blue-100 px-4 py-2 rounded-lg transition-colors whitespace-nowrap"
 >
 Lihat Semua Tabel &rarr;
 </Link>
 </div>

 <div className="overflow-x-auto">
 <table className="min-w-full divide-y divide-slate-200 text-sm text-left">
 <thead className="bg-slate-50">
 <tr>
 <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">User ID</th>
 <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Nama Lengkap</th>
 <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Skor Aturan</th>
 <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Probabilitas ML</th>
 <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Kategori Risiko</th>
 <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Modus Kecurigaan</th>
 </tr>
 </thead>
 <tbody className="bg-white divide-y divide-slate-100 font-medium">
 {topUsers.map((user) => (
 <tr key={user.uid} className="hover:bg-slate-50 transition-colors">
 <td className="px-6 py-4 text-slate-900 font-bold">{user.uid}</td>
 <td className="px-6 py-4 text-slate-600">{user.full_name || 'N/A'}</td>
 <td className="px-6 py-4">
 <span className="bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-mono font-bold border border-slate-200">
 {user.risk_score_rule_based}/100
 </span>
 </td>
 <td className="px-6 py-4 text-slate-600 font-mono">
 {user.ml_probability !== null ? `${(user.ml_probability * 100).toFixed(1)}%` : 'N/A'}
 </td>
 <td className="px-6 py-4">
 <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-bold ${
 user.risk_category === 'High' ? 'bg-red-100 text-red-700' : 
 user.risk_category === 'Medium' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
 }`}>
 {user.risk_category}
 </span>
 </td>
 <td className="px-6 py-4">
 <span className="bg-red-50 text-red-600 px-2.5 py-1 rounded-md text-xs font-bold border border-red-100 uppercase tracking-wide">
 {user.ftype?.replace('_', ' ') || 'SUSPICIOUS'}
 </span>
 </td>
 </tr>
 ))}
 </tbody>
 </table>
 </div>
 </div>

 </section>
 </div>
 );
}

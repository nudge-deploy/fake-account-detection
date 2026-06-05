"use client";

import { useEffect, useState } from 'react';
import { getOverviewStats, listUsers, OverviewStats, RiskUser } from '@/lib/api';
import Link from 'next/link';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, Legend } from 'recharts';

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
        setError('Gagal memuat data dari server backend. Pastikan server FastAPI berjalan di port 8000.');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh] gap-4">
        <div className="h-12 w-12 rounded-full border-4 border-slate-300 border-t-red-600 animate-spin"></div>
        <p className="text-slate-500 font-medium animate-pulse">Memuat dashboard data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 max-w-4xl mx-auto my-12 bg-red-950/20 border border-red-800 text-red-300 rounded-lg shadow-lg flex flex-col gap-4">
        <h3 className="text-xl font-bold flex items-center gap-2">⚠️ Gangguan Koneksi API</h3>
        <p className="text-sm leading-relaxed">{error}</p>
        <div className="text-xs bg-black/40 p-3 rounded font-mono border border-red-950/50">
          Tip: Buka terminal dan jalankan: cd backend; python -m uvicorn app.main:app --reload
        </div>
      </div>
    );
  }

  if (!stats) return null;

  // Format currency to IDR
  const formatIDR = (value: number) => {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  // Pie chart data: Normal vs Fake Account
  const accountData = [
    { name: 'Normal Accounts', value: stats.total_users - stats.total_fake_accounts },
    { name: 'Fake Accounts', value: stats.total_fake_accounts },
  ];
  const COLORS_ACCOUNTS = ['#10b981', '#ef4444'];

  // Bar chart data: Promo discount allocation
  const promoData = [
    {
      name: 'Safe Promo Usage',
      amount: stats.total_promo_discount - stats.estimated_promo_abuse_amount,
    },
    {
      name: 'Abused Promo (Fakes)',
      amount: stats.estimated_promo_abuse_amount,
    },
  ];

  return (
    <div className="space-y-8 animate-fadeIn px-4">
      {/* Title Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">
            Fraud & Fake Account Detection Dashboard
          </h1>
          <p className="text-slate-500 mt-1">
            Ringkasan Eksekutif Hasil Analisis Kecurangan Mobile App Retail Alfagift
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm bg-slate-900 text-white px-3 py-1.5 rounded-full self-start">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping"></span>
          <span>Sistem Aktif & Terlindungi</span>
        </div>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Total Users */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="absolute top-0 right-0 h-24 w-24 bg-blue-50 rounded-full translate-x-8 -translate-y-8 opacity-40"></div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Users Teranalisis</p>
          <p className="text-3xl font-bold text-slate-100 mt-2">{stats.total_users.toLocaleString('id-ID')}</p>
          <div className="mt-4 flex items-center text-xs text-slate-500">
            <span>Berdasarkan ABT terpadu</span>
          </div>
        </div>

        {/* Total Fake Accounts */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="absolute top-0 right-0 h-24 w-24 bg-red-50 rounded-full translate-x-8 -translate-y-8 opacity-40"></div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Akun Palsu (Fake)</p>
          <p className="text-3xl font-bold text-red-600 mt-2">{stats.total_fake_accounts.toLocaleString('id-ID')}</p>
          <div className="mt-4 flex items-center text-xs text-red-500 font-medium">
            <span>Rasio Terdeteksi: {(stats.fake_account_rate * 100).toFixed(1)}%</span>
          </div>
        </div>

        {/* High Risk Users */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="absolute top-0 right-0 h-24 w-24 bg-orange-50 rounded-full translate-x-8 -translate-y-8 opacity-40"></div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Akun Risiko Tinggi (High Risk)</p>
          <p className="text-3xl font-bold text-amber-500 mt-2">{stats.high_risk_users.toLocaleString('id-ID')}</p>
          <div className="mt-4 flex items-center text-xs text-slate-500">
            <span>Rule-Based Score &gt; 60</span>
          </div>
        </div>

        {/* Total Transactions */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
          <div className="absolute top-0 right-0 h-24 w-24 bg-emerald-50 rounded-full translate-x-8 -translate-y-8 opacity-40"></div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Transaksi Belanja</p>
          <p className="text-3xl font-bold text-slate-100 mt-2">{stats.total_transactions.toLocaleString('id-ID')}</p>
          <div className="mt-4 flex items-center text-xs text-slate-500">
            <span>Data transaksi terekam</span>
          </div>
        </div>

      </div>

      {/* Financial Exposure Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-900 rounded-2xl p-6 md:p-8 text-white relative overflow-hidden shadow-xl">
        <div className="absolute inset-0 bg-gradient-to-r from-red-950/20 via-slate-900/10 to-transparent pointer-events-none"></div>
        
        <div>
          <p className="text-xs font-bold text-red-400 uppercase tracking-wider">Total Subsidi Promo Diskon</p>
          <p className="text-4xl font-extrabold mt-2 tracking-tight">{formatIDR(stats.total_promo_discount)}</p>
          <p className="text-slate-400 text-xs mt-3 leading-relaxed">
            Akumulasi nilai seluruh potongan harga dan voucher belanja yang disalurkan ke pengguna terdaftar.
          </p>
        </div>

        <div className="border-t md:border-t-0 md:border-l border-slate-800 pt-6 md:pt-0 md:pl-8 flex flex-col justify-between">
          <div>
            <p className="text-xs font-bold text-red-500 uppercase tracking-wider flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-red-500 animate-ping"></span>
              Estimasi Eksploitasi Voucher (Abuse)
            </p>
            <p className="text-4xl font-extrabold text-red-500 mt-2 tracking-tight">
              {formatIDR(stats.estimated_promo_abuse_amount)}
            </p>
          </div>
          <div className="bg-red-950/30 border border-red-900/30 rounded-lg p-2.5 mt-4 flex items-center justify-between text-xs text-red-300">
            <span>Persentase Bocor:</span>
            <span className="font-bold">{((stats.estimated_promo_abuse_amount / stats.total_promo_discount) * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Visualizations - Executive Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Account Proportion Chart */}
        <div className="bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 group-hover:bg-emerald-500/10 transition-colors duration-700"></div>
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-red-500/5 rounded-full blur-3xl translate-y-1/3 -translate-x-1/3 group-hover:bg-red-500/10 transition-colors duration-700"></div>
          
          <h3 className="text-xl font-bold text-white mb-2 relative z-10 flex items-center gap-2">
            <span className="h-4 w-1 bg-emerald-500 rounded-full"></span>
            Distribusi Keamanan Akun
          </h3>
          <p className="text-slate-400 text-xs mb-8 relative z-10">Proporsi akun yang aman dibandingkan dengan akun palsu yang terdeteksi oleh sistem AI.</p>
          
          <div className="h-72 flex items-center justify-center relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <defs>
                  <linearGradient id="colorNormal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#34d399" stopOpacity={1}/>
                    <stop offset="95%" stopColor="#059669" stopOpacity={1}/>
                  </linearGradient>
                  <linearGradient id="colorFake" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#fb7185" stopOpacity={1}/>
                    <stop offset="95%" stopColor="#e11d48" stopOpacity={1}/>
                  </linearGradient>
                </defs>
                <Pie
                  data={accountData}
                  cx="50%"
                  cy="50%"
                  innerRadius={75}
                  outerRadius={100}
                  paddingAngle={8}
                  dataKey="value"
                  stroke="none"
                  cornerRadius={6}
                >
                  {accountData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={index === 0 ? "url(#colorNormal)" : "url(#colorFake)"} 
                          style={{ filter: `drop-shadow(0px 4px 6px ${index === 0 ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'})` }} />
                  ))}
                </Pie>
                <Tooltip 
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-slate-800/90 backdrop-blur-md border border-slate-700 p-4 rounded-xl shadow-2xl">
                          <p className="text-white font-bold text-sm mb-1">{payload[0].name as string}</p>
                          <p className="text-lg font-extrabold" style={{ color: payload[0].payload?.fill?.includes('Normal') || String(payload[0].name).includes('Normal') ? '#34d399' : '#fb7185' }}>
                            {payload[0].value?.toLocaleString('id-ID')} Akun
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Legend 
                  layout="horizontal" 
                  verticalAlign="bottom" 
                  align="center"
                  iconType="circle"
                  wrapperStyle={{ paddingTop: '20px', fontSize: '12px', fontWeight: 'bold' }}
                />
              </PieChart>
            </ResponsiveContainer>
            
            {/* Center Label */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-[calc(50%+10px)] text-center pointer-events-none">
              <span className="block text-3xl font-black text-white tracking-tighter">
                {stats.total_users >= 1000 ? `${(stats.total_users/1000).toFixed(1)}k` : stats.total_users}
              </span>
              <span className="block text-[10px] uppercase font-bold text-slate-500 tracking-widest mt-1">Total Users</span>
            </div>
          </div>
        </div>

        {/* Promo Exposure Allocation */}
        <div className="bg-gradient-to-b from-slate-900 to-slate-950 border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-full h-full bg-gradient-to-br from-indigo-500/5 to-purple-500/5 opacity-50 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
          
          <h3 className="text-xl font-bold text-white mb-2 relative z-10 flex items-center gap-2">
            <span className="h-4 w-1 bg-indigo-500 rounded-full"></span>
            Paparan Risiko Finansial
          </h3>
          <p className="text-slate-400 text-xs mb-8 relative z-10">Perbandingan subsidi promo yang dimanfaatkan pengguna asli vs dieksploitasi oleh botnet.</p>
          
          <div className="h-72 flex items-center justify-center relative z-10">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={promoData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                barSize={45}
              >
                <defs>
                  <linearGradient id="barNormal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#818cf8" stopOpacity={1}/>
                    <stop offset="100%" stopColor="#4f46e5" stopOpacity={1}/>
                  </linearGradient>
                  <linearGradient id="barFake" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f472b6" stopOpacity={1}/>
                    <stop offset="100%" stopColor="#db2777" stopOpacity={1}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="name" 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 600 }}
                  dy={10}
                />
                <YAxis 
                  axisLine={false} 
                  tickLine={false} 
                  tickFormatter={(value) => `Rp${value / 1000000}M`}
                  tick={{ fill: '#64748b', fontSize: 10 }}
                />
                <Tooltip 
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      return (
                        <div className="bg-slate-800/90 backdrop-blur-md border border-slate-700 p-4 rounded-xl shadow-2xl">
                          <p className="text-slate-300 font-bold text-xs mb-1 uppercase tracking-wider">{payload[0].payload.name}</p>
                          <p className="text-xl font-black text-white">
                            {formatIDR(payload[0].value as number)}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar 
                  dataKey="amount" 
                  radius={[6, 6, 0, 0]}
                >
                  {promoData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={index === 0 ? "url(#barNormal)" : "url(#barFake)"} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Quick Suspicious User Summary Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-bold text-slate-100">Daftar Teratas Akun Mencurigakan</h3>
            <p className="text-xs text-slate-500 mt-1">Daftar pengguna dengan tingkat kecurigaan tertinggi</p>
          </div>
          <Link
            href="/risk"
            className="text-xs font-semibold text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100/80 px-3 py-1.5 rounded-lg transition-colors"
          >
            Lihat Semua Tabel &rarr;
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-800 text-sm text-left">
            <thead>
              <tr className="text-slate-400 font-semibold bg-slate-800/50">
                <th className="px-6 py-3 rounded-l-lg">User ID</th>
                <th className="px-6 py-3">Nama Lengkap</th>
                <th className="px-6 py-3">Skor Aturan</th>
                <th className="px-6 py-3">Probabilitas ML</th>
                <th className="px-6 py-3">Kategori Risiko</th>
                <th className="px-6 py-3 rounded-r-lg">Modus Kecurigaan</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-medium">
              {topUsers.map((user) => (
                <tr key={user.uid} className="hover:bg-slate-800/50/50 transition-colors">
                  <td className="px-6 py-4 text-white font-bold">{user.uid}</td>
                  <td className="px-6 py-4 text-slate-400">{user.full_name || 'N/A'}</td>
                  <td className="px-6 py-4 text-slate-300">
                    <span className="bg-slate-100 px-2 py-0.5 rounded text-xs font-mono font-bold">
                      {user.risk_score_rule_based}/100
                    </span>
                  </td>
                  <td className="px-6 py-4 text-slate-300 font-mono">
                    {user.ml_probability !== null ? `${(user.ml_probability * 100).toFixed(1)}%` : 'N/A'}
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${
                        user.risk_category === 'High'
                          ? 'bg-red-100 text-red-800'
                          : user.risk_category === 'Medium'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {user.risk_category}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="bg-red-50 text-red-600 px-2.5 py-1 rounded text-xs font-semibold border border-red-100 uppercase tracking-wide">
                      {user.ftype?.replace('_', ' ') || 'SUSPICIOUS'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

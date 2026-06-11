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
import Link from 'next/link';

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
 <tr className="text-slate-600 font-semibold bg-slate-50">
 <th className="px-6 py-3">User ID</th>
 <th className="px-6 py-3">Nama Lengkap</th>
 <th className="px-6 py-3">Kota</th>
 <th className="px-6 py-3">Skor Aturan</th>
 <th className="px-6 py-3">Kategori</th>
 <th className="px-6 py-3">Prediksi Model</th>
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
 <span className={`inline-flex items-center gap-1.5 ${
 user.ml_prediction === 1 ? 'text-red-600 font-bold' : 'text-emerald-600'
 }`}>
 <span className={`h-1.5 w-1.5 rounded-full ${user.ml_prediction === 1 ? 'bg-red-600' : 'bg-emerald-600'}`}></span>
 {user.ml_prediction === 1 ? 'Fake' : 'Normal'}
 {user.ml_probability !== null && ` (${(user.ml_probability * 100).toFixed(0)}%)`}
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
 <div className="space-y-3">
 <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Hasil Assessment Risiko</h4>
 <div className="grid grid-cols-2 gap-3 text-center">
 <div className="border border-slate-200 rounded-lg p-3 bg-white shadow-sm">
 <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Risk Score</p>
 <p className="text-xl font-black text-slate-900 mt-1 font-mono">{userDetail.risk_score_rule_based}/100</p>
 </div>
 <div className="border border-slate-200 rounded-lg p-3 bg-white shadow-sm">
 <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Model ML Probability</p>
 <p className="text-xl font-black text-red-600 mt-1 font-mono">
 {userDetail.ml_probability !== null ? `${(userDetail.ml_probability * 100).toFixed(1)}%` : 'N/A'}
 </p>
 </div>
 </div>
 </div>

 {/* Suspect indicators */}
 <div className="space-y-2">
 <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Faktor Pemicu Kecurigaan</h4>
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
 <Link
 href={`/graph?user_id=${selectedUserId}`}
 onClick={() => setSelectedUserId(null)}
 className="flex-1 text-center bg-v-blue hover:bg-blue-600 text-white font-bold text-xs py-3 rounded-lg shadow transition-colors"
 >
 Visualisasikan di Graph
 </Link>
 <button
 onClick={() => setSelectedUserId(null)}
 className="flex-1 border border-slate-300 hover:bg-slate-100 text-slate-700 hover:text-slate-900 font-bold text-xs py-3 rounded-lg transition-colors"
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

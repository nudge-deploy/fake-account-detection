"use client";

import { useState } from 'react';
import { predictRaw, PredictionResponse } from '@/lib/api';

export default function ModelInferencePage() {
  // Form input states with reasonable defaults representing a normal user
  const [accountsPerDevice, setAccountsPerDevice] = useState(1);
  const [accountsPerPayment, setAccountsPerPayment] = useState(1);
  const [accountsPerAddress, setAccountsPerAddress] = useState(1);
  const [promoOrderRatio, setPromoOrderRatio] = useState(0.2); // 20%
  const [loginF1h, setLoginF1h] = useState(1);
  const [loginF24h, setLoginF24h] = useState(2);
  const [signupToFirstTxn, setSignupToFirstTxn] = useState(120); // 2 hours

  // Result states
  const [result, setResult] = useState<PredictionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      
      // Map form states to raw feature payload for predictRaw API call
      const features = {
        max_acc_dev: accountsPerDevice,
        max_acc_pay: accountsPerPayment,
        max_acc_addr: accountsPerAddress,
        promo_ratio: promoOrderRatio,
        login_f1h: loginF1h,
        login_f24h: loginF24h,
        reg2txn_min: signupToFirstTxn,
      };

      const data = await predictRaw(features);
      setResult(data);
    } catch (err: any) {
      console.error(err);
      setError('Gagal menghubungkan model prediksi. Pastikan API backend FastAPI berjalan.');
    } finally {
      setLoading(false);
    }
  };

  const loadNormalPreset = () => {
    setAccountsPerDevice(1);
    setAccountsPerPayment(1);
    setAccountsPerAddress(1);
    setPromoOrderRatio(0.15);
    setLoginF1h(1);
    setLoginF24h(2);
    setSignupToFirstTxn(1440); // 1 day
  };

  const loadVoucherFarmerPreset = () => {
    setAccountsPerDevice(8);
    setAccountsPerPayment(4);
    setAccountsPerAddress(6);
    setPromoOrderRatio(0.95);
    setLoginF1h(5);
    setLoginF24h(25);
    setSignupToFirstTxn(4); // 4 minutes
  };

  return (
    <div className="space-y-6 px-4">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Model Inference Simulator</h1>
        <p className="text-slate-500 mt-1">Uji keandalan model Machine Learning dengan memasukkan parameter perilaku akun secara manual.</p>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        
        {/* Form Panel */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex justify-between items-center border-b border-slate-200 dark:border-slate-800 pb-3">
            <h3 className="font-bold text-slate-900 dark:text-white">Formulir Input Fitur</h3>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={loadNormalPreset}
                className="text-xs bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold px-2.5 py-1 rounded transition-colors"
              >
                Normal Preset
              </button>
              <button
                type="button"
                onClick={loadVoucherFarmerPreset}
                className="text-xs bg-blue-50 dark:bg-slate-800 hover:bg-blue-100 dark:hover:bg-slate-700 text-v-blue dark:text-blue-400 font-bold px-2.5 py-1 rounded transition-colors"
              >
                Bot Preset (Abuse)
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            
            {/* Accounts per Device */}
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Akun Terhubung per Device Fingerprint (Max): {accountsPerDevice}
              </label>
              <input
                type="range"
                min="1"
                max="15"
                value={accountsPerDevice}
                onChange={(e) => setAccountsPerDevice(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-v-blue"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Jumlah akun yang pernah didaftarkan/login pada perangkat yang sama.</span>
            </div>

            {/* Accounts per Payment */}
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Akun Terhubung per Alat Pembayaran (Max): {accountsPerPayment}
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={accountsPerPayment}
                onChange={(e) => setAccountsPerPayment(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-v-blue"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Jumlah akun belanja yang berbagi kartu kredit/nomor e-wallet yang sama.</span>
            </div>

            {/* Accounts per Address */}
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Akun Terhubung per Alamat Pengiriman (Max): {accountsPerAddress}
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={accountsPerAddress}
                onChange={(e) => setAccountsPerAddress(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-v-blue"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Jumlah akun belanja yang mengirimkan pesanan ke alamat yang sama.</span>
            </div>

            {/* Promo Order Ratio */}
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Rasio Order Menggunakan Voucher/Promo: {(promoOrderRatio * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={promoOrderRatio}
                onChange={(e) => setPromoOrderRatio(parseFloat(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-v-blue"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Persentase transaksi belanja yang memanfaatkan potongan harga/voucher diskon.</span>
            </div>

            {/* Login f1h */}
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Frekuensi Login 1 Jam Terakhir: {loginF1h}x
              </label>
              <input
                type="range"
                min="1"
                max="30"
                value={loginF1h}
                onChange={(e) => setLoginF1h(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-v-blue"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Jumlah aktivitas login / ganti akun dalam kurun 1 jam (indikasi bot).</span>
            </div>

            {/* Login f24h */}
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Frekuensi Login 24 Jam Terakhir: {loginF24h}x
              </label>
              <input
                type="range"
                min="1"
                max="100"
                value={loginF24h}
                onChange={(e) => setLoginF24h(parseInt(e.target.value))}
                className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-v-blue"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Jumlah aktivitas login dalam 24 jam terakhir.</span>
            </div>

            {/* Signup to First Transaction Minutes */}
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 mb-1">
                Waktu Registrasi s.d Transaksi Pertama: {signupToFirstTxn} Menit
              </label>
              <input
                type="number"
                min="1"
                max="10080" // 1 week
                value={signupToFirstTxn}
                onChange={(e) => setSignupToFirstTxn(parseInt(e.target.value) || 0)}
                className="w-full px-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-v-blue bg-white dark:bg-slate-900"
              />
              <span className="text-[10px] text-slate-500 dark:text-slate-400">Kecepatan belanja pasca pendaftaran. Bot/Voucher farmer biasanya bertransaksi &lt; 30 menit.</span>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-v-blue hover:bg-blue-600 disabled:bg-slate-200 dark:disabled:bg-slate-800 disabled:text-slate-500 text-white font-bold text-sm py-3 rounded-lg shadow-md transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Menganalisis Parameter...
                  </>
                ) : (
                  'Jalankan Prediksi Model ML'
                )}
              </button>
            </div>
            
          </form>
        </div>

        {/* Results Panel */}
        <div className="bg-white dark:bg-slate-900 text-white border border-slate-200 dark:border-slate-800 rounded-xl p-6 shadow-md min-h-[460px] flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 h-40 w-40 bg-slate-100 dark:bg-slate-800 rounded-full translate-x-12 -translate-y-12 opacity-30 pointer-events-none"></div>

          {error && (
            <div className="p-4 bg-red-950/40 border border-red-800 rounded-lg text-red-300 text-xs">
              ⚠️ {error}
            </div>
          )}

          {!result && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 gap-3 my-auto">
              <span className="text-4xl">🤖</span>
              <h4 className="font-bold text-slate-700 dark:text-slate-300">Siap Melakukan Prediksi</h4>
              <p className="text-xs text-slate-500 dark:text-slate-400 max-w-xs leading-relaxed">
                Silakan isi data parameter perilaku akun di panel sebelah kiri dan klik <span className="font-bold">Jalankan Prediksi Model ML</span> untuk memicu inferensi model.
              </p>
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 gap-4 my-auto">
              <div className="h-10 w-10 border-4 border-slate-300 dark:border-slate-700 border-t-v-blue rounded-full animate-spin"></div>
              <p className="text-xs text-slate-500 dark:text-slate-400 animate-pulse font-medium">Model sedang menghitung probabilitas kecurangan...</p>
            </div>
          )}

          {result && !loading && (
            <div className="space-y-6 flex-1 flex flex-col justify-between h-full">
              {/* Header result */}
              <div>
                <span className="text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider text-[10px]">Klasifikasi Hasil Inferensi</span>
                <div className="flex items-center gap-3 mt-1.5">
                  <h3 className={`text-2xl font-black tracking-tight ${
                    result.model_prediction === 1 ? 'text-red-500' : 'text-emerald-400'
                  }`}>
                    {result.model_prediction === 1 ? '🔴 FAKE ACCOUNT' : '✅ NORMAL ACCOUNT'}
                  </h3>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                    result.risk_category === 'High' ? 'bg-red-950 text-red-400 border border-red-900' : 'bg-emerald-950 text-emerald-400 border border-emerald-900'
                  }`}>
                    {result.risk_category} Risk
                  </span>
                </div>
              </div>

              {/* Score breakdown indicator */}
              <div className="space-y-2 bg-slate-950/40 p-4 rounded-xl border border-slate-800/60">
                <div className="flex justify-between items-center text-xs font-semibold">
                  <span className="text-slate-500 dark:text-slate-400">Probabilitas Kecurangan (ML)</span>
                  <span className={`font-mono font-bold text-sm ${result.model_prediction === 1 ? 'text-red-400' : 'text-emerald-400'}`}>
                    {(result.model_probability * 100).toFixed(1)}%
                  </span>
                </div>
                
                {/* Custom Progress bar */}
                <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                  <div
                    style={{ width: `${result.model_probability * 100}%` }}
                    className={`h-full rounded-full transition-all duration-500 ${
                      result.model_prediction === 1 ? 'bg-red-500' : 'bg-emerald-500'
                    }`}
                  ></div>
                </div>

                <div className="flex justify-between items-center text-[10px] text-slate-500 font-bold pt-1.5">
                  <span>Normal</span>
                  <span>Skor Aturan: {result.rule_based_score.toFixed(0)}/100</span>
                  <span>Suspicious</span>
                </div>
              </div>

              {/* Indicators checklist */}
              <div className="space-y-2">
                <span className="block font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-[10px]">Indikator Kecurigaan yang Terpicu</span>
                <div className="space-y-1.5 max-h-[160px] overflow-y-auto pr-1">
                  {result.reasons && result.reasons.length > 0 ? (
                    result.reasons.map((r, i) => (
                      <div key={i} className="flex gap-2 text-xs text-red-300 bg-red-950/20 border border-red-900/30 p-2.5 rounded-lg leading-relaxed">
                        <span>🚨</span>
                        <span>{r}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-slate-500 italic p-2 bg-slate-950/10 rounded">
                      Tidak ada indikator kecurigaan utama yang terpicu. Perilaku akun tergolong aman.
                    </div>
                  )}
                </div>
              </div>

              <p className="text-[10px] text-slate-500 leading-relaxed border-t border-slate-800/80 pt-3 mt-4">
                *Penilaian ini dilakukan secara lokal di memori backend menggunakan model koefisien Regresi Logistik dan formulasi skor aturan ABT.
              </p>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

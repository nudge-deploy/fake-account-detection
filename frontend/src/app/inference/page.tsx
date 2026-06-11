/*
Purpose: Lifecycle inference UI for the Alfagift fraud MVP simulation, including staged signup, sign-in, checkout, and order completion flows.
Used by: Frontend users simulating Alfagift mobile app fraud inference for new and existing customers.
Main dependencies: frontend/src/lib/api.ts and frontend API proxy routes for inference stage and journey requests.
Public/main functions: ModelInferencePage component.
Side effects: Triggers HTTP requests to inference APIs and loads existing user details for simulation autofill.
*/

"use client";

import { useEffect, useState } from 'react';
import {
 predictCheckoutStage,
 predictJourney,
 predictLoginStage,
 predictRegistrationStage,
 predictTransactionCompletedStage,
 getUserDetails,
 listUsers,
 LifecycleInferenceResponse,
 LifecycleStage,
 CustomerType,
 RiskUser,
 AlfagiftLifecyclePayload,
} from '@/lib/api';

const STAGES: { id: LifecycleStage; label: string; desc: string }[] = [
 { id: 'registration', label: '1. Sign Up', desc: 'Phone, email, device, referral' },
 { id: 'login', label: '2. Sign In', desc: 'IP and login frequency' },
 { id: 'checkout', label: '3. Place Order', desc: 'Shipping address and payment' },
 { id: 'transaction_completed', label: '4. Order Completed', desc: 'Order, voucher, reg to txn timing' },
];

const PAYMENT_METHODS = [
 'BCA',
 'BCA Debit',
 'BNI',
 'BRI',
 'Cash On Delivery',
 'Dana',
 'GoPay',
 'JCB',
 'LinkAja',
 'Mandiri',
 'Mandiri Debit',
 'Mastercard',
 'OVO',
 'QRIS National',
 'ShopeePay',
 'Visa',
];

const stageIndex = (s: LifecycleStage) => STAGES.findIndex((x) => x.id === s);

const extractErrorMessage = (err: unknown, fallback: string) => {
 if (err && typeof err === 'object') {
 const maybeAxiosError = err as {
 response?: { data?: unknown };
 message?: string;
 };
 const data = maybeAxiosError.response?.data;
 if (typeof data === 'string' && data.trim()) return data;
 if (data && typeof data === 'object') {
 const detail = (data as { detail?: unknown }).detail;
 if (typeof detail === 'string' && detail.trim()) return detail;
 if (Array.isArray(detail) && detail.length > 0) {
 const joined = detail
 .map((item) => {
 if (typeof item === 'string') return item;
 if (item && typeof item === 'object' && 'msg' in item) {
 return String((item as { msg?: unknown }).msg ?? '');
 }
 return '';
 })
 .filter(Boolean)
 .join(', ');
 if (joined) return joined;
 }
 }
 if (typeof maybeAxiosError.message === 'string' && maybeAxiosError.message.trim()) {
 return maybeAxiosError.message;
 }
 }
 return fallback;
};

const makeId = (prefix: string) => `${prefix}${Math.floor(10000 + Math.random() * 90000)}`;

const normalizeDeviceId = (value: string) =>
 (value || '').trim().replace(/^DEV[_-]?DEV/i, 'DEV');

const normalizeAddressId = (value: string) =>
 (value || '')
 .trim()
 .replace(/^ADDR[_-]?ADR/i, 'ADR')
 .replace(/^ADDR[_-]?ADDR/i, 'ADDR')
 .replace(/^ADDR(?=\d)/i, 'ADR');

const normalizeIp = (value: string) => {
 const out = (value || '').trim();
 if (out.startsWith('IP_')) return out.slice(3);
 return out;
};

const getVerdictTone = (r: LifecycleInferenceResponse) => {
 if (r.stage !== 'transaction_completed') return 'text-slate-600';
 if (r.is_fraud || r.is_suspicious) return 'text-red-600';
 return 'text-emerald-600';
};

const getRiskBadgeTone = (r: LifecycleInferenceResponse) => {
 if (r.stage !== 'transaction_completed') return 'bg-slate-100 text-slate-600';
 if (r.risk_category === 'High') return 'bg-red-100 text-red-700';
 if (r.risk_category === 'Medium') return 'bg-amber-100 text-amber-700';
 return 'bg-slate-100 text-slate-600';
};

const getFraudStatus = (r: LifecycleInferenceResponse) => {
 if (r.stage !== 'transaction_completed') return r.is_fraud || r.is_suspicious ? 'Fraud' : 'Tidak Fraud';
 return r.is_fraud ? 'Fraud' : 'Tidak Fraud';
};

const getFraudPercent = (r: LifecycleInferenceResponse) => (r.model_probability * 100).toFixed(1);

export default function ModelInferencePage() {
 const [customerType, setCustomerType] = useState<CustomerType>('new');
 const [stage, setStage] = useState<LifecycleStage>('registration');
 const [uid, setUid] = useState('');
 const [selectedUser, setSelectedUser] = useState<RiskUser | null>(null);
 const [existingUsers, setExistingUsers] = useState<RiskUser[]>([]);
 const [usersLoading, setUsersLoading] = useState(false);

const [phoneNumber, setPhoneNumber] = useState('081448398260');
const [email, setEmail] = useState('ivanmandala@hotmail.com');
const [fullName, setFullName] = useState('');
 const [dateOfBirth, setDateOfBirth] = useState('2001-05-10');
const [gender, setGender] = useState('Male');
const [maritalStatus, setMaritalStatus] = useState('Single');
const [password, setPassword] = useState('password-demo');
const [showPassword, setShowPassword] = useState(false);
const [isEmailVerified, setIsEmailVerified] = useState(false);
const [isPhoneVerified, setIsPhoneVerified] = useState(false);
const [loginPhoneNumber, setLoginPhoneNumber] = useState('081448398260');
 const [deviceId] = useState('');
 const [deviceFingerprint] = useState('');
 const [referralCode, setReferralCode] = useState('');
 const [ipAddress] = useState('');
 const [loginCount1h] = useState(1);
 const [loginCount24h] = useState(2);
 const [accountsOnSameIp] = useState(1);
 const [shippingAddress, setShippingAddress] = useState('');
 const [receiverName, setReceiverName] = useState('');
 const [receiverPhone, setReceiverPhone] = useState('');
 const [shippingMethod, setShippingMethod] = useState('Regular');
 const [addressId] = useState('');
 const [paymentIdentifier, setPaymentIdentifier] = useState('Dana');
 const [voucherCode, setVoucherCode] = useState('');
 const [orderAmount, setOrderAmount] = useState(150000);
 const [voucherUsed, setVoucherUsed] = useState(false);
 const [shippingFee, setShippingFee] = useState(15000);
 const [promoDiscount] = useState(0);
 const [generatedUserId, setGeneratedUserId] = useState('');
 const [generatedDeviceId, setGeneratedDeviceId] = useState('');
 const [generatedAddressId, setGeneratedAddressId] = useState('');
 const [generatedIpAddress, setGeneratedIpAddress] = useState('');
 const [signupAt, setSignupAt] = useState<number | null>(null);

 const [result, setResult] = useState<LifecycleInferenceResponse | null>(null);
 const [journeyResults, setJourneyResults] = useState<LifecycleInferenceResponse[] | null>(null);
 const [loading, setLoading] = useState(false);
 const [error, setError] = useState<string | null>(null);
 const finalAmount = Math.max(0, orderAmount + shippingFee - promoDiscount);

 useEffect(() => {
 const loadUsers = async () => {
 if (customerType !== 'existing') return;
 try {
 setUsersLoading(true);
 const data = await listUsers({ page: 1, limit: 25 });
 setExistingUsers(data.users);
 } catch (err) {
 console.error(err);
 } finally {
 setUsersLoading(false);
 }
 };
 loadUsers();
 if (customerType === 'existing') {
 setStage('login');
 } else {
 setStage('registration');
 setSelectedUser(null);
 }
 }, [customerType]);

 useEffect(() => {
 if (customerType === 'existing' && selectedUser) {
 setUid(selectedUser.uid);
 if (selectedUser.email) setEmail(selectedUser.email);
 setGeneratedUserId(selectedUser.uid);
 }
 }, [customerType, selectedUser]);

 useEffect(() => {
 if (customerType === 'new') {
 setLoginPhoneNumber(phoneNumber);
 }
 }, [customerType, phoneNumber]);

 useEffect(() => {
 const loadUserDetails = async () => {
 if (customerType !== 'existing' || !selectedUser?.uid) return;
 try {
 const details = await getUserDetails(selectedUser.uid);
 if (details.phone_number) setPhoneNumber(details.phone_number);
 if (details.email) setEmail(details.email);
 setLoginPhoneNumber(details.phone_number || '');
 if (details.connected_devices?.length > 0) setGeneratedDeviceId(normalizeDeviceId(details.connected_devices[0]));
 if (details.connected_addresses?.length > 0) setGeneratedAddressId(normalizeAddressId(details.connected_addresses[0]));
 if (details.connected_ips?.length > 0) setGeneratedIpAddress(normalizeIp(details.connected_ips[0]));
 setGeneratedUserId(details.uid);
 } catch (err) {
 console.error(err);
 }
 };
 loadUserDetails();
 }, [customerType, selectedUser]);

 const buildPayload = (overrides?: {
 userId?: string;
 deviceId?: string;
 ipAddress?: string;
 addressId?: string;
 }): AlfagiftLifecyclePayload => {
 const payload: AlfagiftLifecyclePayload = {};
 const idx = stageIndex(stage);
 const resolvedPhoneNumber = loginPhoneNumber || phoneNumber;
 const resolvedDeviceId = overrides?.deviceId || generatedDeviceId || deviceId || undefined;
 const resolvedIpAddress = overrides?.ipAddress || generatedIpAddress || ipAddress || undefined;
 const resolvedAddressId = overrides?.addressId || generatedAddressId || addressId || undefined;

if (idx >= 0) {
 payload.phone_number = stage === 'login' ? resolvedPhoneNumber : phoneNumber;
 payload.email = email;
 if (fullName && customerType === 'new') payload.full_name = fullName;
 if (customerType === 'new' && dateOfBirth) payload.date_of_birth = dateOfBirth;
 if (customerType === 'new') payload.registration_hour = new Date().getHours();
 if (customerType === 'new') payload.is_email_verified = isEmailVerified;
 if (customerType === 'new') payload.is_phone_verified = isPhoneVerified;
 if (customerType === 'new' || stage !== 'registration') {
 payload.device_id = resolvedDeviceId;
 if (deviceFingerprint) payload.device_fingerprint = deviceFingerprint;
 if (referralCode) payload.referral_code = referralCode;
 }
 }
 if (idx >= 1) {
 payload.ip_address = resolvedIpAddress;
 payload.login_count_1h = loginCount1h;
 payload.login_count_24h = loginCount24h;
 payload.accounts_on_same_ip = accountsOnSameIp;
 }
 if (idx >= 2) {
 payload.address_id = resolvedAddressId;
 if (paymentIdentifier) payload.payment_identifier = paymentIdentifier;
 }
 if (idx >= 3) {
 payload.order_amount = orderAmount;
 payload.voucher_used = voucherUsed;
 payload.promo_discount = promoDiscount;
 payload.minutes_since_registration = signupAt ? Math.max(1, Math.floor((Date.now() - signupAt) / 60000)) : 120;
 if (voucherUsed) payload.new_user_voucher = 1;
 }
 return payload;
 };

const buildFullJourneyPayload = (): AlfagiftLifecyclePayload => ({
 phone_number: customerType === 'existing' ? (loginPhoneNumber || phoneNumber) : phoneNumber,
 email,
 full_name: fullName || undefined,
 date_of_birth: customerType === 'new' ? dateOfBirth || undefined : undefined,
 registration_hour: customerType === 'new' ? new Date().getHours() : undefined,
 is_email_verified: customerType === 'new' ? isEmailVerified : undefined,
 is_phone_verified: customerType === 'new' ? isPhoneVerified : undefined,
 device_id: generatedDeviceId || deviceId || undefined,
 device_fingerprint: deviceFingerprint || undefined,
 referral_code: referralCode || undefined,
 ip_address: generatedIpAddress || ipAddress || undefined,
 login_count_1h: loginCount1h,
 login_count_24h: loginCount24h,
 accounts_on_same_ip: accountsOnSameIp,
 address_id: generatedAddressId || addressId || undefined,
 payment_identifier: paymentIdentifier || undefined,
 order_amount: orderAmount,
 voucher_used: voucherUsed,
 promo_discount: promoDiscount,
 minutes_since_registration: signupAt ? Math.max(1, Math.floor((Date.now() - signupAt) / 60000)) : 120,
 new_user_voucher: voucherUsed ? 1 : 0,
 });

 const handleSubmit = async (e: React.FormEvent) => {
 e.preventDefault();
 try {
 setLoading(true);
 setError(null);
 setJourneyResults(null);
 const effectiveUserId = generatedUserId || selectedUser?.uid || uid || makeId('USR');
 const effectiveDeviceId = generatedDeviceId || makeId('DEV');
 const effectiveIpAddress = normalizeIp(generatedIpAddress) || `103.${Math.floor(Math.random() * 200)}.${Math.floor(Math.random() * 200)}.${Math.floor(Math.random() * 200)}`;
 const effectiveAddressId = generatedAddressId || (shippingAddress ? makeId('ADR') : '');

 if (!generatedUserId) setGeneratedUserId(effectiveUserId);
 if (!generatedDeviceId) setGeneratedDeviceId(normalizeDeviceId(effectiveDeviceId));
 if (!generatedIpAddress) setGeneratedIpAddress(effectiveIpAddress);
 if (!generatedAddressId && effectiveAddressId) setGeneratedAddressId(normalizeAddressId(effectiveAddressId));
 if (!signupAt) setSignupAt(Date.now());

 const params = {
 customer_type: customerType,
 uid: effectiveUserId,
 payload: buildPayload({
 userId: effectiveUserId,
 deviceId: normalizeDeviceId(effectiveDeviceId),
 ipAddress: effectiveIpAddress,
 addressId: normalizeAddressId(effectiveAddressId),
 }),
 };
 const data =
 stage === 'registration'
 ? await predictRegistrationStage(params)
 : stage === 'login'
 ? await predictLoginStage(params)
 : stage === 'checkout'
 ? await predictCheckoutStage(params)
 : await predictTransactionCompletedStage(params);
 setResult(data);
} catch (err) {
 console.error(err);
 setError(extractErrorMessage(err, 'Failed to run inference. Make sure the FastAPI backend is running on port 8000.'));
} finally {
 setLoading(false);
}
 };

 const handleJourney = async () => {
 try {
 setLoading(true);
 setError(null);
 setResult(null);
 const data = await predictJourney({
 customer_type: customerType,
 uid: generatedUserId || uid || selectedUser?.uid || undefined,
 payload: buildFullJourneyPayload(),
 });
 setJourneyResults(data.results);
} catch (err) {
 console.error(err);
 setError(extractErrorMessage(err, 'Failed to run the inference journey.'));
} finally {
 setLoading(false);
}
 };

 const displayResult = result;
 const resultsToShow = journeyResults || (displayResult ? [displayResult] : []);

const renderResultCard = (
 r: LifecycleInferenceResponse,
 showDelta?: LifecycleInferenceResponse,
) => (
 <div key={r.stage} className="space-y-4 border border-slate-200 rounded-xl p-4 bg-slate-50">
 {showDelta && (
 <p className="text-[10px] text-amber-600 font-bold">
 Perubahan dari stage sebelumnya - Rule: {(r.rule_based_score - showDelta.rule_based_score).toFixed(0)}
 </p>
 )}
 <div className="flex items-center justify-between gap-2">
 <div>
 <p className="text-[10px] uppercase tracking-wider text-slate-500">{r.stage_label}</p>
 <h4 className={`text-lg font-black ${getVerdictTone(r)}`}>
 {getFraudStatus(r)}
 </h4>
 </div>
 <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getRiskBadgeTone(r)}`}>
 {r.risk_category}
 </span>
 </div>

 <div className="grid grid-cols-2 gap-2 text-xs text-slate-700">
 <div>Probabilitas: {getFraudPercent(r)}%</div>
 <div>Rule: {r.rule_based_score.toFixed(0)}/100</div>
 <div className="col-span-2 text-v-blue font-medium">Tipe fraud: {r.primary_fraud_label}</div>
 </div>

 {r.reasons.length > 0 && (
 <div className="space-y-1">
 {r.reasons.map((reason, i) => (
 <div key={i} className="text-[11px] text-red-700 bg-red-50 border border-red-200 p-2 rounded">
 {reason}
 </div>
 ))}
 </div>
 )}

 {r.ground_truth_fraud != null && (
 <p className="text-[10px] text-slate-500">
 Ground truth: {r.ground_truth_fraud ? 'FAKE' : 'NORMAL'} ({r.ground_truth_ftype || 'normal'})
 </p>
 )}
 </div>
 );

 return (
 <div className="space-y-6 px-4">
 <div>
 <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Alfagift Mobile Simulation</h1>
 <p className="text-slate-500 mt-1">
 Continuous fraud inference for the Alfagift lifecycle: registration, login, checkout, and transaction completed.
 </p>
 </div>

 <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
 <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-5">
 <div className="flex flex-wrap justify-between items-center gap-2 border-b border-slate-200 pb-3">
 <h3 className="font-bold text-slate-900 ">Mobile App Simulation</h3>
 </div>

 <div className="grid grid-cols-2 gap-3">
 <div>
 <label className="text-[10px] font-bold text-slate-500 uppercase">Tipe Pelanggan</label>
 <select
 value={customerType}
 onChange={(e) => setCustomerType(e.target.value as CustomerType)}
 className="w-full mt-1 text-xs border rounded-lg px-2 py-2 bg-white "
 >
 <option value="new">New customer</option>
 <option value="existing">Existing customer</option>
 </select>
 </div>
 </div>

 {customerType === 'existing' && (
 <div className="space-y-2">
 <label className="text-[10px] font-bold text-slate-500 uppercase">Choose Existing User</label>
 <select
 value={selectedUser?.uid || ''}
 onChange={(e) => {
 const picked = existingUsers.find((u) => u.uid === e.target.value) || null;
 setSelectedUser(picked);
 }}
 className="w-full text-xs border rounded-lg px-2 py-2 bg-white "
 disabled={usersLoading}
 >
 <option value="">{usersLoading ? 'Loading users...' : 'Select a user'}</option>
 {existingUsers.map((user) => (
 <option key={user.uid} value={user.uid}>
 {user.uid} - {user.full_name || user.email || 'Unnamed user'}
 </option>
 ))}
 </select>
 <div className="rounded-lg border border-slate-200 p-3 text-[11px]">
 <p className="text-slate-500 uppercase tracking-wider text-[10px]">Selected User</p>
 <p className="font-bold text-slate-900 ">{selectedUser?.uid || 'None'}</p>
 <p className="text-slate-500">{selectedUser?.full_name || selectedUser?.email || ''}</p>
 </div>
 </div>
 )}

 <div className="rounded-lg border border-slate-200 p-3 text-[11px]">
 <p className="uppercase tracking-wider text-slate-500 text-[10px]">Flow</p>
 <p className="mt-1 text-slate-600">
 {customerType === 'new'
 ? 'Sign Up -> Sign In -> Place Order -> Order Completed'
 : 'Sign In -> Place Order -> Order Completed'}
 </p>
 </div>

 <div className="grid grid-cols-2 gap-3 text-[11px]">
 <div className="rounded-lg border border-slate-200 p-3">
 <p className="text-slate-500 uppercase tracking-wider text-[10px]">Generated User ID</p>
 <p className="font-bold text-slate-900 ">{generatedUserId || 'AUTO'}</p>
 </div>
 <div className="rounded-lg border border-slate-200 p-3">
 <p className="text-slate-500 uppercase tracking-wider text-[10px]">Generated Device ID</p>
 <p className="font-bold text-slate-900 ">{normalizeDeviceId(generatedDeviceId) || 'AUTO'}</p>
 </div>
 <div className="rounded-lg border border-slate-200 p-3">
 <p className="text-slate-500 uppercase tracking-wider text-[10px]">Generated IP</p>
 <p className="font-bold text-slate-900 ">{generatedIpAddress || 'AUTO'}</p>
 </div>
 <div className="rounded-lg border border-slate-200 p-3">
 <p className="text-slate-500 uppercase tracking-wider text-[10px]">Generated Address ID</p>
 <p className="font-bold text-slate-900 ">{normalizeAddressId(generatedAddressId) || 'AUTO'}</p>
 </div>
 </div>

 <div>
 <label className="text-[10px] font-bold text-slate-500 uppercase">App Flow</label>
 <div className="grid grid-cols-2 gap-2 mt-2">
 {STAGES.filter((s) => customerType === 'new' || s.id !== 'registration').map((s) => (
 <button
 key={s.id}
 type="button"
 onClick={() => setStage(s.id)}
 className={`text-left text-[11px] p-2 rounded-lg border transition-colors ${
 stage === s.id
 ? 'border-v-blue bg-blue-50 text-v-blue'
 : 'border-slate-200 text-slate-500'
 }`}
 >
 <span className="font-bold block">{s.label}</span>
 <span className="opacity-70">{s.desc}</span>
 </button>
 ))}
 </div>
 </div>

 <form onSubmit={handleSubmit} className="space-y-4">
 {customerType === 'new' && stage === 'registration' && (
 <fieldset className="space-y-3 border border-slate-200 rounded-lg p-3">
 <legend className="text-[10px] font-bold text-slate-500 px-1">Sign Up</legend>
 <input value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Full name" className="w-full text-xs border rounded px-2 py-2 " />
 <input value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} placeholder="Phone number" className="w-full text-xs border rounded px-2 py-2 " />
 <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email address" className="w-full text-xs border rounded px-2 py-2 " />
 <div className="grid grid-cols-3 gap-2">
 <input type="date" value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} className="w-full text-xs border rounded px-2 py-2 " />
 <select value={gender} onChange={(e) => setGender(e.target.value)} className="w-full text-xs border rounded px-2 py-2 ">
 <option>Male</option>
 <option>Female</option>
 <option>Other</option>
 </select>
 <select value={maritalStatus} onChange={(e) => setMaritalStatus(e.target.value)} className="w-full text-xs border rounded px-2 py-2 ">
 <option>Single</option>
 <option>Married</option>
 </select>
 </div>
<input value={referralCode} onChange={(e) => setReferralCode(e.target.value)} placeholder="Referral code (optional)" className="w-full text-xs border rounded px-2 py-2 " />
<div className="grid grid-cols-2 gap-2 text-xs">
 <label className="flex items-center gap-2 rounded border border-slate-200 px-2 py-2">
 <input
 type="checkbox"
 checked={isEmailVerified}
 onChange={(e) => setIsEmailVerified(e.target.checked)}
 />
 <span>Email verified</span>
 </label>
 <label className="flex items-center gap-2 rounded border border-slate-200 px-2 py-2">
 <input
 type="checkbox"
 checked={isPhoneVerified}
 onChange={(e) => setIsPhoneVerified(e.target.checked)}
 />
 <span>Phone verified</span>
 </label>
</div>
<div className="relative">
<input
type={showPassword ? 'text' : 'password'}
value={password}
 onChange={(e) => setPassword(e.target.value)}
 placeholder="Password"
 className="w-full text-xs border rounded px-2 py-2 pr-16 "
 />
 <button
 type="button"
 onClick={() => setShowPassword((prev) => !prev)}
 className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-bold text-blue-400"
 >
 {showPassword ? 'Hide' : 'Show'}
 </button>
 </div>
 <div className="rounded border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-500">
 Password, date of birth, gender, and marital status are kept as app inputs only; they are not sent as model features.
 </div>
 </fieldset>
 )}

 {stage === 'login' && (
 <fieldset className="space-y-3 border border-slate-200 rounded-lg p-3">
 <legend className="text-[10px] font-bold text-slate-500 px-1">Sign In</legend>
 <input
 value={loginPhoneNumber}
 onChange={(e) => setLoginPhoneNumber(e.target.value)}
 readOnly={customerType === 'existing'}
 placeholder="Phone number"
 className="w-full text-xs border rounded px-2 py-2 read-only:bg-slate-100 read-only:text-slate-500"
 />
 <div className="relative">
 <input
 type={showPassword ? 'text' : 'password'}
 value={password}
 onChange={(e) => setPassword(e.target.value)}
 placeholder="Password"
 className="w-full text-xs border rounded px-2 py-2 pr-16 "
 />
 <button
 type="button"
 onClick={() => setShowPassword((prev) => !prev)}
 className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] font-bold text-blue-400"
 >
 {showPassword ? 'Hide' : 'Show'}
 </button>
 </div>
 <div className="rounded border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-500">
 Device fingerprint, IP, login timestamp, location, and session duration are generated automatically.
 </div>
 </fieldset>
 )}

 {stage === 'checkout' && (
 <fieldset className="space-y-3 border border-slate-200 rounded-lg p-3">
 <legend className="text-[10px] font-bold text-slate-500 px-1">Place Order</legend>
 <input value={shippingAddress} onChange={(e) => setShippingAddress(e.target.value)} placeholder="Shipping address" className="w-full text-xs border rounded px-2 py-2 " />
 <div className="grid grid-cols-2 gap-2">
 <input value={receiverName} onChange={(e) => setReceiverName(e.target.value)} placeholder="Receiver name" className="w-full text-xs border rounded px-2 py-2 " />
 <input value={receiverPhone} onChange={(e) => setReceiverPhone(e.target.value)} placeholder="Receiver phone" className="w-full text-xs border rounded px-2 py-2 " />
 </div>
 <select value={shippingMethod} onChange={(e) => setShippingMethod(e.target.value)} className="w-full text-xs border rounded px-2 py-2 ">
 <option>Regular</option>
 <option>Instant</option>
 <option>Same Day</option>
 <option>Pickup</option>
 </select>
 <select
 value={paymentIdentifier}
 onChange={(e) => setPaymentIdentifier(e.target.value)}
 className="w-full text-xs border rounded px-2 py-2 "
 >
 {PAYMENT_METHODS.map((method) => (
 <option key={method} value={method}>
 {method}
 </option>
 ))}
 </select>
 <input value={voucherCode} onChange={(e) => setVoucherCode(e.target.value)} placeholder="Voucher code (optional)" className="w-full text-xs border rounded px-2 py-2 " />
 <label className="flex items-center gap-2 text-xs">
 <input type="checkbox" checked={voucherUsed} onChange={(e) => setVoucherUsed(e.target.checked)} />
 Use promo or voucher
 </label>
 <div className="grid grid-cols-3 gap-2">
 <label className="space-y-1">
 <span className="block text-[10px] font-bold uppercase text-slate-500">Order Amount</span>
 <input type="number" value={orderAmount} onChange={(e) => setOrderAmount(+e.target.value)} className="w-full text-xs border rounded px-2 py-2 " />
 </label>
 <label className="space-y-1">
 <span className="block text-[10px] font-bold uppercase text-slate-500">Shipping Fee</span>
 <input type="number" value={shippingFee} onChange={(e) => setShippingFee(+e.target.value)} className="w-full text-xs border rounded px-2 py-2 " />
 </label>
 <label className="space-y-1">
 <span className="block text-[10px] font-bold uppercase text-slate-500">Final Amount</span>
 <input type="number" value={finalAmount} readOnly className="w-full text-xs border rounded px-2 py-2 bg-slate-100 text-slate-500 " />
 </label>
 </div>
 <div className="rounded border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-500">
 Address ID, payment ID, transaction ID, voucher ID, and payment token are generated automatically.
 </div>
 </fieldset>
 )}

 {stage === 'transaction_completed' && (
 <fieldset className="space-y-3 border border-slate-200 rounded-lg p-3">
 <legend className="text-[10px] font-bold text-slate-500 px-1">Order Completed</legend>
 <button type="submit" disabled={loading} className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold text-sm py-3 rounded-lg">
 {loading ? 'Completing...' : 'Pesanan Selesai'}
 </button>
 <div className="rounded border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-500">
 Order status, delivery status, payment status, and completed timestamp are updated automatically.
 </div>
 </fieldset>
 )}

 <div className="flex gap-2 pt-2">
 {stage !== 'transaction_completed' && (
 <button type="submit" disabled={loading} className="flex-1 bg-v-blue hover:bg-blue-600 disabled:opacity-50 text-white font-bold text-sm py-3 rounded-lg">
 {loading ? 'Analyzing...' : 'Analyze Stage'}
 </button>
 )}
 <button type="button" disabled={loading} onClick={handleJourney} className="flex-1 bg-slate-700 hover:bg-slate-600 text-white font-bold text-sm py-3 rounded-lg">
 Full Journey
 </button>
 </div>
 </form>
 </div>

 <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-md min-h-[460px]">
 {error && <div className="p-3 bg-red-50 border border-red-200 rounded text-red-700 text-xs mb-4">{error}</div>}

 {!loading && resultsToShow.length === 0 && (
 <div className="flex flex-col items-center justify-center h-full text-center p-8 gap-3">
 <span className="text-4xl">📱</span>
 <h4 className="font-bold text-slate-700 ">Ready for Mobile App Simulation</h4>
 <p className="text-xs text-slate-500 max-w-sm">
 Fill in the app flow, then run a single stage or the full journey to see how the score changes as new data arrives.
 </p>
 </div>
 )}

 {loading && (
 <div className="flex flex-col items-center justify-center h-full gap-4">
 <div className="h-10 w-10 border-4 border-slate-200 border-t-v-blue rounded-full animate-spin" />
 <p className="text-xs text-slate-500">Menghitung probabilitas fraud...</p>
 </div>
 )}

 {!loading && resultsToShow.length > 0 && (
 <div className="space-y-3 max-h-[700px] overflow-y-auto">
 <h3 className="font-bold text-slate-900 text-sm">
 {journeyResults ? `Journey (${journeyResults.length} stages)` : 'Inference Result'}
 </h3>
 {resultsToShow.map((r, i) => {
 return renderResultCard(r, i > 0 ? resultsToShow[i - 1] : undefined);
 })}
  </div>
  )}
 </div>
 </div>
 </div>
 );
}

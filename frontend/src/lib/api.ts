/**
 * Purpose: Central typed client for backend Fraud Detection API calls.
 * Used by: Next.js app pages and visualizations.
 * Depends on: axios and NEXT_PUBLIC_API_URL.
 * Public functions: getOverviewStats, listUsers, getUserDetails, getGraphData, predictRaw, chatWithAgent.
 * Side effects: Performs HTTP requests to the backend API.
 */

import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const frontendClient = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface OverviewStats {
  total_users: number;
  total_fake_accounts: number;
  fake_account_rate: number;
  total_transactions: number;
  total_promo_discount: number;
  estimated_promo_abuse_amount: number;
  high_risk_users: number;
}

export interface RiskUser {
  uid: string;
  full_name: string | null;
  email: string | null;
  risk_score_rule_based: number;
  risk_category: string;
  ml_prediction: number | null;
  ml_probability: number | null;
  ftype: string | null;
  city: string | null;
  top_reason: string | null;
}

export interface PaginatedUsers {
  total: number;
  page: number;
  limit: number;
  users: RiskUser[];
}

export interface UserDetails {
  uid: string;
  full_name: string | null;
  email: string | null;
  phone_number: string | null;
  registration_date: string | null;
  registration_channel: string | null;
  city: string | null;
  province: string | null;
  account_status: string | null;
  features: Record<string, number>;
  risk_score_rule_based: number;
  risk_category: string;
  fraud: boolean | null;
  ftype: string | null;
  ml_prediction: number | null;
  ml_probability: number | null;
  connected_devices: string[];
  connected_payments: string[];
  connected_addresses: string[];
  connected_ips: string[];
  reasons: string[];
  model_type: string;
  risk_score_breakdown: { category: string; label: string; points: number; value?: string | number }[];
  combined_risk_category: string;
  score_conflict: boolean;
  critical_trigger: boolean;
  raw_rule_points: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  risk_score?: number;
  risk_category?: string;
  ftype?: string | null;
}

export interface GraphEdge {
  source: string | Record<string, any>;
  target: string | Record<string, any>;
  relationship: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphStats {
  total_users: number;
  high_risk_users: number;
  medium_risk_users: number;
  low_risk_users: number;
  fraud_rings: number;
  largest_ring_size: number;
  avg_ring_size: number;
  shared_device_networks: number;
  shared_ip_networks: number;
  shared_payment_networks: number;
  shared_address_networks: number;
  total_nodes: number;
  total_edges: number;
}

export interface EntityDetailUser {
  uid: string;
  label: string;
  risk_category: string;
  risk_score: number;
  ftype: string | null;
}

export interface EntityDetail {
  entity_id: string;
  entity_type: string;
  label: string;
  total_connections: number;
  connected_users: EntityDetailUser[];
}

export interface PredictionResponse {
  uid: string | null;
  model_prediction: number;
  model_probability: number;
  rule_based_score: number;
  risk_category: string;
  is_suspicious: boolean;
  reasons: string[];
}

export type LifecycleStage = 'registration' | 'login' | 'checkout' | 'transaction_completed';
export type CustomerType = 'new' | 'existing';

export interface AlfagiftLifecyclePayload {
  phone_number?: string;
  email?: string;
  full_name?: string;
  date_of_birth?: string;
  registration_hour?: number;
  is_email_verified?: boolean;
  is_phone_verified?: boolean;
  device_id?: string;
  device_fingerprint?: string;
  referral_code?: string;
  ip_address?: string;
  login_count_1h?: number;
  login_count_24h?: number;
  accounts_on_same_ip?: number;
  address_id?: string;
  payment_id?: string;
  payment_identifier?: string;
  order_amount?: number;
  voucher_used?: boolean;
  new_user_voucher?: number;
  minutes_since_registration?: number;
  promo_discount?: number;
  promo_ratio?: number;
}

export interface SuspectedFraudType {
  type: string;
  label: string;
  score: number;
}

export interface LifecycleInferenceResponse {
  uid: string;
  stage: LifecycleStage;
  stage_label: string;
  customer_type: CustomerType;
  model_prediction: number;
  model_probability: number;
  rule_based_score: number;
  risk_category: string;
  is_suspicious: boolean;
  is_fraud: boolean;
  primary_fraud_type: string;
  primary_fraud_label: string;
  suspected_fraud_types: SuspectedFraudType[];
  reasons: string[];
  features_available: number;
  features_total: number;
  confidence_note: string;
  ground_truth_fraud?: boolean | null;
  ground_truth_ftype?: string | null;
}

export interface LifecycleJourneyResponse {
  results: LifecycleInferenceResponse[];
}

export interface ChatResponse {
  reply: string;
  data?: Record<string, any> | null;
}

export const getOverviewStats = async (): Promise<OverviewStats> => {
  const response = await client.get<OverviewStats>('/api/stats/overview');
  return response.data;
};

export const listUsers = async (params: {
  page?: number;
  limit?: number;
  search?: string;
  risk_category?: string;
  fraud_type?: string;
  city?: string;
  device_abuse?: boolean;
  payment_abuse?: boolean;
  address_abuse?: boolean;
}): Promise<PaginatedUsers> => {
  const response = await client.get<PaginatedUsers>('/api/users', { params });
  return response.data;
};

export const getUserDetails = async (userId: string): Promise<UserDetails> => {
  const response = await client.get<UserDetails>(`/api/user/${userId}`);
  return response.data;
};

export const getGraphData = async (params: {
  user_id?: string;
  risk_category?: string;
  max_nodes?: number;
  hop_depth?: number;
}): Promise<GraphData> => {
  const response = await client.get<GraphData>('/api/graph', { params });
  return response.data;
};

export const getGraphStats = async (): Promise<GraphStats> => {
  const response = await client.get<GraphStats>('/api/graph/stats');
  return response.data;
};

export const getEntityDetail = async (entityId: string): Promise<EntityDetail> => {
  const response = await client.get<EntityDetail>(`/api/graph/entity/${entityId}`);
  return response.data;
};

export const predictRaw = async (features: Record<string, any>): Promise<PredictionResponse> => {
  const response = await client.post<PredictionResponse>('/api/predict', { features });
  return response.data;
};

export const predictLifecycle = async (params: {
  stage: LifecycleStage;
  customer_type: CustomerType;
  uid?: string;
  payload: AlfagiftLifecyclePayload;
}): Promise<LifecycleInferenceResponse> => {
  const response = await frontendClient.post<LifecycleInferenceResponse>('/api/inference/lifecycle', params);
  return response.data;
};

export const predictJourney = async (params: {
  customer_type: CustomerType;
  uid?: string;
  payload: AlfagiftLifecyclePayload;
  up_to_stage?: LifecycleStage;
}): Promise<LifecycleJourneyResponse> => {
  const response = await frontendClient.post<LifecycleJourneyResponse>('/api/inference/journey', params);
  return response.data;
};

export const predictRegistrationStage = async (params: {
  customer_type: CustomerType;
  uid?: string;
  payload: AlfagiftLifecyclePayload;
}): Promise<LifecycleInferenceResponse> => {
  const response = await frontendClient.post<LifecycleInferenceResponse>('/api/inference/registration', params);
  return response.data;
};

export const predictLoginStage = async (params: {
  customer_type: CustomerType;
  uid?: string;
  payload: AlfagiftLifecyclePayload;
}): Promise<LifecycleInferenceResponse> => {
  const response = await frontendClient.post<LifecycleInferenceResponse>('/api/inference/login', params);
  return response.data;
};

export const predictCheckoutStage = async (params: {
  customer_type: CustomerType;
  uid?: string;
  payload: AlfagiftLifecyclePayload;
}): Promise<LifecycleInferenceResponse> => {
  const response = await frontendClient.post<LifecycleInferenceResponse>('/api/inference/checkout', params);
  return response.data;
};

export const predictTransactionCompletedStage = async (params: {
  customer_type: CustomerType;
  uid?: string;
  payload: AlfagiftLifecyclePayload;
}): Promise<LifecycleInferenceResponse> => {
  const response = await frontendClient.post<LifecycleInferenceResponse>('/api/inference/transaction-completed', params);
  return response.data;
};

export const chatWithAgent = async (message: string): Promise<ChatResponse> => {
  const response = await client.post<ChatResponse>('/api/chat', { message });
  return response.data;
};

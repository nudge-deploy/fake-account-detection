import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
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
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  risk_score?: number;
  risk_category?: string;
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

export interface PredictionResponse {
  uid: string | null;
  model_prediction: number;
  model_probability: number;
  rule_based_score: number;
  risk_category: string;
  is_suspicious: boolean;
  reasons: string[];
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
}): Promise<GraphData> => {
  const response = await client.get<GraphData>('/api/graph', { params });
  return response.data;
};

export const predictRaw = async (features: Record<string, any>): Promise<PredictionResponse> => {
  const response = await client.post<PredictionResponse>('/api/predict', { features });
  return response.data;
};

export const chatWithAgent = async (message: string): Promise<ChatResponse> => {
  const response = await client.post<ChatResponse>('/api/chat', { message });
  return response.data;
};

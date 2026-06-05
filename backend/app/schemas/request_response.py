from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- Prediction Schema ---
class PredictionRequest(BaseModel):
    uid: Optional[str] = Field(None, description="User ID to look up in ABT and predict.")
    features: Optional[Dict[str, Any]] = Field(None, description="Optional raw features if user is not in ABT.")

class PredictionResponse(BaseModel):
    uid: Optional[str] = None
    model_prediction: int = Field(..., description="0 for Normal, 1 for Fake Account")
    model_probability: float = Field(..., description="ML model probability of being fake")
    rule_based_score: float = Field(..., description="Rule-based risk score (0-100)")
    risk_category: str = Field(..., description="Risk category: Low, Medium, High")
    is_suspicious: bool = Field(..., description="Whether account is suspicious (ML prob > 0.5 or rule-based >= 50)")
    reasons: List[str] = Field(default_factory=list, description="Key indicators that made this account suspicious")

# --- User Detail Schema ---
class UserDetailResponse(BaseModel):
    uid: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    registration_date: Optional[str] = None
    registration_channel: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    account_status: Optional[str] = None
    features: Dict[str, Any] = Field(..., description="All engineered features from the ABT")
    risk_score_rule_based: float
    risk_category: str
    fraud: Optional[bool] = None
    ftype: Optional[str] = None
    ml_prediction: Optional[int] = None
    ml_probability: Optional[float] = None
    connected_devices: Optional[List[str]] = Field(default_factory=list, description="List of device IDs connected to this user in the graph")
    connected_payments: Optional[List[str]] = Field(default_factory=list, description="List of payment IDs connected to this user in the graph")
    connected_addresses: Optional[List[str]] = Field(default_factory=list, description="List of address IDs connected to this user in the graph")
    connected_ips: Optional[List[str]] = Field(default_factory=list, description="List of IP addresses connected to this user in the graph")
    reasons: Optional[List[str]] = Field(default_factory=list, description="Key indicators that made this account suspicious")

# --- Overview Stats Schema ---
class OverviewStatsResponse(BaseModel):
    total_users: int
    total_fake_accounts: int
    fake_account_rate: float
    total_transactions: int
    total_promo_discount: float
    estimated_promo_abuse_amount: float
    high_risk_users: int

# --- Paginated Users List Schema ---
class RiskUserListItem(BaseModel):
    uid: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    risk_score_rule_based: float
    risk_category: str
    ml_prediction: Optional[int] = None
    ml_probability: Optional[float] = None
    ftype: Optional[str] = None
    city: Optional[str] = None
    top_reason: Optional[str] = None

class PaginatedUsersResponse(BaseModel):
    total: int
    page: int
    limit: int
    users: List[RiskUserListItem]

# --- Top Risk Users Schema ---
class TopRiskUser(BaseModel):
    uid: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    risk_score_rule_based: float
    risk_category: str
    ml_probability: Optional[float] = None
    ftype: Optional[str] = None

class TopRiskUsersResponse(BaseModel):
    total_suspicious: int
    users: List[TopRiskUser]

# --- Graph Schema ---
class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # user, device, address, payment, ip, voucher
    risk_score: Optional[int] = None
    risk_category: Optional[str] = None
    ftype: Optional[str] = None

class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str

class GraphDataResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

# --- Chatbot Schema ---
class ChatRequest(BaseModel):
    message: str = Field(..., example="Why is user USR00010 suspicious?")

class ChatResponse(BaseModel):
    reply: str
    data: Optional[Dict[str, Any]] = None

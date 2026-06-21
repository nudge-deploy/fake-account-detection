"""Purpose: Define request/response contracts for the FastAPI backend.
Used by: API routers, service return values, OpenAPI schema generation.
Depends on: pydantic BaseModel/Field.
Public functions: PredictionRequest/Response, UserDetailResponse, GraphDataResponse, ChatResponse.
Side effects: None.
"""

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

# --- Alfagift Lifecycle Inference Schema ---
class AlfagiftLifecyclePayload(BaseModel):
    """Input sesuai alur nyata Alfagift per tahap user journey."""
    phone_number: Optional[str] = Field(None, example="081234567890")
    email: Optional[str] = Field(None, example="user@gmail.com")
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = Field(None, example="2001-05-10")
    registration_hour: Optional[int] = Field(None, ge=0, le=23)
    is_email_verified: Optional[bool] = None
    is_phone_verified: Optional[bool] = None
    device_id: Optional[str] = Field(None, example="DEV00001")
    device_fingerprint: Optional[str] = Field(None, example="FP_Vivo_Y27_9d94bdeaa1e75c56")
    referral_code: Optional[str] = None
    ip_address: Optional[str] = Field(None, example="103.10.20.5")
    login_count_1h: Optional[int] = Field(None, ge=0, description="Jumlah login dalam 1 jam terakhir")
    login_count_24h: Optional[int] = Field(None, ge=0)
    accounts_on_same_ip: Optional[int] = Field(None, ge=1)
    address_id: Optional[str] = Field(None, example="ADDR00001")
    payment_id: Optional[str] = None
    payment_identifier: Optional[str] = Field(None, description="Hash/nomor e-wallet/kartu")
    order_amount: Optional[float] = Field(None, ge=0)
    voucher_used: Optional[bool] = None
    new_user_voucher: Optional[int] = Field(None, ge=0)
    minutes_since_registration: Optional[int] = Field(None, ge=0)
    promo_discount: Optional[float] = Field(None, ge=0)
    promo_ratio: Optional[float] = Field(None, ge=0, le=1)

class LifecycleInferenceRequest(BaseModel):
    stage: str = Field(..., description="registration | login | checkout | transaction_completed")
    customer_type: str = Field("new", description="new | existing")
    uid: Optional[str] = Field(None, description="User ID untuk customer lama atau demo dataset")
    payload: AlfagiftLifecyclePayload = Field(default_factory=AlfagiftLifecyclePayload)

class SuspectedFraudType(BaseModel):
    type: str
    label: str
    score: float

class LifecycleInferenceResponse(BaseModel):
    uid: str
    stage: str
    stage_label: str
    customer_type: str
    model_prediction: int
    model_probability: float
    rule_based_score: float
    risk_category: str
    is_suspicious: bool
    is_fraud: bool
    primary_fraud_type: str
    primary_fraud_label: str
    suspected_fraud_types: List[SuspectedFraudType] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    features_available: int
    features_total: int
    confidence_note: str
    ground_truth_fraud: Optional[bool] = None
    ground_truth_ftype: Optional[str] = None

class LifecycleJourneyRequest(BaseModel):
    customer_type: str = Field("new", description="new | existing")
    uid: Optional[str] = None
    payload: AlfagiftLifecyclePayload = Field(default_factory=AlfagiftLifecyclePayload)
    up_to_stage: Optional[str] = None

class LifecycleJourneyResponse(BaseModel):
    results: List[LifecycleInferenceResponse]

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
    model_type: str = Field("existing", description="Which model scored this user: 'existing' or 'new'")
    risk_score_breakdown: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Per-rule contribution to risk score")
    combined_risk_category: str = Field("Low", description="Final verdict combining ML + rule-based")
    score_conflict: bool = Field(False, description="True when ML and rule-based strongly disagree")
    critical_trigger: bool = Field(False, description="True when at least one critical rule is triggered")
    raw_rule_points: float = Field(0.0, description="Sum of all rule points before cap at 100")

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

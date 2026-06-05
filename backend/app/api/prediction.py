from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional
import pandas as pd
from app.schemas.request_response import (
    PredictionRequest, 
    PredictionResponse, 
    UserDetailResponse, 
    TopRiskUsersResponse,
    OverviewStatsResponse,
    PaginatedUsersResponse
)

router = APIRouter()

@router.get("/stats/overview", response_model=OverviewStatsResponse)
async def get_overview_stats(request: Request):
    model_service = request.app.state.model_service
    stats = model_service.get_overview_stats()
    return stats

@router.get("/users", response_model=PaginatedUsersResponse)
async def list_users(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by User ID, Name, or Email"),
    risk_category: Optional[str] = Query(None, description="Filter by risk category: Low, Medium, High"),
    fraud_type: Optional[str] = Query(None, description="Filter by fraud type"),
    city: Optional[str] = Query(None, description="Filter by city"),
    device_abuse: Optional[bool] = Query(None, description="Filter users with potential device abuse"),
    payment_abuse: Optional[bool] = Query(None, description="Filter users with potential payment abuse"),
    address_abuse: Optional[bool] = Query(None, description="Filter users with potential address abuse")
):
    model_service = request.app.state.model_service
    if model_service.df_merged is None:
        return PaginatedUsersResponse(total=0, page=page, limit=limit, users=[])
        
    df = model_service.df_merged.copy()
    
    # 1. Apply search filter
    if search:
        s = search.strip().lower()
        mask = (
            df['uid'].str.lower().str.contains(s, na=False) |
            df['full_name'].str.lower().str.contains(s, na=False) |
            df['email'].str.lower().str.contains(s, na=False)
        )
        df = df[mask]
        
    # 2. Apply risk_category filter
    if risk_category:
        df = df[df['risk_cat'].str.lower() == risk_category.strip().lower()]
        
    # 3. Apply fraud_type filter
    if fraud_type:
        if fraud_type.lower() == 'normal':
            df = df[df['fraud'] == 0]
        else:
            df = df[df['ftype'].str.lower() == fraud_type.strip().lower()]
            
    # 4. Apply city filter
    if city:
        df = df[df['city'].str.lower() == city.strip().lower()]
        
    # 5. Apply device_abuse filter
    if device_abuse is not None:
        if device_abuse:
            df = df[df['max_acc_dev'] > 2]
        else:
            df = df[df['max_acc_dev'] <= 2]
            
    # 6. Apply payment_abuse filter
    if payment_abuse is not None:
        if payment_abuse:
            df = df[df['max_acc_pay'] > 2]
        else:
            df = df[df['max_acc_pay'] <= 2]
            
    # 7. Apply address_abuse filter
    if address_abuse is not None:
        if address_abuse:
            df = df[df['max_acc_addr'] > 2]
        else:
            df = df[df['max_acc_addr'] <= 2]

    total = len(df)
    
    # Sort
    if 'ml_probability' in df.columns:
        df = df.sort_values(by=['ml_probability', 'risk_score'], ascending=[False, False])
    else:
        df = df.sort_values(by='risk_score', ascending=False)
        
    # Pagination
    start = (page - 1) * limit
    end = start + limit
    df_slice = df.iloc[start:end]
    
    users_list = []
    for _, row in df_slice.iterrows():
        reasons = model_service.generate_reasons(row)
        top_reason_val = reasons[0] if len(reasons) > 0 else None
        
        users_list.append({
            "uid": row['uid'],
            "full_name": row.get('full_name') if not pd.isna(row.get('full_name')) else None,
            "email": row.get('email') if not pd.isna(row.get('email')) else None,
            "risk_score_rule_based": float(row.get('risk_score', 0)),
            "risk_category": row.get('risk_cat', 'Low'),
            "ml_prediction": int(row.get('ml_prediction')) if not pd.isna(row.get('ml_prediction')) else None,
            "ml_probability": float(row.get('ml_probability')) if not pd.isna(row.get('ml_probability')) else None,
            "ftype": row.get('ftype') if not pd.isna(row.get('ftype')) else None,
            "city": row.get('city') if not pd.isna(row.get('city')) else None,
            "top_reason": top_reason_val
        })
        
    return PaginatedUsersResponse(
        total=total,
        page=page,
        limit=limit,
        users=users_list
    )

@router.post("/predict", response_model=PredictionResponse)
async def predict_account(request: Request, body: PredictionRequest):
    model_service = request.app.state.model_service
    
    if body.uid:
        result = model_service.predict_user(body.uid)
        if not result:
            raise HTTPException(status_code=404, detail=f"User ID {body.uid} not found in ABT")
        return result
    elif body.features:
        return model_service.predict_raw_features(body.features)
    else:
        raise HTTPException(status_code=400, detail="Must provide either uid or features dict")

@router.get("/user/{uid}", response_model=UserDetailResponse)
async def get_user_details(request: Request, uid: str):
    model_service = request.app.state.model_service
    graph_service = request.app.state.graph_service
    
    result = model_service.get_user_details(uid)
    if not result:
        raise HTTPException(status_code=404, detail=f"User ID {uid} not found")
        
    # Inject active prediction
    prediction = model_service.predict_user(uid)
    if prediction:
        result.ml_prediction = prediction.model_prediction
        result.ml_probability = prediction.model_probability
        
    # Inject graph details
    neighbors = graph_service.adj_list.get(uid, [])
    connected_devices = []
    connected_payments = []
    connected_addresses = []
    connected_ips = []
    for nbr_id in neighbors:
        nbr_node = graph_service.nodes_dict.get(nbr_id)
        if nbr_node:
            node_type = nbr_node.get('type')
            if node_type == 'device':
                connected_devices.append(nbr_id)
            elif node_type == 'payment':
                connected_payments.append(nbr_id)
            elif node_type == 'address':
                connected_addresses.append(nbr_id)
            elif node_type == 'ip':
                connected_ips.append(nbr_id)
                
    result.connected_devices = connected_devices
    result.connected_payments = connected_payments
    result.connected_addresses = connected_addresses
    result.connected_ips = connected_ips
    
    return result

@router.get("/risk/top-users", response_model=TopRiskUsersResponse)
async def get_top_risk_users(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    risk_category: Optional[str] = Query(None, description="Filter by risk category: Low, Medium, High")
):
    model_service = request.app.state.model_service
    return model_service.get_top_risk_users(limit=limit, risk_category=risk_category)

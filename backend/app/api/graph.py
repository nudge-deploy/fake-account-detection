from fastapi import APIRouter, Request, Query
from typing import Optional
from app.schemas.request_response import GraphDataResponse

router = APIRouter()

@router.get("/graph", response_model=GraphDataResponse)
async def get_graph_data(
    request: Request,
    user_id: Optional[str] = Query(None, description="Center graph on this User ID (Ego Network)"),
    risk_category: Optional[str] = Query(None, description="Filter users by risk category: Low, Medium, High"),
    max_nodes: int = Query(1000, description="Max nodes to return to prevent frontend lag", ge=10, le=3000)
):
    graph_service = request.app.state.graph_service
    return graph_service.get_graph_data(
        user_id=user_id,
        risk_category=risk_category,
        max_nodes=max_nodes
    )

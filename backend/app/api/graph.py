from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
from app.schemas.request_response import GraphDataResponse

router = APIRouter()


@router.get("/graph", response_model=GraphDataResponse)
async def get_graph_data(
    request: Request,
    user_id: Optional[str] = Query(None),
    risk_category: Optional[str] = Query(None),
    max_nodes: int = Query(1000, ge=10, le=3000),
    hop_depth: int = Query(2, ge=1, le=3, description="Ego network depth: 1, 2, or 3 hops"),
):
    graph_service = request.app.state.graph_service
    return graph_service.get_graph_data(
        user_id=user_id,
        risk_category=risk_category,
        max_nodes=max_nodes,
        hop_depth=hop_depth,
    )


@router.get("/graph/stats")
async def get_graph_stats(request: Request):
    graph_service = request.app.state.graph_service
    return graph_service.get_stats()


@router.get("/graph/entity/{entity_id}")
async def get_entity_detail(request: Request, entity_id: str):
    graph_service = request.app.state.graph_service
    result = graph_service.get_entity_detail(entity_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found in graph")
    return result

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.models.schemas import RouteResponse, RiskWeights
from app.api.simulation import simulation_engine

router = APIRouter(prefix="/route", tags=["Routing"])


@router.get("", response_model=RouteResponse)
def get_active_route():
    if not simulation_engine or not simulation_engine.active_route:
        raise HTTPException(status_code=404, detail="No active route available")
    return simulation_engine.active_route


@router.post("/recalculate", response_model=RouteResponse)
def recalculate_route(weights: Optional[RiskWeights] = None):
    if not simulation_engine:
        raise HTTPException(status_code=500, detail="Engine uninitialized")
    if weights:
        simulation_engine.risk_weights = weights
    simulation_engine.recalculate_system()
    return simulation_engine.active_route

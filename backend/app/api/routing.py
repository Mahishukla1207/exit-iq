from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.models.schemas import RouteResponse, RiskWeights
from app.api import simulation as simulation_api

router = APIRouter(prefix="/route", tags=["Routing"])


from app.routing.capacity_routing import CapacityAwareFlowRouter

@router.get("", response_model=RouteResponse)
def get_active_route():
    if not simulation_api.simulation_engine or not simulation_api.simulation_engine.active_route:
        raise HTTPException(status_code=404, detail="No active route available")
    return simulation_api.simulation_engine.active_route


@router.get("/capacity-flow")
def get_capacity_flow():
    if not simulation_api.simulation_engine:
        raise HTTPException(status_code=500, detail="Engine uninitialized")
    state = simulation_api.simulation_engine.get_state()
    flow_router = CapacityAwareFlowRouter(simulation_api.simulation_engine.routing_engine)
    total_people = sum(c.count for c in state.crowd_zones.values())
    return flow_router.calculate_multi_exit_flow(
        simulation_api.simulation_engine.start_node_id,
        total_people,
        state.nodes,
        state.edges,
        state.hazards,
        state.crowd_zones,
        state.predictions,
    )


@router.post("/recalculate", response_model=RouteResponse)
def recalculate_route(weights: Optional[RiskWeights] = None):
    if not simulation_api.simulation_engine:
        raise HTTPException(status_code=500, detail="Engine uninitialized")
    if weights:
        simulation_api.simulation_engine.risk_weights = weights
    simulation_api.simulation_engine.recalculate_system()
    return simulation_api.simulation_engine.active_route

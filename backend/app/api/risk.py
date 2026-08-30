from fastapi import APIRouter
from app.api import simulation as simulation_api

router = APIRouter(prefix="/risk-map", tags=["Risk Map"])


@router.get("")
def get_risk_map():
    if not simulation_api.simulation_engine:
        return {}
    state = simulation_api.simulation_engine.get_state()
    return {
        "nodes": state.nodes,
        "edges": state.edges,
        "hazards": state.hazards,
        "crowd_zones": state.crowd_zones,
        "predictions": state.predictions,
        "risk_weights": state.risk_weights,
    }

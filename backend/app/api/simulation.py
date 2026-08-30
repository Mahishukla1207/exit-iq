from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.models.schemas import SimulationState, Hazard, ZoneCrowd, RiskWeights

router = APIRouter(prefix="/simulation", tags=["Simulation"])

# Global simulation instance placeholder (injected in main.py)
simulation_engine = None


def set_simulation_engine(engine):
    global simulation_engine
    simulation_engine = engine
    return simulation_engine


@router.get("/state", response_model=SimulationState)
def get_simulation_state():
    if not simulation_engine:
        raise HTTPException(status_code=500, detail="Simulation engine uninitialized")
    return simulation_engine.get_state()


@router.post("/start")
def start_simulation():
    simulation_engine.is_running = True
    return {"status": "started", "is_running": True}


@router.post("/pause")
def pause_simulation():
    simulation_engine.is_running = False
    return {"status": "paused", "is_running": False}


@router.post("/reset")
def reset_simulation():
    simulation_engine.load_scenario("NORMAL")
    return {"status": "reset", "state": simulation_engine.get_state()}


@router.post("/tick")
def tick_simulation():
    simulation_engine.tick()
    return simulation_engine.get_state()


class HazardRequest(BaseModel):
    zone_id: str
    type: str  # fire, smoke, obstacle
    severity: float
    description: Optional[str] = None
    node_id: Optional[str] = None
    edge_id: Optional[str] = None


@router.post("/hazard")
def add_hazard(req: HazardRequest):
    import time
    h_id = f"h_{int(time.time()*1000)}"
    hazard = Hazard(
        id=h_id,
        zone_id=req.zone_id,
        node_id=req.node_id,
        edge_id=req.edge_id,
        type=req.type,
        severity=req.severity,
        description=req.description or f"Active {req.type} in {req.zone_id}",
    )
    simulation_engine.add_hazard(hazard)
    return {"status": "hazard_added", "hazard": hazard, "state": simulation_engine.get_state()}


@router.delete("/hazard/{hazard_id}")
def remove_hazard(hazard_id: str):
    simulation_engine.remove_hazard(hazard_id)
    return {"status": "hazard_removed", "hazard_id": hazard_id}


class CrowdRequest(BaseModel):
    zone_id: str
    density: float
    count: int


@router.post("/crowd")
def update_crowd(req: CrowdRequest):
    simulation_engine.update_crowd_density(req.zone_id, req.density, req.count)
    return {"status": "crowd_updated", "zone_id": req.zone_id, "density": req.density}


class BlockEdgeRequest(BaseModel):
    edge_id: str
    is_blocked: Optional[bool] = None


@router.post("/edge/block")
def toggle_edge_block(req: BlockEdgeRequest):
    simulation_engine.toggle_edge_block(req.edge_id, req.is_blocked)
    return {"status": "edge_updated", "edge_id": req.edge_id}


@router.post("/scenario/{scenario_name}")
def trigger_scenario(scenario_name: str):
    try:
        simulation_engine.load_scenario(scenario_name)
        return {"status": "scenario_loaded", "scenario": scenario_name, "state": simulation_engine.get_state()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

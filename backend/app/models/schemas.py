from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str = Field(..., description="Unique node identifier")
    name: str = Field(..., description="Display name of room/zone")
    type: str = Field(..., description="room, corridor_intersection, exit, stairwell")
    x: float = Field(..., description="X coordinate on floor plan (meters/pixels)")
    y: float = Field(..., description="Y coordinate on floor plan (meters/pixels)")
    zone_id: str = Field(..., description="Associated zone ID")
    capacity: int = Field(default=50, description="Max safe capacity")
    is_exit: bool = Field(default=False, description="Whether node is an emergency exit")


class Edge(BaseModel):
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    distance: float = Field(..., description="Length/distance in meters")
    base_risk: float = Field(default=0.0, description="Base environmental risk [0.0-1.0]")
    is_blocked: bool = Field(default=False, description="If path is completely impassable")
    width: float = Field(default=2.5, description="Path width in meters")


class Hazard(BaseModel):
    id: str = Field(..., description="Unique hazard ID")
    zone_id: str = Field(..., description="Zone identifier")
    node_id: Optional[str] = Field(default=None, description="Specific node affected")
    edge_id: Optional[str] = Field(default=None, description="Specific edge affected")
    type: str = Field(..., description="fire, smoke, obstacle, structural_damage")
    severity: float = Field(..., ge=0.0, le=1.0, description="Hazard severity level [0.0-1.0]")
    description: Optional[str] = Field(default=None)


class ZoneCrowd(BaseModel):
    zone_id: str = Field(..., description="Zone ID")
    count: int = Field(default=0, description="Current person count in zone")
    density: float = Field(default=0.0, description="Density Index [0.0 - 4.5], image/graph normalized (not people/m²)")
    avg_speed: float = Field(default=1.2, description="Average movement speed (m/s)")
    inflow_rate: float = Field(default=0.0, description="People entering per sec")
    outflow_rate: float = Field(default=0.0, description="People exiting per sec")


class CongestionPrediction(BaseModel):
    zone_id: str
    current_density: float = Field(..., description="Current Density Index for the zone")
    predicted_density_1m: float = Field(..., description="Predicted Density Index at T+1m")
    predicted_density_3m: float = Field(..., description="Predicted Density Index at T+3m")
    predicted_congestion_prob: float
    trend: str = Field(default="STABLE", description="RISING, FALLING, STABLE")


class RiskWeights(BaseModel):
    distance_weight: float = Field(default=1.0, description="Weight for physical distance")
    crowd_weight: float = Field(default=2.5, description="Weight for active crowd density")
    hazard_weight: float = Field(default=5.0, description="Weight for fire/smoke hazards")
    prediction_weight: float = Field(default=3.0, description="Weight for LightGBM predicted congestion")


class RouteStep(BaseModel):
    node_id: str
    node_name: str
    accumulated_distance: float
    accumulated_risk: float
    step_hazard_risk: float
    step_crowd_risk: float
    step_pred_risk: float


class RouteResponse(BaseModel):
    route_id: str
    start_node: str
    target_exit: str
    target_exit_name: str
    path_nodes: List[str]
    path_edges: List[str]
    steps: List[RouteStep]
    total_distance: float
    total_risk_score: float
    est_evacuation_time_sec: float
    is_safe: bool = True
    explanation_summary: str
    explanation_details: List[str]
    alternate_route: Optional[Dict[str, Any]] = None
    timestamp: float


class SystemMetrics(BaseModel):
    people_detected: int = Field(
        default=0,
        description="Primary people count: all simulated zones in simulation mode; CCTV-mapped zones only in live CV mode",
    )
    current_people_detected: int = Field(
        default=0,
        description="People currently observed inside CCTV ROI polygons (live CV mode only)",
    )
    active_tracking_ids: int = Field(
        default=0,
        description="Count of active centroid track IDs in the latest CV frame",
    )
    detections_in_current_frame: int = Field(
        default=0,
        description="Raw YOLO person detections in the latest CV frame (before deduplication by tracking)",
    )
    active_hazards: int = 0
    highest_risk_zone: str = "N/A"
    highest_risk_score: float = 0.0
    predicted_peak_congestion: float = Field(
        default=0.0,
        description="Peak predicted Density Index across all zones",
    )
    route_cost: float = 0.0
    est_evac_time_sec: float = 0.0
    system_latency_ms: float = 12.4
    cv_fps: float = 30.0


class SimulationState(BaseModel):
    mode: str = Field(default="simulation", description="simulation or cctv")
    is_running: bool = False
    tick: int = 0
    active_scenario: Optional[str] = "NORMAL"
    nodes: List[Node]
    edges: List[Edge]
    hazards: List[Hazard]
    crowd_zones: Dict[str, ZoneCrowd]
    predictions: Dict[str, CongestionPrediction]
    risk_weights: RiskWeights
    active_route: Optional[RouteResponse] = None
    metrics: SystemMetrics

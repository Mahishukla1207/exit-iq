import time
from typing import Dict, List, Optional
from app.models.schemas import (
    Node,
    Edge,
    Hazard,
    ZoneCrowd,
    CongestionPrediction,
    RiskWeights,
    SimulationState,
    SystemMetrics,
    RouteResponse,
)
from app.risk.risk_engine import RiskEngine
from app.routing.risk_aware_astar import RiskAwareAStar
from app.prediction.lightgbm_model import LightGBMPredictor


class SimulationEngine:
    """
    Core Simulation Engine for ExitIQ.
    Manages building floor plan graph state, crowd dynamics, hazard events, LightGBM predictions,
    and dynamic route recalculation.
    """

    def __init__(self):
        self.mode = "simulation"
        self.is_running = False
        self.tick_count = 0
        self.active_scenario = "NORMAL"
        self.start_node_id = "node_start"

        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}
        self.hazards: Dict[str, Hazard] = {}
        self.crowd_zones: Dict[str, ZoneCrowd] = {}
        self.predictions: Dict[str, CongestionPrediction] = {}
        self.risk_weights = RiskWeights()

        self.risk_engine = RiskEngine(self.risk_weights)
        self.routing_engine = RiskAwareAStar(self.risk_engine)
        self.prediction_engine = LightGBMPredictor()

        self._load_default_building_map()
        self.recalculate_system()

    def _load_default_building_map(self):
        """Builds default 12-zone building floor map with 4 emergency exits."""
        nodes_list = [
            Node(id="node_start", name="Main Assembly Hall", type="room", x=100.0, y=250.0, zone_id="zone_hall"),
            Node(id="node_west_corridor", name="West Corridor", type="corridor_intersection", x=250.0, y=250.0, zone_id="zone_west"),
            Node(id="node_east_corridor", name="East Corridor", type="corridor_intersection", x=500.0, y=250.0, zone_id="zone_east"),
            Node(id="node_north_hall", name="North Wing Hallway", type="corridor_intersection", x=375.0, y=100.0, zone_id="zone_north"),
            Node(id="node_south_hall", name="South Wing Hallway", type="corridor_intersection", x=375.0, y=400.0, zone_id="zone_south"),
            Node(id="node_west_gate", name="West Wing Atrium", type="room", x=180.0, y=120.0, zone_id="zone_atrium"),
            Node(id="node_east_gate", name="East Wing Atrium", type="room", x=580.0, y=380.0, zone_id="zone_atrium_east"),
            # Exits
            Node(id="exit_a", name="Exit A (West Gate)", type="exit", x=50.0, y=80.0, zone_id="zone_exit_a", is_exit=True),
            Node(id="exit_b", name="Exit B (North Gate)", type="exit", x=500.0, y=40.0, zone_id="zone_exit_b", is_exit=True),
            Node(id="exit_c", name="Exit C (East Gate)", type="exit", x=700.0, y=250.0, zone_id="zone_exit_c", is_exit=True),
            Node(id="exit_d", name="Exit D (South Stairwell)", type="exit", x=500.0, y=460.0, zone_id="zone_exit_d", is_exit=True),
        ]
        self.nodes = {n.id: n for n in nodes_list}

        edges_list = [
            Edge(id="e_start_west", source="node_start", target="node_west_corridor", distance=15.0),
            Edge(id="e_west_east", source="node_west_corridor", target="node_east_corridor", distance=25.0),
            Edge(id="e_west_north", source="node_west_corridor", target="node_north_hall", distance=18.0),
            Edge(id="e_west_south", source="node_west_corridor", target="node_south_hall", distance=18.0),
            Edge(id="e_east_north", source="node_east_corridor", target="node_north_hall", distance=18.0),
            Edge(id="e_east_south", source="node_east_corridor", target="node_south_hall", distance=18.0),
            Edge(id="e_west_atrium", source="node_west_corridor", target="node_west_gate", distance=12.0),
            Edge(id="e_atrium_exit_a", source="node_west_gate", target="exit_a", distance=10.0),
            Edge(id="e_north_exit_b", source="node_north_hall", target="exit_b", distance=12.0),
            Edge(id="e_east_exit_c", source="node_east_corridor", target="exit_c", distance=20.0),
            Edge(id="e_south_atrium", source="node_south_hall", target="node_east_gate", distance=12.0),
            Edge(id="e_atrium_exit_d", source="node_east_gate", target="exit_d", distance=10.0),
            Edge(id="e_south_exit_d", source="node_south_hall", target="exit_d", distance=12.0),
        ]
        self.edges = {e.id: e for e in edges_list}

        # Initialize zone crowd objects
        zone_ids = set(n.zone_id for n in nodes_list)
        for zid in zone_ids:
            self.crowd_zones[zid] = ZoneCrowd(zone_id=zid, count=5, density=0.4, avg_speed=1.2, inflow_rate=0.0, outflow_rate=0.0)

    def recalculate_system(self):
        """Updates LightGBM predictions, dynamic risk metrics, and recalculates evacuation route."""
        # 1. Update LightGBM predictions per zone
        for zid, crowd in self.crowd_zones.items():
            haz_sev = max([h.severity for h in self.hazards.values() if h.zone_id == zid], default=0.0)
            self.predictions[zid] = self.prediction_engine.predict_zone_congestion(
                zone_id=zid,
                crowd=crowd,
                nearby_density=0.5,
                exit_proximity=20.0,
                hazard_severity=haz_sev,
            )

        # 2. Recalculate A* route
        self.risk_engine.update_weights(self.risk_weights)
        self.active_route = self.routing_engine.find_safest_route(
            start_node_id=self.start_node_id,
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values()),
            hazards=list(self.hazards.values()),
            crowd_zones=self.crowd_zones,
            predictions=self.predictions,
        )

    def load_scenario(self, scenario_name: str):
        """Loads pre-configured demonstration scenario 1-6."""
        self.active_scenario = scenario_name.upper()
        # Reset hazards & crowd
        self.hazards.clear()
        for e in self.edges.values():
            e.is_blocked = False
        for z in self.crowd_zones.values():
            z.density = 0.4
            z.count = 5

        if self.active_scenario == "FIRE_CORRIDOR":
            # Scenario 2: Fire blocks North corridor to Exit B
            self.add_hazard(
                Hazard(id="h1", zone_id="zone_north", node_id="node_north_hall", type="fire", severity=0.95, description="Severe Fire in North Corridor")
            )
        elif self.active_scenario == "EXIT_CONGESTION":
            # Scenario 3: Exit A & West gate high crowd surge
            self.update_crowd_density("zone_atrium", density=3.8, count=85)
            self.update_crowd_density("zone_exit_a", density=4.2, count=90)
        elif self.active_scenario == "PREDICTIVE_CONGESTION":
            # Scenario 4: Exit A has moderate density but high inflow rate triggering LightGBM prediction surge
            self.crowd_zones["zone_atrium"].density = 1.8
            self.crowd_zones["zone_atrium"].inflow_rate = 8.5
        elif self.active_scenario == "MULTI_HAZARD":
            # Scenario 5: Fire in North, Heavy Smoke in West, Panic in East
            self.add_hazard(Hazard(id="h1", zone_id="zone_north", type="fire", severity=0.9, description="Active Fire North"))
            self.add_hazard(Hazard(id="h2", zone_id="zone_atrium", type="smoke", severity=0.7, description="Heavy Smoke West"))
            self.update_crowd_density("zone_east", density=3.5, count=70)
        elif self.active_scenario == "NO_SAFE_ROUTE":
            # Scenario 6: Block all corridors/exits
            for e in self.edges.values():
                e.is_blocked = True

        self.recalculate_system()

    def add_hazard(self, hazard: Hazard):
        self.hazards[hazard.id] = hazard
        self.recalculate_system()

    def remove_hazard(self, hazard_id: str):
        if hazard_id in self.hazards:
            del self.hazards[hazard_id]
            self.recalculate_system()

    def update_crowd_density(self, zone_id: str, density: float, count: int):
        if zone_id in self.crowd_zones:
            self.crowd_zones[zone_id].density = density
            self.crowd_zones[zone_id].count = count
            self.recalculate_system()

    def toggle_edge_block(self, edge_id: str, is_blocked: Optional[bool] = None):
        if edge_id in self.edges:
            if is_blocked is None:
                self.edges[edge_id].is_blocked = not self.edges[edge_id].is_blocked
            else:
                self.edges[edge_id].is_blocked = is_blocked
            self.recalculate_system()

    def tick(self):
        """Advances simulation step, dynamically evolving crowd dynamics."""
        self.tick_count += 1
        # Evolve crowd densities slightly for realism if running
        if self.is_running:
            for zid, c in self.crowd_zones.items():
                c.density = max(0.1, min(4.5, c.density + (c.inflow_rate - c.outflow_rate) * 0.02))
            self.recalculate_system()

    def get_state(self) -> SimulationState:
        total_people = sum(c.count for c in self.crowd_zones.values())
        highest_risk_z = "N/A"
        highest_r_score = 0.0
        for zid, pred in self.predictions.items():
            if pred.predicted_congestion_prob > highest_r_score:
                highest_r_score = pred.predicted_congestion_prob
                highest_risk_z = zid

        peak_pred = max([p.predicted_density_1m for p in self.predictions.values()], default=0.0)

        metrics = SystemMetrics(
            people_detected=total_people,
            active_hazards=len(self.hazards),
            highest_risk_zone=highest_risk_z,
            highest_risk_score=round(highest_r_score, 2),
            predicted_peak_congestion=round(peak_pred, 2),
            route_cost=self.active_route.total_risk_score if self.active_route else 0.0,
            est_evac_time_sec=self.active_route.est_evacuation_time_sec if self.active_route else 0.0,
            system_latency_ms=8.5,
            cv_fps=30.0,
        )

        return SimulationState(
            mode=self.mode,
            is_running=self.is_running,
            tick=self.tick_count,
            active_scenario=self.active_scenario,
            nodes=list(self.nodes.values()),
            edges=list(self.edges.values()),
            hazards=list(self.hazards.values()),
            crowd_zones=self.crowd_zones,
            predictions=self.predictions,
            risk_weights=self.risk_weights,
            active_route=self.active_route,
            metrics=metrics,
        )

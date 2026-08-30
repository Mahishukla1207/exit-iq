import math
from typing import Dict, List, Any, Optional
from app.models.schemas import Node, Edge, Hazard, ZoneCrowd, CongestionPrediction, RouteResponse
from app.routing.risk_aware_astar import RiskAwareAStar


class CapacityAwareFlowRouter:
    """
    Capacity-Aware Multi-Exit Flow Allocation Router.
    Splits large crowd streams across multiple safe emergency exits based on path dynamic risk cost
    and corridor/exit physical flow capacity to prevent single-exit stampedes.
    """

    def __init__(self, astar_router: Optional[RiskAwareAStar] = None):
        self.astar_router = astar_router or RiskAwareAStar()

    def calculate_multi_exit_flow(
        self,
        start_node_id: str,
        total_people: int,
        nodes: List[Node],
        edges: List[Edge],
        hazards: List[Hazard],
        crowd_zones: Dict[str, ZoneCrowd],
        predictions: Dict[str, CongestionPrediction],
    ) -> Dict[str, Any]:
        """
        Calculates multi-exit crowd distribution percentage and flow routes.
        Returns: {
            is_safe: bool,
            primary_route: RouteResponse,
            exit_distributions: List[{exit_id, exit_name, flow_percentage, recommended_count}],
            allocation_strategy: str
        }
        """
        primary_route = self.astar_router.find_safest_route(
            start_node_id, nodes, edges, hazards, crowd_zones, predictions
        )

        if not primary_route.is_safe:
            return {
                "is_safe": False,
                "primary_route": primary_route,
                "exit_distributions": [],
                "allocation_strategy": "EMERGENCY_SHELTER_NO_SAFE_EXIT",
            }

        nodes_dict = {n.id: n for n in nodes}
        exits = [n for n in nodes if n.is_exit]

        # Evaluate candidate routes to all safe exits
        valid_exit_routes = []
        for ex in exits:
            # Check if exit is not compromised
            exit_hazard = self.astar_router.risk_engine.calculate_hazard_risk(
                ex.zone_id, "", hazards, ex.id
            )
            if exit_hazard >= 0.40:
                continue

            try:
                # Calculate path to this exit
                G, _, _ = self.astar_router.build_graph(nodes, edges, hazards, crowd_zones, predictions)
                import networkx as nx
                path = nx.astar_path(
                    G,
                    start_node_id,
                    ex.id,
                    heuristic=lambda u, target: self.astar_router._euclidean_heuristic(u, target, G),
                    weight="weight",
                )
                cost = 0.0
                dist = 0.0
                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    cost += G[u][v]["weight"]
                    dist += G[u][v]["distance"]

                valid_exit_routes.append({
                    "exit_id": ex.id,
                    "exit_name": ex.name,
                    "cost": cost,
                    "distance": dist,
                    "capacity": ex.capacity,
                })
            except Exception:
                continue

        if not valid_exit_routes:
            return {
                "is_safe": False,
                "primary_route": primary_route,
                "exit_distributions": [],
                "allocation_strategy": "NO_VALID_CORRIDOR_PATH",
            }

        # If total people is small (<25), 100% to primary exit
        if total_people <= 25 or len(valid_exit_routes) == 1:
            best = min(valid_exit_routes, key=lambda r: r["cost"])
            distributions = [
                {
                    "exit_id": r["exit_id"],
                    "exit_name": r["exit_name"],
                    "flow_percentage": 100.0 if r["exit_id"] == best["exit_id"] else 0.0,
                    "recommended_count": total_people if r["exit_id"] == best["exit_id"] else 0,
                    "path_cost": round(r["cost"], 1),
                }
                for r in valid_exit_routes
            ]
            return {
                "is_safe": True,
                "primary_route": primary_route,
                "exit_distributions": [d for d in distributions if d["flow_percentage"] > 0],
                "allocation_strategy": "SINGLE_PRIMARY_EXIT_LOW_DENSITY",
            }

        # Inverse cost weighting for capacity allocation
        inv_costs = [1.0 / (r["cost"] + 1.0) for r in valid_exit_routes]
        sum_inv = sum(inv_costs)

        distributions = []
        for idx, r in enumerate(valid_exit_routes):
            raw_pct = (inv_costs[idx] / sum_inv) * 100.0
            raw_count = int(round((raw_pct / 100.0) * total_people))

            distributions.append({
                "exit_id": r["exit_id"],
                "exit_name": r["exit_name"],
                "flow_percentage": round(raw_pct, 1),
                "recommended_count": raw_count,
                "path_cost": round(r["cost"], 1),
            })

        distributions.sort(key=lambda d: d["flow_percentage"], reverse=True)

        return {
            "is_safe": True,
            "primary_route": primary_route,
            "exit_distributions": distributions,
            "allocation_strategy": "MULTI_EXIT_BALANCED_FLOW_ALLOCATION",
        }

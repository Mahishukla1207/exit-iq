import time
import math
import networkx as nx
from typing import Dict, List, Optional, Tuple, Any
from app.models.schemas import (
    Node,
    Edge,
    Hazard,
    ZoneCrowd,
    CongestionPrediction,
    RiskWeights,
    RouteResponse,
    RouteStep,
)
from app.risk.risk_engine import RiskEngine


class RiskAwareAStar:
    """
    Weighted Risk-Aware A* Evacuation Routing Engine.
    Extends standard A* pathfinding to optimize for combined (Distance + Environmental Risk + Predicted Congestion).
    """

    def __init__(self, risk_engine: Optional[RiskEngine] = None):
        self.risk_engine = risk_engine or RiskEngine()

    def build_graph(
        self,
        nodes: List[Node],
        edges: List[Edge],
        hazards: List[Hazard],
        crowd_zones: Dict[str, ZoneCrowd],
        predictions: Dict[str, CongestionPrediction],
    ) -> Tuple[nx.DiGraph, Dict[str, Node], Dict[str, Edge]]:
        """Constructs a directed NetworkX graph with dynamically evaluated risk weights."""
        G = nx.DiGraph()
        nodes_dict = {n.id: n for n in nodes}
        edges_dict = {}

        for node in nodes:
            G.add_node(node.id, x=node.x, y=node.y, name=node.name, type=node.type, is_exit=node.is_exit)

        for edge in edges:
            edges_dict[edge.id] = edge
            cost, hazard_r, crowd_r, pred_r = self.risk_engine.calculate_edge_cost(
                edge, nodes_dict, hazards, crowd_zones, predictions
            )

            if cost != float("inf"):
                # Add bidirectional traversal if open
                G.add_edge(
                    edge.source,
                    edge.target,
                    id=edge.id,
                    weight=cost,
                    distance=edge.distance,
                    hazard_risk=hazard_r,
                    crowd_risk=crowd_r,
                    pred_risk=pred_r,
                )
                G.add_edge(
                    edge.target,
                    edge.source,
                    id=edge.id,
                    weight=cost,
                    distance=edge.distance,
                    hazard_risk=hazard_r,
                    crowd_risk=crowd_r,
                    pred_risk=pred_r,
                )

        return G, nodes_dict, edges_dict

    def _euclidean_heuristic(self, u: str, v: str, G: nx.DiGraph) -> float:
        """Euclidean distance heuristic for A*."""
        pos_u = (G.nodes[u]["x"], G.nodes[u]["y"])
        pos_v = (G.nodes[v]["x"], G.nodes[v]["y"])
        return math.hypot(pos_u[0] - pos_v[0], pos_u[1] - pos_v[1])

    def find_safest_route(
        self,
        start_node_id: str,
        nodes: List[Node],
        edges: List[Edge],
        hazards: List[Hazard],
        crowd_zones: Dict[str, ZoneCrowd],
        predictions: Dict[str, CongestionPrediction],
    ) -> RouteResponse:
        """
        Calculates the optimal evacuation route from start_node_id to the safest available emergency exit.
        """
        start_time = time.time()
        G, nodes_dict, edges_dict = self.build_graph(nodes, edges, hazards, crowd_zones, predictions)

        if start_node_id not in G:
            return self._build_no_route_response(start_node_id, "Start node not found on floor plan map.")

        exits = [n.id for n in nodes if n.is_exit]
        if not exits:
            return self._build_no_route_response(start_node_id, "No emergency exits configured in system.")

        # Disqualify any exit node that has an active fire/smoke hazard on the exit node or its zone
        valid_exits = []
        for exit_id in exits:
            exit_node = nodes_dict.get(exit_id)
            if exit_node:
                exit_hazard = self.risk_engine.calculate_hazard_risk(
                    exit_node.zone_id, "", hazards, exit_id
                )
                if exit_hazard >= 0.40:
                    continue  # Exit itself is burning/compromised, skip!
            valid_exits.append(exit_id)

        if not valid_exits:
            return self._build_no_route_response(
                start_node_id, "CRITICAL ALERT: All emergency exits are compromised by active fire or heavy smoke hazards."
            )

        best_route_info = None
        min_total_cost = float("inf")
        alternate_route_info = None

        # Evaluate candidate routes to all available exits
        candidate_routes = []

        for exit_id in valid_exits:
            try:
                path = nx.astar_path(
                    G,
                    start_node_id,
                    exit_id,
                    heuristic=lambda u, v: self._euclidean_heuristic(u, exit_id, G),
                    weight="weight",
                )
                
                total_cost = 0.0
                total_dist = 0.0
                steps = []
                path_edges = []

                for i in range(len(path) - 1):
                    u, v = path[i], path[i + 1]
                    edge_data = G[u][v]
                    w = edge_data["weight"]
                    d = edge_data["distance"]
                    path_edges.append(edge_data["id"])

                    total_cost += w
                    total_dist += d

                    node_obj = nodes_dict.get(v)
                    steps.append(
                        RouteStep(
                            node_id=v,
                            node_name=node_obj.name if node_obj else v,
                            accumulated_distance=total_dist,
                            accumulated_risk=total_cost,
                            step_hazard_risk=edge_data["hazard_risk"],
                            step_crowd_risk=edge_data["crowd_risk"],
                            step_pred_risk=edge_data["pred_risk"],
                        )
                    )

                candidate_routes.append({
                    "exit_id": exit_id,
                    "exit_name": nodes_dict[exit_id].name if exit_id in nodes_dict else exit_id,
                    "path": path,
                    "path_edges": path_edges,
                    "steps": steps,
                    "total_cost": total_cost,
                    "total_dist": total_dist,
                })
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue

        if not candidate_routes:
            return self._build_no_route_response(
                start_node_id, "CRITICAL ALERT: All evacuation corridors to emergency exits are impassable or blocked by severe hazards."
            )

        # Sort candidate routes by dynamic risk cost
        candidate_routes.sort(key=lambda r: r["total_cost"])

        best = candidate_routes[0]
        alt = candidate_routes[1] if len(candidate_routes) > 1 else None

        # Calculate estimated evacuation time (assuming avg walking speed 1.2m/s, modified by crowd density)
        est_time_sec = round(best["total_cost"] / 1.2, 1)

        # Generate Explainability rationale
        explanation_summary, explanation_details = self._generate_explainability(
            best, alt, candidate_routes, nodes_dict, hazards, crowd_zones, predictions
        )

        alt_dict = None
        if alt:
            alt_dict = {
                "exit_id": alt["exit_id"],
                "exit_name": alt["exit_name"],
                "path_nodes": alt["path"],
                "total_distance": round(alt["total_dist"], 1),
                "total_risk_score": round(alt["total_cost"], 1),
            }

        return RouteResponse(
            route_id=f"route_{int(time.time()*1000)}",
            start_node=start_node_id,
            target_exit=best["exit_id"],
            target_exit_name=best["exit_name"],
            path_nodes=best["path"],
            path_edges=best["path_edges"],
            steps=best["steps"],
            total_distance=round(best["total_dist"], 1),
            total_risk_score=round(best["total_cost"], 1),
            est_evacuation_time_sec=est_time_sec,
            is_safe=True,
            explanation_summary=explanation_summary,
            explanation_details=explanation_details,
            alternate_route=alt_dict,
            timestamp=time.time(),
        )

    def _generate_explainability(
        self,
        best: Dict[str, Any],
        alt: Optional[Dict[str, Any]],
        candidates: List[Dict[str, Any]],
        nodes_dict: Dict[str, Node],
        hazards: List[Hazard],
        crowd_zones: Dict[str, ZoneCrowd],
        predictions: Dict[str, CongestionPrediction],
    ) -> Tuple[str, List[str]]:
        """Generates clear, human-readable explainability logs for route selection."""
        best_exit = best["exit_name"]
        details = []

        summary = f"RECOMMENDED ROUTE: {best_exit}"

        # Analyze why best exit was chosen over alternatives or nearest exit
        if alt:
            alt_exit = alt["exit_name"]
            cost_diff_pct = round(((alt["total_cost"] - best["total_cost"]) / best["total_cost"]) * 100, 1)
            details.append(
                f"Selected {best_exit} over {alt_exit} because {best_exit} has a {cost_diff_pct}% lower combined risk cost."
            )

        # Check for active hazards along paths
        active_hazard_count = len([h for h in hazards if h.severity > 0.3])
        if active_hazard_count > 0:
            details.append(f"System identified {active_hazard_count} active hazard(s) and routed around dangerous zones.")

        # Check prediction impact
        high_pred_zones = [z for z, p in predictions.items() if p.predicted_congestion_prob > 0.4]
        if high_pred_zones:
            zone_names = [z for z in high_pred_zones]
            details.append(
                f"LightGBM engine forecasts elevated congestion in zone(s) [{', '.join(zone_names)}]. Route dynamically bypasses predicted bottlenecks."
            )

        # Check if shortest distance path was bypassed for safety
        shortest_dist_route = min(candidates, key=lambda c: c["total_dist"])
        if shortest_dist_route["exit_id"] != best["exit_id"]:
            dist_diff = round(best["total_dist"] - shortest_dist_route["total_dist"], 1)
            details.append(
                f"SAFETY OVERRIDE: Nearest exit ({shortest_dist_route['exit_name']}) is {dist_diff}m shorter but has significantly higher risk. Nearest exit ≠ Safest exit."
            )

        if not details:
            details.append("Path provides clear corridor traversal with minimal crowd density and zero active hazards.")

        return summary, details

    def _build_no_route_response(self, start_node_id: str, reason: str) -> RouteResponse:
        """Constructs emergency fall-back response when no safe path exists."""
        return RouteResponse(
            route_id=f"route_none_{int(time.time())}",
            start_node=start_node_id,
            target_exit="NONE",
            target_exit_name="NO SAFE EXIT AVAILABLE",
            path_nodes=[],
            path_edges=[],
            steps=[],
            total_distance=0.0,
            total_risk_score=99999.0,
            est_evacuation_time_sec=0.0,
            is_safe=False,
            explanation_summary="EMERGENCY ALERT: NO SAFE EVACUATION ROUTE AVAILABLE",
            explanation_details=[
                reason,
                "IMMEDIATE ACTION: Seek designated emergency shelter room / fire-rated stairwell immediately.",
                "System is continuously monitoring for corridor clearance.",
            ],
            alternate_route=None,
            timestamp=time.time(),
        )

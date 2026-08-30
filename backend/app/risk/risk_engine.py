from typing import Dict, List, Tuple, Optional
from app.models.schemas import Node, Edge, Hazard, ZoneCrowd, CongestionPrediction, RiskWeights


class RiskEngine:
    """
    Computes dynamic risk metrics and edge weights for the evacuation graph.
    
    Formula:
    Risk Cost = distance * (
        1.0 + 
        crowd_weight * crowd_density_risk +
        hazard_weight * hazard_severity_risk +
        prediction_weight * predicted_congestion_risk
    )
    """

    def __init__(self, weights: RiskWeights = None):
        self.weights = weights or RiskWeights()

    def update_weights(self, weights: RiskWeights):
        self.weights = weights

    def calculate_hazard_risk(
        self, zone_id: str, edge_id: str, hazards: List[Hazard], node_id: Optional[str] = None
    ) -> float:
        """Calculates maximum hazard severity impacting a zone, node, or edge."""
        max_severity = 0.0
        for hazard in hazards:
            matches_edge = hazard.edge_id and (hazard.edge_id == edge_id)
            matches_zone = hazard.zone_id and (hazard.zone_id == zone_id)
            matches_node = hazard.node_id and node_id and (hazard.node_id == node_id)

            if matches_edge or matches_zone or matches_node:
                multiplier = 1.0 if hazard.type == "fire" else (0.6 if hazard.type == "smoke" else 0.4)
                severity = hazard.severity * multiplier
                if severity > max_severity:
                    max_severity = severity
        return max_severity

    def calculate_crowd_risk(self, zone_id: str, crowd_zones: Dict[str, ZoneCrowd]) -> float:
        """Calculates crowd density risk [0.0 - 1.0]. Density > 3.5 people/m^2 is max panic risk."""
        if zone_id not in crowd_zones:
            return 0.0
        density = crowd_zones[zone_id].density
        return min(1.0, density / 3.5)

    def calculate_prediction_risk(self, zone_id: str, predictions: Dict[str, CongestionPrediction]) -> float:
        """Extracts near-future predicted congestion risk probability."""
        if zone_id not in predictions:
            return 0.0
        pred = predictions[zone_id]
        return min(1.0, pred.predicted_congestion_prob)

    def calculate_edge_cost(
        self,
        edge: Edge,
        nodes_dict: Dict[str, Node],
        hazards: List[Hazard],
        crowd_zones: Dict[str, ZoneCrowd],
        predictions: Dict[str, CongestionPrediction],
    ) -> Tuple[float, float, float, float]:
        """
        Computes dynamic traversal cost for an edge along with breakdown components.
        Returns: (total_cost, hazard_risk, crowd_risk, pred_risk)
        """
        if edge.is_blocked:
            return float("inf"), 1.0, 1.0, 1.0

        source_node = nodes_dict.get(edge.source)
        target_node = nodes_dict.get(edge.target)

        zone_id = target_node.zone_id if target_node else "zone_general"
        source_zone = source_node.zone_id if source_node else "zone_general"

        source_node_id = source_node.id if source_node else None
        target_node_id = target_node.id if target_node else None

        hazard_risk = max(
            self.calculate_hazard_risk(zone_id, edge.id, hazards, target_node_id),
            self.calculate_hazard_risk(source_zone, edge.id, hazards, source_node_id),
        )

        # Any active fire or smoke hazard >= 0.70 on a corridor or node makes it impassable
        if hazard_risk >= 0.70:
            return float("inf"), hazard_risk, 1.0, 1.0

        crowd_risk = max(
            self.calculate_crowd_risk(zone_id, crowd_zones),
            self.calculate_crowd_risk(source_zone, crowd_zones),
        )

        pred_risk = max(
            self.calculate_prediction_risk(zone_id, predictions),
            self.calculate_prediction_risk(source_zone, predictions),
        )

        w = self.weights
        risk_multiplier = (
            1.0
            + (w.hazard_weight * hazard_risk)
            + (w.crowd_weight * crowd_risk)
            + (w.prediction_weight * pred_risk)
        )

        total_cost = edge.distance * risk_multiplier
        return total_cost, hazard_risk, crowd_risk, pred_risk

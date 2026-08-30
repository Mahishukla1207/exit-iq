import pytest
from app.models.schemas import Node, Edge, Hazard, ZoneCrowd, CongestionPrediction, RiskWeights
from app.risk.risk_engine import RiskEngine


def test_hazard_risk_calculation():
    engine = RiskEngine()
    hazards = [
        Hazard(id="h1", zone_id="zone_north", type="fire", severity=0.8),
        Hazard(id="h2", zone_id="zone_west", type="smoke", severity=0.5),
    ]

    fire_risk = engine.calculate_hazard_risk("zone_north", "e1", hazards)
    assert fire_risk == 0.8  # Fire multiplier is 1.0

    smoke_risk = engine.calculate_hazard_risk("zone_west", "e2", hazards)
    assert pytest.approx(smoke_risk, 0.01) == 0.3  # Smoke multiplier is 0.6


def test_edge_cost_dynamic_formula():
    weights = RiskWeights(hazard_weight=5.0, crowd_weight=2.0, prediction_weight=3.0)
    engine = RiskEngine(weights)

    node1 = Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="z1")
    node2 = Node(id="n2", name="N2", type="room", x=10, y=0, zone_id="z2")
    nodes_dict = {"n1": node1, "n2": node2}

    edge = Edge(id="e1", source="n1", target="n2", distance=10.0)

    # Base cost with no hazard or crowd
    cost, h_r, c_r, p_r = engine.calculate_edge_cost(edge, nodes_dict, [], {}, {})
    assert cost == 10.0

    # Add hazard to z2
    hazards = [Hazard(id="h1", zone_id="z2", type="fire", severity=0.5)]
    cost_h, _, _, _ = engine.calculate_edge_cost(edge, nodes_dict, hazards, {}, {})
    # multiplier = 1.0 + 5.0 * 0.5 = 3.5; cost = 10.0 * 3.5 = 35.0
    assert pytest.approx(cost_h, 0.1) == 35.0


def test_blocked_edge_returns_infinite_cost():
    engine = RiskEngine()
    edge = Edge(id="e1", source="n1", target="n2", distance=10.0, is_blocked=True)
    cost, _, _, _ = engine.calculate_edge_cost(edge, {}, [], {}, {})
    assert cost == float("inf")

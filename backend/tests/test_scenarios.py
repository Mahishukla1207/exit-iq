import pytest
from app.simulation.simulation_engine import SimulationEngine


def test_scenario_1_normal():
    sim = SimulationEngine()
    sim.load_scenario("NORMAL")
    assert sim.active_route.is_safe is True
    assert sim.active_route.target_exit is not None


def test_scenario_2_fire_corridor():
    sim = SimulationEngine()
    sim.load_scenario("FIRE_CORRIDOR")
    assert sim.active_route.is_safe is True
    assert "node_north_hall" not in sim.active_route.path_nodes


def test_scenario_3_exit_congestion():
    sim = SimulationEngine()
    sim.load_scenario("EXIT_CONGESTION")
    assert sim.active_route.is_safe is True
    # Exit A is heavily congested, route should prefer Exit B, C, or D
    assert sim.active_route.target_exit != "exit_a"


def test_scenario_4_predictive_congestion():
    sim = SimulationEngine()
    sim.load_scenario("PREDICTIVE_CONGESTION")
    assert sim.active_route.is_safe is True
    # Should contain explanation referencing forecast / predictive congestion
    assert any("LightGBM" in desc or "prediction" in desc.lower() for desc in sim.active_route.explanation_details)


def test_scenario_6_no_safe_route():
    sim = SimulationEngine()
    sim.load_scenario("NO_SAFE_ROUTE")
    assert sim.active_route.is_safe is False
    assert sim.active_route.target_exit == "NONE"
    assert "NO SAFE EVACUATION ROUTE" in sim.active_route.explanation_summary

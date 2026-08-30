import pytest
from app.simulation.simulation_engine import SimulationEngine


def test_routing_engine_finds_valid_route():
    sim = SimulationEngine()
    route = sim.active_route
    assert route is not None
    assert route.is_safe is True
    assert len(route.path_nodes) > 1
    assert route.target_exit in ["exit_a", "exit_b", "exit_c", "exit_d"]


def test_routing_recalculation_on_hazard():
    sim = SimulationEngine()
    sim.load_scenario("NORMAL")
    initial_exit = sim.active_route.target_exit

    # Trigger fire in North Corridor (blocking path to Exit B)
    sim.load_scenario("FIRE_CORRIDOR")
    new_route = sim.active_route

    assert new_route.is_safe is True
    # Path should not pass through node_north_hall
    assert "node_north_hall" not in new_route.path_nodes

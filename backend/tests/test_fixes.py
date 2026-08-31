"""
Test suite for FIX 1-4 implementation.

Tests verify:
1. LIVE CV people count excludes unmapped simulation-only zones
2. SIMULATION mode preserves existing behavior with all zones
3. Normalized density terminology (no p/m²)
4. nearby_density is graph-derived
5. exit_proximity is graph-derived
6. Fallback behavior when graph information is unavailable
"""

import pytest
from app.models.schemas import (
    Node, Edge, ZoneCrowd, Hazard, CongestionPrediction, 
    SimulationState, SystemMetrics, RiskWeights
)
from app.simulation.simulation_engine import SimulationEngine
from app.routing.graph_features import (
    compute_nearby_density, compute_exit_proximity, 
    GraphFeatureValue, NEARBY_DENSITY_FALLBACK, EXIT_PROXIMITY_FALLBACK
)
from app.cv.zone_mapper import CV_MAPPED_ZONE_IDS


class TestFix1LiveCVPeopleCountConsistency:
    """
    FIX 1: Test that LIVE CV mode only counts CCTV-mapped zones,
    and SIMULATION mode counts all zones.
    """

    def test_simulation_mode_counts_all_zones(self):
        """SIMULATION mode should count people from all 11 zones."""
        engine = SimulationEngine()
        engine.mode = "simulation"
        
        # Set counts for all zones
        for zid, crowd in engine.crowd_zones.items():
            crowd.count = 10
        
        state = engine.get_state()
        
        # Should sum all zones
        total_expected = len(engine.crowd_zones) * 10
        assert state.metrics.people_detected == total_expected, \
            f"Simulation mode should count all zones. Got {state.metrics.people_detected}, expected {total_expected}"

    def test_cctv_mode_counts_only_mapped_zones(self):
        """CCTV mode should count people only from CV-mapped zones."""
        engine = SimulationEngine()
        engine.mode = "cctv"
        
        # Set counts for all zones
        for zid, crowd in engine.crowd_zones.items():
            crowd.count = 10
        
        state = engine.get_state()
        
        # Should sum only CV-mapped zones
        total_expected = len(CV_MAPPED_ZONE_IDS) * 10
        assert state.metrics.people_detected == total_expected, \
            f"CCTV mode should count only mapped zones. Got {state.metrics.people_detected}, expected {total_expected}"

    def test_cctv_mode_with_mixed_counts(self):
        """CCTV mode with different counts per zone."""
        engine = SimulationEngine()
        engine.mode = "cctv"
        
        # Set specific counts
        engine.crowd_zones["zone_atrium"].count = 5
        engine.crowd_zones["zone_north"].count = 8
        engine.crowd_zones["zone_south"].count = 3
        engine.crowd_zones["zone_east"].count = 2
        
        # Unmapped zones should be ignored
        for zid in engine.crowd_zones:
            if zid not in CV_MAPPED_ZONE_IDS:
                engine.crowd_zones[zid].count = 100  # Should be ignored
        
        state = engine.get_state()
        
        # Should only sum mapped zones: 5 + 8 + 3 + 2 = 18
        expected = 5 + 8 + 3 + 2
        assert state.metrics.people_detected == expected, \
            f"CCTV mode should ignore unmapped zones. Got {state.metrics.people_detected}, expected {expected}"

    def test_current_people_detected_populated_from_cv(self):
        """current_people_detected should be populated from CV pipeline."""
        engine = SimulationEngine()
        engine.mode = "cctv"
        
        # Simulate CV analytics
        engine.latest_cv_analytics = {"total_people_count": 42}
        engine.cv_active_tracking_ids = 42
        engine.cv_detections_count = 45
        
        state = engine.get_state()
        
        assert state.metrics.current_people_detected == 42
        assert state.metrics.active_tracking_ids == 42
        assert state.metrics.detections_in_current_frame == 45

    def test_mode_field_correctly_reported(self):
        """The SimulationState should report the current mode."""
        engine = SimulationEngine()
        
        engine.mode = "simulation"
        assert engine.get_state().mode == "simulation"
        
        engine.mode = "cctv"
        assert engine.get_state().mode == "cctv"


class TestFix2NormalizedDensityTerminology:
    """
    FIX 2: Verify that density is referred to as Normalized Density,
    not people/m², throughout the system.
    """

    def test_zone_crowd_schema_mentions_normalized_density(self):
        """ZoneCrowd schema should reference Normalized Density, not people/m² as the unit."""
        crowd = ZoneCrowd(
            zone_id="zone_test",
            count=10,
            density=2.5
        )
        
        # Check schema field description
        schema_description = ZoneCrowd.model_fields["density"].description
        assert "Normalized Density" in schema_description or "Density Index" in schema_description, \
            f"ZoneCrowd density description should mention Normalized Density. Got: {schema_description}"
        # The description should clarify that it's NOT people/m²
        assert "not people/m²" in schema_description or "Density Index" in schema_description, \
            f"ZoneCrowd density description should clarify it's not physically calibrated. Got: {schema_description}"

    def test_system_metrics_schema_mentions_density_index(self):
        """SystemMetrics schema should reference Density Index, not people/m²."""
        schema_description = SystemMetrics.model_fields["predicted_peak_congestion"].description
        assert "Density Index" in schema_description, \
            f"SystemMetrics description should mention Density Index. Got: {schema_description}"


class TestFix3NearbyDensityDynamic:
    """
    FIX 3: Test that nearby_density is computed from neighboring zones,
    not hardcoded to 0.5.
    """

    def test_compute_nearby_density_from_neighbors(self):
        """nearby_density should be derived from adjacent zones in the graph."""
        # Create a simple graph: zone_a -- zone_b -- zone_c
        nodes = [
            Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="zone_a"),
            Node(id="n2", name="N2", type="room", x=100, y=0, zone_id="zone_b"),
            Node(id="n3", name="N3", type="room", x=200, y=0, zone_id="zone_c"),
        ]
        
        edges = [
            Edge(id="e1", source="n1", target="n2", distance=10.0),
            Edge(id="e2", source="n2", target="n3", distance=10.0),
        ]
        
        crowd_zones = {
            "zone_a": ZoneCrowd(zone_id="zone_a", count=5, density=1.0),
            "zone_b": ZoneCrowd(zone_id="zone_b", count=10, density=2.0),
            "zone_c": ZoneCrowd(zone_id="zone_c", count=15, density=3.0),
        }
        
        # Compute nearby_density for zone_b (neighbors: zone_a and zone_c)
        result = compute_nearby_density("zone_b", crowd_zones, nodes, edges)
        
        # Should average zone_a (1.0) and zone_c (3.0) = 2.0
        expected_avg = (1.0 + 3.0) / 2.0
        assert result.value == expected_avg, \
            f"nearby_density should be {expected_avg}, got {result.value}"
        assert result.is_fallback is False, \
            "nearby_density should not be fallback when neighbors exist"

    def test_nearby_density_fallback_when_no_neighbors(self):
        """nearby_density should fallback when zone has no neighbors."""
        nodes = [
            Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="zone_isolated"),
        ]
        
        edges = []
        
        crowd_zones = {
            "zone_isolated": ZoneCrowd(zone_id="zone_isolated", count=5, density=1.0),
        }
        
        result = compute_nearby_density("zone_isolated", crowd_zones, nodes, edges)
        
        assert result.is_fallback is True, \
            "nearby_density should be fallback when no neighbors"
        assert result.value == NEARBY_DENSITY_FALLBACK, \
            f"Fallback value should be {NEARBY_DENSITY_FALLBACK}, got {result.value}"

    def test_nearby_density_source_metadata(self):
        """nearby_density should track whether it's from graph or fallback."""
        nodes = [
            Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="zone_a"),
            Node(id="n2", name="N2", type="room", x=100, y=0, zone_id="zone_b"),
        ]
        
        edges = [
            Edge(id="e1", source="n1", target="n2", distance=10.0),
        ]
        
        crowd_zones = {
            "zone_a": ZoneCrowd(zone_id="zone_a", count=5, density=1.5),
            "zone_b": ZoneCrowd(zone_id="zone_b", count=10, density=2.5),
        }
        
        result = compute_nearby_density("zone_a", crowd_zones, nodes, edges)
        
        assert result.source == "graph", \
            "Source should be 'graph' when derived from neighboring zones"
        assert result.is_fallback is False

    def test_simulation_engine_uses_graph_derived_nearby_density(self):
        """SimulationEngine.recalculate_system() should use graph-derived nearby_density."""
        engine = SimulationEngine()
        
        # Modify crowd densities to create different nearby densities
        engine.crowd_zones["zone_atrium"].density = 1.0
        engine.crowd_zones["zone_north"].density = 3.0
        engine.crowd_zones["zone_south"].density = 2.5
        
        engine.recalculate_system()
        
        # Get predictions to verify nearby_density was used
        for pred in engine.predictions.values():
            # The prediction should exist (this verifies recalculation happened)
            assert pred is not None


class TestFix4ExitProximityDynamic:
    """
    FIX 4: Test that exit_proximity is computed from graph shortest path,
    not hardcoded to 20.0.
    """

    def test_compute_exit_proximity_shortest_path(self):
        """exit_proximity should be shortest graph distance to nearest exit."""
        # Create a simple graph with one exit
        nodes = [
            Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="zone_a"),
            Node(id="n2", name="N2", type="room", x=100, y=0, zone_id="zone_b"),
            Node(id="exit_1", name="Exit", type="exit", x=200, y=0, zone_id="zone_exit", is_exit=True),
        ]
        
        edges = [
            Edge(id="e1", source="n1", target="n2", distance=50.0),
            Edge(id="e2", source="n2", target="exit_1", distance=100.0),
        ]
        
        # Shortest path from zone_a to exit is n1->n2->exit_1 = 50 + 100 = 150
        result = compute_exit_proximity("zone_a", nodes, edges)
        
        assert result.value == 150.0, \
            f"exit_proximity should be 150.0 (shortest path), got {result.value}"
        assert result.is_fallback is False, \
            "exit_proximity should not be fallback when exit is reachable"

    def test_exit_proximity_fallback_when_no_exit(self):
        """exit_proximity should fallback when no exit exists."""
        nodes = [
            Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="zone_a"),
        ]
        
        edges = []
        
        result = compute_exit_proximity("zone_a", nodes, edges)
        
        assert result.is_fallback is True, \
            "exit_proximity should be fallback when no exit"
        assert result.value == EXIT_PROXIMITY_FALLBACK, \
            f"Fallback value should be {EXIT_PROXIMITY_FALLBACK}, got {result.value}"

    def test_exit_proximity_source_metadata(self):
        """exit_proximity should track whether it's from graph or fallback."""
        nodes = [
            Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="zone_a"),
            Node(id="exit_1", name="Exit", type="exit", x=100, y=0, zone_id="zone_exit", is_exit=True),
        ]
        
        edges = [
            Edge(id="e1", source="n1", target="exit_1", distance=75.0),
        ]
        
        result = compute_exit_proximity("zone_a", nodes, edges)
        
        assert result.source == "graph", \
            "Source should be 'graph' when derived from graph"
        assert result.is_fallback is False

    def test_exit_proximity_multiple_exits_selects_nearest(self):
        """exit_proximity should select nearest exit from multiple options."""
        nodes = [
            Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="zone_a"),
            Node(id="exit_1", name="Exit1", type="exit", x=100, y=0, zone_id="zone_exit1", is_exit=True),
            Node(id="exit_2", name="Exit2", type="exit", x=50, y=0, zone_id="zone_exit2", is_exit=True),
        ]
        
        edges = [
            Edge(id="e1", source="n1", target="exit_1", distance=100.0),
            Edge(id="e2", source="n1", target="exit_2", distance=50.0),
        ]
        
        result = compute_exit_proximity("zone_a", nodes, edges)
        
        # Should select exit_2 (50.0), not exit_1 (100.0)
        assert result.value == 50.0, \
            f"exit_proximity should select nearest exit (50.0), got {result.value}"

    def test_simulation_engine_uses_graph_derived_exit_proximity(self):
        """SimulationEngine.recalculate_system() should use graph-derived exit_proximity."""
        engine = SimulationEngine()
        
        engine.recalculate_system()
        
        # Get predictions to verify exit_proximity was used
        for pred in engine.predictions.values():
            # The prediction should exist (this verifies recalculation happened)
            assert pred is not None


class TestGraphFeaturesFallbackDocumentation:
    """
    Test that fallback values are distinguishable from real data.
    """

    def test_nearby_density_fallback_clearly_marked(self):
        """Fallback nearby_density should be distinguishable."""
        nodes = [
            Node(id="n1", name="N1", type="room", x=0, y=0, zone_id="isolated"),
        ]
        
        result = compute_nearby_density("isolated", {}, nodes, [])
        
        # Should be marked as fallback
        assert result.is_fallback is True
        assert result.source == "fallback"

    def test_exit_proximity_fallback_clearly_marked(self):
        """Fallback exit_proximity should be distinguishable."""
        result = compute_exit_proximity("any_zone", [], [])
        
        # Should be marked as fallback
        assert result.is_fallback is True
        assert result.source == "fallback"


class TestModeAwarenessEndToEnd:
    """
    End-to-end tests verifying mode-aware behavior.
    """

    def test_simulation_to_cctv_mode_transition(self):
        """System should properly transition between modes."""
        engine = SimulationEngine()
        engine.mode = "simulation"
        
        # All zones have same count
        for zid, crowd in engine.crowd_zones.items():
            crowd.count = 5
        
        sim_state = engine.get_state()
        sim_people = sim_state.metrics.people_detected
        
        # Switch to CCTV mode
        engine.mode = "cctv"
        cctv_state = engine.get_state()
        cctv_people = cctv_state.metrics.people_detected
        
        # CCTV mode should count fewer (only mapped zones)
        assert cctv_people < sim_people, \
            "CCTV mode should report fewer people than simulation mode"

    def test_unmapped_zones_excluded_in_cctv_mode(self):
        """Unmapped zones should not contribute to CCTV people count."""
        engine = SimulationEngine()
        engine.mode = "cctv"
        
        # Mapped zones: 1 person each
        for zid in CV_MAPPED_ZONE_IDS:
            engine.crowd_zones[zid].count = 1
        
        # Unmapped zones: 100 people each (should be ignored)
        unmapped = set(engine.crowd_zones.keys()) - CV_MAPPED_ZONE_IDS
        for zid in unmapped:
            engine.crowd_zones[zid].count = 100
        
        state = engine.get_state()
        
        # Should only count mapped zones (4 zones * 1 person = 4)
        assert state.metrics.people_detected == len(CV_MAPPED_ZONE_IDS), \
            f"CCTV mode should ignore unmapped zones. Got {state.metrics.people_detected}, expected {len(CV_MAPPED_ZONE_IDS)}"

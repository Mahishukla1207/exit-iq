"""
Graph-derived spatial features for LightGBM congestion prediction.

Uses the existing building topology (Node/Edge models) via NetworkX.
Distances use graph edge distance attributes (building-map scale units;
not physically calibrated to real-world meters).
"""

from dataclasses import dataclass
from typing import Dict, List, Set

import networkx as nx

from app.models.schemas import Edge, Node, ZoneCrowd

# Explicit fallbacks when graph topology or neighbor data is unavailable.
# These sentinel defaults are distinguishable via GraphFeatureValue.is_fallback.
NEARBY_DENSITY_FALLBACK = 0.5
EXIT_PROXIMITY_FALLBACK = 20.0


@dataclass(frozen=True)
class GraphFeatureValue:
    """A graph-derived scalar with provenance metadata."""

    value: float
    is_fallback: bool
    source: str  # "graph" or "fallback"


def build_topology_graph(nodes: List[Node], edges: List[Edge]) -> nx.Graph:
    """Builds an undirected topology graph weighted by edge distance."""
    graph = nx.Graph()
    for node in nodes:
        graph.add_node(node.id, zone_id=node.zone_id, is_exit=node.is_exit)
    for edge in edges:
        if edge.is_blocked:
            continue
        graph.add_edge(edge.source, edge.target, distance=edge.distance)
    return graph


def get_neighbor_zone_ids(zone_id: str, nodes: List[Node], edges: List[Edge]) -> Set[str]:
    """Returns zone IDs adjacent to zone_id via any traversable graph edge."""
    graph = build_topology_graph(nodes, edges)
    zone_node_ids = [n.id for n in nodes if n.zone_id == zone_id]

    neighbors: Set[str] = set()
    for node_id in zone_node_ids:
        if node_id not in graph:
            continue
        for adjacent_node in graph.neighbors(node_id):
            adjacent_zone = graph.nodes[adjacent_node].get("zone_id")
            if adjacent_zone and adjacent_zone != zone_id:
                neighbors.add(adjacent_zone)
    return neighbors


def compute_nearby_density(
    zone_id: str,
    crowd_zones: Dict[str, ZoneCrowd],
    nodes: List[Node],
    edges: List[Edge],
) -> GraphFeatureValue:
    """
    Average Density Index of graph-adjacent zones.
    Falls back to NEARBY_DENSITY_FALLBACK when no neighbors or densities exist.
    """
    neighbor_zones = get_neighbor_zone_ids(zone_id, nodes, edges)
    if not neighbor_zones:
        return GraphFeatureValue(NEARBY_DENSITY_FALLBACK, True, "fallback")

    densities = [crowd_zones[nz].density for nz in neighbor_zones if nz in crowd_zones]
    if not densities:
        return GraphFeatureValue(NEARBY_DENSITY_FALLBACK, True, "fallback")

    return GraphFeatureValue(sum(densities) / len(densities), False, "graph")


def compute_exit_proximity(zone_id: str, nodes: List[Node], edges: List[Edge]) -> GraphFeatureValue:
    """
    Shortest graph distance from any node in zone_id to the nearest emergency exit.

    Distance is the sum of Edge.distance along the shortest path (building-map graph
    units — same scale as the floor-plan edge metadata, not calibrated real-world meters).
    Falls back to EXIT_PROXIMITY_FALLBACK when no reachable exit exists.
    """
    graph = build_topology_graph(nodes, edges)
    exit_node_ids = [n.id for n in nodes if n.is_exit]
    zone_node_ids = [n.id for n in nodes if n.zone_id == zone_id]

    if not exit_node_ids or not zone_node_ids:
        return GraphFeatureValue(EXIT_PROXIMITY_FALLBACK, True, "fallback")

    min_distance = float("inf")
    for zone_node_id in zone_node_ids:
        if zone_node_id not in graph:
            continue
        for exit_node_id in exit_node_ids:
            if exit_node_id not in graph:
                continue
            try:
                path_distance = nx.shortest_path_length(
                    graph, zone_node_id, exit_node_id, weight="distance"
                )
                min_distance = min(min_distance, path_distance)
            except nx.NetworkXNoPath:
                continue

    if min_distance == float("inf"):
        return GraphFeatureValue(EXIT_PROXIMITY_FALLBACK, True, "fallback")

    return GraphFeatureValue(min_distance, False, "graph")

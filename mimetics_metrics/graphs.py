"""
Graph construction utilities for temporal network analysis.
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


def build_graph(
    interactions_df: pd.DataFrame,
    src_col: str = "src",
    dst_col: str = "dst",
    directed: bool = True
) -> nx.Graph:
    """
    Build a network graph from interactions DataFrame.
    
    Args:
        interactions_df: DataFrame with interactions
        src_col: Source column name
        dst_col: Destination column name
        directed: Whether to create directed graph
        
    Returns:
        NetworkX graph object
    """
    if len(interactions_df) == 0:
        return nx.DiGraph() if directed else nx.Graph()
    
    # Create graph
    if directed:
        G = nx.DiGraph()
    else:
        G = nx.Graph()
    
    # Add edges
    for _, row in interactions_df.iterrows():
        src = row[src_col]
        dst = row[dst_col]
        
        if src != dst:  # Skip self-loops
            if G.has_edge(src, dst):
                # If edge exists, increment weight (for multiple interactions)
                G[src][dst]['weight'] = G[src][dst].get('weight', 1) + 1
            else:
                G.add_edge(src, dst, weight=1)
    
    logger.info(f"Built {'directed' if directed else 'undirected'} graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def build_undirected_projection(directed_graph: nx.DiGraph) -> nx.Graph:
    """
    Build undirected projection of a directed graph.
    
    Args:
        directed_graph: Directed NetworkX graph
        
    Returns:
        Undirected NetworkX graph
    """
    return directed_graph.to_undirected()


def get_graph_metadata(G: nx.Graph) -> Dict[str, Any]:
    """
    Get basic metadata for a graph.
    
    Args:
        G: NetworkX graph
        
    Returns:
        Dictionary with graph metadata
    """
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    
    # Calculate density
    if n_nodes <= 1:
        density = 0.0
    else:
        if G.is_directed():
            max_edges = n_nodes * (n_nodes - 1)
        else:
            max_edges = n_nodes * (n_nodes - 1) / 2
        density = n_edges / max_edges if max_edges > 0 else 0.0
    
    # Check connectivity
    if G.is_directed():
        is_weakly_connected = nx.is_weakly_connected(G)
        is_strongly_connected = nx.is_strongly_connected(G)
        n_weakly_components = nx.number_weakly_connected_components(G)
        n_strongly_components = nx.number_strongly_connected_components(G)
    else:
        is_weakly_connected = nx.is_connected(G)
        is_strongly_connected = None
        n_weakly_components = nx.number_connected_components(G)
        n_strongly_components = None
    
    return {
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'density': density,
        'is_weakly_connected': is_weakly_connected,
        'is_strongly_connected': is_strongly_connected,
        'n_weakly_components': n_weakly_components,
        'n_strongly_components': n_strongly_components
    }


def get_node_degrees(G: nx.Graph, node: str) -> Dict[str, int]:
    """
    Get degree information for a specific node.
    
    Args:
        G: NetworkX graph
        node: Node ID
        
    Returns:
        Dictionary with degree information
    """
    if not G.has_node(node):
        return {
            'in_degree': 0,
            'out_degree': 0,
            'total_degree': 0
        }
    
    if G.is_directed():
        return {
            'in_degree': G.in_degree(node),
            'out_degree': G.out_degree(node),
            'total_degree': G.degree(node)
        }
    else:
        degree = G.degree(node)
        return {
            'in_degree': degree,
            'out_degree': degree,
            'total_degree': degree
        }


def get_ego_network(G: nx.Graph, node: str) -> nx.Graph:
    """
    Get ego network (neighbors) for a specific node.
    
    Args:
        G: NetworkX graph
        node: Node ID
        
    Returns:
        Subgraph induced by node and its neighbors
    """
    if not G.has_node(node):
        return G.subgraph([])
    
    neighbors = list(G.neighbors(node))
    ego_nodes = [node] + neighbors
    
    return G.subgraph(ego_nodes)


def calculate_ego_density(G: nx.Graph, node: str) -> float:
    """
    Calculate ego density for a specific node.
    
    Args:
        G: NetworkX graph
        node: Node ID
        
    Returns:
        Ego density (density of subgraph induced by neighbors)
    """
    ego_net = get_ego_network(G, node)
    
    if ego_net.number_of_nodes() < 2:
        return 0.0
    
    # Remove the ego node to get neighbors-only subgraph
    neighbors = [n for n in ego_net.nodes() if n != node]
    if len(neighbors) < 2:
        return 0.0
    
    neighbors_subgraph = ego_net.subgraph(neighbors)
    n = neighbors_subgraph.number_of_nodes()
    m = neighbors_subgraph.number_of_edges()
    
    # Density for undirected graph
    max_edges = n * (n - 1) / 2
    return m / max_edges if max_edges > 0 else 0.0


def get_strongly_connected_component_size(G: nx.DiGraph, node: str) -> int:
    """
    Get size of strongly connected component containing a node.
    
    Args:
        G: Directed NetworkX graph
        node: Node ID
        
    Returns:
        Size of SCC containing the node
    """
    if not G.has_node(node):
        return 0
    
    sccs = list(nx.strongly_connected_components(G))
    for scc in sccs:
        if node in scc:
            return len(scc)
    
    return 1  # Node is in its own SCC


def calculate_reciprocity(G: nx.DiGraph, node: str) -> int:
    """
    Calculate reciprocity for a specific node (number of mutual connections).
    
    Args:
        G: Directed NetworkX graph
        node: Node ID
        
    Returns:
        Number of reciprocal connections
    """
    if not G.has_node(node):
        return 0
    
    reciprocal_count = 0
    for neighbor in G.neighbors(node):
        if G.has_edge(neighbor, node):
            reciprocal_count += 1
    
    return reciprocal_count


def get_shortest_paths_to_node(
    G: nx.Graph, 
    target_node: str, 
    max_length: Optional[int] = None
) -> Dict[str, float]:
    """
    Get shortest path lengths to a target node.
    
    Args:
        G: NetworkX graph
        target_node: Target node ID
        max_length: Maximum path length to consider
        
    Returns:
        Dictionary mapping node_id to shortest path length
    """
    if not G.has_node(target_node):
        return {}
    
    try:
        if max_length:
            paths = nx.single_source_shortest_path_length(
                G, target_node, cutoff=max_length
            )
        else:
            paths = nx.single_source_shortest_path_length(G, target_node)
        
        return dict(paths)
    except nx.NetworkXNoPath:
        return {}


def calculate_median_distance_to_node(G: nx.Graph, target_node: str) -> float:
    """
    Calculate median distance to a target node.
    
    Args:
        G: NetworkX graph
        target_node: Target node ID
        
    Returns:
        Median distance to target node
    """
    distances = get_shortest_paths_to_node(G, target_node)
    
    if not distances:
        return np.nan
    
    # Remove the target node itself (distance 0)
    other_distances = [d for node, d in distances.items() if node != target_node]
    
    if not other_distances:
        return np.nan
    
    return np.median(other_distances)


def get_connected_components(G: nx.Graph) -> List[set]:
    """
    Get connected components of a graph.
    
    Args:
        G: NetworkX graph
        
    Returns:
        List of connected components (sets of nodes)
    """
    if G.is_directed():
        return list(nx.weakly_connected_components(G))
    else:
        return list(nx.connected_components(G))


def calculate_effective_diameter(G: nx.Graph, percentile: float = 0.9) -> float:
    """
    Calculate effective diameter of a graph.
    
    Args:
        G: NetworkX graph
        percentile: Percentile for effective diameter (default 0.9)
        
    Returns:
        Effective diameter
    """
    if G.number_of_nodes() < 2:
        return 0.0
    
    try:
        # Get all shortest path lengths
        all_paths = dict(nx.all_pairs_shortest_path_length(G))
        
        # Collect all distances
        distances = []
        for source, targets in all_paths.items():
            for target, distance in targets.items():
                if source != target:  # Exclude self-distances
                    distances.append(distance)
        
        if not distances:
            return 0.0
        
        # Calculate effective diameter
        distances = np.array(distances)
        return np.percentile(distances, percentile * 100)
        
    except nx.NetworkXError:
        return np.nan

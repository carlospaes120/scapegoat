"""
Community detection and analysis utilities.
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging

try:
    import leidenalg
    from leidenalg import find_partition
    from leidenalg import ModularityVertexPartition
    LEIDEN_AVAILABLE = True
except ImportError:
    LEIDEN_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("leidenalg not available, falling back to Louvain")

from sklearn.metrics import normalized_mutual_info_score

logger = logging.getLogger(__name__)


def detect_communities(
    G: nx.Graph,
    method: str = "auto",
    resolution: float = 1.0,
    random_state: Optional[int] = None
) -> Dict[str, int]:
    """
    Detect communities in a graph using specified method.
    
    Args:
        G: NetworkX graph
        method: Community detection method ("leiden", "louvain", "auto")
        resolution: Resolution parameter for community detection
        random_state: Random state for reproducibility
        
    Returns:
        Dictionary mapping node_id to community_id
    """
    if G.number_of_nodes() == 0:
        return {}
    
    if G.number_of_nodes() == 1:
        return {list(G.nodes())[0]: 0}
    
    # Choose method
    if method == "auto":
        method = "leiden" if LEIDEN_AVAILABLE else "louvain"
    
    if method == "leiden" and LEIDEN_AVAILABLE:
        return _detect_communities_leiden(G, resolution, random_state)
    else:
        return _detect_communities_louvain(G, resolution, random_state)


def _detect_communities_leiden(
    G: nx.Graph,
    resolution: float = 1.0,
    random_state: Optional[int] = None
) -> Dict[str, int]:
    """
    Detect communities using Leiden algorithm.
    
    Args:
        G: NetworkX graph
        resolution: Resolution parameter
        random_state: Random state for reproducibility
        
    Returns:
        Dictionary mapping node_id to community_id
    """
    try:
        # Convert to igraph format
        import igraph as ig
        
        # Convert NetworkX graph to igraph
        if G.is_directed():
            ig_graph = ig.Graph.from_networkx(G.to_undirected())
        else:
            ig_graph = ig.Graph.from_networkx(G)
        
        # Set random seed if provided
        if random_state is not None:
            np.random.seed(random_state)
        
        # Find partition using Leiden algorithm
        partition = find_partition(
            ig_graph,
            ModularityVertexPartition,
            resolution_parameter=resolution,
            random_state=random_state
        )
        
        # Convert to node mapping
        communities = {}
        for i, community_id in enumerate(partition.membership):
            node_id = ig_graph.vs[i]['name']
            communities[node_id] = community_id
        
        return communities
        
    except Exception as e:
        logger.warning(f"Leiden algorithm failed: {e}, falling back to Louvain")
        return _detect_communities_louvain(G, resolution, random_state)


def _detect_communities_louvain(
    G: nx.Graph,
    resolution: float = 1.0,
    random_state: Optional[int] = None
) -> Dict[str, int]:
    """
    Detect communities using Louvain algorithm.
    
    Args:
        G: NetworkX graph
        resolution: Resolution parameter
        random_state: Random state for reproducibility
        
    Returns:
        Dictionary mapping node_id to community_id
    """
    try:
        # Use NetworkX's Louvain implementation
        communities = nx.community.louvain_communities(
            G, 
            weight='weight',
            resolution=resolution,
            seed=random_state
        )
        
        # Convert to node mapping
        node_to_community = {}
        for community_id, nodes in enumerate(communities):
            for node in nodes:
                node_to_community[node] = community_id
        
        return node_to_community
        
    except Exception as e:
        logger.error(f"Louvain algorithm failed: {e}")
        # Fallback: assign each node to its own community
        return {node: i for i, node in enumerate(G.nodes())}


def calculate_nmi(
    communities1: Dict[str, int],
    communities2: Dict[str, int]
) -> float:
    """
    Calculate Normalized Mutual Information between two community partitions.
    
    Args:
        communities1: First community partition
        communities2: Second community partition
        
    Returns:
        NMI score (0-1, higher means more similar)
    """
    if not communities1 or not communities2:
        return np.nan
    
    # Get common nodes
    common_nodes = set(communities1.keys()) & set(communities2.keys())
    
    if len(common_nodes) < 2:
        return np.nan
    
    # Create label arrays for common nodes
    labels1 = [communities1[node] for node in common_nodes]
    labels2 = [communities2[node] for node in common_nodes]
    
    try:
        return normalized_mutual_info_score(labels1, labels2)
    except ValueError:
        return np.nan


def calculate_modularity(
    G: nx.Graph,
    communities: Dict[str, int]
) -> float:
    """
    Calculate modularity of a community partition.
    
    Args:
        G: NetworkX graph
        communities: Community partition
        
    Returns:
        Modularity score
    """
    if not communities:
        return 0.0
    
    try:
        # Convert to list of sets
        community_sets = {}
        for node, comm_id in communities.items():
            if comm_id not in community_sets:
                community_sets[comm_id] = set()
            community_sets[comm_id].add(node)
        
        community_list = list(community_sets.values())
        
        return nx.community.modularity(G, community_list)
    except Exception as e:
        logger.warning(f"Modularity calculation failed: {e}")
        return np.nan


def get_community_sizes(communities: Dict[str, int]) -> Dict[int, int]:
    """
    Get size of each community.
    
    Args:
        communities: Community partition
        
    Returns:
        Dictionary mapping community_id to size
    """
    sizes = {}
    for node, comm_id in communities.items():
        sizes[comm_id] = sizes.get(comm_id, 0) + 1
    return sizes


def get_largest_community(communities: Dict[str, int]) -> Tuple[int, int]:
    """
    Get the largest community and its size.
    
    Args:
        communities: Community partition
        
    Returns:
        Tuple of (community_id, size)
    """
    if not communities:
        return None, 0
    
    sizes = get_community_sizes(communities)
    if not sizes:
        return None, 0
    
    largest_comm = max(sizes.items(), key=lambda x: x[1])
    return largest_comm


def calculate_community_metrics(
    G: nx.Graph,
    communities: Dict[str, int]
) -> Dict[str, Any]:
    """
    Calculate comprehensive community metrics.
    
    Args:
        G: NetworkX graph
        communities: Community partition
        
    Returns:
        Dictionary with community metrics
    """
    if not communities:
        return {
            'n_communities': 0,
            'modularity': 0.0,
            'largest_community_size': 0,
            'largest_community_id': None,
            'avg_community_size': 0.0,
            'community_size_std': 0.0
        }
    
    # Basic metrics
    n_communities = len(set(communities.values()))
    modularity = calculate_modularity(G, communities)
    
    # Community sizes
    sizes = get_community_sizes(communities)
    size_values = list(sizes.values())
    
    largest_comm_id, largest_comm_size = get_largest_community(communities)
    avg_community_size = np.mean(size_values) if size_values else 0.0
    community_size_std = np.std(size_values) if len(size_values) > 1 else 0.0
    
    return {
        'n_communities': n_communities,
        'modularity': modularity,
        'largest_community_size': largest_comm_size,
        'largest_community_id': largest_comm_id,
        'avg_community_size': avg_community_size,
        'community_size_std': community_size_std
    }


def detect_communities_with_metrics(
    G: nx.Graph,
    method: str = "auto",
    resolution: float = 1.0,
    random_state: Optional[int] = None
) -> Tuple[Dict[str, int], Dict[str, Any]]:
    """
    Detect communities and calculate associated metrics.
    
    Args:
        G: NetworkX graph
        method: Community detection method
        resolution: Resolution parameter
        random_state: Random state for reproducibility
        
    Returns:
        Tuple of (communities, metrics)
    """
    communities = detect_communities(G, method, resolution, random_state)
    metrics = calculate_community_metrics(G, communities)
    
    return communities, metrics


def compare_communities(
    communities1: Dict[str, int],
    communities2: Dict[str, int]
) -> Dict[str, Any]:
    """
    Compare two community partitions.
    
    Args:
        communities1: First community partition
        communities2: Second community partition
        
    Returns:
        Dictionary with comparison metrics
    """
    nmi = calculate_nmi(communities1, communities2)
    
    # Get common nodes
    common_nodes = set(communities1.keys()) & set(communities2.keys())
    
    # Calculate Jaccard similarity for each community
    comm1_sets = {}
    comm2_sets = {}
    
    for node, comm_id in communities1.items():
        if comm_id not in comm1_sets:
            comm1_sets[comm_id] = set()
        comm1_sets[comm_id].add(node)
    
    for node, comm_id in communities2.items():
        if comm_id not in comm2_sets:
            comm2_sets[comm_id] = set()
        comm2_sets[comm_id].add(node)
    
    # Calculate average Jaccard similarity
    jaccard_scores = []
    for comm1_id, comm1_nodes in comm1_sets.items():
        best_jaccard = 0.0
        for comm2_id, comm2_nodes in comm2_sets.items():
            intersection = len(comm1_nodes & comm2_nodes)
            union = len(comm1_nodes | comm2_nodes)
            jaccard = intersection / union if union > 0 else 0.0
            best_jaccard = max(best_jaccard, jaccard)
        jaccard_scores.append(best_jaccard)
    
    avg_jaccard = np.mean(jaccard_scores) if jaccard_scores else 0.0
    
    return {
        'nmi': nmi,
        'avg_jaccard_similarity': avg_jaccard,
        'n_common_nodes': len(common_nodes),
        'n_communities_1': len(comm1_sets),
        'n_communities_2': len(comm2_sets)
    }

"""
Core metrics calculation for temporal network analysis.
"""

import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import logging
from scipy import stats
from sklearn.metrics import normalized_mutual_info_score

from .graphs import (
    build_graph, build_undirected_projection, get_graph_metadata,
    calculate_ego_density, get_strongly_connected_component_size,
    calculate_reciprocity, calculate_median_distance_to_node,
    calculate_effective_diameter
)

logger = logging.getLogger(__name__)


def calculate_pagerank(G: nx.DiGraph, alpha: float = 0.85) -> Dict[str, float]:
    """
    Calculate PageRank for all nodes in a directed graph.
    
    Args:
        G: Directed NetworkX graph
        alpha: Damping parameter
        
    Returns:
        Dictionary mapping node_id to PageRank score
    """
    if G.number_of_nodes() == 0:
        return {}
    
    try:
        pr = nx.pagerank(G, alpha=alpha)
        return pr
    except nx.PowerIterationFailedConvergence:
        logger.warning("PageRank failed to converge, using default values")
        return {node: 1.0 / G.number_of_nodes() for node in G.nodes()}


def calculate_betweenness_centrality(
    G: nx.Graph, 
    normalized: bool = True,
    k: Optional[int] = None
) -> Dict[str, float]:
    """
    Calculate betweenness centrality for all nodes.
    
    Args:
        G: NetworkX graph
        normalized: Whether to normalize centrality scores
        k: Number of nodes to sample for approximation (if None, use all nodes)
        
    Returns:
        Dictionary mapping node_id to betweenness centrality
    """
    if G.number_of_nodes() == 0:
        return {}
    
    try:
        if k and k < G.number_of_nodes():
            # Use sampling for large graphs
            bc = nx.betweenness_centrality(G, k=k, normalized=normalized)
        else:
            bc = nx.betweenness_centrality(G, normalized=normalized)
        return bc
    except nx.NetworkXError as e:
        logger.warning(f"Betweenness centrality calculation failed: {e}")
        return {node: 0.0 for node in G.nodes()}


def calculate_betweenness_centralization(G: nx.Graph) -> float:
    """
    Calculate Freeman betweenness centralization for a graph.
    
    Args:
        G: NetworkX graph
        
    Returns:
        Betweenness centralization score
    """
    if G.number_of_nodes() < 2:
        return 0.0
    
    # Calculate betweenness centrality
    bc = calculate_betweenness_centrality(G, normalized=False)
    
    if not bc:
        return 0.0
    
    # Find maximum betweenness
    max_bc = max(bc.values())
    
    # Calculate centralization
    n = G.number_of_nodes()
    if n <= 2:
        return 0.0
    
    # Theoretical maximum for directed graph
    if G.is_directed():
        max_theoretical = (n - 1) * (n - 2)
    else:
        max_theoretical = (n - 1) * (n - 2) / 2
    
    if max_theoretical == 0:
        return 0.0
    
    # Sum of differences from maximum
    sum_diff = sum(max_bc - bc_val for bc_val in bc.values())
    
    return sum_diff / max_theoretical


def calculate_topk_share(scores: Dict[str, float], k: int) -> float:
    """
    Calculate share of top-k nodes in total score.
    
    Args:
        scores: Dictionary mapping node_id to score
        k: Number of top nodes to consider
        
    Returns:
        Share of top-k nodes
    """
    if not scores:
        return 0.0
    
    total_score = sum(scores.values())
    if total_score == 0:
        return 0.0
    
    # Get top-k nodes
    sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    topk_score = sum(score for _, score in sorted_nodes[:k])
    
    return topk_score / total_score


def calculate_assortativity(G: nx.Graph, attribute: str) -> float:
    """
    Calculate assortativity coefficient for a node attribute.
    
    Args:
        G: NetworkX graph
        attribute: Node attribute name
        
    Returns:
        Assortativity coefficient
    """
    if G.number_of_nodes() < 2:
        return np.nan
    
    try:
        # Get attribute values
        attrs = nx.get_node_attributes(G, attribute)
        
        if len(attrs) < 2:
            return np.nan
        
        # Calculate assortativity
        return nx.attribute_assortativity_coefficient(G, attribute)
    except (KeyError, nx.NetworkXError):
        return np.nan


def calculate_avg_path_length(G: nx.Graph) -> float:
    """
    Calculate average shortest path length.
    
    Args:
        G: NetworkX graph
        
    Returns:
        Average shortest path length
    """
    if G.number_of_nodes() < 2:
        return np.nan
    
    try:
        if nx.is_connected(G):
            return nx.average_shortest_path_length(G)
        else:
            # For disconnected graphs, calculate for each component
            components = list(nx.connected_components(G))
            if len(components) == 1:
                return nx.average_shortest_path_length(G)
            else:
                # Weighted average by component size
                total_length = 0
                total_pairs = 0
                
                for component in components:
                    if len(component) > 1:
                        subgraph = G.subgraph(component)
                        comp_length = nx.average_shortest_path_length(subgraph)
                        comp_pairs = len(component) * (len(component) - 1)
                        total_length += comp_length * comp_pairs
                        total_pairs += comp_pairs
                
                return total_length / total_pairs if total_pairs > 0 else np.nan
    except nx.NetworkXError:
        return np.nan


def calculate_all_metrics(
    interactions_df: pd.DataFrame,
    t_start: pd.Timestamp,
    t_end: pd.Timestamp,
    victim_id: Optional[str] = None,
    leader_id: Optional[str] = None,
    node_labels: Optional[Dict[str, Dict[str, Any]]] = None,
    prev_communities: Optional[Dict[str, int]] = None,
    ego_density_threshold: float = 0.05,
    topk_values: List[int] = [5, 10],
    approx_betweenness_k: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate all metrics for a time window.
    
    Args:
        interactions_df: DataFrame with interactions in the window
        t_start: Window start time
        t_end: Window end time
        victim_id: ID of victim node
        leader_id: ID of leader node
        node_labels: Dictionary with node labels
        prev_communities: Previous window communities for NMI calculation
        ego_density_threshold: Threshold for ego density
        topk_values: List of k values for top-k share calculation
        approx_betweenness_k: Number of nodes to sample for betweenness approximation
        
    Returns:
        Dictionary with all calculated metrics
    """
    metrics = {
        't_start': t_start,
        't_end': t_end,
        'n_nodes': 0,
        'n_edges': 0,
        'density': 0.0
    }
    
    if len(interactions_df) == 0:
        return metrics
    
    # Build directed graph
    G_directed = build_graph(interactions_df, directed=True)
    G_undirected = build_undirected_projection(G_directed)
    
    # Basic graph metadata
    graph_metadata = get_graph_metadata(G_directed)
    metrics.update(graph_metadata)
    
    if G_directed.number_of_nodes() == 0:
        return metrics
    
    # 4.1 Burst metrics (peak_mean, peak_median)
    edge_counts = len(interactions_df)
    metrics['peak_mean'] = edge_counts
    metrics['peak_median'] = edge_counts  # For single window, mean = median
    
    # 4.2 Reorganization pro-leader metrics
    # PageRank
    pr_scores = calculate_pagerank(G_directed)
    metrics['pagerank_scores'] = pr_scores
    
    # Top-K PageRank share
    for k in topk_values:
        metrics[f'topk_pr_share_k{k}'] = calculate_topk_share(pr_scores, k)
    
    # Leader metrics
    if leader_id and leader_id in G_directed.nodes():
        leader_pr = pr_scores.get(leader_id, 0.0)
        metrics['leader_pagerank'] = leader_pr
        
        # Rank of leader
        sorted_pr = sorted(pr_scores.items(), key=lambda x: x[1], reverse=True)
        leader_rank = next(i for i, (node, _) in enumerate(sorted_pr) if node == leader_id) + 1
        metrics['leader_rank'] = leader_rank
    else:
        # Infer leader as top-1 PageRank
        if pr_scores:
            top_leader = max(pr_scores.items(), key=lambda x: x[1])
            metrics['inferred_leader'] = top_leader[0]
            metrics['inferred_leader_pr'] = top_leader[1]
    
    # Betweenness centralization
    metrics['betweenness_centralization'] = calculate_betweenness_centralization(G_directed)
    
    # 4.3 Community change metrics
    # This will be handled by community detection module
    metrics['communities'] = None  # Placeholder
    
    # 4.4 Victim isolation metrics
    if victim_id and victim_id in G_directed.nodes():
        # Reciprocity
        metrics['victim_reciprocity'] = calculate_reciprocity(G_directed, victim_id)
        
        # SCC size
        metrics['victim_scc_size'] = get_strongly_connected_component_size(G_directed, victim_id)
        
        # Ego density
        ego_density = calculate_ego_density(G_undirected, victim_id)
        metrics['victim_ego_density'] = ego_density
        
        # Time to isolation (will be calculated across windows)
        is_isolated = (
            metrics['victim_reciprocity'] == 0 and 
            metrics['victim_scc_size'] == 1 and 
            ego_density <= ego_density_threshold
        )
        metrics['victim_is_isolated'] = is_isolated
    else:
        metrics['victim_reciprocity'] = 0
        metrics['victim_scc_size'] = 0
        metrics['victim_ego_density'] = 0.0
        metrics['victim_is_isolated'] = False
    
    # 4.5 Skeptics effect metrics
    if node_labels and any('skeptic' in labels for labels in node_labels.values()):
        # Add skeptic labels to graph
        for node, labels in node_labels.items():
            if 'skeptic' in labels and labels['skeptic'] is not None:
                G_undirected.nodes[node]['skeptic'] = labels['skeptic']
        
        # Assortativity by skeptic label
        metrics['assort_skeptic'] = calculate_assortativity(G_undirected, 'skeptic')
        
        # Betweenness share of skeptics
        bc_scores = calculate_betweenness_centrality(G_undirected, k=approx_betweenness_k)
        skeptic_bc = sum(
            bc_scores.get(node, 0) for node, labels in node_labels.items()
            if labels.get('skeptic', 0) == 1
        )
        total_bc = sum(bc_scores.values())
        metrics['betweenness_share_skeptic'] = skeptic_bc / total_bc if total_bc > 0 else 0.0
    else:
        metrics['assort_skeptic'] = np.nan
        metrics['betweenness_share_skeptic'] = 0.0
    
    # Victim in-degree share
    if victim_id and victim_id in G_directed.nodes():
        victim_in_degree = G_directed.in_degree(victim_id)
        total_in_degree = sum(G_directed.in_degree(node) for node in G_directed.nodes())
        metrics['victim_inshare'] = victim_in_degree / total_in_degree if total_in_degree > 0 else 0.0
    else:
        metrics['victim_inshare'] = 0.0
    
    # 4.6 Friendly effect metrics
    # Graph density (already calculated)
    metrics['graph_density'] = metrics['density']
    
    # Average path length
    metrics['avg_path_len'] = calculate_avg_path_length(G_undirected)
    
    # Effective diameter
    metrics['eff_diameter'] = calculate_effective_diameter(G_undirected)
    
    # 4.7 Symbolic emergence metrics (post-ritual)
    if victim_id and victim_id in G_undirected.nodes():
        # Median distance to victim
        median_dist = calculate_median_distance_to_node(G_undirected, victim_id)
        metrics['median_distance_to_victim'] = median_dist
    else:
        metrics['median_distance_to_victim'] = np.nan
    
    # Half-life of victim in-degree share (will be calculated across windows)
    metrics['victim_inshare_half_life'] = np.nan  # Placeholder
    
    return metrics


def calculate_nmi_between_communities(
    communities1: Dict[str, int],
    communities2: Dict[str, int]
) -> float:
    """
    Calculate NMI between two community partitions.
    
    Args:
        communities1: First community partition
        communities2: Second community partition
        
    Returns:
        NMI score
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


def detect_onset_climax(
    metrics_series: pd.DataFrame,
    peak_mean_threshold: float = 3.0,
    peak_median_threshold: float = 5.0
) -> Tuple[Optional[int], Optional[int]]:
    """
    Detect onset and climax in a series of metrics.
    
    Args:
        metrics_series: DataFrame with metrics over time
        peak_mean_threshold: Threshold for onset detection (peak_mean)
        peak_median_threshold: Threshold for onset detection (peak_median)
        
    Returns:
        Tuple of (onset_window, climax_window) indices
    """
    if len(metrics_series) == 0:
        return None, None
    
    # Detect onset
    onset_mask = (
        (metrics_series['peak_mean'] >= peak_mean_threshold) |
        (metrics_series['peak_median'] >= peak_median_threshold)
    )
    
    onset_windows = metrics_series[onset_mask].index.tolist()
    onset_window = onset_windows[0] if onset_windows else None
    
    # Detect climax (first global maximum after onset)
    if onset_window is not None:
        post_onset = metrics_series.loc[onset_window:]
        if len(post_onset) > 0:
            climax_idx = post_onset['peak_mean'].idxmax()
            climax_window = metrics_series.index.get_loc(climax_idx)
        else:
            climax_window = None
    else:
        climax_window = None
    
    return onset_window, climax_window


def calculate_time_to_isolation(
    metrics_series: pd.DataFrame,
    ego_density_threshold: float = 0.05,
    min_windows: int = 1
) -> Optional[int]:
    """
    Calculate time to isolation for victim.
    
    Args:
        metrics_series: DataFrame with metrics over time
        ego_density_threshold: Threshold for ego density
        min_windows: Minimum number of windows for isolation
        
    Returns:
        Number of windows to isolation (None if not isolated)
    """
    if len(metrics_series) == 0:
        return None
    
    # Find first window where victim is isolated
    isolation_mask = (
        (metrics_series['victim_reciprocity'] == 0) &
        (metrics_series['victim_scc_size'] == 1) &
        (metrics_series['victim_ego_density'] <= ego_density_threshold)
    )
    
    isolated_windows = metrics_series[isolation_mask].index.tolist()
    
    if len(isolated_windows) >= min_windows:
        return isolated_windows[0]
    else:
        return None


def calculate_half_life(
    values: pd.Series,
    peak_idx: int,
    baseline: Optional[float] = None
) -> Optional[int]:
    """
    Calculate half-life of a metric after a peak.
    
    Args:
        values: Series of values
        peak_idx: Index of peak
        baseline: Baseline value (if None, use first value)
        
    Returns:
        Number of steps to reach half-life (None if not reached)
    """
    if peak_idx >= len(values) - 1:
        return None
    
    peak_value = values.iloc[peak_idx]
    if baseline is None:
        baseline = values.iloc[0]
    
    half_value = baseline + (peak_value - baseline) / 2
    
    # Look for first value below half
    for i in range(peak_idx + 1, len(values)):
        if values.iloc[i] <= half_value:
            return i - peak_idx
    
    return None

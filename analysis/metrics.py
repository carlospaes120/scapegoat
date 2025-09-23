import argparse
import os
import pandas as pd
import networkx as nx
import numpy as np

def compute_graph_metrics(G):
    """Compute various graph metrics"""
    metrics = {}
    
    # Basic metrics
    metrics['n_nodes'] = G.number_of_nodes()
    metrics['n_edges'] = G.number_of_edges()
    metrics['density'] = nx.density(G)
    
    # Convert to undirected for some metrics
    G_undirected = G.to_undirected()
    
    # Connected components
    if G.is_directed():
        metrics['n_weak_components'] = nx.number_weakly_connected_components(G)
        metrics['n_strong_components'] = nx.number_strongly_connected_components(G)
        
        # Largest weakly connected component
        largest_wcc = max(nx.weakly_connected_components(G), key=len)
        G_largest_wcc = G.subgraph(largest_wcc)
    else:
        metrics['n_components'] = nx.number_connected_components(G_undirected)
        
        # Largest connected component
        largest_cc = max(nx.connected_components(G_undirected), key=len)
        G_largest_cc = G_undirected.subgraph(largest_cc)
        G_largest_wcc = G_largest_cc
    
    # Metrics on largest component
    if G_largest_wcc.number_of_nodes() > 1:
        try:
            metrics['diameter'] = nx.diameter(G_largest_wcc)
        except nx.NetworkXError:
            metrics['diameter'] = None
        
        try:
            metrics['avg_path_length'] = nx.average_shortest_path_length(G_largest_wcc)
        except nx.NetworkXError:
            metrics['avg_path_length'] = None
    else:
        metrics['diameter'] = None
        metrics['avg_path_length'] = None
    
    # Clustering coefficient
    try:
        metrics['avg_clustering'] = nx.average_clustering(G_undirected)
    except:
        metrics['avg_clustering'] = None
    
    # Average degree
    degrees = [d for n, d in G.degree()]
    metrics['avg_degree'] = np.mean(degrees) if degrees else 0
    
    # Modularity (if possible)
    try:
        communities = list(nx.algorithms.community.greedy_modularity_communities(G_undirected))
        metrics['modularity'] = nx.algorithms.community.quality.modularity(G_undirected, communities)
        metrics['n_communities'] = len(communities)
    except:
        metrics['modularity'] = None
        metrics['n_communities'] = None
    
    # PageRank (top 10)
    try:
        pagerank = nx.pagerank(G)
        top_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]
        metrics['top_10_pagerank'] = top_pagerank
    except:
        metrics['top_10_pagerank'] = None
    
    # Betweenness centrality (top 10)
    try:
        betweenness = nx.betweenness_centrality(G_undirected)
        top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]
        metrics['top_10_betweenness'] = top_betweenness
    except:
        metrics['top_10_betweenness'] = None
    
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Compute graph metrics")
    parser.add_argument("--gexf", required=True, help="Input GEXF file")
    parser.add_argument("--out", required=True, help="Output CSV file")
    
    args = parser.parse_args()
    
    # Read graph
    print(f"Reading graph from: {args.gexf}")
    G = nx.read_gexf(args.gexf)
    print(f"Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Compute metrics
    print("Computing metrics...")
    metrics = compute_graph_metrics(G)
    
    # Create output directory
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    
    # Prepare data for CSV
    csv_data = []
    
    # Basic metrics
    csv_data.append({'metric': 'n_nodes', 'value': metrics['n_nodes']})
    csv_data.append({'metric': 'n_edges', 'value': metrics['n_edges']})
    csv_data.append({'metric': 'density', 'value': metrics['density']})
    
    # Component metrics
    if 'n_weak_components' in metrics:
        csv_data.append({'metric': 'n_weak_components', 'value': metrics['n_weak_components']})
        csv_data.append({'metric': 'n_strong_components', 'value': metrics['n_strong_components']})
    else:
        csv_data.append({'metric': 'n_components', 'value': metrics['n_components']})
    
    # Path metrics
    csv_data.append({'metric': 'diameter', 'value': metrics['diameter']})
    csv_data.append({'metric': 'avg_path_length', 'value': metrics['avg_path_length']})
    
    # Clustering and degree
    csv_data.append({'metric': 'avg_clustering', 'value': metrics['avg_clustering']})
    csv_data.append({'metric': 'avg_degree', 'value': metrics['avg_degree']})
    
    # Modularity
    csv_data.append({'metric': 'modularity', 'value': metrics['modularity']})
    csv_data.append({'metric': 'n_communities', 'value': metrics['n_communities']})
    
    # Top PageRank
    if metrics['top_10_pagerank']:
        for i, (node, score) in enumerate(metrics['top_10_pagerank']):
            csv_data.append({'metric': f'top_pagerank_{i+1}', 'value': f'{node}:{score:.6f}'})
    
    # Top Betweenness
    if metrics['top_10_betweenness']:
        for i, (node, score) in enumerate(metrics['top_10_betweenness']):
            csv_data.append({'metric': f'top_betweenness_{i+1}', 'value': f'{node}:{score:.6f}'})
    
    # Save to CSV
    df = pd.DataFrame(csv_data)
    df.to_csv(args.out, index=False)
    print(f"Saved metrics to: {args.out}")
    
    # Print summary
    print(f"\nGraph Metrics Summary:")
    print(f"Nodes: {metrics['n_nodes']}")
    print(f"Edges: {metrics['n_edges']}")
    print(f"Density: {metrics['density']:.6f}")
    print(f"Average degree: {metrics['avg_degree']:.2f}")
    print(f"Average clustering: {metrics['avg_clustering']:.6f}" if metrics['avg_clustering'] else "Average clustering: N/A")
    print(f"Modularity: {metrics['modularity']:.6f}" if metrics['modularity'] else "Modularity: N/A")
    print(f"Average path length: {metrics['avg_path_length']:.2f}" if metrics['avg_path_length'] else "Average path length: N/A")
    print(f"Diameter: {metrics['diameter']}" if metrics['diameter'] else "Diameter: N/A")

if __name__ == "__main__":
    main()


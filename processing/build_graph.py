import argparse
import os
import json
import pandas as pd
import networkx as nx
from datetime import datetime

def build_edges_from_events(events_df):
    """Build edges from events DataFrame"""
    edges = []
    
    for _, row in events_df.iterrows():
        user_id = row['user_id']
        if pd.isna(user_id):
            continue
            
        # Reply edges: user_id -> author of replied tweet
        if pd.notna(row['reply_to']):
            edges.append({
                'source': user_id,
                'target': row['reply_to'],
                'weight': 1,
                'type': 'reply'
            })
        
        # Retweet edges: user_id -> author of original tweet
        if pd.notna(row['retweet_of']):
            edges.append({
                'source': user_id,
                'target': row['retweet_of'],
                'weight': 1,
                'type': 'retweet'
            })
        
        # Mention edges: user_id -> mentioned user
        if pd.notna(row['mentions_json']):
            try:
                mentions = json.loads(row['mentions_json'])
                for mention_id in mentions:
                    if mention_id and mention_id != user_id:  # Don't self-mention
                        edges.append({
                            'source': user_id,
                            'target': mention_id,
                            'weight': 1,
                            'type': 'mention'
                        })
            except (json.JSONDecodeError, TypeError):
                pass
    
    return pd.DataFrame(edges)

def aggregate_edges(edges_df):
    """Aggregate edges by source, target, and type"""
    if edges_df.empty:
        return edges_df
    
    # Group by source, target, and type, sum weights
    aggregated = edges_df.groupby(['source', 'target', 'type'], as_index=False)['weight'].sum()
    
    return aggregated

def build_networkx_graph(edges_df):
    """Build NetworkX directed graph from edges DataFrame"""
    G = nx.DiGraph()
    
    for _, row in edges_df.iterrows():
        G.add_edge(
            row['source'],
            row['target'],
            weight=row['weight'],
            type=row['type']
        )
    
    return G

def main():
    parser = argparse.ArgumentParser(description="Build graph from events.csv")
    parser.add_argument("--events", required=True, help="Events CSV file")
    parser.add_argument("--edges", required=True, help="Output edges CSV file")
    parser.add_argument("--gexf", required=True, help="Output GEXF file")
    parser.add_argument("--directed", action="store_true", help="Create directed graph (default: True)")
    
    args = parser.parse_args()
    
    # Read events
    print(f"Reading events from: {args.events}")
    events_df = pd.read_csv(args.events)
    print(f"Loaded {len(events_df)} events")
    
    # Build edges
    print("Building edges...")
    edges_df = build_edges_from_events(events_df)
    print(f"Created {len(edges_df)} edges")
    
    if edges_df.empty:
        print("No edges found!")
        return
    
    # Aggregate edges
    print("Aggregating edges...")
    aggregated_edges = aggregate_edges(edges_df)
    print(f"Aggregated to {len(aggregated_edges)} unique edges")
    
    # Create output directory
    os.makedirs(os.path.dirname(args.edges), exist_ok=True)
    os.makedirs(os.path.dirname(args.gexf), exist_ok=True)
    
    # Save edges CSV
    aggregated_edges.to_csv(args.edges, index=False)
    print(f"Saved edges to: {args.edges}")
    
    # Build NetworkX graph
    print("Building NetworkX graph...")
    G = build_networkx_graph(aggregated_edges)
    
    # Add node attributes
    for node in G.nodes():
        G.nodes[node]['id'] = node
        G.nodes[node]['label'] = str(node)
    
    # Save GEXF
    nx.write_gexf(G, args.gexf)
    print(f"Saved graph to: {args.gexf}")
    
    # Print summary
    print(f"\nGraph Summary:")
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Directed: {G.is_directed()}")
    
    # Show edge type distribution
    edge_types = aggregated_edges['type'].value_counts()
    print(f"\nEdge types:")
    for edge_type, count in edge_types.items():
        print(f"  {edge_type}: {count}")

if __name__ == "__main__":
    main()


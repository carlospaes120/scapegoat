import pandas as pd
import networkx as nx
import json
import uuid

def create_hybrid_graph(jsonl_filepath):
    """
    Creates a hybrid network graph from a JSONL file of tweets.
    The graph includes both user nodes and tweet nodes.

    Args:
        jsonl_filepath (str): The path to the input JSONL file.

    Returns:
        networkx.DiGraph: The generated hybrid directed graph.
    """
    # Use pandas to easily read the JSONL file into a DataFrame
    try:
        df = pd.read_json(jsonl_filepath, lines=True)
    except FileNotFoundError:
        print(f"Error: The file '{jsonl_filepath}' was not found.")
        return None

    # Initialize a directed graph.
    # Directed graphs are crucial here to show the direction of influence (A replies to B).
    G = nx.DiGraph()

    # Create a mapping for tweet IDs to unique node IDs to avoid duplicates if a tweet appears multiple times.
    tweet_id_map = {}

    for _, row in df.iterrows():
        # User nodes are identified by their username
        user = row.get('user')
        if not user or not isinstance(user, str):
            continue
        
        # Tweet nodes are identified by a unique ID, combining original tweet ID with a new UUID for safety
        tweet_id = row.get('id')
        if not tweet_id:
            continue
        
        # Add the tweet as a node, and link it to the author (user).
        # We'll use a unique identifier for the tweet node to avoid collisions.
        tweet_node_id = f"tweet_{tweet_id}"
        tweet_id_map[tweet_id] = tweet_node_id
        
        # Add nodes with attributes to distinguish between users and tweets
        G.add_node(user, type='user')
        G.add_node(tweet_node_id, type='tweet', tweet_id=tweet_id, text=row['text'])
        
        # Create an edge from the user to their tweet
        G.add_edge(user, tweet_node_id, relationship='authored')

        # --- Create Edges based on user's analysis ---

        # 1. Reply networks (Confrontations or pile-ons)
        in_reply_to_user = row.get('in_reply_to_user')
        in_reply_to_status_id = row.get('in_reply_to_status_id')
        if in_reply_to_user and isinstance(in_reply_to_user, str):
            # Add an edge from the replying user to the replied-to user
            G.add_node(in_reply_to_user, type='user')
            G.add_edge(user, in_reply_to_user, relationship='replied_to', tweet_id=tweet_id)
            
            # If the original tweet is in our dataset, add a tweet-to-tweet edge
            if in_reply_to_status_id in tweet_id_map:
                replied_to_tweet_node = tweet_id_map[in_reply_to_status_id]
                G.add_edge(tweet_node_id, replied_to_tweet_node, relationship='replied_to')

        # 2. Retweet networks (Amplification)
        is_retweet = row.get('is_retweet')
        retweeted_status_user = row.get('retweeted_status', {}).get('user', {}).get('screen_name')
        if is_retweet and retweeted_status_user and isinstance(retweeted_status_user, str):
            # Add an edge from the retweeting user to the original user
            G.add_node(retweeted_status_user, type='user')
            G.add_edge(user, retweeted_status_user, relationship='retweeted')
            
            # Add an edge from the retweeting tweet to the original tweet
            retweeted_status_id = row.get('retweeted_status', {}).get('id')
            if retweeted_status_id in tweet_id_map:
                 G.add_edge(tweet_node_id, tweet_id_map[retweeted_status_id], relationship='retweeted')

        # 3. Mention networks (Direct scapegoating)
        mentions = row.get('mentions', [])
        for mention in mentions:
            if not isinstance(mention, str):
                continue
            # Add an edge from the mentioning user to the mentioned user
            G.add_node(mention, type='user')
            G.add_edge(user, mention, relationship='mentioned')
            
            # Add an edge from the mentioning tweet to the mentioned user
            G.add_edge(tweet_node_id, mention, relationship='mentioned_user')
            
    return G

if __name__ == "__main__":
    filepath = "../../data/raw/tweets_cleaned_monark_1.jsonl"
    
    print("Creating hybrid network graph...")
    graph = create_hybrid_graph(filepath)

    if graph:
        print("\nGraph created successfully!")
        print(f"Number of nodes: {graph.number_of_nodes()}")
        print(f"Number of edges: {graph.number_of_edges()}")

        # You can now save the graph in a format that can be opened by visualization tools like Gephi.
        # Gephi is great for interactive exploration and can handle large networks.
        # Download it from https://gephi.org/
        output_filepath = 'monark_graph.gexf'
        try:
            nx.write_gexf(graph, output_filepath)
            print(f"Graph saved to '{output_filepath}'.")
            print("Open this file with Gephi to visualize and analyze the network.")
        except Exception as e:
            print(f"Error saving graph to GEXF: {e}")
            print("You can still use NetworkX for analysis directly in Python.")

        # Example of basic analysis: find the users with the highest number of direct interactions
        print("\n--- Top 10 Most Interacted-With Nodes (by degree centrality) ---")
        centrality = nx.degree_centrality(graph)
        sorted_centrality = sorted(centrality.items(), key=lambda item: item[1], reverse=True)
        for node, score in sorted_centrality[:10]:
            print(f"Node: '{node}' | Score: {score:.4f}")
            
        print("\n--- Example of Finding Scapegoats (High In-Degree, Low Out-Degree) ---")
        # Find user nodes with a high in-degree and low out-degree, a key indicator of a scapegoat.
        # This shows who is being talked about or attacked, without them necessarily engaging back.
        user_nodes = [n for n, d in graph.nodes(data=True) if d['type'] == 'user']
        in_degrees = {n: graph.in_degree(n) for n in user_nodes}
        out_degrees = {n: graph.out_degree(n) for n in user_nodes}

        # Let's find nodes with a high ratio of in-degree to out-degree
        for node in sorted(in_degrees, key=in_degrees.get, reverse=True)[:10]:
            if out_degrees.get(node, 0) > 0:
                ratio = in_degrees[node] / out_degrees[node]
                print(f"User: '{node}' | In-Degree: {in_degrees[node]} | Out-Degree: {out_degrees[node]} | In/Out Ratio: {ratio:.2f}")

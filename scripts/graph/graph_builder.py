import json
import networkx as nx

def build_twitter_graph(file_path):
    """
    Builds a directed graph from a Twitter JSON Lines (JSONL) file.

    The graph contains the following:
    - Nodes: Twitter users and hashtags.
    - Edges: Represents interactions like mentions and hashtag usage.

    Args:
        file_path (str): The path to the JSONL file.

    Returns:
        nx.DiGraph: The constructed directed graph.
    """
    # Use a directed graph (DiGraph) because mentions and retweets are one-way interactions.
    G = nx.DiGraph()

    # A set to keep track of added nodes to prevent duplicate attributes.
    added_nodes = set()

    print(f"Reading from file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                tweet = json.loads(line)
                
                # The user who wrote the tweet.
                source_user = tweet.get('user')
                
                if not source_user:
                    continue

                # Add the source user as a node if they don't exist yet.
                if source_user not in added_nodes:
                    G.add_node(source_user, type='user')
                    added_nodes.add(source_user)

                # Process mentions
                mentions = tweet.get('mentions', [])
                for mention in mentions:
                    target_user = mention.get('username')
                    if target_user:
                        # Add the mentioned user as a node if they don't exist yet.
                        if target_user not in added_nodes:
                            G.add_node(target_user, type='user')
                            added_nodes.add(target_user)
                        
                        # Add a directed edge from the source user to the mentioned user.
                        G.add_edge(source_user, target_user, type='mention')
                
                # Process hashtags
                hashtags = tweet.get('hashtags', [])
                for hashtag in hashtags:
                    # Clean up the hashtag to ensure consistency.
                    clean_hashtag = hashtag.strip().lower().replace('#', '')
                    if clean_hashtag:
                        # Add the hashtag as a node if it doesn't exist yet.
                        if clean_hashtag not in added_nodes:
                            G.add_node(clean_hashtag, type='hashtag')
                            added_nodes.add(clean_hashtag)

                        # Add a directed edge from the user to the hashtag.
                        G.add_edge(source_user, clean_hashtag, type='uses_hashtag')

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e} in line: {line.strip()}")
                continue
    
    return G

if __name__ == "__main__":
    file_name = "../../data/interim/tweets_cleaned_default.jsonl"
    graph = build_twitter_graph(file_name)

    # Print some summary statistics about the graph.
    print("\n--- Graph Statistics ---")
    print(f"Number of nodes: {graph.number_of_nodes()}")
    print(f"Number of edges: {graph.number_of_edges()}")

    # Count node types
    user_nodes = [node for node, data in graph.nodes(data=True) if data.get('type') == 'user']
    hashtag_nodes = [node for node, data in graph.nodes(data=True) if data.get('type') == 'hashtag']
    print(f"Number of user nodes: {len(user_nodes)}")
    print(f"Number of hashtag nodes: {len(hashtag_nodes)}")
    
    # Save the graph to a file for external visualization.
    # The GEXF format is excellent for tools like Gephi.
    output_file = "twitter_graph.gexf"
    try:
        nx.write_gexf(graph, output_file)
        print(f"\nGraph successfully saved to {output_file}")
        print("You can now open this file with a graph visualization tool like Gephi.")
    except Exception as e:
        print(f"Error saving graph file: {e}")

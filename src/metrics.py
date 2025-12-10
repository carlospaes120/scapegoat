import os
import pandas as pd
import networkx as nx

RAW = "data/raw/edges.csv"
OUT = "exports/metrics.csv"
os.makedirs("exports", exist_ok=True)

if not os.path.exists(RAW):
    raise FileNotFoundError(f"Não encontrei {RAW}. Coloque seu edges.csv em data/raw/")

df = pd.read_csv(RAW)

# sanity
needed = {"source", "target"}
if not needed.issubset(df.columns.str.lower()):
    # tentar normalizar nomes
    cols = {c.lower(): c for c in df.columns}
    df = df.rename(columns={cols.get("source","source"): "source",
                            cols.get("target","target"): "target"})

if "weight" not in df.columns:
    df["weight"] = 1.0

# grafos
Gd = nx.DiGraph()
Gu = nx.Graph()

# adiciona arestas
for _, r in df.iterrows():
    u, v, w = r["source"], r["target"], float(r["weight"])
    Gd.add_edge(u, v, weight=w)
    Gu.add_edge(u, v, weight=w)

def safe_avg_path_length(G):
    try:
        if nx.is_connected(G):
            return nx.average_shortest_path_length(G)
        else:
            # pega maior componente
            cc = max(nx.connected_components(G), key=len)
            return nx.average_shortest_path_length(G.subgraph(cc))
    except Exception:
        return float("nan")

metrics = {
    "nodes_directed": Gd.number_of_nodes(),
    "edges_directed": Gd.number_of_edges(),
    "density_directed": nx.density(Gd),

    "nodes_undirected": Gu.number_of_nodes(),
    "edges_undirected": Gu.number_of_edges(),
    "density_undirected": nx.density(Gu),

    "avg_degree_undirected": sum(dict(Gu.degree()).values())/max(1,Gu.number_of_nodes()),
    "avg_clustering_undirected": nx.average_clustering(Gu) if Gu.number_of_nodes()>0 else float("nan"),
    "avg_path_length_undirected": safe_avg_path_length(Gu),
}

pd.DataFrame([metrics]).to_csv(OUT, index=False)
print(f"OK: métricas salvas em {OUT}")





#!/usr/bin/env python3
"""
make_gexf.py

Converts NetLogo CSV exports (nodes.csv + links_snapshot.csv) to GEXF and GraphML formats
for import into Gephi and other network analysis tools.

Usage:
    python tools/make_gexf.py
"""

import pandas as pd
import networkx as nx
from pathlib import Path
import sys

# Paths relative to project root
DATA = Path(__file__).resolve().parents[1] / "data"
nodes_csv = DATA / "nodes.csv"
links_csv = DATA / "links_snapshot.csv"
gexf_out = DATA / "network.gexf"
graphml_out = DATA / "network.graphml"


def main():
    """Load CSV data and export to GEXF and GraphML formats."""
    
    # Check if input files exist
    if not nodes_csv.exists():
        print(f"❌ Erro: {nodes_csv} não encontrado.")
        print("   Execute 'Export nodes snapshot' no NetLogo primeiro.")
        sys.exit(1)
    
    if not links_csv.exists():
        print(f"❌ Erro: {links_csv} não encontrado.")
        print("   Execute 'Export links snapshot' no NetLogo primeiro.")
        sys.exit(1)
    
    print(f"📂 Lendo {nodes_csv}...")
    nodes = pd.read_csv(nodes_csv)
    print(f"   {len(nodes)} nós carregados")
    
    print(f"📂 Lendo {links_csv}...")
    edges = pd.read_csv(links_csv)
    print(f"   {len(edges)} arestas carregadas")
    
    # Create NetworkX graph
    print("🔨 Construindo grafo NetworkX...")
    G = nx.Graph()
    
    # Add nodes with attributes
    for _, row in nodes.iterrows():
        node_id = int(row["id"])
        G.add_node(node_id, **{
            "kind": str(row.get("kind", "")),
            "health": float(row.get("health", 0.0)),
            "tension": float(row.get("tension", 0.0)),
            "cc_node": float(row.get("cc_node", 0.0)),
            "degree": int(row.get("degree", 0)),
        })
    
    # Add edges
    for _, row in edges.iterrows():
        src = int(row["source"])
        tgt = int(row["target"])
        if src in G and tgt in G:
            G.add_edge(src, tgt)
    
    print(f"   Grafo: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
    
    # Export GEXF
    print(f"💾 Salvando {gexf_out}...")
    gexf_out.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(G, gexf_out)
    
    # Export GraphML
    print(f"💾 Salvando {graphml_out}...")
    nx.write_graphml(G, graphml_out)
    
    print("\n✅ Exportação concluída!")
    print(f"   GEXF:    {gexf_out}")
    print(f"   GraphML: {graphml_out}")
    print("\n💡 Importe qualquer um dos arquivos no Gephi para visualização.")


if __name__ == "__main__":
    main()



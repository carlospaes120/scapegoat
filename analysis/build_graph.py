#!/usr/bin/env python3
"""
Construção de grafos de rede a partir de dados normalizados de tweets.
"""

import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

def build_mention_graph(df: pd.DataFrame, min_mentions: int = 1) -> nx.DiGraph:
    """Constrói grafo de menções a partir dos dados normalizados."""
    logger.info("Construindo grafo de menções...")
    
    G = nx.DiGraph()
    
    # Adicionar nós (autores)
    authors = df['author'].dropna().unique()
    for author in authors:
        if author and author != '':
            G.add_node(author)
    
    # Adicionar arestas (menções)
    mention_edges = {}
    
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Processando menções"):
        author = row['author']
        mentions = row['mentions']
        
        if not author or not mentions:
            continue
        
        for mention in mentions:
            if mention and mention != author:
                edge_key = (author, mention)
                if edge_key in mention_edges:
                    mention_edges[edge_key] += 1
                else:
                    mention_edges[edge_key] = 1
    
    # Adicionar arestas ao grafo
    for (source, target), weight in mention_edges.items():
        if weight >= min_mentions:
            G.add_edge(source, target, weight=weight, type='mention')
    
    logger.info(f"Grafo construído: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
    return G

def build_retweet_graph(df: pd.DataFrame) -> nx.DiGraph:
    """Constrói grafo de retweets."""
    logger.info("Construindo grafo de retweets...")
    
    G = nx.DiGraph()
    
    # Adicionar nós
    authors = df['author'].dropna().unique()
    for author in authors:
        if author and author != '':
            G.add_node(author)
    
    # Adicionar arestas de retweet
    rt_edges = {}
    
    for _, row in df.iterrows():
        if row['is_retweet'] and row['retweet_of']:
            author = row['author']
            # Assumir que retweet_of é o autor original (simplificação)
            # Em um caso real, precisaríamos mapear tweet_id para author
            if author and author != '':
                rt_edges[(author, row['retweet_of'])] = rt_edges.get((author, row['retweet_of']), 0) + 1
    
    for (source, target), weight in rt_edges.items():
        G.add_edge(source, target, weight=weight, type='retweet')
    
    logger.info(f"Grafo de RT construído: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
    return G

def build_reply_graph(df: pd.DataFrame) -> nx.DiGraph:
    """Constrói grafo de replies."""
    logger.info("Construindo grafo de replies...")
    
    G = nx.DiGraph()
    
    # Adicionar nós
    authors = df['author'].dropna().unique()
    for author in authors:
        if author and author != '':
            G.add_node(author)
    
    # Adicionar arestas de reply
    reply_edges = {}
    
    for _, row in df.iterrows():
        if row['is_reply'] and row['in_reply_to']:
            author = row['author']
            if author and author != '':
                reply_edges[(author, row['in_reply_to'])] = reply_edges.get((author, row['in_reply_to']), 0) + 1
    
    for (source, target), weight in reply_edges.items():
        G.add_edge(source, target, weight=weight, type='reply')
    
    logger.info(f"Grafo de replies construído: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
    return G

def combine_graphs(mention_G: nx.DiGraph, rt_G: nx.DiGraph, reply_G: nx.DiGraph) -> nx.DiGraph:
    """Combina múltiplos grafos em um grafo unificado."""
    logger.info("Combinando grafos...")
    
    # Começar com o grafo de menções
    combined_G = mention_G.copy()
    
    # Adicionar arestas de retweet
    for source, target, data in rt_G.edges(data=True):
        if combined_G.has_edge(source, target):
            # Combinar pesos
            combined_G[source][target]['weight'] += data.get('weight', 1)
            combined_G[source][target]['type'] = 'mixed'
        else:
            combined_G.add_edge(source, target, **data)
    
    # Adicionar arestas de reply
    for source, target, data in reply_G.edges(data=True):
        if combined_G.has_edge(source, target):
            # Combinar pesos
            combined_G[source][target]['weight'] += data.get('weight', 1)
            combined_G[source][target]['type'] = 'mixed'
        else:
            combined_G.add_edge(source, target, **data)
    
    logger.info(f"Grafo combinado: {combined_G.number_of_nodes()} nós, {combined_G.number_of_edges()} arestas")
    return combined_G

def calculate_basic_metrics(G: nx.DiGraph) -> Dict[str, float]:
    """Calcula métricas básicas do grafo."""
    if G.number_of_nodes() == 0:
        return {
            'n_nodes': 0,
            'n_edges': 0,
            'density': 0.0
        }
    
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G)
    
    return {
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'density': density
    }

def calculate_centralization_metrics(G: nx.DiGraph) -> Dict[str, float]:
    """Calcula métricas de centralização."""
    if G.number_of_nodes() < 3:
        return {
            'in_degree_centralization': np.nan,
            'out_degree_centralization': np.nan,
            'betweenness_centralization': np.nan
        }
    
    # In-degree centralization (Freeman)
    in_degrees = dict(G.in_degree())
    max_in_degree = max(in_degrees.values()) if in_degrees else 0
    n = G.number_of_nodes()
    
    if n <= 1:
        in_degree_centralization = 0.0
    else:
        in_degree_centralization = sum(max_in_degree - degree for degree in in_degrees.values()) / ((n - 1) * (n - 2))
    
    # Out-degree centralization
    out_degrees = dict(G.out_degree())
    max_out_degree = max(out_degrees.values()) if out_degrees else 0
    
    if n <= 1:
        out_degree_centralization = 0.0
    else:
        out_degree_centralization = sum(max_out_degree - degree for degree in out_degrees.values()) / ((n - 1) * (n - 2))
    
    # Betweenness centralization
    try:
        betweenness = nx.betweenness_centrality(G)
        max_betweenness = max(betweenness.values()) if betweenness else 0
        
        if n <= 1:
            betweenness_centralization = 0.0
        else:
            betweenness_centralization = sum(max_betweenness - bc for bc in betweenness.values()) / ((n - 1) * (n - 2))
    except:
        betweenness_centralization = np.nan
    
    return {
        'in_degree_centralization': in_degree_centralization,
        'out_degree_centralization': out_degree_centralization,
        'betweenness_centralization': betweenness_centralization
    }

def calculate_degree_stats(G: nx.DiGraph) -> Dict[str, float]:
    """Calcula estatísticas de grau."""
    if G.number_of_nodes() == 0:
        return {
            'avg_in_degree': 0.0,
            'median_in_degree': 0.0,
            'p90_in_degree': 0.0,
            'max_in_degree': 0.0,
            'avg_out_degree': 0.0,
            'median_out_degree': 0.0,
            'p90_out_degree': 0.0,
            'max_out_degree': 0.0,
            'avg_total_degree': 0.0,
            'median_total_degree': 0.0,
            'p90_total_degree': 0.0,
            'max_total_degree': 0.0
        }
    
    in_degrees = list(dict(G.in_degree()).values())
    out_degrees = list(dict(G.out_degree()).values())
    total_degrees = list(dict(G.degree()).values())
    
    def calc_stats(degrees):
        if not degrees:
            return 0.0, 0.0, 0.0, 0.0
        return np.mean(degrees), np.median(degrees), np.percentile(degrees, 90), np.max(degrees)
    
    avg_in, median_in, p90_in, max_in = calc_stats(in_degrees)
    avg_out, median_out, p90_out, max_out = calc_stats(out_degrees)
    avg_total, median_total, p90_total, max_total = calc_stats(total_degrees)
    
    return {
        'avg_in_degree': avg_in,
        'median_in_degree': median_in,
        'p90_in_degree': p90_in,
        'max_in_degree': max_in,
        'avg_out_degree': avg_out,
        'median_out_degree': median_out,
        'p90_out_degree': p90_out,
        'max_out_degree': max_out,
        'avg_total_degree': avg_total,
        'median_total_degree': median_total,
        'p90_total_degree': p90_total,
        'max_total_degree': max_total
    }

def calculate_pagerank(G: nx.DiGraph, top_n: int = 10) -> List[Tuple[str, float]]:
    """Calcula PageRank e retorna top N."""
    if G.number_of_nodes() == 0:
        return []
    
    try:
        pagerank = nx.pagerank(G, weight='weight')
        sorted_pagerank = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
        return sorted_pagerank[:top_n]
    except:
        return []

def calculate_betweenness(G: nx.DiGraph, top_n: int = 10) -> List[Tuple[str, float]]:
    """Calcula betweenness centrality e retorna top N."""
    if G.number_of_nodes() == 0:
        return []
    
    try:
        betweenness = nx.betweenness_centrality(G, weight='weight')
        sorted_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
        return sorted_betweenness[:top_n]
    except:
        return []

def calculate_assortativity_by_stance(G: nx.DiGraph, df: pd.DataFrame) -> float:
    """Calcula assortatividade por stance."""
    if 'stance' not in df.columns or df['stance'].isna().all():
        logger.info("Sem dados de stance disponíveis")
        return np.nan
    
    # Criar mapeamento de autor para stance
    author_stance = df.groupby('author')['stance'].first().to_dict()
    
    # Adicionar atributo stance aos nós
    for node in G.nodes():
        if node in author_stance:
            G.nodes[node]['stance'] = author_stance[node]
    
    try:
        assortativity = nx.attribute_assortativity_coefficient(G, 'stance')
        return assortativity
    except:
        return np.nan

def calculate_modularity(G: nx.DiGraph) -> Tuple[float, int]:
    """Calcula modularidade usando Louvain."""
    if G.number_of_nodes() == 0:
        return 0.0, 0
    
    try:
        import community as community_louvain
        
        # Converter para grafo não-direcionado para modularidade
        G_undir = G.to_undirected()
        
        # Calcular comunidades
        communities = community_louvain.best_partition(G_undir, weight='weight')
        
        # Calcular modularidade
        modularity = community_louvain.modularity(communities, G_undir, weight='weight')
        
        # Número de comunidades
        n_communities = len(set(communities.values()))
        
        return modularity, n_communities
    except ImportError:
        logger.warning("python-louvain não disponível, usando NetworkX")
        try:
            # Fallback para NetworkX
            communities = nx.community.louvain_communities(G.to_undirected(), weight='weight')
            modularity = nx.community.modularity(G.to_undirected(), communities, weight='weight')
            return modularity, len(communities)
        except:
            return np.nan, 0

def export_to_gexf(G: nx.DiGraph, output_path: Path, max_nodes: int = 500) -> None:
    """Exporta grafo para formato GEXF."""
    if G.number_of_nodes() == 0:
        logger.warning("Grafo vazio, não exportando GEXF")
        return
    
    # Se o grafo for muito grande, usar apenas os top nós por grau
    if G.number_of_nodes() > max_nodes:
        degrees = dict(G.degree())
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
        top_node_set = set([node for node, _ in top_nodes])
        
        # Criar subgrafo
        G_filtered = G.subgraph(top_node_set)
        logger.info(f"Filtrando grafo para top {max_nodes} nós por grau")
    else:
        G_filtered = G
    
    try:
        nx.write_gexf(G_filtered, output_path)
        logger.info(f"Grafo exportado para {output_path}")
    except Exception as e:
        logger.error(f"Erro ao exportar GEXF: {e}")

def build_complete_graph(df: pd.DataFrame, output_dir: Path, case_slug: str) -> Dict:
    """Constrói grafo completo e calcula todas as métricas."""
    logger.info(f"Construindo grafo completo para caso: {case_slug}")
    
    # Construir grafos individuais
    mention_G = build_mention_graph(df)
    rt_G = build_retweet_graph(df)
    reply_G = build_reply_graph(df)
    
    # Combinar grafos
    combined_G = combine_graphs(mention_G, rt_G, reply_G)
    
    # Calcular métricas
    basic_metrics = calculate_basic_metrics(combined_G)
    centralization_metrics = calculate_centralization_metrics(combined_G)
    degree_stats = calculate_degree_stats(combined_G)
    
    # PageRank e Betweenness
    pagerank_top = calculate_pagerank(combined_G)
    betweenness_top = calculate_betweenness(combined_G)
    
    # Assortatividade por stance
    assortativity = calculate_assortativity_by_stance(combined_G, df)
    
    # Modularidade
    modularity, n_communities = calculate_modularity(combined_G)
    
    # Encontrar usuário com maior in-degree
    in_degrees = dict(combined_G.in_degree())
    if in_degrees:
        max_in_degree_user = max(in_degrees.items(), key=lambda x: x[1])
        in_deg_target_max = max_in_degree_user[1]
        in_deg_target_max_user = max_in_degree_user[0]
    else:
        in_deg_target_max = 0
        in_deg_target_max_user = None
    
    # Compilar todas as métricas
    all_metrics = {
        **basic_metrics,
        **centralization_metrics,
        **degree_stats,
        'assortativity_stance': assortativity,
        'modularity': modularity,
        'n_communities': n_communities,
        'in_deg_target_max': in_deg_target_max,
        'in_deg_target_max_user': in_deg_target_max_user
    }
    
    # Exportar GEXF
    gexf_path = output_dir / f"{case_slug}_mention_graph.gexf"
    export_to_gexf(combined_G, gexf_path)
    
    return {
        'metrics': all_metrics,
        'pagerank_top': pagerank_top,
        'betweenness_top': betweenness_top,
        'graph': combined_G
    }

if __name__ == "__main__":
    # Teste básico
    print("Módulo de construção de grafos carregado")

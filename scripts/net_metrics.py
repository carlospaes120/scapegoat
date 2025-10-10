#!/usr/bin/env python3
"""
Script para calcular métricas de rede robusto a diferentes formatos de entrada.

Calcula métricas de nós (PageRank, betweenness, comunidades) e do grafo
(centralização, modularidade, densidade) a partir de eventos JSONL, 
CSV de arestas ou arquivos GEXF.

Exemplos de uso:
    # Instalação
    pip install -q -r requirements.txt
    
    # 1) Lendo diretamente JSONL (todos os eventos do caso, não só da vítima!)
    python net_metrics.py --jsonl notebooks/tweets_classified_eduardo_bueno.jsonl \
      --victim @EduardoBueno --outdir outputs/eduardo_bueno --btw-sample 500
    
    # 2) A partir de CSV de arestas
    python net_metrics.py --edges data/edges_eduardo.csv --weight-col weight \
      --victim @EduardoBueno --outdir outputs/eduardo_bueno
    
    # 3) A partir de GEXF
    python net_metrics.py --gexf outputs/eduardo_bueno/graph.gexf \
      --victim @EduardoBueno --outdir outputs/eduardo_bueno
"""

import argparse
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import glob

import pandas as pd
import networkx as nx
# --- Louvain (robusto ao ambiente) ---
community_louvain = None
try:
    import community as community_louvain                 # pacote python-louvain
except Exception:
    try:
        import community.community_louvain as community_louvain
    except Exception as e:
        community_louvain = None
        print("[WARN] python-louvain indisponível:", repr(e))
# -------------------------------------



def setup_logging(level: str = "INFO") -> None:
    """Configura logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def normalize_handle(handle: str) -> str:
    """Normaliza handle de usuário."""
    if not handle:
        return ""
    handle = str(handle).lower().strip()
    if not handle.startswith('@'):
        handle = f"@{handle}"
    return handle


def load_events_from_jsonl(file_paths: List[str]) -> pd.DataFrame:
    """
    Carrega eventos de múltiplos arquivos JSONL com esquemas variados.
    
    Args:
        file_paths: Lista de caminhos para arquivos JSONL
        
    Returns:
        DataFrame com eventos normalizados
    """
    logger = logging.getLogger(__name__)
    all_events = []
    
    for file_path in file_paths:
        # Expandir glob patterns
        if '*' in file_path:
            expanded_paths = glob.glob(file_path)
        else:
            expanded_paths = [file_path]
            
        for path in expanded_paths:
            if not os.path.exists(path):
                logger.warning(f"Arquivo não encontrado: {path}")
                continue
                
            logger.info(f"Carregando eventos de: {path}")
            
            try:
                events = []
                with open(path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                            
                        try:
                            event = json.loads(line)
                            events.append(event)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Erro JSON na linha {line_num} de {path}: {e}")
                            continue
                            
                logger.info(f"Carregados {len(events)} eventos de {path}")
                all_events.extend(events)
                
            except Exception as e:
                logger.error(f"Erro ao ler {path}: {e}")
                continue
    
    if not all_events:
        raise ValueError("Nenhum evento válido encontrado nos arquivos JSONL")
    
    logger.info(f"Total de eventos carregados: {len(all_events)}")
    return pd.DataFrame(all_events)


def extract_edges_from_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai arestas de eventos JSONL com esquemas variados.
    
    Args:
        df: DataFrame com eventos
        
    Returns:
        DataFrame com arestas (source, target, weight, type)
    """
    logger = logging.getLogger(__name__)
    edges = []
    
    # Aliases para campos
    author_fields = ['user_username', 'username', 'author.username', 'user.screen_name', 'user']
    mention_fields = ['mentioned_usernames', 'mentions', 'entities.mentions[].username', 
                   'entities.user_mentions[].screen_name']
    retweet_fields = ['retweeted_user_username', 'retweet_username', 'retweeted_status.user.screen_name']
    reply_fields = ['in_reply_to_username', 'in_reply_to_screen_name']
    stance_fields = ['stance', 'label_stance', 'stance_label']
    
    def get_field_value(row, field_list):
        """Tenta obter valor de uma lista de campos possíveis."""
        for field in field_list:
            if '.' in field:
                # Campo aninhado
                parts = field.split('.')
                value = row
                try:
                    for part in parts:
                        if part.endswith('[]'):
                            # Lista
                            part = part[:-2]
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                value = []
                                break
                        else:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                value = None
                                break
                    if value is not None:
                        return value
                except (KeyError, TypeError, AttributeError):
                    continue
            else:
                # Campo simples
                if field in row and pd.notna(row[field]):
                    return row[field]
        return None
    
    def extract_mentions_from_text(text: str) -> List[str]:
        """Extrai menções do texto usando regex."""
        if not text:
            return []
        mentions = re.findall(r'@(\w+)', str(text))
        return [f"@{mention.lower()}" for mention in mentions]
    
    for idx, row in df.iterrows():
        try:
            # Autor do tweet
            author = get_field_value(row, author_fields)
            if not author:
                continue
            author = normalize_handle(author)
            
            # Stance (se disponível)
            stance = get_field_value(row, stance_fields)
            
            # Menções
            mentions = []
            mention_data = get_field_value(row, mention_fields)
            if mention_data:
                if isinstance(mention_data, list):
                    mentions = [normalize_handle(m) for m in mention_data if m]
                elif isinstance(mention_data, str):
                    mentions = [normalize_handle(mention_data)]
            
            # Extrair menções do texto se não encontradas nos campos
            if not mentions and 'text' in row:
                text_mentions = extract_mentions_from_text(row['text'])
                mentions.extend(text_mentions)
            
            # Adicionar arestas de menções
            for mention in mentions:
                if mention and mention != author:  # Evitar self-loops
                    edges.append({
                        'source': author,
                        'target': mention,
                        'weight': 1,
                        'type': 'mention'
                    })
            
            # Retweets
            retweet_user = get_field_value(row, retweet_fields)
            if retweet_user:
                retweet_user = normalize_handle(retweet_user)
                if retweet_user != author:
                    edges.append({
                        'source': author,
                        'target': retweet_user,
                        'weight': 1,
                        'type': 'retweet'
                    })
            
            # Replies
            reply_user = get_field_value(row, reply_fields)
            if reply_user:
                reply_user = normalize_handle(reply_user)
                if reply_user != author:
                    edges.append({
                        'source': author,
                        'target': reply_user,
                        'weight': 1,
                        'type': 'reply'
                    })
            
            # Armazenar stance do autor se disponível
            if stance and author:
                # Adicionar como atributo do nó (será usado depois)
                pass
                
        except Exception as e:
            logger.warning(f"Erro ao processar evento {idx}: {e}")
            continue
    
    if not edges:
        raise ValueError("Nenhuma aresta extraída dos eventos")
    
    edges_df = pd.DataFrame(edges)
    
    # Consolidar multiarestas
    edges_consolidated = edges_df.groupby(['source', 'target']).agg({
        'weight': 'sum',
        'type': lambda x: '/'.join(sorted(set(x)))
    }).reset_index()
    
    logger.info(f"Extraídas {len(edges_consolidated)} arestas únicas de {len(edges)} arestas brutas")
    return edges_consolidated


def build_graph(edges_df: pd.DataFrame, min_degree: int = 0) -> nx.DiGraph:
    """
    Constrói grafo dirigido a partir de DataFrame de arestas.
    
    Args:
        edges_df: DataFrame com colunas source, target, weight
        min_degree: Grau mínimo para manter nós
        
    Returns:
        DiGraph com arestas e pesos
    """
    logger = logging.getLogger(__name__)
    
    G = nx.DiGraph()
    
    # Adicionar arestas
    for _, row in edges_df.iterrows():
        G.add_edge(
            row['source'], 
            row['target'], 
            weight=row['weight']
        )
    
    # Remover self-loops
    G.remove_edges_from(nx.selfloop_edges(G))
    
    # Filtrar por grau mínimo se especificado
    if min_degree > 0:
        nodes_to_remove = [
            node for node in G.nodes()
            if G.in_degree(node) + G.out_degree(node) < min_degree
        ]
        G.remove_nodes_from(nodes_to_remove)
        logger.info(f"Removidos {len(nodes_to_remove)} nós com grau < {min_degree}")
    
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G)
    
    logger.info(f"Nós: {n_nodes}, Arestas: {n_edges}, Densidade: {density:.6f}")
    
    if n_nodes < 3:
        logger.warning("Grafo com menos de 3 nós - algumas métricas podem ser NaN")
    if n_edges == 0:
        logger.warning("Grafo sem arestas - algumas métricas podem ser NaN")
    
    return G


def indegree_centralization(G: nx.DiGraph) -> float:
    """
    Calcula centralização de in-degree (Freeman, 0-1).
    
    Args:
        G: Grafo dirigido
        
    Returns:
        Centralização de in-degree (0-1) ou NaN se n < 3
    """
    n = G.number_of_nodes()
    if n < 3:
        return float("nan")
    
    deg_in = dict(G.in_degree())
    if not deg_in:
        return float("nan")
    
    max_deg = max(deg_in.values())
    num = sum(max_deg - d for d in deg_in.values())
    den = (n - 1) * (n - 2)
    
    return num / den if den > 0 else float("nan")


def compute_metrics(G: nx.DiGraph, btw_sample: int = 0) -> Tuple[Dict, pd.DataFrame]:
    """
    Calcula métricas de rede e de nós.
    
    Args:
        G: Grafo dirigido
        btw_sample: Número de nós para amostragem de betweenness (0 = completo)
        
    Returns:
        Tupla com (métricas_do_grafo, métricas_dos_nós)
    """
    logger = logging.getLogger(__name__)
    
    # Métricas básicas do grafo
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    density = nx.density(G)
    in_deg_centralization = indegree_centralization(G)
    
    # Modularidade (Louvain)
    # Modularity (Louvain) no grafo não-dirigido com peso
if community_louvain is not None and G.number_of_edges() > 0:
    und = G.to_undirected()
    part = community_louvain.best_partition(und, weight="weight")
    modularity = community_louvain.modularity(part, und, weight="weight")
else:
    modularity = float("nan")

    
    # Assortatividade por stance (se disponível)
    assortativity_stance = None
    if 'stance' in G.nodes[list(G.nodes())[0]] if G.nodes() else False:
        try:
            stance_values = {node: G.nodes[node].get('stance', 0) for node in G.nodes()}
            if len(set(stance_values.values())) > 1:  # Mais de uma categoria
                assortativity_stance = nx.attribute_assortativity_coefficient(
                    G.to_undirected(), "stance"
                )
        except Exception as e:
            logger.warning(f"Erro no cálculo de assortatividade: {e}")
    
    # Métricas dos nós
    node_metrics = []
    
    # PageRank
    try:
        pagerank = nx.pagerank(G, alpha=0.85, weight="weight")
    except Exception as e:
        logger.warning(f"Erro no cálculo de PageRank: {e}")
        pagerank = {node: 0.0 for node in G.nodes()}
    
    # Betweenness centrality
    if btw_sample > 0 and G.number_of_nodes() > btw_sample:
        logger.info(f"Calculando betweenness com amostragem de {btw_sample} nós")
        try:
            betweenness = nx.betweenness_centrality(G, k=btw_sample, weight="weight")
        except Exception as e:
            logger.warning(f"Erro no cálculo de betweenness (amostragem): {e}")
            betweenness = {node: 0.0 for node in G.nodes()}
    else:
        if G.number_of_nodes() > 100:
            logger.info("Calculando betweenness completo (pode ser lento para grafos grandes)")
        try:
            betweenness = nx.betweenness_centrality(G, weight="weight")
        except Exception as e:
            logger.warning(f"Erro no cálculo de betweenness: {e}")
            betweenness = {node: 0.0 for node in G.nodes()}
    
    # Compilar métricas dos nós
    for node in G.nodes():
        in_deg = G.in_degree(node)
        out_deg = G.out_degree(node)
        community = partition.get(node, 0)
        stance = G.nodes[node].get('stance', None)
        
        node_metrics.append({
            'node': node,
            'in_degree': in_deg,
            'out_degree': out_deg,
            'pagerank': pagerank.get(node, 0.0),
            'betweenness': betweenness.get(node, 0.0),
            'community': community,
            'stance': stance
        })
    
    node_df = pd.DataFrame(node_metrics)
    
    # Métricas do grafo
    graph_metrics = {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "density": density,
        "in_degree_centralization": in_deg_centralization,
        "modularity": modularity,
        "assortativity_stance": assortativity_stance
    }
    
    return graph_metrics, node_df


def compute_victim_metrics(G: nx.DiGraph, victim_aliases: List[str], 
                          node_df: pd.DataFrame) -> Optional[Dict]:
    """
    Calcula métricas específicas da vítima.
    
    Args:
        G: Grafo dirigido
        victim_aliases: Lista de aliases da vítima
        node_df: DataFrame com métricas dos nós
        
    Returns:
        Dicionário com métricas da vítima ou None se não encontrada
    """
    logger = logging.getLogger(__name__)
    
    # Normalizar aliases
    normalized_aliases = [normalize_handle(alias) for alias in victim_aliases]
    
    # Encontrar nó correspondente
    victim_node = None
    for node in G.nodes():
        if node in normalized_aliases:
            victim_node = node
            break
    
    if not victim_node:
        logger.warning(f"Vítima não encontrada no grafo. Aliases procurados: {victim_aliases}")
        return None
    
    # Métricas da vítima
    victim_data = node_df[node_df['node'] == victim_node].iloc[0]
    
    # Ego-rede (1-hop)
    ego_nodes = set([victim_node])
    ego_nodes.update(G.predecessors(victim_node))
    ego_nodes.update(G.successors(victim_node))
    
    ego_subgraph = G.subgraph(ego_nodes)
    ego_n = ego_subgraph.number_of_nodes()
    ego_m = ego_subgraph.number_of_edges()
    
    victim_metrics = {
        "victim_node": victim_node,
        "in_degree": int(victim_data['in_degree']),
        "out_degree": int(victim_data['out_degree']),
        "pagerank": float(victim_data['pagerank']),
        "betweenness": float(victim_data['betweenness']),
        "community": int(victim_data['community']),
        "ego_n": ego_n,
        "ego_m": ego_m
    }
    
    logger.info(f"Métricas da vítima {victim_node}: in_degree={victim_metrics['in_degree']}, "
                f"out_degree={victim_metrics['out_degree']}, pagerank={victim_metrics['pagerank']:.6f}")
    
    return victim_metrics


def save_outputs(outdir: str, graph_metrics: Dict, node_df: pd.DataFrame, 
                G: nx.DiGraph, victim_metrics: Optional[Dict] = None) -> None:
    """
    Salva todas as saídas em arquivos.
    
    Args:
        outdir: Diretório de saída
        graph_metrics: Métricas do grafo
        node_df: Métricas dos nós
        G: Grafo
        victim_metrics: Métricas da vítima (opcional)
    """
    logger = logging.getLogger(__name__)
    
    # Criar diretório
    os.makedirs(outdir, exist_ok=True)
    
    # Salvar métricas dos nós
    node_file = os.path.join(outdir, "node_metrics.csv")
    node_df.to_csv(node_file, index=False)
    logger.info(f"Métricas dos nós salvas em: {node_file}")
    
    # Salvar métricas do grafo
    graph_file = os.path.join(outdir, "graph_metrics.json")
    with open(graph_file, 'w', encoding='utf-8') as f:
        json.dump(graph_metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Métricas do grafo salvas em: {graph_file}")
    
    # Salvar métricas da vítima (se disponível)
    if victim_metrics:
        victim_file = os.path.join(outdir, "victim_metrics.json")
        with open(victim_file, 'w', encoding='utf-8') as f:
            json.dump(victim_metrics, f, indent=2, ensure_ascii=False)
        logger.info(f"Métricas da vítima salvas em: {victim_file}")
    
    # Salvar grafo em GEXF
    gexf_file = os.path.join(outdir, "graph.gexf")
    try:
        nx.write_gexf(G, gexf_file)
        logger.info(f"Grafo salvo em GEXF: {gexf_file}")
    except Exception as e:
        logger.error(f"Erro ao salvar GEXF: {e}")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Calcula métricas de rede robusto a diferentes formatos de entrada"
    )
    
    # Modos de entrada (mutuamente exclusivos)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--jsonl', nargs='+', help='Arquivos JSONL com eventos')
    input_group.add_argument('--edges', help='CSV com arestas (source,target[,weight])')
    input_group.add_argument('--gexf', help='Arquivo GEXF')
    
    # Parâmetros adicionais
    parser.add_argument('--weight-col', default='weight', help='Nome da coluna de peso no CSV')
    parser.add_argument('--victim', help='Aliases da vítima (separados por vírgula)')
    parser.add_argument('--outdir', required=True, help='Diretório de saída')
    parser.add_argument('--btw-sample', type=int, default=0, 
                       help='Amostragem para betweenness (0=completo)')
    parser.add_argument('--min-degree', type=int, default=0, 
                       help='Grau mínimo para manter nós')
    parser.add_argument('--log', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Nível de log')
    
    args = parser.parse_args()
    setup_logging(args.log)
    logger = logging.getLogger(__name__)
    
    try:
        # Carregar dados
        if args.jsonl:
            logger.info("Modo: JSONL")
            events_df = load_events_from_jsonl(args.jsonl)
            edges_df = extract_edges_from_events(events_df)
        elif args.edges:
            logger.info("Modo: CSV de arestas")
            edges_df = pd.read_csv(args.edges)
            if args.weight_col not in edges_df.columns:
                logger.warning(f"Coluna de peso '{args.weight_col}' não encontrada, usando peso=1")
                edges_df['weight'] = 1
            else:
                edges_df['weight'] = edges_df[args.weight_col]
        elif args.gexf:
            logger.info("Modo: GEXF")
            G = nx.read_gexf(args.gexf)
            if not G.is_directed():
                raise ValueError("Grafo deve ser dirigido")
            edges_df = None
        else:
            raise ValueError("Nenhum modo de entrada especificado")
        
        # Construir grafo (se não carregado do GEXF)
        if edges_df is not None:
            G = build_graph(edges_df, args.min_degree)
        
        # Verificações
        if not G.is_directed():
            raise ValueError("Grafo deve ser dirigido")
        
        # Calcular métricas
        graph_metrics, node_df = compute_metrics(G, args.btw_sample)
        
        # Métricas da vítima (se especificada)
        victim_metrics = None
        if args.victim:
            victim_aliases = [alias.strip() for alias in args.victim.split(',')]
            victim_metrics = compute_victim_metrics(G, victim_aliases, node_df)
        
        # Salvar saídas
        save_outputs(args.outdir, graph_metrics, node_df, G, victim_metrics)
        
        # Validações finais
        logger.info("=== VALIDAÇÕES ===")
        logger.info(f"n_nodes: {graph_metrics['n_nodes']} (deve ser > 0)")
        logger.info(f"n_edges: {graph_metrics['n_edges']} (deve ser > 0)")
        logger.info(f"in_degree_centralization: {graph_metrics['in_degree_centralization']:.6f} (deve estar em [0,1] ou ser NaN)")
        logger.info(f"modularity: {graph_metrics['modularity']:.6f} (deve estar em [0,1] ou ser NaN)")
        
        # Assertions
        assert graph_metrics['n_nodes'] > 0, "n_nodes deve ser > 0"
        assert graph_metrics['n_edges'] > 0, "n_edges deve ser > 0"
        
        if not pd.isna(graph_metrics['in_degree_centralization']):
            assert 0 <= graph_metrics['in_degree_centralization'] <= 1, \
                "in_degree_centralization deve estar em [0,1]"
        
        if not pd.isna(graph_metrics['modularity']):
            assert -0.5 <= graph_metrics['modularity'] <= 1, \
                "modularity deve estar em [-0.5,1]"
        
        logger.info("✅ Todas as validações passaram!")
        
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        raise


if __name__ == "__main__":
    main()

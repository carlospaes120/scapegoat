#!/usr/bin/env python3
"""
Análise de Estabilidade de Métricas de Rede - Caso Karol Conká
Mede estabilidade de métricas de rede através de amostragem progressiva

Como rodar:
pip install pandas numpy networkx matplotlib
python analysis/stability_curves.py

Objetivo: Determinar o tamanho mínimo de amostra necessário para métricas estáveis
"""

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import os
import glob
import json
from pathlib import Path

# Configurações
R = 100  # Número de réplicas por tamanho
PLOT_DIR = "analysis/stability_plots"

def load_karol_graph():
    """
    Carrega o grafo empírico da Karol Conká
    Tenta usar arquivos processados primeiro, depois raw
    """
    print("🔍 Carregando grafo empírico da Karol Conká...")
    
    # Tentar carregar edges processados primeiro
    edges_file = "data/processed/karol_conka/edges.csv"
    if os.path.exists(edges_file):
        print(f"📁 Carregando edges de: {edges_file}")
        edges_df = pd.read_csv(edges_file)
        
        # Criar grafo dirigido
        G = nx.DiGraph()
        
        for _, row in edges_df.iterrows():
            source = str(int(row['source']))
            target = str(int(row['target']))
            weight = row.get('weight', 1)
            edge_type = row.get('type', 'mention')
            
            G.add_edge(source, target, weight=weight, type=edge_type)
        
        print(f"✅ Grafo carregado: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
        return G
    
    # Fallback: tentar carregar de arquivos raw
    print("⚠️ Arquivo processado não encontrado, tentando arquivos raw...")
    raw_files = glob.glob("data/raw/karol_conka_*.json")
    
    if not raw_files:
        raise FileNotFoundError("Nenhum arquivo de dados encontrado")
    
    print(f"📁 Encontrados {len(raw_files)} arquivos raw")
    
    # Carregar e unir dados raw
    all_tweets = []
    for file in raw_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        all_tweets.extend(data)
                    elif isinstance(data, dict) and 'tweets' in data:
                        all_tweets.extend(data['tweets'])
            except Exception as e:
                print(f"⚠️ Erro ao carregar {file}: {e}")
    
    if not all_tweets:
        raise ValueError("Nenhum tweet carregado dos arquivos raw")
    
    print(f"📊 Total de tweets carregados: {len(all_tweets)}")
    
    # Construir grafo a partir dos tweets
    G = nx.DiGraph()
    
    for tweet in all_tweets:
        user_id = str(tweet.get('user', {}).get('id_str', tweet.get('user', {}).get('id', '')))
        if not user_id:
            continue
        
        # Adicionar nós de menções
        entities = tweet.get('entities', {})
        mentions = entities.get('user_mentions', [])
        
        for mention in mentions:
            mention_id = str(mention.get('id_str', mention.get('id', '')))
            if mention_id and mention_id != user_id:
                G.add_edge(user_id, mention_id, weight=1, type='mention')
        
        # Adicionar nós de retweets
        if 'retweeted_status' in tweet:
            rt_user_id = str(tweet['retweeted_status'].get('user', {}).get('id_str', 
                         tweet['retweeted_status'].get('user', {}).get('id', '')))
            if rt_user_id and rt_user_id != user_id:
                G.add_edge(user_id, rt_user_id, weight=1, type='retweet')
    
    print(f"✅ Grafo construído: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
    return G

def compute_network_metrics(G_sub):
    """
    Computa métricas de rede para um subgrafo
    """
    metrics = {}
    
    # Métricas básicas
    metrics['n_nodes'] = G_sub.number_of_nodes()
    metrics['n_edges'] = G_sub.number_of_edges()
    
    if metrics['n_nodes'] == 0:
        return metrics
    
    # Converter para não-dirigido para algumas métricas
    G_undir = G_sub.to_undirected()
    
    # LCC (Largest Connected Component)
    if G_undir.number_of_nodes() > 0:
        lcc = max(nx.connected_components(G_undir), key=len)
        metrics['lcc_nodes'] = len(lcc)
        metrics['lcc_ratio'] = len(lcc) / metrics['n_nodes'] if metrics['n_nodes'] > 0 else 0
        
        # Métricas na LCC
        if len(lcc) > 1:
            G_lcc = G_undir.subgraph(lcc)
            try:
                metrics['avg_shortest_path_lcc'] = nx.average_shortest_path_length(G_lcc)
                metrics['diameter_lcc'] = nx.diameter(G_lcc)
            except:
                metrics['avg_shortest_path_lcc'] = np.nan
                metrics['diameter_lcc'] = np.nan
        else:
            metrics['avg_shortest_path_lcc'] = np.nan
            metrics['diameter_lcc'] = np.nan
    else:
        metrics['lcc_nodes'] = 0
        metrics['lcc_ratio'] = 0
        metrics['avg_shortest_path_lcc'] = np.nan
        metrics['diameter_lcc'] = np.nan
    
    # Degree assortativity (não-dirigido)
    if G_undir.number_of_edges() > 0:
        try:
            metrics['degree_assortativity_ud'] = nx.degree_assortativity_coefficient(G_undir)
        except:
            metrics['degree_assortativity_ud'] = np.nan
    else:
        metrics['degree_assortativity_ud'] = np.nan
    
    # Average clustering (não-dirigido)
    if G_undir.number_of_nodes() > 0:
        try:
            metrics['avg_clustering_ud'] = nx.average_clustering(G_undir)
        except:
            metrics['avg_clustering_ud'] = np.nan
    else:
        metrics['avg_clustering_ud'] = np.nan
    
    # Modularity (não-dirigido)
    try:
        import networkx.algorithms.community as nx_comm
        if G_undir.number_of_edges() > 0:
            communities = nx_comm.louvain_communities(G_undir)
            metrics['modularity_ud'] = nx_comm.modularity(G_undir, communities)
        else:
            metrics['modularity_ud'] = np.nan
    except ImportError:
        metrics['modularity_ud'] = np.nan
        print("⚠️ networkx-community não disponível, modularity será NA")
    except Exception as e:
        metrics['modularity_ud'] = np.nan
        print(f"⚠️ Erro ao calcular modularity: {e}")
    
    return metrics

def run_stability_analysis():
    """
    Executa análise de estabilidade
    """
    print("🚀 ANÁLISE DE ESTABILIDADE - CASO KAROL CONKÁ")
    print("=" * 60)
    
    # Carregar grafo
    G = load_karol_graph()
    
    # Obter nós e definir tamanhos
    V = list(G.nodes())
    N_max = len(V)
    print(f"📊 N_max = {N_max}")
    
    # Definir tamanhos para análise
    Ns_candidates = [50, 100, 150, 200, 250, 300, 350, N_max]
    Ns = sorted([n for n in Ns_candidates if n <= N_max])
    print(f"📏 Tamanhos a analisar: {Ns}")
    
    # Criar diretório para plots
    os.makedirs(PLOT_DIR, exist_ok=True)
    
    # Armazenar resultados
    results = []
    
    print(f"\n🔄 Iniciando análise com R={R} réplicas por tamanho...")
    
    for N in Ns:
        print(f"\n📊 Analisando N={N}...")
        
        for r in range(R):
            if (r + 1) % 20 == 0:
                print(f"  Réplica {r+1}/{R}")
            
            # Amostrar N nós sem reposição
            sampled_nodes = np.random.choice(V, size=N, replace=False)
            
            # Criar subgrafo induzido
            G_sub = G.subgraph(sampled_nodes)
            
            # Computar métricas
            metrics = compute_network_metrics(G_sub)
            
            # Armazenar resultados
            for metric, value in metrics.items():
                results.append({
                    'N': N,
                    'replica': r,
                    'metric': metric,
                    'value': value
                })
    
    # Converter para DataFrame
    results_df = pd.DataFrame(results)
    
    # Salvar resultados brutos
    os.makedirs('analysis', exist_ok=True)
    results_df.to_csv('analysis/stability_curves.csv', index=False)
    print(f"💾 Resultados salvos: analysis/stability_curves.csv")
    
    # Calcular estatísticas por N e métrica
    summary_data = []
    
    for N in Ns:
        for metric in results_df['metric'].unique():
            values = results_df[(results_df['N'] == N) & (results_df['metric'] == metric)]['value']
            values = values.dropna()
            
            if len(values) > 0:
                summary_data.append({
                    'N': N,
                    'metric': metric,
                    'mean': values.mean(),
                    'std': values.std(),
                    'p2.5': np.percentile(values, 2.5),
                    'p97.5': np.percentile(values, 97.5),
                    'count': len(values)
                })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv('analysis/stability_summary.csv', index=False)
    print(f"💾 Resumo salvos: analysis/stability_summary.csv")
    
    # Gerar plots
    generate_plots(summary_df, Ns)
    
    # Analisar estabilidade e gerar relatório
    analyze_stability(summary_df, Ns)
    
    print(f"\n✅ Análise concluída!")

def generate_plots(summary_df, Ns):
    """
    Gera gráficos de estabilidade
    """
    print(f"\n📊 Gerando gráficos em {PLOT_DIR}/...")
    
    metrics_to_plot = ['n_nodes', 'n_edges', 'lcc_nodes', 'lcc_ratio', 
                      'degree_assortativity_ud', 'modularity_ud', 
                      'avg_shortest_path_lcc', 'diameter_lcc', 'avg_clustering_ud']
    
    for metric in metrics_to_plot:
        metric_data = summary_df[summary_df['metric'] == metric]
        
        if len(metric_data) == 0:
            continue
        
        plt.figure(figsize=(10, 6))
        
        # Plotar média
        plt.plot(metric_data['N'], metric_data['mean'], 'o-', label='Média', linewidth=2)
        
        # Plotar intervalos de confiança
        plt.fill_between(metric_data['N'], 
                        metric_data['p2.5'], 
                        metric_data['p97.5'], 
                        alpha=0.3, label='IC 95%')
        
        plt.xlabel('Tamanho da Amostra (N)')
        plt.ylabel(metric)
        plt.title(f'Estabilidade de {metric}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Salvar plot
        plot_file = f"{PLOT_DIR}/{metric}.png"
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  📈 {metric}.png")

def analyze_stability(summary_df, Ns):
    """
    Analisa estabilidade e gera relatório
    """
    print(f"\n📋 Analisando estabilidade...")
    
    # Critérios de estabilidade
    stability_criteria = {}
    
    for metric in summary_df['metric'].unique():
        metric_data = summary_df[summary_df['metric'] == metric].sort_values('N')
        
        if len(metric_data) == 0:
            continue
        
        stable_N = None
        
        for i, row in metric_data.iterrows():
            N = row['N']
            mean_val = row['mean']
            p2_5 = row['p2.5']
            p97_5 = row['p97.5']
            
            # Critério 1: intervalo < 10% da média (ou < 0.05 para modularity/assortativity)
            if metric in ['modularity_ud', 'degree_assortativity_ud']:
                interval_criterion = (p97_5 - p2_5) < 0.05
            else:
                interval_criterion = (p97_5 - p2_5) < 0.1 * abs(mean_val)
            
            # Critério 2: variação relativa < 5%
            variation_criterion = True
            if len(metric_data) > 1 and i > 0:
                prev_row = metric_data.iloc[i-1]
                prev_mean = prev_row['mean']
                if abs(prev_mean) > 1e-10:  # Evitar divisão por zero
                    variation = abs(mean_val - prev_mean) / abs(prev_mean)
                    variation_criterion = variation < 0.05
            
            if interval_criterion and variation_criterion:
                stable_N = N
                break
        
        stability_criteria[metric] = stable_N
    
    # Gerar relatório
    generate_report(stability_criteria, summary_df)
    
    # Imprimir resumo no terminal
    print(f"\n🎯 RESUMO DE ESTABILIDADE:")
    print("=" * 50)
    
    for metric, stable_N in stability_criteria.items():
        if stable_N:
            print(f"{metric:25s}: N = {stable_N:3d} (estável)")
        else:
            print(f"{metric:25s}: N = N/A (nunca estável)")
    
    # N_target final
    stable_Ns = [N for N in stability_criteria.values() if N is not None]
    if stable_Ns:
        N_target_final = max(stable_Ns)
        print(f"\n🎯 N_TARGET_FINAL = {N_target_final}")
    else:
        print(f"\n⚠️ Nenhuma métrica atingiu estabilidade")
        N_target_final = None
    
    return N_target_final

def generate_report(stability_criteria, summary_df):
    """
    Gera relatório em Markdown
    """
    report_content = "# Relatório de Estabilidade - Caso Karol Conká\n\n"
    report_content += "Análise de estabilidade de métricas de rede através de amostragem progressiva.\n\n"
    
    report_content += "## Critérios de Estabilidade\n\n"
    report_content += "- **Intervalo de confiança**: (p97.5 - p2.5) < 10% da média\n"
    report_content += "- **Variação relativa**: |mean(N) - mean(N-Δ)| / mean(N) < 5%\n"
    report_content += "- **Exceções**: Para modularity e assortativity, intervalo < 0.05\n\n"
    
    report_content += "## Resultados por Métrica\n\n"
    report_content += "| Métrica | N Estável | Observações |\n"
    report_content += "|---------|-----------|-------------|\n"
    
    for metric, stable_N in stability_criteria.items():
        if stable_N:
            report_content += f"| {metric} | {stable_N} | ✅ Estável |\n"
        else:
            report_content += f"| {metric} | N/A | ❌ Nunca estável |\n"
    
    # N_target final
    stable_Ns = [N for N in stability_criteria.values() if N is not None]
    if stable_Ns:
        N_target_final = max(stable_Ns)
        report_content += f"\n## Recomendação\n\n"
        report_content += f"**N_TARGET_FINAL = {N_target_final}**\n\n"
        report_content += f"Este é o tamanho mínimo recomendado para garantir estabilidade em todas as métricas analisadas.\n\n"
    else:
        report_content += f"\n## Recomendação\n\n"
        report_content += f"**Nenhuma métrica atingiu estabilidade**\n\n"
        report_content += f"Considere aumentar o tamanho da amostra ou revisar os critérios de estabilidade.\n\n"
    
    report_content += "## Arquivos Gerados\n\n"
    report_content += "- `stability_curves.csv`: Resultados brutos de todas as réplicas\n"
    report_content += "- `stability_summary.csv`: Estatísticas por tamanho e métrica\n"
    report_content += "- `stability_plots/`: Gráficos de estabilidade por métrica\n"
    
    # Salvar relatório
    with open('analysis/stability_report.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 Relatório salvo: analysis/stability_report.md")

if __name__ == "__main__":
    run_stability_analysis()

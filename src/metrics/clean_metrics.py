"""
Script para limpar e corrigir o arquivo de métricas.
"""

import pandas as pd
import numpy as np
import ast

def clean_metrics_csv(input_file, output_file):
    """
    Limpa o arquivo de métricas CSV.
    """
    print(f"Lendo arquivo: {input_file}")
    
    # Ler o CSV
    df = pd.read_csv(input_file)
    
    print(f"Colunas originais: {list(df.columns)}")
    print(f"Shape: {df.shape}")
    
    # Limpar espaços das colunas
    df.columns = df.columns.str.strip()
    
    # Remover linhas vazias
    df = df.dropna(how='all')
    
    # Converter colunas numéricas
    numeric_columns = [
        'n_nodes', 'n_edges', 'density', 'peak_mean', 'peak_median',
        'topk_pr_share_k5', 'topk_pr_share_k10', 'betweenness_centralization',
        'victim_reciprocity', 'victim_scc_size', 'victim_ego_density',
        'victim_inshare', 'graph_density', 'avg_path_len', 'eff_diameter',
        'n_communities', 'modularity', 'largest_community_size',
        'avg_community_size', 'community_size_std'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Converter colunas booleanas
    boolean_columns = [
        'is_weakly_connected', 'is_strongly_connected', 'victim_is_isolated',
        'onset_flag', 'climax_flag'
    ]
    
    for col in boolean_columns:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    # Converter timestamps
    if 't_start' in df.columns:
        df['t_start'] = pd.to_datetime(df['t_start'])
    if 't_end' in df.columns:
        df['t_end'] = pd.to_datetime(df['t_end'])
    
    # Limpar colunas de dicionários
    dict_columns = ['pagerank_scores', 'communities']
    for col in dict_columns:
        if col in df.columns:
            # Converter strings de dicionário para NaN
            df[col] = df[col].apply(lambda x: np.nan if isinstance(x, str) and x.startswith('{') else x)
    
    # Preencher valores NaN com valores padrão
    df = df.fillna({
        'victim_reciprocity': 0,
        'victim_scc_size': 0,
        'victim_ego_density': 0.0,
        'victim_inshare': 0.0,
        'assort_skeptic': np.nan,
        'betweenness_share_skeptic': 0.0,
        'avg_path_len': np.nan,
        'eff_diameter': np.nan,
        'median_distance_to_victim': np.nan,
        'victim_inshare_half_life': np.nan
    })
    
    # Salvar arquivo limpo
    df.to_csv(output_file, index=False)
    print(f"Arquivo limpo salvo em: {output_file}")
    print(f"Shape final: {df.shape}")
    print(f"Colunas finais: {list(df.columns)}")
    
    return df

if __name__ == "__main__":
    # Limpar o arquivo de métricas
    clean_df = clean_metrics_csv('results/metrics_by_window.csv', 'results/metrics_by_window_clean.csv')
    
    print("\nPrimeiras linhas do arquivo limpo:")
    print(clean_df.head())

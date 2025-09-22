#!/usr/bin/env python3
"""
Script para análise de dados do BehaviorSpace do NetLogo
Analisa simulações contra métricas empíricas do caso Karol Conká
"""

import pandas as pd
import numpy as np
import glob
import os
from pathlib import Path

# Metas empíricas do caso Karol Conká
TARGETS = {
    "largest_wcc_nodes": 191,
    "degree_assortativity_ud": -0.39,
    "modularity_ud": 0.64,
    "avg_shortest_path_lcc": 3.17,
    "diameter_lcc": 7,
    "avg_clustering_ud": 0.00,
    "n_nodes": 318,
    "n_edges": 304,
}

# Tolerâncias para métricas de tamanho
TOL = {"n_nodes": 0.1, "n_edges": 0.1}  # ±10% para tamanho

def load_csvs(pattern="data/behaviorspace/*.csv"):
    """
    Carrega e concatena todos os CSVs do BehaviorSpace
    Normaliza nomes de colunas (lowercase, espaços por _)
    """
    print(f"🔍 Buscando arquivos com padrão: {pattern}")
    
    # Buscar arquivos
    files = glob.glob(pattern)
    if not files:
        print(f"❌ Nenhum arquivo encontrado com padrão: {pattern}")
        return pd.DataFrame()
    
    print(f"📁 Encontrados {len(files)} arquivos:")
    for f in files:
        print(f"  - {f}")
    
    # Carregar e concatenar CSVs
    dfs = []
    for file in files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
            print(f"✅ Carregado: {file} ({len(df)} linhas)")
        except Exception as e:
            print(f"❌ Erro ao carregar {file}: {e}")
    
    if not dfs:
        print("❌ Nenhum CSV foi carregado com sucesso")
        return pd.DataFrame()
    
    # Concatenar todos os DataFrames
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"📊 Total de linhas combinadas: {len(combined_df)}")
    
    # Normalizar nomes de colunas
    combined_df.columns = combined_df.columns.str.lower().str.replace(' ', '_')
    print(f"🏷️ Colunas normalizadas: {list(combined_df.columns)}")
    
    return combined_df

def score_row(row):
    """
    Calcula score para uma linha baseado nas métricas empíricas
    Retorna dict com erros e score total
    """
    errors = {}
    score = 0.0
    
    for metric, target in TARGETS.items():
        if metric not in row:
            errors[f"err_{metric}"] = np.nan
            continue
        
        value = row[metric]
        if pd.isna(value):
            errors[f"err_{metric}"] = np.nan
            continue
        
        # Calcular erro
        if metric in ["degree_assortativity_ud", "avg_clustering_ud"]:
            # Erro absoluto para essas métricas
            error = abs(value - target)
        else:
            # Erro relativo para outras métricas
            if target != 0:
                error = abs(value - target) / abs(target)
            else:
                error = abs(value - target)
        
        errors[f"err_{metric}"] = error
        score += error
        
        # Penalidade extra para métricas de tamanho se sair do range
        if metric in TOL:
            tolerance = TOL[metric]
            if abs(value - target) / target > tolerance:
                penalty = 2.0  # Penalidade extra
                score += penalty
                errors[f"err_{metric}_penalty"] = penalty
            else:
                errors[f"err_{metric}_penalty"] = 0.0
    
    errors["score_total"] = score
    return errors

def analyze_behaviorspace():
    """
    Função principal de análise
    """
    print("🚀 ANÁLISE DO BEHAVIORSPACE - CASO KAROL CONKÁ")
    print("=" * 60)
    
    # Carregar dados
    df = load_csvs()
    if df.empty:
        print("❌ Não foi possível carregar dados. Encerrando.")
        return
    
    print(f"\n📊 Dataset carregado:")
    print(f"  - Linhas: {len(df)}")
    print(f"  - Colunas: {len(df.columns)}")
    
    # Verificar se as métricas alvo existem
    missing_metrics = [m for m in TARGETS.keys() if m not in df.columns]
    if missing_metrics:
        print(f"⚠️ Métricas não encontradas: {missing_metrics}")
    
    # Calcular erros e scores
    print("\n🧮 Calculando erros e scores...")
    
    error_data = []
    for idx, row in df.iterrows():
        errors = score_row(row)
        error_data.append(errors)
    
    # Adicionar colunas de erro ao DataFrame
    error_df = pd.DataFrame(error_data)
    df_with_errors = pd.concat([df, error_df], axis=1)
    
    # Ordenar por score total
    df_with_errors = df_with_errors.sort_values('score_total', ascending=True)
    
    # Criar diretório de saída se não existir
    os.makedirs('analysis', exist_ok=True)
    
    # Salvar relatório completo
    report_file = 'analysis/bs_report.csv'
    df_with_errors.to_csv(report_file, index=False)
    print(f"💾 Relatório completo salvo: {report_file}")
    
    # Criar relatório dos top 20
    top_20 = df_with_errors.head(20)
    create_top_report(top_20)
    
    # Mostrar resumo dos 10 melhores
    print_summary(df_with_errors.head(10))
    
    # Mostrar estatísticas por parâmetro
    print_parameter_stats(df_with_errors)
    
    print(f"\n✅ Análise concluída!")
    print(f"📁 Arquivos gerados:")
    print(f"  - {report_file}")
    print(f"  - analysis/bs_top.md")

def create_top_report(top_df):
    """
    Cria relatório Markdown dos top 20 runs
    """
    md_content = "# Top 20 Runs - BehaviorSpace Analysis\n\n"
    md_content += "Análise das melhores simulações contra métricas empíricas do caso Karol Conká\n\n"
    
    md_content += "## Métricas Alvo\n\n"
    for metric, target in TARGETS.items():
        md_content += f"- **{metric}**: {target}\n"
    
    md_content += "\n## Top 20 Runs\n\n"
    md_content += "| Rank | Score | Friendliness | Skepticism | NumNodes | "
    
    # Adicionar colunas para métricas principais
    main_metrics = ["largest_wcc_nodes", "degree_assortativity_ud", "modularity_ud", 
                   "avg_shortest_path_lcc", "n_nodes", "n_edges"]
    for metric in main_metrics:
        if metric in top_df.columns:
            md_content += f"{metric} | "
    
    md_content += "\n|------|-------|--------------|------------|----------|"
    for _ in main_metrics:
        md_content += "--------|"
    md_content += "\n"
    
    for idx, (_, row) in enumerate(top_df.iterrows(), 1):
        md_content += f"| {idx} | {row['score_total']:.3f} | "
        
        # Parâmetros principais
        friendliness = row.get('friendliness', 'N/A')
        skepticism = row.get('skepticism', 'N/A')
        numnodes = row.get('numnodes', 'N/A')
        
        md_content += f"{friendliness} | {skepticism} | {numnodes} | "
        
        # Métricas principais
        for metric in main_metrics:
            if metric in row:
                value = row[metric]
                if pd.isna(value):
                    md_content += "N/A | "
                else:
                    md_content += f"{value:.3f} | "
            else:
                md_content += "N/A | "
        
        md_content += "\n"
    
    # Salvar arquivo
    with open('analysis/bs_top.md', 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print("📄 Relatório top 20 salvo: analysis/bs_top.md")

def print_summary(top_10):
    """
    Imprime resumo dos 10 melhores runs
    """
    print("\n🏆 TOP 10 MELHORES RUNS")
    print("=" * 80)
    
    for idx, (_, row) in enumerate(top_10.iterrows(), 1):
        print(f"\n#{idx} - Score: {row['score_total']:.3f}")
        print(f"  Parâmetros: friendliness={row.get('friendliness', 'N/A')}, "
              f"skepticism={row.get('skepticism', 'N/A')}, "
              f"numnodes={row.get('numnodes', 'N/A')}")
        
        # Mostrar métricas principais
        main_metrics = ["largest_wcc_nodes", "degree_assortativity_ud", "modularity_ud", 
                       "avg_shortest_path_lcc", "n_nodes", "n_edges"]
        
        for metric in main_metrics:
            if metric in row and not pd.isna(row[metric]):
                target = TARGETS[metric]
                value = row[metric]
                error = abs(value - target)
                print(f"  {metric}: {value:.3f} (target: {target}, error: {error:.3f})")

def print_parameter_stats(df):
    """
    Imprime estatísticas por parâmetro
    """
    print("\n📊 ESTATÍSTICAS POR PARÂMETRO")
    print("=" * 60)
    
    # Parâmetros principais para análise
    main_params = ['friendliness', 'skepticism', 'numnodes']
    
    for param in main_params:
        if param in df.columns:
            values = df[param].dropna()
            if len(values) > 0:
                print(f"\n{param.upper()}:")
                print(f"  Média: {values.mean():.3f}")
                print(f"  Desvio: {values.std():.3f}")
                print(f"  Min: {values.min():.3f}")
                print(f"  Max: {values.max():.3f}")
                print(f"  Valores únicos: {values.nunique()}")
    
    # Estatísticas do score
    scores = df['score_total'].dropna()
    if len(scores) > 0:
        print(f"\nSCORE TOTAL:")
        print(f"  Média: {scores.mean():.3f}")
        print(f"  Desvio: {scores.std():.3f}")
        print(f"  Min: {scores.min():.3f}")
        print(f"  Max: {scores.max():.3f}")

if __name__ == "__main__":
    analyze_behaviorspace()

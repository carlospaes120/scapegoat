#!/usr/bin/env python3
"""
Orquestração da análise comparativa entre casos de cancelamento.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
import json
from datetime import datetime

from process_jsonl import process_jsonl_file, get_case_slug_from_filename, discover_jsonl_files
from build_graph import build_complete_graph
from metrics_reports import (
    calculate_engagement_metrics, calculate_temporal_metrics, 
    calculate_mention_metrics, create_time_series_data,
    create_user_engagement_table, create_mention_targets_table,
    calculate_case_summary_metrics
)
from plots import (
    plot_temporal_volume, plot_peak_metrics, plot_inequality_metrics,
    plot_top_shares, plot_top_mentions, plot_engagement_distribution,
    plot_network_preview, plot_comparative_metrics, plot_temporal_overlay
)

logger = logging.getLogger(__name__)

def process_single_case(file_path: Path, output_dir: Path) -> Dict:
    """Processa um único caso e gera todas as análises."""
    case_slug = get_case_slug_from_filename(file_path)
    logger.info(f"Processando caso: {case_slug}")
    
    # Criar diretórios de saída
    case_output_dir = output_dir / case_slug
    figures_dir = case_output_dir / "figures"
    tables_dir = case_output_dir / "tables"
    
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    
    # Processar dados
    logger.info(f"Lendo e normalizando dados de {file_path.name}")
    df = process_jsonl_file(file_path)
    
    if len(df) == 0:
        logger.warning(f"Nenhum dado válido encontrado em {file_path.name}")
        return {
            'case_slug': case_slug,
            'data': pd.DataFrame(),
            'metrics': {},
            'graph_metrics': {},
            'success': False
        }
    
    # Construir grafo e calcular métricas de rede
    logger.info(f"Construindo grafo para {case_slug}")
    graph_results = build_complete_graph(df, tables_dir, case_slug)
    
    # Calcular métricas de engajamento
    logger.info(f"Calculando métricas de engajamento para {case_slug}")
    engagement_metrics = calculate_engagement_metrics(df)
    
    # Calcular métricas temporais
    logger.info(f"Calculando métricas temporais para {case_slug}")
    temporal_metrics = calculate_temporal_metrics(df)
    
    # Calcular métricas de menções
    logger.info(f"Calculando métricas de menções para {case_slug}")
    mention_metrics = calculate_mention_metrics(df)
    
    # Compilar métricas resumo
    summary_metrics = calculate_case_summary_metrics(df, graph_results['metrics'])
    
    # Gerar tabelas
    logger.info(f"Gerando tabelas para {case_slug}")
    
    # Tabela de usuários por engajamento
    user_engagement_table = create_user_engagement_table(df)
    user_engagement_table.to_csv(tables_dir / "top_users_by_engagement.csv", index=False)
    
    # Tabela de alvos por menções
    mention_targets_table = create_mention_targets_table(df)
    mention_targets_table.to_csv(tables_dir / "top_targets_by_mentions.csv", index=False)
    
    # Séries temporais
    daily_series, hourly_series = create_time_series_data(df)
    daily_series.to_csv(tables_dir / "time_series_day.csv", index=False)
    hourly_series.to_csv(tables_dir / "time_series_hour.csv", index=False)
    
    # Métricas de rede
    network_metrics_df = pd.DataFrame([graph_results['metrics']])
    network_metrics_df.to_csv(tables_dir / f"metrics_{case_slug}.csv", index=False)
    
    # Top PageRank e Betweenness
    if graph_results['pagerank_top']:
        pagerank_df = pd.DataFrame(graph_results['pagerank_top'], 
                                 columns=['user', 'pagerank'])
        pagerank_df.to_csv(tables_dir / "top_pagerank.csv", index=False)
    
    if graph_results['betweenness_top']:
        betweenness_df = pd.DataFrame(graph_results['betweenness_top'], 
                                   columns=['user', 'betweenness'])
        betweenness_df.to_csv(tables_dir / "top_betweenness.csv", index=False)
    
    # Gerar visualizações
    logger.info(f"Gerando visualizações para {case_slug}")
    
    # Volume temporal
    plot_temporal_volume(df, figures_dir / "ts_day.png", case_slug)
    
    # Métricas de pico
    plot_peak_metrics(df, figures_dir / "peak_div_median_day.png", case_slug)
    
    # Métricas de desigualdade
    plot_inequality_metrics(df, figures_dir / "gini_eng_tweet.png", case_slug)
    
    # Top shares
    plot_top_shares(df, figures_dir / "top_share_users.png", case_slug)
    
    # Top menções
    plot_top_mentions(df, figures_dir / "top_mentions.png", case_slug)
    
    # Distribuição de engajamento
    plot_engagement_distribution(df, figures_dir / "engagement_hist.png", case_slug)
    
    # Preview da rede
    if graph_results['graph'].number_of_nodes() > 0:
        plot_network_preview(graph_results['graph'], 
                           figures_dir / "mention_graph_preview.png", case_slug)
    
    logger.info(f"Caso {case_slug} processado com sucesso")
    
    return {
        'case_slug': case_slug,
        'data': df,
        'metrics': summary_metrics,
        'graph_metrics': graph_results['metrics'],
        'graph': graph_results['graph'],
        'success': True
    }

def create_comparative_analysis(cases_results: List[Dict], output_dir: Path) -> None:
    """Cria análise comparativa entre todos os casos."""
    logger.info("Criando análise comparativa")
    
    compare_dir = output_dir / "compare"
    compare_dir.mkdir(parents=True, exist_ok=True)
    
    # Compilar métricas de todos os casos
    cases_summary = []
    cases_data = {}
    
    for case_result in cases_results:
        if not case_result['success']:
            continue
        
        case_slug = case_result['case_slug']
        metrics = case_result['metrics']
        data = case_result['data']
        
        # Adicionar ao resumo
        summary_row = {
            'case': case_slug,
            **metrics
        }
        cases_summary.append(summary_row)
        
        # Adicionar dados para comparação temporal
        cases_data[case_slug] = data
    
    # Salvar resumo comparativo
    if cases_summary:
        summary_df = pd.DataFrame(cases_summary)
        summary_df.to_csv(compare_dir / "cases_summary.csv", index=False)
        logger.info(f"Resumo comparativo salvo: {compare_dir / 'cases_summary.csv'}")
    
    # Gerar visualizações comparativas
    if len(cases_summary) > 1:
        logger.info("Gerando visualizações comparativas")
        
        # Métricas comparativas
        metrics_to_compare = [
            'gini_engagement_tweet', 'gini_engagement_user', 'hhi_engagement_tweet',
            'top1_share', 'top5_share', 'top10_share', 'in_degree_centralization'
        ]
        
        for metric in metrics_to_compare:
            if metric in summary_df.columns:
                cases_dict = {row['case']: row for row in cases_summary}
                plot_comparative_metrics(cases_dict, 
                                       compare_dir / f"compare_{metric}.png", 
                                       metric)
        
        # Sobreposição temporal
        if cases_data:
            plot_temporal_overlay(cases_data, compare_dir / "compare_ts_day_overlay.png")
    
    logger.info("Análise comparativa concluída")

def run_complete_analysis(data_dir: Path, output_dir: Path) -> Dict:
    """Executa análise completa de todos os casos."""
    logger.info("Iniciando análise completa")
    
    # Descobrir arquivos JSONL
    jsonl_files = discover_jsonl_files(data_dir)
    
    if not jsonl_files:
        logger.error(f"Nenhum arquivo JSONL encontrado em {data_dir}")
        return {'success': False, 'cases_processed': 0}
    
    logger.info(f"Encontrados {len(jsonl_files)} arquivos para processar")
    
    # Processar cada caso
    cases_results = []
    successful_cases = 0
    
    for file_path in jsonl_files:
        try:
            case_result = process_single_case(file_path, output_dir)
            cases_results.append(case_result)
            
            if case_result['success']:
                successful_cases += 1
                logger.info(f"✅ Caso {case_result['case_slug']} processado com sucesso")
            else:
                logger.warning(f"⚠️ Caso {case_result['case_slug']} falhou")
        
        except Exception as e:
            logger.error(f"❌ Erro ao processar {file_path.name}: {e}")
            continue
    
    # Criar análise comparativa
    if successful_cases > 1:
        create_comparative_analysis(cases_results, output_dir)
    
    # Gerar relatório final
    generate_final_report(cases_results, output_dir)
    
    logger.info(f"Análise completa finalizada. {successful_cases}/{len(jsonl_files)} casos processados com sucesso")
    
    return {
        'success': True,
        'cases_processed': successful_cases,
        'total_cases': len(jsonl_files),
        'cases_results': cases_results
    }

def generate_final_report(cases_results: List[Dict], output_dir: Path) -> None:
    """Gera relatório final da análise."""
    logger.info("Gerando relatório final")
    
    report_path = output_dir / "analysis_report.txt"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE ANÁLISE - CASOS DE CANCELAMENTO\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Data da análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total de casos processados: {len(cases_results)}\n\n")
        
        for case_result in cases_results:
            if not case_result['success']:
                continue
            
            case_slug = case_result['case_slug']
            metrics = case_result['metrics']
            data = case_result['data']
            
            f.write(f"CASO: {case_slug.upper()}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Volume total: {metrics.get('total_volume', 0):,} tweets\n")
            f.write(f"Usuários únicos: {metrics.get('unique_users', 0):,}\n")
            f.write(f"Gini (tweet): {metrics.get('gini_engagement_tweet', 0):.3f}\n")
            f.write(f"Gini (usuário): {metrics.get('gini_engagement_user', 0):.3f}\n")
            f.write(f"Top 1 share: {metrics.get('top1_share', 0):.1f}%\n")
            f.write(f"Centralização in-degree: {metrics.get('in_degree_centralization', 0):.3f}\n")
            f.write(f"Modularidade: {metrics.get('modularity', 0):.3f}\n")
            f.write("\n")
    
    logger.info(f"Relatório final salvo: {report_path}")

def print_output_summary(output_dir: Path) -> None:
    """Imprime resumo da estrutura de saída."""
    logger.info("Estrutura de saída gerada:")
    
    def print_tree(directory: Path, prefix: str = ""):
        if not directory.exists():
            return
        
        items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name))
        
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            try:
                print(f"{prefix}{current_prefix}{item.name}")
            except UnicodeEncodeError:
                print(f"{prefix}{current_prefix}{item.name.encode('ascii', 'replace').decode()}")
            
            if item.is_dir():
                next_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(item, next_prefix)
    
    print(f"\n{output_dir}")
    print_tree(output_dir)
    
    # Listar arquivos PNG e CSV
    png_files = list(output_dir.rglob("*.png"))
    csv_files = list(output_dir.rglob("*.csv"))
    
    print(f"\nResumo:")
    print(f"  - {len(png_files)} arquivos PNG (figuras)")
    print(f"  - {len(csv_files)} arquivos CSV (tabelas)")
    
    # Listar por caso
    for case_dir in output_dir.iterdir():
        if case_dir.is_dir() and case_dir.name != "compare":
            case_png = len(list(case_dir.rglob("*.png")))
            case_csv = len(list(case_dir.rglob("*.csv")))
            print(f"  - {case_dir.name}: {case_png} PNGs, {case_csv} CSVs")

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('outputs/log.txt'),
            logging.StreamHandler()
        ]
    )
    
    # Executar análise
    data_dir = Path("data/jsonl")
    output_dir = Path("outputs")
    
    if not data_dir.exists():
        print(f"❌ Diretório {data_dir} não encontrado")
        print("Crie o diretório e adicione arquivos .jsonl para processar")
    else:
        results = run_complete_analysis(data_dir, output_dir)
        
        if results['success']:
            print(f"\n✅ Análise concluída com sucesso!")
            print(f"📊 {results['cases_processed']}/{results['total_cases']} casos processados")
            print_output_summary(output_dir)
        else:
            print("❌ Análise falhou")

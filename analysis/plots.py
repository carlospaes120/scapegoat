#!/usr/bin/env python3
"""
Geração de visualizações para análise de casos de cancelamento no Twitter.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import networkx as nx
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# Configurar matplotlib
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['figure.figsize'] = (19.2, 10.8)  # 1920x1080 pixels
plt.rcParams['font.size'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10

logger = logging.getLogger(__name__)

def plot_temporal_volume(df: pd.DataFrame, output_path: Path, case_slug: str) -> None:
    """Plota volume temporal por dia e por hora."""
    if len(df) == 0:
        logger.warning(f"Sem dados para plotar volume temporal para {case_slug}")
        return
    
    df_temp = df.copy()
    df_temp['created_at'] = pd.to_datetime(df_temp['created_at'])
    df_temp = df_temp.set_index('created_at')
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(19.2, 10.8))
    
    # Volume diário
    daily_volume = df_temp.resample('D').size()
    ax1.plot(daily_volume.index, daily_volume.values, linewidth=2, color='blue')
    ax1.set_title(f'{case_slug.title()} - Volume Diário de Tweets', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Data')
    ax1.set_ylabel('Número de Tweets')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Volume horário
    hourly_volume = df_temp.resample('H').size()
    ax2.plot(hourly_volume.index, hourly_volume.values, linewidth=1, color='red', alpha=0.7)
    ax2.set_title(f'{case_slug.title()} - Volume Horário de Tweets', fontsize=16, fontweight='bold')
    ax2.set_xlabel('Data/Hora')
    ax2.set_ylabel('Número de Tweets')
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Volume temporal salvo: {output_path}")

def plot_peak_metrics(df: pd.DataFrame, output_path: Path, case_slug: str) -> None:
    """Plota métricas de pico (pico/mediana, pico/P90)."""
    if len(df) == 0:
        logger.warning(f"Sem dados para plotar métricas de pico para {case_slug}")
        return
    
    df_temp = df.copy()
    df_temp['created_at'] = pd.to_datetime(df_temp['created_at'])
    df_temp = df_temp.set_index('created_at')
    
    # Calcular métricas
    daily_volume = df_temp.resample('D').size()
    hourly_volume = df_temp.resample('H').size()
    
    peak_daily = daily_volume.max()
    median_daily = daily_volume.median()
    p90_daily = daily_volume.quantile(0.9)
    
    peak_hourly = hourly_volume.max()
    median_hourly = hourly_volume.median()
    p90_hourly = hourly_volume.quantile(0.9)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(19.2, 10.8))
    
    # Pico/Mediana diário
    peak_median_daily = peak_daily / median_daily if median_daily > 0 else np.nan
    ax1.bar(['Pico/Mediana (Dia)'], [peak_median_daily], color='blue', alpha=0.7)
    ax1.set_title(f'Pico/Mediana Diário: {peak_median_daily:.2f}')
    ax1.set_ylabel('Razão')
    
    # Pico/P90 diário
    peak_p90_daily = peak_daily / p90_daily if p90_daily > 0 else np.nan
    ax2.bar(['Pico/P90 (Dia)'], [peak_p90_daily], color='green', alpha=0.7)
    ax2.set_title(f'Pico/P90 Diário: {peak_p90_daily:.2f}')
    ax2.set_ylabel('Razão')
    
    # Pico/Mediana horário
    peak_median_hourly = peak_hourly / median_hourly if median_hourly > 0 else np.nan
    ax3.bar(['Pico/Mediana (Hora)'], [peak_median_hourly], color='orange', alpha=0.7)
    ax3.set_title(f'Pico/Mediana Horário: {peak_median_hourly:.2f}')
    ax3.set_ylabel('Razão')
    
    # Pico/P90 horário
    peak_p90_hourly = peak_hourly / p90_hourly if p90_hourly > 0 else np.nan
    ax4.bar(['Pico/P90 (Hora)'], [peak_p90_hourly], color='red', alpha=0.7)
    ax4.set_title(f'Pico/P90 Horário: {peak_p90_hourly:.2f}')
    ax4.set_ylabel('Razão')
    
    plt.suptitle(f'{case_slug.title()} - Métricas de Pico', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Métricas de pico salvas: {output_path}")

def plot_inequality_metrics(df: pd.DataFrame, output_path: Path, case_slug: str) -> None:
    """Plota métricas de desigualdade (Gini, HHI)."""
    if len(df) == 0:
        logger.warning(f"Sem dados para plotar métricas de desigualdade para {case_slug}")
        return
    
    # Calcular métricas
    tweet_engagement = df['engagement'].values
    user_engagement = df.groupby('author')['engagement'].sum().values
    
    gini_tweet = calculate_gini(tweet_engagement)
    hhi_tweet = calculate_hhi(tweet_engagement)
    gini_user = calculate_gini(user_engagement)
    hhi_user = calculate_hhi(user_engagement)
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(19.2, 10.8))
    
    # Gini por tweet
    ax1.bar(['Gini Tweet'], [gini_tweet], color='blue', alpha=0.7)
    ax1.set_title(f'Gini do Engajamento por Tweet: {gini_tweet:.3f}')
    ax1.set_ylabel('Coeficiente de Gini')
    ax1.set_ylim(0, 1)
    
    # HHI por tweet
    ax2.bar(['HHI Tweet'], [hhi_tweet], color='green', alpha=0.7)
    ax2.set_title(f'HHI do Engajamento por Tweet: {hhi_tweet:.3f}')
    ax2.set_ylabel('Índice HHI')
    ax2.set_ylim(0, 1)
    
    # Gini por usuário
    ax3.bar(['Gini Usuário'], [gini_user], color='orange', alpha=0.7)
    ax3.set_title(f'Gini do Engajamento por Usuário: {gini_user:.3f}')
    ax3.set_ylabel('Coeficiente de Gini')
    ax3.set_ylim(0, 1)
    
    # HHI por usuário
    ax4.bar(['HHI Usuário'], [hhi_user], color='red', alpha=0.7)
    ax4.set_title(f'HHI do Engajamento por Usuário: {hhi_user:.3f}')
    ax4.set_ylabel('Índice HHI')
    ax4.set_ylim(0, 1)
    
    plt.suptitle(f'{case_slug.title()} - Métricas de Desigualdade', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Métricas de desigualdade salvas: {output_path}")

def plot_top_shares(df: pd.DataFrame, output_path: Path, case_slug: str) -> None:
    """Plota shares dos top usuários."""
    if len(df) == 0:
        logger.warning(f"Sem dados para plotar top shares para {case_slug}")
        return
    
    user_engagement = df.groupby('author')['engagement'].sum()
    total_engagement = user_engagement.sum()
    
    if total_engagement == 0:
        logger.warning(f"Engajamento total zero para {case_slug}")
        return
    
    # Calcular shares
    top1_share = user_engagement.max() / total_engagement * 100
    top5_share = user_engagement.nlargest(5).sum() / total_engagement * 100
    top10_share = user_engagement.nlargest(10).sum() / total_engagement * 100
    
    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    
    categories = ['Top 1', 'Top 5', 'Top 10']
    shares = [top1_share, top5_share, top10_share]
    colors = ['red', 'orange', 'blue']
    
    bars = ax.bar(categories, shares, color=colors, alpha=0.7)
    ax.set_title(f'{case_slug.title()} - Concentração de Engajamento', fontsize=16, fontweight='bold')
    ax.set_ylabel('Share do Engajamento Total (%)')
    ax.set_ylim(0, 100)
    
    # Adicionar valores nas barras
    for bar, share in zip(bars, shares):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{share:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Top shares salvo: {output_path}")

def plot_top_mentions(df: pd.DataFrame, output_path: Path, case_slug: str, top_n: int = 20) -> None:
    """Plota top N usuários mais mencionados."""
    if len(df) == 0:
        logger.warning(f"Sem dados para plotar top menções para {case_slug}")
        return
    
    # Expandir menções
    all_mentions = []
    for mentions in df['mentions'].dropna():
        all_mentions.extend(mentions)
    
    if not all_mentions:
        logger.warning(f"Nenhuma menção encontrada para {case_slug}")
        return
    
    # Contar menções
    mention_counts = pd.Series(all_mentions).value_counts().head(top_n)
    
    if len(mention_counts) == 0:
        logger.warning(f"Nenhuma menção válida para {case_slug}")
        return
    
    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    
    # Plotar barras horizontais
    y_pos = np.arange(len(mention_counts))
    bars = ax.barh(y_pos, mention_counts.values, alpha=0.7, color='purple')
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(mention_counts.index)
    ax.set_xlabel('Número de Menções')
    ax.set_title(f'{case_slug.title()} - Top {top_n} Usuários Mais Mencionados', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Adicionar valores nas barras
    for i, (bar, count) in enumerate(zip(bars, mention_counts.values)):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                f'{count}', ha='left', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Top menções salvo: {output_path}")

def plot_engagement_distribution(df: pd.DataFrame, output_path: Path, case_slug: str) -> None:
    """Plota distribuição de engajamento (histograma + CCDF log-log)."""
    if len(df) == 0:
        logger.warning(f"Sem dados para plotar distribuição de engajamento para {case_slug}")
        return
    
    engagement = df['engagement'].values
    engagement = engagement[engagement > 0]  # Remover zeros
    
    if len(engagement) == 0:
        logger.warning(f"Nenhum engajamento positivo para {case_slug}")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(19.2, 10.8))
    
    # Histograma
    ax1.hist(engagement, bins=50, alpha=0.7, color='blue', edgecolor='black')
    ax1.set_xlabel('Engajamento')
    ax1.set_ylabel('Frequência')
    ax1.set_title('Distribuição de Engajamento')
    ax1.set_yscale('log')
    ax1.grid(True, alpha=0.3)
    
    # CCDF log-log
    sorted_engagement = np.sort(engagement)[::-1]
    n = len(sorted_engagement)
    ccdf = np.arange(1, n + 1) / n
    
    ax2.loglog(sorted_engagement, ccdf, 'o-', markersize=3, alpha=0.7, color='red')
    ax2.set_xlabel('Engajamento')
    ax2.set_ylabel('CCDF (Complementary CDF)')
    ax2.set_title('CCDF Log-Log do Engajamento')
    ax2.grid(True, alpha=0.3)
    
    plt.suptitle(f'{case_slug.title()} - Distribuição de Engajamento', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Distribuição de engajamento salva: {output_path}")

def plot_network_preview(G, output_path: Path, case_slug: str, max_nodes: int = 100) -> None:
    """Plota preview da rede (apenas top nós por grau)."""
    if G.number_of_nodes() == 0:
        logger.warning(f"Grafo vazio para {case_slug}")
        return
    
    # Filtrar para top nós por grau
    degrees = dict(G.degree())
    if len(degrees) > max_nodes:
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
        top_node_set = set([node for node, _ in top_nodes])
        G_filtered = G.subgraph(top_node_set)
        logger.info(f"Filtrando grafo para top {max_nodes} nós por grau")
    else:
        G_filtered = G
    
    if G_filtered.number_of_nodes() == 0:
        logger.warning(f"Grafo filtrado vazio para {case_slug}")
        return
    
    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    
    # Layout spring
    pos = nx.spring_layout(G_filtered, k=1, iterations=50, seed=42)
    
    # Plotar nós
    node_sizes = [degrees[node] * 10 for node in G_filtered.nodes()]
    nx.draw_networkx_nodes(G_filtered, pos, node_size=node_sizes, 
                          node_color='lightblue', alpha=0.7, ax=ax)
    
    # Plotar arestas
    nx.draw_networkx_edges(G_filtered, pos, alpha=0.5, edge_color='gray', ax=ax)
    
    # Plotar labels apenas para nós com grau alto
    high_degree_nodes = [node for node in G_filtered.nodes() if degrees[node] > np.percentile(list(degrees.values()), 90)]
    labels = {node: node for node in high_degree_nodes}
    nx.draw_networkx_labels(G_filtered, pos, labels, font_size=8, ax=ax)
    
    ax.set_title(f'{case_slug.title()} - Preview da Rede de Menções\n(Top {G_filtered.number_of_nodes()} nós por grau)', 
                fontsize=16, fontweight='bold')
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Preview da rede salvo: {output_path}")

def plot_comparative_metrics(cases_data: Dict, output_path: Path, metric_name: str) -> None:
    """Plota métricas comparativas entre casos."""
    if not cases_data:
        logger.warning("Sem dados para plotar métricas comparativas")
        return
    
    case_names = list(cases_data.keys())
    values = [cases_data[case].get(metric_name, 0) for case in case_names]
    
    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    
    bars = ax.bar(case_names, values, alpha=0.7, color=['blue', 'red', 'green', 'orange'][:len(case_names)])
    ax.set_title(f'Comparação de {metric_name.title()} entre Casos', fontsize=16, fontweight='bold')
    ax.set_ylabel(metric_name.title())
    ax.grid(True, alpha=0.3, axis='y')
    
    # Adicionar valores nas barras
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + max(values) * 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Métricas comparativas salvas: {output_path}")

def plot_temporal_overlay(cases_data: Dict, output_path: Path) -> None:
    """Plota sobreposição temporal normalizada entre casos."""
    if not cases_data:
        logger.warning("Sem dados para plotar sobreposição temporal")
        return
    
    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    
    colors = ['blue', 'red', 'green', 'orange']
    
    for i, (case_name, case_df) in enumerate(cases_data.items()):
        if len(case_df) == 0:
            continue
        
        # Preparar dados temporais
        df_temp = case_df.copy()
        df_temp['created_at'] = pd.to_datetime(df_temp['created_at'])
        df_temp = df_temp.set_index('created_at')
        
        # Volume diário
        daily_volume = df_temp.resample('D').size()
        
        # Normalizar por máximo
        if len(daily_volume) > 0:
            normalized_volume = daily_volume / daily_volume.max()
            ax.plot(daily_volume.index, normalized_volume.values, 
                   label=case_name.title(), linewidth=2, color=colors[i % len(colors)])
    
    ax.set_title('Volume Temporal Normalizado - Comparação entre Casos', fontsize=16, fontweight='bold')
    ax.set_xlabel('Data')
    ax.set_ylabel('Volume Normalizado (0-1)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    plt.close()
    logger.info(f"Sobreposição temporal salva: {output_path}")

# Funções auxiliares
def calculate_gini(values: np.ndarray) -> float:
    """Calcula coeficiente de Gini."""
    if len(values) == 0:
        return np.nan
    
    values = values[values > 0]
    if len(values) == 0:
        return 0.0
    
    values = np.sort(values)
    n = len(values)
    cumsum = np.cumsum(values)
    
    gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0
    return gini

def calculate_hhi(values: np.ndarray) -> float:
    """Calcula índice Herfindahl-Hirschman."""
    if len(values) == 0:
        return np.nan
    
    total = np.sum(values)
    if total == 0:
        return 0.0
    
    fractions = values / total
    hhi = np.sum(fractions ** 2)
    return hhi

if __name__ == "__main__":
    print("Módulo de plots carregado")

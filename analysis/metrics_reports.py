#!/usr/bin/env python3
"""
Cálculo de métricas de rede e análise estatística para casos de cancelamento.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from scipy import stats

logger = logging.getLogger(__name__)

def calculate_gini(values: np.ndarray) -> float:
    """Calcula coeficiente de Gini."""
    if len(values) == 0:
        return np.nan
    
    # Remover zeros e ordenar
    values = values[values > 0]
    if len(values) == 0:
        return 0.0
    
    values = np.sort(values)
    n = len(values)
    cumsum = np.cumsum(values)
    
    # Fórmula de Gini
    gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0
    return gini

def calculate_hhi(values: np.ndarray) -> float:
    """Calcula índice Herfindahl-Hirschman."""
    if len(values) == 0:
        return np.nan
    
    total = np.sum(values)
    if total == 0:
        return 0.0
    
    # Calcular frações
    fractions = values / total
    
    # HHI = soma dos quadrados das frações
    hhi = np.sum(fractions ** 2)
    return hhi

def calculate_top_shares(values: np.ndarray, top_k: List[int] = [1, 5, 10]) -> Dict[int, float]:
    """Calcula share dos top K elementos."""
    if len(values) == 0:
        return {k: 0.0 for k in top_k}
    
    total = np.sum(values)
    if total == 0:
        return {k: 0.0 for k in top_k}
    
    # Ordenar em ordem decrescente
    sorted_values = np.sort(values)[::-1]
    
    shares = {}
    for k in top_k:
        if k <= len(sorted_values):
            top_k_sum = np.sum(sorted_values[:k])
            shares[k] = top_k_sum / total
        else:
            shares[k] = 1.0  # Se k >= len(values), share = 100%
    
    return shares

def calculate_peak_metrics(series: pd.Series, window: str = 'D') -> Dict[str, float]:
    """Calcula métricas de pico (pico/mediana, pico/P90)."""
    if len(series) == 0:
        return {
            'peak_median': np.nan,
            'peak_p90': np.nan
        }
    
    # Agregar por janela temporal
    if window == 'D':
        aggregated = series.resample('D').sum()
    elif window == 'H':
        aggregated = series.resample('H').sum()
    else:
        aggregated = series
    
    if len(aggregated) == 0:
        return {
            'peak_median': np.nan,
            'peak_p90': np.nan
        }
    
    peak = aggregated.max()
    median = aggregated.median()
    p90 = aggregated.quantile(0.9)
    
    peak_median = peak / median if median > 0 else np.nan
    peak_p90 = peak / p90 if p90 > 0 else np.nan
    
    return {
        'peak_median': peak_median,
        'peak_p90': peak_p90
    }

def calculate_engagement_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Calcula métricas de engajamento por tweet e por usuário."""
    if len(df) == 0:
        return {
            'gini_engagement_tweet': np.nan,
            'hhi_engagement_tweet': np.nan,
            'gini_engagement_user': np.nan,
            'hhi_engagement_user': np.nan,
            'top1_share': 0.0,
            'top5_share': 0.0,
            'top10_share': 0.0
        }
    
    # Métricas por tweet
    tweet_engagement = df['engagement'].values
    gini_tweet = calculate_gini(tweet_engagement)
    hhi_tweet = calculate_hhi(tweet_engagement)
    
    # Métricas por usuário
    user_engagement = df.groupby('author')['engagement'].sum().values
    gini_user = calculate_gini(user_engagement)
    hhi_user = calculate_hhi(user_engagement)
    
    # Top shares por usuário
    top_shares = calculate_top_shares(user_engagement)
    
    return {
        'gini_engagement_tweet': gini_tweet,
        'hhi_engagement_tweet': hhi_tweet,
        'gini_engagement_user': gini_user,
        'hhi_engagement_user': hhi_user,
        'top1_share': top_shares.get(1, 0.0),
        'top5_share': top_shares.get(5, 0.0),
        'top10_share': top_shares.get(10, 0.0)
    }

def calculate_temporal_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Calcula métricas temporais."""
    if len(df) == 0:
        return {
            'peak_median_day': np.nan,
            'peak_p90_day': np.nan,
            'peak_median_hour': np.nan,
            'peak_p90_hour': np.nan
        }
    
    # Criar série temporal
    df_temp = df.copy()
    df_temp['created_at'] = pd.to_datetime(df_temp['created_at'])
    df_temp = df_temp.set_index('created_at')
    
    # Volume por dia
    daily_volume = df_temp.resample('D').size()
    daily_metrics = calculate_peak_metrics(daily_volume, 'D')
    
    # Volume por hora
    hourly_volume = df_temp.resample('H').size()
    hourly_metrics = calculate_peak_metrics(hourly_volume, 'H')
    
    return {
        'peak_median_day': daily_metrics['peak_median'],
        'peak_p90_day': daily_metrics['peak_p90'],
        'peak_median_hour': hourly_metrics['peak_median'],
        'peak_p90_hour': hourly_metrics['peak_p90']
    }

def calculate_mention_metrics(df: pd.DataFrame) -> Dict[str, any]:
    """Calcula métricas de menções."""
    if len(df) == 0:
        return {
            'total_mentions': 0,
            'unique_mentioned_users': 0,
            'avg_mentions_per_tweet': 0.0,
            'top_mentioned_users': []
        }
    
    # Expandir menções
    all_mentions = []
    for mentions in df['mentions'].dropna():
        all_mentions.extend(mentions)
    
    if not all_mentions:
        return {
            'total_mentions': 0,
            'unique_mentioned_users': 0,
            'avg_mentions_per_tweet': 0.0,
            'top_mentioned_users': []
        }
    
    # Contar menções
    mention_counts = pd.Series(all_mentions).value_counts()
    
    return {
        'total_mentions': len(all_mentions),
        'unique_mentioned_users': len(mention_counts),
        'avg_mentions_per_tweet': len(all_mentions) / len(df),
        'top_mentioned_users': mention_counts.head(20).to_dict()
    }

def create_time_series_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Cria dados de série temporal para visualização."""
    if len(df) == 0:
        return pd.DataFrame(), pd.DataFrame()
    
    df_temp = df.copy()
    df_temp['created_at'] = pd.to_datetime(df_temp['created_at'])
    df_temp = df_temp.set_index('created_at')
    
    # Série diária
    daily_series = df_temp.resample('D').size().reset_index()
    daily_series.columns = ['date', 'volume']
    
    # Série horária
    hourly_series = df_temp.resample('H').size().reset_index()
    hourly_series.columns = ['timestamp', 'volume']
    
    return daily_series, hourly_series

def create_user_engagement_table(df: pd.DataFrame) -> pd.DataFrame:
    """Cria tabela de engajamento por usuário."""
    if len(df) == 0:
        return pd.DataFrame()
    
    user_stats = df.groupby('author').agg({
        'engagement': ['sum', 'count', 'mean'],
        'like_count': 'sum',
        'retweet_count': 'sum',
        'reply_count': 'sum',
        'quote_count': 'sum'
    }).round(2)
    
    # Flatten column names
    user_stats.columns = ['engagement_total', 'tweet_count', 'engagement_avg',
                         'likes_total', 'retweets_total', 'replies_total', 'quotes_total']
    
    # Calcular share
    total_engagement = user_stats['engagement_total'].sum()
    user_stats['share'] = (user_stats['engagement_total'] / total_engagement * 100).round(2)
    
    # Adicionar rank
    user_stats['rank'] = user_stats['engagement_total'].rank(ascending=False, method='min').astype(int)
    
    # Ordenar por engajamento
    user_stats = user_stats.sort_values('engagement_total', ascending=False)
    
    return user_stats.reset_index()

def create_mention_targets_table(df: pd.DataFrame) -> pd.DataFrame:
    """Cria tabela de usuários mais mencionados."""
    if len(df) == 0:
        return pd.DataFrame()
    
    # Expandir menções
    all_mentions = []
    for mentions in df['mentions'].dropna():
        all_mentions.extend(mentions)
    
    if not all_mentions:
        return pd.DataFrame()
    
    # Contar menções
    mention_counts = pd.Series(all_mentions).value_counts()
    
    # Calcular share
    total_mentions = mention_counts.sum()
    mention_df = pd.DataFrame({
        'target': mention_counts.index,
        'mentions': mention_counts.values,
        'share': (mention_counts.values / total_mentions * 100).round(2)
    })
    
    # Adicionar rank
    mention_df['rank'] = range(1, len(mention_df) + 1)
    
    return mention_df

def calculate_case_summary_metrics(df: pd.DataFrame, graph_metrics: Dict) -> Dict[str, any]:
    """Calcula métricas resumo para um caso."""
    if len(df) == 0:
        return {
            'total_volume': 0,
            'date_range': (None, None),
            'unique_users': 0,
            'peak_median_day': np.nan,
            'peak_p90_day': np.nan,
            'gini_engagement_tweet': np.nan,
            'gini_engagement_user': np.nan,
            'hhi_engagement_tweet': np.nan,
            'top1_share': 0.0,
            'top5_share': 0.0,
            'top10_share': 0.0,
            'in_degree_centralization': np.nan,
            'in_deg_target_max': 0,
            'modularity': np.nan
        }
    
    # Métricas básicas
    total_volume = len(df)
    unique_users = df['author'].nunique()
    
    # Range temporal
    dates = pd.to_datetime(df['created_at'])
    date_range = (dates.min(), dates.max())
    
    # Métricas de engajamento
    engagement_metrics = calculate_engagement_metrics(df)
    
    # Métricas temporais
    temporal_metrics = calculate_temporal_metrics(df)
    
    # Métricas de rede
    network_metrics = {
        'in_degree_centralization': graph_metrics.get('in_degree_centralization', np.nan),
        'in_deg_target_max': graph_metrics.get('in_deg_target_max', 0),
        'modularity': graph_metrics.get('modularity', np.nan)
    }
    
    return {
        'total_volume': total_volume,
        'date_range': date_range,
        'unique_users': unique_users,
        'peak_median_day': temporal_metrics['peak_median_day'],
        'peak_p90_day': temporal_metrics['peak_p90_day'],
        **engagement_metrics,
        **network_metrics
    }

if __name__ == "__main__":
    # Teste básico
    print("Módulo de métricas carregado")

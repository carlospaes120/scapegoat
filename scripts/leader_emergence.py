"""
Pipeline para análise de emergência de líderes em crises miméticas no Twitter.

Este módulo contém todas as funções necessárias para:
- Carregar dados de posts do Twitter (JSONL/CSV)
- Calcular atenção (menções, retweets, quotes, replies)
- Computar Top-1 e Top-5 shares ao longo do tempo
- Identificar líderes e ponto de emergência
- Gerar visualizações e estatísticas
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from datetime import datetime
import json


def load_data(paths: List[str]) -> pd.DataFrame:
    """
    Carrega dados de múltiplos arquivos JSONL ou CSV.
    
    Args:
        paths: Lista de caminhos para arquivos (JSONL ou CSV)
    
    Returns:
        DataFrame concatenado com todos os posts
    """
    dfs = []
    
    for path in paths:
        path_obj = Path(path)
        
        if not path_obj.exists():
            print(f"Aviso: arquivo {path} não encontrado, pulando...")
            continue
        
        if path_obj.suffix == '.jsonl':
            # Carregar JSONL
            records = []
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            if records:
                dfs.append(pd.DataFrame(records))
        
        elif path_obj.suffix == '.csv':
            # Carregar CSV
            df = pd.read_csv(path)
            dfs.append(df)
        
        else:
            print(f"Aviso: formato não suportado para {path}, pulando...")
    
    if not dfs:
        raise ValueError("Nenhum arquivo válido encontrado para carregar")
    
    df = pd.concat(dfs, ignore_index=True)
    
    # Normalizar nomes de colunas comuns
    df.columns = df.columns.str.lower()
    
    return df


def extract_mentions_from_text(text: str) -> List[str]:
    """
    Extrai menções de um texto usando regex.
    
    Args:
        text: Texto do post
    
    Returns:
        Lista de usernames mencionados (lowercase, sem @)
    """
    if pd.isna(text) or not isinstance(text, str):
        return []
    
    pattern = r'@([A-Za-z0-9_]{1,15})'
    mentions = re.findall(pattern, text)
    return [m.lower() for m in mentions]


def explode_attention_events(df: pd.DataFrame, count_rules: Dict[str, float]) -> pd.DataFrame:
    """
    Transforma cada post em eventos de atenção (quem recebeu atenção de quem).
    
    Args:
        df: DataFrame com posts
        count_rules: Dicionário com pesos {'mention': 1, 'retweet': 1, 'quote': 1, 'reply': 1}
    
    Returns:
        DataFrame com colunas [time, target_user, weight]
    """
    events = []
    
    for idx, row in df.iterrows():
        time = row.get('created_at')
        text = row.get('text', '')
        author = row.get('author', '')
        
        # Parse timestamp
        if isinstance(time, str):
            time = pd.to_datetime(time, utc=True, errors='coerce')
        
        if pd.isna(time):
            continue
        
        # 1. Menções no texto
        if count_rules.get('mention', 0) > 0:
            # Tentar campo estruturado primeiro
            mentions = row.get('mentions', None)
            
            # Verificar tipo antes de processar
            if mentions is None:
                # Extrair do texto
                mentions = extract_mentions_from_text(text)
            elif isinstance(mentions, list):
                # Já é lista, normalizar considerando dicionários
                normalized = []
                for m in mentions:
                    if isinstance(m, str):
                        normalized.append(m.lower().lstrip('@'))
                    elif isinstance(m, dict):
                        # Campo pode ser dicionário com username/screen_name
                        username = m.get('username') or m.get('screen_name') or m.get('user') or str(m.get('id_str', ''))
                        if username:
                            normalized.append(str(username).lower().lstrip('@'))
                    else:
                        normalized.append(str(m).lower().lstrip('@'))
                mentions = normalized
            elif isinstance(mentions, str):
                # Pode ser uma string JSON ou separada por vírgulas
                try:
                    mentions = json.loads(mentions)
                    if isinstance(mentions, list):
                        mentions = [m.lower().lstrip('@') if isinstance(m, str) else str(m).lower() for m in mentions]
                    else:
                        mentions = extract_mentions_from_text(text)
                except:
                    # Tentar separar por vírgulas
                    if ',' in mentions:
                        mentions = [m.strip().lower().lstrip('@') for m in mentions.split(',') if m.strip()]
                    else:
                        # Extrair do texto original
                        mentions = extract_mentions_from_text(text)
            elif pd.isna(mentions):
                # Campo existe mas é NaN
                mentions = extract_mentions_from_text(text)
            else:
                mentions = []
            
            for mention in mentions:
                if mention and mention != author.lower():
                    events.append({
                        'time': time,
                        'target_user': mention,
                        'weight': count_rules['mention']
                    })
        
        # 2. Retweet
        if count_rules.get('retweet', 0) > 0:
            rt_user = row.get('retweet_of') or row.get('retweeted_user')
            if rt_user and not pd.isna(rt_user):
                # Pode ser dict ou string
                if isinstance(rt_user, dict):
                    rt_user = rt_user.get('username') or rt_user.get('screen_name') or rt_user.get('user') or str(rt_user.get('id_str', ''))
                rt_user = str(rt_user).lower().lstrip('@')
                if rt_user and rt_user != author.lower():
                    events.append({
                        'time': time,
                        'target_user': rt_user,
                        'weight': count_rules['retweet']
                    })
        
        # 3. Quote
        if count_rules.get('quote', 0) > 0:
            qt_user = row.get('quoted_user')
            if qt_user and not pd.isna(qt_user):
                # Pode ser dict ou string
                if isinstance(qt_user, dict):
                    qt_user = qt_user.get('username') or qt_user.get('screen_name') or qt_user.get('user') or str(qt_user.get('id_str', ''))
                qt_user = str(qt_user).lower().lstrip('@')
                if qt_user and qt_user != author.lower():
                    events.append({
                        'time': time,
                        'target_user': qt_user,
                        'weight': count_rules['quote']
                    })
        
        # 4. Reply
        if count_rules.get('reply', 0) > 0:
            rp_user = row.get('reply_to') or row.get('in_reply_to_user')
            if rp_user and not pd.isna(rp_user):
                # Pode ser dict ou string
                if isinstance(rp_user, dict):
                    rp_user = rp_user.get('username') or rp_user.get('screen_name') or rp_user.get('user') or str(rp_user.get('id_str', ''))
                rp_user = str(rp_user).lower().lstrip('@')
                if rp_user and rp_user != author.lower():
                    events.append({
                        'time': time,
                        'target_user': rp_user,
                        'weight': count_rules['reply']
                    })
    
    events_df = pd.DataFrame(events)
    
    if events_df.empty:
        raise ValueError("Nenhum evento de atenção foi extraído dos dados")
    
    return events_df


def build_bins(events_df: pd.DataFrame, bin_hours: float, tz: str) -> pd.DataFrame:
    """
    Agrupa eventos de atenção em bins temporais.
    
    Args:
        events_df: DataFrame com eventos [time, target_user, weight]
        bin_hours: Tamanho do bin em horas
        tz: Timezone (ex: 'America/Sao_Paulo')
    
    Returns:
        DataFrame com bins agregados
    """
    df = events_df.copy()
    
    # Converter para timezone local
    df['time'] = pd.to_datetime(df['time']).dt.tz_convert(tz)
    df = df.set_index('time')
    
    # Agrupar por bin e usuário
    bins_df = df.groupby([
        pd.Grouper(freq=f"{bin_hours}H"),
        'target_user'
    ])['weight'].sum().reset_index()
    
    bins_df.columns = ['bin_start', 'user', 'attention']
    
    return bins_df


def compute_shares_per_bin(bins_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula Top-1 e Top-5 shares para cada bin temporal.
    
    Args:
        bins_df: DataFrame com [bin_start, user, attention]
    
    Returns:
        DataFrame com [bin_start, total_attention, top1_user, top1_share, top5_share]
    """
    results = []
    
    for bin_start, group in bins_df.groupby('bin_start'):
        total_attention = group['attention'].sum()
        
        if total_attention == 0:
            continue
        
        # Ordenar por atenção
        sorted_users = group.sort_values('attention', ascending=False)
        
        # Top-1
        top1_user = sorted_users.iloc[0]['user']
        top1_attention = sorted_users.iloc[0]['attention']
        top1_share = top1_attention / total_attention
        
        # Top-5
        top5_attention = sorted_users.head(5)['attention'].sum()
        top5_share = top5_attention / total_attention
        
        results.append({
            'bin_start': bin_start,
            'total_attention': total_attention,
            'top1_user': top1_user,
            'top1_share': top1_share,
            'top5_share': top5_share
        })
    
    ts_df = pd.DataFrame(results)
    ts_df = ts_df.sort_values('bin_start').reset_index(drop=True)
    
    return ts_df


def identify_leaders_at_peak(ts_df: pd.DataFrame, bins_df: pd.DataFrame, k: int = 5) -> List[str]:
    """
    Identifica os líderes (Top-k usuários no bin do pico).
    
    Args:
        ts_df: DataFrame com séries temporais
        bins_df: DataFrame com bins desagregados
        k: Número de líderes (default 5)
    
    Returns:
        Lista de usernames dos líderes
    """
    # Identificar bin do pico
    peak_idx = ts_df['total_attention'].idxmax()
    peak_bin = ts_df.loc[peak_idx, 'bin_start']
    
    # Pegar Top-k desse bin
    peak_users = bins_df[bins_df['bin_start'] == peak_bin].sort_values(
        'attention', ascending=False
    ).head(k)
    
    leaders = peak_users['user'].tolist()
    
    return leaders


def detect_emergence(ts_df: pd.DataFrame, pre_frac: float = 0.2, k_consec: int = 2) -> Optional[pd.Timestamp]:
    """
    Detecta o ponto de emergência do líder.
    
    Emergência = primeiro bin onde Top-1 share >= μ_pre + 2σ_pre por k bins consecutivos.
    
    Args:
        ts_df: DataFrame com séries temporais
        pre_frac: Fração inicial para baseline pré-crise
        k_consec: Janelas consecutivas necessárias
    
    Returns:
        Timestamp do ponto de emergência (ou None se não detectado)
    """
    if len(ts_df) == 0:
        return None
    
    # Calcular baseline na fase pré
    n_pre = max(1, int(len(ts_df) * pre_frac))
    pre_data = ts_df.head(n_pre)
    
    mu_pre = pre_data['top1_share'].mean()
    sigma_pre = pre_data['top1_share'].std()
    
    threshold = mu_pre + 2 * sigma_pre
    
    # Procurar k bins consecutivos acima do threshold
    above_threshold = (ts_df['top1_share'] >= threshold).astype(int)
    
    # Detectar sequências consecutivas
    for i in range(len(ts_df) - k_consec + 1):
        if above_threshold.iloc[i:i+k_consec].sum() == k_consec:
            return ts_df.loc[i, 'bin_start']
    
    return None


def phase_labels(ts_df: pd.DataFrame, t_emergence: Optional[pd.Timestamp], 
                 t_peak: pd.Timestamp) -> pd.Series:
    """
    Atribui labels de fase (pré/durante/pós) a cada bin.
    
    Args:
        ts_df: DataFrame com séries temporais
        t_emergence: Timestamp da emergência
        t_peak: Timestamp do pico
    
    Returns:
        Series com labels ['pre', 'during', 'post']
    """
    phases = pd.Series(index=ts_df.index, dtype=str)
    
    if t_emergence is None:
        # Se não detectou emergência, tudo antes do pico é "pré"
        t_emergence = t_peak
    
    for idx, row in ts_df.iterrows():
        t = row['bin_start']
        
        if t < t_emergence:
            phases[idx] = 'pre'
        elif t <= t_peak:
            phases[idx] = 'during'
        else:
            phases[idx] = 'post'
    
    return phases


def compute_leaders_share(ts_df: pd.DataFrame, bins_df: pd.DataFrame, 
                         leaders: List[str]) -> pd.Series:
    """
    Calcula o share agregado dos líderes em cada bin.
    
    Args:
        ts_df: DataFrame com séries temporais
        bins_df: DataFrame com bins desagregados
        leaders: Lista de usernames dos líderes
    
    Returns:
        Series com leaders_share para cada bin
    """
    leaders_share = []
    
    for bin_start in ts_df['bin_start']:
        bin_data = bins_df[bins_df['bin_start'] == bin_start]
        
        total_attention = bin_data['attention'].sum()
        
        if total_attention == 0:
            leaders_share.append(0.0)
            continue
        
        leaders_attention = bin_data[bin_data['user'].isin(leaders)]['attention'].sum()
        share = leaders_attention / total_attention
        
        leaders_share.append(share)
    
    return pd.Series(leaders_share, index=ts_df.index)


def bootstrap_ci(values: np.ndarray, n: int = 1000, stat: str = 'mean', 
                confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calcula intervalo de confiança via bootstrap.
    
    Args:
        values: Array com valores
        n: Número de amostras bootstrap
        stat: Estatística ('mean' ou 'median')
        confidence: Nível de confiança
    
    Returns:
        Tupla (limite_inferior, limite_superior)
    """
    if len(values) == 0:
        return (np.nan, np.nan)
    
    bootstrap_stats = []
    
    for _ in range(n):
        sample = np.random.choice(values, size=len(values), replace=True)
        
        if stat == 'mean':
            bootstrap_stats.append(np.mean(sample))
        elif stat == 'median':
            bootstrap_stats.append(np.median(sample))
    
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, alpha/2 * 100)
    upper = np.percentile(bootstrap_stats, (1 - alpha/2) * 100)
    
    return (lower, upper)


def welch_ttest(a: np.ndarray, b: np.ndarray) -> Tuple[float, float]:
    """
    Realiza teste t de Welch (variâncias desiguais).
    
    Args:
        a: Array do grupo A
        b: Array do grupo B
    
    Returns:
        Tupla (estatística_t, p_value)
    """
    if len(a) < 2 or len(b) < 2:
        return (np.nan, np.nan)
    
    t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
    
    return (t_stat, p_value)


def plot_shares(ts_df: pd.DataFrame, phases: pd.Series, 
               t_emergence: Optional[pd.Timestamp], t_peak: pd.Timestamp,
               case_name: str, outdir: Path):
    """
    Gera gráfico de Top-1 e Top-5 shares ao longo do tempo.
    
    Args:
        ts_df: DataFrame com séries temporais
        phases: Series com labels de fase
        t_emergence: Timestamp da emergência
        t_peak: Timestamp do pico
        case_name: Nome do caso
        outdir: Diretório de saída
    """
    fig, ax = plt.subplots(figsize=(14, 6))
    
    times = ts_df['bin_start']
    
    # Plotar linhas
    ax.plot(times, ts_df['top1_share'], label='Top-1 Share', 
            linewidth=2, color='#e74c3c', marker='o', markersize=3)
    ax.plot(times, ts_df['top5_share'], label='Top-5 Share', 
            linewidth=2, color='#3498db', marker='s', markersize=3)
    
    # Sombrear fases
    phase_colors = {'pre': '#ecf0f1', 'during': '#fff3cd', 'post': '#d4edda'}
    
    for phase_name, color in phase_colors.items():
        phase_bins = ts_df[phases == phase_name]
        if not phase_bins.empty:
            ax.axvspan(phase_bins['bin_start'].min(), 
                      phase_bins['bin_start'].max(), 
                      alpha=0.3, color=color, label=f'Fase: {phase_name.capitalize()}')
    
    # Linhas verticais
    if t_emergence is not None:
        ax.axvline(t_emergence, color='orange', linestyle='--', 
                  linewidth=2, label='Emergência')
    
    ax.axvline(t_peak, color='red', linestyle='-', 
              linewidth=2, label='Pico')
    
    # Formatação
    ax.set_xlabel('Tempo', fontsize=12, fontweight='bold')
    ax.set_ylabel('Share (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'{case_name}: Emergência do Líder (Top-1/Top-5 Share)', 
                fontsize=14, fontweight='bold')
    
    # Formatar eixo Y como percentual
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.0f}%'))
    
    # Formatar eixo X (datas)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3, linestyle=':')
    
    plt.tight_layout()
    
    # Salvar
    outdir.mkdir(parents=True, exist_ok=True)
    fig.savefig(outdir / f'leader_emergence_{case_name}.png', dpi=300, bbox_inches='tight')
    fig.savefig(outdir / f'leader_emergence_{case_name}.svg', bbox_inches='tight')
    plt.close(fig)


def plot_leaders_attention(ts_df: pd.DataFrame, bins_df: pd.DataFrame,
                          leaders: List[str], phases: pd.Series,
                          t_peak: pd.Timestamp, case_name: str, outdir: Path):
    """
    Gera gráfico de atenção dos líderes ao longo do tempo.
    
    Args:
        ts_df: DataFrame com séries temporais
        bins_df: DataFrame com bins desagregados
        leaders: Lista de líderes
        phases: Series com labels de fase
        t_peak: Timestamp do pico
        case_name: Nome do caso
        outdir: Diretório de saída
    """
    # Calcular atenção dos líderes
    leaders_attention = []
    
    for bin_start in ts_df['bin_start']:
        bin_data = bins_df[bins_df['bin_start'] == bin_start]
        leaders_attn = bin_data[bin_data['user'].isin(leaders)]['attention'].sum()
        leaders_attention.append(leaders_attn)
    
    leaders_share = compute_leaders_share(ts_df, bins_df, leaders)
    
    # Gráfico 1: Atenção absoluta
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    times = ts_df['bin_start']
    
    # Subplot 1: Atenção absoluta
    ax1_twin = ax1.twinx()
    
    ax1.plot(times, leaders_attention, label='Atenção dos Líderes', 
            linewidth=2, color='#9b59b6', marker='o', markersize=3)
    ax1_twin.plot(times, ts_df['total_attention'], label='Atenção Total', 
                 linewidth=2, color='#95a5a6', marker='s', markersize=3, alpha=0.6)
    
    ax1.axvline(t_peak, color='red', linestyle='-', linewidth=2, label='Pico')
    
    ax1.set_xlabel('Tempo', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Atenção dos Líderes', fontsize=12, fontweight='bold', color='#9b59b6')
    ax1_twin.set_ylabel('Atenção Total', fontsize=12, fontweight='bold', color='#95a5a6')
    ax1.set_title(f'{case_name}: Atenção dos Líderes vs. Total', 
                 fontsize=14, fontweight='bold')
    
    ax1.tick_params(axis='y', labelcolor='#9b59b6')
    ax1_twin.tick_params(axis='y', labelcolor='#95a5a6')
    
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    ax1.grid(True, alpha=0.3, linestyle=':')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='best', fontsize=10)
    
    # Subplot 2: Leaders share
    ax2.plot(times, leaders_share, label='Leaders Share', 
            linewidth=2, color='#16a085', marker='o', markersize=3)
    
    # Sombrear fases
    phase_colors = {'pre': '#ecf0f1', 'during': '#fff3cd', 'post': '#d4edda'}
    
    for phase_name, color in phase_colors.items():
        phase_bins = ts_df[phases == phase_name]
        if not phase_bins.empty:
            ax2.axvspan(phase_bins['bin_start'].min(), 
                       phase_bins['bin_start'].max(), 
                       alpha=0.3, color=color, label=f'Fase: {phase_name.capitalize()}')
    
    ax2.axvline(t_peak, color='red', linestyle='-', linewidth=2, label='Pico')
    
    ax2.set_xlabel('Tempo', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Leaders Share (%)', fontsize=12, fontweight='bold')
    ax2.set_title(f'{case_name}: Share Agregado dos Líderes', 
                 fontsize=14, fontweight='bold')
    
    ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y*100:.0f}%'))
    
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle=':')
    
    plt.tight_layout()
    
    # Salvar
    fig.savefig(outdir / f'leaders_attention_{case_name}.png', dpi=300, bbox_inches='tight')
    fig.savefig(outdir / f'leaders_attention_{case_name}.svg', bbox_inches='tight')
    plt.close(fig)


def export_tables(ts_df: pd.DataFrame, bins_df: pd.DataFrame, 
                 leaders: List[str], phases: pd.Series,
                 t_emergence: Optional[pd.Timestamp], t_peak: pd.Timestamp,
                 case_name: str, outdir: Path):
    """
    Exporta tabelas CSV e arquivo de estatísticas.
    
    Args:
        ts_df: DataFrame com séries temporais
        bins_df: DataFrame com bins desagregados
        leaders: Lista de líderes
        phases: Series com labels de fase
        t_emergence: Timestamp da emergência
        t_peak: Timestamp do pico
        case_name: Nome do caso
        outdir: Diretório de saída
    """
    outdir.mkdir(parents=True, exist_ok=True)
    
    # 1. Série temporal
    ts_export = ts_df.copy()
    ts_export['phase'] = phases
    ts_export['leaders_share'] = compute_leaders_share(ts_df, bins_df, leaders)
    ts_export['peak_flag'] = (ts_export['bin_start'] == t_peak).astype(int)
    
    ts_export.to_csv(outdir / f'timeseries_{case_name}.csv', index=False)
    
    # 2. Líderes
    peak_bin = ts_df[ts_df['bin_start'] == t_peak].iloc[0]
    peak_users = bins_df[bins_df['bin_start'] == t_peak].sort_values(
        'attention', ascending=False
    ).head(len(leaders))
    
    # Calcular atenção total de cada líder em todo o período
    total_attention_per_user = bins_df.groupby('user')['attention'].sum()
    
    leaders_df = pd.DataFrame({
        'rank': range(1, len(leaders) + 1),
        'user': leaders,
        'attention_at_peak': [peak_users[peak_users['user'] == u]['attention'].values[0] 
                             if u in peak_users['user'].values else 0 
                             for u in leaders],
        'total_attention': [total_attention_per_user.get(u, 0) for u in leaders]
    })
    
    leaders_df.to_csv(outdir / f'leaders_{case_name}.csv', index=False)
    
    # 3. Estatísticas
    stats_text = []
    stats_text.append(f"=== ANÁLISE DE EMERGÊNCIA DE LÍDERES: {case_name} ===\n")
    stats_text.append(f"Data de análise: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    stats_text.append("")
    
    # Timestamps importantes
    stats_text.append("MARCOS TEMPORAIS:")
    stats_text.append(f"  Início: {ts_df['bin_start'].min()}")
    stats_text.append(f"  Emergência: {t_emergence if t_emergence else 'NÃO DETECTADA'}")
    stats_text.append(f"  Pico: {t_peak}")
    stats_text.append(f"  Fim: {ts_df['bin_start'].max()}")
    stats_text.append("")
    
    # Líderes
    stats_text.append(f"LÍDERES IDENTIFICADOS (Top-5 no pico):")
    for idx, row in leaders_df.iterrows():
        stats_text.append(f"  {row['rank']}. @{row['user']} - "
                         f"Atenção no pico: {row['attention_at_peak']:.0f}, "
                         f"Total: {row['total_attention']:.0f}")
    stats_text.append("")
    
    # Estatísticas por fase
    ts_export['leaders_share_val'] = ts_export['leaders_share']
    
    for metric_name, metric_col in [('Top-1 Share', 'top1_share'), 
                                     ('Top-5 Share', 'top5_share'),
                                     ('Leaders Share', 'leaders_share_val')]:
        stats_text.append(f"MÉTRICA: {metric_name}")
        stats_text.append("-" * 60)
        
        phase_stats = {}
        
        for phase_name in ['pre', 'during', 'post']:
            phase_data = ts_export[ts_export['phase'] == phase_name][metric_col].values
            
            if len(phase_data) == 0:
                phase_stats[phase_name] = {
                    'mean': np.nan,
                    'ci': (np.nan, np.nan),
                    'n': 0
                }
                continue
            
            mean_val = np.mean(phase_data)
            ci_low, ci_high = bootstrap_ci(phase_data, n=1000)
            
            phase_stats[phase_name] = {
                'mean': mean_val,
                'ci': (ci_low, ci_high),
                'n': len(phase_data),
                'data': phase_data
            }
            
            stats_text.append(f"  {phase_name.upper()}: "
                            f"Média = {mean_val:.3f} ({mean_val*100:.1f}%), "
                            f"IC95% = [{ci_low:.3f}, {ci_high:.3f}], "
                            f"N = {len(phase_data)} bins")
        
        stats_text.append("")
        
        # Testes estatísticos
        stats_text.append("  TESTES ESTATÍSTICOS (Welch t-test):")
        
        # Pré vs Durante
        if phase_stats['pre']['n'] >= 2 and phase_stats['during']['n'] >= 2:
            t_stat, p_val = welch_ttest(phase_stats['pre']['data'], 
                                        phase_stats['during']['data'])
            stats_text.append(f"    Pré vs Durante: t = {t_stat:.3f}, p = {p_val:.4f} "
                            f"{'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'}")
        
        # Pré vs Pós
        if phase_stats['pre']['n'] >= 2 and phase_stats['post']['n'] >= 2:
            t_stat, p_val = welch_ttest(phase_stats['pre']['data'], 
                                        phase_stats['post']['data'])
            stats_text.append(f"    Pré vs Pós: t = {t_stat:.3f}, p = {p_val:.4f} "
                            f"{'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'}")
        
        # Durante vs Pós
        if phase_stats['during']['n'] >= 2 and phase_stats['post']['n'] >= 2:
            t_stat, p_val = welch_ttest(phase_stats['during']['data'], 
                                        phase_stats['post']['data'])
            stats_text.append(f"    Durante vs Pós: t = {t_stat:.3f}, p = {p_val:.4f} "
                            f"{'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else 'ns'}")
        
        stats_text.append("")
        stats_text.append("")
    
    # Legenda de significância
    stats_text.append("LEGENDA:")
    stats_text.append("  *** p < 0.001 (altamente significativo)")
    stats_text.append("  **  p < 0.01  (muito significativo)")
    stats_text.append("  *   p < 0.05  (significativo)")
    stats_text.append("  ns           (não significativo)")
    
    # Salvar
    with open(outdir / f'stats_{case_name}.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(stats_text))
    
    # Gerar README do caso (bônus)
    readme_text = []
    readme_text.append(f"# Análise de Emergência de Líderes: {case_name}")
    readme_text.append("")
    readme_text.append("## Resumo Executivo")
    readme_text.append("")
    readme_text.append(f"Esta análise identifica a emergência de líderes durante a crise mimética **{case_name}** no Twitter.")
    readme_text.append("")
    readme_text.append("### Líderes Identificados")
    readme_text.append("")
    readme_text.append("Os seguintes usuários constituíram o Top-5 no momento do pico de atenção:")
    readme_text.append("")
    for idx, row in leaders_df.iterrows():
        readme_text.append(f"{row['rank']}. **@{row['user']}** - "
                          f"Atenção no pico: {row['attention_at_peak']:.0f}")
    readme_text.append("")
    
    readme_text.append("### Momento de Emergência")
    readme_text.append("")
    if t_emergence:
        readme_text.append(f"A emergência do líder foi detectada em **{t_emergence}**, "
                          f"quando o Top-1 share ultrapassou μ + 2σ da fase pré-crise de forma sustentada.")
    else:
        readme_text.append("Não foi possível detectar um ponto claro de emergência com os critérios estabelecidos.")
    readme_text.append("")
    
    readme_text.append(f"O **pico de atenção** ocorreu em **{t_peak}**.")
    readme_text.append("")
    
    readme_text.append("### Concentração de Atenção")
    readme_text.append("")
    readme_text.append("A análise compara três fases:")
    readme_text.append("- **Pré**: antes da emergência do líder")
    readme_text.append("- **Durante**: da emergência até o pico (inclusive)")
    readme_text.append("- **Pós**: após o pico")
    readme_text.append("")
    
    # Resumir se houve aumento significativo
    ts_export_local = ts_export.copy()
    
    pre_top1 = ts_export_local[ts_export_local['phase'] == 'pre']['top1_share'].mean()
    during_top1 = ts_export_local[ts_export_local['phase'] == 'during']['top1_share'].mean()
    post_top1 = ts_export_local[ts_export_local['phase'] == 'post']['top1_share'].mean()
    
    readme_text.append("#### Top-1 Share")
    readme_text.append(f"- Pré: {pre_top1*100:.1f}%")
    readme_text.append(f"- Durante: {during_top1*100:.1f}% "
                      f"({'↑' if during_top1 > pre_top1 else '↓'} "
                      f"{abs(during_top1-pre_top1)*100:.1f} pp)")
    readme_text.append(f"- Pós: {post_top1*100:.1f}% "
                      f"({'↑' if post_top1 > pre_top1 else '↓'} "
                      f"{abs(post_top1-pre_top1)*100:.1f} pp)")
    readme_text.append("")
    
    pre_top5 = ts_export_local[ts_export_local['phase'] == 'pre']['top5_share'].mean()
    during_top5 = ts_export_local[ts_export_local['phase'] == 'during']['top5_share'].mean()
    post_top5 = ts_export_local[ts_export_local['phase'] == 'post']['top5_share'].mean()
    
    readme_text.append("#### Top-5 Share")
    readme_text.append(f"- Pré: {pre_top5*100:.1f}%")
    readme_text.append(f"- Durante: {during_top5*100:.1f}% "
                      f"({'↑' if during_top5 > pre_top5 else '↓'} "
                      f"{abs(during_top5-pre_top5)*100:.1f} pp)")
    readme_text.append(f"- Pós: {post_top5*100:.1f}% "
                      f"({'↑' if post_top5 > pre_top5 else '↓'} "
                      f"{abs(post_top5-pre_top5)*100:.1f} pp)")
    readme_text.append("")
    
    readme_text.append("### Conclusões")
    readme_text.append("")
    
    if during_top1 > pre_top1 * 1.2:
        readme_text.append(f"✓ Os líderes **aumentaram substancialmente** sua concentração de atenção "
                          f"durante a crise (+{(during_top1-pre_top1)*100:.1f} pp no Top-1 share).")
    elif during_top1 > pre_top1:
        readme_text.append(f"✓ Os líderes **aumentaram** sua concentração de atenção durante a crise.")
    else:
        readme_text.append(f"✗ Não houve aumento significativo na concentração de atenção durante a crise.")
    
    if post_top1 > pre_top1:
        readme_text.append(f"✓ A concentração de atenção nos líderes **persistiu após o pico**.")
    else:
        readme_text.append(f"✗ A concentração de atenção voltou aos níveis pré-crise após o pico.")
    
    readme_text.append("")
    readme_text.append("## Arquivos Gerados")
    readme_text.append("")
    readme_text.append(f"- `timeseries_{case_name}.csv`: Série temporal completa com todas as métricas")
    readme_text.append(f"- `leaders_{case_name}.csv`: Lista dos líderes identificados")
    readme_text.append(f"- `stats_{case_name}.txt`: Estatísticas detalhadas com testes de hipótese")
    readme_text.append(f"- `leader_emergence_{case_name}.png/svg`: Gráfico de emergência (Top-1/Top-5)")
    readme_text.append(f"- `leaders_attention_{case_name}.png/svg`: Gráfico de atenção dos líderes")
    readme_text.append("")
    readme_text.append("---")
    readme_text.append(f"*Gerado automaticamente em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    with open(outdir / 'README.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(readme_text))


def run_analysis(input_paths: List[str], case_name: str, 
                bin_hours: float = 1.0, tz: str = 'America/Sao_Paulo',
                count_rules: Optional[Dict[str, float]] = None,
                pre_frac: float = 0.2, k_consec: int = 2,
                output_dir: str = './outputs') -> Dict:
    """
    Executa pipeline completo de análise.
    
    Args:
        input_paths: Lista de caminhos para arquivos de dados
        case_name: Nome do caso
        bin_hours: Tamanho do bin em horas
        tz: Timezone
        count_rules: Pesos para cada tipo de atenção
        pre_frac: Fração inicial para baseline
        k_consec: Janelas consecutivas para emergência
        output_dir: Diretório base de saída
    
    Returns:
        Dicionário com resultados principais
    """
    if count_rules is None:
        count_rules = {'mention': 1, 'retweet': 1, 'quote': 1, 'reply': 1}
    
    outdir = Path(output_dir) / case_name
    
    print(f"\n{'='*60}")
    print(f"ANÁLISE DE EMERGÊNCIA DE LÍDERES: {case_name}")
    print(f"{'='*60}\n")
    
    # 1. Carregar dados
    print("1. Carregando dados...")
    df = load_data(input_paths)
    print(f"   ✓ {len(df):,} posts carregados")
    
    # 2. Extrair eventos de atenção
    print("\n2. Extraindo eventos de atenção...")
    events_df = explode_attention_events(df, count_rules)
    print(f"   ✓ {len(events_df):,} eventos de atenção extraídos")
    print(f"   ✓ {events_df['target_user'].nunique():,} usuários únicos receberam atenção")
    
    # 3. Construir bins temporais
    print(f"\n3. Construindo bins temporais ({bin_hours}h)...")
    bins_df = build_bins(events_df, bin_hours, tz)
    print(f"   ✓ {len(bins_df):,} registros (user × bin)")
    
    # 4. Calcular shares
    print("\n4. Calculando Top-1 e Top-5 shares...")
    ts_df = compute_shares_per_bin(bins_df)
    print(f"   ✓ {len(ts_df)} bins temporais")
    print(f"   ✓ Período: {ts_df['bin_start'].min()} → {ts_df['bin_start'].max()}")
    
    # 5. Identificar pico e líderes
    print("\n5. Identificando pico e líderes...")
    peak_idx = ts_df['total_attention'].idxmax()
    t_peak = ts_df.loc[peak_idx, 'bin_start']
    leaders = identify_leaders_at_peak(ts_df, bins_df, k=5)
    print(f"   ✓ Pico em: {t_peak}")
    print(f"   ✓ Líderes: {', '.join(['@' + l for l in leaders])}")
    
    # 6. Detectar emergência
    print("\n6. Detectando ponto de emergência...")
    t_emergence = detect_emergence(ts_df, pre_frac, k_consec)
    if t_emergence:
        print(f"   ✓ Emergência detectada em: {t_emergence}")
    else:
        print(f"   ⚠ Emergência não detectada (usando pico como referência)")
    
    # 7. Atribuir fases
    print("\n7. Atribuindo fases...")
    phases = phase_labels(ts_df, t_emergence, t_peak)
    n_pre = (phases == 'pre').sum()
    n_during = (phases == 'during').sum()
    n_post = (phases == 'post').sum()
    print(f"   ✓ Pré: {n_pre} bins | Durante: {n_during} bins | Pós: {n_post} bins")
    
    # 8. Gerar visualizações
    print("\n8. Gerando visualizações...")
    plot_shares(ts_df, phases, t_emergence, t_peak, case_name, outdir)
    print(f"   ✓ leader_emergence_{case_name}.png/svg")
    
    plot_leaders_attention(ts_df, bins_df, leaders, phases, t_peak, case_name, outdir)
    print(f"   ✓ leaders_attention_{case_name}.png/svg")
    
    # 9. Exportar tabelas
    print("\n9. Exportando tabelas e estatísticas...")
    export_tables(ts_df, bins_df, leaders, phases, t_emergence, t_peak, case_name, outdir)
    print(f"   ✓ timeseries_{case_name}.csv")
    print(f"   ✓ leaders_{case_name}.csv")
    print(f"   ✓ stats_{case_name}.txt")
    print(f"   ✓ README.md")
    
    print(f"\n{'='*60}")
    print(f"ANÁLISE CONCLUÍDA!")
    print(f"Resultados salvos em: {outdir.absolute()}")
    print(f"{'='*60}\n")
    
    return {
        'case_name': case_name,
        'n_posts': len(df),
        'n_events': len(events_df),
        'n_bins': len(ts_df),
        'leaders': leaders,
        't_emergence': t_emergence,
        't_peak': t_peak,
        'output_dir': str(outdir.absolute())
    }


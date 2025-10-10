#!/usr/bin/env python3
"""
analyze_simulation.py

Exemplo de análise dos dados exportados pelo modelo NetLogo Scapegoat.
Demonstra como carregar, processar e visualizar os dados de simulação.

Usage:
    python examples/analyze_simulation.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys

# Configurar estilo de gráficos
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


def load_data(data_dir):
    """Carrega todos os CSVs de dados."""
    print("📂 Carregando dados...")
    
    data = {}
    
    # Events
    events_path = data_dir / "events.csv"
    if events_path.exists():
        data['events'] = pd.read_csv(events_path)
        print(f"   ✅ events.csv: {len(data['events'])} eventos")
    else:
        print(f"   ⚠️  events.csv não encontrado")
        data['events'] = None
    
    # Timeseries
    timeseries_path = data_dir / "timeseries.csv"
    if timeseries_path.exists():
        data['timeseries'] = pd.read_csv(timeseries_path)
        print(f"   ✅ timeseries.csv: {len(data['timeseries'])} ticks")
    else:
        print(f"   ⚠️  timeseries.csv não encontrado")
        data['timeseries'] = None
    
    # Nodes
    nodes_path = data_dir / "nodes.csv"
    if nodes_path.exists():
        data['nodes'] = pd.read_csv(nodes_path)
        print(f"   ✅ nodes.csv: {len(data['nodes'])} nós")
    else:
        print(f"   ⚠️  nodes.csv não encontrado")
        data['nodes'] = None
    
    # Links
    links_path = data_dir / "links_snapshot.csv"
    if links_path.exists():
        data['links'] = pd.read_csv(links_path)
        print(f"   ✅ links_snapshot.csv: {len(data['links'])} arestas")
    else:
        print(f"   ⚠️  links_snapshot.csv não encontrado")
        data['links'] = None
    
    return data


def analyze_events(events_df):
    """Analisa distribuição de eventos."""
    print("\n" + "="*60)
    print("📊 ANÁLISE DE EVENTOS")
    print("="*60)
    
    if events_df is None or len(events_df) == 0:
        print("⚠️  Nenhum evento para analisar")
        return
    
    # Contagem por tipo
    print("\n🔢 Contagem de eventos por tipo:")
    event_counts = events_df['etype'].value_counts()
    for etype, count in event_counts.items():
        print(f"   {etype}: {count} ({count/len(events_df)*100:.1f}%)")
    
    # Distribuição temporal
    print("\n⏱️  Distribuição temporal:")
    print(f"   Primeiro evento: tick {events_df['tick'].min()}")
    print(f"   Último evento: tick {events_df['tick'].max()}")
    print(f"   Taxa média: {len(events_df) / (events_df['tick'].max() - events_df['tick'].min() + 1):.2f} eventos/tick")
    
    # Matriz de tipos (source_kind → target_kind)
    print("\n🎯 Matriz de acusações (source → target):")
    if 'source_kind' in events_df.columns and 'target_kind' in events_df.columns:
        matrix = pd.crosstab(events_df['source_kind'], events_df['target_kind'])
        print(matrix)
    
    # Plot: Evolução de eventos ao longo do tempo
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Subplot 1: Contagem por tipo
    event_counts.plot(kind='bar', ax=axes[0], color='steelblue')
    axes[0].set_title('Distribuição de Tipos de Evento', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Tipo de Evento')
    axes[0].set_ylabel('Contagem')
    axes[0].tick_params(axis='x', rotation=45)
    
    # Subplot 2: Eventos acumulados ao longo do tempo
    events_by_tick = events_df.groupby('tick').size().cumsum()
    axes[1].plot(events_by_tick.index, events_by_tick.values, linewidth=2, color='darkorange')
    axes[1].set_title('Eventos Acumulados ao Longo do Tempo', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Tick')
    axes[1].set_ylabel('Eventos Acumulados')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path("outputs/events_analysis.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n💾 Gráfico salvo em: {output_path}")
    plt.close()


def analyze_timeseries(ts_df):
    """Analisa séries temporais."""
    print("\n" + "="*60)
    print("📈 ANÁLISE DE SÉRIES TEMPORAIS")
    print("="*60)
    
    if ts_df is None or len(ts_df) == 0:
        print("⚠️  Nenhum dado de série temporal para analisar")
        return
    
    # Estatísticas resumidas
    print("\n📊 Estatísticas resumidas:")
    print(f"   Ticks simulados: {len(ts_df)}")
    print(f"   Média de agentes vivos: {ts_df['n_alive'].mean():.1f}")
    print(f"   Média de vítimas: {ts_df['n_victims'].mean():.1f} ({ts_df['pct_victims'].mean():.1f}%)")
    print(f"   Média de líderes: {ts_df['n_leaders'].mean():.1f}")
    print(f"   Saúde média geral: {ts_df['avggeneralhealth'].mean():.2f}")
    
    # Plot: Principais métricas temporais
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    
    # 1. População (n_alive, n_victims, n_leaders)
    axes[0, 0].plot(ts_df['tick'], ts_df['n_alive'], label='Total Vivo', linewidth=2, color='green')
    axes[0, 0].plot(ts_df['tick'], ts_df['n_victims'], label='Vítimas', linewidth=2, color='red')
    axes[0, 0].plot(ts_df['tick'], ts_df['n_leaders'], label='Líderes', linewidth=2, color='blue')
    axes[0, 0].set_title('Evolução da População', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Tick')
    axes[0, 0].set_ylabel('Número de Agentes')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Percentual de vítimas
    axes[0, 1].plot(ts_df['tick'], ts_df['pct_victims'], linewidth=2, color='darkred')
    axes[0, 1].set_title('Percentual de Vítimas', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Tick')
    axes[0, 1].set_ylabel('% de Vítimas')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Saúde média por grupo
    axes[1, 0].plot(ts_df['tick'], ts_df['avggeneralhealth'], label='Geral', linewidth=2)
    axes[1, 0].plot(ts_df['tick'], ts_df['avgleaderhealth'], label='Líderes', linewidth=2)
    axes[1, 0].plot(ts_df['tick'], ts_df['avgvictimhealth'], label='Vítimas', linewidth=2)
    axes[1, 0].set_title('Saúde Média por Grupo', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Tick')
    axes[1, 0].set_ylabel('Saúde Média')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Grau médio por grupo
    axes[1, 1].plot(ts_df['tick'], ts_df['avggenerallinkneighbors'], label='Geral', linewidth=2)
    axes[1, 1].plot(ts_df['tick'], ts_df['avgleaderlinkneighbors'], label='Líderes', linewidth=2)
    axes[1, 1].plot(ts_df['tick'], ts_df['avgvictimlinkneighbors'], label='Vítimas', linewidth=2)
    axes[1, 1].set_title('Grau Médio por Grupo', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Tick')
    axes[1, 1].set_ylabel('Grau Médio')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    # 5. Clustering Coefficient por grupo
    axes[2, 0].plot(ts_df['tick'], ts_df['avggeneralcc'], label='Geral', linewidth=2)
    axes[2, 0].plot(ts_df['tick'], ts_df['avgleadercc'], label='Líderes', linewidth=2)
    axes[2, 0].plot(ts_df['tick'], ts_df['avgvictimcc'], label='Vítimas', linewidth=2)
    axes[2, 0].set_title('Clustering Coefficient por Grupo', fontsize=12, fontweight='bold')
    axes[2, 0].set_xlabel('Tick')
    axes[2, 0].set_ylabel('CC Médio')
    axes[2, 0].legend()
    axes[2, 0].grid(True, alpha=0.3)
    
    # 6. Poluição e tempo de ritual
    ax6 = axes[2, 1]
    ax6.plot(ts_df['tick'], ts_df['pollution'], label='Poluição', linewidth=2, color='brown')
    ax6.set_xlabel('Tick')
    ax6.set_ylabel('Poluição (0-3)', color='brown')
    ax6.tick_params(axis='y', labelcolor='brown')
    ax6.grid(True, alpha=0.3)
    
    ax6_twin = ax6.twinx()
    ax6_twin.plot(ts_df['tick'], ts_df['ritualtime'], label='Ritual Time', linewidth=2, color='purple')
    ax6_twin.set_ylabel('Ritual Time', color='purple')
    ax6_twin.tick_params(axis='y', labelcolor='purple')
    
    ax6.set_title('Poluição e Tempo de Ritual', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    output_path = Path("outputs/timeseries_analysis.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n💾 Gráfico salvo em: {output_path}")
    plt.close()


def analyze_network(nodes_df, links_df):
    """Analisa snapshot da rede."""
    print("\n" + "="*60)
    print("🌐 ANÁLISE DE REDE (SNAPSHOT)")
    print("="*60)
    
    if nodes_df is None or links_df is None:
        print("⚠️  Dados de rede não disponíveis")
        return
    
    # Estatísticas de nós
    print("\n🔵 Estatísticas de nós:")
    print(f"   Total de nós: {len(nodes_df)}")
    print(f"   Saúde média: {nodes_df['health'].mean():.2f}")
    print(f"   Tensão média: {nodes_df['tension'].mean():.2f}")
    print(f"   Grau médio: {nodes_df['degree'].mean():.2f}")
    print(f"   CC médio: {nodes_df['cc_node'].mean():.3f}")
    
    # Distribuição de tipos
    print("\n🏷️  Distribuição de tipos:")
    kind_counts = nodes_df['kind'].value_counts()
    for kind, count in kind_counts.items():
        print(f"   {kind}: {count} ({count/len(nodes_df)*100:.1f}%)")
    
    # Estatísticas de arestas
    print(f"\n🔗 Total de arestas: {len(links_df)}")
    print(f"   Densidade: {2 * len(links_df) / (len(nodes_df) * (len(nodes_df) - 1)):.4f}")
    
    # Plot: Distribuições
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. Distribuição de tipos
    kind_counts.plot(kind='bar', ax=axes[0, 0], color='steelblue')
    axes[0, 0].set_title('Distribuição de Tipos de Nó', fontsize=12, fontweight='bold')
    axes[0, 0].set_xlabel('Tipo')
    axes[0, 0].set_ylabel('Contagem')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # 2. Distribuição de saúde
    axes[0, 1].hist(nodes_df['health'], bins=20, color='green', alpha=0.7, edgecolor='black')
    axes[0, 1].set_title('Distribuição de Saúde', fontsize=12, fontweight='bold')
    axes[0, 1].set_xlabel('Saúde')
    axes[0, 1].set_ylabel('Frequência')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Distribuição de grau
    axes[1, 0].hist(nodes_df['degree'], bins=range(0, int(nodes_df['degree'].max())+2), 
                    color='orange', alpha=0.7, edgecolor='black')
    axes[1, 0].set_title('Distribuição de Grau', fontsize=12, fontweight='bold')
    axes[1, 0].set_xlabel('Grau')
    axes[1, 0].set_ylabel('Frequência')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Scatter: Grau vs Saúde (colorido por tipo)
    for kind in nodes_df['kind'].unique():
        subset = nodes_df[nodes_df['kind'] == kind]
        axes[1, 1].scatter(subset['degree'], subset['health'], label=kind, alpha=0.6, s=50)
    axes[1, 1].set_title('Grau vs Saúde (por Tipo)', fontsize=12, fontweight='bold')
    axes[1, 1].set_xlabel('Grau')
    axes[1, 1].set_ylabel('Saúde')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = Path("outputs/network_analysis.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n💾 Gráfico salvo em: {output_path}")
    plt.close()


def main():
    """Executa análise completa."""
    print("="*60)
    print("🔬 ANÁLISE DE DADOS - MODELO SCAPEGOAT")
    print("="*60)
    
    # Carregar dados
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data = load_data(data_dir)
    
    # Analisar eventos
    if data['events'] is not None:
        analyze_events(data['events'])
    
    # Analisar séries temporais
    if data['timeseries'] is not None:
        analyze_timeseries(data['timeseries'])
    
    # Analisar rede
    if data['nodes'] is not None and data['links'] is not None:
        analyze_network(data['nodes'], data['links'])
    
    # Resumo final
    print("\n" + "="*60)
    print("✅ ANÁLISE CONCLUÍDA")
    print("="*60)
    print("\n💡 Os gráficos foram salvos em: outputs/")
    print("   - events_analysis.png")
    print("   - timeseries_analysis.png")
    print("   - network_analysis.png")


if __name__ == "__main__":
    main()


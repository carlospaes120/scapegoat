#!/usr/bin/env python3
"""
verify_data.py

Verifica a integridade dos arquivos CSV exportados pelo modelo NetLogo.
Útil para testar se a instrumentação está funcionando corretamente.

Usage:
    python tools/verify_data.py
"""

import pandas as pd
from pathlib import Path
import sys


def check_file_exists(filepath):
    """Verifica se um arquivo existe."""
    if not filepath.exists():
        print(f"❌ {filepath.name} NÃO encontrado em {filepath.parent}")
        return False
    print(f"✅ {filepath.name} encontrado")
    return True


def verify_events_csv(filepath):
    """Verifica events.csv."""
    print(f"\n📋 Verificando {filepath.name}...")
    
    if not filepath.exists():
        print(f"   ❌ Arquivo não existe. Execute a simulação primeiro.")
        return False
    
    try:
        df = pd.read_csv(filepath)
        print(f"   ✅ {len(df)} eventos carregados")
        
        # Verificar colunas esperadas
        expected_cols = ["tick", "source", "target", "etype", "source_kind", "target_kind", "weight"]
        missing = set(expected_cols) - set(df.columns)
        if missing:
            print(f"   ⚠️  Colunas faltando: {missing}")
            return False
        
        # Verificar tipos de evento
        if 'etype' in df.columns:
            event_counts = df['etype'].value_counts()
            print(f"   📊 Tipos de evento:")
            for etype, count in event_counts.items():
                print(f"      - {etype}: {count}")
        
        # Verificar se há eventos
        if len(df) == 0:
            print(f"   ⚠️  Nenhum evento registrado ainda. Execute a simulação por mais tempo.")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return False


def verify_timeseries_csv(filepath):
    """Verifica timeseries.csv."""
    print(f"\n📈 Verificando {filepath.name}...")
    
    if not filepath.exists():
        print(f"   ❌ Arquivo não existe. Execute a simulação primeiro.")
        return False
    
    try:
        df = pd.read_csv(filepath)
        print(f"   ✅ {len(df)} registros de tick carregados")
        
        # Verificar colunas esperadas
        expected_cols = [
            "tick", "n_alive", "n_leaders", "n_victims", "pct_victims",
            "avggeneralhealth", "avgleaderhealth", "avgvictimhealth",
            "avggenerallinkneighbors", "avgvictimlinkneighbors", "avgleaderlinkneighbors",
            "avggeneralcc", "avgleadercc", "avgvictimcc",
            "pollution", "timetoritual", "ritualtime"
        ]
        missing = set(expected_cols) - set(df.columns)
        if missing:
            print(f"   ⚠️  Colunas faltando: {missing}")
            return False
        
        # Estatísticas básicas
        if len(df) > 0:
            print(f"   📊 Resumo:")
            print(f"      - Tick inicial: {df['tick'].min()}")
            print(f"      - Tick final: {df['tick'].max()}")
            print(f"      - Média de agentes vivos: {df['n_alive'].mean():.1f}")
            print(f"      - Média de vítimas: {df['n_victims'].mean():.1f}")
            print(f"      - Média de líderes: {df['n_leaders'].mean():.1f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return False


def verify_nodes_csv(filepath):
    """Verifica nodes.csv."""
    print(f"\n🔵 Verificando {filepath.name}...")
    
    if not filepath.exists():
        print(f"   ⚠️  Arquivo não existe. Clique em 'Export nodes snapshot' no NetLogo.")
        return False
    
    try:
        df = pd.read_csv(filepath)
        print(f"   ✅ {len(df)} nós carregados")
        
        # Verificar colunas esperadas
        expected_cols = ["id", "kind", "health", "tension", "cc_node", "degree"]
        missing = set(expected_cols) - set(df.columns)
        if missing:
            print(f"   ⚠️  Colunas faltando: {missing}")
            return False
        
        # Distribuição de tipos
        if 'kind' in df.columns:
            kind_counts = df['kind'].value_counts()
            print(f"   📊 Tipos de nós:")
            for kind, count in kind_counts.items():
                print(f"      - {kind}: {count}")
        
        # Estatísticas de saúde
        if 'health' in df.columns:
            print(f"   💚 Saúde média: {df['health'].mean():.2f}")
        
        # Estatísticas de grau
        if 'degree' in df.columns:
            print(f"   🔗 Grau médio: {df['degree'].mean():.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return False


def verify_links_csv(filepath):
    """Verifica links_snapshot.csv."""
    print(f"\n🔗 Verificando {filepath.name}...")
    
    if not filepath.exists():
        print(f"   ⚠️  Arquivo não existe. Clique em 'Export links snapshot' no NetLogo.")
        return False
    
    try:
        df = pd.read_csv(filepath)
        print(f"   ✅ {len(df)} arestas carregadas")
        
        # Verificar colunas esperadas
        expected_cols = ["source", "target"]
        missing = set(expected_cols) - set(df.columns)
        if missing:
            print(f"   ⚠️  Colunas faltando: {missing}")
            return False
        
        # Verificar se há arestas
        if len(df) == 0:
            print(f"   ⚠️  Nenhuma aresta registrada. Verifique a rede no NetLogo.")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return False


def verify_gexf(filepath):
    """Verifica se GEXF pode ser lido pelo NetworkX."""
    print(f"\n🌐 Verificando {filepath.name}...")
    
    if not filepath.exists():
        print(f"   ⚠️  Arquivo não existe. Execute 'python tools/make_gexf.py' primeiro.")
        return False
    
    try:
        import networkx as nx
        G = nx.read_gexf(filepath)
        print(f"   ✅ Grafo carregado com sucesso")
        print(f"   📊 {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
        
        # Verificar atributos de nós
        if G.number_of_nodes() > 0:
            sample_node = list(G.nodes())[0]
            attrs = G.nodes[sample_node]
            print(f"   🏷️  Atributos de nó: {list(attrs.keys())}")
        
        return True
        
    except ImportError:
        print(f"   ⚠️  NetworkX não instalado. Instale com: pip install networkx")
        return False
    except Exception as e:
        print(f"   ❌ Erro ao ler arquivo: {e}")
        return False


def main():
    """Executa todas as verificações."""
    print("=" * 60)
    print("🔍 Verificação de Integridade dos Dados - Modelo Scapegoat")
    print("=" * 60)
    
    # Caminhos
    data_dir = Path(__file__).resolve().parents[1] / "data"
    
    events_csv = data_dir / "events.csv"
    timeseries_csv = data_dir / "timeseries.csv"
    nodes_csv = data_dir / "nodes.csv"
    links_csv = data_dir / "links_snapshot.csv"
    gexf_file = data_dir / "network.gexf"
    
    # Verificar arquivos essenciais (devem existir sempre)
    print("\n📂 Verificando existência de arquivos...")
    events_exists = check_file_exists(events_csv)
    timeseries_exists = check_file_exists(timeseries_csv)
    
    # Verificar snapshots (opcionais)
    nodes_exists = check_file_exists(nodes_csv)
    links_exists = check_file_exists(links_csv)
    gexf_exists = check_file_exists(gexf_file)
    
    # Verificar conteúdo
    results = []
    
    if events_exists:
        results.append(verify_events_csv(events_csv))
    
    if timeseries_exists:
        results.append(verify_timeseries_csv(timeseries_csv))
    
    if nodes_exists:
        results.append(verify_nodes_csv(nodes_csv))
    
    if links_exists:
        results.append(verify_links_csv(links_csv))
    
    if gexf_exists:
        results.append(verify_gexf(gexf_file))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO")
    print("=" * 60)
    
    if all(results):
        print("✅ Todos os arquivos verificados estão OK!")
        print("\n💡 Próximos passos:")
        if not gexf_exists:
            print("   1. Execute: python tools/make_gexf.py")
            print("   2. Importe data/network.gexf no Gephi")
        else:
            print("   1. Importe data/network.gexf no Gephi")
            print("   2. Analise os dados em Python com pandas")
        sys.exit(0)
    else:
        print("⚠️  Alguns arquivos têm problemas. Veja detalhes acima.")
        print("\n💡 Ações recomendadas:")
        if not events_exists or not timeseries_exists:
            print("   1. Execute 'setup' no NetLogo")
            print("   2. Execute 'go' por pelo menos 50 ticks")
        if not nodes_exists or not links_exists:
            print("   3. Clique em 'Export nodes snapshot' no NetLogo")
            print("   4. Clique em 'Export links snapshot' no NetLogo")
        if not gexf_exists:
            print("   5. Execute: python tools/make_gexf.py")
        sys.exit(1)


if __name__ == "__main__":
    main()







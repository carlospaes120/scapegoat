#!/usr/bin/env python3
"""
create_sample_data.py

Cria dados de exemplo para testar o pipeline sem precisar rodar o NetLogo.
Útil para testes rápidos de scripts de análise e visualização.

Usage:
    python tools/create_sample_data.py
"""

import pandas as pd
import numpy as np
from pathlib import Path


def create_events_csv(output_path, n_events=50):
    """Cria arquivo events.csv de exemplo."""
    print(f"📝 Criando {output_path.name} com {n_events} eventos...")
    
    np.random.seed(42)
    
    events = []
    for i in range(n_events):
        tick = np.random.randint(10, 200)
        source = np.random.randint(0, 100)
        target = np.random.randint(0, 100)
        etype = np.random.choice(['accuse', 'faccuse', 'ritual_accuse'], p=[0.5, 0.3, 0.2])
        
        # Definir kinds baseados no etype
        if etype == 'ritual_accuse':
            source_kind = 'leader'
            target_kind = 'victim'
        elif etype == 'faccuse':
            source_kind = 'accuser_failed'
            target_kind = 'victim_failed'
        else:
            source_kind = np.random.choice(['leader', 'neutral'])
            target_kind = 'victim'
        
        events.append({
            'tick': tick,
            'source': source,
            'target': target,
            'etype': etype,
            'source_kind': source_kind,
            'target_kind': target_kind,
            'weight': 1
        })
    
    df = pd.DataFrame(events).sort_values('tick')
    df.to_csv(output_path, index=False)
    print(f"   ✅ Salvo: {output_path}")


def create_timeseries_csv(output_path, n_ticks=100):
    """Cria arquivo timeseries.csv de exemplo."""
    print(f"📝 Criando {output_path.name} com {n_ticks} ticks...")
    
    np.random.seed(42)
    
    data = []
    for tick in range(n_ticks):
        # Simular evolução temporal
        n_alive = 100 + np.random.randint(-5, 5)
        n_leaders = 2 + np.random.randint(-1, 2)
        n_victims = 5 + np.random.randint(-2, 3)
        pct_victims = (n_victims / n_alive) * 100
        
        # Saúdes
        avggeneralhealth = 3.5 + np.random.uniform(-0.5, 0.5)
        avgleaderhealth = 3.8 + np.random.uniform(-0.3, 0.3)
        avgvictimhealth = 2.5 + np.random.uniform(-0.5, 0.5)
        
        # Graus
        avggenerallinkneighbors = 4.0 + np.random.uniform(-0.5, 0.5)
        avgvictimlinkneighbors = 3.5 + np.random.uniform(-0.5, 0.5)
        avgleaderlinkneighbors = 5.0 + np.random.uniform(-0.5, 0.5)
        
        # CCs
        avggeneralcc = 0.3 + np.random.uniform(-0.05, 0.05)
        avgleadercc = 0.35 + np.random.uniform(-0.05, 0.05)
        avgvictimcc = 0.25 + np.random.uniform(-0.05, 0.05)
        
        # Outros
        pollution = np.random.randint(0, 4)
        timetoritual = 50 - (tick % 50)
        ritualtime = 5 if tick % 50 < 5 else 0
        
        data.append({
            'tick': tick,
            'n_alive': n_alive,
            'n_leaders': n_leaders,
            'n_victims': n_victims,
            'pct_victims': pct_victims,
            'avggeneralhealth': avggeneralhealth,
            'avgleaderhealth': avgleaderhealth,
            'avgvictimhealth': avgvictimhealth,
            'avggenerallinkneighbors': avggenerallinkneighbors,
            'avgvictimlinkneighbors': avgvictimlinkneighbors,
            'avgleaderlinkneighbors': avgleaderlinkneighbors,
            'avggeneralcc': avggeneralcc,
            'avgleadercc': avgleadercc,
            'avgvictimcc': avgvictimcc,
            'pollution': pollution,
            'timetoritual': timetoritual,
            'ritualtime': ritualtime
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    print(f"   ✅ Salvo: {output_path}")


def create_nodes_csv(output_path, n_nodes=100):
    """Cria arquivo nodes.csv de exemplo."""
    print(f"📝 Criando {output_path.name} com {n_nodes} nós...")
    
    np.random.seed(42)
    
    nodes = []
    for i in range(n_nodes):
        # Distribuição de tipos
        if i < 2:
            kind = 'leader'
            health = np.random.uniform(3.5, 4.0)
            tension = np.random.uniform(0, 1)
        elif i < 7:
            kind = 'victim'
            health = np.random.uniform(2.0, 3.0)
            tension = np.random.uniform(2, 3)
        elif i < 10:
            kind = 'accuser_failed'
            health = np.random.uniform(2.5, 3.5)
            tension = np.random.uniform(1, 2)
        else:
            kind = 'neutral'
            health = np.random.uniform(3.0, 4.0)
            tension = np.random.uniform(0, 2)
        
        cc_node = np.random.uniform(0.1, 0.6)
        degree = np.random.randint(2, 8)
        
        nodes.append({
            'id': i,
            'kind': kind,
            'health': health,
            'tension': tension,
            'cc_node': cc_node,
            'degree': degree
        })
    
    df = pd.DataFrame(nodes)
    df.to_csv(output_path, index=False)
    print(f"   ✅ Salvo: {output_path}")


def create_links_csv(output_path, n_nodes=100, avg_degree=4):
    """Cria arquivo links_snapshot.csv de exemplo."""
    print(f"📝 Criando {output_path.name} (rede Erdős-Rényi)...")
    
    np.random.seed(42)
    
    # Rede Erdős-Rényi
    p = avg_degree / (n_nodes - 1)
    links = []
    
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            if np.random.random() < p:
                links.append({'source': i, 'target': j})
    
    df = pd.DataFrame(links)
    df.to_csv(output_path, index=False)
    print(f"   ✅ Salvo: {output_path} ({len(df)} arestas)")


def main():
    """Cria todos os arquivos de exemplo."""
    print("="*60)
    print("🧪 CRIAÇÃO DE DADOS DE EXEMPLO")
    print("="*60)
    
    # Criar diretório data se não existir
    data_dir = Path(__file__).resolve().parents[1] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Criar arquivos
    create_events_csv(data_dir / "events.csv", n_events=50)
    create_timeseries_csv(data_dir / "timeseries.csv", n_ticks=100)
    create_nodes_csv(data_dir / "nodes.csv", n_nodes=100)
    create_links_csv(data_dir / "links_snapshot.csv", n_nodes=100, avg_degree=4)
    
    print("\n" + "="*60)
    print("✅ DADOS DE EXEMPLO CRIADOS")
    print("="*60)
    print(f"\n📂 Pasta: {data_dir}")
    print("\n💡 Próximos passos:")
    print("   1. python tools/verify_data.py      # Verificar integridade")
    print("   2. python tools/make_gexf.py        # Gerar GEXF")
    print("   3. python examples/analyze_simulation.py  # Análise completa")


if __name__ == "__main__":
    main()







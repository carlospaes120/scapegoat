#!/usr/bin/env python3
"""
convert_netlogo_events_to_edges.py

Converte events.csv do NetLogo para o formato esperado pelo ego_isolation_timeseries.py

O events.csv do NetLogo tem:
  tick, source, target, etype, source_kind, target_kind, weight

Precisamos transformar em:
  src, dst, timestamp

Assumindo que cada tick = 1 dia (ou pode especificar intervalo).
"""

import pandas as pd
import argparse
from pathlib import Path
from datetime import datetime, timedelta

def parse_args():
    p = argparse.ArgumentParser(description="Converte events.csv do NetLogo para formato de arestas temporais")
    p.add_argument("--input", required=True, help="Caminho do events.csv do NetLogo")
    p.add_argument("--output", required=True, help="Caminho do arquivo de saída")
    p.add_argument("--tick_interval", default="1D", help="Intervalo de tempo por tick (ex: 1D, 1H, 6H)")
    p.add_argument("--start_date", default="2024-01-01", help="Data inicial da simulação (formato: YYYY-MM-DD)")
    return p.parse_args()

def main():
    args = parse_args()
    
    print(f"📂 Lendo {args.input}...")
    df = pd.read_csv(args.input)
    
    if df.empty:
        print("⚠️  Arquivo vazio! Execute a simulação e garanta que eventos sejam registrados.")
        return
    
    print(f"✅ {len(df)} eventos carregados")
    
    # Converter tick para timestamp
    start = pd.to_datetime(args.start_date)
    tick_delta = pd.to_timedelta(args.tick_interval)
    
    df["timestamp"] = start + (df["tick"] * tick_delta)
    
    # Renomear colunas
    df_out = df.rename(columns={
        "source": "src",
        "target": "dst"
    })
    
    # Selecionar apenas colunas necessárias (e manter extras opcionalmente)
    cols = ["src", "dst", "timestamp", "etype", "source_kind", "target_kind", "weight"]
    df_out = df_out[cols]
    
    # Salvar
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(output_path, index=False)
    
    print(f"💾 Salvo: {output_path}")
    print(f"📅 Período: {df_out['timestamp'].min()} → {df_out['timestamp'].max()}")
    print(f"📊 Tipos de evento: {df_out['etype'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()







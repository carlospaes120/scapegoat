#!/usr/bin/env python3
"""
Exemplos de uso do script net_metrics.py

Este script demonstra como usar o net_metrics.py com diferentes modos de entrada
e parâmetros para calcular métricas de rede.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """Executa um comando e mostra o resultado."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Comando: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Sucesso!")
        print("Saida:")
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Erro: {e}")
        print("Saida:")
        print(e.stdout)
        if e.stderr:
            print("Erro:")
            print(e.stderr)

def main():
    """Demonstra diferentes usos do net_metrics.py"""
    
    print("EXEMPLOS DE USO DO NET_METRICS.PY")
    print("="*60)
    
    # Verificar se os arquivos existem
    jsonl_files = [
        "data/jsonl/karol_conka.jsonl",
        "data/jsonl/monark.jsonl", 
        "data/jsonl/eduardo_bueno.jsonl",
        "data/jsonl/wagner_schwartz.jsonl"
    ]
    
    missing_files = [f for f in jsonl_files if not Path(f).exists()]
    if missing_files:
        print(f"Arquivos nao encontrados: {missing_files}")
        print("Certifique-se de que os arquivos JSONL estão na pasta data/jsonl/")
        return
    
    # Exemplo 1: Análise básica com Karol Conká
    print("\n1. ANALISE BASICA - KAROL CONKA")
    cmd1 = [
        "python", "net_metrics.py",
        "--jsonl", "data/jsonl/karol_conka.jsonl",
        "--victim", "@karolconka",
        "--outdir", "outputs/karol_conka_net",
        "--btw-sample", "100"
    ]
    run_command(cmd1, "Análise básica com amostragem de betweenness")
    
    # Exemplo 2: Análise completa com Monark
    print("\n2. ANALISE COMPLETA - MONARK")
    cmd2 = [
        "python", "net_metrics.py", 
        "--jsonl", "data/jsonl/monark.jsonl",
        "--victim", "@monark",
        "--outdir", "outputs/monark_net",
        "--btw-sample", "0",  # Betweenness completo
        "--min-degree", "2"   # Filtrar nós com grau < 2
    ]
    run_command(cmd2, "Análise completa com betweenness total e filtro de grau")
    
    # Exemplo 3: Análise com múltiplos arquivos
    print("\n3. ANALISE COM MULTIPLOS ARQUIVOS")
    cmd3 = [
        "python", "net_metrics.py",
        "--jsonl", "data/jsonl/eduardo_bueno.jsonl", "data/jsonl/wagner_schwartz.jsonl",
        "--victim", "@EduardoBueno,@wagnerschwartz",
        "--outdir", "outputs/combined_net",
        "--btw-sample", "200"
    ]
    run_command(cmd3, "Análise combinada de dois casos")
    
    # Exemplo 4: Análise com logging detalhado
    print("\n4. ANALISE COM LOGGING DETALHADO")
    cmd4 = [
        "python", "net_metrics.py",
        "--jsonl", "data/jsonl/karol_conka.jsonl",
        "--victim", "@karolconka",
        "--outdir", "outputs/karol_detailed",
        "--btw-sample", "50",
        "--log", "DEBUG"
    ]
    run_command(cmd4, "Análise com logging detalhado (DEBUG)")
    
    # Exemplo 5: Demonstração de help
    print("\n5. AJUDA E PARAMETROS")
    cmd5 = ["python", "net_metrics.py", "--help"]
    run_command(cmd5, "Mostrar ajuda e parâmetros disponíveis")
    
    print("\n" + "="*60)
    print("TODOS OS EXEMPLOS EXECUTADOS!")
    print("="*60)
    print("\nArquivos gerados:")
    print("- outputs/karol_conka_net/")
    print("- outputs/monark_net/")
    print("- outputs/combined_net/")
    print("- outputs/karol_detailed/")
    print("\nPara cada diretorio:")
    print("- node_metrics.csv: metricas dos nos")
    print("- graph_metrics.json: metricas do grafo")
    print("- graph.gexf: grafo para Gephi")
    print("- victim_metrics.json: metricas da vitima (se encontrada)")

if __name__ == "__main__":
    main()

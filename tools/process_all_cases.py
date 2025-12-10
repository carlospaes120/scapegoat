#!/usr/bin/env python3
"""
process_all_cases.py

Processa todos os casos (Twitter + Simulação) em lote:
1. Extrai arestas dos JSONLs
2. Calcula métricas de isolamento
3. Gera relatório comparativo
"""

import subprocess
import sys
from pathlib import Path

# Configuração dos casos
CASES = [
    {
        'id': 'monark',
        'input': 'notebooks/tweets_classificados_monark.jsonl',
        'victim': '@monark',
        'format': 'jsonl'
    },
    {
        'id': 'karol',
        'input': 'notebooks/tweets_classified_karolconka.jsonl',
        'victim': '@Karolconka',
        'format': 'jsonl'
    },
    {
        'id': 'wagner',
        'input': 'notebooks/tweets_classified_wagner_schwartz.jsonl',
        'victim': '@WagnerSchwartz',
        'format': 'jsonl'
    },
    {
        'id': 'bueno',
        'input': 'notebooks/tweets_classified_eduardo_bueno.jsonl',
        'victim': '@EduardoBueno',
        'format': 'jsonl'
    }
]

def run_command(cmd, description):
    """Executa comando e reporta status."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Comando: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERRO: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    print("="*60)
    print("📊 PROCESSAMENTO EM LOTE - TODOS OS CASOS")
    print("="*60)
    print(f"\nCasos a processar: {len(CASES)}")
    for case in CASES:
        print(f"  - {case['id']}: {case['input']}")
    
    # input("\nPressione Enter para iniciar...")  # Executar automaticamente
    
    results = []
    
    for case in CASES:
        case_id = case['id']
        print(f"\n\n{'#'*60}")
        print(f"# CASO: {case_id.upper()}")
        print(f"{'#'*60}")
        
        # Passo 1: Extrair arestas do Twitter JSONL
        edges_file = f"data/edges_{case_id}.csv"
        
        success = run_command([
            sys.executable,
            "tools/extract_edges_from_twitter.py",
            "--input", case['input'],
            "--output", edges_file,
            "--edge_types", "mention,reply"
        ], f"Extração de arestas - {case_id}")
        
        if not success:
            print(f"⚠️  Pulando {case_id} devido a erro na extração")
            results.append((case_id, False, "Falha na extração"))
            continue
        
        # Passo 2: Calcular métricas de isolamento
        success = run_command([
            sys.executable,
            "scripts/ego_isolation_timeseries.py",
            "--input", edges_file,
            "--format", "csv",
            "--case_id", case_id,
            "--victim", case['victim'],
            "--window", "1D",
            "--directed",
            "--anchor_peak",
            "--outdir", "outputs/isolation"
        ], f"Métricas de isolamento - {case_id}")
        
        if success:
            results.append((case_id, True, "OK"))
        else:
            results.append((case_id, False, "Falha no cálculo de métricas"))
    
    # Resumo final
    print("\n\n" + "="*60)
    print("📊 RESUMO DO PROCESSAMENTO")
    print("="*60)
    
    for case_id, success, msg in results:
        status = "✅" if success else "❌"
        print(f"{status} {case_id}: {msg}")
    
    success_count = sum(1 for _, s, _ in results if s)
    print(f"\n✅ {success_count}/{len(CASES)} casos processados com sucesso")
    
    if success_count > 0:
        print("\n💡 Próximo passo: Executar script de comparação")
        print("   python tools/compare_isolation_cases.py")

if __name__ == "__main__":
    main()


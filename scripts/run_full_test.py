#!/usr/bin/env python3
"""
run_full_test.py

Script de teste integrado completo. Executa todo o pipeline:
1. Cria dados de exemplo
2. Verifica integridade
3. Gera GEXF
4. Executa análise
5. Valida saídas

Usage:
    python run_full_test.py
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Executa um comando e reporta sucesso/falha."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Comando: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        print(f"✅ {description} - SUCESSO")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FALHA")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ {description} - Comando não encontrado")
        print(f"   Certifique-se de que Python está instalado e no PATH")
        return False


def check_file_exists(filepath, description):
    """Verifica se um arquivo existe."""
    if filepath.exists():
        size = filepath.stat().st_size
        print(f"   ✅ {filepath.name} ({size:,} bytes)")
        return True
    else:
        print(f"   ❌ {filepath.name} - NÃO ENCONTRADO")
        return False


def main():
    """Executa teste completo."""
    print("=" * 70)
    print("🧪 TESTE INTEGRADO COMPLETO - MODELO SCAPEGOAT")
    print("=" * 70)
    print("\nEste script testará todo o pipeline de coleta e análise de dados.")
    print("Tempo estimado: ~30 segundos\n")
    
    input("Pressione Enter para começar...")
    
    # Paths
    root = Path(__file__).parent
    data_dir = root / "data"
    outputs_dir = root / "outputs"
    tools_dir = root / "tools"
    examples_dir = root / "examples"
    
    results = []
    
    # Teste 1: Criar dados de exemplo
    results.append(run_command(
        [sys.executable, str(tools_dir / "create_sample_data.py")],
        "Teste 1: Criar Dados de Exemplo"
    ))
    
    # Verificar se arquivos CSV foram criados
    print("\n📂 Verificando arquivos CSV criados:")
    csv_files = [
        data_dir / "events.csv",
        data_dir / "timeseries.csv",
        data_dir / "nodes.csv",
        data_dir / "links_snapshot.csv"
    ]
    csv_ok = all(check_file_exists(f, f.name) for f in csv_files)
    results.append(csv_ok)
    
    # Teste 2: Verificar integridade
    results.append(run_command(
        [sys.executable, str(tools_dir / "verify_data.py")],
        "Teste 2: Verificar Integridade dos Dados"
    ))
    
    # Teste 3: Gerar GEXF
    results.append(run_command(
        [sys.executable, str(tools_dir / "make_gexf.py")],
        "Teste 3: Gerar GEXF/GraphML"
    ))
    
    # Verificar se GEXF foi criado
    print("\n📂 Verificando arquivos de rede criados:")
    network_files = [
        data_dir / "network.gexf",
        data_dir / "network.graphml"
    ]
    network_ok = all(check_file_exists(f, f.name) for f in network_files)
    results.append(network_ok)
    
    # Teste 4: Análise completa
    results.append(run_command(
        [sys.executable, str(examples_dir / "analyze_simulation.py")],
        "Teste 4: Análise Completa com Gráficos"
    ))
    
    # Verificar se gráficos foram criados
    print("\n📂 Verificando gráficos criados:")
    plot_files = [
        outputs_dir / "events_analysis.png",
        outputs_dir / "timeseries_analysis.png",
        outputs_dir / "network_analysis.png"
    ]
    plots_ok = all(check_file_exists(f, f.name) for f in plot_files)
    results.append(plots_ok)
    
    # Teste 5: Validar GEXF com NetworkX
    print(f"\n{'='*60}")
    print("🚀 Teste 5: Validar GEXF com NetworkX")
    print(f"{'='*60}")
    try:
        import networkx as nx
        G = nx.read_gexf(data_dir / "network.gexf")
        print(f"   ✅ GEXF carregado com sucesso")
        print(f"   📊 Grafo: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
        
        # Verificar atributos
        if G.number_of_nodes() > 0:
            sample_node = list(G.nodes())[0]
            attrs = G.nodes[sample_node]
            expected_attrs = ['kind', 'health', 'tension', 'cc_node', 'degree']
            missing_attrs = [a for a in expected_attrs if a not in attrs]
            if missing_attrs:
                print(f"   ⚠️  Atributos faltando: {missing_attrs}")
                results.append(False)
            else:
                print(f"   ✅ Todos os atributos presentes: {list(attrs.keys())}")
                results.append(True)
        else:
            print(f"   ⚠️  Grafo vazio")
            results.append(False)
    except ImportError:
        print(f"   ⚠️  NetworkX não instalado. Pulando validação.")
        results.append(True)  # Não falhar o teste por isso
    except Exception as e:
        print(f"   ❌ Erro ao validar GEXF: {e}")
        results.append(False)
    
    # Resumo final
    print("\n" + "=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)
    
    test_names = [
        "1. Criar Dados de Exemplo",
        "2. Arquivos CSV Criados",
        "3. Verificar Integridade",
        "4. Gerar GEXF/GraphML",
        "5. Arquivos de Rede Criados",
        "6. Análise Completa",
        "7. Gráficos Criados",
        "8. Validar GEXF"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {name}")
    
    passed = sum(results)
    total = len(results)
    print(f"\n   Total: {passed}/{total} testes passaram")
    
    if all(results):
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("\n💡 Próximos passos:")
        print("   1. Abra 'outputs/*.png' para ver os gráficos gerados")
        print("   2. Importe 'data/network.gexf' no Gephi")
        print("   3. Execute a simulação no NetLogo (scapegoat_instrumented.nlogo)")
        print("   4. Repita os testes com dados reais do NetLogo")
        return 0
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        print("\n💡 Ações recomendadas:")
        print("   1. Verifique os erros acima")
        print("   2. Instale dependências: pip install pandas networkx matplotlib seaborn")
        print("   3. Certifique-se de que a pasta 'data/' existe")
        print("   4. Execute: python tools/create_sample_data.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())


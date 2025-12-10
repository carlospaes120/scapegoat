"""
Script de teste rápido usando dados de exemplo.

Este script demonstra o uso do pipeline com dados sintéticos mínimos.
Para dados reais, use main_case.py com seus arquivos JSONL/CSV.
"""

import sys
from pathlib import Path

# Adicionar scripts ao path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from leader_emergence import run_analysis


def main():
    print("\n" + "="*60)
    print("TESTE DO PIPELINE COM DADOS DE EXEMPLO")
    print("="*60 + "\n")
    
    print("ATENÇÃO: Este é apenas um teste com dados sintéticos mínimos.")
    print("Para análises reais, use main_case.py com seus dados.\n")
    
    # Verificar se o arquivo de exemplo existe
    example_file = Path('example_data_format.jsonl')
    
    if not example_file.exists():
        print(f"❌ Arquivo {example_file} não encontrado!")
        print("   Crie o arquivo com dados de exemplo antes de executar este teste.")
        return 1
    
    print(f"✓ Usando arquivo: {example_file}\n")
    
    # Executar análise com parâmetros de teste
    try:
        results = run_analysis(
            input_paths=[str(example_file)],
            case_name="ExemploTeste",
            bin_hours=0.5,  # Bins de 30 minutos para dados pequenos
            tz='America/Sao_Paulo',
            count_rules={'mention': 1, 'retweet': 1, 'quote': 1, 'reply': 1},
            pre_frac=0.3,  # 30% inicial como baseline
            k_consec=1,    # Apenas 1 janela consecutiva (dados pequenos)
            output_dir='./outputs'
        )
        
        print("\n" + "="*60)
        print("✓ TESTE CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print(f"\nResultados salvos em: {results['output_dir']}")
        print("\nPróximos passos:")
        print("  1. Verifique os arquivos gerados em outputs/ExemploTeste/")
        print("  2. Use main_case.py com seus dados reais")
        print("  3. Ajuste parâmetros conforme necessário\n")
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        print("\nNOTA: Este erro pode ocorrer se os dados de exemplo forem")
        print("      insuficientes. Use dados reais para análises completas.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())






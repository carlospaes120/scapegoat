"""
Script principal para análise de emergência de líderes em casos específicos.

Uso:
    python main_case.py --case_name "Monark" --inputs data/monark/*.jsonl
"""

import argparse
import sys
from pathlib import Path
import glob

# Adicionar scripts ao path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from leader_emergence import run_analysis


def main():
    parser = argparse.ArgumentParser(
        description='Análise de emergência de líderes em crises miméticas no Twitter'
    )
    
    parser.add_argument(
        '--case_name',
        type=str,
        required=True,
        help='Nome do caso (ex: "Monark", "KarolConka")'
    )
    
    parser.add_argument(
        '--inputs',
        type=str,
        nargs='+',
        required=True,
        help='Caminhos para arquivos de dados (JSONL ou CSV). Suporta wildcards.'
    )
    
    parser.add_argument(
        '--bin_hours',
        type=float,
        default=1.0,
        help='Tamanho do bin temporal em horas (default: 1.0)'
    )
    
    parser.add_argument(
        '--tz',
        type=str,
        default='America/Sao_Paulo',
        help='Timezone (default: America/Sao_Paulo)'
    )
    
    parser.add_argument(
        '--pre_frac',
        type=float,
        default=0.2,
        help='Fração inicial do período para baseline pré-crise (default: 0.2)'
    )
    
    parser.add_argument(
        '--k_consec',
        type=int,
        default=2,
        help='Janelas consecutivas para confirmar emergência (default: 2)'
    )
    
    parser.add_argument(
        '--mention_weight',
        type=float,
        default=1.0,
        help='Peso para menções (default: 1.0)'
    )
    
    parser.add_argument(
        '--retweet_weight',
        type=float,
        default=1.0,
        help='Peso para retweets (default: 1.0)'
    )
    
    parser.add_argument(
        '--quote_weight',
        type=float,
        default=1.0,
        help='Peso para quotes (default: 1.0)'
    )
    
    parser.add_argument(
        '--reply_weight',
        type=float,
        default=1.0,
        help='Peso para replies (default: 1.0)'
    )
    
    parser.add_argument(
        '--output_dir',
        type=str,
        default='./outputs',
        help='Diretório base de saída (default: ./outputs)'
    )
    
    args = parser.parse_args()
    
    # Expandir wildcards nos caminhos de input
    input_paths = []
    for pattern in args.inputs:
        expanded = glob.glob(pattern)
        if expanded:
            input_paths.extend(expanded)
        else:
            # Se não expandiu, usar o path literal (pode ser um arquivo específico)
            input_paths.append(pattern)
    
    # Remover duplicatas e manter ordem
    input_paths = list(dict.fromkeys(input_paths))
    
    print(f"\nArquivos de entrada ({len(input_paths)}):")
    for path in input_paths:
        print(f"  - {path}")
    
    # Configurar regras de contagem
    count_rules = {
        'mention': args.mention_weight,
        'retweet': args.retweet_weight,
        'quote': args.quote_weight,
        'reply': args.reply_weight
    }
    
    # Executar análise
    try:
        results = run_analysis(
            input_paths=input_paths,
            case_name=args.case_name,
            bin_hours=args.bin_hours,
            tz=args.tz,
            count_rules=count_rules,
            pre_frac=args.pre_frac,
            k_consec=args.k_consec,
            output_dir=args.output_dir
        )
        
        print("\n✓ Análise concluída com sucesso!")
        return 0
    
    except Exception as e:
        print(f"\n✗ Erro durante a análise: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())






#!/usr/bin/env python3
"""
Ponto de entrada principal para análise de casos de cancelamento no Twitter.
"""

import sys
import argparse
from pathlib import Path
import logging
from datetime import datetime

# Adicionar diretório analysis ao path
sys.path.append(str(Path(__file__).parent / "analysis"))

from compare_cases import run_complete_analysis, print_output_summary

def setup_logging(output_dir: Path) -> None:
    """Configura sistema de logging."""
    log_file = output_dir / "log.txt"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Análise iniciada em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Análise de casos de cancelamento no Twitter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python run_all.py
  python run_all.py --data-dir ./data/jsonl --output-dir ./outputs
  python run_all.py --top-n 50
        """
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='./data/jsonl',
        help='Diretório com arquivos JSONL (default: ./data/jsonl)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./outputs',
        help='Diretório de saída (default: ./outputs)'
    )
    
    parser.add_argument(
        '--top-n',
        type=int,
        default=20,
        help='Número de top usuários/menções para análise (default: 20)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Logging verboso'
    )
    
    args = parser.parse_args()
    
    # Converter para Path
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    # Criar diretório de saída
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging(output_dir)
    logger = logging.getLogger(__name__)
    
    # Verificar diretório de dados
    if not data_dir.exists():
        logger.error(f"❌ Diretório de dados não encontrado: {data_dir}")
        logger.info("📁 Crie o diretório e adicione arquivos .jsonl para processar")
        logger.info("   Exemplo: mkdir -p data/jsonl")
        logger.info("   Adicione arquivos como: karol_conka.jsonl, monark.jsonl, etc.")
        return 1
    
    # Verificar arquivos JSONL
    jsonl_files = list(data_dir.glob("*.jsonl"))
    if not jsonl_files:
        logger.error(f"❌ Nenhum arquivo .jsonl encontrado em {data_dir}")
        logger.info("📄 Adicione arquivos .jsonl no diretório de dados")
        return 1
    
    logger.info(f"📊 Encontrados {len(jsonl_files)} arquivos JSONL:")
    for file_path in jsonl_files:
        logger.info(f"   - {file_path.name}")
    
    # Executar análise
    logger.info("🚀 Iniciando análise completa...")
    
    try:
        results = run_complete_analysis(data_dir, output_dir)
        
        if results['success']:
            logger.info("✅ Análise concluída com sucesso!")
            logger.info(f"📊 {results['cases_processed']}/{results['total_cases']} casos processados")
            
            # Imprimir resumo da estrutura
            print("\n" + "="*60)
            print("ESTRUTURA DE SAIDA GERADA:")
            print("="*60)
            print_output_summary(output_dir)
            
            print("\n" + "="*60)
            print("RESUMO DOS ARQUIVOS GERADOS:")
            print("="*60)
            
            # Listar arquivos por tipo
            png_files = sorted(list(output_dir.rglob("*.png")))
            csv_files = sorted(list(output_dir.rglob("*.csv")))
            gexf_files = sorted(list(output_dir.rglob("*.gexf")))
            
            print(f"\nFiguras ({len(png_files)} arquivos):")
            for png_file in png_files:
                rel_path = png_file.relative_to(output_dir)
                print(f"   {rel_path}")
            
            print(f"\nTabelas ({len(csv_files)} arquivos):")
            for csv_file in csv_files:
                rel_path = csv_file.relative_to(output_dir)
                print(f"   {rel_path}")
            
            if gexf_files:
                print(f"\nGrafos ({len(gexf_files)} arquivos):")
                for gexf_file in gexf_files:
                    rel_path = gexf_file.relative_to(output_dir)
                    print(f"   {rel_path}")
            
            print(f"\nLog completo: {output_dir / 'log.txt'}")
            print(f"Relatorio: {output_dir / 'analysis_report.txt'}")
            
            return 0
        
        else:
            logger.error("❌ Análise falhou")
            return 1
    
    except Exception as e:
        logger.error(f"❌ Erro durante análise: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

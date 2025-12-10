#!/usr/bin/env python3
"""
summarize_gephi_nodes.py

Script para processar CSV de nós exportado do Gephi e calcular resumos estatísticos por kind.

Uso:
    python summarize_gephi_nodes.py --nodes "caminho/para/nodes_gephi.csv"

Saída:
    ./outputs/summary_by_kind.csv
    ./outputs/summary_by_kind.xlsx

Requisitos:
    pandas, numpy
"""

import argparse
import os
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


def slug(s):
    """Normaliza string para formato slug (minúscula, sem acentos, espaços por _)."""
    s = ''.join(ch for ch in unicodedata.normalize('NFKD', s) if not unicodedata.combining(ch))
    return s.strip().lower().replace(' ', '_').replace('-', '_')


def read_nodes_csv(path):
    """Lê CSV de nós do Gephi com detecção automática de separador e codificação."""
    print(f"[INFO] Lendo arquivo: {path}")
    
    # Verificar se arquivo existe
    if not os.path.exists(path):
        raise SystemExit(f"Arquivo não encontrado: {path}")
    
    # Detectar separador
    with open(path, 'rb') as fh:
        raw = fh.read(2048)
    sample = raw.decode('utf-8', errors='ignore')
    sep = ',' if sample.count(',') >= sample.count(';') else ';'
    decimal = ',' if sep == ';' else '.'
    
    print(f"[INFO] Separador detectado: '{sep}', Decimal: '{decimal}'")
    
    # Ler CSV
    try:
        df = pd.read_csv(path, sep=sep, encoding='utf-8')
    except Exception as e:
        print(f"[ERRO] Falha ao ler arquivo: {e}")
        raise SystemExit("Erro ao processar CSV")
    
    print(f"[INFO] CSV carregado: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Normalizar colunas
    df.columns = [slug(c) for c in df.columns]
    print(f"[INFO] Colunas normalizadas: {list(df.columns)}")
    
    # Renomear colunas comuns do Gephi para nomes padrão
    ren = {
        'excentricidade': 'eccentricity',
        'excentricity': 'eccentricity',
        'modularityclass': 'modularity_class',
        'modularity_class_': 'modularity_class',
        'grau_de_entrada': 'in_degree',
        'grau_de_saida': 'out_degree',
        'grau': 'degree',
        'grau_de_entrada_ponderado': 'in_degree_weighted',
        'grau_de_saida_ponderado': 'out_degree_weighted',
        'grau_ponderado': 'degree_weighted',
        'grau_de_entrada_ponderado': 'in_degree_weighted',
        'grau_de_saida_ponderado': 'out_degree_weighted',
        'grau_ponderado': 'degree_weighted',
        'closeness_centrality': 'closeness_centrality',
        'harmonic_closeness_centrality': 'harmonic_closeness_centrality',
        'betweenness_centrality': 'betweenness_centrality',
        'pagerank': 'pagerank'
    }
    
    # Aplicar renomeações somente para colunas que existem
    for old_name, new_name in ren.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})
            print(f"[INFO] Renomeado: '{old_name}' -> '{new_name}'")
    
    # Verificar presença de coluna 'kind'
    if 'kind' not in df.columns:
        raise SystemExit(
            "ERRO: Arquivo não tem a coluna 'kind'.\n"
            "SOLUÇÃO: No Gephi:\n"
            "1. Importe o nodes_kind.csv (Nodes table, Append)\n"
            "2. Reexporte a Tabela de Nós (Laboratório de dados -> Exportar tabela)\n"
        )
    
    # Detectar métricas presentes
    metric_candidates = [
        'in_degree', 'out_degree', 'degree',
        'in_degree_weighted', 'out_degree_weighted', 'degree_weighted',
        'pagerank', 'betweenness_centrality', 'closeness_centrality', 
        'harmonic_closeness_centrality',
        'eccentricity', 'modularity_class'
    ]
    
    metrics = [m for m in metric_candidates if m in df.columns]
    print(f"[INFO] Métricas encontradas: {metrics}")
    
    if not metrics:
        raise SystemExit(
            "ERRO: Nenhuma métrica reconhecida.\n"
            "SOLUÇÃO: No Gephi, calcule estatísticas de rede antes de exportar.\n"
            "Métricas esperadas: degree, centrality measures, pagerank, etc."
        )
    
    # Converter métricas para numérico
    print("[INFO] Convertendo métricas para numérico...")
    for m in metrics:
        if m in df.columns:
            # Tratar vírgulas como decimal em caso de separador ';'
            if decimal == ',':
                df[m] = (df[m].astype(str)
                          .str.replace(',', '.', regex=False)
                )
            else:
                # Caso contrário, apenas converter vírgulas em pontos se necessário
                df[m] = df[m].astype(str).str.replace(',', '.', regex=False)
            
            df[m] = pd.to_numeric(df[m], errors='coerce')
            print(f"  {m}: convertido ({df[m].notna().sum()}/{len(df)} valores numéricos)")
    
    return df, metrics


def summarize(df, metrics):
    """Calcula estatísticas por kind para cada métrica."""
    print(f"[INFO] Calculando estatísticas para {len(metrics)} métricas...")
    
    stats = ['n', 'mean', 'std', 'median', 'p75', 'p90', 'p95', 'min', 'max']
    rows = []
    
    grouped = df.groupby('kind', dropna=False)
    
    for m in metrics:
        print(f"  Processando: {m}")
        s = grouped[m].agg(
            n='count',
            mean='mean',
            std='std',
            median='median',
            p75=lambda x: np.nanpercentile(x.dropna(), 75) if x.notna().any() else np.nan,
            p90=lambda x: np.nanpercentile(x.dropna(), 90) if x.notna().any() else np.nan,
            p95=lambda x: np.nanpercentile(x.dropna(), 95) if x.notna().any() else np.nan,
            min='min',
            max='max'
        ).reset_index()
        s.insert(1, 'metric', m)
        rows.append(s)
    
    if rows:
        all_tbl = pd.concat(rows, ignore_index=True)
    else:
        all_tbl = pd.DataFrame(columns=['kind', 'metric'] + stats)
    
    return all_tbl


def main():
    """Função principal do script."""
    # Configurar argumentos
    parser = argparse.ArgumentParser(
        description='Processa CSV de nós do Gephi e calcula estatísticas por kind.'
    )
    parser.add_argument(
        '--nodes', 
        required=True, 
        help='Caminho para o CSV exportado do Gephi (Laboratório de dados -> Exportar tabela)'
    )
    
    args = parser.parse_args()
    
    # Criar pasta de outputs
    outdir = Path('outputs')
    outdir.mkdir(exist_ok=True)
    print(f"[INFO] Diretório de saída: {outdir.absolute()}")
    
    try:
        # Ler e processar dados
        df, metrics = read_nodes_csv(args.nodes)
        
        # Verificar se temos dados
        if len(df) == 0:
            raise SystemExit("Arquivo CSV vazio")
        
        # Calcular estatísticas
        all_tbl = summarize(df, metrics)
        
        if len(all_tbl) == 0:
            raise SystemExit("Nenhuma estatística calculada (sem dados válidos)")
        
        # Salvar CSV empilhado
        csv_path = outdir / 'summary_by_kind.csv'
        all_tbl.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"[INFO] Salvo CSV: {csv_path}")
        
        # Salvar Excel com múltiplas abas
        xlsx_path = outdir / 'summary_by_kind.xlsx'
        print(f"[INFO] Criando Excel: {xlsx_path}")
        
        with pd.ExcelWriter(xlsx_path, engine='openpyxl') as xl:
            # Aba principal
            all_tbl.to_excel(xl, sheet_name='_ALL', index=False)
            
            # Uma aba por métrica
            for m in metrics:
                mdf = all_tbl[all_tbl['metric'] == m].drop(columns=['metric'])
                sheet_name = m[:31]  # Limite de 31 caracteres para nome da aba
                mdf.to_excel(xl, sheet_name=sheet_name, index=False)
        
        print(f"[INFO] Salvo Excel: {xlsx_path}")
        
        # Exibir preview da tabela
        print("\n=== PREVIEW DA TABELA SUMMARY ===")
        print(all_tbl.head())
        print(f"\nTamanho total: {len(all_tbl)} linhas")
        
        print("\n=== ARQUIVOS GERADOS ===")
        print(f"CSV: {csv_path}")
        print(f"Excel: {xlsx_path}")
        print("\n✅ Processamento concluído com sucesso!")
        
    except KeyboardInterrupt:
        print("\n[ERRO] Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

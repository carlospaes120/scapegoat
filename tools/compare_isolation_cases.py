#!/usr/bin/env python3
"""
compare_isolation_cases.py

Compara métricas de isolamento entre múltiplos casos (Twitter + Simulação).

Gera:
- Gráficos comparativos
- Tabela resumo
- Relatório em Markdown
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse

sns.set_style("whitegrid")

def parse_args():
    p = argparse.ArgumentParser(description="Compara métricas de isolamento entre casos")
    p.add_argument("--cases", nargs='+', required=True, help="IDs dos casos a comparar")
    p.add_argument("--indir", default="outputs/isolation", help="Diretório de entrada")
    p.add_argument("--outdir", default="outputs/comparison", help="Diretório de saída")
    return p.parse_args()

def load_case_metrics(case_id, indir):
    """Carrega métricas de um caso."""
    filepath = Path(indir) / case_id / f"metrics_{case_id}.csv"
    
    if not filepath.exists():
        print(f"⚠️  {filepath} não encontrado")
        return None
    
    df = pd.read_csv(filepath)
    df['case_id'] = case_id
    df['t'] = pd.to_datetime(df['t'])
    
    return df

def plot_comparative(all_data, metric, ylabel, title, output_path):
    """Plota métrica comparativa entre casos."""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, case_id in enumerate(all_data['case_id'].unique()):
        case_data = all_data[all_data['case_id'] == case_id]
        
        # Filtrar valores válidos
        valid = case_data[case_data[metric].notna()]
        
        if len(valid) == 0:
            continue
        
        if 't_rel_janelas' in valid.columns:
            # Usar tempo relativo se disponível
            x = valid['t_rel_janelas']
            xlabel = 'Janelas desde o pico'
        else:
            # Usar tempo absoluto
            x = valid['t']
            xlabel = 'Tempo'
        
        ax.plot(x, valid[metric], 
               label=case_id.upper(), 
               linewidth=2.5,
               marker='o',
               markersize=4,
               color=colors[i % len(colors)],
               alpha=0.8)
    
    ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=12, fontweight='bold')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best', frameon=True, shadow=True, fontsize=10)
    ax.grid(True, alpha=0.3)
    
    if 't_rel_janelas' not in all_data.columns:
        plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"   💾 {output_path.name}")

def calculate_summary_stats(all_data, case_ids):
    """Calcula estatísticas resumidas para cada caso."""
    stats = []
    
    for case_id in case_ids:
        case_data = all_data[all_data['case_id'] == case_id]
        
        if len(case_data) == 0:
            continue
        
        # Ego density
        ed = case_data['ego_density'].dropna()
        ed_mean = ed.mean() if len(ed) > 0 else np.nan
        ed_std = ed.std() if len(ed) > 0 else np.nan
        ed_min = ed.min() if len(ed) > 0 else np.nan
        ed_max = ed.max() if len(ed) > 0 else np.nan
        
        # Avg distance
        ad = case_data['avg_dist'].dropna()
        ad_mean = ad.mean() if len(ad) > 0 else np.nan
        ad_std = ad.std() if len(ad) > 0 else np.nan
        ad_min = ad.min() if len(ad) > 0 else np.nan
        ad_max = ad.max() if len(ad) > 0 else np.nan
        
        # Volume
        vol_total = case_data['volume'].sum()
        vol_peak = case_data['volume'].max()
        vol_mean = case_data['volume'].mean()
        
        stats.append({
            'case_id': case_id.upper(),
            'ed_mean': ed_mean,
            'ed_std': ed_std,
            'ed_range': f"{ed_min:.3f} - {ed_max:.3f}" if not np.isnan(ed_min) else "N/A",
            'ad_mean': ad_mean,
            'ad_std': ad_std,
            'ad_range': f"{ad_min:.1f} - {ad_max:.1f}" if not np.isnan(ad_min) else "N/A",
            'vol_total': int(vol_total),
            'vol_peak': int(vol_peak),
            'vol_mean': vol_mean
        })
    
    return pd.DataFrame(stats)

def generate_markdown_report(stats, outdir):
    """Gera relatório em Markdown."""
    report_path = outdir / "COMPARATIVE_REPORT.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Relatório Comparativo - Isolamento da Vítima\n\n")
        f.write("## 📊 Visão Geral\n\n")
        f.write(f"Casos analisados: {len(stats)}\n\n")
        f.write(f"Data: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        
        f.write("---\n\n")
        f.write("## 📈 Ego Density (Densidade do Ego-Network)\n\n")
        f.write("| Caso | Média | Desvio Padrão | Range |\n")
        f.write("|------|-------|---------------|-------|\n")
        for _, row in stats.iterrows():
            f.write(f"| **{row['case_id']}** | {row['ed_mean']:.4f} | {row['ed_std']:.4f} | {row['ed_range']} |\n")
        
        f.write("\n**Interpretação:**\n")
        f.write("- Valores altos (> 0.5): Vizinhos da vítima estão altamente conectados (cluster coeso)\n")
        f.write("- Valores baixos (< 0.3): Vizinhos dispersos, vítima é ponte entre grupos\n\n")
        
        f.write("---\n\n")
        f.write("## 🎯 Avg Distance to Victim (Distância Média)\n\n")
        f.write("| Caso | Média | Desvio Padrão | Range |\n")
        f.write("|------|-------|---------------|-------|\n")
        for _, row in stats.iterrows():
            f.write(f"| **{row['case_id']}** | {row['ad_mean']:.2f} | {row['ad_std']:.2f} | {row['ad_range']} |\n")
        
        f.write("\n**Interpretação:**\n")
        f.write("- Aumento ao longo do tempo: isolamento crescente da vítima\n")
        f.write("- Diminuição: vítima se torna mais central na rede\n\n")
        
        f.write("---\n\n")
        f.write("## 📊 Volume de Arestas\n\n")
        f.write("| Caso | Total | Pico | Média/Janela |\n")
        f.write("|------|-------|------|---------------|\n")
        for _, row in stats.iterrows():
            f.write(f"| **{row['case_id']}** | {row['vol_total']:,} | {row['vol_peak']:,} | {row['vol_mean']:.1f} |\n")
        
        f.write("\n---\n\n")
        f.write("## 🔍 Análise Comparativa\n\n")
        
        # Ranking por ego_density média
        ranked = stats.sort_values('ed_mean', ascending=False)
        f.write("### Ranking por Ego Density (maior → menor)\n\n")
        for i, (_, row) in enumerate(ranked.iterrows(), 1):
            f.write(f"{i}. **{row['case_id']}** - {row['ed_mean']:.4f}\n")
        
        f.write("\n### Ranking por Distância Média (maior → menor isolamento)\n\n")
        ranked_dist = stats.sort_values('ad_mean', ascending=False)
        for i, (_, row) in enumerate(ranked_dist.iterrows(), 1):
            f.write(f"{i}. **{row['case_id']}** - {row['ad_mean']:.2f}\n")
        
        f.write("\n---\n\n")
        f.write("## 📁 Arquivos Gerados\n\n")
        f.write("- `ego_density_comparison.png` - Comparação de densidade do ego\n")
        f.write("- `avg_dist_comparison.png` - Comparação de distância média\n")
        f.write("- `volume_comparison.png` - Comparação de volume\n")
        f.write("- `summary_stats.csv` - Estatísticas resumidas\n")
        f.write("- `COMPARATIVE_REPORT.md` - Este relatório\n\n")
        
        f.write("---\n\n")
        f.write("*Gerado automaticamente por compare_isolation_cases.py*\n")
    
    print(f"   💾 {report_path.name}")

def main():
    args = parse_args()
    
    print("="*60)
    print("📊 COMPARAÇÃO DE ISOLAMENTO ENTRE CASOS")
    print("="*60)
    print(f"\nCasos: {', '.join(args.cases)}")
    print(f"Input: {args.indir}")
    print(f"Output: {args.outdir}\n")
    
    # Criar diretório de saída
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    
    # Carregar dados de todos os casos
    print("📂 Carregando dados...")
    all_data = []
    
    for case_id in args.cases:
        print(f"   {case_id}...", end=" ")
        df = load_case_metrics(case_id, args.indir)
        if df is not None:
            all_data.append(df)
            print(f"✅ {len(df)} janelas")
        else:
            print("❌ Não encontrado")
    
    if not all_data:
        print("\n❌ Nenhum dado encontrado!")
        return
    
    all_data = pd.concat(all_data, ignore_index=True)
    print(f"\n✅ Total: {len(all_data)} registros de {len(all_data['case_id'].unique())} casos")
    
    # Gerar gráficos comparativos
    print("\n📊 Gerando gráficos comparativos...")
    
    plot_comparative(
        all_data, 'ego_density',
        'Ego Density',
        'Comparação: Densidade do Ego-Network da Vítima',
        outdir / 'ego_density_comparison.png'
    )
    
    plot_comparative(
        all_data, 'avg_dist',
        'Distância Média',
        'Comparação: Distância Média até a Vítima',
        outdir / 'avg_dist_comparison.png'
    )
    
    plot_comparative(
        all_data, 'volume',
        'Número de Arestas',
        'Comparação: Volume de Arestas por Janela',
        outdir / 'volume_comparison.png'
    )
    
    # Calcular estatísticas resumidas
    print("\n📋 Calculando estatísticas...")
    stats = calculate_summary_stats(all_data, args.cases)
    
    # Salvar CSV
    stats_path = outdir / "summary_stats.csv"
    stats.to_csv(stats_path, index=False)
    print(f"   💾 {stats_path.name}")
    
    # Gerar relatório Markdown
    print("\n📝 Gerando relatório...")
    generate_markdown_report(stats, outdir)
    
    # Exibir tabela no terminal
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS RESUMIDAS")
    print("="*60)
    print(stats.to_string(index=False))
    
    print("\n" + "="*60)
    print("✅ ANÁLISE CONCLUÍDA")
    print("="*60)
    print(f"\n📂 Resultados em: {outdir}")
    print("\nArquivos gerados:")
    for f in outdir.glob('*'):
        print(f"  - {f.name}")

if __name__ == "__main__":
    main()







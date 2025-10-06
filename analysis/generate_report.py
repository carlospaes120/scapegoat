#!/usr/bin/env python3
"""
Script para gerar relatório final de estabilidade
"""

import pandas as pd
import numpy as np

def generate_final_report():
    # Carregar dados
    summary_df = pd.read_csv('analysis/stability_summary.csv')
    Ns = [50, 100, 150, 200, 250, 300, 316]
    
    # Analisar estabilidade
    stability_criteria = {}
    
    for metric in summary_df['metric'].unique():
        metric_data = summary_df[summary_df['metric'] == metric].sort_values('N')
        
        if len(metric_data) == 0:
            continue
        
        stable_N = None
        
        for idx, (_, row) in enumerate(metric_data.iterrows()):
            N = row['N']
            mean_val = row['mean']
            p2_5 = row['p2.5']
            p97_5 = row['p97.5']
            
            # Critério 1: intervalo < 10% da média (ou < 0.05 para modularity/assortativity)
            if metric in ['modularity_ud', 'degree_assortativity_ud']:
                interval_criterion = (p97_5 - p2_5) < 0.05
            else:
                interval_criterion = (p97_5 - p2_5) < 0.1 * abs(mean_val)
            
            # Critério 2: variação relativa < 5%
            variation_criterion = True
            if len(metric_data) > 1 and idx > 0:
                prev_row = metric_data.iloc[idx-1]
                prev_mean = prev_row['mean']
                if abs(prev_mean) > 1e-10:
                    variation = abs(mean_val - prev_mean) / abs(prev_mean)
                    variation_criterion = variation < 0.05
            
            if interval_criterion and variation_criterion:
                stable_N = N
                break
        
        stability_criteria[metric] = stable_N
    
    # Imprimir resumo
    print('🎯 RESUMO DE ESTABILIDADE:')
    print('=' * 50)
    
    for metric, stable_N in stability_criteria.items():
        if stable_N:
            print(f'{metric:25s}: N = {stable_N:3d} (estável)')
        else:
            print(f'{metric:25s}: N = N/A (nunca estável)')
    
    # N_target final
    stable_Ns = [N for N in stability_criteria.values() if N is not None]
    if stable_Ns:
        N_target_final = max(stable_Ns)
        print(f'\n🎯 N_TARGET_FINAL = {N_target_final}')
    else:
        print(f'\n⚠️ Nenhuma métrica atingiu estabilidade')
    
    # Gerar relatório Markdown
    report_content = "# Relatório de Estabilidade - Caso Karol Conká\n\n"
    report_content += "Análise de estabilidade de métricas de rede através de amostragem progressiva.\n\n"
    
    report_content += "## Critérios de Estabilidade\n\n"
    report_content += "- **Intervalo de confiança**: (p97.5 - p2.5) < 10% da média\n"
    report_content += "- **Variação relativa**: |mean(N) - mean(N-Δ)| / mean(N) < 5%\n"
    report_content += "- **Exceções**: Para modularity e assortativity, intervalo < 0.05\n\n"
    
    report_content += "## Resultados por Métrica\n\n"
    report_content += "| Métrica | N Estável | Observações |\n"
    report_content += "|---------|-----------|-------------|\n"
    
    for metric, stable_N in stability_criteria.items():
        if stable_N:
            report_content += f"| {metric} | {stable_N} | ✅ Estável |\n"
        else:
            report_content += f"| {metric} | N/A | ❌ Nunca estável |\n"
    
    # N_target final
    if stable_Ns:
        report_content += f"\n## Recomendação\n\n"
        report_content += f"**N_TARGET_FINAL = {N_target_final}**\n\n"
        report_content += f"Este é o tamanho mínimo recomendado para garantir estabilidade em todas as métricas analisadas.\n\n"
    else:
        report_content += f"\n## Recomendação\n\n"
        report_content += f"**Nenhuma métrica atingiu estabilidade**\n\n"
        report_content += f"Considere aumentar o tamanho da amostra ou revisar os critérios de estabilidade.\n\n"
    
    report_content += "## Arquivos Gerados\n\n"
    report_content += "- `stability_curves.csv`: Resultados brutos de todas as réplicas\n"
    report_content += "- `stability_summary.csv`: Estatísticas por tamanho e métrica\n"
    report_content += "- `stability_plots/`: Gráficos de estabilidade por métrica\n"
    
    # Salvar relatório
    with open('analysis/stability_report.md', 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 Relatório salvo: analysis/stability_report.md")

if __name__ == "__main__":
    generate_final_report()














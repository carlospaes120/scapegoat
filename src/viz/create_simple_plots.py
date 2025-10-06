#!/usr/bin/env python3
"""
Script simples para criar gráficos básicos dos dados temporais
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def create_simple_plots():
    """
    Cria gráficos simples dos dados temporais
    """
    print("Criando graficos simples...")
    
    # Carregar dados
    df = pd.read_csv('results/metrics_by_window.csv')
    print(f"Carregados {len(df)} registros")
    
    # Converter timestamps
    df['t_start'] = pd.to_datetime(df['t_start'])
    df['t_end'] = pd.to_datetime(df['t_end'])
    
    # Criar diretório de saída
    os.makedirs('figs', exist_ok=True)
    
    # 1. Gráfico de número de nós e arestas
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.plot(df['t_start'], df['n_nodes'], 'o-', label='Nós', linewidth=2)
    plt.plot(df['t_start'], df['n_edges'], 's-', label='Arestas', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Contagem')
    plt.title('Evolução da Rede')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(df['t_start'], df['density'], 'o-', color='green', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Densidade')
    plt.title('Densidade da Rede')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figs/network_evolution.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Salvo: figs/network_evolution.png")
    
    # 2. Gráfico de métricas de centralização
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.plot(df['t_start'], df['topk_pr_share_k5'], 'o-', label='Top-5', linewidth=2)
    plt.plot(df['t_start'], df['topk_pr_share_k10'], 's-', label='Top-10', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Share')
    plt.title('Centralização PageRank')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 2)
    plt.plot(df['t_start'], df['betweenness_centralization'], 'o-', color='red', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Centralização')
    plt.title('Centralização Betweenness')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 3)
    plt.plot(df['t_start'], df['n_communities'], 'o-', color='purple', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Número')
    plt.title('Número de Comunidades')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 4)
    plt.plot(df['t_start'], df['modularity'], 'o-', color='orange', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Modularidade')
    plt.title('Modularidade')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figs/centralization_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Salvo: figs/centralization_metrics.png")
    
    # 3. Gráfico de métricas de burst
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.plot(df['t_start'], df['peak_mean'], 'o-', label='Média', linewidth=2)
    plt.plot(df['t_start'], df['peak_median'], 's-', label='Mediana', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Atividade')
    plt.title('Métricas de Burst')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    # Marcar onset e climax
    onset_times = df[df['onset_flag'] == True]['t_start']
    climax_times = df[df['climax_flag'] == True]['t_start']
    
    plt.plot(df['t_start'], df['peak_mean'], 'o-', linewidth=2)
    if len(onset_times) > 0:
        plt.scatter(onset_times, df[df['onset_flag'] == True]['peak_mean'], 
                   color='green', s=100, label='Onset', zorder=5)
    if len(climax_times) > 0:
        plt.scatter(climax_times, df[df['climax_flag'] == True]['peak_mean'], 
                   color='red', s=100, label='Climax', zorder=5)
    
    plt.xlabel('Tempo')
    plt.ylabel('Atividade')
    plt.title('Burst com Marcadores')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figs/burst_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Salvo: figs/burst_analysis.png")
    
    # 4. Gráfico de métricas de rede
    plt.figure(figsize=(12, 8))
    
    plt.subplot(2, 2, 1)
    plt.plot(df['t_start'], df['avg_path_len'], 'o-', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Comprimento Médio')
    plt.title('Comprimento Médio do Caminho')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 2)
    plt.plot(df['t_start'], df['eff_diameter'], 'o-', color='blue', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Diâmetro')
    plt.title('Diâmetro Efetivo')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 3)
    plt.plot(df['t_start'], df['graph_density'], 'o-', color='green', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Densidade')
    plt.title('Densidade do Grafo')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 2, 4)
    plt.plot(df['t_start'], df['largest_community_size'], 'o-', color='purple', linewidth=2)
    plt.xlabel('Tempo')
    plt.ylabel('Tamanho')
    plt.title('Maior Comunidade')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figs/network_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Salvo: figs/network_metrics.png")
    
    print("\nGraficos criados com sucesso!")
    print("Arquivos gerados:")
    print("- figs/network_evolution.png")
    print("- figs/centralization_metrics.png") 
    print("- figs/burst_analysis.png")
    print("- figs/network_metrics.png")

if __name__ == "__main__":
    create_simple_plots()

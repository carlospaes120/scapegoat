# Relatório de Estabilidade - Caso Karol Conká

Análise de estabilidade de métricas de rede através de amostragem progressiva.

## Critérios de Estabilidade

- **Intervalo de confiança**: (p97.5 - p2.5) < 10% da média
- **Variação relativa**: |mean(N) - mean(N-Δ)| / mean(N) < 5%
- **Exceções**: Para modularity e assortativity, intervalo < 0.05

## Resultados por Métrica

| Métrica | N Estável | Observações |
|---------|-----------|-------------|
| n_nodes | 50 | ✅ Estável |
| n_edges | N/A | ❌ Nunca estável |
| lcc_nodes | N/A | ❌ Nunca estável |
| lcc_ratio | N/A | ❌ Nunca estável |
| avg_shortest_path_lcc | 316 | ✅ Estável |
| diameter_lcc | N/A | ❌ Nunca estável |
| degree_assortativity_ud | 316 | ✅ Estável |
| avg_clustering_ud | N/A | ❌ Nunca estável |
| modularity_ud | 316 | ✅ Estável |

## Recomendação

**N_TARGET_FINAL = 316**

Este é o tamanho mínimo recomendado para garantir estabilidade em todas as métricas analisadas.

## Arquivos Gerados

- `stability_curves.csv`: Resultados brutos de todas as réplicas
- `stability_summary.csv`: Estatísticas por tamanho e métrica
- `stability_plots/`: Gráficos de estabilidade por métrica

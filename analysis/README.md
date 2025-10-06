# Análise do BehaviorSpace - Caso Karol Conká

Este diretório contém scripts para análise dos dados de simulação do NetLogo BehaviorSpace comparados com as métricas empíricas do caso Karol Conká.

## Instalação

```bash
pip install pandas numpy
```

## Uso

```bash
python analysis/analyze_behaviorspace.py
```

## Arquivos Gerados

- `bs_report.csv`: Relatório completo com todas as simulações, erros e scores
- `bs_top.md`: Relatório Markdown dos top 20 runs com parâmetros e métricas

## Métricas Alvo

O script compara as simulações contra as seguintes métricas empíricas:

- **largest_wcc_nodes**: 191
- **degree_assortativity_ud**: -0.39
- **modularity_ud**: 0.64
- **avg_shortest_path_lcc**: 3.17
- **diameter_lcc**: 7
- **avg_clustering_ud**: 0.00
- **n_nodes**: 318
- **n_edges**: 304

## Estrutura dos Dados

O script espera encontrar arquivos CSV no padrão `data/behaviorspace/*.csv` com as seguintes colunas:

- Parâmetros de simulação (friendliness, skepticism, numnodes, etc.)
- Métricas de rede (largest_wcc_nodes, degree_assortativity_ud, etc.)

## Algoritmo de Scoring

- **Erro relativo** para a maioria das métricas
- **Erro absoluto** para degree_assortativity_ud e avg_clustering_ud
- **Penalidade extra** para n_nodes e n_edges se saírem do range de ±10%

## Saída

O script gera:

1. Resumo dos 10 melhores runs
2. Estatísticas por parâmetro (média, desvio, min, max)
3. Arquivo CSV com todas as simulações ordenadas por score
4. Relatório Markdown dos top 20 runs

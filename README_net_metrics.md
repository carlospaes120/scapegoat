# 📊 Net Metrics - Script de Métricas de Rede

Script robusto para calcular métricas de rede a partir de diferentes formatos de entrada (JSONL, CSV, GEXF).

## 🚀 Instalação

```bash
pip install -r requirements.txt
```

## 📋 Dependências

- `pandas`
- `networkx>=3.0`
- `python-louvain`

## 🎯 Funcionalidades

### Métricas de Nós
- **In-degree/Out-degree**: Grau de entrada e saída
- **PageRank**: Centralidade de PageRank
- **Betweenness**: Centralidade de intermediação (com amostragem opcional)
- **Comunidades**: Detecção de comunidades (Louvain)

### Métricas do Grafo
- **Nós e Arestas**: Contagem básica
- **Densidade**: Densidade do grafo
- **Centralização In-degree**: Centralização de Freeman (0-1)
- **Modularidade**: Modularidade de Louvain
- **Assortatividade**: Por stance (se disponível)

### Métricas da Vítima (Opcional)
- Métricas específicas do nó vítima
- Ego-rede (1-hop)
- Centralidades da vítima

## 📁 Formatos de Entrada

### 1. JSONL (Eventos)
```bash
python net_metrics.py --jsonl data/events.jsonl --victim "@usuario" --outdir outputs/caso
```

### 2. CSV (Arestas)
```bash
python net_metrics.py --edges data/edges.csv --weight-col weight --victim "@usuario" --outdir outputs/caso
```

### 3. GEXF (Grafo)
```bash
python net_metrics.py --gexf data/graph.gexf --victim "@usuario" --outdir outputs/caso
```

## 🔧 Parâmetros

### Modos de Entrada (obrigatório um)
- `--jsonl`: Arquivos JSONL com eventos
- `--edges`: CSV com arestas (source,target[,weight])
- `--gexf`: Arquivo GEXF

### Parâmetros Opcionais
- `--victim`: Aliases da vítima (separados por vírgula)
- `--outdir`: Diretório de saída
- `--weight-col`: Nome da coluna de peso no CSV
- `--btw-sample`: Amostragem para betweenness (0=completo)
- `--min-degree`: Grau mínimo para manter nós
- `--log`: Nível de log (DEBUG, INFO, WARNING, ERROR)

## 📊 Saídas

### Arquivos Gerados
- `node_metrics.csv`: Métricas de todos os nós
- `graph_metrics.json`: Métricas do grafo
- `victim_metrics.json`: Métricas da vítima (se especificada)
- `graph.gexf`: Grafo para visualização no Gephi

### Estrutura dos Dados

#### node_metrics.csv
```csv
node,in_degree,out_degree,pagerank,betweenness,community,stance
@usuario1,5,2,0.001234,0.000567,0,
@usuario2,10,1,0.002345,0.001234,1,
```

#### graph_metrics.json
```json
{
  "n_nodes": 1552,
  "n_edges": 1080,
  "density": 0.000449,
  "in_degree_centralization": 0.089286,
  "modularity": 0.961014,
  "assortativity_stance": null
}
```

## 🎯 Exemplos de Uso

### Exemplo 1: Análise Básica
```bash
python net_metrics.py \
  --jsonl data/karol_conka.jsonl \
  --victim "@karolconka" \
  --outdir outputs/karol_net \
  --btw-sample 100
```

### Exemplo 2: Análise Completa
```bash
python net_metrics.py \
  --jsonl data/monark.jsonl \
  --victim "@monark" \
  --outdir outputs/monark_net \
  --btw-sample 0 \
  --min-degree 2 \
  --log DEBUG
```

### Exemplo 3: Múltiplos Arquivos
```bash
python net_metrics.py \
  --jsonl data/caso1.jsonl data/caso2.jsonl \
  --victim "@vítima1,@vítima2" \
  --outdir outputs/combined \
  --btw-sample 200
```

### Exemplo 4: A partir de CSV
```bash
python net_metrics.py \
  --edges data/edges.csv \
  --weight-col weight \
  --victim "@vítima" \
  --outdir outputs/csv_analysis
```

### Exemplo 5: A partir de GEXF
```bash
python net_metrics.py \
  --gexf data/graph.gexf \
  --victim "@vítima" \
  --outdir outputs/gexf_analysis
```

## 🔍 Validações

O script inclui validações automáticas:
- ✅ `n_nodes > 0`
- ✅ `n_edges > 0`
- ✅ `in_degree_centralization` em [0,1] ou NaN
- ✅ `modularity` em [-0.5,1] ou NaN

## 🛠️ Robustez

### Tratamento de Erros
- **Esquemas variados**: Suporte a diferentes formatos de JSONL
- **Campos ausentes**: Tratamento gracioso de campos faltantes
- **Dados inválidos**: Logging de erros sem interromper execução
- **Grafos pequenos**: Validações para grafos com poucos nós

### Performance
- **Amostragem**: Betweenness com amostragem para grafos grandes
- **Filtros**: Remoção de nós de baixo grau
- **Memória**: Processamento eficiente de grandes datasets

## 📈 Métricas Calculadas

### Centralização In-degree (Freeman)
```
C = Σ(max_degree - degree_i) / ((n-1)(n-2))
```

### Modularidade (Louvain)
- Detecção de comunidades
- Cálculo da modularidade
- Atribuição de comunidade a cada nó

### PageRank
- Algoritmo padrão com α=0.85
- Pesos das arestas considerados

### Betweenness
- Centralidade de intermediação
- Amostragem opcional para performance

## 🎨 Visualização

Os arquivos `.gexf` gerados podem ser abertos no **Gephi** para visualização:
- Nós coloridos por comunidade
- Tamanho proporcional ao PageRank
- Arestas com pesos

## 🔧 Troubleshooting

### Problemas Comuns

1. **"Vítima não encontrada"**
   - Verifique se o alias está correto
   - Use múltiplos aliases: `--victim "@user1,@user2"`

2. **"Erro de encoding"**
   - Arquivos JSONL devem estar em UTF-8
   - Use `--log DEBUG` para mais detalhes

3. **"Grafo muito grande"**
   - Use `--btw-sample` para amostragem
   - Use `--min-degree` para filtrar nós

4. **"Campos ausentes"**
   - O script é robusto a esquemas variados
   - Campos faltantes são tratados graciosamente

## 📚 Referências

- **NetworkX**: Biblioteca de análise de redes
- **Louvain**: Algoritmo de detecção de comunidades
- **PageRank**: Algoritmo de centralidade
- **Freeman**: Centralização de redes

## 🤝 Contribuição

Para melhorias ou correções:
1. Identifique o problema
2. Proponha solução
3. Teste com diferentes datasets
4. Documente mudanças

## 📄 Licença

Este script segue a mesma licença do projeto principal.

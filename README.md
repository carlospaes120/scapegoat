# Scapegoat Pipeline - Análise de Cancelamento no Twitter

Pipeline reprodutível em Python para processar casos de "cancelamento" no X/Twitter e gerar figuras e métricas de análise de rede.

## 🆕 Novo: Modelo NetLogo Instrumentado

Este repositório agora inclui um **modelo NetLogo completamente instrumentado** para coleta de dados e comparação com dados empíricos do Twitter.

**🚀 Início Rápido**: Veja [`QUICK_START.md`](QUICK_START.md)  
**📚 Documentação Completa**: Veja [`README_DATA_COLLECTION.md`](README_DATA_COLLECTION.md)

**Principais recursos**:
- ✅ Exportação automática de eventos (CSV)
- ✅ Séries temporais completas (por tick)
- ✅ Snapshots de rede (nós + arestas)
- ✅ Geração de GEXF/GraphML para Gephi
- ✅ Scripts de análise em Python
- ✅ Pipeline de teste integrado

## 🚀 Instalação e Configuração

### 1. Criar ambiente virtual
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Preparar dados
Crie a estrutura de diretórios e adicione seus arquivos JSONL:
```bash
mkdir -p data/jsonl
# Adicione seus arquivos .jsonl em data/jsonl/
# Exemplo: karol_conka.jsonl, monark.jsonl, wagner_schwartz.jsonl, eduardo_bueno.jsonl
```

## 📊 Execução

### Análise completa (recomendado)
```bash
python run_all.py
```

### Opções avançadas
```bash
# Especificar diretórios
python run_all.py --data-dir ./data/jsonl --output-dir ./outputs

# Alterar número de top usuários
python run_all.py --top-n 50

# Logging verboso
python run_all.py --verbose
```

## 📁 Estrutura do Projeto

```
/
├── analysis/                 # Código de análise
│   ├── process_jsonl.py     # Processamento e normalização
│   ├── build_graph.py       # Construção de grafos
│   ├── metrics_reports.py   # Cálculo de métricas
│   ├── plots.py             # Geração de visualizações
│   └── compare_cases.py     # Análise comparativa
├── data/
│   └── jsonl/               # Arquivos JSONL de entrada
├── outputs/                 # Resultados da análise
│   ├── {case}/              # Por caso (ex: karol_conka/)
│   │   ├── figures/         # Gráficos PNG
│   │   └── tables/          # Tabelas CSV
│   └── compare/             # Análises comparativas
├── run_all.py               # Ponto de entrada principal
└── requirements.txt         # Dependências
```

## 📈 Métricas Calculadas

### Métricas Temporais
- Volume diário e horário de tweets
- Pico/Mediana e Pico/P90 (dia e hora)
- Distribuição temporal da atividade

### Métricas de Desigualdade
- Coeficiente de Gini (por tweet e por usuário)
- Índice Herfindahl-Hirschman (HHI)
- Top 1/5/10 share de engajamento

### Métricas de Rede
- Densidade, centralização in-degree
- PageRank e Betweenness centrality
- Modularidade (Louvain)
- Assortatividade por stance

### Métricas de Menções
- Top usuários mais mencionados
- Rede de menções/retweets/replies
- Distribuição de engajamento

## 🖼️ Figuras Geradas

### Por Caso
- `ts_day.png` - Volume temporal diário
- `peak_div_median_day.png` - Métricas de pico
- `gini_eng_tweet.png` - Desigualdade de engajamento
- `top_share_users.png` - Concentração de engajamento
- `top_mentions.png` - Top usuários mencionados
- `engagement_hist.png` - Distribuição de engajamento
- `mention_graph_preview.png` - Preview da rede

### Comparativas
- `compare_gini.png` - Gini entre casos
- `compare_hhi.png` - HHI entre casos
- `compare_top_shares.png` - Concentração entre casos
- `compare_ts_day_overlay.png` - Sobreposição temporal

## 📊 Tabelas Geradas

### Por Caso
- `top_users_by_engagement.csv` - Usuários por engajamento
- `top_targets_by_mentions.csv` - Alvos por menções
- `time_series_day.csv` - Série temporal diária
- `time_series_hour.csv` - Série temporal horária
- `metrics_{case}.csv` - Métricas de rede
- `top_pagerank.csv` - Top PageRank
- `top_betweenness.csv` - Top Betweenness

### Comparativas
- `cases_summary.csv` - Resumo de todos os casos

## 🔧 Formato dos Dados

O pipeline suporta esquemas variáveis de JSONL. A normalização automática produz:

### Colunas Canonizadas
- `tweet_id` (str) - ID único do tweet
- `created_at` (datetime) - Timestamp UTC
- `author` (str) - Autor do tweet (@username)
- `text` (str) - Texto do tweet
- `mentions` (list) - Lista de menções
- `is_retweet/is_quote/is_reply` (bool) - Tipo de tweet
- `engagement` (int) - Soma de likes+RTs+replies+quotes
- `stance` (str) - Posicionamento (se disponível)

### Detecção Automática
- **Menções**: `entities.user_mentions` ou regex `@([A-Za-z0-9_]{1,15})`
- **Retweets**: `referenced_tweets` ou heurística `RT @user:`
- **Engajamento**: `public_metrics` ou campos diretos
- **Timestamps**: Múltiplos formatos suportados

## 🎯 Casos Suportados

O pipeline detecta automaticamente casos baseado no nome do arquivo:
- `karol_conka.jsonl` → `karol_conka`
- `monark.jsonl` → `monark`
- `wagner_schwartz.jsonl` → `wagner_schwartz`
- `eduardo_bueno.jsonl` → `eduardo_bueno`

## 📋 Logs e Relatórios

- `outputs/log.txt` - Log completo da análise
- `outputs/analysis_report.txt` - Relatório resumido
- Console com progresso em tempo real

## 🛠️ Troubleshooting

### Erro: "Nenhum arquivo JSONL encontrado"
```bash
# Verificar estrutura
ls data/jsonl/
# Adicionar arquivos .jsonl
```

### Erro: "Sem dados válidos"
- Verificar formato do JSONL
- Verificar campos obrigatórios (id, created_at, author, text)
- Verificar encoding UTF-8

### Erro de memória
- Reduzir tamanho dos arquivos
- Usar chunks menores no processamento

## 📚 Dependências

- **pandas, numpy** - Manipulação de dados
- **matplotlib** - Visualizações
- **networkx** - Análise de redes
- **python-louvain** - Detecção de comunidades
- **scipy, scikit-learn** - Estatísticas
- **tqdm** - Progresso
- **orjson** - JSON rápido (opcional)

## 🤝 Contribuição

Para adicionar novos tipos de análise:
1. Modifique `analysis/metrics_reports.py` para novas métricas
2. Adicione funções de plot em `analysis/plots.py`
3. Integre em `analysis/compare_cases.py`

## 📄 Licença

Este projeto segue as mesmas diretrizes do projeto Scapegoat Dilemma.
# 🚀 Guia de Início Rápido - Modelo Scapegoat Instrumentado

## ⚡ Setup em 5 Minutos

### 1️⃣ Preparação (primeira vez)

```powershell
# No PowerShell, navegue até a pasta do projeto
cd C:\Users\Paes1\NETLOGO\scapegoat_pipeline_gephi

# Instale dependências Python (se ainda não tiver)
pip install pandas networkx matplotlib seaborn

# Teste se a pasta data/ existe
Test-Path data
# Se retornar False, crie:
New-Item -ItemType Directory -Path "data"
```

---

### 2️⃣ Teste com Dados de Exemplo (sem NetLogo)

```powershell
# Criar dados fictícios para testar o pipeline
python tools/create_sample_data.py

# Verificar integridade
python tools/verify_data.py

# Gerar GEXF
python tools/make_gexf.py

# Análise completa
python examples/analyze_simulation.py
```

**Resultado esperado**:
- ✅ `data/events.csv`, `timeseries.csv`, `nodes.csv`, `links_snapshot.csv` criados
- ✅ `data/network.gexf` e `data/network.graphml` gerados
- ✅ Gráficos salvos em `outputs/`

---

### 3️⃣ Uso com NetLogo (simulação real)

#### A) Configurar Interface

1. Abra `scapegoat_instrumented.nlogo` no NetLogo
2. Vá para a aba **Interface**
3. Adicione os botões seguindo o guia em [`INTERFACE_BUTTONS.md`](INTERFACE_BUTTONS.md)

**Botões mínimos necessários**:
- `Export nodes snapshot` → `export-nodes-snapshot`
- `Export links snapshot` → `export-links-snapshot`

*(Os headers são criados automaticamente no `setup`)*

#### B) Rodar Simulação

1. Configure parâmetros na Interface:
   - `numnodes`: 100 (padrão)
   - `friendliness`: 50 (padrão)
   - `skepticism`: 50 (padrão)
   - `scapegoat?`: On

2. Clique em **setup**
   - ✅ Mensagens no Command Center: "Criado: data/events.csv (header)" etc.

3. Clique em **go** (ou ative go-forever)
   - 🔄 Simulação roda e coleta dados automaticamente
   - 📊 `events.csv` e `timeseries.csv` crescem a cada tick

4. Após alguns ticks (ex: 100), pause e clique:
   - **Export nodes snapshot**
   - **Export links snapshot**

5. No terminal:
   ```powershell
   python tools/make_gexf.py
   ```

#### C) Visualizar no Gephi

1. Abra o Gephi
2. **File → Open** → `data/network.gexf`
3. Escolha **Undirected graph** (ou Directed, se preferir)
4. No **Data Laboratory**, veja os atributos:
   - `kind` (leader, victim, neutral, etc.)
   - `health`, `tension`, `cc_node`, `degree`
5. No **Overview**:
   - Execute **Force Atlas 2** para layout
   - Colorir nós por `kind` (Partition panel)
   - Dimensionar nós por `degree` ou `health` (Ranking panel)

---

## 📊 Análise Rápida em Python

### Carregar e Visualizar Eventos

```python
import pandas as pd
import matplotlib.pyplot as plt

# Carregar eventos
events = pd.read_csv("data/events.csv")

# Ver distribuição de tipos
print(events['etype'].value_counts())

# Plotar eventos acumulados
events_by_tick = events.groupby('tick').size().cumsum()
plt.plot(events_by_tick.index, events_by_tick.values)
plt.xlabel('Tick')
plt.ylabel('Eventos Acumulados')
plt.title('Evolução de Acusações')
plt.show()
```

### Carregar e Visualizar Séries Temporais

```python
# Carregar séries
ts = pd.read_csv("data/timeseries.csv")

# Plotar evolução de vítimas
plt.plot(ts['tick'], ts['n_victims'], label='Vítimas')
plt.plot(ts['tick'], ts['n_leaders'], label='Líderes')
plt.xlabel('Tick')
plt.ylabel('Número de Agentes')
plt.title('Evolução da População')
plt.legend()
plt.show()
```

### Análise de Rede com NetworkX

```python
import networkx as nx

# Carregar grafo
G = nx.read_gexf("data/network.gexf")

# Estatísticas básicas
print(f"Nós: {G.number_of_nodes()}")
print(f"Arestas: {G.number_of_edges()}")
print(f"Densidade: {nx.density(G):.4f}")

# Centralidade de grau
degree_centrality = nx.degree_centrality(G)
top_5 = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
print("Top 5 nós por centralidade de grau:")
for node, cent in top_5:
    print(f"  Nó {node}: {cent:.4f}")
```

---

## 🔧 Troubleshooting Rápido

| Problema | Solução |
|---|---|
| ❌ "pasta data/ não existe" | `New-Item -ItemType Directory -Path "data"` |
| ❌ CSV não está sendo criado no NetLogo | Verifique permissões de escrita. Veja Command Center do NetLogo para erros. |
| ❌ `make_gexf.py` falha | Execute `pip install pandas networkx` |
| ❌ GEXF não abre no Gephi | Tente importar `network.graphml` em vez de `.gexf` |
| ❌ "No valid events loaded" | Execute a simulação por mais tempo até ocorrer uma acusação |

---

## 📁 Estrutura de Arquivos

```
scapegoat_pipeline_gephi/
├── data/                        # Dados exportados (criado ao rodar)
│   ├── events.csv               # Log de eventos
│   ├── timeseries.csv           # Séries temporais
│   ├── nodes.csv                # Snapshot de nós
│   ├── links_snapshot.csv       # Snapshot de arestas
│   ├── network.gexf             # Grafo para Gephi
│   └── network.graphml          # Alternativa ao GEXF
│
├── tools/                       # Scripts utilitários
│   ├── make_gexf.py             # Converter CSV → GEXF
│   ├── verify_data.py           # Verificar integridade
│   └── create_sample_data.py    # Criar dados de teste
│
├── examples/                    # Scripts de análise
│   └── analyze_simulation.py    # Análise completa com gráficos
│
├── outputs/                     # Gráficos gerados (criado ao rodar)
│   ├── events_analysis.png
│   ├── timeseries_analysis.png
│   └── network_analysis.png
│
├── scapegoat_instrumented.nlogo # Modelo NetLogo instrumentado
├── README_DATA_COLLECTION.md    # Documentação completa
├── CHANGES_SUMMARY.md           # Resumo de mudanças
├── INTERFACE_BUTTONS.md         # Guia de botões
└── QUICK_START.md               # Este arquivo
```

---

## 🎯 Casos de Uso

### Use Case 1: Calibração de Parâmetros

**Objetivo**: Ajustar `friendliness` e `skepticism` para match dados empíricos.

1. Rode simulação com `friendliness=30, skepticism=70`
2. Exporte dados: `events.csv`, `timeseries.csv`
3. Compare distribuição de `etype` com dados do Twitter:
   ```python
   sim = pd.read_csv("data/events.csv")
   emp = pd.read_json("notebooks/tweets_classified_monark.jsonl", lines=True)
   
   print("Simulado:", sim['etype'].value_counts(normalize=True))
   print("Empírico:", emp['type'].value_counts(normalize=True))
   ```
4. Ajuste parâmetros e repita

---

### Use Case 2: Comparação de Topologias

**Objetivo**: Comparar estrutura da rede simulada com rede Twitter.

1. Exporte snapshot: `nodes.csv`, `links_snapshot.csv`
2. Gere GEXF: `python tools/make_gexf.py`
3. Calcule métricas em ambas as redes:
   ```python
   # Rede simulada
   G_sim = nx.read_gexf("data/network.gexf")
   print("Simulado - CC:", nx.average_clustering(G_sim.to_undirected()))
   
   # Rede empírica (use scripts existentes)
   from scripts.net_metrics import calculate_metrics
   # ...
   ```

---

### Use Case 3: Análise Temporal de Rituals

**Objetivo**: Identificar padrões temporais de rituais.

1. Rode simulação por 1000 ticks
2. Analise `timeseries.csv`:
   ```python
   ts = pd.read_csv("data/timeseries.csv")
   
   # Identificar rituais (ritualtime > 0)
   rituals = ts[ts['ritualtime'] > 0]
   print(f"Total de rituais: {len(rituals)}")
   print(f"Intervalo médio: {rituals['tick'].diff().mean():.1f} ticks")
   ```

---

## 📚 Referências Rápidas

- **Documentação Completa**: [`README_DATA_COLLECTION.md`](README_DATA_COLLECTION.md)
- **Mudanças no Código**: [`CHANGES_SUMMARY.md`](CHANGES_SUMMARY.md)
- **Botões da Interface**: [`INTERFACE_BUTTONS.md`](INTERFACE_BUTTONS.md)
- **NetLogo Extensions**:
  - [CSV Extension](https://ccl.northwestern.edu/netlogo/docs/csv.html)
  - [NW Extension](https://ccl.northwestern.edu/netlogo/docs/nw.html)
- **NetworkX GEXF**: [Docs](https://networkx.org/documentation/stable/reference/readwrite/gexf.html)
- **Gephi**: [gephi.org](https://gephi.org/)

---

## 🎓 Próximos Passos

1. ✅ **Setup completo** (este guia)
2. 📖 **Leia**: [`README_DATA_COLLECTION.md`](README_DATA_COLLECTION.md) para detalhes completos
3. 🧪 **Teste**: Execute com dados de exemplo (`create_sample_data.py`)
4. 🚀 **Rode**: Simulação real no NetLogo
5. 📊 **Analise**: Use scripts em `examples/` e `scripts/`
6. 🔬 **Compare**: Dados simulados vs dados empíricos do Twitter

---

**Versão**: 1.0  
**Data**: Outubro 2025  
**Contato**: Ver README.md do projeto


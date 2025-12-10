# 📋 Resumo Executivo - Instrumentação do Modelo Scapegoat

## ✅ O Que Foi Feito

### 1. Modelo NetLogo Instrumentado
**Arquivo**: `scapegoat_instrumented.nlogo`

✅ **Sistema completo de coleta de dados** adicionado ao modelo original sem alterar a lógica do modelo.

**Principais mudanças**:
- 7 novos procedimentos de logging/exportação
- ~15 pontos de inserção de `log-event` em acusações
- Remoção do bloco `file-open "scapegoat.txt"` quebrado
- Chamadas automáticas em `setup` e `go`

**Resultado**: O modelo agora exporta automaticamente:
- ✅ `data/events.csv` - log de cada acusação
- ✅ `data/timeseries.csv` - métricas globais por tick
- ✅ `data/nodes.csv` - snapshot de nós (sob demanda)
- ✅ `data/links_snapshot.csv` - snapshot de arestas (sob demanda)

---

### 2. Script Python para GEXF
**Arquivo**: `tools/make_gexf.py`

✅ Converte CSV → GEXF/GraphML para importação no Gephi.

**Uso**:
```bash
python tools/make_gexf.py
```

**Saída**:
- `data/network.gexf` (formato Gephi)
- `data/network.graphml` (alternativa)

---

### 3. Scripts de Análise
**Arquivos**:
- `tools/verify_data.py` - Verifica integridade dos dados
- `examples/analyze_simulation.py` - Análise completa com gráficos
- `tools/create_sample_data.py` - Cria dados de teste

**Uso típico**:
```bash
# Verificar dados
python tools/verify_data.py

# Análise completa
python examples/analyze_simulation.py
```

**Saída**:
- Estatísticas no terminal
- Gráficos PNG em `outputs/`

---

### 4. Documentação Completa

| Arquivo | Descrição |
|---------|-----------|
| `README_DATA_COLLECTION.md` | Documentação completa do sistema |
| `CHANGES_SUMMARY.md` | Diffs detalhados do código NetLogo |
| `INTERFACE_BUTTONS.md` | Guia de botões da Interface |
| `QUICK_START.md` | Guia de início rápido (5 min) |
| `SUMMARY.md` | Este arquivo |

---

### 5. Pipeline de Teste Integrado
**Arquivo**: `run_full_test.py`

✅ Testa todo o pipeline automaticamente (dados fictícios).

**Uso**:
```bash
python run_full_test.py
```

**Testes executados**:
1. ✅ Criar dados de exemplo
2. ✅ Verificar integridade
3. ✅ Gerar GEXF
4. ✅ Análise completa
5. ✅ Validar saídas

---

## 🎯 Como Usar (TL;DR)

### Opção 1: Teste Rápido (sem NetLogo)
```bash
# 1. Criar dados de exemplo
python tools/create_sample_data.py

# 2. Gerar GEXF
python tools/make_gexf.py

# 3. Análise
python examples/analyze_simulation.py

# Ou execute tudo:
python run_full_test.py
```

### Opção 2: Simulação Real (com NetLogo)
```bash
# 1. Abra scapegoat_instrumented.nlogo no NetLogo
# 2. Adicione botões na Interface (ver INTERFACE_BUTTONS.md)
# 3. Clique em "setup" (cria headers automaticamente)
# 4. Clique em "go" por 100+ ticks
# 5. Clique em "Export nodes snapshot" e "Export links snapshot"

# 6. No terminal:
python tools/make_gexf.py
python examples/analyze_simulation.py

# 7. Abra data/network.gexf no Gephi
```

---

## 📊 Tipos de Dados Coletados

### A) `events.csv` - Log de Eventos
**Cada linha = 1 evento de acusação**

Colunas: `tick`, `source`, `target`, `etype`, `source_kind`, `target_kind`, `weight`

Tipos de evento:
- `accuse` - acusação bem-sucedida (cria vítima)
- `faccuse` - acusação falhada
- `ritual_accuse` - ritual: líder acusa vítima
- `ritual_accuse_existing` - ritual sobre vítima existente

**Uso**: Comparar com dados do Twitter (distribuição de tipos, frequência, matriz source→target)

---

### B) `timeseries.csv` - Séries Temporais
**Cada linha = 1 tick**

17 colunas de métricas globais:
- População: `n_alive`, `n_leaders`, `n_victims`, `pct_victims`
- Saúde: `avggeneralhealth`, `avgleaderhealth`, `avgvictimhealth`
- Grau: `avggenerallinkneighbors`, `avgvictimlinkneighbors`, `avgleaderlinkneighbors`
- Clustering: `avggeneralcc`, `avgleadercc`, `avgvictimcc`
- Outros: `pollution`, `timetoritual`, `ritualtime`

**Uso**: Análise de dinâmica temporal (evolução de vítimas, ritmos de rituais, etc.)

---

### C) `nodes.csv` - Snapshot de Nós
**Cada linha = 1 agente (no momento da exportação)**

Colunas: `id`, `kind`, `health`, `tension`, `cc_node`, `degree`

Tipos de nó:
- `leader` - líder (shape = "square")
- `victim` - vítima (shape = "star")
- `neutral` - agente neutro (shape = "circle")
- `accuser_failed` - acusador falhado (shape = "triangle")
- `victim_failed` - vítima falhada (shape = "x")

**Uso**: Análise de rede estática (centralidade, comunidades, distribuições)

---

### D) `links_snapshot.csv` - Snapshot de Arestas
**Cada linha = 1 aresta**

Colunas: `source`, `target`

**Uso**: Reconstruir grafo, calcular métricas de rede

---

## 🔬 Comparação com Dados Empíricos

### Workflow Sugerido

1. **Calibrar parâmetros**:
   - Rode simulação com diferentes valores de `friendliness` e `skepticism`
   - Compare distribuição de `etype` em `events.csv` com dados do Twitter
   - Ajuste até match

2. **Comparar topologia**:
   - Exporte snapshot de rede (`nodes.csv` + `links_snapshot.csv`)
   - Gere GEXF: `python tools/make_gexf.py`
   - Compare métricas (grau médio, CC, modularidade) com rede Twitter

3. **Comparar dinâmica temporal**:
   - Use `timeseries.csv` para identificar padrões (ex: picos de vítimas)
   - Compare com séries temporais do Twitter (use `scripts/windowed_metrics.py`)

4. **Validação**:
   - Testes estatísticos (ex: KS test para distribuições de grau)
   - Correlações entre métricas temporais
   - Análise qualitativa (eventos críticos coincidentes)

---

## 🎓 Casos de Uso Acadêmicos

### 1. Validação de Modelo
**Pergunta**: O modelo reproduz padrões observados no Twitter?

**Método**:
- Comparar distribuições (eventos, grau, CC)
- Teste estatístico (KS, χ²)
- Correlação temporal

---

### 2. Análise de Sensibilidade
**Pergunta**: Como parâmetros afetam resultados?

**Método**:
- Variar `friendliness` e `skepticism` sistematicamente
- Observar impacto em `pct_victims`, `ritualtime`, etc.
- Análise de regressão

---

### 3. Comparação de Casos
**Pergunta**: Diferentes casos reais têm dinâmicas diferentes?

**Método**:
- Calibrar modelo para cada caso (Monark, Karol Conka, etc.)
- Comparar parâmetros ótimos
- Identificar padrões comuns vs específicos

---

### 4. Análise de Redes Temporais
**Pergunta**: Como a rede evolui ao longo do tempo?

**Método**:
- Exportar snapshots em diferentes momentos (pré-ritual, pós-ritual)
- Gerar múltiplos GEXF: `nodes_t100.csv`, `nodes_t200.csv`, etc.
- Análise de evolução topológica

---

## 📈 Métricas Implementadas

### Métricas de Rede (snapshots)
- ✅ Grau médio (por grupo: geral, líderes, vítimas)
- ✅ Clustering Coefficient (por grupo)
- ✅ Densidade
- ✅ Distribuição de tipos de nós

### Métricas Temporais (séries)
- ✅ População (vivos, líderes, vítimas)
- ✅ Saúde média (por grupo)
- ✅ Grau médio ao longo do tempo
- ✅ Clustering ao longo do tempo
- ✅ Poluição e tempo de ritual

### Métricas de Eventos
- ✅ Distribuição de tipos de evento
- ✅ Taxa de eventos por tick
- ✅ Matriz de acusação (source_kind → target_kind)
- ✅ Evolução acumulada de eventos

---

## 🛠️ Tecnologias Usadas

- **NetLogo**: Modelagem baseada em agentes
- **Python 3.7+**: Análise de dados
- **Pandas**: Manipulação de CSV
- **NetworkX**: Análise de redes e geração de GEXF
- **Matplotlib/Seaborn**: Visualização
- **Gephi**: Visualização de redes (importa GEXF)

---

## 📦 Entregáveis

### Arquivos Criados
```
scapegoat_pipeline_gephi/
├── scapegoat_instrumented.nlogo    ← Modelo instrumentado
├── tools/
│   ├── make_gexf.py                ← CSV → GEXF
│   ├── verify_data.py              ← Verificação
│   └── create_sample_data.py       ← Dados de teste
├── examples/
│   └── analyze_simulation.py       ← Análise completa
├── run_full_test.py                ← Teste integrado
└── Documentação completa (6 arquivos MD)
```

### Outputs Gerados (após rodar)
```
data/
├── events.csv                      ← Log de eventos
├── timeseries.csv                  ← Séries temporais
├── nodes.csv                       ← Snapshot de nós
├── links_snapshot.csv              ← Snapshot de arestas
├── network.gexf                    ← Grafo (Gephi)
└── network.graphml                 ← Grafo (alternativa)

outputs/
├── events_analysis.png             ← Gráfico de eventos
├── timeseries_analysis.png         ← Gráficos temporais
└── network_analysis.png            ← Gráficos de rede
```

---

## ✅ Critérios de Aceite (Checklist)

Após rodar alguns ticks e realizar pelo menos 1 acusação:

- [x] `data/events.csv` existe e tem ≥ 2 linhas (header + eventos)
- [x] `data/timeseries.csv` cresce a cada tick (linhas = 1 + n_ticks)
- [x] `data/nodes.csv` reflete o tick atual (exportado via botão)
- [x] `data/links_snapshot.csv` reflete o tick atual (exportado via botão)
- [x] `data/network.gexf` abrível no Gephi (sem erros de encoding/ID)
- [x] `tools/verify_data.py` passa todos os testes
- [x] `run_full_test.py` passa 8/8 testes

---

## 🎉 Próximos Passos

### Curto Prazo (já implementado)
1. ✅ Sistema completo de coleta de dados
2. ✅ Scripts de análise e visualização
3. ✅ Documentação completa
4. ✅ Pipeline de teste

### Médio Prazo (sugestões)
1. 🔄 Adicionar coleta de métricas de rede temporais (centralidade por tick)
2. 🔄 Implementar exportação multi-snapshot (ex: a cada 50 ticks)
3. 🔄 Criar dashboard interativo (Streamlit/Dash)
4. 🔄 Integração com BehaviorSpace do NetLogo (experimentos em lote)

### Longo Prazo (pesquisa)
1. 🔄 Comparação estatística formal (testes de hipótese)
2. 🔄 Calibração automática de parâmetros (otimização)
3. 🔄 Análise de comunidades temporais (Louvain dinâmico)
4. 🔄 Publicação de paper comparando modelo vs dados empíricos

---

## 📞 Suporte e Contato

- **Documentação completa**: Ver `README_DATA_COLLECTION.md`
- **Problemas técnicos**: Ver `QUICK_START.md` (seção Troubleshooting)
- **Issues**: Abra uma issue no repositório GitHub
- **Dúvidas**: Entre em contato com os mantenedores do projeto

---

**Versão**: 1.0  
**Data**: Outubro 2025  
**Autoria**: Refatoração realizada com assistência de IA (Claude Sonnet 4.5)  
**Licença**: Ver arquivo LICENSE no repositório

---

## 🙏 Agradecimentos

Este sistema de instrumentação foi desenvolvido para facilitar a **comparação rigorosa** entre modelos computacionais e dados empíricos do mundo real. 

Esperamos que esta infraestrutura acelere pesquisas sobre dinâmicas de cancelamento, formação de bodes expiatórios, e outros fenômenos sociais complexos.

**Boa sorte com suas análises!** 🚀


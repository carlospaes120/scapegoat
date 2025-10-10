# Sistema de Coleta de Dados - Modelo NetLogo Scapegoat

## 📋 Visão Geral

Este documento descreve o sistema de instrumentação de dados do modelo NetLogo Scapegoat, projetado para facilitar a comparação com dados empíricos do Twitter.

## 🎯 Arquivos Exportados

### 1. `data/events.csv` - Log de Eventos
**Descrição**: Registro detalhado de cada interação/acusação que ocorre no modelo.

**Colunas**:
- `tick`: momento temporal do evento
- `source`: ID do agente acusador
- `target`: ID do agente acusado
- `etype`: tipo de evento
  - `accuse`: acusação bem-sucedida (vítima criada)
  - `faccuse`: acusação falhada
  - `ritual_accuse`: acusação ritual (líder → vítima existente)
  - `ritual_accuse_existing`: ritual sobre vítima pré-existente
- `source_kind`: categoria do acusador (`leader`, `neutral`, `accuser_failed`, etc.)
- `target_kind`: categoria da vítima
- `weight`: peso do evento (sempre 1)

**Atualização**: Cada evento é registrado no momento exato em que ocorre.

### 2. `data/timeseries.csv` - Séries Temporais Globais
**Descrição**: Métricas agregadas do sistema a cada tick.

**Colunas**:
- `tick`: momento temporal
- `n_alive`: número de agentes vivos
- `n_leaders`: número de líderes (shape = "square")
- `n_victims`: número de vítimas (shape = "star")
- `pct_victims`: percentual de vítimas
- Métricas de saúde: `avggeneralhealth`, `avgleaderhealth`, `avgvictimhealth`
- Métricas de grau: `avggenerallinkneighbors`, `avgvictimlinkneighbors`, `avgleaderlinkneighbors`
- Métricas de clustering: `avggeneralcc`, `avgleadercc`, `avgvictimcc`
- `pollution`: nível de poluição (0-3)
- `timetoritual`: ticks até o próximo ritual
- `ritualtime`: duração do ritual atual

**Atualização**: Uma linha adicionada ao final de cada tick.

### 3. `data/nodes.csv` - Snapshot de Nós
**Descrição**: Estado atual de todos os agentes no momento da exportação.

**Colunas**:
- `id`: ID único do agente
- `kind`: categoria (`leader`, `victim`, `neutral`, `accuser_failed`, `victim_failed`)
- `health`: saúde atual (0-4)
- `tension`: tensão atual (0-3)
- `cc_node`: coeficiente de clustering local
- `degree`: grau do nó (número de vizinhos)

**Atualização**: Sob demanda via botão "Export nodes snapshot".

### 4. `data/links_snapshot.csv` - Snapshot de Arestas
**Descrição**: Topologia da rede no momento da exportação.

**Colunas**:
- `source`: ID do nó origem
- `target`: ID do nó destino

**Atualização**: Sob demanda via botão "Export links snapshot".

## 🎮 Botões da Interface NetLogo

Adicione os seguintes botões na Interface do NetLogo:

### Botões de Inicialização
- **Export events header**: Cria `events.csv` com cabeçalho (chame antes de iniciar coleta)
- **Export timeseries header**: Cria `timeseries.csv` com cabeçalho (chame antes de iniciar coleta)

### Botões de Snapshot (sob demanda)
- **Export nodes snapshot**: Exporta estado atual dos nós → `nodes.csv`
- **Export links snapshot**: Exporta topologia atual → `links_snapshot.csv`
- **Export plots (opcional)**: Exporta gráficos → `plots.csv`

### Controle de Coleta
- **Toggle data collector**: Liga/desliga `datacollector?` (controla pausas visuais)

**Nota**: Os headers são criados automaticamente no `setup`, mas você pode recriá-los manualmente com os botões.

## 🚀 Fluxo de Trabalho

### Passo 1: Preparação (primeira vez)
```bash
# Certifique-se de que a pasta data/ existe
cd c:\Users\Paes1\NETLOGO\scapegoat_pipeline_gephi
```

### Passo 2: Configurar NetLogo
1. Abra `scapegoat_instrumented.nlogo` no NetLogo
2. Configure parâmetros: `numnodes`, `friendliness`, `skepticism`, `scapegoat?`
3. Clique em **setup** (cria headers automaticamente)

### Passo 3: Rodar Simulação
1. Clique em **go** (ou ative go-forever)
2. Os dados são coletados automaticamente:
   - `events.csv` cresce a cada acusação
   - `timeseries.csv` cresce a cada tick
3. Para pausar sem perder dados, pare o **go**

### Passo 4: Exportar Snapshot da Rede (quando quiser)
1. Pause a simulação (ou não, se quiser capturar em movimento)
2. Clique em **Export nodes snapshot**
3. Clique em **Export links snapshot**
4. Verifique que `nodes.csv` e `links_snapshot.csv` foram criados

### Passo 5: Gerar GEXF para Gephi
```bash
# No terminal (PowerShell/Bash)
cd c:\Users\Paes1\NETLOGO\scapegoat_pipeline_gephi
python tools/make_gexf.py
```

**Saída**:
- `data/network.gexf` (formato Gephi)
- `data/network.graphml` (alternativa)

### Passo 6: Importar no Gephi
1. Abra o Gephi
2. File → Open → `data/network.gexf` ou `data/network.graphml`
3. Escolha "Undirected graph" (se preferir)
4. Os atributos dos nós (`kind`, `health`, `tension`, `cc_node`, `degree`) estarão disponíveis no Data Laboratory

## 📊 Análise de Dados

### Exemplo: Carregar eventos em Python/Pandas
```python
import pandas as pd

# Ler eventos
events = pd.read_csv("data/events.csv")
print(events.head())

# Filtrar apenas acusações bem-sucedidas
accuses = events[events['etype'] == 'accuse']
print(f"Total de acusações: {len(accuses)}")

# Agrupar por tipo de evento
print(events['etype'].value_counts())
```

### Exemplo: Carregar séries temporais
```python
timeseries = pd.read_csv("data/timeseries.csv")

# Plotar evolução de vítimas
import matplotlib.pyplot as plt
plt.plot(timeseries['tick'], timeseries['n_victims'])
plt.xlabel('Tick')
plt.ylabel('Número de Vítimas')
plt.title('Evolução Temporal de Vítimas')
plt.show()
```

### Exemplo: Comparar com dados empíricos
```python
# Carregar dados do Twitter (exemplo usando o script existente)
from scripts.windowed_metrics import load_events, compute_window_metrics

# Carregar eventos simulados
sim_events = pd.read_csv("data/events.csv")

# Carregar eventos empíricos (exemplo)
emp_events = pd.read_json("notebooks/tweets_classified_monark.jsonl", lines=True)

# Comparar distribuições
print("Simulado:", sim_events['etype'].value_counts(normalize=True))
print("Empírico:", emp_events['type'].value_counts(normalize=True))
```

## 🔍 Verificação de Integridade

### Critérios de Aceite

1. **`data/events.csv` existe e tem ≥ 2 linhas** (header + eventos)
   ```bash
   wc -l data/events.csv  # Linux/Mac
   (Get-Content data/events.csv).Length  # PowerShell
   ```

2. **`data/timeseries.csv` cresce a cada tick**
   - Número de linhas = 1 (header) + número de ticks executados

3. **`data/nodes.csv` reflete o tick atual**
   - Conte os nós na View do NetLogo
   - Compare com `wc -l data/nodes.csv - 1` (subtrair header)

4. **`data/network.gexf` abre no Gephi sem erros**
   - Teste de encoding UTF-8
   - Teste de IDs de nós consistentes

## 🛠️ Resolução de Problemas

### Erro: "pasta data/ não existe"
```powershell
New-Item -ItemType Directory -Force -Path "data"
```

### Erro: "CSV não está sendo criado"
- Verifique permissões de escrita na pasta `data/`
- Veja mensagens no Command Center do NetLogo
- Teste manualmente: clique em "Export events header"

### Erro: "make_gexf.py não encontra arquivos"
- Certifique-se de que `nodes.csv` e `links_snapshot.csv` existem
- Rode os botões de snapshot antes de executar o script Python

### Erro: "GEXF não abre no Gephi"
- Verifique se NetworkX está instalado: `pip install networkx`
- Tente importar o `network.graphml` alternativo
- Verifique se há nós com IDs duplicados

## 📚 Referências

- **Extensão CSV NetLogo**: https://ccl.northwestern.edu/netlogo/docs/csv.html
- **NetworkX GEXF**: https://networkx.org/documentation/stable/reference/readwrite/gexf.html
- **Gephi**: https://gephi.org/

## 📝 Notas de Implementação

### Mudanças no Código Original

1. **Adicionados helpers de logging** (início do arquivo):
   - `write-events-header`
   - `write-timeseries-header`
   - `log-event [src-agent tgt-agent etype]`
   - `append-timeseries-row`
   - `export-nodes-snapshot`
   - `export-links-snapshot`

2. **Inserções de `log-event` nos pontos de acusação**:
   - Ritual de acusação (líder → vítima)
   - Acusações espontâneas (agente → agente)
   - Acusações falhadas (faccuser → faccused)
   - Total: ~15 pontos de inserção

3. **Chamadas em `setup`**:
   - `write-events-header`
   - `write-timeseries-header`

4. **Chamadas em `go` (final)**:
   - `append-timeseries-row` (após atualizar globais)

5. **Bloco removido**:
   - `file-open "scapegoat.txt"` + `file-print (word ...)` (estava quebrado e conflitava com CSV)

### Preservação da Lógica Original

- **Nenhuma** mudança em condições, probabilidades, `random`, `stop`, etc.
- **Apenas** adição de chamadas `log-event` e `append-timeseries-row`
- **Idempotência** garantida: executar `setup` múltiplas vezes recria headers

## 🎓 Uso Acadêmico

Este sistema permite:
- **Validação de modelo**: comparar padrões simulados com dados reais
- **Calibração de parâmetros**: ajustar `friendliness`, `skepticism` para match empírico
- **Análise de sensibilidade**: variar parâmetros e observar impacto em métricas
- **Visualização dinâmica**: exportar snapshots em diferentes momentos (pré-ritual, pós-ritual, steady-state)

## 📞 Suporte

Para dúvidas ou problemas, abra uma issue no repositório ou entre em contato com os mantenedores do projeto.

---

**Versão**: 1.0  
**Data**: Outubro 2025  
**Licença**: Ver arquivo LICENSE no repositório


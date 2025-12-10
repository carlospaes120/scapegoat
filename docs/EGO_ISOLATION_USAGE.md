# Ego Isolation Timeseries - Guia de Uso

## 📋 Visão Geral

O script `ego_isolation_timeseries.py` calcula métricas de **isolamento da vítima** ao longo do tempo usando janelas deslizantes:

1. **ego_density** - Densidade do ego-network da vítima (quão conectados estão os vizinhos entre si)
2. **avg_dist_to_victim** - Distância média de todos os nós até a vítima (isolamento estrutural)

## 🎯 Casos de Uso

### Caso 1: Dados do Twitter (JSONL)

Você tem um arquivo JSONL com eventos de menção/retweet/reply já processados.

**Estrutura esperada:**
```json
{"src": "@usuario1", "dst": "@monark", "timestamp": "2024-01-15T10:30:00Z", ...}
{"src": "@usuario2", "dst": "@usuario3", "timestamp": "2024-01-15T11:45:00Z", ...}
```

**Comando:**
```bash
python scripts/ego_isolation_timeseries.py \
  --input data/twitter/monark_edges.jsonl \
  --format jsonl \
  --case_id monark \
  --victim @monark \
  --window 1D \
  --directed \
  --anchor_peak \
  --outdir outputs/isolation
```

---

### Caso 2: Dados da Simulação NetLogo

**Passo 1: Converter events.csv para formato esperado**

```bash
python tools/convert_netlogo_events_to_edges.py \
  --input data/events.csv \
  --output data/simulation_edges.csv \
  --tick_interval 1D \
  --start_date 2024-01-01
```

**Passo 2: Calcular métricas de isolamento**

Primeiro, identifique quem é a "vítima" na simulação (um nó que foi marcado como victim):

```bash
# Exemplo: nó com ID 42 é a vítima principal
python scripts/ego_isolation_timeseries.py \
  --input data/simulation_edges.csv \
  --format csv \
  --case_id simulation \
  --victim 42 \
  --window 1D \
  --directed \
  --anchor_peak \
  --outdir outputs/isolation
```

**Nota:** Para identificar a vítima, você pode:
1. Abrir `data/nodes.csv` e procurar nós com `kind = "victim"`
2. Ou filtrar `data/events.csv` e ver quais `target` aparecem com `etype = "accuse"`

---

### Caso 3: CSV Genérico de Arestas

Se você já tem um CSV com colunas customizadas:

```bash
python scripts/ego_isolation_timeseries.py \
  --input data/custom/edges.csv \
  --format csv \
  --case_id custom_case \
  --victim node_123 \
  --srccol origin_user \
  --dstcol destination_user \
  --timecol event_time \
  --window 6H \
  --directed \
  --outdir outputs/isolation
```

---

## 📊 Saídas

Para cada caso, o script gera:

```
outputs/isolation/{case_id}/
├── metrics_{case_id}.csv              ← Série temporal completa
├── ego_density_{case_id}.png          ← Gráfico de densidade do ego
├── avg_dist_{case_id}.png             ← Gráfico de distância média
└── volume_{case_id}.png               ← Gráfico de volume de arestas
```

### Formato do CSV de saída

| Coluna | Descrição |
|--------|-----------|
| `t` | Timestamp da janela |
| `ego_density` | Densidade do ego-network (0-1) |
| `avg_dist` | Distância média até a vítima |
| `volume` | Número de arestas na janela |
| `t_rel_janelas` | (se `--anchor_peak`) Janelas relativas ao pico |

---

## 🔧 Parâmetros Principais

### Obrigatórios

- `--input`: Arquivo de entrada (CSV ou JSONL)
- `--case_id`: Identificador do caso (ex: monark, simulation, etc.)
- `--victim`: ID do nó da vítima (deve bater exatamente com valores em src/dst)

### Opcionais

- `--window`: Tamanho da janela (default: `1D`)
  - Exemplos: `1H` (1 hora), `6H`, `1D` (1 dia), `1W` (1 semana)
- `--directed`: Usar fórmula dirigida para ego_density (default: False)
- `--anchor_peak`: Adicionar coluna com tempo relativo ao pico de volume
- `--format`: Formato do arquivo (`csv` ou `jsonl`, default: `csv`)
- `--outdir`: Diretório base de saída (default: `out`)

### Customização de Colunas

Se seu arquivo tem nomes de colunas diferentes:

- `--srccol`: Nome da coluna de origem (default: `src`)
- `--dstcol`: Nome da coluna de destino (default: `dst`)
- `--timecol`: Nome da coluna de tempo (default: `timestamp`)

---

## 📈 Interpretação das Métricas

### Ego Density (Densidade do Ego-Network)

**O que é:** Mede quão conectados estão os vizinhos da vítima entre si.

- **Valor alto (próximo de 1):** Vizinhos da vítima estão altamente conectados → "câmara de eco", cluster coeso
- **Valor baixo (próximo de 0):** Vizinhos da vítima NÃO estão conectados → vítima é "ponte" entre grupos

**Interpretação no contexto de cancelamento:**
- 🔻 **Queda da ego_density** pode indicar fragmentação do cluster da vítima
- 🔺 **Aumento** pode indicar formação de "facção defensora" coesa

### Average Distance to Victim

**O que é:** Distância média (em número de saltos) de todos os nós até a vítima.

- **Valor baixo:** Vítima é central, fácil de alcançar
- **Valor alto:** Vítima está isolada, periférica

**Interpretação no contexto de cancelamento:**
- 🔺 **Aumento da distância** indica **isolamento crescente** da vítima
- 🔻 **Queda** indica **centralização** (mais atenção, menções)

**Nota:** Usamos grafo **não-dirigido** para esta métrica (mais robusto contra desconexões).

---

## 🧪 Exemplo Completo: Caso Monark

### 1. Preparar dados do Twitter

Supondo que você já tem um JSONL processado com arestas:

```bash
# Dados já no formato correto
ls data/twitter/monark_edges.jsonl
```

### 2. Executar análise de isolamento

```bash
python scripts/ego_isolation_timeseries.py \
  --input data/twitter/monark_edges.jsonl \
  --format jsonl \
  --case_id monark \
  --victim @monark \
  --window 1D \
  --directed \
  --anchor_peak \
  --outdir outputs/isolation
```

### 3. Visualizar resultados

```bash
# Abrir pasta com gráficos
explorer outputs\isolation\monark

# Ou no Linux/Mac
open outputs/isolation/monark
```

### 4. Análise dos gráficos

- **`ego_density_monark.png`**: Ver se densidade cai ao longo do tempo (fragmentação)
- **`avg_dist_monark.png`**: Ver se distância aumenta (isolamento)
- **`volume_monark.png`**: Ver o pico de atividade

### 5. Análise quantitativa

```python
import pandas as pd
import matplotlib.pyplot as plt

# Carregar métricas
df = pd.read_csv("outputs/isolation/monark/metrics_monark.csv")

# Ver correlação entre volume e isolamento
print(df[['volume', 'ego_density', 'avg_dist']].corr())

# Plotar densidade vs distância
plt.scatter(df['ego_density'], df['avg_dist'])
plt.xlabel('Ego Density')
plt.ylabel('Avg Distance')
plt.title('Densidade vs Isolamento - Monark')
plt.show()
```

---

## 🔍 Troubleshooting

### Erro: "Vítima não encontrada em nenhuma janela"

**Causa:** O ID da vítima não bate com nenhum valor em `src` ou `dst`.

**Soluções:**
1. Verifique se o ID está correto (case-sensitive!)
2. No Twitter, handles podem ou não ter `@` - tente ambos
3. Use o aviso do script que mostra exemplos de nós encontrados
4. Inspecione manualmente o arquivo:
   ```bash
   # Ver primeiros 10 nós
   cut -d',' -f1,2 data/edges.csv | head -20
   ```

### Erro: "Colunas faltando no arquivo"

**Causa:** Nome das colunas não bate com os padrões.

**Solução:** Use `--srccol`, `--dstcol`, `--timecol` para especificar nomes corretos:

```bash
python scripts/ego_isolation_timeseries.py \
  --input data/custom.csv \
  --srccol author \
  --dstcol mentioned_user \
  --timecol created_at \
  ...
```

### Muitos pontos NaN nos gráficos

**Causa:** Vítima não aparece em muitas janelas (evento raro).

**Soluções:**
1. Use janelas maiores (ex: `--window 1W` em vez de `1H`)
2. Filtre eventos antes para incluir apenas menções à vítima
3. Isso é esperado se a vítima é periférica

---

## 💡 Dicas de Uso

### 1. Escolher Tamanho de Janela

- **Dados horários (Twitter):** Use `1H` ou `6H`
- **Dados diários:** Use `1D`
- **Simulação NetLogo (442 ticks):** Use `1D` ou `10D` dependendo do que cada tick representa

### 2. Dirigido vs Não-Dirigido

- Use `--directed` se a **direção importa** (ex: menções, retweets)
- Omita se relações são simétricas (ex: co-ocorrência)

### 3. Ancoragem no Pico

- Use `--anchor_peak` para alinhar múltiplos casos no tempo relativo
- Útil para comparar "antes vs depois do pico"

### 4. Múltiplos Casos

Execute para todos os casos e compare:

```bash
for case in monark karol wagner bueno; do
  python scripts/ego_isolation_timeseries.py \
    --input data/twitter/${case}_edges.jsonl \
    --format jsonl \
    --case_id $case \
    --victim @$case \
    --window 1D \
    --directed \
    --anchor_peak \
    --outdir outputs/isolation
done
```

Depois, compare os CSVs lado-a-lado.

---

## 📚 Referências

- **Ego-network density:** Marsden, P. V. (1990). Network data and measurement.
- **Isolation metrics:** Borgatti, S. P. (2006). Identifying sets of key players in a social network.
- **Temporal networks:** Holme, P., & Saramäki, J. (2012). Temporal networks.

---

**Última atualização:** Outubro 2025  
**Manutenção:** Ver `scripts/ego_isolation_timeseries.py`







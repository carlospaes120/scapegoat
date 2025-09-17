## Pipeline NetLogo → Gephi (scapegoat roles)

Este projeto cria um pipeline para transformar `events.csv` (exportado de uma simulação NetLogo) em artefatos prontos para o Gephi, incluindo rótulos dinâmicos de papéis (roles) inferidos na janela de pico.

### Instalação

```bash
python -m venv .venv
. .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Uso

```bash
python build_graph.py \
  --in events.csv \
  --outdir build \
  --window 100 \
  --leaders 3 \
  --eps 0.2 \
  --coattention-dt 0
```

- **--in**: caminho para `events.csv` (obrigatório)
- **--outdir**: diretório de saída (default: `build`)
- **--window**: tamanho da janela (ticks) para detectar a janela de pico
- **--leaders**: K do top-K por `out_strength` na janela de pico
- **--eps**: peso para tentativas fracassadas no `viz_weight`
- **--coattention-dt**: se > 0, exporta `edges_coattention.csv` (rede não-direcionada entre co-acusadores)

### Artefatos gerados (em `build/`)

- `nodes.csv`: `id, role, betweenness, in_strength, out_strength, peak_window_start, peak_window_end`
- `edges.csv`: `source, target, weight, attempts, successes, viz_weight`
- `graph.gexf`: grafo dirigido com atributos acima
- (opcional) `edges_coattention.csv`

### Heurística de papéis (na janela de pico)

- A janela de pico é a com maior número de eventos; empate: maior soma de `amount`.
- **vítima (scapegoat)**: maior `net_in = in_strength − out_strength`, muitos fails como fonte; empate final por menor grau na janela.
- **líder**: top-K por `out_strength` na janela; empate: betweenness/PageRank na rede agregada.
- **acusador_falho**: nós (≠ líder, ≠ vítima) com `success=0` como fonte > 0.
- **vítima_falhada (substituta)**: alvos diretos do scapegoat na janela e/ou nós com `in_strength` alto (percentil 75), excluindo scapegoat e líderes.
- **neutro**: todos os demais.

### Import no Gephi

1. File → Open `build/graph.gexf`.
2. Appearance → Partition: colorir por `role`.
3. Appearance → Ranking: tamanho por `in_strength` ou `out_strength`.
4. Layout → ForceAtlas2: habilitar LinLog Mode, Prevent Overlap. Edge Weight Influence ~ 1.0.
5. Para mais densidade visual, use `viz_weight` como Weight no import.

### Resumo impresso

O script imprime: janela de pico, id da vítima (scapegoat), lista de líderes, contagem por role e nº de nós/arestas agregados.

### Formato esperado de events.csv

Colunas obrigatórias: `tick, source, target, success`. Coluna `amount` é opcional; se ausente, assume 1.0.

### Patch de logging no NetLogo

```netlogo
extensions [ csv ]

to setup
  clear-all
  file-close-all
  file-delete "events.csv"
  file-open "events.csv"
  file-print csv:to-row ["tick" "source" "target" "success" "amount"]
  file-close
end

to log-accusation [src tgt success? amount]
  file-open "events.csv"
  file-print csv:to-row (list ticks [who] of src [who] of tgt (ifelse-value success? [1] [0]) amount)
  file-close
end

to attempt-transfer [tgt]
  let amount 1
  let success? (random-float 1 < prob-transfer)
  ; ... atualiza estados/cores/tensão ...
  log-accusation self tgt success? amount
end
```

### Desenvolvimento

- Código principal em `build_graph.py` com pandas/networkx.
- Teste rápido em `tests/test_smoke.py` gera dados sintéticos e verifica artefatos.

### Requisitos

- Python 3.9+
- `pandas`, `numpy`, `networkx`

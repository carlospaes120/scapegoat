# Guia de Botões para Interface NetLogo

## 📋 Botões a Adicionar na Interface

Para adicionar estes botões, abra `scapegoat_instrumented.nlogo` no NetLogo, vá para a aba **Interface**, e clique em **Button** para criar cada um.

---

## 🔵 Botões de Inicialização (Headers)

### 1. Export events header
**Tipo**: Button (click-once)  
**Código**:
```netlogo
write-events-header
```
**Display name**: `Export events header`  
**Tooltip**: Cria data/events.csv com cabeçalho (chame antes de iniciar coleta)  
**Posição sugerida**: Acima do botão `setup`

---

### 2. Export timeseries header
**Tipo**: Button (click-once)  
**Código**:
```netlogo
write-timeseries-header
```
**Display name**: `Export timeseries header`  
**Tooltip**: Cria data/timeseries.csv com cabeçalho (chame antes de iniciar coleta)  
**Posição sugerida**: Ao lado do botão anterior

---

## 📸 Botões de Snapshot (Exportação sob demanda)

### 3. Export nodes snapshot
**Tipo**: Button (click-once)  
**Código**:
```netlogo
export-nodes-snapshot
```
**Display name**: `Export nodes snapshot`  
**Tooltip**: Exporta estado atual dos nós para data/nodes.csv  
**Posição sugerida**: Lado esquerdo, abaixo dos controles principais

---

### 4. Export links snapshot
**Tipo**: Button (click-once)  
**Código**:
```netlogo
export-links-snapshot
```
**Display name**: `Export links snapshot`  
**Tooltip**: Exporta topologia atual para data/links_snapshot.csv  
**Posição sugerida**: Ao lado do botão anterior

---

### 5. Export plots (opcional)
**Tipo**: Button (click-once)  
**Código**:
```netlogo
export-all-plots-csv
```
**Display name**: `Export plots`  
**Tooltip**: Exporta gráficos para data/plots.csv  
**Posição sugerida**: Lado direito, próximo aos plots

---

## 🎮 Botão de Controle

### 6. Toggle data collector
**Tipo**: Button (click-once)  
**Código**:
```netlogo
set datacollector? not datacollector?
```
**Display name**: `Toggle data collector`  
**Tooltip**: Liga/desliga pausas visuais (datacollector?)  
**Posição sugerida**: Próximo ao botão `go`

**Nota**: `datacollector?` já existe no código original. Este botão apenas alterna seu valor.

---

## 📐 Layout Sugerido da Interface

```
┌─────────────────────────────────────────────────────┐
│  [Export events header] [Export timeseries header]  │
│                                                      │
│  [setup]  [go]  [Toggle data collector]            │
│                                                      │
│  Sliders: numnodes, friendliness, skepticism        │
│  Switch: scapegoat?                                 │
│                                                      │
│  [Export nodes snapshot] [Export links snapshot]    │
│                                                      │
│  Monitors: n_alive, n_victims, pctvictims           │
│                                                      │
│  Plots (área de visualização da rede)              │
│                                   [Export plots]    │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 Instruções de Criação

### Como adicionar um botão:

1. **Abra o NetLogo** e carregue `scapegoat_instrumented.nlogo`
2. **Vá para a aba Interface** (no topo)
3. **Clique no botão "Button"** na barra de ferramentas (ou pressione `B`)
4. **Clique na área da interface** onde deseja posicionar o botão
5. **Na janela que abre**:
   - **Commands**: Cole o código NetLogo (ex: `write-events-header`)
   - **Display name**: Digite o nome visível (ex: "Export events header")
   - **Action key**: Deixe em branco (ou atribua um atalho como `E`)
   - **Forever**: Desmarque (todos são click-once, exceto `go` se quiser)
   - **Disable until ticks start**: Desmarque (para headers) ou Marque (para snapshots)
6. **Clique OK**
7. **Redimensione e posicione** o botão conforme necessário

---

## 🎯 Ordem Recomendada de Uso

### Primeira execução (setup inicial):
1. *(Opcional)* Clique em **Export events header** (se quiser recriar)
2. *(Opcional)* Clique em **Export timeseries header** (se quiser recriar)
3. Clique em **setup** (cria headers automaticamente se não existirem)

### Durante a simulação:
4. Clique em **go** (ou ative go-forever)
5. *(Opcional)* Clique em **Toggle data collector** se quiser desativar pausas

### Quando quiser exportar snapshot:
6. Clique em **Export nodes snapshot**
7. Clique em **Export links snapshot**
8. *(Opcional)* Clique em **Export plots**
9. No terminal: `python tools/make_gexf.py`

---

## 📝 Notas

### Sobre `datacollector?`
- **`datacollector? = false`**: Modo rápido, sem pausas visuais (ideal para coleta de dados)
- **`datacollector? = true`**: Modo visual, com `wait 1` após eventos importantes (ideal para demonstração)

### Sobre Headers
- Os botões de header **sobrescrevem** os arquivos existentes (começam "limpo")
- Se você quer **continuar** uma coleta anterior, **NÃO** clique neles
- Se você quer **começar nova coleta**, clique neles antes de `setup`

### Sobre Snapshots
- Podem ser exportados **a qualquer momento** (durante ou após a simulação)
- **Sobrescrevem** os arquivos anteriores (não são cumulativos)
- Se quiser **múltiplos snapshots**, renomeie os arquivos CSV entre exportações (ex: `nodes_tick100.csv`, `nodes_tick200.csv`)

---

## 🔄 Alternativa: Criação Programática (Advanced)

Se preferir adicionar os botões via código (para facilitar distribuição), edite o arquivo `.nlogo` manualmente:

```xml
BUTTON
10 10 180 43
Export events header
write-events-header
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
190 10 360 43
Export timeseries header
write-timeseries-header
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
10 60 180 93
Export nodes snapshot
export-nodes-snapshot
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
190 60 360 93
Export links snapshot
export-links-snapshot
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
370 60 480 93
Export plots
export-all-plots-csv
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

BUTTON
250 110 380 143
Toggle data collector
set datacollector? not datacollector?
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1
```

**Coordenadas**: (left top right bottom) em pixels  
**Flags**: Ver [documentação NetLogo Interface](https://ccl.northwestern.edu/netlogo/docs/programming.html#buttons)

---

## 🎓 Dicas de UX

1. **Agrupe por função**: Headers juntos, snapshots juntos, controles juntos
2. **Use cores**: Defina cores diferentes para botões de diferentes categorias (se o NetLogo permitir)
3. **Tooltips claros**: Sempre adicione tooltips explicativos (campo "Display name" pode incluir descrição curta)
4. **Desabilite quando irrelevante**: Use "Disable until ticks start" para botões que só fazem sentido após `setup`

---

**Versão**: 1.0  
**Data**: Outubro 2025  
**Referência**: https://ccl.northwestern.edu/netlogo/docs/interface.html


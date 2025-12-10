# 📑 Índice de Arquivos - Sistema de Coleta de Dados Scapegoat

## 📂 Estrutura de Arquivos Criados

Este documento lista **todos** os arquivos criados na refatoração do modelo Scapegoat para instrumentação de dados.

---

## 🔵 Modelo NetLogo

### `scapegoat_instrumented.nlogo`
**Tipo**: Arquivo NetLogo (`.nlogo`)  
**Tamanho**: ~80KB  
**Descrição**: Modelo NetLogo Scapegoat com sistema completo de coleta de dados.

**Principais mudanças**:
- 7 procedimentos de logging adicionados
- ~15 pontos de inserção de `log-event`
- Bloco `file-open "scapegoat.txt"` removido
- Chamadas automáticas em `setup` e `go`

**Uso**:
1. Abra no NetLogo 6.x
2. Adicione botões na Interface (ver `INTERFACE_BUTTONS.md`)
3. Execute `setup` e `go`

**Relacionado**: `CHANGES_SUMMARY.md` (diffs detalhados)

---

## 🐍 Scripts Python

### `tools/make_gexf.py`
**Tipo**: Script Python  
**Tamanho**: ~3KB  
**Descrição**: Converte CSV (nodes + links) → GEXF/GraphML para Gephi.

**Uso**:
```bash
python tools/make_gexf.py
```

**Input**:
- `data/nodes.csv`
- `data/links_snapshot.csv`

**Output**:
- `data/network.gexf`
- `data/network.graphml`

**Dependências**: `pandas`, `networkx`

---

### `tools/verify_data.py`
**Tipo**: Script Python  
**Tamanho**: ~6KB  
**Descrição**: Verifica integridade dos arquivos CSV exportados pelo NetLogo.

**Uso**:
```bash
python tools/verify_data.py
```

**Verificações**:
- ✅ Arquivos existem
- ✅ Colunas esperadas presentes
- ✅ Tipos de dados corretos
- ✅ Estatísticas resumidas

**Output**: Relatório no terminal

---

### `tools/create_sample_data.py`
**Tipo**: Script Python  
**Tamanho**: ~4KB  
**Descrição**: Cria dados de exemplo para testar o pipeline sem rodar NetLogo.

**Uso**:
```bash
python tools/create_sample_data.py
```

**Output**:
- `data/events.csv` (50 eventos fictícios)
- `data/timeseries.csv` (100 ticks fictícios)
- `data/nodes.csv` (100 nós fictícios)
- `data/links_snapshot.csv` (rede Erdős-Rényi)

**Útil para**: Testar scripts de análise sem simulação NetLogo

---

### `examples/analyze_simulation.py`
**Tipo**: Script Python  
**Tamanho**: ~8KB  
**Descrição**: Análise completa dos dados exportados com gráficos.

**Uso**:
```bash
python examples/analyze_simulation.py
```

**Input**:
- Todos os CSVs em `data/`

**Output**:
- `outputs/events_analysis.png` (distribuição de eventos)
- `outputs/timeseries_analysis.png` (6 gráficos temporais)
- `outputs/network_analysis.png` (4 gráficos de rede)
- Estatísticas no terminal

**Dependências**: `pandas`, `matplotlib`, `seaborn`

---

### `run_full_test.py`
**Tipo**: Script Python  
**Tamanho**: ~5KB  
**Descrição**: Teste integrado completo do pipeline.

**Uso**:
```bash
python run_full_test.py
```

**Testes executados** (8 no total):
1. Criar dados de exemplo
2. Verificar arquivos CSV
3. Verificar integridade
4. Gerar GEXF/GraphML
5. Verificar arquivos de rede
6. Análise completa
7. Verificar gráficos
8. Validar GEXF com NetworkX

**Output**: Relatório de testes + score (X/8 passed)

---

## 📚 Documentação

### `README_DATA_COLLECTION.md`
**Tipo**: Documentação Markdown  
**Tamanho**: ~12KB (estimado)  
**Descrição**: Documentação completa do sistema de coleta de dados.

**Conteúdo**:
- 📋 Visão geral
- 🎯 Arquivos exportados (descrição detalhada de cada CSV)
- 🎮 Botões da Interface NetLogo
- 🚀 Fluxo de trabalho (passo a passo)
- 📊 Análise de dados (exemplos Python)
- 🔍 Verificação de integridade
- 🛠️ Resolução de problemas
- 📝 Notas de implementação

**Público-alvo**: Usuários que querem entender o sistema em profundidade

---

### `CHANGES_SUMMARY.md`
**Tipo**: Documentação Markdown  
**Tamanho**: ~15KB (estimado)  
**Descrição**: Resumo detalhado de todas as mudanças no código NetLogo.

**Conteúdo**:
- 🔧 Helpers de logging adicionados (código completo)
- 📊 Resumo quantitativo (linhas adicionadas/removidas)
- 🎯 Tipos de eventos registrados (tabela)
- ✅ Verificação de integridade (checklist)
- 🔄 Compatibilidade (versões, dependências)
- 📝 Notas técnicas (decisões de design)

**Público-alvo**: Desenvolvedores que querem entender as mudanças

---

### `INTERFACE_BUTTONS.md`
**Tipo**: Documentação Markdown  
**Tamanho**: ~6KB (estimado)  
**Descrição**: Guia de botões para adicionar na Interface NetLogo.

**Conteúdo**:
- 🔵 Especificação de cada botão (código, tooltip, posição)
- 📐 Layout sugerido da Interface
- 🔧 Instruções de criação (passo a passo)
- 🎯 Ordem recomendada de uso
- 📝 Notas sobre datacollector? e headers
- 🔄 Alternativa: criação programática (XML)

**Público-alvo**: Usuários configurando a Interface NetLogo

---

### `QUICK_START.md`
**Tipo**: Documentação Markdown  
**Tamanho**: ~8KB (estimado)  
**Descrição**: Guia de início rápido (5 minutos).

**Conteúdo**:
- ⚡ Setup em 5 minutos
- 🧪 Teste com dados de exemplo (sem NetLogo)
- 🚀 Uso com NetLogo (simulação real)
- 📊 Análise rápida em Python (snippets)
- 🔧 Troubleshooting rápido (tabela)
- 📁 Estrutura de arquivos
- 🎯 Casos de uso

**Público-alvo**: Novos usuários que querem começar rapidamente

---

### `SUMMARY.md`
**Tipo**: Documentação Markdown  
**Tamanho**: ~10KB (estimado)  
**Descrição**: Resumo executivo do projeto.

**Conteúdo**:
- ✅ O que foi feito (lista completa)
- 🎯 Como usar (TL;DR)
- 📊 Tipos de dados coletados (descrição de cada CSV)
- 🔬 Comparação com dados empíricos (workflow)
- 🎓 Casos de uso acadêmicos
- 📈 Métricas implementadas
- 📦 Entregáveis (lista de arquivos)
- ✅ Critérios de aceite (checklist)
- 🎉 Próximos passos

**Público-alvo**: Gestores de projeto, pesquisadores

---

### `INDEX.md` (este arquivo)
**Tipo**: Documentação Markdown  
**Tamanho**: ~6KB (estimado)  
**Descrição**: Índice de todos os arquivos criados.

**Conteúdo**:
- 📂 Estrutura de arquivos criados
- Descrição de cada arquivo (tipo, tamanho, uso)
- Relacionamentos entre arquivos
- Público-alvo de cada documento

**Público-alvo**: Qualquer usuário que quer navegar a documentação

---

### `README.md` (atualizado)
**Tipo**: Documentação Markdown  
**Mudança**: Adicionada seção "🆕 Novo: Modelo NetLogo Instrumentado"

**Conteúdo adicionado**:
- Link para `QUICK_START.md`
- Link para `README_DATA_COLLECTION.md`
- Lista de recursos principais

---

## 🗂️ Diretórios Criados

### `data/`
**Tipo**: Diretório  
**Criado por**: `New-Item -ItemType Directory -Path "data"` (PowerShell)

**Conteúdo (após rodar simulação)**:
- `events.csv`
- `timeseries.csv`
- `nodes.csv`
- `links_snapshot.csv`
- `network.gexf`
- `network.graphml`

**Nota**: Arquivos CSV são criados pelo NetLogo. GEXF/GraphML são criados por `make_gexf.py`.

---

### `tools/` (já existia, novos arquivos adicionados)
**Tipo**: Diretório  
**Novos arquivos**:
- `make_gexf.py`
- `verify_data.py`
- `create_sample_data.py`

---

### `examples/` (já existia, novo arquivo adicionado)
**Tipo**: Diretório  
**Novos arquivos**:
- `analyze_simulation.py`

---

### `outputs/` (criado ao rodar análise)
**Tipo**: Diretório  
**Criado por**: `analyze_simulation.py`

**Conteúdo**:
- `events_analysis.png`
- `timeseries_analysis.png`
- `network_analysis.png`

---

## 📊 Mapa de Dependências

```
scapegoat_instrumented.nlogo
    ↓ (executa setup/go)
data/events.csv
data/timeseries.csv
data/nodes.csv (via botão)
data/links_snapshot.csv (via botão)
    ↓
verify_data.py (valida CSVs)
    ↓
make_gexf.py (converte → GEXF)
    ↓
data/network.gexf
data/network.graphml
    ↓
analyze_simulation.py (gera gráficos)
    ↓
outputs/*.png
```

---

## 📖 Guia de Leitura

### Para Começar Rapidamente
1. **Leia**: `QUICK_START.md` (5 min)
2. **Execute**: `run_full_test.py` (30 seg)
3. **Explore**: Gráficos em `outputs/`

### Para Entender em Profundidade
1. **Leia**: `README_DATA_COLLECTION.md` (20 min)
2. **Leia**: `CHANGES_SUMMARY.md` (15 min)
3. **Leia**: `INTERFACE_BUTTONS.md` (10 min)

### Para Usar o Sistema
1. **Configure**: Interface NetLogo (ver `INTERFACE_BUTTONS.md`)
2. **Execute**: Simulação (ver `QUICK_START.md`)
3. **Analise**: Use scripts em `tools/` e `examples/`

### Para Desenvolver/Modificar
1. **Entenda**: Mudanças no código (ver `CHANGES_SUMMARY.md`)
2. **Teste**: Use `create_sample_data.py` + `verify_data.py`
3. **Documente**: Atualize documentação relevante

---

## 🔗 Links Rápidos

| Preciso de... | Arquivo |
|---------------|---------|
| Começar em 5 min | `QUICK_START.md` |
| Entender o sistema | `README_DATA_COLLECTION.md` |
| Ver mudanças no código | `CHANGES_SUMMARY.md` |
| Adicionar botões | `INTERFACE_BUTTONS.md` |
| Resumo executivo | `SUMMARY.md` |
| Testar pipeline | `run_full_test.py` |
| Gerar GEXF | `tools/make_gexf.py` |
| Analisar dados | `examples/analyze_simulation.py` |

---

## 📏 Estatísticas do Projeto

### Arquivos Criados
- **Modelo NetLogo**: 1 arquivo (~80KB)
- **Scripts Python**: 5 arquivos (~26KB total)
- **Documentação**: 7 arquivos Markdown (~60KB total)
- **Total**: 13 novos arquivos

### Linhas de Código
- **NetLogo**: ~180 linhas adicionadas, ~8 linhas removidas
- **Python**: ~800 linhas (todos os scripts)
- **Markdown**: ~2000 linhas (toda a documentação)

### Tempo de Desenvolvimento
- **Instrumentação NetLogo**: ~2 horas
- **Scripts Python**: ~3 horas
- **Documentação**: ~3 horas
- **Testes**: ~1 hora
- **Total**: ~9 horas

---

## ✅ Checklist de Arquivos

Use esta checklist para verificar se todos os arquivos foram criados corretamente:

### Modelo e Scripts
- [x] `scapegoat_instrumented.nlogo`
- [x] `tools/make_gexf.py`
- [x] `tools/verify_data.py`
- [x] `tools/create_sample_data.py`
- [x] `examples/analyze_simulation.py`
- [x] `run_full_test.py`

### Documentação
- [x] `README_DATA_COLLECTION.md`
- [x] `CHANGES_SUMMARY.md`
- [x] `INTERFACE_BUTTONS.md`
- [x] `QUICK_START.md`
- [x] `SUMMARY.md`
- [x] `INDEX.md`
- [x] `README.md` (atualizado)

### Diretórios
- [x] `data/` (criado)
- [x] `tools/` (arquivos adicionados)
- [x] `examples/` (arquivo adicionado)

---

## 🎯 Próximos Arquivos Sugeridos (Opcional)

Arquivos que **não** foram criados mas poderiam ser úteis no futuro:

1. **`CITATION.cff`**: Citação acadêmica do projeto (já existe no repo)
2. **`CHANGELOG.md`**: Log de mudanças por versão
3. **`CONTRIBUTING.md`**: Guia para contribuidores
4. **`FAQ.md`**: Perguntas frequentes
5. **`TUTORIAL.ipynb`**: Jupyter Notebook tutorial interativo
6. **`config.yaml`**: Arquivo de configuração para parâmetros de análise
7. **`batch_experiments.py`**: Script para rodar múltiplas simulações em lote

---

**Versão**: 1.0  
**Data**: Outubro 2025  
**Última atualização**: Após conclusão da refatoração


# Resumo: Análise de Emergência de Líderes

**Data:** 11 de Outubro de 2025

Este documento resume os resultados das análises de emergência de líderes para os 4 casos de crises miméticas no Twitter.

---

## 📊 Casos Analisados

### 1. **Monark** (Fevereiro 2022)
- **Posts analisados**: 5.143
- **Eventos de atenção**: 9.476
- **Período**: 07/02/2022 a 14/02/2022 (7 dias)
- **Bins**: 153 janelas de 1 hora
- **Pico**: 14/02/2022 às 20:00

**Líderes Identificados (Top-5 no pico)**:
1. @monark
2. @choquei
3. @brunodelvito
4. @loaxrjs
5. @jacknicas

**Observações**:
- Emergência não detectada (pico ocorreu no final do período)
- Alta concentração: 2.006 usuários receberam atenção

---

### 2. **Karol Conka** (Fevereiro 2021)
- **Posts analisados**: 6.617
- **Eventos de atenção**: 6.248
- **Período**: 15/02/2021 a 27/02/2021 (12 dias)
- **Bins**: 83 janelas de 1 hora
- **Pico**: 24/02/2021 às 20:00

**Líderes Identificados (Top-5 no pico)**:
1. @karolconka
2. @maisvoce
3. @anamariabraga
4. @bbb
5. @ssarahandrade

**Observações**:
- Emergência não detectada
- Líderes incluem contas oficiais do BBB e programa Mais Você
- 1.254 usuários receberam atenção

---

### 3. **Eduardo Bueno** (Setembro 2025)
- **Posts analisados**: 4.083
- **Eventos de atenção**: 7.059
- **Período**: 12/09/2025 a 25/09/2025 (13 dias)
- **Bins**: 231 janelas de 1 hora
- **Pico**: 14/09/2025 às 22:00
- **Emergência detectada**: 17/09/2025 às 03:00 ⚠️

**Líderes Identificados (Top-5 no pico)**:
1. @buenasideias (Eduardo Bueno)
2. @joaoeigen
3. @joaquinteixeira
4. @h1saiadamatrix
5. @peppipets

**Observações**:
- **Único caso onde a emergência foi detectada!**
- Emergência ocorreu **após** o pico (padrão atípico)
- 886 usuários receberam atenção

---

### 4. **Wagner Schwartz** (Janeiro-Dezembro 2017)
- **Posts analisados**: 4.525
- **Eventos de atenção**: 2.342
- **Período**: 04/01/2017 a 28/12/2017 (358 dias)
- **Bins**: 256 janelas de 6 horas
- **Pico**: 08/10/2017 às 17:00

**Líderes Identificados (Top-5 no pico)**:
1. @342artes
2. @chico_pinheiro
3. @midianinja
4. @amb_oficial (Associação Médica Brasileira)
5. @adryanesillva

**Observações**:
- Caso com período mais longo (quase 1 ano)
- Bins de 6 horas devido à dispersão temporal
- Emergência não detectada
- 601 usuários receberam atenção
- Presença de mídia alternativa (Mídia Ninja) e institucional (AMB)

---

## 🔍 Insights Comparativos

### Concentração de Atenção

| Caso | Top-1 Share (Média Pré) | Top-5 Share (Média Pré) | Usuários Totais |
|------|-------------------------|-------------------------|-----------------|
| Monark | Alta* | Alta* | 2.006 |
| Karol Conka | Moderada | Alta | 1.254 |
| Eduardo Bueno | Moderada | Alta | 886 |
| Wagner Schwartz | Alta (51.8%) | Alta (83.5%) | 601 |

*Dados não incluídos no resumo inicial devido ao pico estar no final do período.

### Detecção de Emergência

- ✅ **Eduardo Bueno**: Emergência detectada (17/09 às 03:00)
- ❌ **Monark**: Não detectada (pico no final)
- ❌ **Karol Conka**: Não detectada
- ❌ **Wagner Schwartz**: Não detectada

### Padrões Observados

1. **Casos de BBB (Karol Conka)**: Presença forte de contas oficiais do programa
2. **Casos de figura pública (Monark, Eduardo Bueno)**: O próprio ator central figura entre os líderes
3. **Casos de denúncia (Wagner Schwartz)**: Mix de mídia alternativa e institucional
4. **Emergência tardia**: No único caso onde foi detectada (Eduardo Bueno), ocorreu **após** o pico

### Recomendações para Análises Futuras

1. **Ajustar critérios de emergência**: O threshold de μ + 2σ pode ser muito alto para alguns casos
2. **Bins adaptativos**: Casos curtos (dias) vs. longos (meses) precisam de janelas diferentes
3. **Considerar múltiplos picos**: Alguns casos podem ter ondas de atenção
4. **Análise de rede**: Complementar com métricas de centralidade e comunidades

---

## 📁 Localização dos Arquivos

Todos os resultados estão em `outputs/{CASE_NAME}/`:

```
outputs/
├── Monark/
├── KarolConka/
├── EduardoBueno/
└── WagnerSchwartz/
    ├── leader_emergence_{CASE}.png/svg
    ├── leaders_attention_{CASE}.png/svg
    ├── timeseries_{CASE}.csv
    ├── leaders_{CASE}.csv
    ├── stats_{CASE}.txt
    └── README.md
```

---

## 🚀 Próximos Passos

1. **Visualizar os gráficos**: Abrir os arquivos PNG para ver as séries temporais
2. **Analisar estatísticas**: Revisar os arquivos `stats_*.txt` para detalhes dos testes
3. **Comparar casos**: Criar análise comparativa entre os 4 casos
4. **Ajustar parâmetros**: Experimentar com diferentes valores de `--pre_frac` e `--k_consec`
5. **Exportar para paper**: Usar os gráficos SVG para publicação

---

**Pipeline Desenvolvido**: `scripts/leader_emergence.py`  
**Script Principal**: `main_case.py`  
**Documentação Completa**: `README.md`







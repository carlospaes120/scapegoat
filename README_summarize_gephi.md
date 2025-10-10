# summarize_gephi_nodes.py

Script para processar CSV de nós exportado do Gephi e calcular resumos estatísticos por kind.

## Instalação

```bash
pip install -r requirements.txt
```

## Como usar

### 1. Preparação no Gephi

1. Abra o Gephi
2. Importe seus dados (nodes kind CSV primeiro: Nodes table → Append)
3. Calcule métricas de rede (Statistics)
4. Exporte a tabela: Laboratório de dados → Exportar tabela

### 2. Execução do script

```bash
python summarize_gephi_nodes.py --nodes "caminho/para/nodes_exportados_do_gephi.csv"
```

### Exemplo

```bash
python summarize_gephi_nodes.py --nodes "C:/Users/Paes1/Documents/gephi_export_nodes.csv"
```

## Saída

### Arquivos gerados em `./outputs/`:

1. **summary_by_kind.csv** - Tabela completa com todas as métricas empilhadas
2. **summary_by_kind.xlsx** - Arquivo Excel com múltiplas abas:
   - `_ALL` - Tabela principal (todos os dados)
   - Uma aba por métrica (formato largo para fácil análise)

### Estatísticas calculadas por kind e métrica:

- `n` - Contagem de valores
- `mean` - Média
- `std` - Desvio padrão  
- `median` - Mediana
- `p75` - 75º percentil
- `p90` - 90º percentil
- `p95` - 95º percentil
- `min` - Valor mínimo
- `max` - Valor máximo

## Recursos

✅ **Detecção automática de formato** (separador, codificação)  
✅ **Normalização de nomes de colunas** (acentos, espaços → underscore)  
✅ **Mapeamento de nomes do Gephi** (grau, centrality, etc.)  
✅ **Tratamento de vírgulas decimais**  
✅ **Verificação de dependências** (coluna kind ausente)  
✅ **Criação automática de diretórios**  
✅ **Relatório detalhado no console**  

## Solução de problemas

### Erro: "Arquivo não tem coluna 'kind'"
**Solução:** No Gephi, importe primeiro o nodes_kind.csv (Nodes table → Append), depois exporte a tabela.

### Erro: "Nenhuma métrica reconhecida"
**Solução:** No Gephi, calcule estatísticas de rede antes de exportar (Statistics → Run).

### Erro: "Separador não reconhecido"
**Solução:** Script detecta automaticamente separadores `,` ou `;`. Se ainda falhar, abra em Excel/Calc e salve como CSV com vírgulas.

## Dependências

- pandas >= 1.3.0
- numpy >= 1.21.0
- openpyxl >= 3.0.0













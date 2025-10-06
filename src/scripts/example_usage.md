# Exemplo de Uso do Script Refatorado (v4.0)

## Comando Básico (Caso Karol Conká)

```bash
python scripts/find_tweets.py \
  --query "\"Karol Conká\" OR \"Karol Conka\" OR KarolConka OR @karolconka" \
  --since 2021-01-25 --until 2021-03-05 \
  --lang pt \
  --max-scrolls 60 --stale-scrolls 10 --min-new-per-scroll 3 --sleep 1.5
```

## Parâmetros Disponíveis

### Parâmetros Básicos
- `--query`: Query de busca (default: query do Karol Conká)
- `--since`: Data inicial (YYYY-MM-DD)
- `--until`: Data final (YYYY-MM-DD)
- `--lang`: Idioma (default: pt)
- `--cookies`: Caminho para arquivo de cookies

### Parâmetros de Scroll Robusto
- `--max-scrolls`: Número máximo de scrolls por dia (default: 60)
- `--min-new-per-scroll`: Mínimo de tweets novos por scroll (default: 3)
- `--sleep`: Tempo de espera entre scrolls em segundos (default: 1.5)
- `--stale-scrolls`: Número de scrolls sem novos tweets antes de parar (default: 10)

### Parâmetros de Resiliência (NOVOS)
- `--day-retries`: Tentativas de recuperação antes de pular o dia (default: 3)
- `--empty-waits`: Vezes seguidas com 0 novos itens antes de refresh (default: 3)
- `--max-no-growth-scrolls`: Scrolls consecutivos sem novos IDs antes de refresh (default: 10)
- `--max-refresh-cycles`: Máximo de refresh cycles por dia (default: 4)
- `--resume-from-state`: Caminho para arquivo .state para retomar coleta

## Exemplos de Uso

### Teste Rápido (3 dias)
```bash
python scripts/find_tweets.py \
  --since 2021-02-01 --until 2021-02-04 \
  --max-scrolls 30 --stale-scrolls 5
```

### Busca Personalizada
```bash
python scripts/find_tweets.py \
  --query "Bolsonaro OR Lula lang:pt" \
  --since 2022-01-01 --until 2022-01-07 \
  --max-scrolls 100 --sleep 2.0
```

### Com Resiliência Avançada
```bash
python scripts/find_tweets.py \
  --since 2021-02-21 --until 2021-02-28 \
  --lang pt \
  --max-scrolls 80 --stale-scrolls 14 --min-new-per-scroll 2 --sleep 2.0 \
  --day-retries 3 --empty-waits 3 \
  --max-no-growth-scrolls 10 --max-refresh-cycles 4
```

### Retomada de Coleta Interrompida
```bash
python scripts/find_tweets.py \
  --since 2021-01-25 --until 2021-03-05 \
  --resume-from-state data/raw/coleta.state
```

## Melhorias Implementadas

1. **Busca Latest/Live**: URL sempre inclui `&f=live&src=typed_query`
2. **Slicing Diário**: Processa cada dia separadamente
3. **Scroll Robusto**: Parâmetros configuráveis para controle fino
4. **Deduplicação Global**: Remove duplicatas entre dias
5. **Logs Claros**: Relatório final em PT-BR com estatísticas
6. **Compatibilidade**: Mantém formato de saída existente

## Resiliência Implementada (v4.0)

1. **Watchdog por Dia**: Detecção automática de páginas problemáticas
2. **Recuperação Automática**: Reload, reopen, restart browser conforme necessário
3. **Retentativas Inteligentes**: Backoff exponencial entre tentativas
4. **Sinais de Progresso**: Ajuste automático de tolerância
5. **Persistência de Estado**: Retomada de coleta interrompida
6. **Logs Detalhados**: Visibilidade completa do processo de recuperação

## Saídas

- **Arquivo JSON**: `data/raw/karol_conka_{since}_{until}_{timestamp}.json`
- **Logs**: `logs/karol_conka/run_{timestamp}.log`
- **Parâmetros**: `logs/karol_conka/run_params_{timestamp}.json`
- **Estado**: `data/raw/coleta.state` (se usando --resume-from-state)

## Fluxo de Recuperação

1. **Detecção**: Página problemática detectada (erro, CAPTCHA, timeline vazia)
2. **Reload**: Tentativa de recarregar página e aguardar timeline
3. **Reopen**: Se ainda problemática, reabrir URL do dia
4. **Restart**: Se necessário, reiniciar browser (preservando cookies)
5. **Backoff**: Aguardar tempo exponencial entre tentativas
6. **Ajuste**: Aumentar tolerância após 2 dias sem progresso

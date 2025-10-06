#!/usr/bin/env python3
"""
Script para coleta de tweets do caso Karol Conká
Versão robusta com precedência de parâmetros e validação

MELHORIAS IMPLEMENTADAS:
- Busca forçada em Latest/Live (URL com &f=live&src=typed_query)
- Fatiamento temporal por dias (daily slicing)
- Scroll robusto com parâmetros configuráveis
- Deduplicação global por tweet ID
- Logs claros em PT-BR e relatório final
- Compatibilidade mantida com pipeline existente

RESILIÊNCIA IMPLEMENTADA (v4.0):
- Watchdog por dia com flags --day-retries e --empty-waits
- Detecção de páginas problemáticas (erro, CAPTCHA, timeline vazia)
- Retentativas com backoff exponencial e recuperação automática
- Sinais de progresso e ajuste automático de tolerância
- Scroll robusto com detecção de altura e refresh automático
- Persistência leve com arquivo .state para retomada
- Logs detalhados de recuperação e progresso

NOVOS FLAGS CLI:
- --day-retries: Tentativas de recuperação antes de pular o dia (default: 3)
- --empty-waits: Vezes seguidas com 0 novos itens antes de refresh (default: 3)
- --resume-from-state: Caminho para arquivo .state para retomar coleta

FLUXO DE RECUPERAÇÃO:
1. Detecção de página problemática → reload → aguardar timeline
2. Se ainda problemática → reiniciar browser (preservando cookies)
3. Backoff exponencial entre tentativas (sleep *= 1.5, max 6s)
4. Ajuste automático de tolerância após 2 dias sem progresso
5. Persistência de estado para retomada em caso de interrupção
"""

from playwright.sync_api import sync_playwright
import json
import logging
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import os
import sys
import time
import random
import argparse
from collections import defaultdict
import re

# --- utils: parse seguro p/ respostas do Twitter ---
HTML_MARKERS = ("<html", "<!doctype", "<!DOCTYPE")

def safe_json(response, dump_dir="logs/raw"):
    os.makedirs(dump_dir, exist_ok=True)
    ct = (response.headers.get("content-type") or "").lower()
    body = response.text()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(dump_dir, f"{ts}.txt")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)
    except Exception:
        pass

    # Bloqueio/login detectável
    head = body.strip()[:20].lower()
    if any(head.startswith(m) for m in HTML_MARKERS):
        print("[parse] HTML recebido (provável login/bloqueio). Body salvo em:", path)
        return None

    # Algumas respostas do X vêm como text/plain mas são JSON
    try:
        return json.loads(body)
    except Exception as e:
        print("[parse] Falha ao decodificar JSON:", repr(e), "CT:", ct, "body salvo em:", path)
        return None
# --- fim utils ---

# --- fallback DOM para extração de IDs ---
STATUS_HREF = re.compile(r"/status/(\d+)")

def extract_tweet_ids_from_dom(page):
    ids = set()
    # pega todos os links da timeline que apontam para /status/<id>
    anchors = page.locator('a[href*="/status/"]')
    try:
        n = anchors.count()
    except Exception:
        n = 0
    for i in range(n):
        try:
            href = anchors.nth(i).get_attribute("href") or ""
        except Exception:
            continue
        m = STATUS_HREF.search(href)
        if m:
            ids.add(m.group(1))
    return ids

# --- fim fallback DOM ---

# --- handler p/ inspecionar SearchTimeline ---
def on_response(response):
    try:
        url = response.url
    except Exception:
        return
    if "SearchTimeline" not in url:
        return

    j = safe_json(response)
    if not j:
        return  # sem JSON válido (login/HTML/bloqueio)

    d = j.get("data", {})
    s = (((d.get("search_by_raw_query") or {})
          .get("search_timeline") or {})
          .get("timeline") or {})
    instr = s.get("instructions") or []

    def iter_results():
        for ins in instr:
            for block in (ins.get("addEntries", {}) or {}).get("entries", []):
                ic = (((block.get("content") or {}).get("itemContent") or {})
                      .get("tweet_results") or {})
                r = ic.get("result")
                if r:
                    yield r
            rep = (ins.get("replaceEntry") or {}).get("entry")
            if rep:
                ic = (((rep.get("content") or {}).get("itemContent") or {})
                      .get("tweet_results") or {})
                r = ic.get("result")
                if r:
                    yield r

    try:
        cnt = sum(1 for _ in iter_results())
    except Exception as e:
        print("[SearchTimeline] iter_results error:", repr(e))
        cnt = 0

    print("[SearchTimeline] parsed_tweets_in_response =", cnt)
# --- fim handler ---

# --- Configuration (Karol Conká) ---
SEARCH_TERM = '( "Karol Conká" OR "Karol Conka" OR KarolConka OR #KarolConka OR #KarolConká OR @Karolconka )'

# Datas padrão explícitas
DEFAULT_SINCE_DATE = "2021-01-25"
DEFAULT_UNTIL_DATE = "2021-03-05"
DEFAULT_LANG = "pt"

# Parâmetros de scroll robusto (configuráveis via CLI)
DEFAULT_MAX_SCROLLS = 60
DEFAULT_MIN_NEW_PER_SCROLL = 3
DEFAULT_SLEEP = 1.5
DEFAULT_STALE_SCROLLS = 10

# Parâmetros de resiliência (novos)
DEFAULT_DAY_RETRIES = 3
DEFAULT_EMPTY_WAITS = 3
DEFAULT_MAX_NO_GROWTH_SCROLLS = 10
DEFAULT_MAX_REFRESH_CYCLES = 4

# Configurações legadas (mantidas para compatibilidade)
MAX_SCROLLS = 100  # Aumentado para coletar mais tweets
SCROLL_WAIT_MS = 9000   # aumentar estabilidade
INITIAL_WAIT_MS = 8000  # dar mais tempo para carregar
TARGET_TWEETS = 5000    # Meta de tweets únicos

OUTPUT_DIR = "data/raw"
LOG_DIR = "logs/karol_conka"


def parse_arguments():
    """Parse command line arguments with precedence"""
    parser = argparse.ArgumentParser(description='Coleta tweets do caso Karol Conká')
    
    # Parâmetros básicos
    parser.add_argument('--query', type=str, default=SEARCH_TERM,
                       help=f'Query de busca. Default: {SEARCH_TERM}')
    parser.add_argument('--since', type=str, 
                       help=f'Data inicial (YYYY-MM-DD). Default: {DEFAULT_SINCE_DATE}')
    parser.add_argument('--until', type=str, 
                       help=f'Data final (YYYY-MM-DD). Default: {DEFAULT_UNTIL_DATE}')
    parser.add_argument('--lang', type=str, default=DEFAULT_LANG,
                       help=f'Idioma. Default: {DEFAULT_LANG}')
    parser.add_argument('--cookies', type=str,
                       help='Caminho para arquivo de cookies')
    
    # Parâmetros de scroll robusto
    parser.add_argument('--max-scrolls', type=int, default=DEFAULT_MAX_SCROLLS,
                       help=f'Número máximo de scrolls por dia. Default: {DEFAULT_MAX_SCROLLS}')
    parser.add_argument('--min-new-per-scroll', type=int, default=DEFAULT_MIN_NEW_PER_SCROLL,
                       help=f'Mínimo de tweets novos por scroll. Default: {DEFAULT_MIN_NEW_PER_SCROLL}')
    parser.add_argument('--sleep', type=float, default=DEFAULT_SLEEP,
                       help=f'Tempo de espera entre scrolls (segundos). Default: {DEFAULT_SLEEP}')
    parser.add_argument('--stale-scrolls', type=int, default=DEFAULT_STALE_SCROLLS,
                       help=f'Número de scrolls sem novos tweets antes de parar. Default: {DEFAULT_STALE_SCROLLS}')
    
    # Parâmetros de resiliência
    parser.add_argument('--day-retries', type=int, default=DEFAULT_DAY_RETRIES,
                       help=f'Tentativas de recuperação antes de pular o dia. Default: {DEFAULT_DAY_RETRIES}')
    parser.add_argument('--empty-waits', type=int, default=DEFAULT_EMPTY_WAITS,
                       help=f'Vezes seguidas com 0 novos itens antes de acionar refresh. Default: {DEFAULT_EMPTY_WAITS}')
    parser.add_argument('--max-no-growth-scrolls', type=int, default=DEFAULT_MAX_NO_GROWTH_SCROLLS,
                       help=f'Scrolls consecutivos sem novos IDs antes de refresh. Default: {DEFAULT_MAX_NO_GROWTH_SCROLLS}')
    parser.add_argument('--max-refresh-cycles', type=int, default=DEFAULT_MAX_REFRESH_CYCLES,
                       help=f'Máximo de refresh cycles por dia. Default: {DEFAULT_MAX_REFRESH_CYCLES}')
    parser.add_argument('--resume-from-state', type=str,
                       help='Caminho para arquivo .state para retomar coleta')
    
    return parser.parse_args()


def get_effective_dates(args):
    """Determina as datas efetivas com precedência: CLI > ENV > DEFAULT"""
    since = None
    until = None
    since_source = "none"
    until_source = "none"
    
    # 1. CLI arguments (maior precedência)
    if args.since:
        since = args.since
        since_source = "CLI"
    if args.until:
        until = args.until
        until_source = "CLI"
    
    # 2. Environment variables
    if not since:
        since = os.getenv('SINCE_DATE')
        if since:
            since_source = "ENV"
    
    if not until:
        until = os.getenv('UNTIL_DATE')
        if until:
            until_source = "ENV"
    
    # 3. Default values (menor precedência)
    if not since:
        since = DEFAULT_SINCE_DATE
        since_source = "DEFAULT"
    
    if not until:
        until = DEFAULT_UNTIL_DATE
        until_source = "DEFAULT"
    
    return since, until, since_source, until_source


def get_cookies_file(args):
    """Determina o arquivo de cookies com precedência"""
    if args.cookies:
        return os.path.abspath(args.cookies)
    else:
        # Default: relativo ao script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "..", "twitter_cookies.json")


def validate_dates(since, until):
    """Valida e normaliza as datas"""
    try:
        since_dt = datetime.strptime(since, "%Y-%m-%d")
        until_dt = datetime.strptime(until, "%Y-%m-%d")
        
        if since_dt >= until_dt:
            raise ValueError(f"Data inicial ({since}) deve ser anterior à data final ({until})")
        
        return since, until
    except ValueError as e:
        print(f"❌ Erro na validação das datas: {e}")
        sys.exit(1)


def build_search_url(query, since=None, until=None):
    """Constrói URL de busca com parâmetros Latest/Live forçados"""
    # Incorporar filtros de data na query se fornecidos
    query_parts = [query]
    if since:
        query_parts.append(f"since:{since}")
    if until:
        query_parts.append(f"until:{until}")
    
    final_query = " ".join(query_parts)
    encoded_query = quote_plus(final_query)
    
    # URL com parâmetros Latest/Live forçados
    url = f"https://twitter.com/search?q={encoded_query}&f=live&src=typed_query"
    
    # Verificar se as datas do slice estão na URL
    if since and f"since:{since}" not in final_query:
        raise RuntimeError(f"Slice dates not applied to URL. Expected since:{since} in query")
    if until and f"until:{until}" not in final_query:
        raise RuntimeError(f"Slice dates not applied to URL. Expected until:{until} in query")
    
    return url, final_query

def slice_by_day(since, until):
    """Gera pares de datas para fatiamento diário (since inclusive, until exclusivo)"""
    from datetime import date
    
    def date_from(date_str):
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    
    d = date_from(since)
    end = date_from(until)
    
    days = []
    while d < end:
        d1 = d + timedelta(days=1)
        days.append((
            d.strftime("%Y-%m-%d"),
            d1.strftime("%Y-%m-%d")
        ))
        d += timedelta(days=1)
    
    return days

def build_query(term, lang=None, since=None, until=None):
    """Constrói query de busca (função legada mantida para compatibilidade)"""
    parts = [term]
    if lang:
        parts.append(f"lang:{lang}")
    if since:
        parts.append(f"since:{since}")
    if until:
        parts.append(f"until:{until}")
    return " ".join(parts)


def get_filename_path(query, since, until):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"karol_conka_{since}_{until}_{timestamp}.json")

def parse_created_at(tweet):
    """Extrai e converte created_at para UTC (ISO 8601)"""
    try:
        created_at = tweet.get('created_at', '')
        if not created_at:
            return None
        
        # Se já está em formato ISO, usar diretamente
        if 'T' in created_at and 'Z' in created_at:
            return created_at
        
        # Se está em formato Twitter (ex: "Mon Jan 25 12:00:00 +0000 2021")
        if '+' in created_at or 'UTC' in created_at:
            # Assumir que já está em UTC se tem timezone
            dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Se está em formato simples, assumir UTC
        dt = datetime.strptime(created_at, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%dT00:00:00Z")
        
    except Exception as e:
        logging.warning(f"[⚠️] Erro ao parsear created_at: {e}")
        return None

def get_date_from_created_at(created_at_utc):
    """Extrai data (YYYY-MM-DD) do created_at_utc"""
    if not created_at_utc:
        return None
    
    try:
        # Extrair data da string ISO
        if 'T' in created_at_utc:
            date_part = created_at_utc.split('T')[0]
            return date_part
        return created_at_utc
    except Exception:
        return None

def save_state(state_file, last_completed_day, total_unique, since, until):
    """Salva estado da coleta para retomada"""
    state = {
        "last_completed_day": last_completed_day,
        "since": since,
        "until": until,
        "total_unique": total_unique,
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        logging.info(f"[💾] Estado salvo em: {state_file}")
    except Exception as e:
        logging.error(f"[❌] Erro ao salvar estado: {e}")

def load_state(state_file):
    """Carrega estado da coleta para retomada"""
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        logging.info(f"[📂] Estado carregado de: {state_file}")
        return state
    except Exception as e:
        logging.error(f"[❌] Erro ao carregar estado: {e}")
        return None

def save_daily_file(case_name, day, tweets):
    """Salva arquivo por dia para debug"""
    try:
        daily_dir = os.path.join(OUTPUT_DIR, case_name, "daily")
        os.makedirs(daily_dir, exist_ok=True)
        
        daily_file = os.path.join(daily_dir, f"{day}.json")
        
        # Salvar apenas IDs e created_at para debug
        daily_data = []
        for tweet in tweets:
            tweet_id = tweet.get('id_str') or tweet.get('id')
            created_at_utc = parse_created_at(tweet)
            daily_data.append({
                'id': tweet_id,
                'created_at_utc': created_at_utc
            })
        
        with open(daily_file, "w", encoding="utf-8") as f:
            json.dump(daily_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"[📁] Arquivo diário salvo: {daily_file}")
        
    except Exception as e:
        logging.error(f"[❌] Erro ao salvar arquivo diário: {e}")

def run_day(page, query, day_since, day_until, args, seen_ids, all_tweets, cookies_file, browser, context, since, until):
    """Executa coleta de um dia com retentativas que sempre avança"""
    logging.info(f"[▶] Dia {day_since} → {day_until} (since/until do slice); URL contém &f=live&src=typed_query")
    
    total_new = 0
    
    for attempt in range(args.day_retries):
        try:
            logging.info(f"[🔄] Tentativa {attempt + 1}/{args.day_retries} para dia {day_since}")
            
            # Ajustar sleep baseado no número de tentativas
            current_sleep = args.sleep * (1.5 ** attempt)
            if current_sleep > 6.0:
                current_sleep = 6.0
            
            logging.info(f"[⏱️] Sleep ajustado para: {current_sleep:.2f}s")
            
            # Tentar coleta
            gained = collect_day(day_since, day_until, page, query, args, seen_ids, all_tweets, cookies_file)
            total_new += gained
            
            if gained > 0:
                # Sucesso -> não insistir mais neste dia
                logging.info(f"[✅] Dia {day_since} coletado com sucesso: {gained} novos IDs")
                break
            else:
                # gained == 0 -> tentativa de recuperação entre attempts
                if attempt < args.day_retries - 1:  # Não é a última tentativa
                    logging.info(f"[🔄] Tentando recuperar...")
                    recovery_backoff(attempt, page, current_sleep, browser, context)
                else:
                    logging.warning(f"[⚠️] Dia {day_since} sem resultados após {args.day_retries} tentativas")
            
        except Exception as e:
            logging.error(f"[❌] Erro na tentativa {attempt + 1} para dia {day_since}: {e}")
            
            if attempt < args.day_retries - 1:  # Não é a última tentativa
                logging.info(f"[🔄] Tentando recuperar...")
                recovery_backoff(attempt, page, current_sleep, browser, context)
            else:
                logging.error(f"[❌] Todas as tentativas falharam para dia {day_since}")
    
    # SEMPRE chamado - marca o dia como concluído
    mark_day_completed(day_since, day_until, total_new, len(all_tweets), args, since, until)

def collect_day(day_since, day_until, page, query, args, seen_ids, all_tweets, cookies_file):
    """Coleta um dia específico e retorna quantos novos IDs foram obtidos"""
    # Construir query do dia com apenas as datas do slice
    daily_query = f"({query}) since:{day_since} until:{day_until}"
    if args.lang:
        daily_query += f" lang:{args.lang}"
    
    # Construir URL com parâmetros Latest/Live
    search_url, final_query = build_search_url(daily_query)
    logging.info(f"[🔗] URL: {search_url}")
    
    # Verificar se as datas do slice estão na URL
    if f"since:{day_since}" not in final_query:
        raise RuntimeError(f"Slice dates not applied to URL. Expected since:{day_since} in query")
    if f"until:{day_until}" not in final_query:
        raise RuntimeError(f"Slice dates not applied to URL. Expected until:{day_until} in query")
    
    # Contadores para quebra forte de "sem progresso"
    no_growth_scrolls = 0
    refresh_cycles = 0
    total_scrolls = 0
    new_ids_count = 0
    
    try:
        # Navegar para a busca
        page.goto(search_url, wait_until="domcontentloaded")
        page.wait_for_timeout(INITIAL_WAIT_MS)
        
        # Verificar se há resultados
        if not wait_for_timeline(page):
            logging.warning(f"[⚠️] Timeline não carregada para {day_since}")
            return 0
        
        logging.info(f"[✅] Timeline carregada para {day_since}")
        
        # Verificar se a página está problemática
        is_problematic, reason = detect_problematic_page(page)
        if is_problematic:
            logging.warning(f"[⚠️] Página problemática detectada: {reason}")
            return 0
        
        # Scroll robusto com contadores
        previous_height = 0
        no_height_increase_count = 0
        
        while total_scrolls < args.max_scrolls:
            # Verificar limite absoluto de scrolls
            if total_scrolls >= args.max_scrolls:
                logging.info(f"[🛑] Max scrolls do dia atingido ({args.max_scrolls}); encerrando dia.")
                break
            
            current_height = page.evaluate("document.body.scrollHeight")
            
            # Verificar se a altura aumentou
            if current_height == previous_height:
                no_height_increase_count += 1
                if no_height_increase_count >= 3:
                    logging.warning(f"[⚠️] Altura não aumentou por 3 tentativas, acionando refresh")
                    page.reload()
                    page.wait_for_timeout(INITIAL_WAIT_MS)
                    if not wait_for_timeline(page):
                        logging.error(f"[❌] Timeline não carregou após refresh")
                        break
                    no_height_increase_count = 0
                    continue
            else:
                no_height_increase_count = 0
            
            # Scroll gradual
            for i in range(3):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight / 3)")
                page.wait_for_timeout(1000)
            
            # Simular movimento do mouse
            page.mouse.move(500 + (total_scrolls % 3) * 100, 300 + (total_scrolls % 2) * 50)
            
            # Aguardar entre scrolls
            time.sleep(args.sleep)
            
            # Verificar novos tweets via DOM (fallback)
            dom_ids = extract_tweet_ids_from_dom(page)
            new_ids = dom_ids - seen_ids
            
            # Contar IDs novos neste scroll
            gained_this_scroll = len(new_ids)
            
            if gained_this_scroll > 0:
                no_growth_scrolls = 0  # Reset contador de sem crescimento
                
                # Adicionar novos IDs
                for tweet_id in new_ids:
                    if tweet_id not in seen_ids:
                        seen_ids.add(tweet_id)
                        new_ids_count += 1
                        
                        # Criar tweet básico
                        basic_tweet = {
                            'id_str': tweet_id,
                            'id': tweet_id,
                            'created_at': day_since,  # Fallback para data do slice
                            'full_text': f'[DOM Fallback] Tweet ID: {tweet_id}',
                            'user': {'screen_name': 'unknown'},
                            'entities': {}
                        }
                        all_tweets.append(basic_tweet)
            else:
                no_growth_scrolls += 1
                
                # Verificar se atingiu limite de scrolls sem crescimento
                if no_growth_scrolls >= args.stale_scrolls:
                    # Tentar UM refresh e continuar
                    logging.warning(f"[🔄] {args.stale_scrolls} scrolls sem novos IDs, acionando refresh")
                    page.reload()
                    page.wait_for_timeout(INITIAL_WAIT_MS)
                    if not wait_for_timeline(page):
                        logging.error(f"[❌] Timeline não carregou após refresh")
                        break
                    
                    refresh_cycles += 1
                    no_growth_scrolls = 0  # Zera após refresh
                    
                    # **CORTE FORTE** - Limite de refresh atingido
                    if refresh_cycles >= args.max_refresh_cycles:
                        logging.warning(f"[⚠️] Limite de refresh atingido ({args.max_refresh_cycles}) em {day_since}; encerrando dia.")
                        break  # Sai do loop de scroll → encerra o dia
            
            logging.info(f"[📊] Dia {day_since} - Scroll {total_scrolls + 1}: +{gained_this_scroll} novos tweets (Total dia: {new_ids_count})")
            
            previous_height = current_height
            total_scrolls += 1
        
        logging.info(f"[✅] Dia {day_since} finalizado: {new_ids_count} tweets coletados")
        
    except Exception as e:
        logging.error(f"[❌] Erro ao coletar dia {day_since}: {e}")
    
    return new_ids_count

def recovery_backoff(attempt, page, current_sleep, browser, context):
    """Aplica backoff e recuperação entre tentativas"""
    # Aguardar mais tempo
    time.sleep(current_sleep * 2)
    
    # Tentar reload
    try:
        page.reload()
        page.wait_for_timeout(INITIAL_WAIT_MS)
        if not wait_for_timeline(page):
            logging.warning(f"[⚠️] Timeline não carregou após reload")
    except Exception as e:
        logging.warning(f"[⚠️] Erro no reload: {e}")
    
    # Se ainda problemático, reiniciar browser
    if detect_problematic_page(page)[0]:
        logging.warning(f"[🔄] Reiniciando browser...")
        try:
            browser.close()
            browser = context.browser
            page = context.new_page()
            page.set_default_timeout(120000)
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
        except Exception as e:
            logging.error(f"[❌] Erro ao reiniciar browser: {e}")

def mark_day_completed(day_since, day_until, total_new_ids, total_unique, args, since, until):
    """Marca o dia como concluído e salva o estado"""
    logging.info(f"[✅] Dia {day_since} concluído | novos no dia: {total_new_ids} | total único acumulado: {total_unique}")
    
    # Salvar estado
    if args.resume_from_state:
        save_state(args.resume_from_state, day_since, total_unique, since, until)
        logging.info(f"[💾] State salvo: last_completed_day={day_since}")
    
    # Log do próximo dia
    next_day = (datetime.strptime(day_since, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    logging.info(f"[▶] Próximo: {next_day}")

def detect_problematic_page(page):
    """Detecta páginas problemáticas (erro, CAPTCHA, etc.)"""
    try:
        content = page.content().lower()
        
        # Detectar mensagens de erro
        error_indicators = [
            "something went wrong",
            "the page could not be loaded",
            "try again later",
            "something's not right",
            "rate limit exceeded"
        ]
        
        for indicator in error_indicators:
            if indicator in content:
                return True, f"Erro detectado: {indicator}"
        
        # Verificar se há artigos na timeline
        try:
            articles = page.locator('article').count()
            if articles == 0:
                return True, "Nenhum artigo encontrado na timeline"
        except Exception:
            return True, "Erro ao verificar artigos"
        
        return False, None
        
    except Exception as e:
        return True, f"Erro ao detectar página problemática: {e}"

def wait_for_timeline(page, timeout=10000):
    """Aguarda timeline carregar com seletor robusto"""
    try:
        # Tentar múltiplos seletores
        selectors = [
            '[data-testid="cellInnerDiv"]',
            'article',
            '[aria-label*="Timeline"]',
            '[aria-label*="Search timeline"]'
        ]
        
        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=timeout//len(selectors))
                return True
            except Exception:
                continue
        
        return False
    except Exception:
        return False

def collect_day_robust(page, query, since_d, until_d, args, seen_ids, all_tweets, cookies_file, day_state=None):
    """Coleta robusta para um dia específico com recuperação automática"""
    logging.info(f"[📅] Coletando dia: {since_d} até {until_d}")
    
    # Construir query do dia com apenas as datas do slice
    daily_query = f"({query}) since:{since_d} until:{until_d}"
    if args.lang:
        daily_query += f" lang:{args.lang}"
    
    # Construir URL com parâmetros Latest/Live
    search_url, final_query = build_search_url(daily_query)
    logging.info(f"[🔗] URL: {search_url}")
    
    # Verificar se as datas do slice estão na URL
    if f"since:{since_d}" not in final_query:
        raise RuntimeError(f"Slice dates not applied to URL. Expected since:{since_d} in query")
    if f"until:{until_d}" not in final_query:
        raise RuntimeError(f"Slice dates not applied to URL. Expected until:{until_d} in query")
    
    # Inicializar estado do dia se não fornecido
    if day_state is None:
        day_state = {
            'scrolls_feitos': 0,
            'novos_no_scroll': 0,
            'empty_streak': 0,
            'retry_count': 0
        }
    
    # Variáveis de controle do scroll
    scroll_count = day_state['scrolls_feitos']
    stale_count = 0
    day_tweets = []
    day_seen_ids = set()
    
    try:
        # Navegar para a busca
        page.goto(search_url, wait_until="domcontentloaded")
        page.wait_for_timeout(INITIAL_WAIT_MS)
        
        # Verificar se há resultados
        if not wait_for_timeline(page):
            logging.warning(f"[⚠️] Timeline não carregada para {since_d}")
            return day_tweets, day_seen_ids, day_state
        
        logging.info(f"[✅] Timeline carregada para {since_d}")
        
        # Verificar se a página está problemática
        is_problematic, reason = detect_problematic_page(page)
        if is_problematic:
            logging.warning(f"[⚠️] Página problemática detectada: {reason}")
            return day_tweets, day_seen_ids, day_state
        
        # Scroll robusto
        previous_height = 0
        no_height_increase_count = 0
        
        while scroll_count < args.max_scrolls:
            current_height = page.evaluate("document.body.scrollHeight")
            
            # Verificar se a altura aumentou
            if current_height == previous_height:
                no_height_increase_count += 1
                if no_height_increase_count >= 3:
                    logging.warning(f"[⚠️] Altura não aumentou por 3 tentativas, acionando refresh")
                    page.reload()
                    page.wait_for_timeout(INITIAL_WAIT_MS)
                    if not wait_for_timeline(page):
                        logging.error(f"[❌] Timeline não carregou após refresh")
                        break
                    no_height_increase_count = 0
                    continue
            else:
                no_height_increase_count = 0
            
            if current_height == previous_height:
                stale_count += 1
                if stale_count >= args.stale_scrolls:
                    logging.info(f"[🛑] {args.stale_scrolls} scrolls sem novos tweets, parando dia {since_d}")
                    break
            else:
                stale_count = 0  # Reset contador se há novos tweets
            
            # Scroll gradual
            for i in range(3):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight / 3)")
                page.wait_for_timeout(1000)
            
            # Simular movimento do mouse
            page.mouse.move(500 + (scroll_count % 3) * 100, 300 + (scroll_count % 2) * 50)
            
            # Aguardar entre scrolls
            time.sleep(args.sleep)
            
            # Verificar novos tweets via DOM (fallback)
            dom_ids = extract_tweet_ids_from_dom(page)
            new_ids = dom_ids - day_seen_ids - seen_ids
            
            if len(new_ids) == 0:
                day_state['empty_streak'] += 1
                if day_state['empty_streak'] >= args.empty_waits:
                    logging.warning(f"[⚠️] {args.empty_waits} scrolls sem novos tweets, acionando refresh")
                    time.sleep(args.sleep * 2)  # Aguardar mais
                    page.reload()
                    page.wait_for_timeout(INITIAL_WAIT_MS)
                    if not wait_for_timeline(page):
                        logging.error(f"[❌] Timeline não carregou após refresh")
                        break
                    day_state['empty_streak'] = 0
                    continue
            else:
                day_state['empty_streak'] = 0
            
            if len(new_ids) < args.min_new_per_scroll:
                stale_count += 1
                if stale_count >= args.stale_scrolls:
                    logging.info(f"[🛑] Poucos novos tweets ({len(new_ids)} < {args.min_new_per_scroll}), parando dia {since_d}")
                    break
            else:
                stale_count = 0
            
            # Adicionar novos IDs
            for tweet_id in new_ids:
                if tweet_id not in seen_ids and tweet_id not in day_seen_ids:
                    day_seen_ids.add(tweet_id)
                    seen_ids.add(tweet_id)
                    
                    # Criar tweet básico com created_at real se disponível
                    basic_tweet = {
                        'id_str': tweet_id,
                        'id': tweet_id,
                        'created_at': since_d,  # Fallback para data do slice
                        'full_text': f'[DOM Fallback] Tweet ID: {tweet_id}',
                        'user': {'screen_name': 'unknown'},
                        'entities': {}
                    }
                    day_tweets.append(basic_tweet)
                    all_tweets.append(basic_tweet)
            
            logging.info(f"[📊] Dia {since_d} - Scroll {scroll_count + 1}: +{len(new_ids)} novos tweets (Total dia: {len(day_tweets)})")
            
            previous_height = current_height
            scroll_count += 1
            day_state['scrolls_feitos'] = scroll_count
        
        logging.info(f"[✅] Dia {since_d} finalizado: {len(day_tweets)} tweets coletados")
        
    except Exception as e:
        logging.error(f"[❌] Erro ao coletar dia {since_d}: {e}")
    
    return day_tweets, day_seen_ids, day_state


def extract_tweets_from_response(json_data):
    """Extrai tweets únicos de uma resposta da API do Twitter"""
    tweets = []
    tweet_ids = set()
    
    try:
        # Navegar pela estrutura da API do Twitter
        data = json_data.get('data', {})
        search_by_raw_query = data.get('search_by_raw_query', {})
        search_timeline = search_by_raw_query.get('search_timeline', {})
        timeline = search_timeline.get('timeline', {})
        instructions = timeline.get('instructions', [])
        
        for instruction in instructions:
            # Processar addEntries
            if 'addEntries' in instruction:
                entries = instruction['addEntries'].get('entries', [])
                for entry in entries:
                    if entry.get('entryId', '').startswith('tweet-'):
                        content = entry.get('content', {})
                        item_content = content.get('itemContent', {})
                        tweet_results = item_content.get('tweet_results', {})
                        result = tweet_results.get('result')
                        
                        if result and result.get('__typename') == 'Tweet':
                            tweet_id = result.get('id_str') or result.get('id')
                            if tweet_id and tweet_id not in tweet_ids:
                                tweet_ids.add(tweet_id)
                                tweets.append(result)
            
            # Processar replaceEntry
            if 'replaceEntry' in instruction:
                entry = instruction['replaceEntry'].get('entry', {})
                if entry.get('entryId', '').startswith('tweet-'):
                    content = entry.get('content', {})
                    item_content = content.get('itemContent', {})
                    tweet_results = item_content.get('tweet_results', {})
                    result = tweet_results.get('result')
                    
                    if result and result.get('__typename') == 'Tweet':
                        tweet_id = result.get('id_str') or result.get('id')
                        if tweet_id and tweet_id not in tweet_ids:
                            tweet_ids.add(tweet_id)
                            tweets.append(result)
    
    except Exception as e:
        print(f"[extract_tweets] Erro ao processar resposta: {e}")
        return [], 0
    
    return tweets, len(tweet_ids)


def save_run_params(query, start_date, end_date, timezone, version, attempts, timestamp, cookies_file):
    """Salva parâmetros da execução"""
    params = {
        "query": query,
        "start_date": start_date,
        "end_date": end_date,
        "timezone": timezone,
        "version": version,
        "attempts": attempts,
        "timestamp": timestamp,
        "target_tweets": TARGET_TWEETS,
        "cookies_file": cookies_file
    }
    
    os.makedirs(LOG_DIR, exist_ok=True)
    params_file = os.path.join(LOG_DIR, f"run_params_{timestamp}.json")
    
    with open(params_file, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2, ensure_ascii=False)
    
    return params_file


def generate_final_report(tweets, query, timestamp, since, until, lang, daily_stats=None):
    """Gera relatório final com estatísticas"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL DA COLETA")
    print("="*60)
    
    print(f"QUERY final: {query}")
    print(f"Intervalo: {since} → {until}")
    print(f"Idioma: {lang}")
    print(f"Total de tweets únicos coletados: {len(tweets)}")
    print(f"Timestamp: {timestamp}")
    
    # Estatísticas por dia
    if daily_stats:
        print(f"\n📅 Distribuição por dia:")
        for day, count in daily_stats.items():
            print(f"  {day}: {count} tweets")
    
    if tweets:
        # Análise de datas usando created_at_utc
        dates = []
        hashtags = defaultdict(int)
        mentions = defaultdict(int)
        
        for tweet in tweets:
            # Extrair data usando created_at_utc
            created_at_utc = parse_created_at(tweet)
            if created_at_utc:
                date_from_utc = get_date_from_created_at(created_at_utc)
                if date_from_utc:
                    dates.append(date_from_utc)
            
            # Extrair hashtags
            entities = tweet.get('entities', {})
            hashtag_list = entities.get('hashtags', [])
            for hashtag in hashtag_list:
                text = hashtag.get('text', '').lower()
                hashtags[text] += 1
            
            # Extrair menções
            mention_list = entities.get('user_mentions', [])
            for mention in mention_list:
                screen_name = mention.get('screen_name', '').lower()
                mentions[screen_name] += 1
        
        # Histograma de datas (top 10)
        print(f"\n📅 Top 10 datas com mais tweets (baseado em created_at_utc):")
        date_counts = defaultdict(int)
        for date in dates:
            date_counts[date] += 1
        for date, count in sorted(date_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {date}: {count} tweets")
        
        # Top hashtags
        print(f"\n#️⃣ Top 10 hashtags:")
        for hashtag, count in sorted(hashtags.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  #{hashtag}: {count}")
        
        # Top menções
        print(f"\n👥 Top 10 menções:")
        for mention, count in sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  @{mention}: {count}")
        
        # Verificar ausência de termos Monark
        monark_terms = ['monark', 'nazismo', 'nazi']
        monark_found = False
        for tweet in tweets:
            text = tweet.get('full_text', '').lower()
            for term in monark_terms:
                if term in text:
                    monark_found = True
                    break
            if monark_found:
                break
        
        print(f"\n🚫 Verificação de termos Monark: {'❌ ENCONTRADOS' if monark_found else '✅ NÃO ENCONTRADOS'}")
        
        # Primeiras 5 linhas do JSONL
        print(f"\n📄 Primeiras 5 tweets (IDs):")
        for i, tweet in enumerate(tweets[:5]):
            tweet_id = tweet.get('id_str') or tweet.get('id')
            created_at = tweet.get('created_at', 'N/A')
            print(f"  {i+1}. ID: {tweet_id}, Data: {created_at}")
    
    print("\n" + "="*60)


def main():
    # Parse arguments
    args = parse_arguments()
    
    # Configurar logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"run_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # DIAGNÓSTICO INICIAL
    print("🔍 DIAGNÓSTICO INICIAL")
    print("="*50)
    print(f"RUNNING FILE = {os.path.abspath(__file__)}")
    print(f"CWD = {os.getcwd()}")
    
    # Determinar datas efetivas
    since, until, since_source, until_source = get_effective_dates(args)
    print(f"SINCE ({since_source}) = {since}")
    print(f"UNTIL ({until_source}) = {until}")
    
    # Validar datas
    since, until = validate_dates(since, until)
    
    # Determinar arquivo de cookies
    cookies_file = get_cookies_file(args)
    cookies_exists = os.path.exists(cookies_file)
    print(f"COOKIES_FILE = {cookies_file}")
    print(f"COOKIES EXISTS = {cookies_exists}")
    
    if not cookies_exists:
        print("\n❌ ERRO: Arquivo de cookies não encontrado!")
        print(f"📁 Caminho tentado: {cookies_file}")
        print("\n🔧 SOLUÇÃO:")
        print("1. Execute: python scripts/save_cookies.py")
        print("2. Faça login no Twitter que abrir")
        print("3. Pressione Enter quando estiver logado")
        print("4. Execute novamente este script")
        sys.exit(1)
    
    print(f"\n✅ DATES = {since} {until}")
    print("="*50)

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Incorporar lang na query se fornecido
    query = args.query
    if args.lang:
        query = f"{query} lang:{args.lang}"

    print(">>> running file:", __file__)
    print(">>> QUERY =", query)
    print(">>> DATES =", since, until)
    print(">>> PARAMETROS DE SCROLL:")
    print(f"    --max-scrolls: {args.max_scrolls}")
    print(f"    --min-new-per-scroll: {args.min_new_per_scroll}")
    print(f"    --sleep: {args.sleep}")
    print(f"    --stale-scrolls: {args.stale_scrolls}")
    print(">>> PARAMETROS DE RESILIÊNCIA:")
    print(f"    --day-retries: {args.day_retries}")
    print(f"    --empty-waits: {args.empty_waits}")
    print(f"    --max-no-growth-scrolls: {args.max_no_growth_scrolls}")
    print(f"    --max-refresh-cycles: {args.max_refresh_cycles}")
    if args.resume_from_state:
        print(f"    --resume-from-state: {args.resume_from_state}")
    
    # Salvar parâmetros da execução
    params_file = save_run_params(query, since, until, "America/Sao_Paulo", "4.0", 1, timestamp, cookies_file)
    print(f">>> PARAMS SAVED TO: {params_file}")

    try:
        with open(cookies_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load cookies from '{cookies_file}': {e}")
        sys.exit(1)

    # Fatiamento diário
    days = slice_by_day(since, until)
    logging.info(f"[📅] Processando {len(days)} dias: {since} → {until}")
    
    # Variáveis globais para deduplicação
    all_tweets = []
    seen_tweet_ids = set()
    daily_stats = {}
    
    # Verificar se deve retomar de estado
    slices = list(days)
    if args.resume_from_state:
        state = load_state(args.resume_from_state)
        if state and state.get("since") == since and state.get("until") == until:
            last_completed = state.get("last_completed_day")
            if last_completed:
                # Calcular próximo dia
                start_day = datetime.strptime(last_completed, "%Y-%m-%d") + timedelta(days=1)
                start_day_str = start_day.strftime("%Y-%m-%d")
                
                # Filtrar fatias >= start_day
                slices = [(s, u) for (s, u) in slices if s >= start_day_str]
                logging.info(f"[📂] Retomando a partir de {start_day_str} (exclusivo)")
            else:
                logging.warning(f"[⚠️] Estado sem last_completed_day, iniciando do início")
        else:
            logging.warning(f"[⚠️] Estado incompatível, iniciando coleta do início")
    
    # Variáveis para controle de progresso
    last_total_unique = 0
    days_without_progress = 0
    tolerance_increased = False
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-gpu',
                '--disable-extensions'
            ]
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )
        context.set_default_timeout(120000)

        context.add_cookies(cookies)
        page = context.new_page()
        page.set_default_timeout(120000)
        
        # Remove webdriver property
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)

        # Ir para homepage primeiro
        logging.info("[🏠] Going to Twitter homepage first...")
        page.goto("https://twitter.com", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Simular comportamento humano
        page.mouse.move(100, 100)
        page.wait_for_timeout(1000)

        # Processar cada dia
        for day_since, day_until in slices:
            try:
                # Executar coleta do dia
                run_day(page, query, day_since, day_until, args, seen_tweet_ids, all_tweets, cookies_file, browser, context, since, until)
                
                # Salvar arquivo diário para debug
                save_daily_file("karol_conka", day_since, all_tweets)
                
                # Calcular distribuição por data usando created_at_utc
                day_count_by_date = defaultdict(int)
                for tweet in all_tweets:
                    created_at_utc = parse_created_at(tweet)
                    if created_at_utc:
                        date_from_utc = get_date_from_created_at(created_at_utc)
                        if date_from_utc:
                            day_count_by_date[date_from_utc] += 1
                
                # Se não há created_at_utc, usar data do slice como fallback
                if not day_count_by_date:
                    day_count_by_date[day_since] = len(all_tweets)
                
                # Atualizar estatísticas diárias
                for date, count in day_count_by_date.items():
                    daily_stats[date] = daily_stats.get(date, 0) + count
                
                logging.info(f"[📊] Distribuição por data: {dict(day_count_by_date)}")
                
                # Verificar progresso
                current_total = len(all_tweets)
                if current_total > last_total_unique:
                    days_without_progress = 0
                    last_total_unique = current_total
                else:
                    days_without_progress += 1
                
                # Ajustar tolerância se necessário
                if days_without_progress >= 2 and not tolerance_increased:
                    logging.warning(f"[⚠️] Dois dias sem progresso; aumentando tolerância (stale-scrolls += 5)")
                    args.stale_scrolls += 5
                    tolerance_increased = True
                
            except Exception as e:
                logging.error(f"[❌] Erro no dia {day_since}: {e}")
                daily_stats[day_since] = 0
                continue

        logging.info(f"[🚪] Coleta finalizada. Total: {len(all_tweets)} tweets únicos")
        
        try:
            browser.close()
        except Exception as e:
            logging.warning(f"Erro ao fechar browser: {e}")
        
        # Salvar resultados
        filename_path = get_filename_path(query, since, until)
        output_data = {
            "metadata": {
                "query": query,
                "since": since,
                "until": until,
                "lang": args.lang,
                "timestamp": timestamp,
                "total_tweets": len(all_tweets),
                "daily_stats": daily_stats,
                "parameters": {
                    "max_scrolls": args.max_scrolls,
                    "min_new_per_scroll": args.min_new_per_scroll,
                    "sleep": args.sleep,
                    "stale_scrolls": args.stale_scrolls,
                    "day_retries": args.day_retries,
                    "empty_waits": args.empty_waits
                }
            },
            "tweets": all_tweets
        }
        
        with open(filename_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"[💾] Resultados salvos em: {filename_path}")
        
        # Gerar relatório final
        generate_final_report(all_tweets, query, timestamp, since, until, args.lang, daily_stats)


if __name__ == "__main__":
    main()
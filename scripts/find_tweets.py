#!/usr/bin/env python3
"""
Script para coleta de tweets do caso Karol Conká
Versão robusta com precedência de parâmetros e validação
"""

from playwright.sync_api import sync_playwright
import json
import logging
from datetime import datetime
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

MAX_SCROLLS = 100  # Aumentado para coletar mais tweets
SCROLL_WAIT_MS = 9000   # aumentar estabilidade
INITIAL_WAIT_MS = 8000  # dar mais tempo para carregar
TARGET_TWEETS = 5000    # Meta de tweets únicos

OUTPUT_DIR = "data/raw"
LOG_DIR = "logs/karol_conka"


def parse_arguments():
    """Parse command line arguments with precedence"""
    parser = argparse.ArgumentParser(description='Coleta tweets do caso Karol Conká')
    
    parser.add_argument('--since', type=str, 
                       help=f'Data inicial (YYYY-MM-DD). Default: {DEFAULT_SINCE_DATE}')
    parser.add_argument('--until', type=str, 
                       help=f'Data final (YYYY-MM-DD). Default: {DEFAULT_UNTIL_DATE}')
    parser.add_argument('--lang', type=str, default=DEFAULT_LANG,
                       help=f'Idioma. Default: {DEFAULT_LANG}')
    parser.add_argument('--cookies', type=str,
                       help='Caminho para arquivo de cookies')
    
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


def build_query(term, lang=None, since=None, until=None):
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


def generate_final_report(tweets, query, timestamp):
    """Gera relatório final com estatísticas"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO FINAL DA COLETA")
    print("="*60)
    
    print(f"Query: {query}")
    print(f"Total de tweets únicos coletados: {len(tweets)}")
    print(f"Timestamp: {timestamp}")
    
    if tweets:
        # Análise de datas
        dates = []
        hashtags = defaultdict(int)
        mentions = defaultdict(int)
        
        for tweet in tweets:
            # Extrair data
            created_at = tweet.get('created_at', '')
            if created_at:
                dates.append(created_at)
            
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
        
        # Histograma de datas
        print(f"\n📅 Distribuição por data (primeiras 10):")
        date_counts = defaultdict(int)
        for date in dates[:10]:  # Mostrar apenas as primeiras 10
            date_counts[date] += 1
        for date, count in sorted(date_counts.items()):
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

    query = build_query(SEARCH_TERM, lang=args.lang, since=since, until=until)
    search_url = f"https://twitter.com/search?q={quote_plus(query)}&src=typed_query&f=live"

    print(">>> running file:", __file__)
    print(">>> SEARCH_TERM =", SEARCH_TERM)
    print(">>> DATES =", since, until)
    print(">>> TARGET TWEETS =", TARGET_TWEETS)
    print(">>> URL:", search_url)
    
    # Salvar parâmetros da execução
    params_file = save_run_params(query, since, until, "America/Sao_Paulo", "2.0", 1, timestamp, cookies_file)
    print(f">>> PARAMS SAVED TO: {params_file}")

    try:
        with open(cookies_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load cookies from '{cookies_file}': {e}")
        sys.exit(1)

    filename_path = get_filename_path(query, since, until)
    logging.info(f"Output will be saved to: {filename_path}")
    
    # Variáveis para controle de volume e deduplicação
    all_tweets = []
    seen_tweet_ids = set()
    total_tweets_collected = 0
    response_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # Mudado para headless para evitar problemas
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

        def handle_response(response):
            nonlocal total_tweets_collected, response_count
            
            if "SearchTimeline" in response.url:
                logging.info(f"[✅ FOUND] {response.url}")
                response_count += 1
                
                try:
                    json_data = safe_json(response)
                    if not json_data:
                        logging.warning("[!] Resposta inválida (HTML/login detectado)")
                        return False
                    
                    # Extrair tweets únicos desta resposta
                    new_tweets, new_count = extract_tweets_from_response(json_data)
                    
                    # Adicionar apenas tweets únicos
                    unique_new_tweets = []
                    for tweet in new_tweets:
                        tweet_id = tweet.get('id_str') or tweet.get('id')
                        if tweet_id and tweet_id not in seen_tweet_ids:
                            seen_tweet_ids.add(tweet_id)
                            unique_new_tweets.append(tweet)
                            all_tweets.append(tweet)
                    
                    total_tweets_collected = len(all_tweets)
                    
                    metadata = {
                        "query": query,
                        "timestamp": datetime.now().isoformat(),
                        "response_url": response.url,
                        "response_count": response_count,
                        "new_tweets_in_response": len(new_tweets),
                        "unique_new_tweets": len(unique_new_tweets),
                        "total_unique_tweets": total_tweets_collected,
                        "target_tweets": TARGET_TWEETS
                    }

                    output = {
                        "metadata": metadata,
                        "data": json_data
                    }

                    with open(filename_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(output, indent=2, ensure_ascii=False) + ",\n")

                    logging.info(f"[✔] Response {response_count}: {len(unique_new_tweets)} new unique tweets (Total: {total_tweets_collected}/{TARGET_TWEETS})")
                    
                    # Verificar se atingiu a meta
                    if total_tweets_collected >= TARGET_TWEETS:
                        logging.info(f"[🎯] TARGET REACHED! Collected {total_tweets_collected} unique tweets")
                        return True  # Sinal para parar

                except Exception as e:
                    logging.error(f"[!] Failed to parse or save JSON: {e}")

            else:
                logging.debug(f"[...IGNORE] {response.url}")
            
            return False

        page.on("response", handle_response)

        logging.info(f"[🔍] Navigating to: {search_url}")
        
        # Primeiro, vá para a página inicial do Twitter
        logging.info("[🏠] Going to Twitter homepage first...")
        page.goto("https://twitter.com", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        
        # Simular comportamento humano - mover mouse
        page.mouse.move(100, 100)
        page.wait_for_timeout(1000)
        
        # Agora navegar para a busca
        logging.info("[🔍] Now navigating to search...")
        page.goto(search_url, wait_until="domcontentloaded")
        page.wait_for_timeout(INITIAL_WAIT_MS)
        
        # Aguardar um pouco mais para garantir que a página carregou
        page.wait_for_timeout(5000)
        
        # Verifica se estamos logados e se há resultados
        try:
            page.wait_for_selector('[data-testid="cellInnerDiv"]', timeout=10000)
            print("[✅ LOGIN] Timeline carregada com resultados.")
        except Exception as e:
            # Se não achou tweets, tente detectar tela de login
            content = page.content().lower()
            print(f"[DEBUG] Timeout aguardando timeline: {e}")
            print(f"[DEBUG] Conteúdo da página contém 'password': {'password' in content}")
            print(f"[DEBUG] Conteúdo da página contém 'log in': {'log in' in content}")
            print(f"[DEBUG] Conteúdo da página contém 'entrar': {'entrar' in content}")
            
            if "password" in content or "log in" in content or "entrar" in content:
                raise RuntimeError("❌ Não logado no X/Twitter. Execute: python scripts/save_cookies.py")
            else:
                print("[⚠️ WARNING] Nenhum resultado imediato visível; prosseguindo com cautela.")
                # Tentar aguardar mais um pouco
                page.wait_for_timeout(5000)

        logging.info("[🔄] Starting smart scrolling...")

        previous_height = 0
        scroll_count = 0
        target_reached = False

        while scroll_count < MAX_SCROLLS and not target_reached:
            current_height = page.evaluate("document.body.scrollHeight")
            print(f"[SCROLL {scroll_count + 1}] Altura atual: {current_height}, anterior: {previous_height}")
            
            if current_height == previous_height:
                logging.info("No new content loaded, stopping scroll.")
                break

            # Scroll mais humano - scroll gradual
            for i in range(3):
                page.evaluate("window.scrollBy(0, document.body.scrollHeight / 3)")
                page.wait_for_timeout(1000)
            
            # Simular movimento do mouse
            page.mouse.move(500 + (scroll_count % 3) * 100, 300 + (scroll_count % 2) * 50)
            
            logging.info(f"Scrolled {scroll_count + 1}/{MAX_SCROLLS} (Tweets: {total_tweets_collected}/{TARGET_TWEETS})")
            page.wait_for_timeout(SCROLL_WAIT_MS)

            # Fallback DOM: se não capturou tweets pela API, tenta pelo DOM
            if total_tweets_collected == 0:
                dom_ids = extract_tweet_ids_from_dom(page)
                if dom_ids:
                    print(f"[fallback-dom] +{len(dom_ids)} ids pela página")
                    # Adicionar IDs encontrados ao conjunto de IDs únicos
                    for tweet_id in dom_ids:
                        if tweet_id not in seen_tweet_ids:
                            seen_tweet_ids.add(tweet_id)
                            # Criar um objeto tweet básico com o ID
                            basic_tweet = {
                                'id_str': tweet_id,
                                'id': tweet_id,
                                'created_at': datetime.now().isoformat(),
                                'full_text': f'[DOM Fallback] Tweet ID: {tweet_id}',
                                'user': {'screen_name': 'unknown'},
                                'entities': {}
                            }
                            all_tweets.append(basic_tweet)
                            total_tweets_collected = len(all_tweets)
                            print(f"[fallback-dom] Total tweets agora: {total_tweets_collected}")

            # Verificar se atingiu a meta
            if total_tweets_collected >= TARGET_TWEETS:
                target_reached = True
                logging.info(f"[🎯] TARGET REACHED! Stopping scroll at {total_tweets_collected} tweets")

            previous_height = current_height
            scroll_count += 1
            
            # Log adicional a cada 10 scrolls
            if scroll_count % 10 == 0:
                print(f"[PROGRESS] {scroll_count} scrolls completados, {total_tweets_collected} tweets coletados")

        logging.info(f"[🚪] Done. Final count: {total_tweets_collected} unique tweets")
        
        try:
            browser.close()
        except Exception as e:
            logging.warning(f"Erro ao fechar browser: {e}")
        
        # Gerar relatório final
        generate_final_report(all_tweets, query, timestamp)


if __name__ == "__main__":
    main()
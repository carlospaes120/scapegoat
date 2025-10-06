#!/usr/bin/env python3
"""
Script melhorado para coleta de tweets do caso Karol Conká
Usa o mesmo contexto do navegador para evitar problemas de sessão
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

# --- Configuration ---
SEARCH_TERM = '( "Karol Conká" OR "Karol Conka" OR KarolConka OR #KarolConka OR #KarolConká OR @Karolconka )'
DEFAULT_SINCE_DATE = "2021-01-25"
DEFAULT_UNTIL_DATE = "2021-03-05"
DEFAULT_LANG = "pt"

MAX_SCROLLS = 100
SCROLL_WAIT_MS = 9000
INITIAL_WAIT_MS = 8000
TARGET_TWEETS = 5000

OUTPUT_DIR = "data/raw"
LOG_DIR = "logs/karol_conka"

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Coleta tweets do caso Karol Conká')
    
    parser.add_argument('--since', type=str, 
                       help=f'Data inicial (YYYY-MM-DD). Default: {DEFAULT_SINCE_DATE}')
    parser.add_argument('--until', type=str, 
                       help=f'Data final (YYYY-MM-DD). Default: {DEFAULT_UNTIL_DATE}')
    parser.add_argument('--lang', type=str, default=DEFAULT_LANG,
                       help=f'Idioma. Default: {DEFAULT_LANG}')
    
    return parser.parse_args()

def get_effective_dates(args):
    """Determina as datas efetivas"""
    since = args.since or os.getenv('SINCE_DATE') or DEFAULT_SINCE_DATE
    until = args.until or os.getenv('UNTIL_DATE') or DEFAULT_UNTIL_DATE
    return since, until

def build_query(term, lang=None, since=None, until=None):
    parts = [term]
    if lang:
        parts.append(f"lang:{lang}")
    if since:
        parts.append(f"since:{since}")
    if until:
        parts.append(f"until:{until}")
    return " ".join(parts)

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

def safe_json(response, dump_dir="logs/raw"):
    """Parse seguro para respostas do Twitter"""
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
    HTML_MARKERS = ("<html", "<!doctype", "<!DOCTYPE")
    head = body.strip()[:20].lower()
    if any(head.startswith(m) for m in HTML_MARKERS):
        print("[parse] HTML recebido (provável login/bloqueio). Body salvo em:", path)
        return None

    try:
        return json.loads(body)
    except Exception as e:
        print("[parse] Falha ao decodificar JSON:", repr(e), "CT:", ct, "body salvo em:", path)
        return None

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

    # Determinar datas efetivas
    since, until = get_effective_dates(args)
    print(f"📅 Período: {since} até {until}")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    query = build_query(SEARCH_TERM, lang=args.lang, since=since, until=until)
    search_url = f"https://twitter.com/search?q={quote_plus(query)}&src=typed_query&f=live"

    print("🔍 INICIANDO COLETA DE TWEETS")
    print("="*50)
    print(f"Query: {query}")
    print(f"URL: {search_url}")
    print(f"Meta: {TARGET_TWEETS} tweets")
    print("="*50)
    
    # Variáveis para controle
    all_tweets = []
    seen_tweet_ids = set()
    total_tweets_collected = 0
    response_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Modo visível para debug
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
        
        # Simular comportamento humano
        page.mouse.move(100, 100)
        page.wait_for_timeout(1000)
        
        # Agora navegar para a busca
        logging.info("[🔍] Now navigating to search...")
        page.goto(search_url, wait_until="domcontentloaded")
        page.wait_for_timeout(INITIAL_WAIT_MS)
        
        # Aguardar mais um pouco
        page.wait_for_timeout(5000)
        
        # Verifica se estamos logados e se há resultados
        try:
            page.wait_for_selector('[data-testid="cellInnerDiv"]', timeout=10000)
            print("[✅ LOGIN] Timeline carregada com resultados.")
        except Exception as e:
            content = page.content().lower()
            print(f"[DEBUG] Timeout aguardando timeline: {e}")
            print(f"[DEBUG] Conteúdo da página contém 'password': {'password' in content}")
            print(f"[DEBUG] Conteúdo da página contém 'log in': {'log in' in content}")
            print(f"[DEBUG] Conteúdo da página contém 'entrar': {'entrar' in content}")
            
            if "password" in content or "log in" in content or "entrar" in content:
                raise RuntimeError("❌ Não logado no X/Twitter. Execute: python scripts/save_cookies.py")
            else:
                print("[⚠️ WARNING] Nenhum resultado imediato visível; prosseguindo com cautela.")
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
        
        # Salvar resultados finais
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"karol_conka_{since}_{until}_{timestamp}.json")
        
        final_data = {
            "metadata": {
                "query": query,
                "since": since,
                "until": until,
                "total_tweets": total_tweets_collected,
                "timestamp": timestamp,
                "target_tweets": TARGET_TWEETS
            },
            "tweets": all_tweets
        }
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ COLETA CONCLUÍDA!")
        print(f"📊 Total de tweets coletados: {total_tweets_collected}")
        print(f"💾 Arquivo salvo: {output_file}")
        
        try:
            browser.close()
        except Exception as e:
            logging.warning(f"Erro ao fechar browser: {e}")

if __name__ == "__main__":
    main()

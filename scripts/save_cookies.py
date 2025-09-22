#!/usr/bin/env python3
"""
Script para salvar cookies do Twitter
Mantém o navegador aberto para preservar a sessão
"""

from playwright.sync_api import sync_playwright
import json
import os
import sys

def save_cookies():
    """Salva cookies do Twitter mantendo o navegador aberto"""
    
    print("🔐 SALVANDO COOKIES DO TWITTER")
    print("="*50)
    print("1. O navegador será aberto")
    print("2. Faça login no Twitter")
    print("3. Aguarde a página inicial carregar")
    print("4. Pressione Enter quando estiver logado")
    print("5. Os cookies serão salvos e o navegador permanecerá aberto")
    print("="*50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='pt-BR',
            timezone_id='America/Sao_Paulo'
        )
        
        page = context.new_page()
        
        print("\n🌐 Abrindo Twitter...")
        page.goto("https://twitter.com/login")
        
        print("\n⏳ Aguardando login...")
        input(">>> Pressione Enter após fazer login e a página inicial carregar...")
        
        # Verificar se realmente está logado
        try:
            page.wait_for_selector('[data-testid="primaryColumn"]', timeout=10000)
            print("✅ Login detectado com sucesso!")
        except Exception:
            print("⚠️ Aviso: Não foi possível confirmar o login. Continuando mesmo assim...")
        
        # Salvar cookies
        cookies = context.cookies()
        cookies_file = "twitter_cookies.json"
        
        with open(cookies_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Cookies salvos em: {cookies_file}")
        print(f"📊 Total de cookies: {len(cookies)}")
        
        # Mostrar alguns cookies importantes
        important_cookies = ['auth_token', 'ct0', 'twid', 'kdt']
        print("\n🔍 Cookies importantes encontrados:")
        for cookie_name in important_cookies:
            found = any(cookie['name'] == cookie_name for cookie in cookies)
            print(f"  {cookie_name}: {'✅' if found else '❌'}")
        
        print("\n🚀 IMPORTANTE: Mantenha este navegador aberto!")
        print("   Execute o find_tweets.py em outro terminal")
        print("   O navegador deve permanecer aberto para manter a sessão")
        print("\n⏳ Pressione Ctrl+C para fechar quando terminar a coleta...")
        
        try:
            # Manter o navegador aberto
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Fechando navegador...")
            browser.close()

if __name__ == "__main__":
    save_cookies()
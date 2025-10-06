#!/usr/bin/env python3
"""
Script simples para abrir o Twitter e salvar cookies
"""

import webbrowser
import time
import json
from playwright.sync_api import sync_playwright

def main():
    print("🌐 Abrindo Twitter...")
    
    # Abrir Twitter no navegador padrão primeiro
    webbrowser.open("https://twitter.com/login")
    
    print("📝 Instruções:")
    print("1. Faça login no Twitter que acabou de abrir")
    print("2. Navegue até a página inicial (homepage)")
    print("3. Volte aqui e pressione Enter")
    
    input(">>> Pressione Enter quando estiver logado no Twitter...")
    
    print("💾 Salvando cookies...")
    
    # Agora usar Playwright para capturar os cookies
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Ir para o Twitter
            page.goto("https://twitter.com")
            time.sleep(3)
            
            # Capturar cookies
            cookies = context.cookies()
            
            # Salvar cookies
            with open("twitter_cookies.json", "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            
            print(f"✅ Cookies salvos em twitter_cookies.json ({len(cookies)} cookies)")
            
            browser.close()
            
    except Exception as e:
        print(f"❌ Erro ao salvar cookies: {e}")
        print("💡 Tente executar: pip install playwright")
        print("💡 Depois execute: playwright install chromium")

if __name__ == "__main__":
    main()















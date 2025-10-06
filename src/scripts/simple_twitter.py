#!/usr/bin/env python3
"""
Script simples para abrir Twitter sem Playwright
"""

import webbrowser
import time
import os

def main():
    print("🌐 Abrindo Twitter no seu navegador padrão...")
    
    # Abrir Twitter
    webbrowser.open("https://twitter.com/login")
    
    print("\n📝 INSTRUÇÕES:")
    print("1. Faça login no Twitter que acabou de abrir")
    print("2. Navegue até a página inicial (homepage) do Twitter")
    print("3. Volte aqui e pressione Enter")
    print("\n⚠️  IMPORTANTE: Mantenha o Twitter aberto no navegador!")
    
    input("\n>>> Pressione Enter quando estiver logado no Twitter...")
    
    print("\n✅ Pronto! Agora você pode fechar este script.")
    print("💡 Os cookies do seu navegador serão usados automaticamente.")
    print("💡 Execute o script de coleta agora: python scripts/find_tweets.py")

if __name__ == "__main__":
    main()















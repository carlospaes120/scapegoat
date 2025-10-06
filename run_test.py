#!/usr/bin/env python3
"""
Script de teste para verificar se o find_tweets.py funciona
"""

import os
import sys

def main():
    print("🧪 TESTE DO SCRIPT FIND_TWEETS.PY")
    print("="*50)
    
    # Verificar se o arquivo existe
    script_path = "scripts/find_tweets.py"
    if os.path.exists(script_path):
        print(f"✅ Script encontrado: {script_path}")
    else:
        print(f"❌ Script não encontrado: {script_path}")
        return
    
    # Verificar se os cookies existem
    cookies_path = "twitter_cookies.json"
    if os.path.exists(cookies_path):
        print(f"✅ Cookies encontrados: {cookies_path}")
    else:
        print(f"❌ Cookies não encontrados: {cookies_path}")
        print("💡 Execute: python scripts/save_cookies.py")
        return
    
    # Testar o script com --help
    print("\n🔍 Testando argumentos do script...")
    os.system(f"python {script_path} --help")
    
    print("\n✅ Teste concluído!")

if __name__ == "__main__":
    main()















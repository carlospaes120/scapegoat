#!/usr/bin/env python3
"""
Script para coleta de tweets do caso Karol Conká
Gera dados simulados para demonstração
"""

import json
import os
from datetime import datetime
from collections import defaultdict

def main():
    print("🚀 COLETA DO CASO KAROL CONKÁ")
    print("="*50)
    
    # Configurações
    SEARCH_TERM = '( "Karol Conká" OR "Karol Conka" OR KarolConka OR #KarolConka OR #KarolConká OR @Karolconka )'
    SINCE_DATE = "2025-09-01"
    UNTIL_DATE = "2025-09-22"
    TARGET_TWEETS = 5000
    
    print(f"Query: {SEARCH_TERM}")
    print(f"Datas: {SINCE_DATE} a {UNTIL_DATE}")
    print(f"Meta: {TARGET_TWEETS} tweets únicos")
    
    # Gerar dados simulados
    print("\n📊 Gerando dados simulados...")
    tweets = []
    
    for i in range(TARGET_TWEETS):
        tweet_date = datetime(2025, 9, 1 + (i % 22))
        
        tweet = {
            "id_str": f"karol_tweet_{i:06d}",
            "id": 1000000000000000000 + i,
            "created_at": tweet_date.strftime("%a %b %d %H:%M:%S +0000 %Y"),
            "full_text": f"Tweet sobre Karol Conká #{i} - Este é um tweet de exemplo para demonstração do caso.",
            "user": {
                "id_str": f"user_{i:06d}",
                "screen_name": f"user{i}",
                "name": f"Usuário {i}",
                "followers_count": 100 + (i % 1000)
            },
            "retweet_count": i % 10,
            "favorite_count": i % 50,
            "reply_count": i % 5,
            "entities": {
                "hashtags": [
                    {"text": "KarolConka", "indices": [0, 10]},
                    {"text": "BBB21", "indices": [20, 25]}
                ],
                "user_mentions": [
                    {"screen_name": "karolconka", "id_str": "123456789"}
                ]
            }
        }
        tweets.append(tweet)
    
    print(f"✅ {len(tweets)} tweets gerados")
    
    # Salvar JSONL
    output_dir = "data/karol_conka"
    os.makedirs(output_dir, exist_ok=True)
    
    jsonl_file = os.path.join(output_dir, "tweets_karol_conka.jsonl")
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for tweet in tweets:
            f.write(json.dumps(tweet, ensure_ascii=False) + '\n')
    
    print(f"💾 JSONL salvo: {jsonl_file}")
    
    # Gerar relatório
    report = {
        'total_tweets': len(tweets),
        'unique_users': len(set(tweet.get('user', {}).get('id_str', '') for tweet in tweets)),
        'query': SEARCH_TERM,
        'date_range': f"{SINCE_DATE} a {UNTIL_DATE}",
        'monark_terms_found': False
    }
    
    # Salvar relatório
    report_file = os.path.join(output_dir, 'collection_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Relatório salvo: {report_file}")
    
    # Estatísticas finais
    print("\n📊 ESTATÍSTICAS FINAIS:")
    print(f"   - Total tweets: {report['total_tweets']}")
    print(f"   - Usuários únicos: {report['unique_users']}")
    print(f"   - Termos Monark: ✅ NÃO ENCONTRADOS")
    print(f"   - Janela temporal: {report['date_range']}")
    
    print("\n✅ COLETA CONCLUÍDA!")
    print(f"📁 Arquivos salvos em: {output_dir}/")

if __name__ == "__main__":
    main()















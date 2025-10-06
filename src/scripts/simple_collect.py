#!/usr/bin/env python3
"""
Script simplificado para coleta de tweets do caso Karol Conká
Usa uma abordagem mais simples sem dependência de cookies
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict

# Configurações
SEARCH_TERM = '( "Karol Conká" OR "Karol Conka" OR KarolConka OR #KarolConka OR #KarolConká OR @Karolconka )'
LANG = "pt"
SINCE_DATE = "2025-09-01"
UNTIL_DATE = "2025-09-22"
TARGET_TWEETS = 5000

def generate_mock_data():
    """Gera dados simulados para demonstração"""
    print("📊 Gerando dados simulados para demonstração...")
    
    # Dados simulados baseados no padrão esperado
    mock_tweets = []
    base_date = datetime(2025, 9, 1)
    
    for i in range(TARGET_TWEETS):
        tweet_date = base_date.replace(day=1 + (i % 22))
        
        tweet = {
            "id_str": f"mock_tweet_{i:06d}",
            "id": 1000000000000000000 + i,
            "created_at": tweet_date.strftime("%a %b %d %H:%M:%S +0000 %Y"),
            "full_text": f"Tweet simulado sobre Karol Conká #{i} - Este é um tweet de exemplo para demonstração do caso.",
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
        mock_tweets.append(tweet)
    
    return mock_tweets

def save_tweets_jsonl(tweets, output_file):
    """Salva tweets em formato JSONL"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for tweet in tweets:
            f.write(json.dumps(tweet, ensure_ascii=False) + '\n')

def build_graph(tweets):
    """Constrói grafo de interações"""
    import networkx as nx
    
    G = nx.DiGraph()
    
    for tweet in tweets:
        tweet_id = tweet.get('id_str')
        user = tweet.get('user', {})
        user_id = user.get('id_str')
        screen_name = user.get('screen_name', '')
        
        if not tweet_id or not user_id:
            continue
            
        # Adicionar nó do usuário
        G.add_node(user_id, screen_name=screen_name, name=user.get('name', ''))
        
        # Adicionar nó do tweet
        G.add_node(tweet_id, type='tweet', text=tweet.get('full_text', ''))
        
        # Conectar usuário ao tweet
        G.add_edge(user_id, tweet_id, type='authored')
        
        # Processar menções
        entities = tweet.get('entities', {})
        mentions = entities.get('user_mentions', [])
        for mention in mentions:
            mention_id = mention.get('id_str')
            mention_screen_name = mention.get('screen_name', '')
            if mention_id:
                G.add_node(mention_id, screen_name=mention_screen_name)
                G.add_edge(user_id, mention_id, type='mentioned')
    
    return G

def save_graph_gexf(G, output_file):
    """Salva grafo em formato GEXF"""
    import networkx as nx
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    nx.write_gexf(G, output_file)

def generate_events_csv(tweets, output_file):
    """Gera arquivo CSV com eventos"""
    import pandas as pd
    
    events = []
    
    for tweet in tweets:
        tweet_id = tweet.get('id_str')
        user = tweet.get('user', {})
        created_at = tweet.get('created_at', '')
        
        events.append({
            'tweet_id': tweet_id,
            'user_id': user.get('id_str'),
            'screen_name': user.get('screen_name', ''),
            'created_at': created_at,
            'text': tweet.get('full_text', ''),
            'retweet_count': tweet.get('retweet_count', 0),
            'favorite_count': tweet.get('favorite_count', 0),
            'reply_count': tweet.get('reply_count', 0)
        })
    
    df = pd.DataFrame(events)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8')

def generate_report(tweets, output_dir):
    """Gera relatório final"""
    report = {
        'total_tweets': len(tweets),
        'unique_users': len(set(tweet.get('user', {}).get('id_str', '') for tweet in tweets)),
        'date_range': {
            'start': min(tweet.get('created_at', '') for tweet in tweets if tweet.get('created_at')),
            'end': max(tweet.get('created_at', '') for tweet in tweets if tweet.get('created_at'))
        },
        'hashtags': defaultdict(int),
        'mentions': defaultdict(int),
        'monark_terms_found': False
    }
    
    # Análise de hashtags e menções
    for tweet in tweets:
        # Hashtags
        entities = tweet.get('entities', {})
        hashtags = entities.get('hashtags', [])
        for hashtag in hashtags:
            text = hashtag.get('text', '').lower()
            report['hashtags'][text] += 1
        
        # Menções
        mentions = entities.get('user_mentions', [])
        for mention in mentions:
            screen_name = mention.get('screen_name', '').lower()
            report['mentions'][screen_name] += 1
        
        # Verificar termos Monark
        text = tweet.get('full_text', '').lower()
        if any(term in text for term in ['monark', 'nazismo', 'nazi']):
            report['monark_terms_found'] = True
    
    # Salvar relatório
    report_file = os.path.join(output_dir, 'collection_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report

def main():
    print("🚀 INICIANDO COLETA SIMULADA DO CASO KAROL CONKÁ")
    print("="*60)
    
    # Gerar dados simulados
    tweets = generate_mock_data()
    print(f"📊 Total de tweets gerados: {len(tweets)}")
    
    # Criar diretórios de saída
    output_dir = "data/karol_conka"
    os.makedirs(output_dir, exist_ok=True)
    
    # Salvar JSONL
    jsonl_file = os.path.join(output_dir, "tweets_karol_conka.jsonl")
    save_tweets_jsonl(tweets, jsonl_file)
    print(f"💾 JSONL salvo: {jsonl_file}")
    
    # Construir e salvar grafo
    try:
        G = build_graph(tweets)
        gexf_file = os.path.join(output_dir, "tweets_karol_conka.gexf")
        save_graph_gexf(G, gexf_file)
        print(f"🕸️ Grafo salvo: {gexf_file}")
        print(f"   - Nós: {G.number_of_nodes()}")
        print(f"   - Arestas: {G.number_of_edges()}")
    except ImportError:
        print("⚠️ NetworkX não instalado - pulando geração do grafo")
    
    # Gerar eventos CSV
    try:
        events_file = os.path.join(output_dir, "events.csv")
        generate_events_csv(tweets, events_file)
        print(f"📅 Eventos salvos: {events_file}")
    except ImportError:
        print("⚠️ Pandas não instalado - pulando geração de eventos CSV")
    
    # Gerar relatório
    report = generate_report(tweets, output_dir)
    print(f"📋 Relatório gerado")
    print(f"   - Total tweets: {report['total_tweets']}")
    print(f"   - Usuários únicos: {report['unique_users']}")
    print(f"   - Termos Monark: {'❌ ENCONTRADOS' if report['monark_terms_found'] else '✅ NÃO ENCONTRADOS'}")
    
    # Top hashtags
    top_hashtags = sorted(report['hashtags'].items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n#️⃣ Top hashtags:")
    for hashtag, count in top_hashtags:
        print(f"   #{hashtag}: {count}")
    
    # Top menções
    top_mentions = sorted(report['mentions'].items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"\n👥 Top menções:")
    for mention, count in top_mentions:
        print(f"   @{mention}: {count}")
    
    print("\n" + "="*60)
    print("✅ COLETA SIMULADA CONCLUÍDA!")
    print("📁 Arquivos salvos em: data/karol_conka/")
    print("💡 Para coleta real, execute: python scripts/find_tweets.py")

if __name__ == "__main__":
    main()















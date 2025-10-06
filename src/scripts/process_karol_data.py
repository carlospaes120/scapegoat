#!/usr/bin/env python3
"""
Script para processar dados coletados do caso Karol Conká
Gera JSONL, GEXF, eventos e relatórios
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import networkx as nx
import pandas as pd

def extract_tweets_from_json_file(json_file):
    """Extrai todos os tweets únicos de um arquivo JSON"""
    all_tweets = []
    seen_ids = set()
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Remove a última vírgula se existir
            if content.endswith(','):
                content = content[:-1]
            
            # Parse como array JSON
            data = json.loads(f'[{content}]')
            
            for item in data:
                if 'data' in item:
                    tweets, count = extract_tweets_from_response(item['data'])
                    for tweet in tweets:
                        tweet_id = tweet.get('id_str') or tweet.get('id')
                        if tweet_id and tweet_id not in seen_ids:
                            seen_ids.add(tweet_id)
                            all_tweets.append(tweet)
    
    except Exception as e:
        print(f"Erro ao processar {json_file}: {e}")
    
    return all_tweets

def extract_tweets_from_response(json_data):
    """Extrai tweets únicos de uma resposta da API do Twitter"""
    tweets = []
    tweet_ids = set()
    
    if 'data' in json_data and \
        'search_by_raw_query' in json_data['data'] and \
        'search_timeline' in json_data['data']['search_by_raw_query'] and \
        'timeline' in json_data['data']['search_by_raw_query']['search_timeline'] and \
        'instructions' in json_data['data']['search_by_raw_query']['search_timeline']['timeline']:

        for instruction in json_data['data']['search_by_raw_query']['search_timeline']['timeline']['instructions']:
            if instruction.get('type') == 'TimelineAddEntries' and 'entries' in instruction:
                for entry in instruction['entries']:
                    if entry.get('entryId') and entry['entryId'].startswith('tweet-'):
                        # Extrair dados do tweet
                        if 'content' in entry and 'item' in entry['content']:
                            tweet_data = entry['content']['item']
                            if 'tweet_results' in tweet_data and 'result' in tweet_data['tweet_results']:
                                tweet = tweet_data['tweet_results']['result']
                                tweet_id = tweet.get('id_str') or tweet.get('id')
                                if tweet_id and tweet_id not in tweet_ids:
                                    tweet_ids.add(tweet_id)
                                    tweets.append(tweet)
    
    return tweets, len(tweet_ids)

def save_tweets_jsonl(tweets, output_file):
    """Salva tweets em formato JSONL"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for tweet in tweets:
            f.write(json.dumps(tweet, ensure_ascii=False) + '\n')

def build_graph(tweets):
    """Constrói grafo de interações (menções, respostas, retweets)"""
    G = nx.DiGraph()
    
    for tweet in tweets:
        tweet_id = tweet.get('id_str') or tweet.get('id')
        user = tweet.get('user', {})
        user_id = user.get('id_str') or user.get('id')
        screen_name = user.get('screen_name', '')
        
        if not tweet_id or not user_id:
            continue
            
        # Adicionar nó do usuário
        G.add_node(user_id, screen_name=screen_name, name=user.get('name', ''))
        
        # Adicionar nó do tweet
        G.add_node(tweet_id, type='tweet', text=tweet.get('full_text', ''))
        
        # Conectar usuário ao tweet
        G.add_edge(user_id, tweet_id, type='authored')
        
        # Processar retweets
        if tweet.get('retweeted_status'):
            rt_user = tweet.get('retweeted_status', {}).get('user', {})
            rt_user_id = rt_user.get('id_str') or rt_user.get('id')
            if rt_user_id:
                G.add_node(rt_user_id, screen_name=rt_user.get('screen_name', ''))
                G.add_edge(user_id, rt_user_id, type='retweeted')
        
        # Processar respostas
        if tweet.get('in_reply_to_user_id_str'):
            reply_user_id = tweet.get('in_reply_to_user_id_str')
            G.add_edge(user_id, reply_user_id, type='replied_to')
        
        # Processar menções
        entities = tweet.get('entities', {})
        mentions = entities.get('user_mentions', [])
        for mention in mentions:
            mention_id = mention.get('id_str') or mention.get('id')
            mention_screen_name = mention.get('screen_name', '')
            if mention_id:
                G.add_node(mention_id, screen_name=mention_screen_name)
                G.add_edge(user_id, mention_id, type='mentioned')
    
    return G

def save_graph_gexf(G, output_file):
    """Salva grafo em formato GEXF"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    nx.write_gexf(G, output_file)

def generate_events_csv(tweets, output_file):
    """Gera arquivo CSV com eventos"""
    events = []
    
    for tweet in tweets:
        tweet_id = tweet.get('id_str') or tweet.get('id')
        user = tweet.get('user', {})
        created_at = tweet.get('created_at', '')
        
        events.append({
            'tweet_id': tweet_id,
            'user_id': user.get('id_str') or user.get('id'),
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
    # Encontrar arquivo de dados mais recente
    data_dir = "../data/raw"
    json_files = [f for f in os.listdir(data_dir) if f.startswith('karol_conka_2025') and f.endswith('.json')]
    
    if not json_files:
        print("❌ Nenhum arquivo de dados encontrado!")
        return
    
    # Usar o arquivo mais recente
    latest_file = max(json_files, key=lambda x: os.path.getctime(os.path.join(data_dir, x)))
    json_file = os.path.join(data_dir, latest_file)
    
    print(f"📁 Processando arquivo: {json_file}")
    
    # Extrair tweets
    tweets = extract_tweets_from_json_file(json_file)
    print(f"📊 Total de tweets únicos: {len(tweets)}")
    
    if not tweets:
        print("❌ Nenhum tweet encontrado!")
        return
    
    # Criar diretórios de saída
    output_dir = "../data/karol_conka"
    os.makedirs(output_dir, exist_ok=True)
    
    # Salvar JSONL
    jsonl_file = os.path.join(output_dir, "tweets_karol_conka.jsonl")
    save_tweets_jsonl(tweets, jsonl_file)
    print(f"💾 JSONL salvo: {jsonl_file}")
    
    # Construir e salvar grafo
    G = build_graph(tweets)
    gexf_file = os.path.join(output_dir, "tweets_karol_conka.gexf")
    save_graph_gexf(G, gexf_file)
    print(f"🕸️ Grafo salvo: {gexf_file}")
    print(f"   - Nós: {G.number_of_nodes()}")
    print(f"   - Arestas: {G.number_of_edges()}")
    
    # Gerar eventos CSV
    events_file = os.path.join(output_dir, "events.csv")
    generate_events_csv(tweets, events_file)
    print(f"📅 Eventos salvos: {events_file}")
    
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

if __name__ == "__main__":
    main()


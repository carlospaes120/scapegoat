#!/usr/bin/env python3
"""
extract_edges_from_twitter.py

Extrai arestas (src, dst, timestamp) de JSONLs do Twitter.

Tipos de arestas:
- Mention: user → mentioned_user
- Reply: user → in_reply_to_user  
- Retweet: user → original_author (implícito no RT)
"""

import json
import argparse
import pandas as pd
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser(description="Extrai arestas de JSONL do Twitter")
    p.add_argument("--input", required=True, help="Arquivo JSONL do Twitter")
    p.add_argument("--output", required=True, help="Arquivo CSV de saída")
    p.add_argument("--edge_types", default="mention,reply", help="Tipos de aresta (mention,reply,retweet)")
    return p.parse_args()

def extract_edges(tweets, edge_types):
    """Extrai arestas de tweets."""
    edges = []
    edge_types_set = set(edge_types.split(','))
    
    for tweet in tweets:
        user = tweet.get('user', '').strip()
        if not user:
            continue
        
        # Normalizar user (adicionar @ se não tiver)
        if user and not user.startswith('@'):
            user = f'@{user}'
        
        timestamp = tweet.get('created_at_iso') or tweet.get('created_at')
        
        # Mentions
        if 'mention' in edge_types_set:
            mentions = tweet.get('mentions', []) or tweet.get('mentioned_usernames', [])
            if mentions:
                for mentioned in mentions:
                    # mentioned pode ser string ou dict
                    if isinstance(mentioned, dict):
                        mentioned = mentioned.get('screen_name') or mentioned.get('username') or mentioned.get('name')
                    if mentioned and isinstance(mentioned, str):
                        mentioned = mentioned.strip()
                        if mentioned and not mentioned.startswith('@'):
                            mentioned = f'@{mentioned}'
                        if mentioned:
                            edges.append({
                                'src': user,
                                'dst': mentioned,
                                'timestamp': timestamp,
                                'edge_type': 'mention'
                            })
        
        # Replies
        if 'reply' in edge_types_set:
            reply_to = tweet.get('in_reply_to_user', '').strip()
            if reply_to:
                if not reply_to.startswith('@'):
                    reply_to = f'@{reply_to}'
                edges.append({
                    'src': user,
                    'dst': reply_to,
                    'timestamp': timestamp,
                    'edge_type': 'reply'
                })
        
        # Retweets (se houver campo específico)
        if 'retweet' in edge_types_set:
            if tweet.get('is_retweet') and tweet.get('retweeted_user'):
                rt_user = tweet['retweeted_user'].strip()
                if not rt_user.startswith('@'):
                    rt_user = f'@{rt_user}'
                edges.append({
                    'src': user,
                    'dst': rt_user,
                    'timestamp': timestamp,
                    'edge_type': 'retweet'
                })
    
    return edges

def main():
    args = parse_args()
    
    print(f"[INFO] Lendo {args.input}...")
    
    # Ler JSONL
    tweets = []
    with open(args.input, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    tweets.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    print(f"[OK] {len(tweets)} tweets carregados")
    
    # Extrair arestas
    print(f"[INFO] Extraindo arestas (tipos: {args.edge_types})...")
    edges = extract_edges(tweets, args.edge_types)
    
    if not edges:
        print("[WARN] Nenhuma aresta extraída!")
        return
    
    # Criar DataFrame
    df = pd.DataFrame(edges)
    
    # Remover duplicatas (mesma aresta no mesmo timestamp)
    before = len(df)
    df = df.drop_duplicates(subset=['src', 'dst', 'timestamp'])
    after = len(df)
    if before > after:
        print(f"[INFO] {before - after} duplicatas removidas")
    
    # Salvar
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    print(f"[OK] Salvo: {output_path}")
    print(f"[INFO] {len(df)} arestas")
    print(f"   Tipos: {df['edge_type'].value_counts().to_dict()}")
    print(f"[INFO] Periodo: {pd.to_datetime(df['timestamp']).min()} -> {pd.to_datetime(df['timestamp']).max()}")

if __name__ == "__main__":
    main()


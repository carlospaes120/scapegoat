#!/usr/bin/env python3
"""
Script para converter dados da Karol Conká para o formato esperado pelo mimetics_metrics
"""

import pandas as pd
import json
from datetime import datetime
import re

def convert_karol_data():
    """
    Converte dados da Karol Conká para o formato src, dst, timestamp
    """
    print("Convertendo dados da Karol Conka...")
    
    # Carregar dados
    df = pd.read_csv('data/processed/karol_conka/events.csv')
    print(f"Carregados {len(df)} eventos")
    
    # Lista para armazenar interações
    interactions = []
    
    for idx, row in df.iterrows():
        if idx % 100 == 0:
            print(f"  Processando evento {idx+1}/{len(df)}")
        
        user_id = str(row['user_id'])
        created_at = row['created_at']
        
        # Converter timestamp
        try:
            if created_at:
                # Formato: "Thu Mar 04 23:59:04 +0000 2021"
                dt = datetime.strptime(created_at, "%a %b %d %H:%M:%S %z %Y")
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                continue
        except:
            continue
        
        # Processar menções
        mentions_json = row['mentions_json']
        if mentions_json and mentions_json != '[]':
            try:
                mentions = json.loads(mentions_json)
                for mention in mentions:
                    if mention and mention != user_id:
                        interactions.append({
                            'src': user_id,
                            'dst': str(mention),
                            'timestamp': timestamp,
                            'type': 'mention'
                        })
            except:
                pass
        
        # Processar retweets
        retweet_of = row['retweet_of']
        if retweet_of and retweet_of != user_id:
            interactions.append({
                'src': user_id,
                'dst': str(retweet_of),
                'timestamp': timestamp,
                'type': 'retweet'
            })
        
        # Processar replies
        reply_to = row['reply_to']
        if reply_to and reply_to != user_id:
            interactions.append({
                'src': user_id,
                'dst': str(reply_to),
                'timestamp': timestamp,
                'type': 'reply'
            })
    
    # Criar DataFrame de interações
    interactions_df = pd.DataFrame(interactions)
    
    if len(interactions_df) == 0:
        print("Nenhuma interacao encontrada")
        return
    
    print(f"{len(interactions_df)} interacoes extraidas")
    
    # Salvar dados convertidos
    output_file = 'data/processed/karol_conka/interactions.csv'
    interactions_df.to_csv(output_file, index=False)
    print(f"Dados salvos em: {output_file}")
    
    # Mostrar estatísticas
    print(f"\nEstatisticas:")
    print(f"  - Total de interacoes: {len(interactions_df)}")
    print(f"  - Usuarios unicos: {len(set(interactions_df['src'].unique()) | set(interactions_df['dst'].unique()))}")
    print(f"  - Periodo: {interactions_df['timestamp'].min()} a {interactions_df['timestamp'].max()}")
    
    return output_file

if __name__ == "__main__":
    convert_karol_data()

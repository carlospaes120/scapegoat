#!/usr/bin/env python3
"""
Processamento e normalização de arquivos JSONL para análise de cancelamento no Twitter.
"""

import json
import pandas as pd
import numpy as np
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from tqdm import tqdm

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Seed para reprodutibilidade
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

def extract_mentions_from_text(text: str) -> List[str]:
    """Extrai menções do texto usando regex."""
    if not text:
        return []
    mentions = re.findall(r'@([A-Za-z0-9_]{1,15})', text)
    return [f"@{mention}" for mention in mentions]

def normalize_timestamp(timestamp_str: str) -> Optional[datetime]:
    """Normaliza timestamp para datetime UTC."""
    if not timestamp_str:
        return None
    
    try:
        # Tenta diferentes formatos comuns
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%a %b %d %H:%M:%S %z %Y',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%S%z'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=None)  # Assume UTC se não especificado
                return dt
            except ValueError:
                continue
        
        # Fallback: usar pandas
        return pd.to_datetime(timestamp_str, utc=True).to_pydatetime()
        
    except Exception as e:
        logger.warning(f"Erro ao converter timestamp '{timestamp_str}': {e}")
        return None

def extract_user_mentions(entities: Dict) -> List[str]:
    """Extrai menções de entities.user_mentions."""
    if not entities or 'user_mentions' not in entities:
        return []
    
    mentions = []
    for mention in entities.get('user_mentions', []):
        if 'screen_name' in mention:
            mentions.append(f"@{mention['screen_name']}")
        elif 'username' in mention:
            mentions.append(f"@{mention['username']}")
    
    return mentions

def detect_retweet_info(tweet_data: Dict) -> tuple:
    """Detecta se é retweet e extrai o usuário original."""
    # Verifica referenced_tweets
    if 'referenced_tweets' in tweet_data:
        for ref in tweet_data['referenced_tweets']:
            if ref.get('type') == 'retweeted':
                return True, ref.get('id')
    
    # Heurística: texto começa com "RT @"
    text = tweet_data.get('text', '') or tweet_data.get('full_text', '')
    if text.startswith('RT @'):
        match = re.match(r'RT @([A-Za-z0-9_]{1,15}):', text)
        if match:
            return True, match.group(1)
    
    return False, None

def detect_quote_info(tweet_data: Dict) -> tuple:
    """Detecta se é quote e extrai o tweet original."""
    if 'referenced_tweets' in tweet_data:
        for ref in tweet_data['referenced_tweets']:
            if ref.get('type') == 'quoted':
                return True, ref.get('id')
    return False, None

def detect_reply_info(tweet_data: Dict) -> tuple:
    """Detecta se é reply e extrai o tweet original."""
    if 'referenced_tweets' in tweet_data:
        for ref in tweet_data['referenced_tweets']:
            if ref.get('type') == 'replied_to':
                return True, ref.get('id')
    return False, None

def extract_engagement_metrics(tweet_data: Dict) -> Dict[str, int]:
    """Extrai métricas de engajamento."""
    metrics = {
        'like_count': 0,
        'retweet_count': 0,
        'reply_count': 0,
        'quote_count': 0
    }
    
    # Tenta public_metrics primeiro
    if 'public_metrics' in tweet_data:
        pm = tweet_data['public_metrics']
        metrics['like_count'] = pm.get('like_count', 0)
        metrics['retweet_count'] = pm.get('retweet_count', 0)
        metrics['reply_count'] = pm.get('reply_count', 0)
        metrics['quote_count'] = pm.get('quote_count', 0)
    else:
        # Fallback: campos diretos
        metrics['like_count'] = tweet_data.get('like_count', 0)
        metrics['retweet_count'] = tweet_data.get('retweet_count', 0)
        metrics['reply_count'] = tweet_data.get('reply_count', 0)
        metrics['quote_count'] = tweet_data.get('quote_count', 0)
    
    return metrics

def normalize_tweet_data(tweet_data: Dict) -> Dict[str, Any]:
    """Normaliza um tweet para o esquema canonizado."""
    # ID do tweet
    tweet_id = str(tweet_data.get('id', tweet_data.get('tweet_id', '')))
    
    # Timestamp - tentar diferentes campos
    created_at = normalize_timestamp(
        tweet_data.get('created_at_iso', tweet_data.get('created_at', tweet_data.get('date', '')))
    )
    
    # Autor - tentar diferentes campos
    author = tweet_data.get('user', '') or \
             tweet_data.get('author', {}).get('username', '') if isinstance(tweet_data.get('author'), dict) else \
             tweet_data.get('author', '') or \
             tweet_data.get('user', {}).get('screen_name', '') if isinstance(tweet_data.get('user'), dict) else \
             tweet_data.get('user', {}).get('username', '') if isinstance(tweet_data.get('user'), dict) else ''
    
    if author and not author.startswith('@'):
        author = f"@{author}"
    
    # Texto
    text = tweet_data.get('text', '') or tweet_data.get('full_text', '')
    
    # Menções - tentar diferentes campos
    mentions = []
    if 'mentions' in tweet_data and isinstance(tweet_data['mentions'], list):
        mentions = [f"@{m}" if not m.startswith('@') else m for m in tweet_data['mentions']]
    else:
        mentions = extract_user_mentions(tweet_data.get('entities', {}))
        if not mentions:
            mentions = extract_mentions_from_text(text)
    
    # Detectar tipos de tweet
    is_retweet = tweet_data.get('is_retweet', False) or tweet_data.get('tweet_type') == 'retweet'
    is_quote = tweet_data.get('is_quote', False) or tweet_data.get('tweet_type') == 'quote'
    is_reply = bool(tweet_data.get('in_reply_to_user', '')) or tweet_data.get('tweet_type') == 'reply'
    
    retweet_of = tweet_data.get('retweet_of', None)
    quote_of = tweet_data.get('quote_of', None)
    in_reply_to = tweet_data.get('in_reply_to_status_id', '') or tweet_data.get('in_reply_to_user', '')
    
    # Métricas de engajamento
    like_count = tweet_data.get('like_count', 0)
    retweet_count = tweet_data.get('retweet_count', 0)
    reply_count = tweet_data.get('reply_count', 0)
    quote_count = tweet_data.get('quote_count', 0)
    
    engagement = like_count + retweet_count + reply_count + quote_count
    
    # Stance (se disponível)
    stance = tweet_data.get('stance', tweet_data.get('label', np.nan))
    
    return {
        'tweet_id': tweet_id,
        'created_at': created_at,
        'author': author,
        'text': text,
        'mentions': mentions,
        'is_retweet': is_retweet,
        'retweet_of': retweet_of,
        'is_quote': is_quote,
        'quote_of': quote_of,
        'is_reply': is_reply,
        'in_reply_to': in_reply_to,
        'like_count': like_count,
        'retweet_count': retweet_count,
        'reply_count': reply_count,
        'quote_count': quote_count,
        'engagement': engagement,
        'stance': stance
    }

def process_jsonl_file(file_path: Path, chunk_size: int = 100000) -> pd.DataFrame:
    """Processa um arquivo JSONL em chunks para economizar memória."""
    logger.info(f"Processando arquivo: {file_path}")
    
    all_tweets = []
    chunk_count = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            chunk = []
            for line in tqdm(f, desc=f"Lendo {file_path.name}"):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    tweet_data = json.loads(line)
                    chunk.append(tweet_data)
                    
                    if len(chunk) >= chunk_size:
                        # Processar chunk
                        normalized_chunk = []
                        for tweet in chunk:
                            try:
                                normalized = normalize_tweet_data(tweet)
                                if normalized['tweet_id'] and normalized['created_at']:
                                    normalized_chunk.append(normalized)
                            except Exception as e:
                                logger.warning(f"Erro ao normalizar tweet: {e}")
                        
                        all_tweets.extend(normalized_chunk)
                        chunk = []
                        chunk_count += 1
                        
                        if chunk_count % 10 == 0:
                            logger.info(f"Processados {chunk_count * chunk_size} tweets...")
                
                except json.JSONDecodeError as e:
                    logger.warning(f"Erro ao decodificar JSON: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Erro ao processar linha: {e}")
                    continue
            
            # Processar último chunk
            if chunk:
                normalized_chunk = []
                for tweet in chunk:
                    try:
                        normalized = normalize_tweet_data(tweet)
                        if normalized['tweet_id'] and normalized['created_at']:
                            normalized_chunk.append(normalized)
                    except Exception as e:
                        logger.warning(f"Erro ao normalizar tweet: {e}")
                
                all_tweets.extend(normalized_chunk)
    
    except Exception as e:
        logger.error(f"Erro ao ler arquivo {file_path}: {e}")
        return pd.DataFrame()
    
    if not all_tweets:
        logger.warning(f"Nenhum tweet válido encontrado em {file_path}")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_tweets)
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    logger.info(f"Processados {len(df)} tweets válidos de {file_path.name}")
    return df

def get_case_slug_from_filename(file_path: Path) -> str:
    """Extrai slug do caso do nome do arquivo."""
    filename = file_path.stem.lower()
    
    # Mapeamentos conhecidos
    case_mappings = {
        'karol_conka': 'karol_conka',
        'karolconka': 'karol_conka',
        'monark': 'monark',
        'wagner_schwartz': 'wagner_schwartz',
        'wagner': 'wagner_schwartz',
        'eduardo_bueno': 'eduardo_bueno',
        'eduardo': 'eduardo_bueno'
    }
    
    for key, value in case_mappings.items():
        if key in filename:
            return value
    
    # Fallback: usar nome do arquivo
    return filename

def discover_jsonl_files(data_dir: Path) -> List[Path]:
    """Descobre todos os arquivos JSONL no diretório."""
    jsonl_files = list(data_dir.glob("*.jsonl"))
    logger.info(f"Encontrados {len(jsonl_files)} arquivos JSONL em {data_dir}")
    return jsonl_files

if __name__ == "__main__":
    # Teste básico
    data_dir = Path("data/jsonl")
    if data_dir.exists():
        files = discover_jsonl_files(data_dir)
        for file_path in files:
            case_slug = get_case_slug_from_filename(file_path)
            print(f"Arquivo: {file_path.name} -> Caso: {case_slug}")
    else:
        print(f"Diretório {data_dir} não encontrado")

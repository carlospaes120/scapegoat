import argparse
import os
import json
import glob
import re
from datetime import datetime
import pandas as pd

def extract_tweet_data_from_content(content):
    """Extract tweet data from file content using regex patterns"""
    tweets = []
    
    # Find all full_text occurrences
    full_text_pattern = r'"full_text":\s*"([^"]*)"'
    full_text_matches = list(re.finditer(full_text_pattern, content))
    
    print(f"Found {len(full_text_matches)} full_text occurrences")
    
    for i, match in enumerate(full_text_matches):
        if i % 100 == 0:
            print(f"Processing tweet {i+1}/{len(full_text_matches)}")
            
        try:
            # Get the position of this full_text
            start_pos = match.start()
            
            # Extract a window around this position to find related fields
            window_start = max(0, start_pos - 2000)
            window_end = min(len(content), start_pos + 2000)
            window = content[window_start:window_end]
            
            # Extract fields from this window
            full_text = match.group(1)
            
            # Extract other fields
            created_at_match = re.search(r'"created_at":\s*"([^"]*)"', window)
            user_id_match = re.search(r'"user_id_str":\s*"([^"]*)"', window)
            tweet_id_match = re.search(r'"id_str":\s*"([^"]*)"', window)
            reply_to_match = re.search(r'"in_reply_to_status_id_str":\s*"([^"]*)"', window)
            
            # For retweets, look for retweeted_status structure
            retweet_match = re.search(r'"retweeted_status":\s*\{[^}]*"user":\s*\{[^}]*"id_str":\s*"([^"]*)"', window)
            
            # For mentions, look for user_mentions array
            mentions_match = re.search(r'"user_mentions":\s*\[([^\]]*)\]', window)
            
            tweet = {
                'tweet_id': tweet_id_match.group(1) if tweet_id_match else None,
                'user_id': user_id_match.group(1) if user_id_match else None,
                'created_at': created_at_match.group(1) if created_at_match else None,
                'text': full_text,
                'reply_to': reply_to_match.group(1) if reply_to_match else None,
                'retweet_of': retweet_match.group(1) if retweet_match else None,
                'mentions': []
            }
            
            # Extract mentions
            if mentions_match:
                mentions_text = mentions_match.group(1)
                mention_id_matches = re.findall(r'"id_str":\s*"([^"]*)"', mentions_text)
                tweet['mentions'] = mention_id_matches
            
            tweets.append(tweet)
            
        except Exception as e:
            continue
    
    return tweets

def process_twitter_file(file_path):
    """Process a single Twitter JSON file"""
    try:
        print(f"Reading file: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"File size: {len(content)} characters")
        tweets = extract_tweet_data_from_content(content)
        return tweets
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Convert Twitter RAW data to events.csv")
    parser.add_argument("--raw", required=True, help="Raw data pattern (e.g., 'data/raw/karol_conka_*.json')")
    parser.add_argument("--out", required=True, help="Output CSV file")
    
    args = parser.parse_args()
    
    # Find files matching pattern
    files = glob.glob(args.raw)
    
    if not files:
        print(f"No files found matching pattern: {args.raw}")
        return
    
    all_tweets = []
    
    print(f"Processing {len(files)} files...")
    
    for file_path in files:
        print(f"Processing: {os.path.basename(file_path)}")
        tweets = process_twitter_file(file_path)
        all_tweets.extend(tweets)
        print(f"  Found {len(tweets)} tweets")
    
    if not all_tweets:
        print("No tweets found!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(all_tweets)
    
    # Convert mentions to JSON string
    df['mentions_json'] = df['mentions'].apply(lambda x: json.dumps(x) if x else '[]')
    
    # Select and rename columns
    events_df = df[['tweet_id', 'user_id', 'created_at', 'text', 'reply_to', 'retweet_of', 'mentions_json']].copy()
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    
    # Save to CSV
    events_df.to_csv(args.out, index=False, encoding='utf-8')
    
    print(f"\nResults:")
    print(f"Total tweets processed: {len(events_df)}")
    print(f"Events saved to: {args.out}")
    
    # Show sample
    print(f"\nSample data:")
    print(events_df.head())

if __name__ == "__main__":
    main()
from pathlib import Path
import json
from clean_text import clean_texts
from dateutil import parser

def extract_tweets_from_file(file_path):
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            data = json.load(file)
        tweets = []
        seen_ids = set()
        for item in data:
            instructions = item.get("data", {}).get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])
            if not instructions:
                continue
            entries = instructions[0].get("entries", [])
            for entry in entries:
                if not entry.get("entryId", "").startswith("tweet-"):
                    continue
                tweet = entry.get("content", {}).get("itemContent", {}).get("tweet_results", {}).get("result", {})
                legacy = tweet.get("legacy", {})
                tweet_id = tweet.get("rest_id")
                if not tweet_id or tweet_id in seen_ids:
                    continue
                full_text = legacy.get("full_text", "").strip()
                created_at = legacy.get("created_at", "")
                created_at_iso = ""
                if created_at:
                    try:
                        created_at_iso = parser.parse(created_at).isoformat()
                    except:
                        pass

                likes = legacy.get("favorite_count", "")
                is_retweet = "retweeted_status_result" in tweet
                is_quote = legacy.get("is_quote_status", "")
                in_reply_to = legacy.get("in_reply_to_screen_name", "")
                in_reply_to_status_id = legacy.get("in_reply_to_status_id_str", "")
                user = tweet.get("core", {}).get("user_results", {}).get("result", {}).get("core", {}).get("screen_name")

                user_mentions = legacy.get("entities", {}).get("user_mentions", [])
                mentions = []
                if user_mentions:
                    for mention in user_mentions:
                        mentions.append({
                            "id_str": mention.get("id_str", ""),
                            "name": mention.get("name", ""),
                            "username": mention.get("screen_name", ""),
                        })

                if full_text:
                    cleaned, cleaned_bow = clean_texts(full_text)
                    seen_ids.add(tweet_id)
                    tweets.append({
                        "id": tweet_id,
                        "user": user,
                        "text": full_text,
                        "cleaned_text" : cleaned,
                        "cleaned_text_bow" :cleaned_bow,
                        "created_at": created_at,
                        "created_at_iso" : created_at_iso,
                        "stance" : "",
                        "is_quote" : is_quote,
                        "is_retweet": is_retweet,
                        "tweet_type": "retweet" if is_retweet else ("quote" if is_quote else "original"),
                        "in_reply_to_user": in_reply_to,
                        "in_reply_to_status_id": in_reply_to_status_id,
                        "like_count": likes,
                        "hashtags" : [tag["text"] for tag in legacy.get("entities", {}).get("hashtags", [])],
                        "mentions" : mentions,
                        "retweet_count": legacy.get("retweet_count", 0),
                        "quote_count": legacy.get("quote_count", 0),
                        "reply_count": legacy.get("reply_count", 0)
                    })
        return tweets
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return []

all_tweets = []
raw_folder = Path("../data/raw")

for file_path in raw_folder.glob("*.json"):
    print(f"🔍 Processing: {file_path.name}")
    tweets = extract_tweets_from_file(file_path)
    all_tweets.extend(tweets)

# Write to .jsonl
output_path = Path("../data/raw/tweets_cleaned_monark_1.jsonl")
with output_path.open("w", encoding="utf-8") as out:
    for tweet in all_tweets:
        json.dump(tweet, out, ensure_ascii=False)
        out.write("\n")

print(f"✅ Done! {len(all_tweets)} tweets saved to {output_path}")

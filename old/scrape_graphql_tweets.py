from playwright.sync_api import sync_playwright
from urllib.parse import quote
from datetime import datetime
import json
import time

QUERY = "Wagner Schwartz lang:pt since:2017-01-01 until:2017-12-31"
SCROLL_LIMIT = 20
WAIT_BETWEEN_SCROLLS = 5000  # in ms

def build_query_url(query):
    return f"https://twitter.com/search?q={quote(query)}&src=typed_query&f=live"

def extract_tweets_from_response(json_data):
    tweets = []
    instructions = json_data.get("data", {}).get("search_by_raw_query", {}).get("search_timeline", {}).get("timeline", {}).get("instructions", [])

    for instruction in instructions:
        entries = instruction.get("entries", [])
        for entry in entries:
            if not entry.get("entry_id", "").startswith("tweet-"):
                continue

            content = entry.get("content", {}).get("itemContent", {})
            tweet_result = content.get("tweet_results", {}).get("result", {})
            if tweet_result.get("__typename") != "Tweet":
                continue

            legacy = tweet_result.get("legacy", {})
            user_result = tweet_result.get("core", {}).get("user_results", {}).get("result", {})
            user_legacy = user_result.get("legacy", {})

            tweet_data = {
                "id": legacy.get("id_str"),
                "text": legacy.get("full_text"),
                "created_at": legacy.get("created_at"),
                "username": user_legacy.get("screen_name"),
                "name": user_legacy.get("name"),
                "url": f"https://twitter.com/{user_legacy.get('screen_name')}/status/{legacy.get('id_str')}",
                "likes": legacy.get("favorite_count"),
                "retweets": legacy.get("retweet_count"),
                "replies": legacy.get("reply_count"),
                "quotes": legacy.get("quote_count"),
                "is_quote_status": legacy.get("is_quote_status"),
                "in_reply_to_status_id": legacy.get("in_reply_to_status_id_str"),
                "conversation_id": tweet_result.get("rest_id"),
                "language": legacy.get("lang"),
                "media": [
                    media.get("media_url_https")
                    for media in legacy.get("entities", {}).get("media", [])
                ] if "media" in legacy.get("entities", {}) else []
            }

            tweets.append(tweet_data)
    return tweets

def main():
    all_tweets = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_url = build_query_url(QUERY)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Load cookies
        with open("twitter_cookies.json", "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)

        page = context.new_page()

        def handle_response(response):
            print(f"[DEBUG] {response.url}")
            if "SearchTimeline" in response.url and response.status == 200:
                try:
                    json_body = response.json()
                    tweets = extract_tweets_from_response(json_body)
                    for tweet in tweets:
                        all_tweets[tweet['id']] = tweet  # dedup by ID
                except Exception as e:
                    print(f"[!] Error decoding response: {e}")

        page.on("response", handle_response)

        print(f"[→] Navigating to: {query_url}")
        page.goto(query_url)
        page.wait_for_timeout(WAIT_BETWEEN_SCROLLS)

        prev_count = 0
        for i in range(SCROLL_LIMIT):
            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(WAIT_BETWEEN_SCROLLS)
            current_count = len(all_tweets)
            print(f"[↓] Scroll {i+1}: {current_count} tweets collected.")
            if current_count == prev_count:
                print("[✔] No new tweets loaded. Stopping scroll.")
                break
            prev_count = current_count

        browser.close()

    # Save tweets
    output_file = f"tweets_query_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(list(all_tweets.values()), f, indent=2, ensure_ascii=False)
    print(f"[✔] {len(all_tweets)} tweets saved to {output_file}")

    # Save metadata
    metadata = {
        "query": QUERY,
        "timestamp": timestamp,
        "query_url": query_url,
        "tweet_count": len(all_tweets),
        "scraper_version": "1.1"
    }
    with open(f"metadata_{timestamp}.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"[ℹ] Metadata saved.")

if __name__ == "__main__":
    main()

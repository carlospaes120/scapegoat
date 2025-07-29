from playwright.sync_api import sync_playwright
import json
import logging
from datetime import datetime
from urllib.parse import quote_plus
import os
import sys

# --- Configuration ---
SEARCH_TERM = 'Wagner Schwartz'
LANG = "pt"
SINCE_DATE = "2017-01-01"
UNTIL_DATE = "2017-12-31"

MAX_SCROLLS = 70        # Max scrolls before stopping, avoid infinite loops
SCROLL_WAIT_MS = 6000   # Wait 6 seconds after each scroll
INITIAL_WAIT_MS = 5000

COOKIES_FILE = "twitter_cookies.json"
OUTPUT_DIR = "data/raw"


def build_query(term, lang=None, since=None, until=None):
    parts = [term]
    if lang:
        parts.append(f"lang:{lang}")
    if since:
        parts.append(f"since:{since}")
    if until:
        parts.append(f"until:{until}")
    return " ".join(parts)


def get_filename_path(query):
    # Use a simplified query for filename to avoid very long names
    safe_query_for_filename = quote_plus(f"{SEARCH_TERM}_{SINCE_DATE}_{UNTIL_DATE}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(OUTPUT_DIR, f"search_response_{safe_query_for_filename}_{timestamp}.json")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    query = build_query(SEARCH_TERM, LANG, SINCE_DATE, UNTIL_DATE)
    query_url = f"https://twitter.com/search?q={quote_plus(query)}&src=typed_query&f=live"

    if not os.path.exists(COOKIES_FILE):
        logging.error(f"Cookies file '{COOKIES_FILE}' not found. Please provide it before running.")
        sys.exit(1)

    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load cookies from '{COOKIES_FILE}': {e}")
        sys.exit(1)

    filename_path = get_filename_path(query)
    logging.info(f"Output will be saved to: {filename_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        context.add_cookies(cookies)
        page = context.new_page()

        def handle_response(response):
            if "SearchTimeline" in response.url:
                logging.info(f"[✅ FOUND] {response.url}")
                try:
                    json_data = response.json()

                    item_count = 0 # Initialize item_count
                    if 'data' in json_data and \
                        'search_by_raw_query' in json_data['data'] and \
                        'search_timeline' in json_data['data']['search_by_raw_query'] and \
                        'timeline' in json_data['data']['search_by_raw_query']['search_timeline'] and \
                        'instructions' in json_data['data']['search_by_raw_query']['search_timeline']['timeline']:

                        for instruction in json_data['data']['search_by_raw_query']['search_timeline']['timeline']['instructions']:
                            if instruction.get('type') == 'TimelineAddEntries' and 'entries' in instruction:
                                for entry in instruction['entries']:
                                    # Check if the entry is a tweet (usually identified by 'tweet-' in entryId)
                                    if entry.get('entryId') and entry['entryId'].startswith('tweet-'):
                                        item_count += 1
                            elif instruction.get('type') == 'TimelineReplaceEntry':
                                # This handles the initial "TimelineReplaceEntry" responses that only set cursors
                                # and don't contain tweet data. We don't increment item_count for these.
                                pass


                    metadata = {
                        "query": query,
                        "timestamp": datetime.now().isoformat(),
                        "response_url": response.url,
                        "item_count": item_count,
                    }

                    output = {
                        "metadata": metadata,
                        "data": json_data # Keep the full JSON data for later parsing
                    }


                    with open(filename_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(output, indent=2, ensure_ascii=False) + ",\n") # Add a comma for valid JSON array later
                        # Or, if you want a file per response, change 'a' to 'w' and make filename_path unique inside handle_response

                    logging.info(f"[✔] Appended SearchTimeline response with {item_count} items to '{filename_path}'!")

                except Exception as e:
                    logging.error(f"[!] Failed to parse or save JSON: {e}")

            else:
                logging.debug(f"[...IGNORE] {response.url}")

        page.on("response", handle_response)

        logging.info(f"[🔍] Navigating to: {query_url}")
        page.goto(query_url)
        page.wait_for_timeout(INITIAL_WAIT_MS)

        logging.info("[🔄] Starting smart scrolling...")

        previous_height = 0
        scroll_count = 0

        while scroll_count < MAX_SCROLLS:
            current_height = page.evaluate("document.body.scrollHeight")
            if current_height == previous_height:
                logging.info("No new content loaded, stopping scroll.")
                break

            page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            logging.info(f"Scrolled {scroll_count + 1}/{MAX_SCROLLS}")
            page.wait_for_timeout(SCROLL_WAIT_MS)

            previous_height = current_height
            scroll_count += 1

        logging.info("[🚪] Done. Closing browser.")
        browser.close()


if __name__ == "__main__":
    main()
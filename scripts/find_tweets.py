from playwright.sync_api import sync_playwright
import json
import logging
from datetime import datetime
from urllib.parse import quote_plus
import os
import sys
import hashlib
from pathlib import Path
import re
import time
import random

# =========================
# Configuration
# =========================

# --- Entities/aliases to catch the target (lowercase is fine; X search is case-insensitive) ---
ENTITIES = [
    '"Karol Conká"',      # full name
    "KarolConka",         # variant without accent
    "@Karolconka",        # official handle
    '"Karol Conka'
]

# --- Stance/lynching related terms (Portuguese variants, accents, verbs/nouns) ---
TOPIC_TERMS = [
]

# --- Hard excludes; keep it lean (we already exclude Grok carefully) ---
EXCLUDES = [
    '-grok', '-Grok', '-#Grok',
    # add more if you see spammy mirrors
]

LANG = "pt"
SINCE_DATE = "2021-02-01"
UNTIL_DATE = "2021-02-26"

# UI/scroll
MAX_SCROLLS        = 60          # allow a bit more; we stop earlier if no growth
SCROLL_WAIT_MS     = 5000
INITIAL_WAIT_MS    = 5000
STABLE_ROUNDS_STOP = 3           # stop after N scrolls with zero new items

# Files
COOKIES_FILE = "twitter_cookies.json"
OUTPUT_DIR   = "../data/raw/karolconka"

# Browser flags
HEADLESS = False  # set to True for background runs


# =========================
# Query builder
# =========================

def build_query(entities, topic_terms, excludes=None, lang=None, since=None, until=None):
    """
    Build a robust X (Twitter) search query:
    ( (ent1 OR ent2 ...) (term1 OR term2 ...) ) lang:xx since:YYYY-MM-DD until:YYYY-MM-DD -exclude1 -exclude2 ...
    """
    ent_group   = "(" + " OR ".join(entities) + ")"
    topic_group = "(" + " OR ".join(topic_terms) + ")"

    parts = [ent_group, topic_group]

    if lang:
        parts.append(f"lang:{lang}")
    if since:
        parts.append(f"since:{since}")
    if until:
        parts.append(f"until:{until}")
    if excludes:
        parts.extend(excludes)

    return " ".join(parts)


def build_search_url(query, live_tab=True):
    """
    live_tab=True -> 'Latest' tab (more complete for timelines)
    live_tab=False -> 'Top' tab
    """
    base = "https://twitter.com/search"
    q = quote_plus(query)
    return f"{base}?q={q}&src=typed_query&f={'live' if live_tab else 'top'}"


# =========================
# Filename helper (short & safe)
# =========================

def make_output_path(query: str) -> str:
    """Short, safe filename: scapegoat_<timestamp>_<8-char-hash>.json"""
    h = hashlib.sha1(query.encode("utf-8")).hexdigest()[:8]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scapegoat_{ts}_{h}.json"
    return str(Path(OUTPUT_DIR) / filename)


# =========================
# JSON file helpers (valid array)
# =========================

class ArrayFileWriter:
    """
    Appends objects into a valid JSON array:
    - writes '[' on open, ']' on close
    - inserts commas between items correctly
    """
    def __init__(self, path: str):
        self.path = path
        self.count = 0
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("[\n")

    def append(self, obj):
        with open(self.path, "a", encoding="utf-8") as f:
            if self.count > 0:
                f.write(",\n")
            f.write(json.dumps(obj, ensure_ascii=False, indent=2))
            self.count += 1

    def close(self):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write("\n]\n")


# =========================
# Utilities
# =========================

def is_search_timeline_url(url: str) -> bool:
    """
    Match X GraphQL SearchTimeline calls *accurately*.
    Typical pattern contains .../i/api/graphql/<hash>/SearchTimeline
    """
    return re.search(r"/i/api/graphql/[^/]+/SearchTimeline(\?|$)", url) is not None


def safe_response_json(response):
    """
    response.json() sometimes fails on big payloads; fallback to .text() -> json.loads
    """
    try:
        return response.json()
    except Exception:
        try:
            txt = response.text()
            return json.loads(txt)
        except Exception:
            return None


# =========================
# Main
# =========================

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    query = build_query(ENTITIES, TOPIC_TERMS, EXCLUDES, LANG, SINCE_DATE, UNTIL_DATE)
    search_url = build_search_url(query, live_tab=True)
    out_path = make_output_path(query)
    logging.info(f"Query: {query}")
    logging.info(f"URL:   {search_url}")
    logging.info(f"Output file: {out_path}")

    # cookies
    if not os.path.exists(COOKIES_FILE):
        logging.error(f"Cookies file '{COOKIES_FILE}' not found. Provide it and retry.")
        sys.exit(1)
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load cookies from '{COOKIES_FILE}': {e}")
        sys.exit(1)

    writer = ArrayFileWriter(out_path)

    # Track seen tweet entry IDs to avoid duplicates
    seen_entry_ids = set()

    # State for smart stopping
    stable_rounds = 0
    last_seen_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context()
        context.add_cookies(cookies)
        page = context.new_page()

        def handle_response(response):
            # Only handle SearchTimeline GraphQL responses (accurate match)
            if not is_search_timeline_url(response.url):
                return

            payload = safe_response_json(response)
            if not payload:
                logging.warning("[!] SearchTimeline: empty/invalid JSON payload")
                return

            # Count entries & dedupe
            item_count = 0
            new_entry_ids = 0

            try:
                instructions = (
                    payload.get("data", {})
                          .get("search_by_raw_query", {})
                          .get("search_timeline", {})
                          .get("timeline", {})
                          .get("instructions", [])
                )

                for instr in instructions:
                    t = instr.get("type")
                    if t == "TimelineAddEntries" and "entries" in instr:
                        for entry in instr["entries"]:
                            entry_id = entry.get("entryId")
                            if not entry_id:
                                continue
                            # Tweets typically have entryId like 'tweet-<id>'
                            if entry_id.startswith("tweet-"):
                                item_count += 1
                                if entry_id not in seen_entry_ids:
                                    seen_entry_ids.add(entry_id)
                                    new_entry_ids += 1
                    # We ignore TimelineReplaceEntry except for debugging/cursors

            except Exception as e:
                logging.error(f"[!] Error parsing instructions: {e}")

            metadata = {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "response_url": response.url,
                "total_entries_in_response": item_count,
                "new_tweet_entries_added": new_entry_ids,
                "seen_total_unique_tweet_entries": len(seen_entry_ids),
            }

            output = {
                "metadata": metadata,
                "data": payload  # keep full JSON for later parsing
            }

            writer.append(output)

            logging.info(
                f"[✔ SearchTimeline] items:{item_count} new:{new_entry_ids} seen_total:{len(seen_entry_ids)}"
            )

        page.on("response", handle_response)

        logging.info(f"[🔍] Navigating to: {search_url}")
        page.goto(search_url)
        page.wait_for_timeout(INITIAL_WAIT_MS)

        # Scroll loop
        logging.info("[🔄] Starting smart scrolling…")
        for i in range(1, MAX_SCROLLS + 1):
            # Scroll to bottom
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # jittered wait to avoid bot heuristics a bit
            wait_ms = int(SCROLL_WAIT_MS * random.uniform(0.85, 1.15))
            page.wait_for_timeout(wait_ms)

            # Progress check
            current_seen = len(seen_entry_ids)
            gained = current_seen - last_seen_count
            logging.info(f"Scrolled {i}/{MAX_SCROLLS} — gained {gained} new tweets this round")

            if gained == 0:
                stable_rounds += 1
            else:
                stable_rounds = 0
                last_seen_count = current_seen

            if stable_rounds >= STABLE_ROUNDS_STOP:
                logging.info(f"No growth for {STABLE_ROUNDS_STOP} rounds. Stopping.")
                break

        logging.info("[🚪] Done. Closing browser.")
        browser.close()

    writer.close()
    logging.info(f"[✅] Saved valid JSON array to: {out_path}")


if __name__ == "__main__":
    main()

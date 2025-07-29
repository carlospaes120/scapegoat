from playwright.sync_api import sync_playwright
import json
from bs4 import BeautifulSoup

def load_cookies(context, path="twitter_cookies.json"):
    with open(path, "r") as f:
        cookies = json.load(f)
    context.add_cookies(cookies)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    load_cookies(context)
    
    page = context.new_page()
    page.goto("https://twitter.com/search?q=Wagner%20Schwartz%20lang%3Apt%20until%3A2017-12-31%20since%3A2017-01-01&src=typed_query&f=live")

    # Let the tweets load
    page.wait_for_timeout(5000)  # 5 seconds

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")

    print("=== TWEETS FOUND ===")
    for tweet in soup.select('article [data-testid="tweetText"]'):
        print("-" * 40)
        print(tweet.get_text())

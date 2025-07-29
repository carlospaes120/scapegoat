#esqueciaminhasenha!@#$%

from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    print(">>> Go login to Twitter manually. I'll save cookies after you close the browser.")
    page.goto("https://twitter.com/login")
    input(">>> Press Enter after login and Twitter homepage is loaded...")

    cookies = context.cookies()
    with open("twitter_cookies.json", "w") as f:
        json.dump(cookies, f)
    
    browser.close()
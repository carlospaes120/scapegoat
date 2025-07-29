from scripts.scraper import scrape_all

if __name__ == "__main__":
    df = scrape_all()
    print(f"Scraped {len(df)} tweets.")
"""
Crypto News Collector
-----------------------
Pulls recent articles from major crypto news outlets via their public RSS
feeds. This is the most reliable free source (no API key, no rate limits,
no scraping fragility) and is great for spotting trending narratives.
"""

import feedparser
import json

FEEDS = {
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed",
    "The Block": "https://www.theblock.co/rss.xml",
    "Bitcoin Magazine": "https://bitcoinmagazine.com/feed",
}


def collect(limit_per_feed: int = 15, company_name: str = None):
    articles = []
    
    if company_name:
        print(f"  -> targeted search for '{company_name}' in Google News")
        search_url = f"https://news.google.com/rss/search?q={company_name}+crypto&hl=en-US"
        try:
            feed = feedparser.parse(search_url)
            print(f"  -> fetched {len(feed.entries)} search results from Google News")
            for entry in feed.entries[:limit_per_feed * 3]:
                articles.append({
                    "source": "news_search",
                    "outlet": "Google News Search",
                    "title": entry.title,
                    "summary": getattr(entry, "summary", "")[:400],
                    "published": entry.get("published", ""),
                    "url": entry.link,
                    "tags": [t.term for t in entry.get("tags", [])] if entry.get("tags") else [],
                })
        except Exception as e:
            print(f"  [!] Failed to fetch news search for '{company_name}': {e}")
    else:
        for name, url in FEEDS.items():
            try:
                feed = feedparser.parse(url)
                print(f"  -> fetched {len(feed.entries)} from {name}")
                for entry in feed.entries[:limit_per_feed]:
                    articles.append({
                        "source": "news",
                        "outlet": name,
                        "title": entry.title,
                        "summary": getattr(entry, "summary", "")[:400],
                        "published": entry.get("published", ""),
                        "url": entry.link,
                        "tags": [t.term for t in entry.get("tags", [])] if entry.get("tags") else [],
                    })
            except Exception as e:
                print(f"  [!] Failed to fetch {name}: {e}")
    return articles


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", default=None)
    args = parser.parse_args()
    results = collect(company_name=args.company)
    out_path = "../data/news_articles.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nCollected {len(results)} news articles -> {out_path}")

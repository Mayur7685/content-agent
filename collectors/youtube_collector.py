"""
YouTube Collector
------------------
Two modes:
  1. RSS mode (default, no API key): pulls latest videos from known crypto
     channels via YouTube's public RSS feeds. RSS doesn't expose view counts,
     so engagement is approximated via title/description signal + recency.
  2. Data API mode (optional): if YOUTUBE_API_KEY env var is set, uses the
     official YouTube Data API v3 search + videos endpoints to get real
     view/like/comment counts for crypto-related queries. This is the
     recommended mode for genuine "high engagement" filtering.

Get a free YouTube Data API key: https://console.cloud.google.com/
(enable "YouTube Data API v3", free quota: 10,000 units/day)
"""

import os
import requests
import feedparser
import json
import re

# Known active crypto YouTube channels as of 2026 (channel_id, name)
CHANNELS = [
    ("UCqK_GSMbpiV8spgD3ZGloSw", "Coin Bureau"),
    ("UCRvqjQPSeaWn-uEx-w0XOIg", "Benjamin Cowen"),
    ("UCCatR7nWbYrkVXdxXb4cGXg", "Altcoin Daily"),
    ("UCnhdZlwVf6grxyKFbQm7TxA", "Lark Davis"),
    ("UCiUnrCUGCJTCC7KjuW493Ww", "The Modern Investor"),
    ("UCc4Rz_T9Sb1w5rqqo9pL1Og", "Sheldon Evans"),
]

SEARCH_QUERIES = [
    "bitcoin prediction 2026", "altcoin season", "crypto news today",
    "ethereum upgrade", "best crypto to buy", "memecoin",
    "solana ecosystem", "crypto AI projects", "web3 trends",
]

# Fallback sample data — used when both RSS and API fail
FALLBACK_SAMPLE = [
    {
        "source": "youtube_sample",
        "channel": "Coin Bureau",
        "title": "Bitcoin Just Did Something UNPRECEDENTED (What Happens Next)",
        "summary": "Analysis of Bitcoin's latest on-chain metrics and what they signal for the next market phase.",
        "url": "https://youtube.com/watch?v=sample1",
        "score": None,
    },
    {
        "source": "youtube_sample",
        "channel": "Altcoin Daily",
        "title": "Top 5 Altcoins That Will 10x (Not What You Think)",
        "summary": "Deep dive into undervalued altcoins with strong fundamentals and upcoming catalysts.",
        "url": "https://youtube.com/watch?v=sample2",
        "score": None,
    },
    {
        "source": "youtube_sample",
        "channel": "Benjamin Cowen",
        "title": "The Ethereum Merge Changed Everything. Here's the Data.",
        "summary": "Quantitative analysis of ETH's deflationary supply dynamics post-merge.",
        "url": "https://youtube.com/watch?v=sample3",
        "score": None,
    },
    {
        "source": "youtube_sample",
        "channel": "Crypto Research",
        "title": "I Asked 50 Crypto VCs What They're Buying. Their Answers Shocked Me.",
        "summary": "Interviews with venture capitalists on their 2026 crypto investment theses.",
        "url": "https://youtube.com/watch?v=sample4",
        "score": None,
    },
    {
        "source": "youtube_sample",
        "channel": "DeFi Explained",
        "title": "DeFi in 2026: The 3 Protocols Nobody Is Watching (Yet)",
        "summary": "Under-the-radar DeFi protocols with innovative tokenomics and real yield.",
        "url": "https://youtube.com/watch?v=sample5",
        "score": None,
    },
]


def get_interpolated_fallback(company_name):
    interpolated = []
    for item in FALLBACK_SAMPLE:
        new_item = item.copy()
        title = new_item.get("title", "")
        summary = new_item.get("summary", "")
        
        # Replace occurrences of Bitcoin, Ethereum, Solana, and DeFi
        title = re.sub(r"\b(Bitcoin|Ethereum|Solana|DeFi)\b", company_name, title, flags=re.IGNORECASE)
        summary = re.sub(r"\b(Bitcoin|Ethereum|Solana|DeFi)\b", company_name, summary, flags=re.IGNORECASE)
        
        new_item["title"] = title
        new_item["summary"] = summary
        new_item["source"] = "youtube_sample_interpolated"
        interpolated.append(new_item)
    return interpolated


def collect_via_rss(company_name=None):
    """Fallback: no API key needed, but no real engagement metrics."""
    videos = []
    for channel_id, name in CHANNELS:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                title = entry.title
                summary = getattr(entry, "summary", "")[:300]
                
                # If target company name is specified, filter strictly
                if company_name and not (
                    re.search(rf"\b{company_name}\b", title, re.I) or 
                    re.search(rf"\b{company_name}\b", summary, re.I)
                ):
                    continue
                    
                videos.append({
                    "source": "youtube_rss",
                    "channel": name,
                    "title": title,
                    "summary": summary,
                    "published": entry.get("published", ""),
                    "url": entry.link,
                    "score": None,  # not available via RSS
                })
        except Exception as e:
            print(f"  [!] Failed RSS for {name}: {e}")
    return videos


def collect_via_data_api(api_key: str, max_per_query: int = 8, company_name=None):
    """Preferred: real view/like/comment counts via YouTube Data API v3."""
    videos = []
    search_url = "https://www.googleapis.com/youtube/v3/search"
    videos_url = "https://www.googleapis.com/youtube/v3/videos"

    queries = SEARCH_QUERIES
    if company_name:
        queries = [
            f"{company_name} crypto",
            f"{company_name} protocol",
            f"{company_name} token"
        ]

    for query in queries:
        params = {
            "key": api_key, "q": query, "part": "id",
            "type": "video", "order": "viewCount",
            "maxResults": max_per_query, "publishedAfter": "2025-01-01T00:00:00Z",
        }
        try:
            r = requests.get(search_url, params=params, timeout=10)
            r.raise_for_status()
            ids = [item["id"]["videoId"] for item in r.json().get("items", [])]
            if not ids:
                continue

            stats_params = {"key": api_key, "id": ",".join(ids), "part": "snippet,statistics"}
            r2 = requests.get(videos_url, params=stats_params, timeout=10)
            r2.raise_for_status()
            for item in r2.json().get("items", []):
                snip = item["snippet"]
                stats = item["statistics"]
                videos.append({
                    "source": "youtube_api",
                    "query": query,
                    "title": snip.get("title", ""),
                    "description": snip.get("description", "")[:300],
                    "channel": snip.get("channelTitle", ""),
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "url": f"https://youtube.com/watch?v={item['id']}",
                })
        except Exception as e:
            print(f"  [!] Data API query '{query}' failed: {e}")

    videos.sort(key=lambda v: v.get("views", 0), reverse=True)
    return videos


def collect(company_name=None):
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if api_key:
        print("  -> using YouTube Data API (real engagement metrics)")
        videos = collect_via_data_api(api_key, company_name=company_name)
        if videos:
            return videos
        print("  [!] Data API returned nothing, falling back to RSS")

    if company_name:
        print(f"  -> targeted filtering for '{company_name}' in YouTube RSS feeds")
    else:
        print("  -> no YOUTUBE_API_KEY set, using RSS (no view counts)")
        
    videos = collect_via_rss(company_name=company_name)

    if not videos:
        print("  [!] RSS also returned nothing — using fallback sample data")
        fallback_data = get_interpolated_fallback(company_name) if company_name else FALLBACK_SAMPLE
        return fallback_data

    return videos


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", default=None)
    args = parser.parse_args()
    results = collect(company_name=args.company)
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "youtube_videos.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nCollected {len(results)} YouTube videos -> {out_path}")

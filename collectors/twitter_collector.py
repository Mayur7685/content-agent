"""
Twitter / X Collector (via twitterapi.io)
-------------------------------------------
Collects real high-engagement crypto tweets using the twitterapi.io REST API,
which provides full access to X search and user data with just an API key
(no OAuth, no official X developer portal needed).

Three collection strategies, run in sequence:

  1. ADVANCED SEARCH — queries like "bitcoin min_faves:500" to find viral tweets
  2. TRENDING TOPICS — fetches X's global trending topics for narrative detection
  3. KOL TWEETS — pulls recent tweets from known crypto influencers

Requires: TWITTERAPI_IO_KEY environment variable (get one at https://twitterapi.io/dashboard)
Cost: ~$0.15 per 1,000 tweets fetched — a full run costs under $0.05

If no API key is set, falls back to a curated sample dataset of realistic
viral tweet patterns (clearly labeled as `twitter_sample`).
"""

import os
import requests
import json
import time

# Load environment variables from .env if present in parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

BASE_URL = "https://api.twitterapi.io"

# Crypto search queries with engagement filters (X search operators)
SEARCH_QUERIES = [
    "bitcoin min_faves:500 -filter:replies",
    "ethereum min_faves:500 -filter:replies",
    "crypto min_faves:1000 -filter:replies",
    "memecoin min_faves:300 -filter:replies",
    "solana min_faves:300 -filter:replies",
    "altcoin min_faves:200 -filter:replies",
    "defi min_faves:200 -filter:replies",
    "web3 min_faves:200 -filter:replies",
]

# Known crypto KOLs (key opinion leaders) to pull recent viral tweets from
CRYPTO_KOLS = [
    "VitalikButerin",
    "caborek",        # Crypto Birb
    "inversebrah",
    "CryptoCobain",
    "lookonchain",
    "WatcherGuru",
    "CryptoCapo_",
    "ZssBecker",
]

# Static fallback — only used when NO API key is available
FALLBACK_SAMPLE = [
    {
        "source": "twitter_sample", "text": "I turned $500 into $40,000 in 3 weeks. Here's the exact memecoin strategy I used (thread)",
        "likes": 12400, "retweets": 3200, "replies": 890, "views": 980000,
        "pattern": "money_transformation_thread",
    },
    {
        "source": "twitter_sample", "text": "Everyone is missing this Bitcoin chart pattern. We've seen it exactly twice before in history.",
        "likes": 8900, "retweets": 2100, "replies": 540, "views": 650000,
        "pattern": "rare_pattern_authority",
    },
    {
        "source": "twitter_sample", "text": "I asked 10 crypto VCs what they're buying in 2026. Their answers shocked me.",
        "likes": 6700, "retweets": 1500, "replies": 410, "views": 420000,
        "pattern": "insider_access_curiosity",
    },
    {
        "source": "twitter_sample", "text": "Unpopular opinion: 90% of L2s will be dead by 2027. Here's why.",
        "likes": 15200, "retweets": 4100, "replies": 1900, "views": 1200000,
        "pattern": "contrarian_take",
    },
    {
        "source": "twitter_sample", "text": "I lost $80k on a rug pull. Here are the 5 red flags I ignored.",
        "likes": 22000, "retweets": 6800, "replies": 2300, "views": 1800000,
        "pattern": "loss_confessional_lessons",
    },
    {
        "source": "twitter_sample", "text": "BREAKING: SEC just filed something that changes everything for ETH ETFs.",
        "likes": 9800, "retweets": 3400, "replies": 670, "views": 780000,
        "pattern": "breaking_news_urgency",
    },
    {
        "source": "twitter_sample", "text": "The biggest crypto exchange in the world just quietly did this. Nobody's talking about it.",
        "likes": 7300, "retweets": 1900, "replies": 520, "views": 560000,
        "pattern": "secret_nobody_talking_about",
    },
]


def _get_headers():
    """Build auth headers for twitterapi.io."""
    api_key = os.environ.get("TWITTERAPI_IO_KEY", "")
    if not api_key:
        return None
    return {"x-api-key": api_key}


def _parse_tweet(tweet_data, source_label="twitter_live"):
    """Normalize a tweet object from twitterapi.io into our standard schema."""
    return {
        "source": source_label,
        "text": tweet_data.get("text", ""),
        "likes": tweet_data.get("likeCount", 0) or 0,
        "retweets": tweet_data.get("retweetCount", 0) or 0,
        "replies": tweet_data.get("replyCount", 0) or 0,
        "views": tweet_data.get("viewCount", 0) or 0,
        "author": tweet_data.get("author", {}).get("userName", ""),
        "url": tweet_data.get("url", ""),
        "created_at": tweet_data.get("createdAt", ""),
    }


def search_viral_tweets(headers, max_per_query=15, queries=None):
    """
    Strategy 1: Advanced search for high-engagement crypto tweets.
    Uses X's native search operators (min_faves, min_retweets) via
    twitterapi.io's /twitter/tweet/advanced_search endpoint.
    """
    all_tweets = []
    url = f"{BASE_URL}/twitter/tweet/advanced_search"

    target_queries = queries if queries else SEARCH_QUERIES

    for query in target_queries:
        try:
            params = {
                "query": query,
                "queryType": "Top",  # Sort by engagement, not recency
            }
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            tweets = data.get("tweets", [])
            for t in tweets[:max_per_query]:
                parsed = _parse_tweet(t, source_label="twitter_search")
                if parsed["text"]:
                    all_tweets.append(parsed)

            print(f"    [{query[:35]:35s}] -> {len(tweets)} tweets")
            time.sleep(0.3)  # Be polite to the API

        except requests.exceptions.RequestException as e:
            print(f"    [!] Search failed for '{query[:30]}': {e}")
        except Exception as e:
            print(f"    [!] Unexpected error for '{query[:30]}': {e}")

    return all_tweets


def fetch_kol_tweets(headers, max_per_kol=10):
    """
    Strategy 2: Pull recent tweets from known crypto influencers.
    Uses /twitter/user/last_tweets endpoint.
    """
    all_tweets = []
    url = f"{BASE_URL}/twitter/user/last_tweets"

    for kol in CRYPTO_KOLS:
        try:
            params = {"userName": kol}
            resp = requests.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Response is data-wrapped: r["data"]["tweets"]
            tweets_data = data.get("data", {}).get("tweets", [])
            if not tweets_data:
                # Some endpoints return flat
                tweets_data = data.get("tweets", [])

            count = 0
            for t in tweets_data[:max_per_kol]:
                parsed = _parse_tweet(t, source_label="twitter_kol")
                # Only include tweets with decent engagement
                if parsed["text"] and parsed["likes"] >= 50:
                    all_tweets.append(parsed)
                    count += 1

            print(f"    @{kol:20s} -> {count} high-engagement tweets")
            time.sleep(0.3)

        except requests.exceptions.RequestException as e:
            print(f"    [!] Failed to fetch @{kol}: {e}")
        except Exception as e:
            print(f"    [!] Unexpected error for @{kol}: {e}")

    return all_tweets


def fetch_trending_topics(headers):
    """
    Strategy 3: Fetch X's global trending topics.
    Uses /twitter/trends endpoint. These feed directly into narrative detection.
    """
    url = f"{BASE_URL}/twitter/trends"
    try:
        params = {"woeid": 1, "count": 30}  # 1 = worldwide
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Response is data-wrapped
        trends_data = data.get("data", data.get("trends", []))
        if isinstance(trends_data, dict):
            trends_data = trends_data.get("trends", [])

        trends = []
        for t in trends_data:
            name = t.get("name", "") if isinstance(t, dict) else str(t)
            if name:
                trends.append({
                    "source": "twitter_trends",
                    "text": name,
                    "tweet_volume": t.get("tweet_volume", 0) if isinstance(t, dict) else 0,
                })

        # Filter for crypto-related trends (loose matching)
        crypto_keywords = [
            "bitcoin", "btc", "ethereum", "eth", "crypto", "solana", "sol",
            "memecoin", "defi", "nft", "web3", "altcoin", "token", "chain",
            "binance", "coinbase", "sec", "etf", "airdrop", "whale",
        ]
        crypto_trends = [
            t for t in trends
            if any(kw in t["text"].lower() for kw in crypto_keywords)
        ]
        # If very few crypto-specific trends, include all (they still show narrative)
        if len(crypto_trends) < 5:
            crypto_trends = trends[:15]

        print(f"    Fetched {len(trends)} global trends ({len(crypto_trends)} crypto-related)")
        return crypto_trends

    except Exception as e:
        print(f"    [!] Failed to fetch trends: {e}")
        return []


def get_interpolated_fallback(company_name):
    interpolated = []
    import re
    for item in FALLBACK_SAMPLE:
        new_item = item.copy()
        text = new_item.get("text", "")
        # Replace occurrences of Bitcoin, ETH, L2s, and crypto
        text = re.sub(r"\b(Bitcoin|ETH|L2s|crypto)\b", company_name, text, flags=re.IGNORECASE)
        new_item["text"] = text
        new_item["source"] = "twitter_sample_interpolated"
        interpolated.append(new_item)
    return interpolated


def collect(company_name=None):
    """
    Main collection entry point. Tries twitterapi.io first, falls back
    to hardcoded samples if no API key is set.
    """
    headers = _get_headers()

    if headers is None:
        print("  [!] TWITTERAPI_IO_KEY not set.")
        print("  [!] To get REAL Twitter data, sign up at https://twitterapi.io/dashboard")
        print("      and set: export TWITTERAPI_IO_KEY=your_key_here")
        fallback_data = get_interpolated_fallback(company_name) if company_name else FALLBACK_SAMPLE
        print("  -> using curated fallback sample of known viral tweet patterns")
        return fallback_data

    print("  -> using twitterapi.io (real Twitter/X data)")
    all_data = []

    if company_name:
        print(f"\n  [Search] Querying targeted tweets for '{company_name}'...")
        # Targeted search queries with slightly lowered engagement thresholds to find niche tweets
        queries = [
            f"{company_name} min_faves:10 -filter:replies",
            f"{company_name} crypto min_faves:10 -filter:replies",
            f"{company_name} token min_faves:5 -filter:replies"
        ]
        search_tweets = search_viral_tweets(headers, max_per_query=20, queries=queries)
        all_data.extend(search_tweets)
        print(f"  [Search] Total: {len(search_tweets)} tweets")
    else:
        # Strategy 1: Search for viral tweets
        print("\n  [Search] Querying high-engagement crypto tweets...")
        search_tweets = search_viral_tweets(headers)
        all_data.extend(search_tweets)
        print(f"  [Search] Total: {len(search_tweets)} tweets")

        # Strategy 2: KOL tweets
        print("\n  [KOLs] Fetching recent tweets from crypto influencers...")
        kol_tweets = fetch_kol_tweets(headers)
        all_data.extend(kol_tweets)
        print(f"  [KOLs] Total: {len(kol_tweets)} tweets")

        # Strategy 3: Trending topics
        print("\n  [Trends] Fetching global trending topics...")
        trends = fetch_trending_topics(headers)
        all_data.extend(trends)
        print(f"  [Trends] Total: {len(trends)} topics")

    if not all_data:
        print("\n  [!] twitterapi.io returned no data — falling back to sample data")
        fallback_data = get_interpolated_fallback(company_name) if company_name else FALLBACK_SAMPLE
        return fallback_data

    # Sort by engagement (likes + retweets*2) — trends have no likes, put them at end
    all_data.sort(
        key=lambda t: t.get("likes", 0) + t.get("retweets", 0) * 2,
        reverse=True,
    )

    print(f"\n  => Collected {len(all_data)} total Twitter/X items")
    return all_data


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--company", default=None)
    args = parser.parse_args()
    results = collect(company_name=args.company)
    out_path = os.path.join(os.path.dirname(__file__), "..", "data", "twitter_posts.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nCollected {len(results)} tweets -> {out_path}")

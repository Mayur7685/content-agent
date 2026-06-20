"""
Collector Orchestrator
-------------------------
Runs all data collectors and saves a unified dataset.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

import reddit_collector
import youtube_collector
import news_collector
import twitter_collector

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def run_all(company_name=None):
    os.makedirs(DATA_DIR, exist_ok=True)
    unified = {}

    print("\n[1/4] Reddit...")
    unified["reddit"] = reddit_collector.collect(company_name=company_name)

    print("\n[2/4] YouTube...")
    unified["youtube"] = youtube_collector.collect(company_name=company_name)

    print("\n[3/4] News (RSS)...")
    unified["news"] = news_collector.collect(company_name=company_name)

    print("\n[4/4] Twitter / X...")
    unified["twitter"] = twitter_collector.collect(company_name=company_name)

    out_path = os.path.join(DATA_DIR, "unified_dataset.json")
    with open(out_path, "w") as f:
        json.dump(unified, f, indent=2)

    print("\n" + "=" * 50)
    for k, v in unified.items():
        print(f"  {k:10s}: {len(v)} items")
    print("=" * 50)
    print(f"Saved unified dataset -> {out_path}")
    return unified


if __name__ == "__main__":
    run_all()

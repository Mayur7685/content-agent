"""
Main Pipeline Runner
----------------------
Runs the full system end-to-end:
  1. Collect viral content (Reddit, YouTube, News, Twitter/X)
  2. Analyze patterns (hooks, topics, structures)
  3. Generate content ideas via local Ollama LLM

Usage:
    python3 main.py                  # full pipeline
    python3 main.py --skip-collect   # reuse existing data/unified_dataset.json
    python3 main.py --skip-generate  # stop after pattern analysis (no LLM needed)
"""

import argparse
import sys
import os

# Load environment variables from .env if present
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "collectors"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "analyzer"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "generator"))


def main():
    parser = argparse.ArgumentParser(description="Viral Crypto Content Idea Generator")
    parser.add_argument("--skip-collect", action="store_true", help="Reuse existing collected data")
    parser.add_argument("--skip-generate", action="store_true", help="Stop after pattern analysis")
    parser.add_argument("--model", default=None, help="Model name override (Ollama only; for LM Studio, load the model in-app)")
    parser.add_argument("--platforms", default=None, help="Comma-separated list of target platforms (instagram, tiktok, shorts, youtube, twitter)")
    parser.add_argument("--company", default=None, help="Target a specific crypto company or ecosystem (e.g. Uniswap, Solana)")
    args = parser.parse_args()

    if args.model:
        os.environ["OLLAMA_MODEL"] = args.model

    print("\n" + "#" * 60)
    print("# VIRAL CRYPTO CONTENT IDEA GENERATOR")
    print("#" * 60)

    if not args.skip_collect:
        print("\n### STEP 1: Collecting viral content data ###")
        import run_collectors
        run_collectors.run_all(company_name=args.company)
    else:
        print("\n### STEP 1: Skipped (using existing data) ###")

    print("\n### STEP 2: Analyzing patterns ###")
    import pattern_analyzer
    data = pattern_analyzer.load_unified()
    report = pattern_analyzer.analyze(data)
    pattern_analyzer.print_report(report)

    out_path = os.path.join(os.path.dirname(__file__), "data", "pattern_report.json")
    import json
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    if args.skip_generate:
        print("\n### STEP 3: Skipped ###")
        print("\nDone. Pattern report saved. Run idea_generator.py separately once Ollama is ready.")
        return

    print("\n### STEP 3: Generating content ideas (Ollama/LM Studio) ###")
    import idea_generator
    ideas = idea_generator.main(platforms=args.platforms, company_name=args.company)

    if ideas:
        print("\n### STEP 4: Publishing to Notion Content Database ###")
        import notion_publisher
        notion_publisher.publish_to_notion(ideas)

    print("\n✅ Pipeline complete. Check the output/ folder for results.")


if __name__ == "__main__":
    main()

"""
Pattern Analyzer
------------------
Takes the unified dataset (Reddit, YouTube, News, Twitter) and extracts:

  1. Viral hook patterns (opening-line structures that drive engagement)
  2. Popular topics (keyword frequency, weighted by engagement)
  3. Common storytelling structures (e.g. loss-confessional, contrarian take,
     "X vs Y" comparison, breaking news, insider access)
  4. Trending narratives (clusters of related high-engagement content)

This uses lightweight rule-based NLP (regex + keyword frequency) rather than
a heavy NLP model, since the goal is fast, transparent, explainable pattern
extraction that feeds directly into LLM prompts in the next stage.
"""

import json
import re
import os
from collections import Counter

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Hook pattern templates: (regex, label)
# These detect common viral content openings and structures
HOOK_PATTERNS = [
    # Money & personal finance hooks
    (r"\bi (lost|turned|made|spent|invested|blew)\b", "personal_money_story"),
    (r"\b\$\d+[kKmM]?\b.*\b(into|to|in)\b.*\b\$\d+", "money_transformation"),
    (r"\b(made|earned|lost)\s+\$\d+", "specific_dollar_amount"),

    # Contrarian & opinion hooks
    (r"\bunpopular opinion\b", "contrarian_take"),
    (r"\bcontroversial take\b", "contrarian_take"),
    (r"\b(hot take|bold claim)\b", "contrarian_take"),
    (r"\bmost people (don't|won't|can't)\b", "contrarian_take"),

    # FOMO & secrecy hooks
    (r"\b(everyone|nobody)('s| is) (missing|ignoring|sleeping on)\b", "fomo_secret"),
    (r"\bnobody('s| is) talking about\b", "secret_alpha"),
    (r"\bno one('s| is) (talking|paying attention)\b", "secret_alpha"),
    (r"\bslept on\b", "fomo_secret"),
    (r"\bunder the radar\b", "fomo_secret"),

    # Breaking news & urgency
    (r"^breaking\b", "breaking_news"),
    (r"\bjust (announced|happened|dropped|filed|released)\b", "breaking_news"),
    (r"\bthis just in\b", "breaking_news"),

    # Insider access & authority
    (r"\bi asked\b.*\b(experts?|vcs?|traders?|ceos?|founders?)\b", "insider_access"),
    (r"\b(insider|behind the scenes|exclusive)\b", "insider_access"),
    (r"\baccording to\b", "authority_citation"),

    # Lessons & warnings
    (r"\b(red flags?|mistakes?|lessons?|warning signs?)\b", "loss_lessons"),
    (r"\b(rug pull|scam|hack|exploit)\b", "security_warning"),
    (r"\b(don't|never) (buy|invest|trade)\b", "cautionary_advice"),

    # Prediction & analysis hooks
    (r"^(why|how) .*(will|won't|never|always)\b", "bold_prediction"),
    (r"\b(prediction|forecast|outlook)\b.*\b(20\d{2})\b", "dated_prediction"),
    (r"\bprice target\b", "price_prediction"),

    # Stat & number shock
    (r"\d+%\b", "stat_shock"),
    (r"\b\d+x\b", "multiplier_claim"),
    (r"\b(million|billion|trillion)\b", "big_number"),

    # Comparison & versus
    (r"\bvs\.?\b", "comparison"),
    (r"\bcompared to\b", "comparison"),
    (r"\bbetter than\b", "comparison"),

    # List & thread hooks
    (r"\b(top \d+|here are \d+|\d+ (things|reasons|ways))\b", "listicle"),
    (r"\b(thread|🧵)\b", "thread_hook"),
    (r"\bstep.by.step\b", "tutorial"),

    # AI + Crypto (2026 trend)
    (r"\b(ai|artificial intelligence)\b.*\b(crypto|blockchain|web3|token)\b", "ai_crypto"),
    (r"\b(crypto|blockchain|web3)\b.*\b(ai|artificial intelligence)\b", "ai_crypto"),
]

# Crypto topics with word-boundary matching to avoid false positives
CRYPTO_TOPICS = [
    (r"\bbitcoin\b", "bitcoin"),
    (r"\bbtc\b", "bitcoin"),
    (r"\bethereum\b", "ethereum"),
    (r"\beth\b", "ethereum"),
    (r"\bsolana\b", "solana"),
    (r"\bsol\b", "solana"),
    (r"\bmemecoin\b", "memecoin"),
    (r"\bmeme coin\b", "memecoin"),
    (r"\baltcoin\b", "altcoin"),
    (r"\balt coin\b", "altcoin"),
    (r"\bdefi\b", "defi"),
    (r"\bnfts?\b", "nft"),
    (r"\betfs?\b", "etf"),
    (r"\bairdrops?\b", "airdrop"),
    (r"\blayer.?2\b", "layer2"),
    (r"\bl2s?\b", "layer2"),
    (r"\bstablecoins?\b", "stablecoin"),
    (r"\brug pulls?\b", "rug_pull"),
    (r"\bstaking\b", "staking"),
    (r"\brestaking\b", "restaking"),
    (r"\bmining\b", "mining"),
    (r"\bhalving\b", "halving"),
    (r"\bregulation\b", "regulation"),
    (r"\bsec\b", "sec"),
    (r"\bweb3\b", "web3"),
    (r"\bdaos?\b", "dao"),
    (r"\byield farming\b", "yield_farming"),
    (r"\bleverage\b", "leverage"),
    (r"\bliquidation\b", "liquidation"),
    (r"\bwhales?\b", "whale"),
    (r"\bai crypto\b", "ai_crypto"),
    (r"\brwa\b", "rwa"),
    (r"\btokenization\b", "tokenization"),
    (r"\bcbdc\b", "cbdc"),
    (r"\brollups?\b", "rollup"),
    (r"\bbullish\b", "bullish_sentiment"),
    (r"\bbearish\b", "bearish_sentiment"),
]

STOPWORDS = set("""
the a an and or but is are was were be been being to of in on for with as
at by from this that these those it its it's i you we they he she his her
their our your my will would could should can may might has have had do
does did not no nor so if then than too very just about into out up down
what how why when where which who whom all each every some any many much
more most other another such like also back only own same even new now
https http www com org net html href rel nofollow noopener target blank
get set use via per let after still over
""".split())


def strip_html(text):
    """Remove HTML tags from text (RSS summaries often contain HTML)."""
    return re.sub(r'<[^>]+>', ' ', text)


def load_unified():
    path = os.path.join(DATA_DIR, "unified_dataset.json")
    with open(path) as f:
        return json.load(f)


def get_text_and_score(item, source):
    """Normalize text + engagement score across different source schemas."""
    if source == "reddit":
        text = item.get("title", "") + " " + item.get("selftext", "")
        score = item.get("score", 0) + item.get("num_comments", 0) * 2
    elif source in ("youtube",):
        text = item.get("title", "") + " " + item.get("description", item.get("summary", ""))
        score = item.get("views", 0) // 100 + item.get("likes", 0)
    elif source == "news":
        text = item.get("title", "") + " " + strip_html(item.get("summary", ""))
        tags = item.get("tags", [])
        # News has no native engagement; boost if it has tags (editorial signal)
        score = 5 + len(tags) * 2
    elif source == "twitter":
        text = item.get("text", "")
        score = (
            item.get("likes", 0)
            + item.get("retweets", 0) * 2
            + item.get("views", 0) // 500
        )
    else:
        text, score = "", 0
    return text.strip(), max(score, 0)


def detect_hooks(text):
    text_lower = text.lower()
    matched = []
    seen_labels = set()
    for pattern, label in HOOK_PATTERNS:
        if label not in seen_labels and re.search(pattern, text_lower):
            matched.append(label)
            seen_labels.add(label)
    return matched


def extract_topics(text):
    text_lower = text.lower()
    found = []
    seen = set()
    for pattern, topic_name in CRYPTO_TOPICS:
        if topic_name not in seen and re.search(pattern, text_lower):
            found.append(topic_name)
            seen.add(topic_name)
    return found


def keyword_frequency(texts, top_n=25):
    counter = Counter()
    for text in texts:
        words = re.findall(r"[a-zA-Z']{3,}", text.lower())
        for w in words:
            if w not in STOPWORDS:
                counter[w] += 1
    return counter.most_common(top_n)


def detect_storytelling_structure(text, hooks):
    """Classify the storytelling structure based on detected hooks."""
    structures = []
    hook_set = set(hooks)

    if hook_set & {"personal_money_story", "money_transformation", "specific_dollar_amount"}:
        structures.append("personal_narrative")
    if hook_set & {"loss_lessons", "security_warning", "cautionary_advice"}:
        structures.append("cautionary_tale")
    if hook_set & {"contrarian_take"}:
        structures.append("contrarian_argument")
    if hook_set & {"breaking_news"}:
        structures.append("news_commentary")
    if hook_set & {"insider_access", "authority_citation"}:
        structures.append("expert_insight")
    if hook_set & {"listicle", "tutorial"}:
        structures.append("educational_list")
    if hook_set & {"comparison"}:
        structures.append("versus_comparison")
    if hook_set & {"thread_hook"}:
        structures.append("deep_dive_thread")
    if hook_set & {"bold_prediction", "price_prediction", "dated_prediction"}:
        structures.append("prediction_thesis")

    return structures if structures else ["general"]


def analyze(unified_data):
    hook_counter = Counter()
    topic_counter = Counter()
    topic_engagement = Counter()  # Engagement-weighted topic scores
    structure_counter = Counter()
    high_engagement_items = []
    all_texts = []

    # Count how many real live items (not samples) are in the dataset
    num_live_items = 0
    for source, items in unified_data.items():
        for item in items:
            if "sample" not in item.get("source", ""):
                num_live_items += 1

    # Filter out fallback samples if there is at least some real live data
    filter_samples = num_live_items > 0
    if filter_samples:
        print(f"  [INFO] Real live data detected ({num_live_items} items). Filtering out mock fallback samples to prevent narrative dilution.")

    for source, items in unified_data.items():
        for item in items:
            item_source = item.get("source", "")
            if filter_samples and "sample" in item_source:
                continue

            text, score = get_text_and_score(item, source)
            if not text:
                continue
            all_texts.append(text)

            hooks = detect_hooks(text)
            topics = extract_topics(text)
            structures = detect_storytelling_structure(text, hooks)

            for h in hooks:
                hook_counter[h] += 1
            for t in topics:
                topic_counter[t] += 1
                topic_engagement[t] += score  # Weight by engagement
            for s in structures:
                structure_counter[s] += 1

            high_engagement_items.append({
                "source": source,
                "text": text[:200],
                "score": score,
                "hooks": hooks,
                "topics": topics,
                "structures": structures,
            })

    # Sort by engagement score to surface the best examples
    high_engagement_items.sort(key=lambda x: x["score"], reverse=True)

    # Compute engagement-weighted topic ranking
    # (frequency * avg_engagement gives a better signal than frequency alone)
    weighted_topics = []
    for topic, freq in topic_counter.most_common(20):
        avg_eng = topic_engagement[topic] / freq if freq > 0 else 0
        weighted_topics.append({
            "topic": topic,
            "frequency": freq,
            "total_engagement": topic_engagement[topic],
            "avg_engagement": round(avg_eng, 1),
        })
    weighted_topics.sort(key=lambda x: x["total_engagement"], reverse=True)

    report = {
        "total_items_analyzed": len(all_texts),
        "top_hook_patterns": hook_counter.most_common(15),
        "top_topics": topic_counter.most_common(15),
        "weighted_topics": weighted_topics[:15],
        "storytelling_structures": structure_counter.most_common(10),
        "top_keywords": keyword_frequency(all_texts),
        "top_20_examples": high_engagement_items[:20],
    }
    return report


def print_report(report):
    print("\n" + "=" * 60)
    print("PATTERN ANALYSIS REPORT")
    print("=" * 60)
    print(f"\nTotal items analyzed: {report['total_items_analyzed']}")

    print("\n--- Top Viral Hook Patterns ---")
    for label, count in report["top_hook_patterns"]:
        print(f"  {label:30s} x{count}")

    print("\n--- Top Crypto Topics (by frequency) ---")
    for topic, count in report["top_topics"]:
        print(f"  {topic:20s} x{count}")

    if report.get("weighted_topics"):
        print("\n--- Top Topics (engagement-weighted) ---")
        for t in report["weighted_topics"][:10]:
            print(f"  {t['topic']:20s} freq={t['frequency']:3d}  "
                  f"total_eng={t['total_engagement']:>8}  avg_eng={t['avg_engagement']:>8.1f}")

    if report.get("storytelling_structures"):
        print("\n--- Storytelling Structures ---")
        for struct, count in report["storytelling_structures"]:
            print(f"  {struct:25s} x{count}")

    print("\n--- Top Keywords ---")
    kw_line = ", ".join(f"{w}({c})" for w, c in report["top_keywords"][:15])
    print(f"  {kw_line}")

    print("\n--- Top 5 Highest-Engagement Examples ---")
    for ex in report["top_20_examples"][:5]:
        print(f"  [{ex['source']:15s} score={ex['score']:>8}] {ex['text'][:90]}")
    print("=" * 60)


if __name__ == "__main__":
    data = load_unified()
    report = analyze(data)
    print_report(report)

    out_path = os.path.join(DATA_DIR, "pattern_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nSaved -> {out_path}")

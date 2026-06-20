# Testing Guide — Targeted Intelligence Pipeline

This guide is designed for **Evaluators, Judges, and HR** to quickly set up, run, and verify the **Targeted Intelligence Pipeline** on their local machines.

The pipeline is built with **zero external paid service requirements** and degrades gracefully to mock samples if no API keys are provided.

---

## 🛠️ Step 1: Prerequisites

1. **Python 3.8+**: Ensure Python is installed. Check via `python3 --version`.
2. **Local LLM Server (LM Studio)**:
   - Download from [lmstudio.ai](https://lmstudio.ai).
   - Search & load **google/gemma-4-12b** (or **Qwen 2.5 7B/14B Instruct** Q4).
   - Go to the **Local Server** tab (`<->` icon in left sidebar).
   - **IMPORTANT**: Under **Hardware Settings** → increase **Context Length** from 2048 → **8192** (prevents truncation).
   - Click **Start Server** (runs on port `1234`).

---

## 🔑 Step 2: Environment Configuration (`.env`)

Create a `.env` file in the project root. Two modes available:

### Mode A: Zero-Key Dry Run (Fastest for evaluators)
No API accounts needed. The system uses **Tier-3 Fallback Engine** to interpolate your target into mock data:
```env
# No API keys required — mock fallbacks activate automatically
```

### Mode B: Full Production Run
Populate variables to query live APIs and enable Notion publishing:
```env
# Optional — Reddit data via OAuth API (Tier 1)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here

# Optional — YouTube Data API v3 (enables view counts)
YOUTUBE_API_KEY=your_google_youtube_api_key_here

# Optional — Twitter/X real-time data via twitterapi.io
TWITTERAPI_IO_KEY=your_twitterapi_io_key_here

# Optional — Notion automated publishing
NOTION_TOKEN=secret_your_notion_token_here
NOTION_DATABASE_ID=your_notion_database_id_here
```

---

## ⚙️ Step 3: Install & Activate

```bash
python3 -m venv venv
source venv/bin/activate          # macOS/Linux
# .\venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

---

## 🗂️ CLI Endpoint Reference

All commands use `python3 main.py` (or `./venv/bin/python3 main.py` with the venv active).

### Flags Overview

| Flag | Type | Description |
|------|------|-------------|
| `--company <name>` | Optional string | Target a specific company or protocol (e.g. `Uniswap`, `Solana`, `Ethena`). Omit for general trend mode. |
| `--platforms <list>` | Optional CSV | Comma-separated platforms: `instagram`, `tiktok`, `shorts`, `youtube`, `twitter`. Defaults to **all 5** if omitted. |
| `--skip-collect` | Flag | Skip live scraping; reuse existing `data/unified_dataset.json`. |
| `--skip-generate` | Flag | Stop after pattern analysis. No LLM required. |
| `--model <name>` | Optional string | Override the Ollama model name (e.g. `llama3.1`). For LM Studio, load the model in-app. |

---

## 🧪 Test Scenarios — All Endpoints & Combinations

### ─── GROUP A: General Trend Discovery Mode (No `--company`) ───

#### A1 — General + Analysis Only (No LLM)
Scrape live data, analyze patterns, skip LLM generation. **Best for verifying collectors work without needing LM Studio.**
```bash
python3 main.py --skip-generate
```
**Expected output:**
- `### STEP 1: Collecting viral content data ###` → shows Reddit/YouTube/News/Twitter fetch logs
- `PATTERN ANALYSIS REPORT` → prints top hooks, topics, keywords
- `### STEP 3: Skipped ###`
- Saves `data/pattern_report.json`
✅ **Tested & Verified**

---

#### A2 — General + Single Platform: YouTube Shorts
```bash
python3 main.py --skip-collect --platforms shorts
```
**Expected output:**
- Step 1 skipped (reuses existing data)
- Runs pattern analysis
- Generates 3 YouTube Shorts templates (title, topic, loop_hook_strategy, 3 scenes)
- Saves `output/content_ideas.json` + `output/history/content_ideas_general_{timestamp}.json`
✅ **Tested & Verified**

---

#### A3 — General + Single Platform: Twitter Threads
```bash
python3 main.py --skip-collect --platforms twitter
```
**Expected output:**
- Generates 3 Twitter Thread templates (thread_hook, tweets array, visual_asset_prompt)
- Archive: `output/history/content_ideas_general_{timestamp}.json`
✅ **Tested & Verified**

---

#### A4 — General + Multiple Platforms: Shorts + Twitter
```bash
python3 main.py --platforms shorts,twitter
```
**Expected output:**
- Step 1: Live scrapes Reddit RSS, YouTube RSS channels, CoinDesk/Cointelegraph/Decrypt/The Block/Bitcoin Magazine RSS, Twitter API
- Step 2: Pattern report across all collected data
- Step 3: Sequential generation — first Shorts (3 items), then Twitter (3 items)
- Archive: `output/history/content_ideas_general_{timestamp}.json`
✅ **Tested & Verified**

---

#### A5 — General + All 5 Platforms (Default)
Generates the full 5-platform content suite in one run.
```bash
python3 main.py --skip-collect
```
**Expected output:**
- Sequentially generates: instagram_reels, tiktok_videos, youtube_shorts, youtube_videos, twitter_threads
- All 15 ideas (3 per platform) saved to `output/content_ideas.json`
- Archive: `output/history/content_ideas_general_{timestamp}.json`

---

#### A6 — General + Single Platform: Instagram Reels
```bash
python3 main.py --skip-collect --platforms instagram
```
**Expected output:**
- Generates 3 Instagram Reel templates with: `title`, `hook`, `topic`, `angle`, `visual_style_guidelines`, `scene_by_scene_script` (3 scenes each)
- Each scene contains: `visual`, `on_screen_text`, `voiceover`
- Archive: `output/history/content_ideas_general_{timestamp}.json`
✅ **Tested & Verified** — Generated: *The Memecoin Blueprint*, *Rug Pull Red Flags*, *The ETF Revolution*

---

#### A7 — General + Single Platform: TikTok
```bash
python3 main.py --skip-collect --platforms tiktok
```
**Expected output:**
- Generates 3 TikTok Video templates with: `title`, `hook`, `topic`, `angle`, `sound_and_music_prompt`, `scene_by_scene_script` (3 scenes)
- Each scene contains: `visual`, `on_screen_text`, `voiceover`
- Archive: `output/history/content_ideas_general_{timestamp}.json`
✅ **Tested & Verified** — Generated: *Memecoin Moonshot Strategy*, *Rug Pull Survival Guide*, *The Bitcoin ETF Multiplier*

---

#### A8 — General + Single Platform: YouTube Long-form
```bash
python3 main.py --skip-collect --platforms youtube
```
**Expected output:**
- Generates 3 YouTube Video concepts with: `title_suggestions` (3 options), `thumbnail_concept`, `hook_script`, `topic`, `angle_thesis`, `chapters` (3 timestamped chapters with `core_points` and `b_roll_and_visuals`)
- Archive: `output/history/content_ideas_general_{timestamp}.json`
✅ **Tested & Verified** — Generated: *I Lost $80k on a Rug Pull*, *Why 90% of L2s Will Be Dead by 2027*, *How I Turned $500 into $40,000*

---

### ─── GROUP B: Targeted Intelligence Mode (`--company`) ───

#### B1 — Targeted + Analysis Only (No LLM)
Scrape targeted data for a specific company, analyze patterns, skip generation.
```bash
python3 main.py --company Uniswap --skip-generate
```
**Expected output:**
- Reddit uses search RSS/OAuth targeting "Uniswap"
- Google News RSS searches "Uniswap crypto"
- Twitter searches for "Uniswap" tweets
- Pattern report reflects Uniswap-specific data
✅ **Tested & Verified**

---

#### B2 — Targeted + Shorts (Fast Debug Run, Skip Collection)
```bash
python3 main.py --skip-collect --company Ethena --platforms shorts
```
**Expected output:**
- `--- Starting Multi-Agent Debate for ETHENA ---`
- `[Agent 1/3] Bull Agent: Analyzing positives...`
- `[Agent 2/3] Bear Agent: Analyzing risks...`
- `[Agent 3/3] Editor Agent: Synthesizing balanced consensus...`
- Generates 3 Ethena-focused YouTube Shorts
- Archive: `output/history/content_ideas_ethena_{timestamp}.json`
✅ **Tested & Verified**

---

#### B3 — Targeted + Twitter (Full Live Run)
```bash
python3 main.py --company Solana --platforms twitter
```
**Expected output:**
- Scrapes Solana-targeted content from all 4 sources
- Runs Multi-Agent Debate for Solana
- Generates 3 Solana-focused Twitter Threads
- Archive: `output/history/content_ideas_solana_{timestamp}.json`
✅ **Tested & Verified**

---

#### B4 — Targeted + Multi-Platform: Twitter + Instagram
```bash
python3 main.py --skip-collect --company Solana --platforms twitter,instagram
```
**Expected output:**
- Debate loop runs once for Solana context
- Sequential: Twitter threads (3) → Instagram Reels (3)
- Archive: `output/history/content_ideas_solana_{timestamp}.json`

---

#### B5 — Targeted + All Platforms (Full Suite)
```bash
python3 main.py --skip-collect --company Uniswap --platforms instagram,tiktok,shorts,youtube,twitter
```
**Expected output:**
- Full Uniswap-focused 5-platform suite (15 ideas total)
- Each platform schema strictly focuses on Uniswap token, protocol, and roadmap
- Notion sync attempted (prints setup instructions if no token set)

---

#### B6 — Targeted + Ethena (Ecosystem example)
```bash
python3 main.py --company Ethena --platforms shorts,twitter
```
**Expected output:**
- Ethena-specific data scrape
- Multi-Agent Debate (Bull: USDe yield, Bear: depeg risk, Editor: balanced)
- 6 ideas: 3 Shorts + 3 Twitter threads about Ethena

---

#### B7 — Different Company: Arbitrum
```bash
python3 main.py --skip-collect --company Arbitrum --platforms youtube,twitter
```
**Expected output:**
- Collector fallbacks interpolate "Arbitrum" into mock data
- Debate loop synthesizes Arbitrum-specific context
- Generates YouTube long-form + Twitter threads all focused on Arbitrum

---

### ─── GROUP C: Skip Flags ───

#### C1 — Skip Collection (Reuse Existing Data)
Fastest way to re-run generation without scraping again:
```bash
python3 main.py --skip-collect --platforms shorts
```
**Expected output:**
- `### STEP 1: Skipped (using existing data) ###`
- Loads `data/unified_dataset.json` from previous run
✅ **Tested & Verified**

---

#### C2 — Skip Generation (Analysis Only, No LLM)
Useful to verify collectors are working, without needing LM Studio running:
```bash
python3 main.py --skip-generate
```
**Expected output:**
- `### STEP 3: Skipped ###`
- Saves `data/pattern_report.json`
✅ **Tested & Verified**

---

#### C3 — Targeted + Skip Collection + Skip Generation
Zero LLM — fastest targeted scrape test:
```bash
python3 main.py --company Solana --skip-generate
```
**Expected output:**
- Scrapes Solana-specific content from all 4 sources using search mode
- Prints Solana-enriched pattern report
- No LLM called
✅ **Tested & Verified**

---

#### C4 — Skip Collection AND Generation (Absolute Fastest Test)
**No scraping, no LLM** — just analyzes existing cached data. Runs in ~3 seconds:
```bash
python3 main.py --skip-collect --skip-generate
```
**Expected output:**
- `### STEP 1: Skipped (using existing data) ###`
- Full `PATTERN ANALYSIS REPORT` from cached data
- `### STEP 3: Skipped ###`
- Saves updated `data/pattern_report.json`
✅ **Tested & Verified** — Completes in under 3 seconds. Perfect for environment validation.

---

### ─── GROUP D: Platform Combinations Matrix ───

| Command | JSON Key Output | Content Fields | Status |
|---------|----------------|----------------|--------|
| `--platforms instagram` | `instagram_reels` | title, hook, visual_style_guidelines, scene_by_scene_script (3 scenes) | ✅ Verified |
| `--platforms tiktok` | `tiktok_videos` | title, hook, sound_and_music_prompt, scene_by_scene_script (3 scenes) | ✅ Verified |
| `--platforms shorts` | `youtube_shorts` | title, loop_hook_strategy, scene_by_scene_script (3 scenes) | ✅ Verified |
| `--platforms youtube` | `youtube_videos` | title_suggestions, thumbnail_concept, hook_script, chapters (timestamped) | ✅ Verified |
| `--platforms twitter` | `twitter_threads` | thread_hook, tweets[], visual_asset_prompts | ✅ Verified |
| `--platforms instagram,tiktok` | instagram_reels + tiktok_videos | Sequential, 6 ideas total | ✅ Verified |
| `--platforms shorts,twitter` | youtube_shorts + twitter_threads | Sequential, 6 ideas total | ✅ Verified |
| `--platforms instagram,tiktok,shorts,youtube,twitter` | All 5 keys | Full suite, 15 ideas | |
| *(no `--platforms` flag)* | All 5 keys | Same as above — defaults to all 5 | |

---

### ─── GROUP E: Notion Publishing ───

#### E1 — Notion Sync Skipped (No credentials set)
```bash
python3 main.py --skip-collect --platforms shorts
```
**Expected Notion console block:**
```
NOTION AUTOMATED PUBLICATION SYNC
[INFO] Notion sync is currently skipped because credentials are not set.
To enable Notion auto-publishing, perform the following steps:
  1. Create a Notion integration: https://www.notion.so/my-integrations
  2. Add your integration secret key and database ID to your .env file:
     NOTION_TOKEN=secret_your_token_here
     NOTION_DATABASE_ID=your_database_id_here
  3. Make sure to share your Notion database with the integration.
```
✅ **Tested & Verified** — prints graceful setup instructions

---

#### E2 — Notion Sync Active (With credentials)
Set in `.env`:
```env
NOTION_TOKEN=secret_your_token_here
NOTION_DATABASE_ID=your_database_id_here
```
Then run any generation command, e.g.:
```bash
python3 main.py --skip-collect --company Ethena --platforms shorts
```
**Expected Notion console block:**
```
NOTION AUTOMATED PUBLICATION SYNC
  -> Connection detected: Syncing templates to Notion...
    -> Successfully published 'Why ETHENA is the Yield King' [YouTube Shorts]
    -> Successfully published '...' [YouTube Shorts]
    -> Successfully published '...' [YouTube Shorts]
  => Sync Complete: 3 published, 0 failed.
```

---

## 🔍 Step 4: Verification Checklist

### ✅ 1. Collector Output (after any run without `--skip-collect`)
Check `data/unified_dataset.json` exists and contains keys: `reddit`, `youtube`, `news`, `twitter`
```bash
python3 -c "import json; d=json.load(open('data/unified_dataset.json')); print({k:len(v) for k,v in d.items()})"
```

### ✅ 2. Pattern Report
Check `data/pattern_report.json` after any Step 2 run:
```bash
python3 -c "import json; d=json.load(open('data/pattern_report.json')); print(list(d.keys()))"
```
**Expected keys:** `top_hook_patterns`, `top_topics`, `top_keywords`, `weighted_topics`, `storytelling_structures`, `top_20_examples`

### ✅ 3. Multi-Agent Debate (Targeted runs only)
Terminal output must show all three agent steps:
- `[Agent 1/3] Bull Agent: Analyzing positives and growth thesis...`
- `[Agent 2/3] Bear Agent: Analyzing risks and critique points...`
- `[Agent 3/3] Editor Agent: Synthesizing balanced consensus...`
- `Financial Editor synthesized final balanced consensus report successfully.`

*(Note: In General Trend mode, the debate loop is automatically bypassed — this is expected behavior.)*

### ✅ 4. Output File Check
```bash
cat output/content_ideas.json | python3 -m json.tool | head -50
```
Should print a valid JSON with platform keys matching what you requested.

### ✅ 5. History Archive Check
```bash
ls -lt output/history/
```
Verify a file matching `content_ideas_{company_or_general}_{timestamp}.json` was created by your latest run.

### ✅ 6. Fallback Engine (No API keys)
Run any targeted command without API keys. You should see `(Strategy Tier 3)` in logs:
```
[!] Live fetches failed (or no credentials & RSS rate-limited)
  -> falling back to curated sample dataset (Strategy Tier 3)
```

---

## 📁 Output Files Reference

| File | Description |
|------|-------------|
| `data/unified_dataset.json` | Raw merged scrape output (reddit + youtube + news + twitter) |
| `data/pattern_report.json` | Analyzed hook patterns, topics, keywords, structures |
| `output/content_ideas.json` | Latest generation output (overwritten each run) |
| `output/history/content_ideas_general_{ts}.json` | Archive for General Trend runs |
| `output/history/content_ideas_{company}_{ts}.json` | Archive for Targeted runs (e.g. `uniswap`, `solana`, `ethena`) |

---

## 🏃 Quick Test Sequence (for evaluators with LM Studio running)

Run these in order to verify all major capabilities in ~10 minutes:

```bash
# 1. Verify collectors + analysis work (no LLM needed)
python3 main.py --skip-generate

# 2. General Trend — shorts only (no company, uses existing data)
python3 main.py --skip-collect --platforms shorts

# 3. Targeted — Ethena with debate loop (uses existing data)
python3 main.py --skip-collect --company Ethena --platforms shorts

# 4. Targeted — Solana, twitter threads
python3 main.py --skip-collect --company Solana --platforms twitter

# 5. Test a brand new company (Arbitrum) — proves dynamic targeting works
python3 main.py --skip-collect --company Arbitrum --platforms twitter

# 6. Check all archives created
ls -lt output/history/
```

### 🚀 Zero-LLM Verification (No LM Studio required)

Run this sequence to validate collectors and pattern analysis **without** any LLM:

```bash
# Fastest possible run (~3 seconds, no LLM, no scrape)
python3 main.py --skip-collect --skip-generate

# Fresh live scrape — verify all 4 collectors work
python3 main.py --skip-generate

# Targeted company scrape without LLM — verify targeted mode data resolution
python3 main.py --company Ethena --skip-generate

# Inspect saved pattern report
python3 -c "import json; d=json.load(open('data/pattern_report.json')); print('Keys:', list(d.keys())); print('Items analyzed:', d.get('total_items_analyzed'))"
```

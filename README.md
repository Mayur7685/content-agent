# Viral Crypto Content Idea Generator & Targeted Intelligence Pipeline

An AI-powered content automation pipeline that collects high-engagement crypto content, extracts viral hook patterns, and generates production-ready, platform-specific content scripts using a **local LLM** (LM Studio or Ollama). It runs fully offline with zero API cost.

This repository has been upgraded into a **Targeted Intelligence Pipeline** incorporating multi-agent collaboration, historical archiving, and automated sync options for publishing.

---

## ⚙️ Architecture

```
┌──────────────────┐     ┌───────────────────┐     ┌───────────────────┐     ┌──────────────────┐
│  1. COLLECT      │ --> │  2. ANALYZE       │ --> │  3. DEBATE        │ --> │  4. GENERATE     │
│                  │     │                   │     │  (Multi-Agent)    │     │  (Latest + Hist) │
│  Reddit search   │     │  Hook patterns    │     │                   │     │                  │
│  & Subreddits    │     │  Topic frequency  │     │  Bull Agent       │     │  Instagram Reels │
│                  │     │                   │     │  (Growth shill)   │     │  TikTok Videos   │
│  YouTube search  │     │  Storytelling     │     │                   │     │  YouTube Shorts  │
│  & RSS Channels  │     │  structures       │     │  Bear Agent       │     │  YouTube Videos  │
│                  │     │                   │     │  (Risk critic)    │     │  Twitter Threads │
│  Google News     │     │  Keyword rankings │     │                   │     │                  │
│  RSS search      │     │                   │     │  Editor Agent     │     │  5. NOTION SYNC  │
│                  │     │  Engagement       │     │  (Financial       │     │  (Automated db   │
│  Twitter search  │     │  weighted scoring │     │   consensus)      │     │   publishing)    │
└──────────────────┘     └───────────────────┘     └───────────────────┘     └──────────────────┘
```

---

## 🔥 Key Features

1. **Dual-Mode Engine (Dynamic Resolution)**:
   - **Targeted Intelligence Pipeline (`--company <name>`)**: Scrapes and filters content for specific tokens, protocols, or ecosystems (e.g. `Uniswap`, `Solana`, `Ethena`). Initiates a local 3-Agent Debate loop to synthesize context before generating highly focused, brand-specific templates.
   - **General Trend Discovery Pipeline (Omit `--company`)**: Scrapes macro cryptocurrency topics across top communities and media (e.g. CoinDesk, Decrypt, r/CryptoCurrency, r/Bitcoin, r/ethereum, etc.) to analyze general viral patterns, hooks, and keywords, generating trend-based ideations.
2. **Multi-Agent Debate Loop (Bull vs. Bear)**:
   A stateful 3-agent orchestration process to create unbiased, objective content. The *Bull Agent* finds positives, the *Bear Agent* critiques vulnerabilities, and the *Financial Editor* synthesizes a balanced consensus context.
3. **Selective Rich Platform Output (`--platforms`)**:
   - `instagram`: Reels with titles, hooks, visual guidelines, and scene-by-scene script templates.
   - `tiktok`: Video structures with sticker directives, dialogue, and sound prompts.
   - `shorts`: Mobile vertical layouts with looping hook strategies.
   - `youtube`: YouTube concepts with suggestion variants, high-CTR thumbnails, intro hook drafts, and time-stamped chapters.
   - `twitter`: Fully drafted Twitter threads (under 200 characters) with visual asset prompts.
4. **Historical Archive System**:
   Prevents overwriting previous generations. Saves the latest file to `output/content_ideas.json` and logs a metadata-named, timestamped copy in `output/history/` for audit tracking.
5. **Notion Synchronization**:
   Syncs generated content pages straight to a Notion database, creating page properties and embedding scene-by-scene scripts in child block layouts.

---

## 📂 Project Structure

```
crypto-content-ai/
├── collectors/
│   ├── reddit_collector.py     # Subreddits (RSS/OAuth) + targeted search RSS/OAuth
│   ├── youtube_collector.py    # RSS or Data API search filters
│   ├── news_collector.py       # Core RSS feeds or targeted Google News search RSS
│   ├── twitter_collector.py    # twitterapi.io targeted search query integrations
│   └── run_collectors.py       # Orchestrates collection and merges unified dataset
├── analyzer/
│   └── pattern_analyzer.py     # Rule-based regex hooks, structures, & weighted rankings
├── generator/
│   ├── idea_generator.py       # Runs Multi-Agent Debate and platform generator (Ollama/LM Studio)
│   └── notion_publisher.py     # Pushes generated scripts into Notion database API pages
├── data/                       # Scraped dataset logs and pattern report files
├── output/                     # Latest JSON output pointer
│   └── history/                # Timestamped runs (content_ideas_ethena_20260619_152029.json)
├── main.py                     # E2E pipeline runner script
├── requirements.txt            # System dependencies
└── .env                        # Configuration variables
```

---

## ⚡ Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
*Dependencies: `requests` and `feedparser`.*

### 2. Configure Environment (`.env`)
Create a `.env` file in the root directory:
```env
# Local LLM Server Configurations (Optional overrides)
LM_STUDIO_MODEL=                # Auto-resolves loaded model in LM Studio if empty
OLLAMA_MODEL=llama3.1

# Third-party Data Collectors (Optional keys)
TWITTERAPI_IO_KEY=your_twitterapi_io_key_here
YOUTUBE_API_KEY=your_google_youtube_api_key_here
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here

# Notion Synchronization (Optional keys)
NOTION_TOKEN=secret_your_notion_token_here
NOTION_DATABASE_ID=your_notion_database_id_here
```

### 3. Load Local LLM (LM Studio)
1. Launch **LM Studio** and download **google/gemma-4-12b** (or a similar high-performance model like **Qwen 2.5 7B/14B Instruct**).
2. Open the **Local Server** tab (the `<->` icon).
3. Load the model at the top and select **Start Server** (default: port `1234`).

---

## 🚀 CLI Reference — All Commands & Endpoints

### Flags

| Flag | Description | Default |
|------|-------------|----------|
| `--company <name>` | Target a specific protocol/ecosystem (e.g. `Uniswap`, `Solana`, `Ethena`). Omit for General Trend mode. | None (general) |
| `--platforms <list>` | Comma-separated: `instagram`, `tiktok`, `shorts`, `youtube`, `twitter` | All 5 |
| `--skip-collect` | Skip live scraping, reuse `data/unified_dataset.json` | Off |
| `--skip-generate` | Stop after pattern analysis — no LLM needed | Off |
| `--model <name>` | Override Ollama model name (LM Studio: load model in-app) | `llama3.1` |

---

### Group A — General Trend Discovery (Omit `--company`)

| Command | What It Does |
|---------|-------------|
| `python3 main.py --skip-generate` | Live scrape → analyze → skip LLM. **No LM Studio needed.** |
| `python3 main.py --skip-collect --platforms shorts` | Reuse data → generate YouTube Shorts |
| `python3 main.py --skip-collect --platforms twitter` | Reuse data → generate Twitter Threads |
| `python3 main.py --skip-collect --platforms instagram` | Reuse data → generate Instagram Reels |
| `python3 main.py --skip-collect --platforms tiktok` | Reuse data → generate TikTok Videos |
| `python3 main.py --skip-collect --platforms youtube` | Reuse data → generate YouTube Long-form |
| `python3 main.py --platforms shorts,twitter` | Live scrape → Shorts + Twitter |
| `python3 main.py --platforms instagram,tiktok` | Live scrape → Reels + TikTok |
| `python3 main.py --skip-collect` | Reuse data → all 5 platforms |
| `python3 main.py` | Full live pipeline → all 5 platforms |

---

### Group B — Targeted Intelligence Mode (`--company`)

| Command | What It Does |
|---------|-------------|
| `python3 main.py --company Uniswap --skip-generate` | Targeted Uniswap scrape → analyze → skip LLM |
| `python3 main.py --skip-collect --company Ethena --platforms shorts` | Debate loop for Ethena → Shorts |
| `python3 main.py --skip-collect --company Solana --platforms twitter` | Debate loop for Solana → Twitter Threads |
| `python3 main.py --company Solana --platforms twitter,instagram` | Live Solana scrape → debate → Threads + Reels |
| `python3 main.py --company Ethena --platforms shorts,twitter` | Live Ethena scrape → debate → Shorts + Threads |
| `python3 main.py --skip-collect --company Arbitrum --platforms youtube,twitter` | Arbitrum debate → YouTube + Twitter |
| `python3 main.py --company Uniswap --platforms instagram,tiktok,shorts,youtube,twitter` | Full Uniswap 5-platform suite (15 ideas) |

---

### Group C — Skip Flag Combinations

| Command | What It Does |
|---------|-------------|
| `python3 main.py --skip-collect --platforms shorts` | Fastest rerun: existing data → Shorts |
| `python3 main.py --skip-generate` | No LLM: fresh scrape + analysis only |
| `python3 main.py --company Solana --skip-generate` | No LLM: targeted Solana scrape + analysis |
| `python3 main.py --skip-collect --skip-generate` | Fastest test: existing data → pattern report only |

---

### Platform Output Schemas

| `--platforms` value | JSON key | Content Generated |
|---------------------|----------|------------------|
| `instagram` | `instagram_reels` | title, hook, visual_style_guidelines, scene_by_scene_script (3 scenes) |
| `tiktok` | `tiktok_videos` | title, sticker_directives, sound_prompt, dialogue_script |
| `shorts` | `youtube_shorts` | title, loop_hook_strategy, scene_by_scene_script (3 scenes) |
| `youtube` | `youtube_videos` | title_suggestions, hook_script, chapters with timestamps |
| `twitter` | `twitter_threads` | thread_hook, tweets[], visual_asset_prompt |

---

## 📊 Output Files

| File | Description |
|------|-------------|
| `data/unified_dataset.json` | Raw merged collector output (reddit + youtube + news + twitter) |
| `data/pattern_report.json` | Hook patterns, topic frequency, keywords, storytelling structures |
| `output/content_ideas.json` | Latest generation result (overwritten each run) |
| `output/history/content_ideas_general_{ts}.json` | Archive for General Trend runs |
| `output/history/content_ideas_{company}_{ts}.json` | Archive for Targeted runs (e.g. `uniswap`, `solana`, `ethena`) |

> 📖 See [TESTING_GUIDE.md](./TESTING_GUIDE.md) for the complete test scenario list, expected outputs, and verification checklist.

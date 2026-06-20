"""
Idea Generator (Local LLM via LM Studio or Ollama)
-----------------------------------------------------
Takes the pattern analysis report and generates long-format content ideas for
specific platforms (Instagram Reels, TikTok, YouTube Shorts, YouTube, Twitter).

Supports dynamically tailored schemas and CLI controls.
"""

import json
import os
import requests
import sys
import argparse
import datetime

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/api/generate"

LM_STUDIO_MODEL = os.environ.get("LM_STUDIO_MODEL", "")  # empty = use whatever's loaded
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")

# Load environment variables from .env if present in parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")


def load_pattern_report():
    path = os.path.join(DATA_DIR, "pattern_report.json")
    with open(path) as f:
        return json.load(f)


def build_prompt(report, target_platforms, company_name=None, company_context=None):
    hooks = ", ".join(f"{h[0]} ({h[1]}x)" for h in report["top_hook_patterns"][:5])
    topics = ", ".join(f"{t[0]} ({t[1]}x)" for t in report["top_topics"][:6])
    keywords = ", ".join(w for w, _ in report["top_keywords"][:8])
    examples = "\n".join(
        f"  - [{e['source']}] {e['text'][:80]}" for e in report["top_20_examples"][:3]
    )

    weighted_section = ""
    if report.get("weighted_topics"):
        weighted = ", ".join(
            f"{t['topic']} (eng:{t['total_engagement']})"
            for t in report["weighted_topics"][:4]
        )
        weighted_section = f"\nENGAGEMENT WEIGHTS:\n{weighted}\n"

    structures_section = ""
    if report.get("storytelling_structures"):
        structures = ", ".join(
            f"{s[0]} ({s[1]}x)" for s in report["storytelling_structures"][:4]
        )
        structures_section = f"\nSTRUCTURES:\n{structures}\n"

    company_instruction = ""
    if company_name and company_context:
        company_instruction = f"""
TARGET COMPANY/ECOSYSTEM: {company_name.upper()}
LATEST DEVELOPMENTS & ROADMAP CONTEXT:
{json.dumps(company_context, indent=2)}

CRITICAL REQUIREMENT: You MUST focus all generated content ideas exclusively on the project '{company_name.upper()}' and its recent developments/roadmap shown above. Do not generate generic crypto advice; keep every single idea, scene, chapter, and tweet strictly about {company_name.upper()}.
"""

    schemas = {}
    schema_descriptions = []

    if "instagram" in target_platforms:
        schemas["instagram_reels"] = [
            {
                "title": "Title",
                "hook": "Hook",
                "topic": "Topic",
                "angle": "Angle",
                "visual_style_guidelines": "Visual style",
                "scene_by_scene_script": [
                    {
                        "scene_number": 1,
                        "visual": "Visual prompt",
                        "on_screen_text": "Overlay",
                        "voiceover": "Narration"
                    }
                ],
                "based_on_pattern": "Pattern name"
            }
        ]
        schema_descriptions.append("- instagram_reels: exactly 3 items.")

    if "tiktok" in target_platforms:
        schemas["tiktok_videos"] = [
            {
                "title": "Title",
                "hook": "Hook",
                "topic": "Topic",
                "angle": "Angle",
                "sound_and_music_prompt": "Sound prompt",
                "scene_by_scene_script": [
                    {
                        "scene_number": 1,
                        "visual": "Visual prompt",
                        "on_screen_text": "Overlay",
                        "voiceover": "Dialogue"
                    }
                ],
                "based_on_pattern": "Pattern name"
            }
        ]
        schema_descriptions.append("- tiktok_videos: exactly 3 items.")

    if "shorts" in target_platforms:
        schemas["youtube_shorts"] = [
            {
                "title": "Title",
                "topic": "Topic",
                "angle": "Angle",
                "loop_hook_strategy": "Loop strategy",
                "scene_by_scene_script": [
                    {
                        "scene_number": 1,
                        "visual": "Visual prompt",
                        "on_screen_text": "Overlay",
                        "voiceover": "Narration"
                    }
                ],
                "based_on_pattern": "Pattern name"
            }
        ]
        schema_descriptions.append("- youtube_shorts: exactly 3 items.")

    if "youtube" in target_platforms:
        schemas["youtube_videos"] = [
            {
                "title_suggestions": ["CTR Title 1", "CTR Title 2", "CTR Title 3"],
                "thumbnail_concept": "Thumbnail concept",
                "hook_script": "Hook script (first 30-45s voiceover)",
                "topic": "Topic",
                "angle_thesis": "Thesis summary",
                "chapters": [
                    {
                        "timestamp_marker": "0:00 - 1:30",
                        "chapter_title": "Chapter title",
                        "core_points": ["Point 1", "Point 2"],
                        "b_roll_and_visuals": "Visual prompt"
                    }
                ],
                "based_on_pattern": "Pattern name"
            }
        ]
        schema_descriptions.append("- youtube_videos: exactly 3 long-form video concepts.")

    if "twitter" in target_platforms:
        schemas["twitter_threads"] = [
            {
                "thread_hook": "Hook Tweet (under 280 chars)",
                "topic": "Topic",
                "angle_thesis": "Thesis summary",
                "tweets": ["Tweet 1", "Tweet 2"],
                "visual_asset_prompts": ["Asset prompt for tweet 2"],
                "based_on_pattern": "Pattern name"
            }
        ]
        schema_descriptions.append("- twitter_threads: exactly 3 threads (4-7 tweets per thread).")

    json_template = json.dumps(schemas, indent=2)
    descriptions_str = "\n".join(schema_descriptions)

    prompt = f"""You are a viral crypto content strategist. Below is real data extracted
from high-engagement crypto content (Reddit, YouTube, news, Twitter/X).

DOMINANT HOOK PATTERNS:
{hooks}

TRENDING TOPICS:
{topics}
{weighted_section}{structures_section}
TOP KEYWORDS:
{keywords}

REAL EXAMPLES FROM THIS WEEK:
{examples}
{company_instruction}

---

Using these REAL patterns, generate highly detailed, long-format, and actionable content templates for:
{", ".join(target_platforms).upper()}

Each idea must directly draw on at least one of the hook patterns or topics above.

IMPORTANT: Do not generate any thinking, reasoning, explanation, or thought blocks. Skip the thinking phase entirely. Respond with ONLY valid JSON matching this schema structure, with no markdown fences, no preamble, and no postscript:

{json_template}

Ensure you generate exactly:
{descriptions_str}

To prevent latency and avoid API timeouts, you must strictly follow these constraints:
1. Limit 'scene_by_scene_script' arrays to exactly 3 scenes: Scene 1 (Hook), Scene 2 (Body), Scene 3 (CTA).
2. Keep visual prompts under 10 words.
3. Keep voiceover/narration text under 15 words.
4. Keep drafted tweets under 200 characters to safely fit standard limits.
5. Begin immediately with the opening bracket '{' and end with the closing bracket '}'.
"""
    return prompt


def detect_backend():
    """Check which local LLM server is actually running. LM Studio first."""
    try:
        r = requests.get("http://localhost:1234/v1/models", timeout=3)
        if r.status_code == 200:
            return "lmstudio"
    except requests.exceptions.RequestException:
        pass

    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            return "ollama"
    except requests.exceptions.RequestException:
        pass

    return None


def call_lmstudio(prompt, json_mode=True):
    # Dynamically fetch the loaded model ID from LM Studio
    model_id = LM_STUDIO_MODEL
    if not model_id:
        try:
            r = requests.get("http://localhost:1234/v1/models", timeout=5)
            if r.status_code == 200:
                models_data = r.json().get("data", [])
                # Find first model that is not an embedding model
                for m in models_data:
                    m_id = m.get("id", "")
                    if "embed" not in m_id:
                        model_id = m_id
                        break
                # Fallback to the first model if none found
                if not model_id and models_data:
                    model_id = models_data[0].get("id")
        except Exception:
            pass
            
    # Default fallback if fetch failed
    if not model_id:
        model_id = "local-model"

    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 4000,
        "stream": True
    }
    
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    def perform_stream(req_payload):
        resp = requests.post(LM_STUDIO_URL, json=req_payload, stream=True, timeout=(60, 600))
        resp.raise_for_status()
        
        full_content = []
        has_reasoning = False
        
        print("\n--- Model Reasoning (Chain of Thought) ---")
        for chunk in resp.iter_lines():
            if chunk:
                decoded = chunk.decode("utf-8")
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choice = data.get("choices", [{}])[0]
                        
                        # Handle reasoning content
                        reasoning = choice.get("delta", {}).get("reasoning_content")
                        if reasoning:
                            if not has_reasoning:
                                has_reasoning = True
                            sys.stdout.write(reasoning)
                            sys.stdout.flush()
                            
                        # Handle assistant content
                        content = choice.get("delta", {}).get("content")
                        if content:
                            if has_reasoning:
                                print("\n\n--- Generating Final Content JSON ---")
                                has_reasoning = False
                            sys.stdout.write(content)
                            sys.stdout.flush()
                            full_content.append(content)
                    except Exception:
                        pass
        print()
        return "".join(full_content)

    try:
        return perform_stream(payload)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 400 and json_mode:
            print("  [!] LM Studio rejected 'json_object' format. Retrying in plain text streaming mode...")
            payload.pop("response_format", None)
            return perform_stream(payload)
        raise e


def call_ollama(prompt, json_mode=True):
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": True}
    if json_mode:
        payload["format"] = "json"
        
    resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=(60, 600))
    resp.raise_for_status()
    
    full_content = []
    print("\n--- Ollama Generating Content ---")
    for chunk in resp.iter_lines():
        if chunk:
            try:
                data = json.loads(chunk.decode("utf-8"))
                content = data.get("response", "")
                if content:
                    sys.stdout.write(content)
                    sys.stdout.flush()
                    full_content.append(content)
                if data.get("done", False):
                    break
            except Exception:
                pass
    print()
    return "".join(full_content)


def call_llm(prompt, backend, json_mode=True):
    if backend == "lmstudio":
        return call_lmstudio(prompt, json_mode)
    elif backend == "ollama":
        return call_ollama(prompt, json_mode)
    raise RuntimeError("No backend specified")


def strip_code_fences(text):
    """Some models wrap JSON in ```json fences even when told not to."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def print_ideas(ideas):
    print("\n" + "=" * 60)
    print("GENERATED ACTIONABLE CONTENT IDEAS")
    print("=" * 60)

    if ideas.get("instagram_reels"):
        print("\n📱 INSTAGRAM REELS")
        for i, idea in enumerate(ideas["instagram_reels"], 1):
            print(f"\n  {i}. TITLE: {idea.get('title')}")
            print(f"     Hook: \"{idea.get('hook')}\"")
            print(f"     Topic: {idea.get('topic')} (Based on: {idea.get('based_on_pattern')})")
            print(f"     Angle: {idea.get('angle')}")
            print(f"     Visual Style: {idea.get('visual_style_guidelines')}")
            print(f"     Script Outline:")
            for beat in idea.get("scene_by_scene_script", []):
                print(f"       [Scene {beat.get('scene_number')}] Visual: {beat.get('visual')}")
                print(f"                 Overlay: \"{beat.get('on_screen_text')}\"")
                print(f"                 VO: \"{beat.get('voiceover')}\"")

    if ideas.get("tiktok_videos"):
        print("\n🎵 TIKTOK VIDEOS")
        for i, idea in enumerate(ideas["tiktok_videos"], 1):
            print(f"\n  {i}. TITLE: {idea.get('title')}")
            print(f"     Hook: \"{idea.get('hook')}\"")
            print(f"     Topic: {idea.get('topic')} (Based on: {idea.get('based_on_pattern')})")
            print(f"     Sound Prompt: {idea.get('sound_and_music_prompt')}")
            print(f"     Script Outline:")
            for beat in idea.get("scene_by_scene_script", []):
                print(f"       [Scene {beat.get('scene_number')}] Visual: {beat.get('visual')}")
                print(f"                 Overlay: \"{beat.get('on_screen_text')}\"")
                print(f"                 VO: \"{beat.get('voiceover')}\"")

    if ideas.get("youtube_shorts"):
        print("\n⚡ YOUTUBE SHORTS")
        for i, idea in enumerate(ideas["youtube_shorts"], 1):
            print(f"\n  {i}. TITLE: {idea.get('title')}")
            print(f"     Topic: {idea.get('topic')} (Based on: {idea.get('based_on_pattern')})")
            print(f"     Loop Strategy: {idea.get('loop_hook_strategy')}")
            print(f"     Script Outline:")
            for beat in idea.get("scene_by_scene_script", []):
                print(f"       [Scene {beat.get('scene_number')}] Visual: {beat.get('visual')}")
                print(f"                 Overlay: \"{beat.get('on_screen_text')}\"")
                print(f"                 VO: \"{beat.get('voiceover')}\"")

    if ideas.get("youtube_videos"):
        print("\n🎥 YOUTUBE LONG-FORM VIDEOS")
        for i, idea in enumerate(ideas["youtube_videos"], 1):
            print(f"\n  {i}. TOPIC: {idea.get('topic')} (Based on: {idea.get('based_on_pattern')})")
            print(f"     Suggested Titles:")
            for title in idea.get("title_suggestions", []):
                print(f"       - {title}")
            print(f"     Thumbnail Concept: {idea.get('thumbnail_concept')}")
            print(f"     Opening Hook VO Script: \"{idea.get('hook_script')}\"")
            print(f"     Angle Thesis: {idea.get('angle_thesis')}")
            print(f"     Video Chapters:")
            for chapter in idea.get("chapters", []):
                print(f"       [{chapter.get('timestamp_marker')}] {chapter.get('chapter_title')}")
                print(f"         Points: {', '.join(chapter.get('core_points', []))}")
                print(f"         Visuals: {chapter.get('b_roll_and_visuals')}")

    if ideas.get("twitter_threads"):
        print("\n🧵 TWITTER THREADS")
        for i, idea in enumerate(ideas["twitter_threads"], 1):
            print(f"\n  {i}. TOPIC: {idea.get('topic')} (Based on: {idea.get('based_on_pattern')})")
            print(f"     Thread Thesis: {idea.get('angle_thesis')}")
            print(f"     First Tweet (Hook): \"{idea.get('thread_hook')}\"")
            print(f"     Thread Tweets:")
            for index, tweet in enumerate(idea.get("tweets", []), 1):
                print(f"       Tweet {index}: \"{tweet}\"")
            if idea.get("visual_asset_prompts"):
                print(f"     Asset Prompts: {idea.get('visual_asset_prompts')}")

    print("\n" + "=" * 60)


def synthesize_company_context(report, company_name, backend):
    # Extract the text of the examples to use as context
    examples_text = "\n".join(
        f"- [{e['source']}] {e['text']}" for e in report.get("top_20_examples", [])[:10]
    )
    
    print(f"\n--- Starting Multi-Agent Debate for {company_name.upper()} ---")

    # Step 1: Bull Agent
    print("[Agent 1/3] Bull Agent: Analyzing positives and growth thesis...")
    bull_prompt = f"""You are a crypto bull and project shill. Analyze the recent posts about '{company_name}' and compile a highly optimistic summary of its latest achievements, launches, and positive roadmap indicators.
Posts:
{examples_text}

Provide your bullish report in valid JSON format with exactly these two keys:
- "positives": A list of 2-3 major bullish achievements or upcoming bullish catalysts.
- "growth_thesis": A one-sentence summary explaining why this project is poised for growth.
Respond with ONLY valid JSON, starting with '{{' and ending with '}}'. Do not include markdown fences or preamble."""
    
    bull_report = None
    try:
        raw_bull = call_llm(bull_prompt, backend, json_mode=True)
        cleaned_bull = strip_code_fences(raw_bull)
        bull_report = json.loads(cleaned_bull)
        print("  -> Bull Agent report compiled successfully.")
    except Exception as e:
        print(f"  [!] Bull Agent failed: {e}. Using fallback positives.")
        bull_report = {
            "positives": [f"Strong community support and recent utility upgrades for {company_name}."],
            "growth_thesis": f"The ecosystem shows solid user retention and scaling momentum."
        }

    # Step 2: Bear Agent
    print("[Agent 2/3] Bear Agent: Analyzing risks and critique points...")
    bear_prompt = f"""You are a crypto bear, skeptic, and risk analyst. Analyze the recent posts about '{company_name}' and compile a critical review of its vulnerabilities, centralization risks, security audits, or potential price correction indicators.
Posts:
{examples_text}

Provide your bearish report in valid JSON format with exactly these two keys:
- "negatives": A list of 2-3 critical risks, concerns, or warnings.
- "risk_thesis": A one-sentence summary explaining what could cause the project to drop or fail.
Respond with ONLY valid JSON, starting with '{{' and ending with '}}'. Do not include markdown fences or preamble."""

    bear_report = None
    try:
        raw_bear = call_llm(bear_prompt, backend, json_mode=True)
        cleaned_bear = strip_code_fences(raw_bear)
        bear_report = json.loads(cleaned_bear)
        print("  -> Bear Agent report compiled successfully.")
    except Exception as e:
        print(f"  [!] Bear Agent failed: {e}. Using fallback concerns.")
        bear_report = {
            "negatives": [f"Market volatility and regulatory scrutiny facing the {company_name} ecosystem."],
            "risk_thesis": f"High sell pressure or protocol vulnerabilities could trigger corrections."
        }

    # Step 3: Editor Agent
    print("[Agent 3/3] Editor Agent: Synthesizing balanced consensus...")
    editor_prompt = f"""You are a senior financial crypto editor. Ingest the following bullish analysis and bearish critique for '{company_name}':

BULL REPORT:
{json.dumps(bull_report, indent=2)}

BEAR CRITIQUE:
{json.dumps(bear_report, indent=2)}

Synthesize these two contrasting perspectives into a balanced, highly objective target context report.
Provide a concise summary in valid JSON format with exactly these three keys:
- "recent_developments": A list of 2-3 developments (mentioning both recent launches and relevant risks or concerns).
- "community_sentiment": A one-sentence summary showing both the hype and the skepticism.
- "upcoming_roadmap": A list of 1-2 upcoming milestones or critical warnings.

Respond with ONLY valid JSON, starting with '{{' and ending with '}}'. Do not include markdown fences, thinking, or preamble."""

    try:
        raw_editor = call_llm(editor_prompt, backend, json_mode=True)
        cleaned_editor = strip_code_fences(raw_editor)
        context = json.loads(cleaned_editor)
        print("  -> Financial Editor synthesized final balanced consensus report successfully.")
        return context
    except Exception as e:
        print(f"  [!] Editor Agent failed: {e}. Using combined fallback.")
        return {
            "recent_developments": [
                f"{company_name} shows active development, but faces standard market headwinds.",
                "Community discussion highlights both structural upgrades and security concerns."
            ],
            "community_sentiment": f"A mix of high bullish optimism and cautious warning flags.",
            "upcoming_roadmap": [
                f"Protocol enhancements are on schedule, but users are advised to monitor risk markers."
            ]
        }


def main(platforms=None, company_name=None):
    # Parse command-line arguments if not passed from main.py
    if platforms is None or company_name is None:
        parser = argparse.ArgumentParser(description="Idea Generator Standalone")
        parser.add_argument("--platforms", default=None, help="Comma-separated target platforms (instagram, tiktok, shorts, youtube, twitter)")
        parser.add_argument("--company", default=None, help="Target a specific crypto company/ecosystem")
        args, unknown = parser.parse_known_args()
        if platforms is None:
            platforms = args.platforms
        if company_name is None:
            company_name = args.company

    target_platforms = []
    if platforms:
        target_platforms = [p.strip().lower() for p in platforms.split(",") if p.strip()]
    else:
        # Default is all platforms
        target_platforms = ["instagram", "tiktok", "shorts", "youtube", "twitter"]

    # Filter out invalid entries
    valid_platforms = {"instagram", "tiktok", "shorts", "youtube", "twitter"}
    target_platforms = [p for p in target_platforms if p in valid_platforms]
    if not target_platforms:
        target_platforms = ["instagram", "tiktok", "shorts", "youtube", "twitter"]

    print(f"Generating rich content ideas for platforms: {', '.join(target_platforms).upper()}")

    print("Loading pattern report...")
    report = load_pattern_report()

    print("Checking for a running local LLM server...")
    backend = detect_backend()

    if backend is None:
        print("\n[ERROR] No local LLM server detected.")
        print("Start ONE of these:")
        print("  LM Studio: open the app -> Local Server tab -> load a model -> Start Server")
        print("            (default: http://localhost:1234)")
        print("  Ollama:    ollama pull llama3.1 && ollama serve")
        print("            (default: http://localhost:11434)")
        return None

    print(f"  -> using backend: {backend}")
    
    company_context = None
    if company_name:
        company_context = synthesize_company_context(report, company_name, backend)
        print(f"Synthesized context for {company_name}:")
        print(json.dumps(company_context, indent=2))

    ideas = {}
    for platform in target_platforms:
        print(f"\n--- Generating ideas for platform: {platform.upper()} ---")
        prompt = build_prompt(report, [platform], company_name=company_name, company_context=company_context)
        
        try:
            raw = call_llm(prompt, backend, json_mode=True)
            cleaned = strip_code_fences(raw)
            platform_ideas = json.loads(cleaned)
            ideas.update(platform_ideas)
        except json.JSONDecodeError:
            print(f"\n[WARN] Model did not return valid JSON for platform {platform.upper()}. Retrying once...")
            try:
                raw = call_llm(prompt, backend, json_mode=True)
                cleaned = strip_code_fences(raw)
                platform_ideas = json.loads(cleaned)
                ideas.update(platform_ideas)
            except Exception as e:
                print(f"[ERROR] Retry failed for {platform.upper()}: {e}")
        except requests.exceptions.RequestException as e:
            print(f"\n[ERROR] Request to {backend} failed for platform {platform.upper()}: {e}")

    if not ideas:
        print("\n[ERROR] No ideas were successfully generated.")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save to standard latest content ideas file
    latest_path = os.path.join(OUTPUT_DIR, "content_ideas.json")
    with open(latest_path, "w") as f:
        json.dump(ideas, f, indent=2)

    # Save to history directory with timestamp and target company/ecosystem details
    history_dir = os.path.join(OUTPUT_DIR, "history")
    os.makedirs(history_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_label = company_name.lower().replace(" ", "_") if company_name else "general"
    history_filename = f"content_ideas_{target_label}_{timestamp}.json"
    history_path = os.path.join(history_dir, history_filename)
    
    with open(history_path, "w") as f:
        json.dump(ideas, f, indent=2)

    print_ideas(ideas)
    print(f"\nSaved Latest -> {latest_path}")
    print(f"Saved History -> {history_path}")
    return ideas


if __name__ == "__main__":
    main()

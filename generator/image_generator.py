"""
AI Visual Asset Generator
----------------------------
Takes generated content ideas and uses Pollinations.ai's free image generation API 
to automatically download and save visual assets (thumbnails and script scene graphics)
locally to output/assets/.
"""

import os
import requests
import urllib.parse

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
ASSET_DIR = os.path.join(OUTPUT_DIR, "assets")


def generate_image(prompt: str, filename: str) -> bool:
    """Download an AI generated image matching a prompt from Pollinations.ai."""
    os.makedirs(ASSET_DIR, exist_ok=True)
    out_path = os.path.join(ASSET_DIR, filename)

    print(f"  [AI Image] Querying prompt: '{prompt[:60]}...'")
    
    # URL encode the prompt
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"

    try:
        # Fetch image bytes
        r = requests.get(url, timeout=45)
        r.raise_for_status()
        
        with open(out_path, "wb") as f:
            f.write(r.content)
            
        print(f"    -> Saved asset to: output/assets/{filename}")
        return True
    except Exception as e:
        print(f"    [!] Failed to generate image for filename '{filename}': {e}")
        return False


def generate_and_save_assets(ideas):
    """Scan ideas across platforms and generate visual assets where prompts exist."""
    if not ideas:
        return

    print("\n============================================================")
    print("GENERATING AI VISUAL ASSETS (Pollinations.ai)")
    print("============================================================")

    # 1. Instagram Reels
    if "instagram_reels" in ideas:
        for idx, item in enumerate(ideas["instagram_reels"], 1):
            title_slug = item.get("title", f"reel_{idx}").lower().replace(" ", "_")[:20]
            scenes = item.get("scene_by_scene_script", [])
            if scenes:
                # Generate first scene graphic as visual suggest
                first_visual = scenes[0].get("visual", "")
                if first_visual and first_visual != "Visual prompt":
                    generate_image(
                        prompt=f"{first_visual}, high quality aesthetic cinematic visual",
                        filename=f"instagram_{title_slug}_scene1.jpg"
                    )

    # 2. TikTok Videos
    if "tiktok_videos" in ideas:
        for idx, item in enumerate(ideas["tiktok_videos"], 1):
            title_slug = item.get("title", f"tiktok_{idx}").lower().replace(" ", "_")[:20]
            scenes = item.get("scene_by_scene_script", [])
            if scenes:
                first_visual = scenes[0].get("visual", "")
                if first_visual and first_visual != "Visual prompt":
                    generate_image(
                        prompt=f"{first_visual}, high contrast trending tiktok graphic",
                        filename=f"tiktok_{title_slug}_scene1.jpg"
                    )

    # 3. YouTube Shorts
    if "youtube_shorts" in ideas:
        for idx, item in enumerate(ideas["youtube_shorts"], 1):
            title_slug = item.get("title", f"shorts_{idx}").lower().replace(" ", "_")[:20]
            scenes = item.get("scene_by_scene_script", [])
            if scenes:
                first_visual = scenes[0].get("visual", "")
                if first_visual and first_visual != "Visual prompt":
                    generate_image(
                        prompt=f"{first_visual}, cinematic framing vertical vertical short style",
                        filename=f"shorts_{title_slug}_scene1.jpg"
                    )

    # 4. YouTube Long-form Videos
    if "youtube_videos" in ideas:
        for idx, item in enumerate(ideas["youtube_videos"], 1):
            concept = item.get("thumbnail_concept", "")
            title = item.get("title_suggestions", ["youtube_video"])[0]
            title_slug = title.lower().replace(" ", "_")[:20]
            if concept and concept != "Thumbnail concept":
                generate_image(
                    prompt=f"{concept}, professional youtube thumbnail design, vibrant colors, 4k",
                    filename=f"youtube_{title_slug}_thumbnail.jpg"
                )

    # 5. Twitter Threads
    if "twitter_threads" in ideas:
        for idx, item in enumerate(ideas["twitter_threads"], 1):
            asset_prompts = item.get("visual_asset_prompts", [])
            topic_slug = item.get("topic", f"thread_{idx}").lower().replace(" ", "_")[:20]
            for asset_idx, prompt in enumerate(asset_prompts, 1):
                if prompt and "Asset prompt" not in prompt:
                    generate_image(
                        prompt=f"{prompt}, professional infographic style digital illustration",
                        filename=f"twitter_{topic_slug}_asset{asset_idx}.jpg"
                    )

    print("============================================================\n")

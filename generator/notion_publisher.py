"""
Notion Publisher
-------------------
Automatically synchronizes and publishes generated crypto content ideas to a target 
Notion database.

Requires: NOTION_TOKEN and NOTION_DATABASE_ID in your .env file.
If not set, skips execution with instructions on how to set up the integration.
"""

import os
import requests
import json

# Load environment variables from .env if present in parent directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'\"")


def create_notion_blocks(platform, item):
    """Build body blocks for a Notion page depending on the platform type."""
    blocks = []

    # Title / Header Block
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "🎬 Content Details & Script"}}]
        }
    })

    # Add scene by scene details
    if "scene_by_scene_script" in item:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "Below is the scene-by-scene outline for editing:"}}]
            }
        })
        for scene in item["scene_by_scene_script"]:
            num = scene.get("scene_number", 1)
            visual = scene.get("visual", "")
            overlay = scene.get("on_screen_text", "")
            vo = scene.get("voiceover", "")
            
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": f"Scene {num}"}}]
                }
            })
            
            content_str = f"🎥 Visual: {visual}\n💬 Text Overlay: \"{overlay}\"\n🎙️ Voiceover/Narration: \"{vo}\""
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content_str}}]
                }
            })

    # Add chapters details for YouTube long-form
    if "chapters" in item:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"📽️ Hook Script:\n\"{item.get('hook_script', '')}\"\n\nVideo Chapters:"}}]
            }
        })
        for ch in item["chapters"]:
            marker = ch.get("timestamp_marker", "")
            ch_title = ch.get("chapter_title", "")
            points = ", ".join(ch.get("core_points", []))
            vis = ch.get("b_roll_and_visuals", "")
            
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": f"[{marker}] {ch_title}"}}]
                }
            })
            
            content_str = f"💡 Points: {points}\n🎬 Visuals/B-Roll: {vis}"
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content_str}}]
                }
            })

    # Add tweets list for Twitter Threads
    if "tweets" in item:
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "🧵 Drafted Tweets:"}}]
            }
        })
        for i, tweet in enumerate(item["tweets"], 1):
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"{i}/ {tweet}"}}]
                }
            })

    # Add pattern details
    blocks.append({
        "object": "block",
        "type": "divider",
        "divider": {}
    })
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": f"Based on viral pattern: {item.get('based_on_pattern', 'unknown')}"}}]
        }
    })

    return blocks


def publish_to_notion(ideas):
    """Publish generated ideas directly to Notion if environment variables are set."""
    token = os.environ.get("NOTION_TOKEN")
    db_id = os.environ.get("NOTION_DATABASE_ID")

    print("\n============================================================")
    print("NOTION AUTOMATED PUBLICATION SYNC")
    print("============================================================")

    if not token or not db_id:
        print("[INFO] Notion sync is currently skipped because credentials are not set.")
        print("To enable Notion auto-publishing, perform the following steps:")
        print("  1. Create a Notion integration: https://www.notion.so/my-integrations")
        print("  2. Add your integration secret key and database ID to your .env file:")
        print("     NOTION_TOKEN=secret_your_token_here")
        print("     NOTION_DATABASE_ID=your_database_id_here")
        print("  3. Make sure to share your Notion database with the integration.")
        print("============================================================\n")
        return False

    print("  -> Connection detected: Syncing templates to Notion...")

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # Map platform keys to readable names
    platform_names = {
        "instagram_reels": "Instagram Reels",
        "tiktok_videos": "TikTok Videos",
        "youtube_shorts": "YouTube Shorts",
        "youtube_videos": "YouTube Long-form",
        "twitter_threads": "Twitter Threads"
    }

    success_count = 0
    fail_count = 0

    for platform_key, items in ideas.items():
        platform_name = platform_names.get(platform_key, platform_key)
        for item in items:
            # Determine suitable title
            title = item.get("title", item.get("thread_hook", item.get("title_suggestions", ["Untitled"])[0]))
            if isinstance(title, list):
                title = title[0]
            # Limit length of title just in case
            title = title[:100]

            topic = item.get("topic", "General")
            pattern = item.get("based_on_pattern", "General Pattern")

            # Create properties payload
            properties = {
                "Title": {
                    "title": [
                        {"text": {"content": title}}
                    ]
                },
                "Platform": {
                    "select": {"name": platform_name}
                },
                "Topic": {
                    "rich_text": [
                        {"text": {"content": topic}}
                    ]
                },
                "Pattern": {
                    "rich_text": [
                        {"text": {"content": pattern}}
                    ]
                }
            }

            blocks = create_notion_blocks(platform_key, item)

            payload = {
                "parent": {"database_id": db_id},
                "properties": properties,
                "children": blocks[:100]  # Notion limit: max 100 blocks per request
            }

            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=20)
                resp.raise_for_status()
                print(f"    -> Successfully published '{title}' [{platform_name}]")
                success_count += 1
            except Exception as e:
                print(f"    [!] Failed to publish '{title}': {e}")
                try:
                    if 'resp' in locals() and hasattr(resp, 'text'):
                        print(f"        Notion API Error Response: {resp.text}")
                except Exception:
                    pass
                fail_count += 1

    print(f"\n  => Sync Complete: {success_count} published, {fail_count} failed.")
    print("============================================================\n")
    return success_count > 0

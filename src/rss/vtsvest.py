import asyncio
import requests
import hashlib
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Assuming you already have these clients set up:
from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

async def get_vtsvest_news():
    feed_url = "https://rss.app/feeds/v1.1/6d0viibyyK1Kbx5m.json"
    
    try:
        response = requests.get(feed_url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.error(f"Could not fetch VTSvest feed from {feed_url}: {e}")
        return

    items = data.get("items", [])
    for item in items:
        # Extract title and description (from "content_text")
        title = item.get("title", "").strip()
        description = item.get("content_text", "").strip()
        url = item.get("url", "").strip()

        # Create a hash of the title to use as our Redis key
        hashed_title = hashlib.md5(title.encode("utf-8")).hexdigest()
        # Check Redis to see if the hashed title already exists
        if not redis_client.exists(hashed_title):
            try:
                # Build the Slack message
                message_text = (
                    f"*{title}*\n"
                    f"{description}\n\n"
                    f"<{url}|Les mer>"
                )
                send_slack_chat(message_text, "https://pbs.twimg.com/profile_images/705375750464081920/1dLC1aX4_normal.jpg", "Vegtrafikksentralen Vest (X)")
                
                # Save hash in Redis, so we don't post the same item again
                redis_client.set(hashed_title, 1)
                print(f"Sent VTSvest message with title: {title}")
            except Exception as err:
                logging.error(f"Error sending Slack message for {title}: {err}")
        else:
            logging.info(f"Skipping already posted item: {title}")

if __name__ == "__main__":
    asyncio.run(get_vtsvest_news())

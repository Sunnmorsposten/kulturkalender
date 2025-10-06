import requests
import asyncio
import hashlib
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Assuming you already have these clients set up:
from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

async def get_110vest_news():
    feed_url = "https://rss.app/feeds/v1.1/4t9ySEvvb9v7q1wp.json"
    
    try:
        response = requests.get(feed_url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.error(f"Could not fetch feed from {feed_url}: {e}")
        return

    items = data.get("items", [])
    for item in items:
        # Extract title and "description" (we'll use content_text as the description)
        title = item.get("title", "").strip()
        description = item.get("content_text", "").strip()
        url = item.get("url", "").strip()

        # Hash the title to use as a Redis key
        hashed_title = hashlib.md5(title.encode("utf-8")).hexdigest()

        # Check if we already have this news item (title) in Redis
        if not redis_client.exists(hashed_title):
            try:
                # Construct the message to post to Slack
                message_text = (
                    f"*{title}*\n"
                    f"{description}\n\n"
                    f"<{url}|Les mer>"
                )
                send_slack_chat(message_text, "https://pbs.twimg.com/profile_images/1356161899721797632/ljUMvWMo_normal.jpg", "110 Vest (X)")
                
                # Store in Redis to avoid duplicates later
                redis_client.set(hashed_title, 1)
                print(f"Sent 110 Vest message with title: {title}")
            except Exception as err:
                logging.error(f"Error sending Slack message: {err}")
        else:
            logging.info(f"Skipping existing news item: {title}")

if __name__ == "__main__":
    asyncio.run(get_110vest_news())
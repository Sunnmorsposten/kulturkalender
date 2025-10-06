import asyncio
import feedparser
import logging
import hashlib
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# If these are available in your environment:
from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

async def get_sjomatradet_news():
    try:
        # Parse the RSS feed
        feed = feedparser.parse("https://www.seafood.no/rssfeed?feedId=26&lang=no")
        for entry in feed.entries[:10]:
            link = entry.link
            title = entry.title
            description = entry.description
            if not title:
                continue
            title = title.strip()
            message_id = link
            message_text = (
                f"*{title}*\n"
                f"{description}\n\n"
                f"<{link}|Les mer på Seafood.no her.>"
            )
            send_slack_chat(message_id, message_text, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSjdHP1jos1KogYVEfvo2YZjgcelaXCfAPVJg&s", "Norges Sjømatråd")
            
    except Exception as e:
        print(f"An error occurred while fetching Seafood news: {e}")

if __name__ == "__main__":
    asyncio.run(get_sjomatradet_news())
import logging
import asyncio
import requests
import hashlib
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# If these clients are available in your environment:
from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

async def get_sildelaget_news():
    try:
        response = requests.get("https://www.sildelaget.no/umbraco/api/articlesearch/fetchAllArticles?skip=0&take=20&order=desc&culture=nb")
        response.raise_for_status()
        data = response.json()
        for item in data.get("items", [])[:10]:
            url = f"https://www.sildelaget.no{item.get('url', '')}"
            title = item.get("title", "")
            if not title:
                continue
            title = title.strip()
            subtitle = item.get("subtitle", "").strip()
            message_id = url

            message_text = (
                f"*{title}*\n"
                f"{subtitle}\n\n"
                f"<{url}|Les mer>")
            
            send_slack_chat(message_id, message_text, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRDNmGyBWOQrLSUGY3x0ywuCb9O5C2BPVkbTw&s", "Norges Sildesalgslag")
            

    except Exception as err:
        logging.error(f"An error occurred while fetching Sildelaget news: {err}")

if __name__ == "__main__":
    asyncio.run(get_sildelaget_news())
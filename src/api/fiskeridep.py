import asyncio
import feedparser
import logging
import hashlib
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

async def get_fiskeridep_news():
    """
    Fetches news from Fiskeridepartementet and posts to Slack if not already seen.
    """
    try:
        feed_url = "https://www.regjeringen.no/no/rss/Rss/2581966/?documentType=aktuelt/nyheter&owner=709"
        feed = feedparser.parse(feed_url)

        for entry in feed.entries[:10]:
            link = entry.link
            title = entry.title
            description = getattr(entry, "description", "")
            if not title:
                continue
            title = title.strip()
            
            message_id = link

            message_text = (
                f"*{title}*\n"
                f"{description}\n\n"
                f"<{link}|Les mer på Nærings- og fiskeridepartementet sine sider her.>"
            )
            
            send_slack_chat(message_id, message_text, "https://media.licdn.com/dms/image/v2/C510BAQEu34Wh9CCiQw/company-logo_200_200/company-logo_200_200/0/1630568996082/ministry_of_trade_and_industry_logo?e=2147483647&v=beta&t=6fi0Ik12Yx7P-w49DxEr4BsAgEOoDDl4CGJSTXPdgnA", "Nærings- og fiskeridepartementet")
            

    except Exception as e:
        logging.error(f"An error occurred while fetching Fiskeridep news: {e}")

if __name__ == "__main__":
    asyncio.run(get_fiskeridep_news())

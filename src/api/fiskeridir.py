import feedparser
import logging
import asyncio
import hashlib
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat


async def get_fiskeridir_news(newstype: str) -> None:
    """
    Fetches news from Fiskeridir and posts to Slack if not already seen.

    Parameters
    ----------
    newstype : str
        Type of news to get. Either "nyheter" or "rss/j-meldinger"
    """
    try:
        feed = feedparser.parse(f"https://www.fiskeridir.no/rss/{newstype}")
        for entry in feed.entries[:10]:
            link = entry.link
            title = entry.title
            description = entry.description

            if not title:
                continue
            title = title.strip()
            
            message_text = (
                        f"*{title}*\n"
                        f"{description}\n\n"
                        f"<{link}|Les mer på Fiskeridir sine sider her.>"
                    )
            message_id = link
            send_slack_chat(message_id, message_text, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTDdRsw3d5p_zgRPpMGk1yafwzJethA3aUdy1_wicSMlNU-hrt4pvnptcR-_91nE-g3ZPQ&usqp=CAU", "Fiskeridirektoratet")
            

    except Exception as e:
        logging.error(f"An error occurred while fetching Fiskeridir news: {e}")


if __name__ == "__main__":
    asyncio.run(get_fiskeridir_news("nyheter"))
    # asyncio.run(get_fiskeridir_news("rss/j-meldinger"))
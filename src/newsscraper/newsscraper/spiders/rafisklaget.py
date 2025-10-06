import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat
from src.util.date import convert_norwegian_date_to_postgres

class RafisklagetSpider(scrapy.Spider):
    name = "rafisklagetspider"
    allowed_domains = ["rafisklaget.no"]
    start_urls = ["https://www.rafisklaget.no/nyheter"]

    def parse(self, response):
        articles = response.css('div.articles > *')
        for article in articles[:10]:
            title = article.css('a.defaultColor::text').get()
            if not title:
                continue
            title = title.strip()
            subtitle = article.css('p.description::text').get()
            url = article.css('a.defaultColor').attrib.get('href', '')

            full_url = f"https://www.rafisklaget.no{url}"
            message_id = full_url
            message_text = (
                f"*{title.strip()}*\n"
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på Norges Råfisklag sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://yt3.googleusercontent.com/ytc/AIdro_nNC6jSGKbdKThmuLkv4H3E-bI-8W-hVaz6etd1yfIzSnc=s900-c-k-c0x00ffffff-no-rj", "Norges Råfisklag")
            
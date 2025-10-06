import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

class SurofiSpider(scrapy.Spider):
    name = "surofispider"
    allowed_domains = ["surofi.no"]
    start_urls = ["https://www.surofi.no/nyheter-og-aktuelt"]

    def parse(self, response):
        articles = response.css('div.column-item._3-2-2-1.w-dyn-item')
        for article in articles[:10]:
            title = article.css("a::text").get()    
            if not title:
                continue
            title = title.strip()
            subtitle = article.css("p.paragraph-3-lines::text").get()
            url = article.css("a.text-button").attrib["href"]

            full_url = f"https://www.surofi.no{url}"
            message_id = full_url
            message_text = (
                f"*{title.strip()}*\n"
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på Surofi sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQFwN3j_9Cg4eoDz8NObe2BZlWCOZ0pYnNpVA&s", "Surofi")
            
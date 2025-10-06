import sys
import os
import hashlib
import logging
import scrapy
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

class BypakkealesundSpider(scrapy.Spider):
    name = "bypakkealesundspider"
    allowed_domains = ["bypakkealesund.no"]
    start_urls = ["https://www.bypakkealesund.no/aktuelt/"]

    def parse(self, response):
        articles = response.css('ol.ac-content-grid-list > *')
        for article in articles[:10]:
            title = article.css("span.ac-content-teaser-title-text::text").get()
            if not title:
                continue  
            title = title.strip()
            rel_url = article.css("a.ac-content-link.ac-content-teaser-title-link::attr(href)").get()
            full_url = response.urljoin(rel_url)

            subtitle = article.css("div.ac-content-teaser-excerpt::text").get()
            if subtitle:
                subtitle = subtitle.strip()

            message_id = full_url
            message_text = (
                f'*{title.strip()}*\n'
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på Bypakke Ålesund sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS96qcrLJLYqzW0ySrlMj6ku880ul4DFYt89A&s", "Bypakke Ålesund")

            

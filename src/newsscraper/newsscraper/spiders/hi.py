import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat
from src.util.date import convert_date_to_postgres

class HiSpider(scrapy.Spider):
    name = "hispider"
    allowed_domains = ["hi.no"]
    start_urls = ["https://www.hi.no/hi/nyheter"]

    def parse(self, response):
        articles = response.css('div.row.small-up-1.medium-up-3.large-up-3 > *')

        for article in articles[:10]:
            title = article.css('h3>a::text').get()
            if not title:
                continue
            title = title.strip()
            subtitle = article.css('div.teaser>p::text').get()
            url = article.css('a').attrib.get('href', '')

            message_id = url
            message_text = (
                f"*{title.strip()}*\n"
                f"{subtitle}\n\n"
                f"<{url}|Les mer på Havforskningsinstituttet sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://image.forskning.no/1201044.webp?imageId=1201044&x=0.00&y=0.00&cropw=100.00&croph=100.00&width=456&height=456&format=jpg", "Havforskningsinstituttet")

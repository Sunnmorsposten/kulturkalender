import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat
from src.util.date import convert_date_to_postgres

class SjomatnorgeSpider(scrapy.Spider):
    name = "sjomatnorgespider"
    allowed_domains = ["sjomatnorge.no"]
    start_urls = ["https://sjomatnorge.no/kategori/avdelinger/"]

    def parse(self, response):
        articles = response.css('div.news-row-outer > *')

        for article in articles[:10]:
            title = article.css('h3::text').get() or article.css('h3>a::text').get()
            if not title:
                continue
            title = title.strip()
            subtitle = article.css('div.news-banner-info>p::text').getall()
            url = article.css('a').attrib.get('href', '')

            subtitle = subtitle[1] if len(subtitle) > 1 else article.css('p::text').get()
            full_url = url if url.startswith("http") else f"https://sjomatnorge.no{url}"
            message_id = full_url
            message_text = (
                f"*{title.strip()}*\n"
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på SjømatNorge sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR3AzTRt1TAtp2X4Vws4GMVVPdzVDPRvOWNZg&s", "Sjømat Norge")

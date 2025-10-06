import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat
from src.util.date import convert_array_to_postgresql_date

class FiskebatSpider(scrapy.Spider):
    name = "fiskebatspider"
    allowed_domains = ["fiskebat.no"]
    start_urls = ["https://www.fiskebat.no/kategorier/nyheter"]

    def parse(self, response):
        articles = response.css("div[role='list'].grid-medium.w-dyn-items > *")
        for article in articles[:10]:
            articletype = article.css('div.badge::text').get()
            if articletype == "Ytringer":
                continue

            title = article.css('h4::text').get()
            if not title:
                continue
            title = title.strip()
            subtitle = article.css('div.text-block-3::text').get()
            url = article.css('a').attrib.get('href', '')

            full_url = f"https://fiskebat.no{url}"
            message_id = full_url
            message_text = (
                f"*{title.strip()}*\n"
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på Fiskebåt sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://cdn.prod.website-files.com/6308a0081a24641f86439830/6308d09158a86c45780f8d3d_logo_fiskebat_sirkel.png", "Fiskebåt")


import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from datetime import datetime
from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

class KystverketSpider(scrapy.Spider):
    name = "kystverketspider"
    allowed_domains = ["kystverket.no"]
    start_urls = ["https://www.kystverket.no/nyheter"]

    def parse(self, response):
        articles = response.css('div.card-list__item')

        for article in articles[:10]:
            title = article.css('h1 > a::text').get()
            if not title:
                continue
            title = title.strip()
            subtitle = article.css('div.card__content > p::text').get()
            url = article.css('h1 > a::attr(href)').get()

            full_url = f"https://kystverket.no{url}"
            message_id = full_url
            
            message_text = (
                f"*{title.strip()}* \n"
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på Kystverket sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://kommunikasjon.ntb.no/data/images/00203/6895a2bf-b0bd-4af9-bac4-96ec7bda0dd3-w_300_h_250.png", "Kystverket")
            
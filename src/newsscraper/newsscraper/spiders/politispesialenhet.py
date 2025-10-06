import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

class PolitispesialenhetSpider(scrapy.Spider):
    name = "politispesialenhetspider"
    allowed_domains = ["spesialenheten.no"]
    start_urls = ["https://www.spesialenheten.no/politidistrikt/more-og-romsdal/"]

    def parse(self, response):
        articles = response.css("article.entry-archive")
        for article in articles[:10]:
            title = article.css("h2.entry-title-archive a::text").get()
            if not title:
                continue  
            title = title.strip()
            rel_url = article.css("h2.entry-title-archive a::attr(href)").get()
            full_url = response.urljoin(rel_url)

            subtitle = article.css("div.entry-excerpt p::text").get()
            if subtitle:
                subtitle = subtitle.strip()

            message_id = full_url

            message_text = (
                f"*{title.strip()}*\n"
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på Spesialenheten sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://www.spesialenheten.no/wp-content/uploads/2020/07/spesialenheten-for-politisaker-logo-some.png", "Spesialenheten for politisaker")
            
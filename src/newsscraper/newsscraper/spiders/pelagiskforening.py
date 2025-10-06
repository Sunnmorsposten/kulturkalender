import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat
from src.util.date import convert_norwegian_date_to_postgres

class PelagiskForeningSpider(scrapy.Spider):
    name = "pelagiskforeningspider"
    allowed_domains = ["pelagisk.net"]
    start_urls = ["https://www.pelagisk.net/for-medlemmer/aktuelt"]

    def parse(self, response):
        articles = response.css('div.articleBox')

        for article in articles[:10]:
            title = article.css('h4 > a::text').get()
            if not title:
                continue
            title = title.strip()
            subtitle = article.css('div.articleText ::text').getall()
            url = article.css('div.articleImg > a').attrib.get('href', '')

            if subtitle:
                subtitle = ''.join(subtitle[1:-1])
                subtitle = ' '.join(subtitle.split()).replace('Les mer...', '').strip()

            full_url = f"https://pelagisk.net{url}"
            message_id = full_url
            message_text = (
                f"*{title.strip()}*\n"
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på Pelagisk Forening sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTsuCt3-Se3yqSRNWyXcPJEHur1ZpqYP8tNsQ&s", "Pelagisk Forening")

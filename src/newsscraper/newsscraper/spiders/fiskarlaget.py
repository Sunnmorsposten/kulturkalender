import sys
import os
import hashlib
import logging
import scrapy

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat
from src.util.date import convert_date_to_postgres

class FiskarlagetSpider(scrapy.Spider):
    name = "fiskarlagetspider"
    allowed_domains = ["fiskarlaget.no"]
    start_urls = ["https://www.fiskarlaget.no/artikler/nyheter"]

    def parse(self, response):
        articles = response.css('div.grid-margin-x.grid-x.grid-margin-y > *')

        for article in articles[:10]:
            title = article.css('h4::text').get()
            if not title:
                continue
            title = title.strip()
            subtitle = article.css('p:not([class])::text').get()
            group = article.css('p.lightblue::text').get()
            url = article.css('a.news::attr(href)').get()

            if group:
                group = group.strip()
            if subtitle:
                subtitle = f"{group}: {subtitle}" if group else subtitle

            full_url = f"https://www.fiskarlaget.no{url}"
            
            message_id = full_url
            message_text = (
                f"*{title.strip()}*\n"
                f"{subtitle}\n\n"
                f"<{full_url}|Les mer på Norges Fiskarlag sine sider.>"
            )
            send_slack_chat(message_id, message_text, "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQMDl_gfjK-w8SfaC_i3YvEBSi-5JuMM1mkmg&s", "Norges Fiskarlag")   
            

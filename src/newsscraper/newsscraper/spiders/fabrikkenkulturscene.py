import re
import sys
import os
import json
import logging
from datetime import datetime
from urllib.parse import urlparse
import scrapy

# Add project root to import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.services.send_slack_chat import send_slack_chat

class FabrikkenKultursceneSpider(scrapy.Spider):
    name = "fabrikkenkulturscene"
    allowed_domains = ["fabrikkenkulturscene.no", "www.fabrikkenkulturscene.no"]
    start_urls = ["https://www.fabrikkenkulturscene.no/program"]

    def parse(self, response):
        events = response.css("div.collection-item.w-dyn-item")

        for event in events:
            # Event URL
            rel_url = event.css("a.div-block-5::attr(href)").get()
            url = response.urljoin(rel_url)

            # Image
            image_url = event.css("a.image-wrapper img::attr(src)").get()
            if image_url:
                image_url = response.urljoin(image_url)

            # Title
            title = event.css("h3.card-heading.list::text").get()
            if title:
                title = title.strip()

            # Subtitle (excerpt)
            subtitle = event.css("p.card-excerpt::text").get()
            if subtitle:
                subtitle = subtitle.strip()

            # Date extraction from div.card-date
            date_parts = event.css(".card-date.white.list div::text").getall()
            date_str = "".join(date_parts).strip()  # e.g., "08.10.25"
            iso_date = self._parse_date(date_str)

            item = {
                "title": title,
                "subtitle": subtitle,
                "url": url,
                "image_url": image_url,
                "date": iso_date,
                "site": "Fabrikken Kulturscene",
            }

            message_id = url

            send_slack_chat(
                message_id=message_id,
                item=item,
                sender="Kulturkalender",
                icon_url="https://www.fabrikkenkulturscene.no/favicon.ico",
            )

            yield item

    def _parse_date(self, text: str) -> str:
        """
        Convert date format '08.10.25' to ISO format '2025-10-08:00:00:00'
        """
        if not text:
            return self._fallback_date()

        # Handle formats like 08.10.25 or 8.10.25
        m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", text)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year = int(m.group(3))
            # If year is two digits, assume 20xx
            if year < 100:
                year += 2000
            try:
                dt = datetime(year, month, day)
                return dt.strftime("%Y-%m-%d:%H:%M:%S")
            except ValueError:
                pass

        return self._fallback_date()

    def _fallback_date(self) -> str:
        """Return today's date as fallback"""
        dt = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.strftime("%Y-%m-%d:%H:%M:%S")

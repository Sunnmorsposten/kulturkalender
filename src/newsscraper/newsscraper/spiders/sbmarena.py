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

class sbmArenaSpider(scrapy.Spider):
    name = "sbmarenaspider"
    allowed_domains = ["sbmarena.no", "www.sbmarena.no"]
    start_urls = ["https://sbmarena.no/arrangement"]

    def parse(self, response):
        events = response.css("div.event.type-events")

        for event in events:
            # Event URL
            rel_url = event.css("a::attr(href)").get()
            url = response.urljoin(rel_url)

            # Image
            image_style = event.css("div.img::attr(style)").get()
            image_url = ""
            if image_style:
                match = re.search(r"url\((.*?)\)", image_style)
                if match:
                    image_url = response.urljoin(match.group(1))

            # Title
            title = event.css("div.title h3::text").get()
            if title:
                title = title.strip()

            # Subtitle (not available in this view)
            subtitle = ""

            # Date extraction
            date_str = event.css("span.date::text").get()
            iso_date = self._parse_date(date_str)

            item = {
                "title": title,
                "subtitle": subtitle,
                "url": url,
                "image_url": image_url,
                "date": iso_date,
                "site": "SBM Arena",
            }

            message_id = url

            print(f"→ {item['date']} | {item['title']} | {item['url']}")

            yield item

    def _parse_date(self, text: str) -> str:
        """
        Convert date format like '11.09 - 13.09.2026' or '08.10.25' to ISO format 'YYYY-MM-DD:HH:MM:SS'
        """
        if not text:
            return self._fallback_date()
        
        text = text.strip()

        # Handle range format '11.09 - 13.09.2026' -> use start date
        m_range = re.match(r"(\d{1,2})\.(\d{1,2})\s*-\s*\d{1,2}\.\d{1,2}\.(\d{2,4})", text)
        if m_range:
            day = int(m_range.group(1))
            month = int(m_range.group(2))
            year = int(m_range.group(3))
            if year < 100:
                year += 2000
            try:
                dt = datetime(year, month, day)
                return dt.strftime("%Y-%m-%d:%H:%M:%S")
            except ValueError:
                pass

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

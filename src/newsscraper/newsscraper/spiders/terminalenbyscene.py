import sys
import os
import re
import json
import hashlib
import logging
from datetime import datetime
import scrapy

# Add project root to import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.services.send_slack_chat import send_slack_chat


class TerminalenBysceneSpider(scrapy.Spider):
    name = "terminalenbyscenespider"
    allowed_domains = ["terminalenbyscene.no", "www.terminalenbyscene.no"]
    start_urls = ["https://terminalenbyscene.no/program"]

    MONTHS = {
        "jan": 1, "januar": 1,
        "feb": 2, "februar": 2,
        "mar": 3, "mars": 3,
        "apr": 4, "april": 4,
        "mai": 5,
        "jun": 6, "juni": 6,
        "jul": 7, "juli": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9,
        "okt": 10, "oktober": 10,
        "nov": 11, "november": 11,
        "des": 12, "desember": 12,
    }

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"Fetching start URL: {url}")
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        """
        Parse events from Terminalen Byscene (Squarespace layout)
        HTML pattern:
            <h2>Honningbarna</h2>
            <p>10. oktober 2025</p>
            <a href="https://tikkio.com/tickets/55913-honningbarna-terminalen">Billetter</a>
        """
        self.logger.info(f"Parsing {response.url}")

        # Each event is typically a block section with <h2>, <p> (date), and <a> (Billetter)
        blocks = response.css("div.fe-block")

        title, date_text, link = None, None, None

        for i, block in enumerate(blocks[:10]):
            h2 = block.css("h2::text").get()
            if h2:
                title = h2.strip()

            p_date = block.css("p.sqsrte-large::text").get()
            if p_date:
                date_text = p_date.strip()

            a = block.css("a[href*='tikkio.com']::attr(href)").get()
            if a:
                link = response.urljoin(a)
            
            # inside your per-event block/card loop (where `block` is a fe-block for that event)
            img = block.css("div.fluid-image-container > img::attr(src)").get()
            if img:
                image_url = response.urljoin(img)
            else:
                image_url = " "

            # If we have all three, we assume one event found
            if title and date_text and link:
                print(f"Found event {i} of 10")
                iso_date = self._to_iso_date(date_text)

                item = {
                    "title": title,
                    "subtitle": " ",
                    "url": link,
                    "image_url": image_url,
                    "date": iso_date,
                    "site": "Terminalen Byscene",
                }

                message_id = link

                send_slack_chat(
                    message_id=message_id,
                    item=item,
                    sender="Kulturkalender",
                    icon_url="https://terminalenbyscene.no/favicon.ico",
                )

                yield item

                # reset for next block
                title, date_text, link = None, None, None

    def _to_iso_date(self, text: str) -> str:
        """
        Convert Norwegian-style date '10. oktober 2025' -> '2025-10-10:00:00:00'
        """
        if not text:
            return self._fallback_date()

        text = text.strip()
        m = re.match(r"(\d{1,2})\.\s*([A-Za-zæøåÆØÅ]+)\s*(\d{4})?", text)
        if not m:
            return self._fallback_date()

        day = int(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3)) if m.group(3) else datetime.utcnow().year

        month = self.MONTHS.get(month_name)
        if not month:
            return self._fallback_date()

        try:
            dt = datetime(year, month, day, 0, 0, 0)
            return dt.strftime("%Y-%m-%d:%H:%M:%S")
        except ValueError:
            return self._fallback_date()

    def _fallback_date(self):
        dt = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.strftime("%Y-%m-%d:%H:%M:%S")

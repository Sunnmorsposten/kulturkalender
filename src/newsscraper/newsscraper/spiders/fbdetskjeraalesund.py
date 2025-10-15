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

#spider for facebookgroup id : 835724373149177

class DetSkjerAalesundSpider(scrapy.Spider):
    name = "detskjeraalesundspider"
    allowed_domains = ["smps3.ams3.cdn.digitaloceanspaces.com"]
    start_urls = ["https://smps3.ams3.cdn.digitaloceanspaces.com/kultur-data/835724373149177-events.html"]

    # Norwegian month name -> month number
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
        if not self.start_urls:
            self.logger.warning("start_urls is empty — no initial requests will be scheduled.")
        for url in self.start_urls:
            self.logger.info(f"[seed] scheduling: {url}")
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        """
        Extract event cards and emit normalized items in the requested format:
        {
            "title": "",
            "subtitle": "",
            "url": "",
            "date": "YYYY-MM-DD:HH:MM:SS",
            "site": ""
        }
        """
        self.logger.info(f"[parse] fetched {response.url} (status {response.status})")
        
        # Select all event divs
        events = response.css("div.events div.event")

        for event in events:
            # Title
            title = event.css("div.name::text").get()
            if not title:
                continue
            title = title.strip()

            # Subtitle (description)
            subtitle = event.css("div.description::text").get()
            subtitle = subtitle.strip() if subtitle else ""
            if len(subtitle) > 200: # A bit less than 255 to be safe
                subtitle = subtitle[:200] + "..."
            if not subtitle:
                subtitle = None
            # URL
            url = event.css("div.url a::attr(href)").get()
            if not url:
                continue
            url = url.strip()

            # Date (already in ISO format)
            iso_date = event.css("div.iso_date::text").get()
            if not iso_date:
                iso_date = iso_date.strip()




            # Site name
            site = "Facebook - Det Skjer i Ålesund"

            item = {
                "title": title,
                "subtitle": subtitle,
                "url": url,
                "date": iso_date,
                "site": site,
            }

            message_id = url

            send_slack_chat(
                message_id=message_id,
                item=item,
                sender="Kulturkalender",
                icon_url="https://static.xx.fbcdn.net/rsrc.php/y1/r/ay1hV6OlegS.ico",
            )


            yield item

    # ----------------------------
    # Helpers
    # ----------------------------
    def _get_year_from_data_month(self, data_month_attr: str) -> int | None:
        """
        data-month is a JSON array of slugs like ["november-2025"].
        Return int year if present, else None.
        """
        try:
            months = json.loads(data_month_attr)
            if months and isinstance(months, list):
                # take the first, split on '-', last part should be YYYY
                parts = str(months[0]).rsplit("-", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    return int(parts[1])
        except Exception:
            pass
        return None

    def _to_iso_start_date(self, text: str, year_hint: int | None) -> str:
        """
        Normalize date string to "YYYY-MM-DD:HH:MM:SS".
        The site sometimes shows ranges ("14. nov – 15. nov") or single dates ("8. okt 2025").
        We take the START date of the range.
        If the year is missing, we use year_hint (from data-month).
        Time is not present on the page -> "00:00:00".
        """
        if not text:
            return self._fallback_date()

        # Replace different dashes with a simple hyphen for easier parsing
        normalized = text.replace("–", "-").replace("—", "-").strip()

        # Split range on hyphen. Left part is the start date.
        start_part = normalized.split("-", 1)[0].strip()

        # Examples to match:
        # "8. okt 2025"
        # "24. okt 2025" (standard)
        # "14. nov" (year omitted)
        # "6. mar"  (year omitted)
        m = re.match(r"^\s*(\d{1,2})\.\s*([A-Za-zæøåÆØÅ]+)\s*(\d{4})?\s*$", start_part)
        if not m:
            # Some rows may show "14. nov – 15. nov" with spaces: still handled above.
            # If completely unparseable, return fallback.
            return self._fallback_date()

        day = int(m.group(1))
        month_name = m.group(2).strip().lower()
        year_str = m.group(3)

        month = self.MONTHS.get(month_name)
        if not month:
            return self._fallback_date()

        if year_str and year_str.isdigit():
            year = int(year_str)
        else:
            # No year in the start part: use hint (from data-month).
            year = year_hint if year_hint else datetime.utcnow().year

        try:
            dt = datetime(year, month, day, 0, 0, 0)
            return dt.strftime("%Y-%m-%d:%H:%M:%S")
        except ValueError:
            # Invalid date (e.g., "31. nov"). Safeguard:
            return self._fallback_date()

    def _fallback_date(self) -> str:
        """
        If we can't parse, set date to today's date at 00:00:00 UTC to avoid blank fields.
        """
        dt = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.strftime("%Y-%m-%d:%H:%M:%S")
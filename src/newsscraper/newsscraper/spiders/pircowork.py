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


class PirCoworkSpider(scrapy.Spider):
    name = "pircoworkspider"
    allowed_domains = ["pirwork.no", "www.pirwork.no"]
    start_urls = ["https://www.pirwork.no/en/calendar/"]

    # English month -> month number
    MONTHS = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    def parse(self, response):
        """
        Extract events from the calendar page.
        Structure:
          .month-wrapper
            span.arrangement-month -> Month label (English)
            .arrangement-day (N per month)
              h1.title
              .time-and-place span elements:
                 [0] => "Wednesday, October 15"
                 [1] => " 16 - 23"      (may be missing)
                 [2] => "Venue"         (optional)
              p.ingress (subtitle/description)
              .flex-image img[src] (image)
              a.btn-primary[href] (external "read more / signup" link; optional)
        """
        page_url = response.url

        # Iterate each visible month section
        for mw in response.css(".month-wrapper"):
            month_label = (mw.css(".arrangement-month::text").get() or "").strip()

            for day in mw.css(".arrangement-day"):
                title = (day.css("h1.title::text").get() or "").strip()
                if not title:
                    continue

                # Description as subtitle
                subtitle = (day.css("p.ingress::text").get() or "").strip()

                # Time/Date/Place spans
                spans = [s.strip() for s in day.css(".time-and-place span::text").getall() if s.strip()]
                date_text = spans[0] if spans else ""
                time_text = spans[1] if len(spans) > 1 else ""
                # place not used directly, but you could append to subtitle if desired
                # place = spans[2] if len(spans) > 2 else ""

                # External URL if provided, else fall back to the calendar page
                ext_url = day.css("a.btn-primary::attr(href)").get()
                url = response.urljoin(ext_url) if ext_url else page_url

                # Image URL
                image_url = day.css(".flex-image img::attr(src)").get()
                if image_url:
                    image_url = response.urljoin(image_url)

                # Parse ISO date (start of event)
                iso_date = self._to_iso(date_text, time_text)

                item = {
                    "title": title[:255],
                    "subtitle": subtitle[:255],
                    "url": url[:255],
                    "image_url": image_url,
                    "date": iso_date,
                    "site": "Pir Cowork",
                }

                message_id = f"pircowork-{iso_date}-{title}"

                send_slack_chat(
                    message_id=message_id,
                    item=item,
                    sender="Kulturkalender",
                    icon_url="https://www.pirwork.no/favicon.ico",
                )

                yield item

    # ----------------------------
    # Helpers
    # ----------------------------
    def _to_iso(self, date_text: str, time_text: str) -> str:
        """
        Convert:
          date_text like "Wednesday, October 15" or "Thursday, November 27"
          time_text like "08 - 10" or "16 - 23" (optional)
        to "YYYY-MM-DD:HH:MM:SS"
        Year is inferred:
          - Prefer current year (UTC); if month/day already passed this year by > 9 months,
            still keep current year (these are curated future events on the page).
        """
        if not date_text:
            return self._fallback_date()

        # Remove weekday + comma if present
        # e.g. "Wednesday, October 15" -> "October 15"
        date_text = date_text.strip()
        date_text = re.sub(r"^[A-Za-z]+,\s*", "", date_text)

        # Extract month/day (English month names)
        # "October 15" or "Nov 9"
        m = re.match(r"^\s*([A-Za-z]+)\s+(\d{1,2})\s*$", date_text)
        if not m:
            return self._fallback_date()

        month_name = m.group(1).strip().lower()
        day = int(m.group(2))
        month = self.MONTHS.get(month_name)
        if not month:
            return self._fallback_date()

        # Parse start hour from time_text if present
        # "08 - 10" -> 8, "16 - 23" -> 16
        hour = 0
        minute = 0
        if time_text:
            t = time_text.strip()
            t = t.replace("–", "-").replace("—", "-")
            mtime = re.match(r"^\s*(\d{1,2})(?::(\d{2}))?\s*-\s*\d{1,2}(?::\d{2})?\s*$", t)
            if mtime:
                hour = int(mtime.group(1))
                minute = int(mtime.group(2) or "0")

        # Year guess: default current year
        now = datetime.utcnow()
        year = now.year

        # Build datetime safely
        try:
            dt = datetime(year, month, day, hour, minute, 0)
        except ValueError:
            return self._fallback_date()

        return dt.strftime("%Y-%m-%d:%H:%M:%S")

    def _fallback_date(self) -> str:
        dt = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.strftime("%Y-%m-%d:%H:%M:%S")

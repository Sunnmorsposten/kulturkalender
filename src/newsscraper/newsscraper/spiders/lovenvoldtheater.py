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

class LovenvoldTheaterSpider(scrapy.Spider):
    """
    Generic spider for Squarespace-style event lists (like the HTML snippet you provided).
    Usage:
        scrapy crawl lovenvoldtheaterspider -a start_url="https://example.com/events/"
    """
    name = "lovenvoldtheaterspider"
    allowed_domains = ["lovenvoldtheater.no", "www.lovenvoldtheater.no"]
    start_urls = ["https://lovenvoldtheater.no/scene"]
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
    }

    # Norwegian month names/abbreviations -> month number
    MONTHS = {
        "jan": 1, "januar": 1,
        "feb": 2, "februar": 2,
        "mar": 3, "mars": 3,
        "apr": 4, "april": 4,
        "mai": 5,
        "jun": 6, "juni": 6,
        "jul": 7, "juli": 7,
        "aug": 8, "august": 8,
        "sep": 9, "sept": 9, "september": 9,
        "okt": 10, "oktober": 10,
        "nov": 11, "november": 11,
        "des": 12, "desember": 12,
    }

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # Try to improve site label from <title>
        site_from_title = (response.css("title::text").get() or "").strip()
        if site_from_title:
            # keep it short-ish
            self._site_label = site_from_title.split("—")[0].split("|")[0].split(" • ")[0].strip() or self._site_label

        # Squarespace list items
        cards = response.css('li.list-item[data-is-card-enabled="true"]')
        self.logger.info(f"[parse] found {len(cards)} event-like list items on {response.url}")

        for card in cards:
            # Title
            title = card.css("h2.list-item-content__title::text").get()
            if not title:
                # sometimes wrapped in <a> or spans, fall back to text() of h2
                title = (card.css("h2.list-item-content__title *::text").get() or "").strip()
            if not title:
                continue
            title = title.strip()

            # Subtitle: take the category before "/" in description line, e.g., "Standup /"
            desc_text = " ".join([t.strip() for t in card.css(".list-item-content__description *::text").getall() if t.strip()])
            # Common patterns: "Standup / 17. oktober", "Konsert / 29. november", "Show / 30. okt - 20. des", "Show / Ekstra i november"
            subtitle = ""
            m_sub = re.search(r"^\s*([A-Za-zÆØÅæøå]+)\s*/", desc_text)
            if m_sub:
                subtitle = m_sub.group(1).strip()

            # Date string (usually inside <strong>)
            raw_date = ""
            strongs = [s.strip() for s in card.css(".list-item-content__description strong::text").getall() if s.strip()]
            if strongs:
                raw_date = strongs[0]
            else:
                # fallback if no <strong>
                # try to grab after slash
                m_dt = re.search(r"/\s*(.+)$", desc_text)
                raw_date = m_dt.group(1).strip() if m_dt else ""

            # Year hints: from surrounding text/title/href
            year_hints = self._extract_year_hints(text=" ".join([title, desc_text]))
            # URL
            rel_url = card.css(".list-item-content__button a::attr(href), a.list-item-content__button::attr(href)").get()
            url = response.urljoin(rel_url) if rel_url else response.url
            # add year hint from slug if present
            year_hints.update(self._extract_year_hints(text=url))

            # Image
            image_url = card.css(".list-item-media img::attr(src), .list-item-media img::attr(data-src)").get()
            if image_url:
                image_url = response.urljoin(image_url)

            iso_date = self._to_iso_start_date(raw_date, year_hints)

            item = {
                "title": title,
                "subtitle": subtitle,
                "url": url,
                "image_url": image_url,
                "date": iso_date,
                "site": "Løvenvold Teater Scene",
            }

            message_id = url

            send_slack_chat(
                message_id=message_id,
                item=item,
                sender="Kulturkalender",
                icon_url="https://images.squarespace-cdn.com/content/v1/63da264305cd2849258b5165/d0e873c7-c247-4af8-8eea-09023b8175e6/l%C3%B8venvold_logo_symbol_brun.png",
            )

            yield item

    # ----------------------------
    # Helpers
    # ----------------------------
    def _hostname_to_label(self, host: str) -> str:
        if not host:
            return "Ukjent nettsted"
        host = host.lower()
        if host.startswith("www."):
            host = host[4:]
        base = host.split(":")[0].split("/")[0]
        return base

    def _extract_year_hints(self, text: str) -> set[int]:
        hints = set()
        for y in re.findall(r"(20\d{2})", text or ""):
            try:
                hints.add(int(y))
            except Exception:
                pass
        return hints

    def _to_iso_start_date(self, raw: str, year_hints: set[int]) -> str:
        """
        Normalize many Norwegian date shapes to 'YYYY-MM-DD:HH:MM:SS'.
        Examples supported:
          - '17. oktober'
          - '23. - 25. oktober'
          - '30. okt - 20. des'
          - '29. november 2025'
          - 'Ekstra i november' (defaults to 1st of that month)
        Strategy:
          - If it's a range, take the START date.
          - If year missing, try from year_hints else current year (UTC).
          - Time not provided -> 00:00:00
        """
        if not raw:
            return self._fallback_date()

        txt = raw.strip()
        txt = txt.replace("–", "-").replace("—", "-")
        txt = re.sub(r"\s{2,}", " ", txt)

        # RANGE: "23. - 25. oktober" or "30. okt - 20. des [2025]"
        m_range = re.match(
            r"^\s*(\d{1,2})\.\s*([A-Za-zÆØÅæøå]+)?\s*-\s*(\d{1,2})\.\s*([A-Za-zÆØÅæøå]+)\s*(\d{4})?\s*$",
            txt,
            flags=re.IGNORECASE,
        )
        if m_range:
            day1 = int(m_range.group(1))
            month1_name = (m_range.group(2) or "").strip().lower()
            day2 = int(m_range.group(3))
            month2_name = (m_range.group(4) or "").strip().lower()
            year_str = m_range.group(5)

            # If first month missing, use second month
            month_name = month1_name or month2_name
            month = self.MONTHS.get(month_name, None)
            year = int(year_str) if (year_str and year_str.isdigit()) else self._pick_year(year_hints)

            if month:
                return self._safe_dt(year, month, day1)

        # SINGLE: "17. oktober" or "29. november 2025" or "30. okt"
        m_single = re.match(
            r"^\s*(\d{1,2})\.\s*([A-Za-zÆØÅæøå]+)\s*(\d{4})?\s*$",
            txt,
            flags=re.IGNORECASE,
        )
        if m_single:
            day = int(m_single.group(1))
            month_name = (m_single.group(2) or "").strip().lower()
            month = self.MONTHS.get(month_name, None)
            year = int(m_single.group(3)) if (m_single.group(3) and m_single.group(3).isdigit()) else self._pick_year(year_hints)
            if month:
                return self._safe_dt(year, month, day)

        # MONTH ONLY phrases like "Ekstra i november" / "i november"
        m_month_only = re.search(r"(?:ekstra\s+i|i)\s+([A-Za-zÆØÅæøå]+)", txt, flags=re.IGNORECASE)
        if m_month_only:
            month_name = m_month_only.group(1).strip().lower()
            month = self.MONTHS.get(month_name, None)
            year = self._pick_year(year_hints)
            if month:
                return self._safe_dt(year, month, 1)

        # Last resort: if there's exactly a month name, treat as 1st of that month
        for name, num in self.MONTHS.items():
            if re.fullmatch(rf"\s*{re.escape(name)}\s*", txt, flags=re.IGNORECASE):
                return self._safe_dt(self._pick_year(year_hints), num, 1)

        # Unrecognized -> fallback
        return self._fallback_date()

    def _pick_year(self, year_hints: set[int]) -> int:
        """
        Choose a year:
          - If year_hints contains any year >= current_year, choose the smallest such.
          - Else if year_hints contains any year < current_year, choose the largest such.
          - Else default to current UTC year.
        """
        now_y = datetime.utcnow().year
        futureish = sorted([y for y in year_hints if y >= now_y])
        if futureish:
            return futureish[0]
        past = sorted([y for y in year_hints if y < now_y], reverse=True)
        if past:
            return past[0]
        return now_y

    def _safe_dt(self, year: int, month: int, day: int) -> str:
        try:
            dt = datetime(year, month, day, 0, 0, 0)
            return dt.strftime("%Y-%m-%d:%H:%M:%S")
        except ValueError:
            return self._fallback_date()

    def _fallback_date(self) -> str:
        dt = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.strftime("%Y-%m-%d:%H:%M:%S")

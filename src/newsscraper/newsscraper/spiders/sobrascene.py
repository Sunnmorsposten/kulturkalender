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

class SobrasceneSpider(scrapy.Spider):
    name = "sobrascenespider"
    allowed_domains = ["sobrascene.no", "www.sobrascene.no"]
    start_urls = ["https://www.sobrascene.no/program/"]
    event_details_url = "https://www.sobrascene.no/event-details/"

    # English month -> month number
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


    def parse(self, response):
        script_content = response.xpath('//script[contains(@id, "wix-warmup-data")]/text()').get()

        if not script_content:
            self.logger.warning(f"Could not find the 'wix-warmup-data' script tag on {response.url}")
            return

        try:
            data = json.loads(script_content)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to decode JSON from script tag on {response.url}")
            return

        # The events are under appsWarmupData -> <dynamic_id> -> <some_other_key> -> events -> events
        # We need to search for the 'events' list.
        events_list = []
        apps_warmup_data = data.get('appsWarmupData', {})
        for app_data in apps_warmup_data.values():
            if isinstance(app_data, dict):
                for inner_data in app_data.values():
                    if isinstance(inner_data, dict) and 'events' in inner_data and 'events' in inner_data['events']:
                        events_list = inner_data['events']['events']
                        break
            if events_list:
                break
        
        if not events_list:
            # Fallback to the 'platform' structure if 'appsWarmupData' fails
            events_list = data.get('platform', {}).get('events', {}).get('events', [])

        if not events_list:
            self.logger.warning(f"Could not find events list on {response.url}")
            return

        for event in events_list:
            title = event.get('title', 'No title').strip()
            subtitle = event.get('description', '').strip()
            image_url = event.get('mainImage', {}).get('url', '')
            slug = event.get('slug')
            url = self.event_details_url + slug if slug else ''
            
            start_date = event.get('scheduling', {}).get('config', {}).get('startDate')
            iso_date = self._to_iso(start_date)
            
            item = {
                "title": title,
                "subtitle": subtitle,
                "url": url,
                "image_url": image_url,
                "date": iso_date,
                "site": "Sobra Scene",
            }

            message_id = url

            send_slack_chat(
                message_id=message_id,
                item=item,
                sender="Kulturkalender",
                icon_url="https://static.wixstatic.com/media/96047c_14706cd160454a26b00b58bd711e05d9%7Emv2.jpeg/v1/fill/w_192%2Ch_192%2Clg_1%2Cusm_0.66_1.00_0.01/96047c_14706cd160454a26b00b58bd711e05d9%7Emv2.jpeg",
            )

            yield item


    # ----------------------------
    # Helpers
    # ----------------------------
    def _to_iso(self, date_text: str, time_text: str = None) -> str:
        """
        Convert a date string to "YYYY-MM-DD:HH:MM:SS".
        Handles ISO 8601 format like "2024-09-13T19:00:00.000Z"
        and older formats like date_text="October 15", time_text="19:00".
        """
        if not date_text:
            return self._fallback_date()

        # Handle ISO 8601 format
        if 'T' in date_text and 'Z' in date_text:
            try:
                dt = datetime.fromisoformat(date_text.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d:%H:%M:%S")
            except ValueError:
                return self._fallback_date()

        # Fallback to original implementation for other formats
        date_text = date_text.strip()
        date_text = re.sub(r"^[A-Za-z]+,\s*", "", date_text)

        m = re.match(r"^\s*([A-Za-z]+)\s+(\d{1,2})\s*$", date_text)
        if not m:
            return self._fallback_date()

        month_name = m.group(1).strip().lower()
        day = int(m.group(2))
        month = self.MONTHS.get(month_name)
        if not month:
            return self._fallback_date()

        hour = 0
        minute = 0
        if time_text:
            t = time_text.strip()
            t = t.replace("–", "-").replace("—", "-")
            mtime = re.match(r"^\s*(\d{1,2})(?::(\d{2}))?", t)
            if mtime:
                hour = int(mtime.group(1))
                minute = int(mtime.group(2) or "0")

        now = datetime.utcnow()
        year = now.year

        try:
            dt = datetime(year, month, day, hour, minute, 0)
        except ValueError:
            return self._fallback_date()

        return dt.strftime("%Y-%m-%d:%H:%M:%S")

    def _fallback_date(self) -> str:
        dt = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return dt.strftime("%Y-%m-%d:%H:%M:%S")

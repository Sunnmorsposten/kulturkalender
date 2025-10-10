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


class AlesundBibliotekaSpider(scrapy.Spider):
    name = "alesundsbibliotekaspider"
    allowed_domains = ["alesundsbiblioteka.no"]
    start_urls = ["https://alesundsbiblioteka.no/kva-skjer/kalender/"]
    api_url = "https://alesundsbiblioteka.no/api/presentation/v2/filtervisning/"
    api_end_of_url = "/init?date=upcoming&kategori=79&deviceType=desktop"
    data_filter_identifier = None #     <div class="client-content-widget client-content-widget--filtervisning client-content-widget--filtervisning--kalender js-filtervisning" data-filter-identifier="36HGAkuMJkAKnwqomAIPOdKa1wicVPGabYnApcble0ylS_cFsLSEhZY_iFws_NQr" data-use-query-params="true"><!-- --></div>

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
            yield scrapy.Request(
                url,
                callback=self.parse,      # <- this now does the real parsing
                errback=self.errback,
                dont_filter=True,
            )

    async def parse(self, response, **kwargs):

        self.data_filter_identifier = response.css('div.js-filtervisning::attr(data-filter-identifier)').get()

        if self.data_filter_identifier:
            api_url = f"{self.api_url}{self.data_filter_identifier}{self.api_end_of_url}"
            yield scrapy.Request(api_url, callback=self.parse_api)
        else:
            self.logger.error("Could not find data-filter-identifier")


    def parse_api(self, response):
        data = response.json()
        items = data.get("content", {}).get("body", {}).get("result", {}).get("items", [])
        self.logger.info(f"Got {len(items)} items from API")

        for item in items:
            content_html = item.get('content', '')
            if not content_html:
                continue

            selector = scrapy.Selector(text=content_html)

            # Clean up whitespace and join text parts
            def clean_text(nodes):
                return ' '.join(node.strip() for node in nodes if node.strip())

            title = clean_text(selector.css('.cc-teaser-title-text ::text').getall())
            url = selector.css('.cc-teaser-title a::attr(href)').get()
            full_url = response.urljoin(url) if url else None
            date_text = clean_text(selector.css('.cc-teaser-meta-item--date .cc-teaser-meta-item-value-content ::text').getall()) #  'date': 'Onsdag 5. november 2025'
            time_text = clean_text(selector.css('.cc-teaser-meta-item--time .cc-teaser-meta-item-value-content ::text').getall()) # 'time': 'kl. 18:00 - 19:00'
            #location_text = clean_text(selector.css('.cc-teaser-meta-item--location .cc-teaser-meta-item-value-content ::text').getall())
            image_url = selector.css('.cc-teaser-image-content img::attr(src)').get()
            
            iso_date = self._parse_isodate(date_text, time_text)

            item = {
                "title": title,
                "subtitle": None,
                "url": full_url,
                "image_url": image_url,
                "date": iso_date,
                "site": "Ålesund Biblioteka"
            }


            message_id = full_url

            send_slack_chat(
                message_id=message_id,
                item=item,
                sender="Kulturkalender",
                icon_url="https://alesund.kommune.no/kunde/favicon.ico",
            )

            yield item



    async def errback(self, failure):
        self.logger.error(f"Request failed: {failure}")

    def _parse_isodate(self, date_text, time_text):
        if not date_text:
            return None

        # Handle date ranges, take the first date
        start_date_str = date_text.split(' - ')[0].strip()

        # Extract time, take the first time
        start_time_str = "00:00"
        if time_text:
            time_match = re.search(r'(\d{2}:\d{2})', time_text)
            if time_match:
                start_time_str = time_match.group(1)

        hour, minute = map(int, start_time_str.split(':'))

        # Extract date parts
        date_parts = start_date_str.split()
        if len(date_parts) < 3:
            return None # Not enough parts to form a date

        try:
            # Assuming format like "Måndag 6. oktober 2025"
            day = int(re.sub(r'\D', '', date_parts[1]))
            month_str = date_parts[2].lower()
            month = self.MONTHS.get(month_str)
            year = int(date_parts[3])

            if month:
                dt_object = datetime(year, month, day, hour, minute)
                return dt_object.isoformat()
        except (ValueError, IndexError) as e:
            self.logger.warning(f"Could not parse date: '{date_text}' with time '{time_text}'. Error: {e}")

        return None
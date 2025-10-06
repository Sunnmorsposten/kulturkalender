# helpers/slack_blocks.py
from typing import List, Dict, Any

from src.util.date import convert_iso_date_to_norwegian_date

def build_event_blocks(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build a Slack Block Kit payload for a Kulturkalender event.

    Expected item keys:
      - site, date, title, subtitle, url
      - image_url (optional, but recommended)
      - calendar_url (optional; defaults to item['url'])

    Returns a list suitable for Slack's chat_postMessage(blocks=...).
    """
    site        = item.get("site", " ")
    date        = item.get("date", " ")
    title       = item.get("title", " ")
    subtitle    = item.get("subtitle", " ")
    url         = item.get("url", " ")
    image_url   = item.get("image_url", " ")

    formatted_date = convert_iso_date_to_norwegian_date(date)

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Nytt arrangement!*\n\n*Hvor:* {site}\n*Når:* {formatted_date}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}*\n{subtitle}\n\n",
            },
            "accessory": {
                "type": "image",
                "image_url": image_url,
                "alt_text": title or "Arrangement",
            },
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Mer om arrangementet"},
                    "url": url,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Se hele kulturkalenderen"},
                    "url": "https://toolbox-app-4q5rr.ondigitalocean.app/",
                },
            ],
        },
    ]
    return blocks

import sys
import os
import hashlib
import logging
import scrapy
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat
from src.services.nff.insert_to_s3 import insert_to_s3

class NffovergangerSpider(scrapy.Spider):
    name = "nffovergangerspider"
    allowed_domains = ["fotball.no"]
    start_urls = [
        "https://www.fotball.no/lov-og-reglement/overganger/sok-overganger/?districtId=17&atomic=True"
    ]

    def parse(self, response):
        rows = response.css("table tbody tr")

        for row in rows[:10]:
            player_name = row.css("td:nth-child(1) a::text").get()
            from_club   = row.css("td:nth-child(5) a::text").get() or row.css("td:nth-child(5) ::text").get()
            to_club     = row.css("td:nth-child(6) a::text").get() or row.css("td:nth-child(6) ::text").get()

            if not player_name or not from_club or not to_club:
                continue

            from_club = from_club.strip()
            to_club = to_club.strip()

            # Extract additional fields as needed:
            godkjent   = row.css("td:nth-child(2)::text").get() or ""
            spilleklar = row.css("td:nth-child(3)::text").get() or ""
            sakstype   = row.css("td:nth-child(4)::text").get() or ""
            overgangstype = row.css("td:nth-child(7)::text").get() or ""
            kategori   = row.css("td:nth-child(8) span::text").get() or ""

            # Construct the full_url for 'Les mer'
            rel_url = row.css("td:nth-child(1) a::attr(href)").get()
            full_url = response.urljoin(rel_url) if rel_url else ""

            # Construct blocks for Slack
            blocks = self.build_transfer_blocks(
                player_name=player_name,
                from_club=from_club,
                to_club=to_club,
                godkjent=godkjent,
                spilleklar=spilleklar,
                sakstype=sakstype,
                overgangstype=overgangstype,
                kategori=kategori,
                full_url=full_url
            )

            # Fallback text for older Slack clients or notifications:
            fallback_text = (
                f"Ny overgang!\n"
                f"Spiller: {player_name}\n"
                f"Fra {from_club} til {to_club}\n"
                f"Godkjent: {godkjent}\n"
                f"Spilleklar: {spilleklar}\n"
                f"Sakstype: {sakstype}\n"
                f"Type: {overgangstype}\n"
                f"Kategori: {kategori}\n"
                f"Les mer: {full_url}\n"
                f"Se alle overganger: https://www.fotball.no/lov-og-reglement/overganger/sok-overganger/?districtId=17&atomic=True"
            )

            player = {
                "player_name": player_name,
                "from_club": from_club,
                "to_club": to_club,
                "godkjent": godkjent.strip(),
                "spilleklar": spilleklar.strip(),
                "sakstype": sakstype.strip(),
                "overgangstype": overgangstype.strip(),
                "kategori": kategori.strip(),
                "full_url": full_url,
            }

            message_id = f"{player_name.replace(' ', '_')}_{from_club.replace(' ', '_')}_{to_club.replace(' ', '_')}"

            insert_to_s3(
                message_id=message_id,
                player=player,
            )

            send_slack_chat(
                message_id=message_id,
                message=fallback_text, 
                icon_url="https://no-fotball.s2s.net/data/uimages/2021/02/16/1de00c.png",
                username="Sunnmøre Fotballkrets (overganger)",
                blocks=blocks,
            )

    def build_transfer_blocks(
        self,
        player_name,
        from_club,
        to_club,
        godkjent,
        spilleklar,
        sakstype,
        overgangstype,
        kategori,
        full_url
    ):
        """
        Build the Slack block structure. 
        From and To are placed side-by-side, along with other details below.
        """
        # Buttons for 'Les mer' and 'Se alle overganger'
        actions = [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Les mer om overgangen",
                    "emoji": True
                },
                "url": full_url if full_url else None,
                "value": "les_mer_overgangen"
            },
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Se alle overganger",
                    "emoji": True
                },
                "url": "https://www.fotball.no/lov-og-reglement/overganger/sok-overganger/?districtId=17&atomic=True",
                "value": "se_alle_overganger"
            }
        ]

        # Build fields for the second block
        fields = [
            {
                "type": "mrkdwn",
                "text": f"*Fra:*\n{from_club}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Til:*\n{to_club}"
            }
        ]

        if godkjent.strip():
            fields.append({
                "type": "mrkdwn",
                "text": f"*Godkjent:*{godkjent}"
            })

        if spilleklar.strip():
            fields.append({
                "type": "mrkdwn",
                "text": f"*Spilleklar:*{spilleklar}"
            })

        if sakstype.strip():
            fields.append({
                "type": "mrkdwn",
                "text": f"*Sakstype:*{sakstype}"
            })

        if overgangstype.strip():
            fields.append({
                "type": "mrkdwn",
                "text": f"*Type:*\n{overgangstype}"
            })

        if kategori.strip():
            fields.append({
                "type": "mrkdwn",
                "text": f"*Kategori:*\n{kategori}"
            })

        # Combine everything into blocks
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🤝 *Ny overgang!*\nSpiller: {player_name}"
                }
            },
            {
                "type": "section",
                "fields": fields
            },
            {
                "type": "actions",
                "elements": actions
            }
        ]

        return blocks

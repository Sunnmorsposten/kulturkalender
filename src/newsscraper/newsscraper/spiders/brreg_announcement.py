import sys
import os
import hashlib
import logging
import scrapy
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from src.clients.pg import conn 
from src.clients.slack import app

class BrregSpider(scrapy.Spider):
    name = "brregspider"
    allowed_domains = ["w2.brreg.no"]

    def start_requests(self):
        today = datetime.now().strftime("%d.%m.%Y")
        base = (
            "https://w2.brreg.no/kunngjoring/kombisok.jsp"
            f"?datoFra={today}&datoTil={today}"
            "&id_fylke=-+-+-&id_niva1=1&id_bransje1=0"
        )

        # iterate over 100, 200, …, 600
        for region in range(100, 601, 100):
            url = f"{base}&id_region={region}"
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        rows = response.css("table.normal-br-link tr")
        today = datetime.now().strftime("%d.%m.%Y")
        for i, row in enumerate(rows):
            name = row.css("td:nth-child(2) p::text").get()
            orgnr = row.css("td:nth-child(4)::text").get()
            action_text = row.css("td:nth-child(6) a::text").get()
            rel_url = row.css("td:nth-child(6) a::attr(href)").get()
            full_url = response.urljoin(rel_url) if rel_url else ""
            if not name or not orgnr or not action_text or not full_url:
                continue

            orgnr = orgnr.strip()
            orgnr = orgnr.replace(" ", "")

            title = f"{name.strip()} ({orgnr.strip()})"
            description = action_text.strip()
            url = full_url

            message_text = (
                f"Selskap: *{title}*\n"
                f"Endringstype: {description}\n\n"
                f"<{url}|Les mer>"
            )
            blocks = self.build_blocks(title, description, url, orgnr)
            message_id = f"BRREG - {orgnr} - {name.strip()} - {today} - {action_text.strip()}"
            username = f"BRREG - {orgnr} - {name.strip()}"
            
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT channel FROM nyhetsjegersubs WHERE newssource = %s",
                        (username,),
                    )
                    channels = [row[0] for row in cur.fetchall()]
                    
                    if not channels:
                        continue
                    
                    cur.execute(
                        """
                        INSERT INTO nyhetsjegerid (id)
                        VALUES (%s)
                        ON CONFLICT DO NOTHING
                        RETURNING id
                        """,
                        (message_id,),
                    )
                    
                    if cur.fetchone() is None:     # row already existed
                        continue
                    
            
                    for channel in channels:
                        app.client.chat_postMessage(
                            channel=channel,
                            text=message_text,
                            blocks=blocks,
                            icon_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSq3xQmpMDQBk3x5jeYmPOQPUjUjOKtP7v_VQ&s",
                            username="Brønnøysundregistrene",
                        )

    def build_blocks(self, title, description, url, orgnr):
        return [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": f"🔔 Kunngjøring fra selskap.\n\n Selskap: *{title}*\n Org nr: *{orgnr}*\nEndring: *{description}*"
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Se kunngjøringen"
					},
					"url": url,
					"value": "les_mer_link"
				},
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Se Proff.no-side"
					},
					"url": f"https://www.proff.no/bransjes%C3%B8k?q={orgnr}",
					"value": "proff_link"
				}
			]
		}
	]

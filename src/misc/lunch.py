import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.clients.slack import app
from src.clients.pg import conn  

async def send_lunch_message():
    blocks = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "🚨 *Husk å bestille lunsj!*"
			}
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "button",
					"text": {
						"type": "plain_text",
						"text": "Trykk her for å bestille lunsj",
						"emoji": True
					},
					"value": "bestill_lunsj",
					"url": "https://dampsentralenbedrift.munu.shop/"
				}
			]
		},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "@channel"
            }
		}	
    ]
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT channel FROM nyhetsjegersubs WHERE newssource = %s",
                ("Lunsjpåminnelse",),
            )
            channels = [row[0] for row in cur.fetchall()]

    for channel in channels:
        app.client.chat_postMessage(
            channel=channel,
            text="🚨 *Husk å bestille lunsj!*",
            blocks=blocks,
            icon_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRN6nlDDHYEj_dmjqR73gY7IweBnVs7O1HrZA&s",
            username="Lunsjpåminnelse"
		)

if __name__ == "__main__":
    asyncio.run(send_lunch_message())
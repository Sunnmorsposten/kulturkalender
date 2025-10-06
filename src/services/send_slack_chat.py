import os
import sys
from psycopg2 import sql


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.clients.slack import app
from src.clients.pg import conn   # psycopg2 connection object
from src.util.slack import build_event_blocks

def send_slack_chat(
    message_id: str,
    item: dict,
    sender: str,
    icon_url: str,
) -> bool:
    """
    Send a Slack message to every channel that subscribes to `username`, **once per
    `message_id`**:

    • Reserve `message_id` in PostgreSQL (table `nyhetsjegerid`); if the row
      already exists, nothing is sent.
    • On first use of the id, forward the message and insert the id atomically.

    Returns
    -------
    bool
        True  – message sent  
        False – message had already been sent earlier
    """
    with conn:                       # <-- commits automatically on success, rolls back on error
        with conn.cursor() as cur:
            # 1. Atomically try to reserve the id
            cur.execute(
                """
                INSERT INTO events (id, url, image_url, site, title, subtitle, date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                RETURNING id
                """,
                (message_id, item["url"], item["image_url"], item["site"], item["title"], item["subtitle"], item["date"]),
            )
            # if cur.fetchone() is None:     # row already existed
            #     return False

            # 2. Find all channels that subscribe to this news-source
            cur.execute(
                "SELECT channel FROM nyhetsjegersubs WHERE newssource = %s",
                ("Kulturkalender",),
            )
            channels = [row[0] for row in cur.fetchall()]
    message = (
        f"Nytt arrangement!\n\n"
        f"Hvor: {item['site']}\n"
        f"Når: {item['date']}\n\n"
        f"*{item['title']}*\n"
        f"{item['subtitle']}\n\n"
        f"<{item['url']}|Les mer på {item['site']} her.>"
    )

    blocks = build_event_blocks(item)

    # 3. Send the message outside the DB transaction
    for channel in channels:
        app.client.chat_postMessage(
            channel=channel,
            text=message,
            blocks=blocks,           # Slack API ignores None
            icon_url=icon_url,
            username=sender,
        )
    return True

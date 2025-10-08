from datetime import datetime
from zoneinfo import ZoneInfo

from src.clients.pg import get_conn
from src.clients.slack import app


CHANNEL = "#smp-kulturjeger-test"
USERNAME = "Kulturkalender"
ICON_EMOJI = ":calendar:"  # optional


def header_block(date_iso: str):
    return {
        "type": "header",
        "text": {"type": "plain_text", "text": f"Her er noen arrangementer som skjer i dag – {date_iso}", "emoji": True},
    }

def footer_block_button():
    return {
        "type": "actions",
        "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Se hele kulturkalenderen", "emoji": True}, "url": "https://toolbox-app-4q5rr.ondigitalocean.app/kultur"}
        ]
    }


def event_blocks(event):
    """
    event is a tuple in the order:
    (id, url, image_url, site, title, subtitle, date)
    """
    _id, url, image_url, site, title, subtitle, _date = event

    # Main line: bold, clickable title
    section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*<{url}|{title}>*\n\n{subtitle}\n\n{site}",
        },
    }

    # Optional image on the right (only if image_url present)
    if image_url:
        section["accessory"] = {
            "type": "image",
            "image_url": image_url,
            "alt_text": title[:150] if title else "event image",
        }

    # Context line with site + subtitle
    context_text = " • ".join(filter(None, [site, subtitle]))
    context = {
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": context_text or " "}],
    }

    return [section, context, {"type": "divider"}]


def chunk_blocks(blocks, max_blocks=45):
    """
    Slack allows up to 50 blocks per message.
    Keep some headroom (header + a little buffer), so default to 45.
    """
    for i in range(0, len(blocks), max_blocks):
        yield blocks[i : i + max_blocks]


if __name__ == "__main__":
    # Use Oslo time so "today" matches your local calendar logic
    today_oslo = datetime.now(ZoneInfo("Europe/Oslo")).date().isoformat()

    conn = get_conn()
    with conn, conn.cursor() as cur:
        # Be explicit about columns to avoid index surprises if the table changes
        cur.execute(
            """
            SELECT id, url, image_url, site, title, subtitle, date
            FROM events
            WHERE date = %s
            ORDER BY site NULLS LAST, title NULLS LAST, id
            """,
            (today_oslo,),
        )
        events = cur.fetchall()

    all_blocks = [header_block(today_oslo)]
    for event in events:
        all_blocks.extend(event_blocks(event))
    all_blocks.append(footer_block_button())

    # Send one or more messages if needed (chunk to respect Slack limits)
    first = True
    for chunk in chunk_blocks(all_blocks):
        app.client.chat_postMessage(
            channel=CHANNEL,
            text=f"Her er noen arrangementer som skjer i dag – {today_oslo}",  # fallback text
            blocks=chunk,
            username=USERNAME,
            icon_emoji=ICON_EMOJI,
            unfurl_links=False,
            unfurl_media=False,
            reply_broadcast=False,
        )
        first = False

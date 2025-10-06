import asyncio
from datetime import datetime, timezone, timedelta
from pprint import pprint
import requests
import logging
import hashlib
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BRREG_UPDATES_URL = "https://data.brreg.no/enhetsregisteret/api/oppdateringer/roller"
DEFAULT_SIZE = 1

async def get_brreg_roles():
    """
    Fetches the latest updates on roller from Brønnøysundregistrene and posts to Slack if not already seen.
    """
    try:
        after_id = redis_client.get("brreg_after_id")
        if after_id:
            after_id = int(after_id)
        else:
            after_id = 0
        after_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(timespec='milliseconds').replace('+00:00', 'Z')

        params = {
            "afterTime": after_time,
            "size": DEFAULT_SIZE,
            "afterId": after_id
        }

        try:
            response = requests.get(BRREG_UPDATES_URL, params=params)
            response.raise_for_status()
            data = response.json()
            for update in data:
                orgnr = update['data']['organisasjonsnummer']
                update_id = int(update['id'])
                if update_id > after_id:
                    after_id = update_id
                unit_details_url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{orgnr}"
                try:
                    unit_response = requests.get(unit_details_url, timeout=10)
                    unit_response.raise_for_status()
                    unit_data = unit_response.json()
                except requests.exceptions.RequestException:
                    continue
                pprint(unit_data)
                pprint(update)
            
            redis_client.set("brreg_after_id", after_id)
                
        except Exception as e:
            logger.error(f"Error fetching BRREG roller updates: {e}")
            return

    except Exception as e:
        logger.error(f"An error occurred while fetching BRREG roller updates: {e}")

if __name__ == "__main__":
    asyncio.run(get_brreg_roles())

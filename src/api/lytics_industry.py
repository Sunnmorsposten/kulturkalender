import logging
import asyncio
import requests
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# If these clients are available in your environment:
from src.clients.redis import redis_client
from src.services.send_slack_chat import send_slack_chat

LYTICS_INDUSTRY_URL = "https://api.lytix.com/constr/projects?page=1&per_page=10&stages[]=initiation&stages[]=frame_permit&stages[]=commissioning_permit&stages[]=completed&municipalities[]=1508&municipalities[]=1531&municipalities[]=1532&municipalities[]=1520&municipalities[]=1577&municipalities[]=1515&municipalities[]=1525&municipalities[]=1528&municipalities[]=1517&municipalities[]=1580&municipalities[]=1511&municipalities[]=1578&municipalities[]=4649&municipalities[]=1535&municipalities[]=1514&municipalities[]=1516&municipalities[]=1566&municipalities[]=4651&municipalities[]=3432&with_detached_house=false&with_old_projects=false"

headers = {
    "Apikey": "x-olc-pr-ea5eed735fe2cb2c3914b82cec64b756"
}

async def get_lytics_industry():
    try:
        response = requests.get(LYTICS_INDUSTRY_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # "projects" is the array of items in the JSON
        for project in data.get("projects", [])[:10]:
            if project.get("ml_title", ""):
                ml_title = project.get("ml_title", "").strip()
                project_id = project.get("id", "")
                redis_id = f"lytix_app_{project.get('id', '')}"
            else:
                continue
            message_text = f"*{ml_title}*\n"
            if project.get("stage_no", ""):
                message_text += f"Stadie: {project.get('stage_no', '')}\n"
                redis_id += f"_{project.get('stage_no', '')}"
            if project.get("stage_date", ""):
                message_text += f"Dato: {project.get('stage_date', '')}\n"
            if project.get("ml_usable_area", ""):
                message_text += f"Bruttoareal: {project.get('ml_usable_area', '')} kvm\n"
            if project.get("property_types_no", []):
                message_text += f"Type(r): {', '.join(project.get('property_types_no', []))}\n"

            message_text += f"<https://app.lytix.com/project/{project_id}|Les mer>"

            message_id = f"lytics_industry_{project_id}"

            send_slack_chat(
                message_id,
                message_text,
                "https://lytix-cms-assets.s3.eu-west-2.amazonaws.com/big_logo_c24c764ef5.svg",
                "Lytics - Prosjektoversikt"
            )
            

    except Exception as err:
        logging.error(f"An error occurred while fetching Lytics Industry data: {err}")

if __name__ == "__main__":
    asyncio.run(get_lytics_industry())

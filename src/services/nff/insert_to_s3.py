import os
import sys
import json
import io
from psycopg2 import sql

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.clients.slack import app
from src.clients.pg import conn   # psycopg2 connection object
from src.clients.s3 import client

def get_from_s3():
    # Create a file-like object to hold the downloaded data
    file_obj = io.BytesIO()

    # Download the file from the S3 bucket into the file-like object
    client.download_fileobj(
        'smps3',
        "nff-overganger/overganger_2025.json", 
        file_obj, 
        ExtraArgs={'ChecksumMode': 'disabled'}
    )

    # Move the file pointer to the beginning of the file so we can read it
    file_obj.seek(0)

    # Read and decode the file content
    file_content = file_obj.read().decode('utf-8')

    # Parse the JSON data from the file content
    data = json.loads(file_content)

    return data

def write_to_s3(data: object, key: str) -> None:
    """
    Overwrite *key* in the S3 bucket with the supplied JSON-serialisable *data*.
    """
    json_data = json.dumps(data, ensure_ascii=False)
    file_obj = io.BytesIO(json_data.encode("utf-8"))
    client.upload_fileobj(
        file_obj,
        'smps3',
        f"{key}",
        ExtraArgs={
            "ACL": "public-read",
            "ContentType": "application/json",
            "CacheControl": "max-age=0"
        }
    )


def insert_to_s3(message_id: str, player: dict) -> bool:
    """
    Ensure the player with *message_id* exists in the S3 list.

    Returns
    -------
    bool
        True  – a new record was appended and pushed to S3  
        False – the message_id already existed; nothing changed
    """
    # Pull the current list
    data = get_from_s3()

    # Bail out early if the ID is already present
    if any(item["message_id"] == message_id for item in data):
        return False

    # Append a new record
    data.insert(0, {
        "message_id": message_id,
        "player": player,  # expected to match the JSON schema you showed
    })

    # Push the updated list back to S3
    write_to_s3(data, key="nff-overganger/overganger_2025.json")
    return True

# def insert_to_s3(
#     message_id: str,
#     player: object,
# ) -> bool:
#     """
#     Insert a message to S3.

#     Parameters
#     ----------
#     message_id : str
#         The ID of the message.
#     message : str
#     """
#     # with conn:                       # <-- commits automatically on success, rolls back on error
#     #     with conn.cursor() as cur:
#     #         # 1. Atomically try to reserve the id
#     #         # cur.execute(
#     #         #     """
#     #         #     SELECT * FROM nff_overganger WHERE message_id = %s
#     #         #     """,
#     #         #     (message_id,),
#     #         # )
#     #         # if cur.fetchone() is None:     # row already existed
#     #         #     return False
#     data = get_from_s3()
#     print(data)
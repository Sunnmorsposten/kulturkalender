from boto3 import session
from botocore.config import Config

import os

# from dotenv import load_dotenv
# load_dotenv()

ACCESS_ID = os.getenv("SPACES_ACCESS_ID")
SECRET_KEY = os.getenv("SPACES_SECRET_KEY")
BUCKET_URL = os.getenv("BUCKET_URL")

session = session.Session()
client = session.client('s3',
                        region_name="ams3",
                        endpoint_url=BUCKET_URL,
                        aws_access_key_id=ACCESS_ID,
                        aws_secret_access_key=SECRET_KEY)
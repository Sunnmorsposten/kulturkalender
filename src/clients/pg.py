import psycopg2
import os

from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    database=os.environ.get("POSTGRES_DB"),
    host=os.environ.get("POSTGRES_HOST"),
    user=os.environ.get("POSTGRES_USER"),
    password=os.environ.get("POSTGRES_PASSWORD"),
    port=os.environ.get("POSTGRES_PORT")
)
import traceback

from pydantic import ValidationError
from src.models.news import NewsEntry
from src.clients.redis import redis_client

def write_article(article: NewsEntry):
    try:
        entry = NewsEntry.model_validate(article)
        data_to_stream = {
            "url": entry.url,
            "site": entry.site,
            "title": entry.title,
            "subtitle": entry.subtitle,
            "date": str(entry.date)
        }

        message_id = redis_client.xadd("article_stream", data_to_stream)
        print(f"Successfully written article with url: {entry.url} and message id: {message_id}")
    except ValidationError as e:
        print(f"Validation error for article {entry.url}: {e}")
        traceback.print_exc()
        
    except Exception as err:
        print(f"Error writing article {entry.url}: {err}")
        traceback.print_exc()
        
    
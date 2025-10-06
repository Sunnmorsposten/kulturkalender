from typing import Optional
from pydantic import BaseModel, HttpUrl, field_validator
from datetime import datetime

class NewsEntry(BaseModel):
    url: str
    title: str
    site: str
    subtitle: str
    date: Optional[datetime]

    @field_validator('url', 'title', 'site')
    def non_empty_strings(cls, value, field):
        if not value.strip():
            raise ValueError(f'{field.name} must not be emtpy or just whitespace.')
        return value

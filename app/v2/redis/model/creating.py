from datetime import date

from redis_om import HashModel, Field, JsonModel


class Creating(JsonModel):
    keyword: str = Field(index=True)
    started_at: date

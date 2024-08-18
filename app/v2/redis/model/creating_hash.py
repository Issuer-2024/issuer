from redis_om import Field, JsonModel


class CreatingHash(JsonModel):
    keyword: str = Field(index=True)
    started_at: str
    ratio: int
    status: str

from datetime import datetime

from redis_om import JsonModel


class APICallCount(JsonModel):
    count: int
    last_call: datetime

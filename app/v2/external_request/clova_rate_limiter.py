import uuid
import re

from app.v2.redis import redis_connection


RATE_LIMIT_BLOCK_KEY = "clova:rate-limit:block"
RATE_LIMIT_LOCK_KEY = "clova:rate-limit:in-flight"


class ClovaRateLimitError(RuntimeError):
    pass


class ClovaRateLimiter:
    def __init__(self, timeout=30):
        self.timeout = timeout
        self.token = str(uuid.uuid4())
        self.acquired = False

    def __enter__(self):
        redis_client = redis_connection.redis_client
        if redis_client is None:
            return self

        block_ttl = redis_client.ttl(RATE_LIMIT_BLOCK_KEY)
        if block_ttl and block_ttl > 0:
            raise ClovaRateLimitError(f"CLOVA rate limit resets in {block_ttl}s")

        self.acquired = bool(redis_client.set(
            RATE_LIMIT_LOCK_KEY, self.token, nx=True, ex=self.timeout
        ))
        if not self.acquired:
            raise ClovaRateLimitError("Another CLOVA request is currently in flight")
        return self

    def update_from_response(self, response):
        redis_client = redis_connection.redis_client
        if redis_client is None:
            return

        remaining = response.headers.get("x-ratelimit-remaining-requests")
        reset = response.headers.get("x-ratelimit-reset-requests")
        if remaining is None or reset is None:
            return

        try:
            if int(remaining) <= 0:
                reset_seconds = int(float(re.sub(r"[^0-9.]", "", reset)))
                redis_client.set(RATE_LIMIT_BLOCK_KEY, "1", ex=max(1, reset_seconds))
        except (TypeError, ValueError):
            return

    def __exit__(self, exc_type, exc_value, traceback):
        redis_client = redis_connection.redis_client
        if redis_client is not None and self.acquired:
            if redis_client.get(RATE_LIMIT_LOCK_KEY) == self.token:
                redis_client.delete(RATE_LIMIT_LOCK_KEY)
        return False

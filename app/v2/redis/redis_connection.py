from redis_om import get_redis_connection

redis = None
db_redis = None


def connect_redis():
    global redis, db_redis
    redis = get_redis_connection(
        host="redis",
        port=6379,
        decode_responses=True
    )
    db_redis = redis



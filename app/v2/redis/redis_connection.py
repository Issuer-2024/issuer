from redis_om import get_redis_connection, Migrator

redis = None
db_redis = None


def connect_redis():
    global redis, db_redis
    redis = get_redis_connection(
        host="redis",
        port=6379,
        decode_responses=True
    )
    Migrator().run()
    db_redis = redis



import redis

channel_name = 'broadcast_channel'


def connect_redis_pub_sub():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    pubsub = redis_client.pubsub()
    pubsub.subscribe(channel_name)
    return redis_client

from redis_om import get_redis_connection
from redis import Redis
from redis_om.model import Migrator

redis_om = None  # Redis OM용 (Model 저장용)
redis_client = None  # 일반 Redis 명령용


def connect_redis():
    global redis_om, redis_client

    # 1) Redis OM (JSON, Hash 모델용)
    redis_om = get_redis_connection(
        host="localhost",
        port=6379,
        decode_responses=True
    )

    # 모델 스키마 생성
    Migrator().run()

    # 2) 일반 redis-py 클라이언트 (List, BRPOP, SET NX 등)
    redis_client = Redis(
        host="localhost",
        port=6379,
        decode_responses=True
    )
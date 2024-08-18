import time
from datetime import datetime

import pytz
from redis_om import Migrator

from app.v2.model.content import Content
from app.v2.redis.model import ContentHash
from app.v2.redis.model.creating_hash import CreatingHash
from app.v2.redis.redis_connection import db_redis
from fastapi import BackgroundTasks


def move_to_db_and_delete_from_cache(content_id: str):
    time.sleep(3600)  # 1 hour
    content = ContentHash.get(content_id)
    if content:
        db_redis.hset(f"content:{content_id}", mapping=content.dict())
        ContentHash.delete(content_id)


def save_to_caching(content: Content):
    content_hash = ContentHash(keyword=content.keyword,
                               created_at=content.created_at,
                               keyword_trend_data=content.keyword_trend_data,
                               keyword_suggestions_data=content.keyword_suggestions_data,
                               public_opinion_sentiment=content.public_opinion_sentiment,
                               public_opinion_word_frequency=content.public_opinion_word_frequency,
                               table_of_contents=content.table_of_contents,
                               body=content.body,
                               table_of_public_opinion=content.table_of_public_opinion,
                               public_opinion_trend=content.public_opinion_trend,
                               public_opinion_summary=content.public_opinion_summary)
    content_hash.save()
    content_hash.expire(7200)


def save_creating(keyword: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    creating_hash = CreatingHash(keyword=keyword, started_at=now, ratio= 0, status="로딩중")

    creating_hash.save()
    creating_hash.expire(600)

    return creating_hash


def read_creating(keyword: str):
    Migrator().run()
    keys = CreatingHash.find(CreatingHash.keyword == keyword).all()
    if not keys:
        return None
    creating = [CreatingHash.get(key.pk) for key in keys]
    return creating[0]


def remove_creating(keyword: str):
    Migrator().run()
    keys = CreatingHash.find(CreatingHash.keyword == keyword).all()
    if not keys:
        return
    for key in keys:
        CreatingHash.delete(key.pk)


# def read_cache_content(keyword: str):
#     Migrator().run()
#     keys = ContentHash.find(ContentHash.keyword == keyword).all()
#     if not keys:
#         return None
#     contents = [ContentHash.get(key.pk) for key in keys]
#     return contents[0]

def read_cache_content(keyword: str):
    Migrator().run()  # 마이그레이션 실행
    keys = ContentHash.find(ContentHash.keyword == keyword).all()  # 키워드에 해당하는 모든 키 찾기

    if not keys:
        return None

    # 첫 번째 키에 해당하는 데이터를 압축 해제하여 반환
    content = ContentHash.get_decompressed(keys[0].pk)
    return content

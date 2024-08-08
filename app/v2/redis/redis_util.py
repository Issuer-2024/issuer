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


def save_to_caching(content: Content, background_tasks: BackgroundTasks):
    content_hash = ContentHash(keyword=content.keyword,
                               created_at=content.created_at,
                               keyword_trend_data=content.keyword_trend_data,
                               keyword_suggestions_data=content.keyword_suggestions_data,
                               public_opinion_activity_data=content.public_opinion_activity_data,
                               public_opinion_word_frequency=content.public_opinion_word_frequency,
                               table_of_contents=content.table_of_contents,
                               body=content.body,
                               trend_public_opinion=content.trend_public_opinion,
                               table_of_public_opinion=content.table_of_public_opinion,)
    content_hash.save()
    background_tasks.add_task(move_to_db_and_delete_from_cache, content_hash.pk)


def save_creating(keyword: str):
    KST = pytz.timezone('Asia/Seoul')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    creating_hash = CreatingHash(keyword=keyword, started_at=now)

    creating_hash.save()

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


def read_cache_content(keyword: str):
    Migrator().run()
    keys = ContentHash.find(ContentHash.keyword == keyword).all()
    if not keys:
        return None
    contents = [ContentHash.get(key.pk) for key in keys]
    return contents[0]

def db_read(keyword: str):
    keys = db_redis.keys(f"content:*")
    contents = []
    for key in keys:
        content = db_redis.hgetall(key)
        if content and content['keyword'] == keyword:
            contents.append(content)
    if not contents:
        return None
    return contents

from datetime import datetime
from enum import Enum

from redis_om import Migrator
from app.v2.model.content import Content
from app.v2.redis.model import PickleContent, JSONContent
from app.v2.redis.redis_util import RedisUtil
from app.v2.redis.model.creating import Creating


class ObjectType(str, Enum):
    JSON = "json"
    PICKLE = "pickle"


class CompressType(str, Enum):
    BROTli = "brotli"
    ZSTD = "zstd"
    ZLIB = "zlib"
    NONE = "none"


OBJ_MAP = {
    ObjectType.JSON: JSONContent,
    ObjectType.PICKLE: PickleContent,
}

SERIALIZE_FUNC_MAP = {
    ObjectType.JSON: RedisUtil.json_serialize,
    ObjectType.PICKLE: RedisUtil.pickle_serialize,
}

DESERIALIZE_FUNC_MAP = {
    ObjectType.JSON: RedisUtil.json_deserialize,
    ObjectType.PICKLE: RedisUtil.pickle_deserialize,
}

COMPRESS_FUNC_MAP = {
    CompressType.ZSTD: RedisUtil.compress_zstd,
    CompressType.BROTli: RedisUtil.compress_brotli,
    CompressType.ZLIB: RedisUtil.compress_zlib,
    CompressType.NONE: (lambda x: x),  # 압축 안 하는 경우
}

DECOMPRESS_FUNC_MAP = {
    CompressType.ZSTD: RedisUtil.decompress_zstd,
    CompressType.BROTli: RedisUtil.decompress_brotli,
    CompressType.ZLIB: RedisUtil.decompress_zlib,
    CompressType.NONE: (lambda x: x),  # 압축 안 하는 경우
}


class RedisManager:
    @staticmethod
    def read_content(
            keyword: str,
            object_type: ObjectType = ObjectType.JSON,
            compress_type: CompressType = CompressType.NONE
    ):
        return RedisContentManager.read_content(object_type, compress_type, keyword)

    @staticmethod
    def save_content(
            content: Content,
            object_type: ObjectType = ObjectType.JSON,
            compress_type: CompressType = CompressType.NONE
    ):
        return RedisContentManager.save_content(object_type, compress_type, content)

    @staticmethod
    def read_creating(keyword):
        return RedisCreatingManager.read_creating(keyword)

    @staticmethod
    def save_creating(keyword: str):
        return RedisCreatingManager.save_creating(keyword)

    @staticmethod
    def remove_creating(keyword):
        return RedisCreatingManager.remove_creating(keyword)


class RedisCreatingManager:
    @staticmethod
    def save_creating(keyword: str):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        creating = Creating(keyword=keyword, started_at=now, ratio=0, status="로딩중")
        creating.save()
        return creating

    @staticmethod
    def read_creating(keyword: str):
        Migrator().run()
        keys = Creating.find(Creating.keyword == keyword).all()
        if not keys:
            return None
        creating = [Creating.get(key.pk) for key in keys]
        return creating[0]

    @staticmethod
    def remove_creating(keyword: str):
        Migrator().run()
        keys = Creating.find(Creating.keyword == keyword).all()
        if not keys:
            return
        for key in keys:
            Creating.delete(key.pk)


class RedisContentManager:
    @staticmethod
    def save_content(object_type: ObjectType, compress_type: CompressType, content: Content):
        obj = OBJ_MAP[object_type]
        serialize_func = SERIALIZE_FUNC_MAP[object_type]
        compress_func = COMPRESS_FUNC_MAP[compress_type]

        content_model = obj(keyword=content.keyword,
                            created_at=content.created_at,
                            data=serialize_func(content))
        content_model.savef(compress_func)
        content_model.expire(7200)

    @staticmethod
    def read_content(object_type: ObjectType, compress_type: CompressType, keyword: str):
        obj = OBJ_MAP[object_type]
        deserialize_func = DESERIALIZE_FUNC_MAP[object_type]
        decompress_func = DECOMPRESS_FUNC_MAP[compress_type]

        keys = obj.find(obj.keyword == keyword).all()

        if not keys:
            return None
        content = obj.get_decompressed(keys[0].pk, deserialize_func, decompress_func)
        return content

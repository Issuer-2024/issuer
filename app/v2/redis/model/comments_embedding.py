from typing import Any
from redis_om import Field, JsonModel

from app.v2.redis import RedisUtil


class CommentsEmbedding(JsonModel):
    keyword: str = Field(index=True)
    embedding_results: Any  # 압축된 데이터로 저장

    def save(self, *args, **kwargs):
        self.embedding_results = RedisUtil.compress_data(self.embedding_results)
        super().save(*args, **kwargs)

    @classmethod
    def get_decompressed(cls, pk: str):
        instance = cls.get(pk)
        instance.embedding_results = RedisUtil.decompress_data(instance.embedding_results)

        return instance

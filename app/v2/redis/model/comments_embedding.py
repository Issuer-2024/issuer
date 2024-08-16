import base64
import json
import zlib
from typing import Any

from redis_om import Field, JsonModel


def compress_data(data: Any) -> str:
    json_data = json.dumps(data)
    compressed_data = zlib.compress(json_data.encode('utf-8'))
    base64_data = base64.b64encode(compressed_data).decode('utf-8')
    return base64_data


def decompress_data(base64_data: str) -> Any:
    compressed_data = base64.b64decode(base64_data)
    decompressed_data = zlib.decompress(compressed_data).decode('utf-8')
    return json.loads(decompressed_data)


class CommentsEmbedding(JsonModel):
    keyword: str = Field(index=True)
    embedding_results: Any  # 압축된 데이터로 저장

    def save(self, *args, **kwargs):
        # 저장하기 전에 데이터를 압축합니다.
        self.embedding_results = compress_data(self.embedding_results)
        super().save(*args, **kwargs)

    @classmethod
    def get_decompressed(cls, pk: str):
        # 압축을 해제하여 데이터를 가져옵니다.
        instance = cls.get(pk)
        instance.embedding_results = decompress_data(instance.embedding_results)

        return instance

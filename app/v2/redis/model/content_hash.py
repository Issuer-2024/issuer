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


# class ContentHash(JsonModel):
#     keyword: str = Field(index=True)
#     created_at: str = Field(index=True)
#     keyword_trend_data: List[Dict[str, Any]]
#     keyword_suggestions_data: List[Dict[str, Any]]
#     public_opinion_sentiment: Any
#     public_opinion_word_frequency: Any
#     table_of_contents: List[Dict[str, Any]]
#     body: List[Dict[str, Any]]
#     table_of_public_opinion: Any
#     public_opinion_trend: Any
#     public_opinion_summary: Any

class ContentHash(JsonModel):
    keyword: str = Field(index=True)
    created_at: str = Field(index=True)
    keyword_trend_data: Any  # 압축된 데이터로 저장
    keyword_suggestions_data: Any  # 압축된 데이터로 저장
    public_opinion_sentiment: Any  # 압축된 데이터로 저장
    public_opinion_word_frequency: Any  # 압축된 데이터로 저장
    table_of_contents: Any  # 압축된 데이터로 저장
    body: Any  # 압축된 데이터로 저장
    table_of_public_opinion: Any  # 압축된 데이터로 저장
    public_opinion_trend: Any  # 압축된 데이터로 저장
    public_opinion_summary: Any  # 압축된 데이터로 저장

    def save(self, *args, **kwargs):
        # 저장하기 전에 데이터를 압축합니다.
        self.keyword_trend_data = compress_data(self.keyword_trend_data)
        self.keyword_suggestions_data = compress_data(self.keyword_suggestions_data)
        self.public_opinion_sentiment = compress_data(self.public_opinion_sentiment)
        self.public_opinion_word_frequency = compress_data(self.public_opinion_word_frequency)
        self.table_of_contents = compress_data(self.table_of_contents)
        self.body = compress_data(self.body)
        self.table_of_public_opinion = compress_data(self.table_of_public_opinion)
        self.public_opinion_trend = compress_data(self.public_opinion_trend)
        self.public_opinion_summary = compress_data(self.public_opinion_summary)

        super().save(*args, **kwargs)

    @classmethod
    def get_decompressed(cls, pk: str):
        # 압축을 해제하여 데이터를 가져옵니다.
        instance = cls.get(pk)
        instance.keyword_trend_data = decompress_data(instance.keyword_trend_data)
        instance.keyword_suggestions_data = decompress_data(instance.keyword_suggestions_data)
        instance.public_opinion_sentiment = decompress_data(instance.public_opinion_sentiment)
        instance.public_opinion_word_frequency = decompress_data(instance.public_opinion_word_frequency)
        instance.table_of_contents = decompress_data(instance.table_of_contents)
        instance.body = decompress_data(instance.body)
        instance.table_of_public_opinion = decompress_data(instance.table_of_public_opinion)
        instance.public_opinion_trend = decompress_data(instance.public_opinion_trend)
        instance.public_opinion_summary = decompress_data(instance.public_opinion_summary)

        return instance

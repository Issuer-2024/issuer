from typing import Any
from redis_om import Field, JsonModel

class JSONContent(JsonModel):
    keyword: str = Field(index=True)
    created_at: str = Field(index=True)
    keyword_trend_data: Any
    keyword_suggestions_data: Any
    public_opinion_sentiment: Any
    public_opinion_word_frequency: Any
    table_of_contents: Any
    body: Any
    table_of_public_opinion: Any
    public_opinion_trend: Any
    public_opinion_summary: Any

    def savef(self, func, *args, **kwargs):
        # 저장하기 전에 데이터를 압축합니다.
        self.keyword_trend_data = func(self.keyword_trend_data)
        self.keyword_suggestions_data = func(self.keyword_suggestions_data)
        self.public_opinion_sentiment = func(self.public_opinion_sentiment)
        self.public_opinion_word_frequency = func(self.public_opinion_word_frequency)
        self.table_of_contents = func(self.table_of_contents)
        self.body = func(self.body)
        self.table_of_public_opinion = func(self.table_of_public_opinion)
        self.public_opinion_trend = func(self.public_opinion_trend)
        self.public_opinion_summary = func(self.public_opinion_summary)

        super().save(*args, **kwargs)

    @classmethod
    def get_decompressed(cls, pk: str, func):
        # 압축을 해제하여 데이터를 가져옵니다.
        instance = cls.get(pk)
        instance.keyword_trend_data = func(instance.keyword_trend_data)
        instance.keyword_suggestions_data = func(instance.keyword_suggestions_data)
        instance.public_opinion_sentiment = func(instance.public_opinion_sentiment)
        instance.public_opinion_word_frequency = func(instance.public_opinion_word_frequency)
        instance.table_of_contents = func(instance.table_of_contents)
        instance.body = func(instance.body)
        instance.table_of_public_opinion = func(instance.table_of_public_opinion)
        instance.public_opinion_trend = func(instance.public_opinion_trend)
        instance.public_opinion_summary = func(instance.public_opinion_summary)

        return instance

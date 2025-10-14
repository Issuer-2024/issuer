from redis_om import HashModel, Field
from app.v2.redis.redis_util import RedisUtil


class PickleContent(HashModel):
    keyword: str = Field(index=True)
    created_at: str = Field(index=True)
    keyword_trend_data: bytes
    keyword_suggestions_data: bytes
    public_opinion_sentiment: bytes
    public_opinion_word_frequency: bytes
    table_of_contents: bytes
    body: bytes
    table_of_public_opinion: bytes
    public_opinion_trend: bytes
    public_opinion_summary: bytes

    def save(self, *args, **kwargs):
        func = RedisUtil.pickle_serialize
        # pickle 직렬화
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
    def get_unpickled(cls, pk: str):
        instance = cls.get(pk)
        func = RedisUtil.pickle_deserialize
        # 역직렬화
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

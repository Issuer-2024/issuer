from datetime import datetime
from redis_om import Migrator
from app.v2.model.content import Content
from app.v2.redis.redis_util import RedisUtil
from app.v2.redis.model import JSONContent, PickleContent
from app.v2.redis.model.creating import Creating


class RedisManager:
    @staticmethod
    def read_content(keyword):
        return RedisContentManager.read_json_content(keyword)

    @staticmethod
    def save_content(content: Content):
        return RedisContentManager.save_json_content(content)

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
    def save_json_content(content: Content):
        json_content = JSONContent(keyword=content.keyword,
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
        json_content.save()
        json_content.expire(7200)

    @staticmethod
    def save_pickle_content(content: Content):
        pickle_content = PickleContent(keyword=content.keyword,
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
        pickle_content.save()
        pickle_content.expire(7200)

    @staticmethod
    def read_json_content(keyword: str, func=None):
        def noop(data):
            return data

        if func is None:
            func = noop

        Migrator().run()  # 마이그레이션 실행
        keys = JSONContent.find(JSONContent.keyword == keyword).all()  # 키워드에 해당하는 모든 키 찾기

        if not keys:
            return None

        # 첫 번째 키에 해당하는 데이터를 압축 해제하여 반환
        content = JSONContent.get_decompressed(keys[0].pk, func)
        return content

if __name__ == '__main__':
    import time
    start = time.time()
    RedisContentManager.read_json_content("캄보디아 대학생")
    end = time.time()
    print(f"캄보디아 대학생 실행 시간: {end - start:.3f}초")

    start = time.time()
    RedisContentManager.read_json_content("김다현", RedisUtil.decompress_data)
    end = time.time()
    print(f"김다현 실행 시간: {end - start:.3f}초")
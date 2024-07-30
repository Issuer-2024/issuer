import os
from asyncio import as_completed
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from app.v2.external_request import RequestTrend, EmbeddingExecutor, get_naver_news
from app.v2.model.content import Content


def collect_issues(q: str):
    naver_news_response = get_naver_news(q, 100, 1, sort='sim')
    news_items = naver_news_response.json().get('items', [])
    news_items = [news_item for news_item in news_items if
                  news_item['link'].startswith('https://n.news.naver.com/mnews/article')]
    return news_items


def create_embedding_result(issues: list):

    embedding_executor = EmbeddingExecutor(
        host='clovastudio.apigw.ntruss.com',
        api_key=os.getenv("CLOVA_EMBEDDING_CLIENT_KEY"),
        api_key_primary_val=os.getenv("CLOVA_EMBEDDING_CLIENT_KEY_PRIMARY_VAR"),
        request_id=os.getenv("CLOVA_EMBEDDING_REQUEST_ID")
    )

    def get_embedding(title):
        request_data = {"text": title}
        return embedding_executor.execute(request_data)

    embedding_results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_title = {executor.submit(get_embedding, title): title for title in titles}
        for future in as_completed(future_to_title):
            embedding = future.result()
            if embedding != "Error":
                embedding_results.append(embedding)

    return embedding_results



def get_content(q: str):
    title = q
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    today = datetime.today()
    one_months_ago = (today - timedelta(days=30)).replace(day=1).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')

    keyword_groups = [
        {'groupName': q, 'keywords': [q]}
    ]

    trend_search_data = RequestTrend.get_naver_trend_search_data(one_months_ago,
                                                                 today,
                                                                 'date',
                                                                 keyword_groups)[0]['data']

    return Content(title, created_at, trend_search_data, [], {})


if __name__ == '__main__':
    print(collect_issues("티몬"))
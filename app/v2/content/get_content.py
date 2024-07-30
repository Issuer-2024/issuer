import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
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

    def get_embedding(item):
        request_data = {"text": item['title']}
        return embedding_executor.execute(request_data)

    embedding_results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_item = {executor.submit(get_embedding, item): item for item in issues}
        for future in as_completed(future_to_item):
            embedding = future.result()
            if embedding != "Error":
                embedding_results.append((embedding, future_to_item[future]))

    return embedding_results


def grouping_issues(embedding_results):
    embeddings, items = zip(*embedding_results)
    embeddings = StandardScaler().fit_transform(embeddings)
    dbscan = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
    labels = dbscan.fit_predict(embeddings)

    clustered_items = {}
    for item, label in zip(items, labels):
        if label not in clustered_items:
            clustered_items[label] = []
        clustered_items[label].append(item)

    return clustered_items


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
    issues = collect_issues("티몬")
    result = create_embedding_result(issues)

    print(grouping_issues(result))
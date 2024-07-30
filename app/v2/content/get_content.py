import json
import os
import pprint
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from app.v2.external_request import RequestTrend, EmbeddingExecutor, get_naver_news, CompletionExecutor, \
    get_news_summary, ClovaSummary
from app.v2.model.content import Content


def collect_issues(q: str):
    naver_news_response = get_naver_news(q, 5, 1, sort='sim')
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
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(get_embedding, item): item for item in issues}
        for future in as_completed(future_to_item):
            embedding = future.result()
            if embedding != "Error":
                embedding_results.append((embedding, future_to_item[future]))

    return embedding_results


def cluster_issues(embedding_results):
    embeddings, items = zip(*embedding_results)
    embeddings = StandardScaler().fit_transform(embeddings)
    dbscan = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
    labels = dbscan.fit_predict(embeddings)

    clustered_issues = {}
    for item, label in zip(items, labels):
        if label not in clustered_issues:
            clustered_issues[label] = []
        clustered_issues[label].append(item)

    return clustered_issues


def create_group_title(clustered_issues):
    group_titles = {}

    for cluster_num, items in clustered_issues.items():
        titles = [item['title'] for item in items]

        completion_executor = CompletionExecutor(
            host='https://clovastudio.stream.ntruss.com',
            api_key=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY"),
            api_key_primary_val=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY_PRIMARY_VAR"),
            request_id=os.getenv("CLOVA_CHAT_COMPLETION_REQUEST_ID")
        )
        preset_text = [{"role": "system",
                        "content": "적합한 제목을 도출하는 AI입니다."
                                   "### 지시사항\n"
                                   "- 입력된 제목들에서 핵심 내용을 조합하여 1줄로 나타냅니다.\n"
                                   "\n## 응답형식: 제목"},
                       {"role": "user", "content": f"{titles}"}]

        request_data = {
            'messages': preset_text,
            'topP': 0.8,
            'topK': 0,
            'maxTokens': 128,
            'temperature': 0.1,
            'repeatPenalty': 1.0,
            'stopBefore': [],
            'includeAiFilters': False,
            'seed': 0
        }
        result = completion_executor.execute(request_data)
        group_titles[cluster_num] = result
    return group_titles


def create_group_content(clustered_issues):
    clova_summary = ClovaSummary(
        host='clovastudio.apigw.ntruss.com',
        api_key=os.getenv("CLOVA_SUMMARY_CLIENT_KEY"),
        api_key_primary_val=os.getenv('CLOVA_SUMMARY_CLIENT_KEY_PRIMARY_VAR'),
        request_id=os.getenv("CLOVA_SUMMARY_REQUEST_ID")
    )

    group_contents = {}

    for cluster_num, items in clustered_issues.items():
        contents = [get_news_summary(item['link'])['summary'] for item in items]
        request_data = {
            "texts": contents,
            "segMinSize": 300,
            "includeAiFilters": True,
            "autoSentenceSplitter": True,
            "segCount": -1,
            "segMaxSize": 1000
        }
        request_data_json = json.dumps(request_data)

        group_contents_summary = clova_summary.execute(json.loads(request_data_json))
        group_contents[cluster_num] = group_contents_summary
    return group_contents


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

    a = collect_issues(q)
    b = create_embedding_result(a)
    c = cluster_issues(b)
    d = create_group_title(c)
    e = create_group_content(c)

    body = {"개요": "", "현재 이슈": {
        cluster_num: {
            "title": title,
            "content": ""
        } for cluster_num, title in d.items()
    }}

    for cluster_num, content in e.items():
        body["현재 이슈"][cluster_num]["content"] = content

    table_of_contents = [{'title': "개요", 'depth': 0}, {'title': "현재 이슈", 'depth': 0}]
    table_of_contents += [{'title': v['title'], 'depth': 1} for v in body['현재 이슈'].values()]
    print(body)
    return Content(title, created_at, trend_search_data, table_of_contents, body)


if __name__ == '__main__':
    start_time = time.time()

    step_start = time.time()
    a = collect_issues("쯔양")
    print(f"collect_issues took {time.time() - step_start:.2f} seconds")

    step_start = time.time()
    b = create_embedding_result(a)
    print(f"create_embedding_result took {time.time() - step_start:.2f} seconds")

    step_start = time.time()
    c = cluster_issues(b)
    print(f"cluster_issues took {time.time() - step_start:.2f} seconds")

    step_start = time.time()
    d = create_group_title(c)
    print(f"create_group_title took {time.time() - step_start:.2f} seconds")

    step_start = time.time()
    e = create_group_content(c)
    print(f"create_group_content took {time.time() - step_start:.2f} seconds")

    body = {"개요": "", "현재 이슈": {
        cluster_num: {
            "title": title,
            "content": ""
        } for cluster_num, title in d.items()
    }}

    for cluster_num, content in e.items():
        body["현재 이슈"][cluster_num]["content"] = content

    pprint.pprint(body)
    print(f"Total execution took {time.time() - start_time:.2f} seconds")
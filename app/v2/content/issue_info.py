import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from app.v2.content.get_high_searching_news import get_high_searching_days, get_high_searching_news
from app.v2.external_request import EmbeddingExecutor, get_naver_news, CompletionExecutor, \
    get_news_summary, HCX003Chat


def convert_pubDate_format(data):
    for item in data:
        try:
            date_obj = datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S %z')
            item['pubDate'] = date_obj.strftime('%Y%m%d')
        except ValueError:
            try:
                date_obj = datetime.strptime(item['pubDate'], '%Y%m%d')
                item['pubDate'] = date_obj.strftime('%Y%m%d')
            except ValueError:
                continue



def collect_issues(q: str, estimated_search_amount: list):
    high_searching_days = get_high_searching_days(estimated_search_amount)
    high_searching_news = get_high_searching_news(q, high_searching_days)

    naver_news_response = get_naver_news(q, 10, 1, sort='sim')
    news_items = naver_news_response.json().get('items', [])
    news_items = [news_item for news_item in news_items if
                  news_item['link'].startswith('https://n.news.naver.com/mnews/article')]
    news_items += high_searching_news
    convert_pubDate_format(news_items)
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
    if not embedding_results:
        return {}

    embeddings, items = zip(*embedding_results)
    embeddings = StandardScaler().fit_transform(embeddings)
    dbscan = DBSCAN(eps=0.6, min_samples=2, metric='cosine')
    labels = dbscan.fit_predict(embeddings)

    clustered_issues = {}
    for item, label in zip(items, labels):
        if label == -1:
            continue
        if label not in clustered_issues:
            clustered_issues[label] = []
        clustered_issues[label].append(item)

    return clustered_issues


def create_group_title(clustered_issues):
    group_titles = {}

    for cluster_num, items in clustered_issues.items():
        titles = [item['title'] for item in items[:5]]

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
    chat = HCX003Chat(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv('CLOVA_CHAT_COMPLETION_003_CLIENT_KEY'),
        api_key_primary_val=os.getenv('CLOVA_CHAT_COMPLETION_003_CLIENT_KEY_PRIMARY_VAR'),
        request_id=os.getenv('CLOVA_CHAT_COMPLETION_003_CLIENT_KEY_REQUEST_ID'),
    )

    group_contents = {}
    for cluster_num, items in clustered_issues.items():
        contents = [get_news_summary(item['link'])['summary'] for item in items[:5]]
        preset_text = [{"role": "system",
                        "content": "- 내용을 정리하는 AI입니다."
                                   "- 반드시 본문과 관련된 내용만 출력합니다."
                                   "- 본문의 핵심 내용이 잘 드러나게 정리합니다."
                                   "- 최소 300자 이내로 내용을 출력합니다."
                        },
                       {"role": "user", "content": f"{''.join(contents)}"}]

        request_data = {
            'messages': preset_text,
            'topP': 0.8,
            'topK': 0,
            'maxTokens': 256,
            'temperature': 0.5,
            'repeatPenalty': 5.0,
            'stopBefore': [],
            'includeAiFilters': False,
            'seed': 0
        }

        group_contents_summary = chat.execute(request_data)
        group_contents[cluster_num] = group_contents_summary
    return group_contents
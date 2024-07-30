import os
from datetime import datetime

from app.v1.request_external_api import get_news_summary
from app.v1.timeline import get_news_list_by_date
from app.v1.util import CompletionExecutor


def get_news_title_list(q: str) -> list:

    date = datetime.now().strftime('%Y-%m-%d')
    news_link = get_news_list_by_date(q, date)
    news_link = [url for url in news_link if 'https://n.news.naver.com' in url]
    news_title = []
    for url in news_link:
        news_title.append(get_news_summary(url)['title'])

    return news_title


def get_today_issue_summary(q: str):
    news_title_list = get_news_title_list(q)

    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY"),
        api_key_primary_val=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY_PRIMARY_VAR"),
        request_id=os.getenv("CLOVA_CHAT_COMPLETION_REQUEST_ID")
    )

    preset_text = [{"role": "system", "content": "당신은 뉴스 기사를 요약하는 도우미입니다."},
                   {"role": "user", "content": f"다음 뉴스 제목을 최소 3개, 최대 6개의 간결하고 명확한 순서형 목록으로 요약하여 주요 문제를 강조해 주세요. "
                                               f"순서형 목록만을 보여주고"
                                               f"문체는 정중체로 ~니다로 종결합니다.: "
                                               f"\"{news_title_list}\""}]

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

    return completion_executor.execute(request_data).split('\n')

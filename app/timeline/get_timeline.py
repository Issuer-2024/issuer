from datetime import datetime
import pandas as pd
import os
from app.request_external_api import RequestNews
from app.util import CompletionExecutor


def get_timeline(q: str):
    timeline_data = {}

    articles_data = []
    all_articles = []

    for i in range(1, 2):
        all_articles += RequestNews.get_naver_news(q, 100, i, 'sim').json()['items']
    for article in all_articles:
        title = article['title']
        link = article['link']
        pub_date = article['pubDate']
        formatted_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S +0900').strftime('%Y-%m-%d')
        articles_data.append([title, link, formatted_date])

    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY"),
        api_key_primary_val=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY_PRIMARY_VAR"),
        request_id=os.getenv("CLOVA_CHAT_COMPLETION_REQUEST_ID")
    )

    df = pd.DataFrame(articles_data, columns=['Title', 'Link', 'Date'])
    grouped_df = df.groupby('Date')
    for date, group in grouped_df:
        news_title = []
        for index, row in group.head(5).iterrows():
            news_title.append(row['Title'])

        preset_text = [{"role": "system", "content": "당신은 뉴스 기사를 요약하는 도우미입니다."},
                       {"role": "user",
                        "content": f"다음 뉴스 제목을 최소 1개, 최대 3개의 간결하고 명확한 순서형 목록으로 요약하여 주요 문제를 강조해 주세요. "
                                   f"순서형 목록만을 보여주고"
                                   f"문체는 정중체로 ~니다로 종결합니다.: "
                                   f"\"{news_title}\""}]

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

        result = completion_executor.execute(request_data).split('\n')
        timeline_data[date] = result

    return timeline_data

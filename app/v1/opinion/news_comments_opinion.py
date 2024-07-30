from datetime import datetime

import requests
from bs4 import BeautifulSoup

from app.v1.request_external_api import RequestNewsComments
from app.v1.timeline import get_news_list_by_date
from app.v1.util import CompletionExecutor

import os

def get_news_title(url):
    # 웹 페이지의 HTML 가져오기
    response = requests.get(url)
    html_content = response.text

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, 'html.parser')

    # 뉴스 제목 요소 찾기
    title_element = soup.find('h2', {'class': 'media_end_head_headline'})

    # 제목 가져오기
    if title_element:
        title = title_element.get_text()
        return title
    else:
        return None

def get_news_comments_opinion(q: str):
    comment_sentiment_data = []
    date = datetime.now().strftime('%Y-%m-%d')
    news_link = get_news_list_by_date(q, date)
    news_link = [url for url in news_link if 'https://n.news.naver.com' in url][:5]
    news_title = []
    for url in news_link:
        news_title.append(get_news_title(url))
    raw_data = []

    for url in news_link:
        tmp = RequestNewsComments.get_news_comments(url)
        if tmp:
            raw_data.append(tmp)

    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY"),
        api_key_primary_val=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY_PRIMARY_VAR"),
        request_id=os.getenv("CLOVA_CHAT_COMPLETION_REQUEST_ID")
    )

    for items, title in zip(raw_data, news_title):
        trend_score = 0
        contents = []
        for item in items:
            contents.append(item['contents'])
            trend_score += item['sympathy_count'] + item['antipathy_count'] + item['reply_count']
        preset_text = [{"role": "system",
                        "content": "댓글을 분석하는 AI 어시스턴트 입니다.\n출력 형식: 다음 입력에 대해 3줄로 명확하게 사용자 여론을 표현해주세요.\n\n"},
                       {"role": "user", "content": f"{contents}"}]

        request_data = {
            'messages': preset_text,
            'topP': 0.8,
            'topK': 0,
            'maxTokens': 256,
            'temperature': 0.5,
            'repeatPenalty': 1.0,
            'stopBefore': [],
            'includeAiFilters': False,
            'seed': 0
        }
        result = completion_executor.execute(request_data)
        comment_sentiment_data.append({'title': title, "result": result, "ratio": trend_score})
        comment_sentiment_data.sort(key=lambda x: x['ratio'], reverse=True)
    return comment_sentiment_data

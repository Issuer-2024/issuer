from fastapi import HTTPException

from app.request_external_api import RequestSuggestions, RequestNews
from app.util import NewsCommentsCrawler, StringUtil, CompletionExecutor

import os


def get_news_comments_opinion(q: str):
    comment_sentiment_data = []

    suggestions = RequestSuggestions.get_suggestions(q)
    news_link = []
    for suggestion in suggestions[:1]:
        naver_news_response = RequestNews.get_naver_news(suggestion, display=10, sort='sim')
        if naver_news_response.status_code != 200:
            raise HTTPException(status_code=500, detail="NEWS API 호출 오류")

        news_items = naver_news_response.json().get('items', [])
        news_items = [news_item for news_item in news_items if
                      news_item['link'].startswith('https://n.news.naver.com/mnews/article')]
        for news_item in news_items:
            news_link.append(news_item['link'])
    raw_data = []
    news_comments_crawler = NewsCommentsCrawler()

    for link in news_link:
        tmp = news_comments_crawler.parse(StringUtil.convert_news_url_to_comment_url(link))
        if tmp:
            raw_data.append(tmp)

    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY"),
        api_key_primary_val=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY_PRIMARY_VAR"),
        request_id=os.getenv("CLOVA_CHAT_COMPLETION_REQUEST_ID")
    )

    for item in raw_data:
        preset_text = [{"role": "system",
                        "content": "댓글을 분석하는 AI 어시스턴트 입니다.\n출력 형식: 다음 입력에 대해 3줄로 명확하게 사용자 여론을 표현해주세요.\n\n"},
                       {"role": "user", "content": f"{item['댓글']}"}]

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
        comment_sentiment_data.append({'title': item['제목'], "result": result, "ratio": item['트랜드 수치']})
        comment_sentiment_data.sort(key=lambda x: x['ratio'], reverse=True)
    return comment_sentiment_data

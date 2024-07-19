import json
import os
from datetime import datetime, timedelta

import pandas as pd
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from app.util.completion_executor import CompletionExecutor
from app.util.news_comments_crawler import NewsCommentsCrawler
from app.util.string_util import StringUtil
from app.request_external_api.request_news import RequestNews
from app.request_external_api.request_suggestions import RequestSuggestions
from app.request_external_api.request_trend import RequestTrend
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")





def get_today_issue_summary(q: str):
    news_title = []

    suggestions = RequestSuggestions.get_suggestions(q)

    for suggestion in suggestions[:1]:
        naver_news_response = RequestNews.get_naver_news(suggestion, display=10, sort='sim')
        if naver_news_response.status_code != 200:
            raise HTTPException(status_code=500, detail="NEWS API 호출 오류")

        news_items = naver_news_response.json().get('items', [])
        # news_items = [news_item for news_item in news_items if
        #               news_item['link'].startswith('https://n.news.naver.com/mnews/article')]

        for news_item in news_items:
            news_title.append(StringUtil.clean_and_extract_korean_english(news_item['title']))

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
    return completion_executor.execute(request_data).split('\n')

def get_trend_variation(q: str):
    today = datetime.today()
    two_months_ago = (today - timedelta(days=60)).replace(day=1)
    two_months_ago = two_months_ago.strftime('%Y-%m-01')
    today = today.strftime('%Y-%m-%d')

    keyword_groups = [{'groupName': q, 'keywords': [suggestion for suggestion in RequestSuggestions.get_suggestions(q)]}]

    trend_search_data = RequestTrend.get_naver_trend_search_data(two_months_ago, today, 'date', keyword_groups)[0]['data']
    daily_variation = (trend_search_data[-1]['ratio'] / trend_search_data[-2]['ratio'] * 100) - 100
    two_weeks_ago_ratio = sum([entry['ratio'] for entry in trend_search_data[-14:-7]])
    one_weeks_ago_ratio = sum([entry['ratio'] for entry in trend_search_data[-7:]])
    weekly_variation = (one_weeks_ago_ratio / two_weeks_ago_ratio * 100) - 100

    two_months_ago_ratio = sum([entry['ratio'] for entry in trend_search_data[-60:30]])
    one_months_ago_ratio = sum([entry['ratio'] for entry in trend_search_data[-30:]])
    monthly_variation = (one_months_ago_ratio / two_months_ago_ratio * 100) - 100

    today = datetime.now()
    yesterday = today - timedelta(days=1)
    one_weeks_ago = today - timedelta(days=7)
    one_months_ago = today - timedelta(days=30)
    today_str = today.strftime('%Y.%m.%d')
    yesterday_str = yesterday.strftime('%Y.%m.%d')
    one_weeks_ago_str = one_weeks_ago.strftime('%Y.%m.%d')
    one_months_ago_str = one_months_ago.strftime('%Y.%m.%d')

    trend_variation = {"date":
                           {'ratio': daily_variation,
                            'duration': f"{today_str} ~ {yesterday_str}"},
                       "week": {
                           'ratio': weekly_variation,
                           'duration': f"{today_str} ~ {one_weeks_ago_str}",
                       },
                       "month": {
                           'ratio': monthly_variation,
                           'duration': f"{today_str} ~ {one_months_ago_str}"
                       }}

    return trend_variation


def get_suggestion_trend(q: str):
    today = datetime.today()
    one_week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')
    suggestions = RequestSuggestions.get_suggestions(q)
    keyword_groups = [{'groupName': suggestion, 'keywords': [suggestion]} for suggestion in suggestions[1:6]]
    return RequestTrend.get_naver_trend_search_data(one_week_ago, today, 'date', keyword_groups)


def get_suggestion_trend_score(trend_data: list):
    score = 0
    for data in trend_data:
        score += data['ratio']
    return score


def get_most_trend_day(trend_data: list):
    # 'ratio' 필드가 있는 항목만 필터링
    filtered_trend_data = list(filter(lambda x: 'ratio' in x, trend_data))

    # 필터링된 데이터가 비어 있지 않으면, 최대 ratio 값을 가진 항목을 찾습니다.
    if filtered_trend_data:
        max_ratio_entry = max(filtered_trend_data, key=lambda x: x['ratio'])
        return max_ratio_entry['period']
    else:
        return None  # 'ratio' 필드가 있는 항목이 없는 경우 None을 반환합니다.


def get_suggestion_entire_data(q: str):
    suggestion_entire_data = []
    suggestion_trend = get_suggestion_trend(q)

    for i, data in enumerate(suggestion_trend):  # title, keywords, data
        tmp = {'id': i, 'keyword': data['title'], 'trend': data['data'],
               'score': get_suggestion_trend_score(data['data']),
               'most_trend_day': get_most_trend_day(data['data'])}
        suggestion_entire_data.append(tmp)

    total_score = sum(item['score'] for item in suggestion_entire_data)
    for i in range(len(suggestion_entire_data)):
        suggestion_entire_data[i]['trend_proportion'] = suggestion_entire_data[i]['score'] / total_score * 100

    suggestion_entire_data.sort(key=lambda x: x['score'], reverse=True)
    return suggestion_entire_data


def get_comment_sentiment_data(q: str):
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

@app.get("/")
async def render_main(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )


@app.get("/report")
def render_report(q: str, request: Request):
    return templates.TemplateResponse(
        request=request, name="report.html", context={"issue_summary": get_today_issue_summary(q),
                                                      "trend_variation": get_trend_variation(q),
                                                      "suggestion_trend_data": get_suggestion_entire_data(q)
                                                      }
    )


@app.get("/opinion")
def render_opinion(q: str, request: Request):
    return templates.TemplateResponse(
        request=request, name="opinion.html", context={"opinions": get_comment_sentiment_data(q)}
    )

@app.get("/timeline")
def render_timeline(q: str, request: Request):
    return templates.TemplateResponse(
        request=request, name="timeline.html", context={"timeline": get_timeline(q)}
    )



uvicorn.run(app, host='0.0.0.0', port=8000)

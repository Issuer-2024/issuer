import json
import os
from datetime import datetime, timedelta

import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel
from collections import defaultdict
from bs4 import BeautifulSoup
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates
from webdriver_manager.chrome import ChromeDriverManager

load_dotenv()

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

NAVER_API_HEADERS = {
    'X-Naver-Client-Id': os.getenv('NAVER_API_CLIENT_ID'),
    'X-Naver-Client-Secret': os.getenv('NAVER_API_CLIENT_SECRET'),
}

CLOVA_API_HEADERS = {
    "X-NCP-APIGW-API-KEY-ID": os.getenv('CLOVA_API_CLIENT_ID'),
    "X-NCP-APIGW-API-KEY": os.getenv('CLOVA_API_CLIENT_SECRET'),
    "Content-Type": "application/json"
}

CLOVA_SUMMARY_API_ENDPOINT = "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize"


def get_naver_news(query, display, start=1, sort='date'):
    naver_news_api_url = f'https://openapi.naver.com/v1/search/news.json?query={query}&display={display}&start={start}&sort={sort}'
    return requests.get(naver_news_api_url, headers=NAVER_API_HEADERS)


def get_clova_summary_result(content, tone=0, summary_count=1):
    # tone - 0: 원문 어투, 1: 해요체 2: 정중체, 3: 명사형 종결체
    data = {
        "document": {
            "content": content
        },
        "option": {
            "language": "ko",
            "model": "general",
            "tone": tone,
            "summaryCount": summary_count
        }
    }

    try:
        response = requests.post(CLOVA_SUMMARY_API_ENDPOINT, headers=CLOVA_API_HEADERS, data=json.dumps(data))
        response.raise_for_status()
        return response.json()['summary']
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # HTTP 에러 출력
        print(f"Response content: {response.content.decode()}")  # 응답 본문 출력
        return None
    except Exception as err:
        print(f"Other error occurred: {err}")  # 기타 에러 출력


def get_suggestions(query):
    suggestions_api_url = f"http://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={query}&hl=ko"
    suggestions_response = requests.get(suggestions_api_url)
    return suggestions_response.json()[1]


def get_today_issue_summary(q: str):
    issue_summary = []

    suggestions = get_suggestions(q)

    for suggestion in suggestions:
        naver_news_response = get_naver_news(suggestion, display=1, sort='sim')
        if naver_news_response.status_code != 200:
            raise HTTPException(status_code=500, detail="NEWS API 호출 오류")

        news_items = naver_news_response.json().get('items', [])
        news_items = [news_item for news_item in news_items if
                      news_item['link'].startswith('https://n.news.naver.com/mnews/article')]
        for news_item in news_items:
            driver.get(news_item['link'])
            article_body = driver.find_element(By.ID, "dic_area").text
            issue_summary.append(get_clova_summary_result(article_body[:400], tone=0, summary_count=1))

    return issue_summary


def get_trend_searh_data(start_date: str, end_date: str, time_unit: str, keyword_groups: list):
    # 구간단위 - date, week, month
    # group data => groupName, keywords:list
    # 날짜 형식 yyyy-mm-dd
    naver_trend_search_api_endpoint = "https://openapi.naver.com/v1/datalab/search"

    request_body = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": time_unit,
        "keywordGroups": keyword_groups
    }

    try:
        response = requests.post(naver_trend_search_api_endpoint, headers=NAVER_API_HEADERS,
                                 data=json.dumps(request_body))
        response.raise_for_status()
        return response.json()['results'][0]['data']
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # HTTP 에러 출력
        print(f"Response content: {response.content.decode()}")  # 응답 본문 출력
        return None
    except Exception as err:
        print(f"Other error occurred: {err}")  # 기타 에러 출력


def get_trend_variation(q: str):
    today = datetime.today()
    two_months_ago = (today - timedelta(days=60)).replace(day=1)
    two_months_ago = two_months_ago.strftime('%Y-%m-01')
    today = today.strftime('%Y-%m-%d')

    keyword_groups = [{'groupName': q, 'keywords': [suggestion for suggestion in get_suggestions(q)]}]

    trend_search_data = get_trend_searh_data(two_months_ago, today, 'date', keyword_groups)
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
                                                      }
    )


uvicorn.run(app, host='0.0.0.0', port=8000)

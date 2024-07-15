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



@app.get("/timeline")
def get_timeline_preview(q: str):
    # 각 타임라인에 들어갈 아이템
    class TimelineDataItem(BaseModel):
        title: str
        link: str
        pub_date: str

    timeline_data = defaultdict(list)
    naver_news_response = get_naver_news(q, display=100, sort='sim')

    news_items = naver_news_response.json().get('items', [])

    news_items = [news_item for news_item in news_items if
                  news_item['link'].startswith('https://n.news.naver.com/mnews/article')]

    for news_item in news_items:
        timeline_data_item = TimelineDataItem(
            title=news_item['title'],
            link=news_item['link'],
            pub_date=news_item['pubDate'],
        )
        date_parts = ' '.join(timeline_data_item.pub_date.split(' ')[:3])
        timeline_data[date_parts].append(timeline_data_item)
    return timeline_data


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

@app.get("/")
async def render_main(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html"
    )

@app.get("/report")
def render_report(q: str, request: Request):
    return templates.TemplateResponse(
        request=request, name="report.html", context={"issue_summary": get_today_issue_summary(q)}
    )

uvicorn.run(app, host='0.0.0.0', port=8000)

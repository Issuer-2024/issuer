import json
import os
from datetime import datetime, timedelta

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel
from collections import defaultdict

load_dotenv()

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
    return requests.post(CLOVA_SUMMARY_API_ENDPOINT, headers=CLOVA_API_HEADERS, data=json.dumps(data))


app = FastAPI()


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


@app.get("/today-issue-summary")
def get_today_issue_summary(q: str):
    naver_news_response = get_naver_news(q, display=100, sort='date')
    news_items = naver_news_response.json().get('items', [])
    news_items = [news_item for news_item in news_items if
                  datetime.strptime(news_item['pubDate'], "%a, %d %b %Y %H:%M:%S %z").date() == datetime.now().date()]
    target_summary_data = ""

    for news_item in news_items:
        target_summary_data += news_item['title'] + '\n'


uvicorn.run(app, host='0.0.0.0', port=8000)

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



app = FastAPI()


@app.get("/timeline")
def get_timeline_preview(q: str):

    # 각 타임라인에 들어갈 아이템
    class TimelineDataItem(BaseModel):
        title: str
        link: str
        pub_date: str

    def get_naver_news(query, display, start=1, sort='date'):
        naver_news_api_url = f'https://openapi.naver.com/v1/search/news.json?query={query}&display={display}&start={start}&sort={sort}'
        return requests.get(naver_news_api_url, headers=NAVER_API_HEADERS)

    timeline_data = defaultdict(list)
    naver_news_response = get_naver_news(q, display=100, sort='sim')

    news_items = naver_news_response.json().get('items', [])

    for news_item in news_items:
        timeline_data_item = TimelineDataItem(
            title=news_item['title'],
            link=news_item['link'],
            pub_date=news_item['pubDate'],
        )
        date_parts = ' '.join(timeline_data_item.pub_date.split(' ')[:3])
        timeline_data[date_parts].append(timeline_data_item)
    return timeline_data



    pass



uvicorn.run(app, host='0.0.0.0', port=8000)

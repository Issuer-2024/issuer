from datetime import datetime, timedelta

from fastapi import FastAPI
import uvicorn
import requests

app = FastAPI()


@app.get("/timeline")
def get_timeline_preview(q: str):

    def get_naver_news(query, display, start, sort):
        naver_news_api_url = f'https://openapi.naver.com/v1/search/news.json?query={query}&display={display}&start={start}&sort={sort}'
        return requests.get(naver_news_api_url, headers=naver_news_api_headers)

    pass



uvicorn.run(app, host='0.0.0.0', port=8000)

import os
from datetime import datetime, timedelta

import requests
import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

NAVER_API_HEADERS = {
    'X-Naver-Client-Id': os.getenv('NAVER_API_CLIENT_ID'),
    'X-Naver-Client-Secret': os.getenv('NAVER_API_CLIENT_SECRET'),
}



app = FastAPI()


@app.get("/timeline")
def get_timeline_preview(q: str):

    def get_naver_news(query, display, start=1, sort='date'):
        naver_news_api_url = f'https://openapi.naver.com/v1/search/news.json?query={query}&display={display}&start={start}&sort={sort}'
        return requests.get(naver_news_api_url, headers=NAVER_API_HEADERS)

    main_timeline_data = {(datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d'): [] for i in range(7)}

    pass



uvicorn.run(app, host='0.0.0.0', port=8000)

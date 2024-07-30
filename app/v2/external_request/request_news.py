import os

import requests

from dotenv import load_dotenv
load_dotenv()

NAVER_API_HEADERS = {
    'X-Naver-Client-Id': os.getenv('NAVER_API_CLIENT_ID'),
    'X-Naver-Client-Secret': os.getenv('NAVER_API_CLIENT_SECRET'),
}


def get_naver_news(query, display, start=1, sort='date'):
    naver_news_api_url = (f'https://openapi.naver.com/v1/search/news.json?'
                          f'query={query}&display={display}&start={start}&sort={sort}')

    try:
        response = requests.get(naver_news_api_url, headers=NAVER_API_HEADERS)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # HTTP 에러 출력
        print(f"Response content: {response.content.decode()}")  # 응답 본문 출력
        return None
    except Exception as err:
        print(f"Other error occurred: {err}")  # 기타 에러 출력

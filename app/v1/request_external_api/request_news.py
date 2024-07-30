import requests
import os
from dotenv import load_dotenv
load_dotenv()

NAVER_API_HEADERS = {
    'X-Naver-Client-Id': os.getenv('NAVER_API_CLIENT_ID'),
    'X-Naver-Client-Secret': os.getenv('NAVER_API_CLIENT_SECRET'),
}


class RequestNews:

    @staticmethod
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

# def get_clova_summary_result(content, tone=0, summary_count=1):
#     # tone - 0: 원문 어투, 1: 해요체 2: 정중체, 3: 명사형 종결체
#     data = {
#         "document": {
#             "content": content
#         },
#         "option": {
#             "language": "ko",
#             "model": "general",
#             "tone": tone,
#             "summaryCount": summary_count
#         }
#     }
#
#     try:
#         response = requests.post(CLOVA_SUMMARY_API_ENDPOINT, headers=CLOVA_API_HEADERS, data=json.dumps(data))
#         response.raise_for_status()
#         return response.json()['summary']
#     except requests.exceptions.HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err}")  # HTTP 에러 출력
#         print(f"Response content: {response.content.decode()}")  # 응답 본문 출력
#         return None
#     except Exception as err:
#         print(f"Other error occurred: {err}")  # 기타 에러 출력
# CLOVA_API_HEADERS = {
#     "X-NCP-APIGW-API-KEY-ID": os.getenv('CLOVA_API_CLIENT_ID'),
#     "X-NCP-APIGW-API-KEY": os.getenv('CLOVA_API_CLIENT_SECRET'),
#     "Content-Type": "application/json"
# }
#
# CLOVA_SUMMARY_API_ENDPOINT = "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize"

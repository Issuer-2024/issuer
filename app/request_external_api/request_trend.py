import requests
import json
import os

NAVER_API_HEADERS = {
    'X-Naver-Client-Id': os.getenv('NAVER_API_CLIENT_ID'),
    'X-Naver-Client-Secret': os.getenv('NAVER_API_CLIENT_SECRET'),
}


class RequestTrend:
    @staticmethod
    def get_naver_trend_search_data(start_date: str, end_date: str, time_unit: str, keyword_groups: list, ages: list = [],
                                    gender: str = ""):
        # 구간단위 - date, week, month
        # group data => groupName, keywords:list
        # 날짜 형식 yyyy-mm-dd
        naver_trend_search_api_endpoint = "https://openapi.naver.com/v1/datalab/search"

        request_body = {
            "startDate": start_date,
            "endDate": end_date,
            "timeUnit": time_unit,
            "keywordGroups": keyword_groups,
            "ages": ages,
            "gender": gender
        }

        try:
            response = requests.post(naver_trend_search_api_endpoint, headers=NAVER_API_HEADERS,
                                     data=json.dumps(request_body))
            response.raise_for_status()
            return response.json()['results']
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # HTTP 에러 출력
            print(f"Response content: {response.content.decode()}")  # 응답 본문 출력
            return None
        except Exception as err:
            print(f"Other error occurred: {err}")  # 기타 에러 출력

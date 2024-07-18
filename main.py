import json
import os
import re
from datetime import datetime, timedelta

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from starlette.templating import Jinja2Templates
from bs4 import BeautifulSoup

load_dotenv()

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class CompletionExecutor:
    def __init__(self, host, api_key, api_key_primary_val, request_id):
        self._host = host
        self._api_key = api_key
        self._api_key_primary_val = api_key_primary_val
        self._request_id = request_id

    def execute(self, completion_request):
        headers = {
            'X-NCP-CLOVASTUDIO-API-KEY': self._api_key,
            'X-NCP-APIGW-API-KEY': self._api_key_primary_val,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json'
        }

        response = requests.post(self._host + '/testapp/v1/chat-completions/HCX-DASH-001',
                                 headers=headers, json=completion_request)

        if response.status_code == 200:
            return response.json()['result']['message']['content']
        else:
            response.raise_for_status()


class NewsCommentsCrawler:

    # def _wait_more_btn(self):
    #     while True:
    #         try:
    #             WebDriverWait(self.driver, 3).until(
    #                 EC.presence_of_element_located((By.LINK_TEXT, "더보기"))
    #             )
    #             more_button = self.driver.find_element(by=By.LINK_TEXT, value='더보기')
    #             more_button.click()
    #         except Exception as e:
    #             break

    def _get_text(self, elem):
        return elem.select_one(
            "div.u_cbox_text_wrap span.u_cbox_contents").text.strip().replace(
            '\n', '')

    def _get_recomm(self, elem):
        return int(elem.select_one('em.u_cbox_cnt_recomm').text.strip())

    def _get_unrecomm(self, elem):
        return int(elem.select_one('em.u_cbox_cnt_unrecomm').text.strip())

    def _get_reply_num(self, elem):
        return int(elem.select_one('span.u_cbox_reply_cnt').text.strip())

    def parse(self, url):
        driver = webdriver.Remote(
            command_executor=os.getenv('WEB_DRIVER_HUB_URL'),
            options=chrome_options
        )
        driver.get(url)
        # 페이지 소스 파싱
        print(url)
        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.LINK_TEXT, "MY댓글"))
                        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        if int(soup.select("span.u_cbox_info_txt")[0].text.replace(',', '').strip()) <= 30:
            driver.quit()
            node_url = os.getenv('WEB_DRIVER_HUB_URL') + '/session/' + driver.session_id  # 노드 URL 및 세션 ID 설정
            response = requests.delete(node_url)
            return None

        # 댓글 추출
        comments = []
        title = soup.select("h2#title_area")[0].text.strip()
        comment_elements = soup.select("ul.u_cbox_list li.u_cbox_comment")
        trend_score = 0
        for comment_element in comment_elements:

            if comment_element.select_one("div.u_cbox_text_wrap span.u_cbox_contents"):  #삭제된 댓글 처리
                trend_score += self._get_recomm(comment_element) + self._get_unrecomm(comment_element) + self._get_reply_num(comment_element)
                if self._get_recomm(comment_element) >= 10:
                    comments.append(self._get_text(comment_element))
                    # comments.append({
                    #     "내용": self._get_text(comment_element),
                    #     #"공감 비율": self._get_recomm(comment_element) / (self._get_unrecomm(comment_element)+1),
                    #     #"대댓글 수": self._get_reply_num(comment_element)
                    # })
            else:
                continue
        driver.quit()
        node_url = os.getenv('WEB_DRIVER_HUB_URL') + '/session/' + driver.session_id  # 노드 URL 및 세션 ID 설정
        response = requests.delete(node_url)
        return {"링크": url, "제목": title, "댓글": comments, "트랜드 수치": trend_score}


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


def clean_and_extract_korean_english(text):
    # HTML 태그와 특수 문자를 제거
    clean_text = re.sub(r'(&quot;|<[^>]*>|\\)', '', text)
    # 한글과 영어 문자만 추출하는 정규 표현식
    korean_english_text = re.findall(r'[가-힣a-zA-Z0-9]+', clean_text)
    # 추출한 문자열들을 공백으로 이어 붙여서 반환
    return ' '.join(korean_english_text)


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
    news_title = []

    suggestions = get_suggestions(q)

    for suggestion in suggestions[1:4]:
        naver_news_response = get_naver_news(suggestion, display=3, sort='sim')
        if naver_news_response.status_code != 200:
            raise HTTPException(status_code=500, detail="NEWS API 호출 오류")

        news_items = naver_news_response.json().get('items', [])
        # news_items = [news_item for news_item in news_items if
        #               news_item['link'].startswith('https://n.news.naver.com/mnews/article')]

        for news_item in news_items:
            news_title.append(clean_and_extract_korean_english(news_item['title']))

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
        return response.json()['results']
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

    trend_search_data = get_trend_searh_data(two_months_ago, today, 'date', keyword_groups)[0]['data']
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
    suggestions = get_suggestions(q)
    keyword_groups = [{'groupName': suggestion, 'keywords': [suggestion]} for suggestion in suggestions[1:6]]
    return get_trend_searh_data(one_week_ago, today, 'date', keyword_groups)


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


def convert_news_url_to_comment_url(news_url):
    # 뉴스 URL의 정규식 패턴
    pattern = r"(https://n\.news\.naver\.com/mnews/article/)(\d+/\d+)(\?.*)"
    replacement = r"\1comment/\2\3"

    # 정규식을 사용하여 댓글 URL로 변환
    comment_url = re.sub(pattern, replacement, news_url)

    return comment_url


def extract_first_two_parentheses_content(text):
    # 정규 표현식으로 첫 번째와 두 번째 괄호 안의 내용 추출
    pattern = r'\(([^)]+)\)'
    matches = re.findall(pattern, text)

    # 첫 번째와 두 번째 괄호 안의 내용만 반환
    if len(matches) >= 2:
        return matches[:2]
    else:
        return matches

def get_comment_sentiment_data(q: str):

    comment_sentiment_data = []

    suggestions = get_suggestions(q)
    news_link = []
    for suggestion in suggestions[:1]:
        naver_news_response = get_naver_news(suggestion, display=20, sort='sim')
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
        tmp = news_comments_crawler.parse(convert_news_url_to_comment_url(link))
        if tmp:
            raw_data.append(tmp)
        if len(raw_data) >= 10:
            break

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
        request=request, name="opinion.html", context={"opinions": get_comment_sentiment_data(q) }
    )


uvicorn.run(app, host='0.0.0.0', port=8000)

from datetime import datetime, timedelta
import pandas as pd
import os

import requests
from bs4 import BeautifulSoup

from app.request_external_api import RequestNews, RequestTrend
from app.util import CompletionExecutor


def get_date_to_collect(duration: int):
    date_list = []
    for i in range(duration + 1):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y.%m.%d')
        date_list.append(date_str)
    return date_list


def get_news_list_by_date(q: str, date: str):
    news_list = []
    url = f'https://search.naver.com/search.naver?where=news&query={q}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={date}&de={date}'
    # 웹 페이지의 HTML 가져오기
    response = requests.get(url)
    html_content = response.text

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, 'html.parser')

    # 뉴스 링크 요소 찾기
    news_links = soup.find_all('a', {'class': 'info'}, href=True)

    # 링크 URL 가져오기
    for link in news_links:
        news_list.append(link['href'])

    return news_list


def filter_naver_news(url_list: list):
    # 네이버 뉴스 URL만 필터링
    naver_news_urls = [url for url in url_list if 'https://n.news.naver.com' in url]
    return naver_news_urls


def get_news_title(url):
    # 웹 페이지의 HTML 가져오기
    response = requests.get(url)
    html_content = response.text

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, 'html.parser')

    # 뉴스 제목 요소 찾기
    title_element = soup.find('h2', {'class': 'media_end_head_headline'})

    # 제목 가져오기
    if title_element:
        title = title_element.get_text()
        return title
    else:
        return None


def get_trend_data(keyword: str):
    date_to_collect = get_date_to_collect(7)[1:]
    trend_data_result = {date: {"10": 0, "20": 0, "30": 0, "40": 0,
                                "50": 0, "60": 0, "male": 0, "female": 0} for date in date_to_collect}
    today = datetime.today()
    one_week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')
    age_group = {"10": ["1", "2"], "20": ["3", "4"], "30": ["5", "6"], "40": ["7", "8"], "50": ["9", "10"],
                 "60": ["11"]}
    sex_group = {"male": "m", "female": "f"}
    keyword_groups = [
        {'groupName': keyword, 'keywords': [keyword]}]
    for k, v in age_group.items():
        trend_data_list = RequestTrend.get_naver_trend_search_data(one_week_ago, today, "date", keyword_groups, v, "")
        for trend_data in trend_data_list:
            for item in trend_data['data']:
                trend_data_result[item['period'].replace('-', '.')][k] = item['ratio']
    for k, v in sex_group.items():
        trend_data_list = RequestTrend.get_naver_trend_search_data(one_week_ago, today, "date", keyword_groups, [], v)
        for trend_data in trend_data_list:
            for item in trend_data['data']:
                trend_data_result[item['period'].replace('-', '.')][k] = item['ratio']
    return trend_data_result


def get_timeline_v2(q: str):
    date_to_collect = get_date_to_collect(7)[1:]
    result = {date: {"issue_summary": "",
                     "trend": {"10": 0, "20": 0, "30": 0, "40": 0, "50": 0, "60": 0, "male": 0, "female": 0},
                     "keyword_sentiment": {"postive": [], "negative": []},
                     "reaction_summary": ""
                     } for date in date_to_collect}

    news_title = {date: [] for date in date_to_collect}
    news_comments = {date: [] for date in date_to_collect}
    for date in date_to_collect:
        news_list = get_news_list_by_date(q, date)
        news_list = filter_naver_news(news_list)

        news_title[date] = [get_news_title(url) for url in news_list[:2]]
        # news_comments[date] = [get_news_comments(url) for url in news_list[:3]]

    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key="NTA0MjU2MWZlZTcxNDJiY9qg8Bwi+oD6PVp1ecnZXbiDvzB4y8m2qLv8/xabLAQg",
        api_key_primary_val="Ad6P4V4p9ncI5qpSnrGDuboJS7rSjaMAaqL9Sxcl",
        request_id='2ab6ff99-5837-465e-b961-7d301eb674e6',
    )

    for date, item in news_title.items():
        preset_text = [{"role": "system", "content": "당신은 뉴스 기사를 요약하는 도우미입니다."},
                       {"role": "user", "content": f"다음 뉴스 제목을 최소 3개, 최대 6개의 간결하고 명확한 순서형 목록으로 요약하여 주요 문제를 강조해 주세요. "
                                                   f"순서형 목록만을 보여주고"
                                                   f"문체는 정중체로 ~니다로 종결합니다.: "
                                                   f"\"{item}\""}]

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
        issue_summary = completion_executor.execute(request_data)
        result[date]['issue_summary'] = issue_summary.split('\n')
    trend_data = get_trend_data(q)
    for date, item in trend_data.items():
        for i, ratio in item.items():
            result[date]['trend'][i] = ratio

    timeline = []
    for k, v in result.items():
        v['date'] = k
        v['age_trend'] = list(v['trend'].values())[:-2]
        v['mf_trend'] = list(v['trend'].values())[-2:]
        timeline.append(v)
    timeline.sort(key=lambda x: x['date'])
    return timeline


def get_timeline(q: str):
    timeline_data = {}

    articles_data = []
    all_articles = []

    for i in range(1, 2):
        all_articles += RequestNews.get_naver_news(q, 100, i, 'sim').json()['items']
    for article in all_articles:
        title = article['title']
        link = article['link']
        pub_date = article['pubDate']
        formatted_date = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S +0900').strftime('%Y-%m-%d')
        articles_data.append([title, link, formatted_date])

    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY"),
        api_key_primary_val=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY_PRIMARY_VAR"),
        request_id=os.getenv("CLOVA_CHAT_COMPLETION_REQUEST_ID")
    )

    df = pd.DataFrame(articles_data, columns=['Title', 'Link', 'Date'])
    grouped_df = df.groupby('Date')
    for date, group in grouped_df:
        news_title = []
        for index, row in group.head(5).iterrows():
            news_title.append(row['Title'])

        preset_text = [{"role": "system", "content": "당신은 뉴스 기사를 요약하는 도우미입니다."},
                       {"role": "user",
                        "content": f"다음 뉴스 제목을 최소 1개, 최대 3개의 간결하고 명확한 순서형 목록으로 요약하여 주요 문제를 강조해 주세요. "
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

        result = completion_executor.execute(request_data).split('\n')
        timeline_data[date] = result

    return timeline_data

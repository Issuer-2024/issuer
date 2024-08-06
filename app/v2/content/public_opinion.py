import time
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup

from app.v2.external_request import get_news_summary
from app.v2.external_request.request_news_comments import RequestNewsComments
from konlpy.tag import Okt
from collections import Counter


office_codes = ['1001', '1421', '1003', '1015', '1437']


# 연합뉴스, 뉴스1, 뉴시스, 한국경제 JTBC


def add_days(date_str, dur):
    date_format = '%Y%m%d'
    date = datetime.strptime(date_str, date_format)
    new_date = date + timedelta(days=3)
    return new_date.strftime(date_format)


def get_news_list_by_office_code(q: str, date, office_code, dur=3):
    news_list = []
    url = f'https://search.naver.com/search.naver?where=news&query={q}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={date}&de={add_days(date, dur)}&docid=&related=0&mynews=1&office_type=2&office_section_code=2&news_office_checked={office_code}&nso=so%3Ar%2Cp%3Afrom20240707to20240707&is_sug_officeid=0&office_category=0&service_area=2'
    # pd =  (기간) 1=1주 2=1달 3=사용자 정의
    # news_office_checked (언론사 코드)
    # 웹 페이지의 HTML 가져오기
    response = requests.get(url)
    if response.status_code != 200:
        return "Error"

    html_content = response.text

    # BeautifulSoup 객체 생성
    soup = BeautifulSoup(html_content, 'html.parser')
    # 뉴스 링크 요소 찾기
    news_links = soup.find_all('a', {'class': 'info'}, href=True)
    # 링크 URL 가져오기
    for link in news_links:
        news_list.append(link['href'])

    news_list = [url for url in news_list if 'https://n.news.naver.com' in url]

    return news_list


def get_dates_to_collect(ago):
    dates = []
    today = datetime.today()
    for i in range(0, ago + 1, 4):  # 3일 단위로 반복
        date = (today - timedelta(days=i)).strftime('%Y%m%d')
        dates.append(date)
    return dates


def collect_comments(q: str):
    dates = get_dates_to_collect(30)
    all_comments_data = []
    for office_code in office_codes[:1]:
        news_urls = []
        for i in range(0, len(dates)):
            tmp = get_news_list_by_office_code(q, dates[i], office_code)
            while tmp == "Error":
                time.sleep(0.5)
                tmp = get_news_list_by_office_code(q, dates[i], office_code)
            news_urls += tmp

        for url in news_urls:
            summary = get_news_summary(url)
            comments = RequestNewsComments.get_news_comments(url)
            all_comments_data.append({'url': url, 'summary': summary, 'comments': comments})

    return all_comments_data


def get_public_opinion_activity_data(all_comments_data):
    comments = []
    for data in all_comments_data:
        comments += data['comments']
    # 데이터프레임으로 변환
    df = pd.DataFrame(comments)
    df['total_interaction'] = df['antipathy_count'] + df['sympathy_count'] + df['reply_count']
    # 날짜 형식 변환
    df['date'] = pd.to_datetime(df['date']).dt.date

    # 일자별로 집계
    interaction_result = df.groupby('date').agg({
        'antipathy_count': 'sum',
        'sympathy_count': 'sum',
        'reply_count': 'sum',
        'total_interaction': 'sum'
    }).reset_index()

    # 일자별 댓글 수 집계
    comment_count_result = df.groupby('date').size().reset_index(name='comment_count')

    # 두 결과 합치기
    final_result = pd.merge(interaction_result, comment_count_result, on='date')

    # date 필드의 날짜 형식을 YYYY-MM-DD 형태로 변환
    final_result['date'] = final_result['date'].astype(str)

    return final_result.to_dict(orient='list')


def get_word_frequency(all_comments_data):
    okt = Okt()
    tmp = []
    for data in all_comments_data:
        for comment in data['comments']:
            tmp += comment['contents']
    all_comments_txt = ''.join(tmp)
    nouns = okt.nouns(all_comments_txt)
    for i, v in enumerate(nouns):
        if len(v) < 2:
            nouns.pop(i)
    counter = Counter(nouns)
    most_common = counter.most_common(30)

    print("키워드와 빈도수:", most_common)

def get_statistic(q):
    all_comments_data = collect_comments(q)
    public_opinion_activity_data = get_public_opinion_activity_data(all_comments_data)
    word_frequency = get_word_frequency(all_comments_data)

    return public_opinion_activity_data, word_frequency


if __name__ == '__main__':
    all_comments_data = collect_comments("주식")
    get_word_frequency(all_comments_data)


# if __name__ == '__main__':
# import pprint
#
# dates = get_dates_to_collect(30)
# all_comments_data = []
# for office_code in office_codes[:1]:
#     news_urls = []
#     for i in range(0, len(dates)):
#         tmp = get_news_list_by_office_code("엔비디아 주가", dates[i], office_code)
#         while tmp == "Error":
#             time.sleep(0.5)
#             tmp = get_news_list_by_office_code("엔비디아 주가", dates[i], office_code)
#         news_urls += tmp
#
#     for url in news_urls:
#         summary = get_news_summary(url)
#         comments = RequestNewsComments.get_news_comments(url)
#         all_comments_data.append({'url': url, 'summary': summary, 'comments': comments})
#
# pprint.pprint(all_comments_data)

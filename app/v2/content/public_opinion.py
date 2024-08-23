import os
import time

import pandas as pd
from konlpy.tag import Okt

from app.v2.external_request import HCX003Chat
from app.v2.external_request.request_clova_sentimet import get_clova_sentiment
from app.v2.external_request.request_news_comments import RequestNewsComments
from dotenv import load_dotenv

load_dotenv()


# office_codes = ['1001', '1421', '1003', '1015', '1437']
# proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
# 연합뉴스, 뉴스1, 뉴시스, 한국경제 JTBC
# def add_days(date_str, dur):
#     date_format = '%Y%m%d'
#     date = datetime.strptime(date_str, date_format)
#     new_date = date + timedelta(days=3)
#     return new_date.strftime(date_format)
#
#
# def get_news_list_by_office_code(q: str, date, office_code, dur=3):
#     header = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
#         'accept': "*/*",
#         'accept-encoding': 'gzip, deflate, br',
#         'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
#         'referer': 'https://n.news.naver.com',
#     }
#     news_list = []
#     url = f'https://search.naver.com/search.naver?where=news&query={q}&sm=tab_opt&sort=0&photo=0&field=0&pd=3&ds={date}&de={add_days(date, dur)}&docid=&related=0&mynews=1&office_type=2&office_section_code=2&news_office_checked={office_code}&nso=so%3Ar%2Cp%3Afrom20240707to20240707&is_sug_officeid=0&office_category=0&service_area=2'
#     # pd =  (기간) 1=1주 2=1달 3=사용자 정의
#     # news_office_checked (언론사 코드)
#     # 웹 페이지의 HTML 가져오기
#     response = requests.get(url, headers=header)
#     if response.status_code != 200:
#         return "Error"
#
#     html_content = response.text
#
#     # BeautifulSoup 객체 생성
#     soup = BeautifulSoup(html_content, 'html.parser')
#     # 뉴스 링크 요소 찾기
#     news_links = soup.find_all('a', {'class': 'info'}, href=True)
#     # 링크 URL 가져오기
#     for link in news_links:
#         news_list.append(link['href'])
#
#     news_list = [url for url in news_list if 'https://n.news.naver.com' in url]
#
#     return news_list
#
#
# def get_news_list_by_api(q: str):
#     news_items = []
#     for i in range(10):
#         naver_news_response = get_naver_news(q, 100, i + 1, sort='sim')
#         tmp = naver_news_response.json().get('items', [])
#         tmp = [news_item for news_item in tmp if
#                news_item['link'].startswith('https://n.news.naver.com/mnews/article')]
#         news_items += tmp
#     return news_items
#
#
# def get_dates_to_collect(ago):
#     dates = []
#     today = datetime.today()
#     for i in range(0, ago + 1, 4):  # 3일 단위로 반복
#         date = (today - timedelta(days=i)).strftime('%Y%m%d')
#         dates.append(date)
#     return dates


# def collect_comments(q: str):
#     dates = get_dates_to_collect(30)
#     all_comments_data = []
#     for office_code in office_codes[:5]:
#         news_urls = []
#         for i in range(0, len(dates)):
#             tmp = get_news_list_by_office_code(q, dates[i], office_code)
#             while tmp == "Error":
#                 time.sleep(3)
#                 tmp = get_news_list_by_office_code(q, dates[i], office_code)
#             news_urls += tmp
#
#         for url in news_urls:
#             summary = get_news_summary(url)
#             comments = RequestNewsComments.get_news_comments(url)
#             all_comments_data.append({'url': url, 'summary': summary, 'comments': comments})
#
#     return all_comments_data


# def get_public_opinion_activity_data(clusters):
#     comments = get_comments_from_clusters(clusters)
#     # 데이터프레임으로 변환
#     df = pd.DataFrame(comments)
#     if 'date' not in df.columns:
#         df['date'] = '19700101'
#     if 'antipathy_count' not in df.columns:
#         df['antipathy_count'] = 0
#     if 'sympathy_count' not in df.columns:
#         df['sympathy_count'] = 0
#     if 'reply_count' not in df.columns:
#         df['reply_count'] = 0
#
#     df['total_interaction'] = df['antipathy_count'] + df['sympathy_count'] + df['reply_count']
#     # 날짜 형식 변환
#     df['date'] = pd.to_datetime(df['date']).dt.date
#
#     # 일자별로 집계
#     interaction_result = df.groupby('date').agg({
#         'antipathy_count': 'sum',
#         'sympathy_count': 'sum',
#         'reply_count': 'sum',
#         'total_interaction': 'sum'
#     }).reset_index()
#
#     # 일자별 댓글 수 집계
#     comment_count_result = df.groupby('date').size().reset_index(name='comment_count')
#
#     # 두 결과 합치기
#     final_result = pd.merge(interaction_result, comment_count_result, on='date')
#
#     # date 필드의 날짜 형식을 YYYY-MM-DD 형태로 변환
#     final_result['date'] = final_result['date'].astype(str)
#     return final_result.to_dict(orient='list')


def get_comments_from_clusters(clusters):
    comments = []
    for cluster in clusters.values():
        for news_item in cluster:
            comment = RequestNewsComments.get_news_comments(news_item['link'])
            for i in range(len(comment)):
                comment[i]['title'] = news_item['title']
                comment[i]['link'] = news_item['link']
            comments += comment

    # 데이터프레임으로 변환
    df = pd.DataFrame(comments)
    if 'date' not in df.columns:
        df['date'] = '19700101'
    if 'antipathy_count' not in df.columns:
        df['antipathy_count'] = 0
    if 'sympathy_count' not in df.columns:
        df['sympathy_count'] = 0
    if 'reply_count' not in df.columns:
        df['reply_count'] = 0

    df['total_interaction'] = df['antipathy_count'] + df['sympathy_count'] + df['reply_count']
    df['sympathy_ratio'] = df['sympathy_count'] / (df['antipathy_count'] + 1)
    # 날짜 형식 변환
    #df['date'] = pd.to_datetime(df['date']).dt.date
    df['date'] = df['date'].astype(str)
    return df


def get_word_frequency(comments_df):
    word_frequency = []

    # {'keyword': 'aa', 'comment': [Comment, Comment...], 'count': len(comment)}

    okt = Okt()

    keyword_map = {}

    sorted_by_sympathy_count = comments_df.sort_values(by='sympathy_count', ascending=False)
    for index, row in sorted_by_sympathy_count.iterrows():
        nouns = okt.nouns(row['contents'])
        nouns = [v for v in nouns if len(v) >= 2]
        nouns = list(set(nouns))
        for noun in nouns:
            if noun not in keyword_map:
                keyword_map[noun] = []
            keyword_map[noun].append(row.to_dict())

    for keyword, comments in sorted(keyword_map.items(), key=lambda x: len(x[1]), reverse=True):
        word_frequency.append({
            'keyword': keyword,
            'comments': comments,
            'count': len(comments)
        })
    return word_frequency


def get_public_opinion_sentiment(comments_df):
    sentiment = {
        'positive': 0,
        'neutral': 0,
        'negative': 0,

        'comments': {
            'positive': [],
            'neutral': [],
            'negative': []
        }
    }
    sorted_by_sympathy_count = comments_df.sort_values(by='sympathy_count', ascending=False)[:10]
    comment_text = ''
    for index, row in sorted_by_sympathy_count.iterrows():
        if len(row['contents']) + len(comment_text) > 1000:
            break
        comment_text += row['contents']

    clova_sentiment = get_clova_sentiment(comment_text)
    if clova_sentiment:
        for sentiment_kind in clova_sentiment['document']['confidence'].keys():
            sentiment[sentiment_kind] = clova_sentiment['document']['confidence'][sentiment_kind]
        for sentiment_item in clova_sentiment['sentences']:
            sentiment_result = sentiment_item['sentiment']
            sentiment['comments'][sentiment_result].append(sentiment_item['content'])

    return sentiment


def get_trend_public_opinion(comments_df):
    trend_public_opinion = {
        'high_sympathy': comments_df.sort_values(by='sympathy_count', ascending=False)[:10].to_dict(orient='records'),
        'high_interaction': comments_df.sort_values(by='total_interaction', ascending=False)[:10].to_dict(
            orient='records')
    }

    return trend_public_opinion


def get_public_opinion_summary(comments_df):
    chat = HCX003Chat(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv('CLOVA_CHAT_COMPLETION_003_CLIENT_KEY'),
        api_key_primary_val=os.getenv('CLOVA_CHAT_COMPLETION_003_CLIENT_KEY_PRIMARY_VAR'),
        request_id=os.getenv('CLOVA_CHAT_COMPLETION_003_CLIENT_KEY_REQUEST_ID'),
    )

    sorted_by_sympathy_count = comments_df.sort_values(by='sympathy_count', ascending=False)

    top_10_comments = sorted_by_sympathy_count.head(10)
    comment_text = ''
    for index, row in top_10_comments.iterrows():
        comment_text += '\n' + row['contents']
    if not comment_text:
        return None
    preset_text = [{"role": "system",
                    "content": "- 댓글을 요약하는 AI 어시스턴트입니다."
                               "- 반드시 댓글 내용에 관한 내용만 출력합니다."
                               "- 예를 들어, “찬성 의견이 60% 이상입니다” 또는 “주요 우려 사항은 X입니다”와 같은 분석 결과를 제공합니다."
                               "- 최소 300자 이내로 내용을 출력합니다."
                    },
                   {"role": "user", "content": f"{comment_text}"}]

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
    public_opinion_summary = None
    try_count = 0
    while public_opinion_summary is None:

        if try_count >= 100:
            break

        public_opinion_summary = chat.execute(request_data)
        if public_opinion_summary is None:
            time.sleep(5)
        try_count += 1

    return public_opinion_summary


def get_public_opinion(clusters):
    comments_df = get_comments_from_clusters(clusters)

    word_frequency = get_word_frequency(comments_df)
    sentiment = get_public_opinion_sentiment(comments_df)
    trend_public_opinion = get_trend_public_opinion(comments_df)
    public_opinion_summary = get_public_opinion_summary(comments_df)

    return comments_df, word_frequency, sentiment, trend_public_opinion, public_opinion_summary


if __name__ == '__main__':
    pass

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

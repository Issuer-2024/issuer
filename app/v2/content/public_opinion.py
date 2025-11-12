import os
import time

import pandas as pd
from konlpy.tag import Okt

from app.v2.external_request import HCX003Chat
from app.v2.external_request.request_clova_sentimet import get_clova_sentiment
from app.v2.external_request.request_news_comments import RequestNewsComments
from dotenv import load_dotenv

load_dotenv()

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

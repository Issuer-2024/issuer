import json
from datetime import timedelta, datetime

import requests

target_news_api_platform_list = {
    "뉴시스": "https://media.naver.com/api/press/003/ranking?type=popular",
    "연합뉴스": "https://media.naver.com/api/press/001/ranking?type=popular",
    "한국경제": "https://media.naver.com/api/press/215/ranking?type=popular",
    "뉴스1": "https://media.naver.com/api/press/421/ranking?type=popular",
    "이데일리": "https://media.naver.com/api/press/018/ranking?type=popular",
    "헤럴드경제": "https://media.naver.com/api/press/016/ranking?type=popular",
    "서울신문": "https://media.naver.com/api/press/081/ranking?type=popular",
}
yesterday = datetime.now() - timedelta(days=1)
formatted_yesterday = yesterday.strftime('%Y%m%d')

headers = {
    'Referer': 'https://media.naver.com'
}


def get_news_rank(date=formatted_yesterday):
    news_list = []
    for platform, url in target_news_api_platform_list.items():
        raw = requests.get(url + f'&date={date}', headers=headers).text
        news_rank = json.loads(raw)

        news_list += (news_rank['articleList'])
    news_list.sort(key=lambda x: x['hitCount'], reverse=True)
    return [item['title'] for item in news_list[:10]]





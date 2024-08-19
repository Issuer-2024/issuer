import json
import re

import requests


def parse_url(url):
    match = re.search(r'/article/(\d+)/(\d+)', url)
    if match:
        media_id = match.group(1)
        article_id = match.group(2)
        return media_id, article_id

    else:
        return None, None


def get_news_summary(url):
    media_id, article_id = parse_url(url)
    if not media_id or not article_id:
        return {'title': '', 'summary': ''}
    try:
        url = f"https://tts.news.naver.com/article/{media_id}/{article_id}/summary"
        response = requests.get(url)

        if not response.status_code == 200:
            return {'title': '', 'summary': ''}

        raw = response.text
        json_data = json.loads(raw)
        news_summary = {'title': json_data['title'], 'summary': json_data['summary']}
        return news_summary
    except Exception as e:
        print("error in news_summary")
        return None

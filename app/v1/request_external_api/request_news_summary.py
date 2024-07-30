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
        return None
    try:
        url = f"https://tts.news.naver.com/article/{media_id}/{article_id}/summary"
        raw = requests.get(url).text
        json_data = json.loads(raw)
        news_summary = {'title': json_data['title'], 'summary': json_data['summary']}
        return news_summary
    except Exception as e:
        return None

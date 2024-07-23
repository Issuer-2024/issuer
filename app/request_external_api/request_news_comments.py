import json
import re

import requests

header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
    'accept': "*/*",
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'referer': 'https://n.news.naver.com'
}


class RequestNewsComments:

    def _parse_url(self, url):
        match = re.search(r'/article/(\d+)/(\d+)', url)
        if match:
            media_id = match.group(1)
            article_id = match.group(2)
            return media_id, article_id

        else:
            return None, None

    def get_news_comments(self, url, num=5):
        media_id, article_id = self._parse_url(url)
        if not media_id or not article_id:
            return None

        url = f"https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json?ticket=news&pool=cbox5&_callback=&lang=ko&country=KR&objectId=news{media_id}%2C{article_id}&pageSize={num}"
        html = requests.get(url, headers=header)
        comment_text = json.loads(html.text.replace('_callback(', '')[:-2])
        comments = [comment_info['contents'] for comment_info in comment_text['result']['commentList']]

        return comments
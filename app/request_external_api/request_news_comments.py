import re

class RequestNewsComments:

    def _parse_url(self, url):
        match = re.search(r'/article/(\d+)/(\d+)', url)
        if match:
            media_id = match.group(1)
            article_id = match.group(2)
            return media_id, article_id

        else:
            return None, None

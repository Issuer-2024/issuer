import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import traceback
from dotenv import load_dotenv

load_dotenv()

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

target_news_platform_list = {
    "뉴시스": "https://media.naver.com/press/003/ranking",
    "연합뉴스": "https://media.naver.com/press/001/ranking",
    "한국경제": "https://media.naver.com/press/215/ranking",
    "뉴스1": "https://media.naver.com/press/421/ranking",
    "이데일리": "https://media.naver.com/press/018/ranking",
    "헤럴드경제": "https://media.naver.com/press/016/ranking",
    "서울신문": "https://media.naver.com/press/081/ranking"
}


class NewsIssueLoader:

    def __init__(self):
        super().__init__()
        self.target_platforms = target_news_platform_list
        self.main_platform = 'News'

    def _get_news_items(self, elem):
        return elem.select('ul.press_ranking_list > li.as_thumb')

    def _get_news_rank(self, elem):
        return elem.select_one('em.list_ranking_num').get_text()

    def _get_news_title(self, elem):
        return elem.select_one('strong.list_title').get_text(strip=True)

    def _get_news_link(self, elem):
        return elem.select_one('a')['href']

    def _get_news_views(self, elem):
        news_view = None
        if elem.select_one('span.list_view'):
            news_view = int(elem.select_one('span.list_view')
                            .get_text(strip=True).replace(',', '')
                            .replace('조회수', ''))
        return news_view

    def parse(self, html):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            news_items = []

            ranking_box = soup.select('div.press_ranking_home > div.press_ranking_box')

            for sub_ranking in ranking_box:
                items = self._get_news_items(sub_ranking)
                for item in items:
                    news_items.append({
                        "순위": self._get_news_rank(item),
                        "제목": self._get_news_title(item),
                        "URL": self._get_news_link(item),
                        "조회수": self._get_news_views(item),
                    })

            return news_items
        except Exception as e:
            traceback.print_exc()
            return []

    def crawl_issues(self):
        all_issues = []
        for platform, url in self.target_platforms.items():
            issue_items = self.parse(requests.get(url).content)
            for i in range(len(issue_items)):
                issue_items[i]['플랫폼'] = platform
                issue_items[i]['상위 플랫폼'] = self.main_platform
                issue_items[i]['하위 플랫폼'] = platform
            all_issues += issue_items
        return all_issues



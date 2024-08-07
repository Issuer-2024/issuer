import requests
from bs4 import BeautifulSoup
from app.v2.external_request import get_news_summary


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

    news_list = [url for url in news_list if 'https://n.news.naver.com' in url]

    return news_list


def get_high_searching_days(estimated_search_amount):
    threshold = 20000

    high_searching_days = [item for item in estimated_search_amount if
                           item['ratio'] >= 5 and item['estimated'] > threshold]
    return high_searching_days


def get_high_searching_news(q, high_searching_days):
    news_items = []
    for high_searching_day in high_searching_days:
        date = high_searching_day['period'].replace('-', '')
        links = get_news_list_by_date(q, date)[:3]
        for link in links:
            summary = get_news_summary(link)
            title = summary['title']
            news_items.append({'pubDate': date, 'title': title, 'link': link})

    return news_items




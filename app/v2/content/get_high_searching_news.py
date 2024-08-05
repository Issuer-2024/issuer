import requests
from bs4 import BeautifulSoup

from app.v2.content.get_estimated_search_amount import get_estimated_search_amount

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
    result = []
    for high_searching_day in high_searching_days:
        date = high_searching_day['period'].replace('-', '')
        news = get_news_list_by_date(q, date)[:3]
        result.append({'date': date, 'news': news})

    return result


if __name__ == '__main__':
    keyword = "쯔양"
    from datetime import datetime, timedelta

    today = datetime.today()
    one_months_ago = (today - timedelta(days=30)).replace(day=1).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')

    keyword_groups = [
        {'groupName': keyword, 'keywords': [keyword]}
    ]
    from app.v2.external_request import RequestTrend

    trend_search_data = RequestTrend.get_naver_trend_search_data(one_months_ago,
                                                                 today,
                                                                 'date',
                                                                 keyword_groups)[0]['data']
    import pprint
    estimated_search_amount = get_estimated_search_amount(keyword, trend_search_data)
    get_high_searching_days = get_high_searching_days(estimated_search_amount)
    pprint.pprint(get_high_searching_news(keyword, get_high_searching_days))





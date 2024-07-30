def get_news_list_by_crawling(q: str, date: str):
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

    return news_list
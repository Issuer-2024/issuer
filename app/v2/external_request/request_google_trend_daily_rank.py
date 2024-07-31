import requests
import xml.etree.ElementTree as ET


def get_google_trend_daily_rank():
    # RSS 피드 URL
    url = 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR'

    # RSS 피드 데이터 가져오기
    response = requests.get(url)
    response.raise_for_status()  # 요청이 성공했는지 확인

    # XML 파싱
    root = ET.fromstring(response.content)

    # 제목 추출
    titles = []
    for item in root.findall('.//item'):
        title = item.find('title').text
        titles.append(title)

    return titles

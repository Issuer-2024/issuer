from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

target_news_platform_list = {
        "뉴시스": "https://media.naver.com/press/003/ranking",
        "연합뉴스": "https://media.naver.com/press/001/ranking",
        "한국경제": "https://media.naver.com/press/215/ranking",
        "머니투데이": "https://media.naver.com/press/008/ranking",
        "뉴스1": "https://media.naver.com/press/421/ranking",
        "이데일리": "https://media.naver.com/press/018/ranking",
        "헤럴드경제": "https://media.naver.com/press/016/ranking",
        "서울신문": "https://media.naver.com/press/081/ranking"
    }
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

load_dotenv()

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')


class NewsCommentsCrawler:

    # def _wait_more_btn(self):
    #     while True:
    #         try:
    #             WebDriverWait(self.driver, 3).until(
    #                 EC.presence_of_element_located((By.LINK_TEXT, "더보기"))
    #             )
    #             more_button = self.driver.find_element(by=By.LINK_TEXT, value='더보기')
    #             more_button.click()
    #         except Exception as e:
    #             break

    def _get_text(self, elem):
        return elem.select_one(
            "div.u_cbox_text_wrap span.u_cbox_contents").text.strip().replace(
            '\n', '')

    def _get_recomm(self, elem):
        return int(elem.select_one('em.u_cbox_cnt_recomm').text.strip())

    def _get_unrecomm(self, elem):
        return int(elem.select_one('em.u_cbox_cnt_unrecomm').text.strip())

    def _get_reply_num(self, elem):
        return int(elem.select_one('span.u_cbox_reply_cnt').text.strip())

    def parse(self, url: str):
        driver = webdriver.Remote(
            command_executor=os.getenv('WEB_DRIVER_HUB_URL'),
            options=chrome_options
        )
        driver.get(url)
        # 페이지 소스 파싱
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "MY댓글"))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")

        if int(soup.select("span.u_cbox_info_txt")[0].text.replace(',', '').strip()) <= 30:
            driver.quit()
            node_url = os.getenv('WEB_DRIVER_HUB_URL') + '/session/' + driver.session_id  # 노드 URL 및 세션 ID 설정
            response = requests.delete(node_url)
            return None

        # 댓글 추출
        comments = []
        title = soup.select("h2#title_area")[0].text.strip()
        comment_elements = soup.select("ul.u_cbox_list li.u_cbox_comment")
        trend_score = 0
        for comment_element in comment_elements[:5]:

            if comment_element.select_one("div.u_cbox_text_wrap span.u_cbox_contents"):  #pi 댓글 처리
                trend_score += self._get_recomm(comment_element) + self._get_unrecomm(
                    comment_element) + self._get_reply_num(comment_element)
                comments.append(self._get_text(comment_element))
                    # comments.append({
                    #     "내용": self._get_text(comment_element),
                    #     #"공감 비율": self._get_recomm(comment_element) / (self._get_unrecomm(comment_element)+1),
                    #     #"대댓글 수": self._get_reply_num(comment_element)
                    # })
            else:
                continue
        driver.quit()
        node_url = os.getenv('WEB_DRIVER_HUB_URL') + '/session/' + driver.session_id  # 노드 URL 및 세션 ID 설정
        response = requests.delete(node_url)
        return {"링크": url, "제목": title, "댓글": comments, "트랜드 수치": trend_score}

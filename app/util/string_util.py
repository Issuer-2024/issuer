import re


class StringUtil:
    @staticmethod
    def clean_and_extract_korean_english(text):
        clean_text = re.sub(r'(&quot;|<[^>]*>|\\)', '', text)  # HTML 태그와 특수 문자를 제거
        korean_english_text = re.findall(r'[가-힣a-zA-Z0-9]+', clean_text)  # 한글과 영어 문자만 추출하는 정규 표현식
        return ' '.join(korean_english_text)  # 추출한 문자열들을 공백으로 이어 붙여서 반환

    @staticmethod
    def extract_first_two_parentheses_content(text):
        pattern = r'\(([^)]+)\)'  # 정규 표현식으로 첫 번째와 두 번째 괄호 안의 내용 추출
        matches = re.findall(pattern, text)

        if len(matches) >= 2:  # 첫 번째와 두 번째 괄호 안의 내용만 반환
            return matches[:2]
        else:
            return matches

    @staticmethod
    def convert_news_url_to_comment_url(news_url):
        pattern = r"(https://n\.news\.naver\.com/mnews/article/)(\d+/\d+)(\?.*)"  # 뉴스 URL의 정규식 패턴
        replacement = r"\1comment/\2\3"

        comment_url = re.sub(pattern, replacement, news_url)  # 정규식을 사용하여 댓글 URL로 변환

        return comment_url

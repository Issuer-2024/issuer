import re


class StringUtil:
    @staticmethod
    def clean_and_extract_korean_english(text):
        clean_text = re.sub(r'(&quot;|<[^>]*>|\\)', '', text)  # HTML 태그와 특수 문자를 제거
        korean_english_text = re.findall(r'[가-힣a-zA-Z0-9]+', clean_text)  # 한글과 영어 문자만 추출하는 정규 표현식
        return ' '.join(korean_english_text)  # 추출한 문자열들을 공백으로 이어 붙여서 반환

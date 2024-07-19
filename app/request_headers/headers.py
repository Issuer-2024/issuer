import os

NAVER_API_HEADERS = {
    'X-Naver-Client-Id': os.getenv('NAVER_API_CLIENT_ID'),
    'X-Naver-Client-Secret': os.getenv('NAVER_API_CLIENT_SECRET'),
}

CLOVA_API_HEADERS = {
    "X-NCP-APIGW-API-KEY-ID": os.getenv('CLOVA_API_CLIENT_ID'),
    "X-NCP-APIGW-API-KEY": os.getenv('CLOVA_API_CLIENT_SECRET'),
    "Content-Type": "application/json"
}

CLOVA_SUMMARY_API_ENDPOINT = "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize"
import json
import os

import requests


SENTIMENT_API_URL = "https://naveropenapi.apigw.ntruss.com/sentiment-analysis/v1/analyze"


def get_clova_sentiment(content):
    headers = {
        "X-NCP-APIGW-API-KEY-ID": os.getenv("CLOVA_API_CLIENT_ID"),
        "X-NCP-APIGW-API-KEY": os.getenv("CLOVA_API_CLIENT_SECRET"),
        "Content-Type": "application/json",
    }
    response = requests.post(
        SENTIMENT_API_URL,
        data=json.dumps({"content": content}),
        headers=headers,
    )
    if response.status_code == 200:
        return response.json()
    return None

import os

import requests
import json

headers = {
    "X-NCP-APIGW-API-KEY-ID": os.getenv('CLOVA_API_CLIENT_ID'),
    "X-NCP-APIGW-API-KEY": os.getenv('CLOVA_API_CLIENT_SECRET'),
    "Content-Type": "application/json"
}


def get_clova_sentiment(content):
    url = "https://naveropenapi.apigw.ntruss.com/sentiment-analysis/v1/analyze"
    data = {
        "content": content
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error : " + response.text)

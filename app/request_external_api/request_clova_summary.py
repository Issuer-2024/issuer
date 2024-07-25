import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "X-NCP-APIGW-API-KEY-ID": os.getenv('CLOVA_API_CLIENT_ID'),
    "X-NCP-APIGW-API-KEY": os.getenv('CLOVA_API_CLIENT_SECRET'),
    "Content-Type": "application/json"
}


def get_clova_summary(title="", content=""):
    language = "ko"  # Language of document (ko, ja )
    model = "news"  # Model used for summaries (general, news)
    tone = "2"  # Converts the tone of the summarized result. (0, 1, 2, 3)
    summary_count = "3"  # This is the number of sentences for the summarized document.
    url = "https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize"

    data = {
        "document": {
            "title": title,
            "content": content
        },
        "option": {
            "language": language,
            "model": model,
            "tone": tone,
            "summaryCount": summary_count
        }
    }

    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        return response.json()['summary']
    else:
        print("Error : " + response.text)
        return None

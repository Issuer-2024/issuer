import os

import requests


class HCX003Chat:
    def __init__(self, host, api_key, api_key_primary_val, request_id):
        self._host = host
        self._api_key = api_key
        self._api_key_primary_val = api_key_primary_val
        self._request_id = request_id

    def _mock_completion(self, completion_request):
        """TEST 모드용 가짜 응답"""
        return {
            "status": {
                "code": "20000",
                "message": "OK"
            },
            "result": {
                "message": {
                    "role": "assistant",
                    "content": "문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 "
                               "일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, "
                               "내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 "
                               "당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 "
                               "만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: "
                               "오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 "
                               "기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, "
                               "내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 "
                               "당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 "
                               "만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: "
                               "오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 "
                               "기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, "
                               "내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 "
                               "당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 "
                               "만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: "
                               "오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 "
                               "기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, "
                               "내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 "
                               "당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 "
                               "만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: "
                               "오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 "
                               "기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, "
                               "내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 "
                               "당신의 삶을 더욱 풍요롭게 만들어 줄 것입니다.\n문구: 오늘 하루 있었던 일들을 기록하며, 내일을 준비하세요. 다이어리는 당신의 삶을 더욱 풍요롭게 "
                               "만들어 줄 것입니다.\n"
                },
                "stopReason": "LENGTH",
                "inputLength": 100,
                "outputLength": 10,
                "aiFilter": [
                    {
                        "groupName": "curse",
                        "name": "insult",
                        "score": "1"
                    },
                    {
                        "groupName": "curse",
                        "name": "discrimination",
                        "score": "0"
                    },
                    {
                        "groupName": "unsafeContents",
                        "name": "sexualHarassment",
                        "score": "2"
                    }
                ]
            }
        }

    def execute(self, completion_request):

        if os.getenv("ENV") == "TEST":
            res = self._mock_completion(completion_request)
            return res["result"]["message"]["content"]

        headers = {
            'X-NCP-CLOVASTUDIO-API-KEY': self._api_key,
            'X-NCP-APIGW-API-KEY': self._api_key_primary_val,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json'
        }

        response = requests.post(self._host + '/testapp/v1/chat-completions/HCX-003',
                                 headers=headers, json=completion_request)

        if response.status_code == 200:
            return response.json()['result']['message']['content']

        else:
            print("Error : " + response.text)
            return None



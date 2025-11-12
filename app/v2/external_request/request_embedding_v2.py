import json
import http.client
import os

import numpy as np


class EmbeddingV2Executor:
    def __init__(self, host, api_key, api_key_primary_val, request_id):
        self._host = host
        self._api_key = api_key
        self._api_key_primary_val = api_key_primary_val
        self._request_id = request_id

    def _send_request(self, completion_request):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'X-NCP-CLOVASTUDIO-API-KEY': self._api_key,
            'X-NCP-APIGW-API-KEY': self._api_key_primary_val,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id
        }

        conn = http.client.HTTPSConnection(self._host)
        conn.request('POST', '/testapp/v1/api-tools/embedding/v2/1196e580236e4d2a814946b6e37efe45', json.dumps(completion_request), headers)
        response = conn.getresponse()
        result = json.loads(response.read().decode(encoding='utf-8'))
        conn.close()
        return result

    def _mock_embedding(self):
        """1024차원 랜덤 mock embedding"""
        return {
            "status": {"code": "20000", "message": "OK"},
            "result": {
                "embedding": np.random.uniform(-1, 1, 1024).round(7).tolist(),
                "inputTokens": 4
            }
        }

    def execute(self, completion_request):
        if os.getenv("ENV") == "TEST":
            return self._mock_embedding()

        res = self._send_request(completion_request)
        if res['status']['code'] == '20000':
            return res['result']['embedding']
        else:
            return 'Error'
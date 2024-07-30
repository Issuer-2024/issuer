import requests


class CompletionExecutor:
    def __init__(self, host, api_key, api_key_primary_val, request_id):
        self._host = host
        self._api_key = api_key
        self._api_key_primary_val = api_key_primary_val
        self._request_id = request_id

    def execute(self, completion_request):
        headers = {
            'X-NCP-CLOVASTUDIO-API-KEY': self._api_key,
            'X-NCP-APIGW-API-KEY': self._api_key_primary_val,
            'X-NCP-CLOVASTUDIO-REQUEST-ID': self._request_id,
            'Content-Type': 'application/json; charset=utf-8',
            'Accept': 'application/json'
        }

        response = requests.post(self._host + '/testapp/v1/chat-completions/HCX-DASH-001',
                                 headers=headers, json=completion_request)

        if response.status_code == 200:
            return response.json()['result']['message']['content']
        else:
            response.raise_for_status()

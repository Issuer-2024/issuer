import os
import time
import requests

import hashlib
import hmac
import base64

from dotenv import load_dotenv

load_dotenv()


class Signature:

    @staticmethod
    def generate(timestamp, method, uri, secret_key):
        message = "{}.{}.{}".format(timestamp, method, uri)
        hash = hmac.new(bytes(secret_key, "utf-8"), bytes(message, "utf-8"), hashlib.sha256)

        hash.hexdigest()
        return base64.b64encode(hash.digest())


def get_header(method, uri, api_key, secret_key, customer_id):
    timestamp = str(round(time.time() * 1000))
    signature = Signature.generate(timestamp, method, uri, secret_key)

    return {'Content-Type': 'application/json; charset=UTF-8', 'X-Timestamp': timestamp,
            'X-API-KEY': api_key, 'X-Customer': str(customer_id), 'X-Signature': signature}


def get_search_amount(hintKeywords):
    BASE_URL = 'https://api.naver.com'
    API_KEY = os.getenv('NAVER_AD_API_KEY')
    SECRET_KEY = os.getenv('NAVER_AD_SECRET_KEY')
    CUSTOMER_ID = os.getenv('NAVER_AD_CUSTOMER_ID')

    uri = '/keywordstool'
    method = 'GET'

    params = {}
    hintKeywords = hintKeywords.replace(' ', '')
    params['hintKeywords'] = hintKeywords
    params['showDetail'] = '1'

    r = requests.get(BASE_URL + uri, params=params,
                     headers=get_header(method, uri, API_KEY, SECRET_KEY, CUSTOMER_ID))

    try:
        # return pd.DataFrame(r.json()['keywordList'])
        result = r.json()['keywordList'][0]
        return int(result['monthlyMobileQcCnt']) + int(result['monthlyPcQcCnt'])
    except Exception as e:
        return None

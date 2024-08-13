import datetime

from redis_om import NotFoundError

from app.v2.redis.model.api_call_count import APICallCount

RATE_LIMIT = 300
TIME_PERIOD = 60 * 60 * 24


def check_rate_limit():
    try:
        api_call_count = APICallCount.find().first()
        if api_call_count.count > RATE_LIMIT:
            return {'status': False, 'count': api_call_count.count, 'message': '금일 할당량을 초과했습니다.'}

        api_call_count.count += 1
        api_call_count.save()
        return {'status': True, 'count': api_call_count.count}

    except NotFoundError as e:
        api_call_count = APICallCount(count=1, last_call=datetime.datetime.now())
        api_call_count.save()
        api_call_count.expire(TIME_PERIOD)
        return {'status': True, 'count': api_call_count.count}

    except Exception as e:
        return {'status': False, 'count': str(e)}

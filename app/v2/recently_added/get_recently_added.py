from datetime import datetime

import pytz

from app.v2.model.recently_added import RecentlyAdded
from app.v2.redis.model import ContentHash


def calculate_elapsed_time(created_at_str: str) -> str:
    # 현재 시간을 한국 시간대로 설정
    KST = pytz.timezone('Asia/Seoul')
    now = datetime.now(KST)

    # created_at을 datetime 객체로 변환하고 한국 시간대로 설정
    created_at_naive = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
    created_at = KST.localize(created_at_naive)

    # elapsed_time 계산
    elapsed_time = now - created_at

    # 초, 분, 시간 단위로 변환
    total_seconds = abs(int(elapsed_time.total_seconds()))
    if total_seconds < 60:
        return f"{total_seconds}초 전"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}분 전"
    else:
        hours = total_seconds // 3600
        return f"{hours}시간 전"


def get_recently_added_sep():
    limit = 10
    query = ContentHash.find()
    items = sorted([content for content in query], key=lambda x: x.created_at, reverse=True)

    recently_added_list = [
        RecentlyAdded(
            keyword=item.keyword,
            elapsed_time=calculate_elapsed_time(item.created_at)
        )
        for item in items[:limit]
    ]
    return recently_added_list


def get_recently_added_all():
    query = ContentHash.find()
    items = sorted([content for content in query], key=lambda x: x.created_at, reverse=True)

    recently_added_list = [
        RecentlyAdded(
            keyword=item.keyword,
            elapsed_time=calculate_elapsed_time(item.created_at)
        )
        for item in items[:]
    ]
    return recently_added_list

from datetime import datetime

import pytz

from app.v2.model.creating import Creating
from app.v2.redis.model.creating_hash import CreatingHash


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


def get_creating_sep():
    limit = 10
    query = CreatingHash.find()
    items = sorted([creating for creating in query], key=lambda x: x.started_at, reverse=True)

    creating_list = [
        Creating(
            keyword=item.keyword,
            elapsed_time=calculate_elapsed_time(item.started_at)
        )
        for item in items[:limit]
    ]
    return creating_list

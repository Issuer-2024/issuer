import json
import uuid
from datetime import datetime
from app.v2.content import create_content
from app.v2.redis import redis_connection


def acquire_lock(lock_key: str, ttl: int = 60) -> bool:
    # SET key value NX EX ttl
    # 성공하면 True, 이미 있으면 False
    redis_client = redis_connection.redis_client
    return redis_client.set(lock_key, "1", nx=True, ex=ttl) is True


def release_lock(lock_key: str):
    redis_client = redis_connection.redis_client
    redis_client.delete(lock_key)


def enqueue_issue_job(keyword: str) -> str:
    redis_client = redis_connection.redis_client
    job_id = str(uuid.uuid4())

    job = {
        "job_id": job_id,
        "payload": {
            "keyword": keyword,
        },
        "retry": 0,
        "created_at": datetime.utcnow().isoformat(),
    }

    # 큐에 작업 넣기 (worker_loop에서 BRPOP으로 꺼냄)
    redis_client.lpush("issue_jobs", json.dumps(job))

    return job_id


def worker_loop():
    redis_client = redis_connection.redis_client
    while True:
        _, raw_job = redis_client.brpop("issue_jobs")
        job = json.loads(raw_job)
        handle_job(job)


def handle_job(job):
    redis_client = redis_connection.redis_client
    job_id = job["job_id"]
    keyword = job["payload"]["keyword"]

    lock_key = f"lock:issue:{keyword}"  # 혹은 전체 공용 lock:global_issue

    # 1. 락 먼저 시도
    if not acquire_lock(lock_key, ttl=60):
        # 이미 실행중인 작업이 있으면, 나중에 다시 실행하도록 재큐잉
        retry_count = job.get("retry", 0)
        if retry_count < 5:
            job["retry"] = retry_count + 1
            # backoff 설계
            redis_client.lpush("issue_jobs", json.dumps(job))
        else:
            # 재시도 횟수 초과 → dead-letter 큐로 보내거나 로그만 남김
            redis_client.lpush("issue_jobs:dead", json.dumps(job))
        return

    try:
        # 2. 이 키워드에 대해 실행
        result = create_content(keyword)
        redis_client.hset(f"job:{job_id}", mapping={
            "status": "SUCCESS",
            "result": json.dumps(result)
        })
    except Exception as e:
        redis_client.hset(f"job:{job_id}", mapping={
            "status": "FAILED",
            "error": str(e)
        })
    finally:
        # 3. 실행 끝나면 락 해제
        release_lock(lock_key)

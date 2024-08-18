import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from dotenv import load_dotenv
from redis_om import Migrator

from app.v2.external_request.request_embedding_v2 import EmbeddingV2Executor
from app.v2.redis.model.comments_embedding import CommentsEmbedding

load_dotenv()

embedding_v2_executor = EmbeddingV2Executor(
    host='clovastudio.apigw.ntruss.com',
    api_key=os.getenv('CLOVA_EMBEDDING_CLIENT_KEY'),
    api_key_primary_val=os.getenv('CLOVA_EMBEDDING_CLIENT_KEY_PRIMARY_VAR'),
    request_id=os.getenv('CLOVA_EMBEDDING_V2_REQUEST_ID')
)


def get_embedding(text):
    request_data = {"text": text}
    embedding = embedding_v2_executor.execute(request_data)
    while embedding == 'Error':
        embedding = embedding_v2_executor.execute(request_data)
        time.sleep(1)
    return embedding


def cosine_similarity(embedding1, embedding2):
    dot_product = np.dot(embedding1, embedding2)
    norm_embedding1 = np.linalg.norm(embedding1)
    norm_embedding2 = np.linalg.norm(embedding2)
    return dot_product / (norm_embedding1 * norm_embedding2)


def save_comments_embedding(q, comments_df):
    #1. embedding executor v2 환경변수 추가
    #2. Embedding executor 생성
    #3. Embedding executor 임베딩하기 (속도 빠르게)
    #4. 결과 저장하기
    #5. 비슷한 댓글 찾기 기능 구현하기

    sorted_by_sympathy_count = comments_df.sort_values(by='sympathy_count', ascending=False)

    embedding_targets = sorted_by_sympathy_count.head(20).to_dict(orient='records')

    embedding_results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_item = {executor.submit(get_embedding, item['contents']): item for item in embedding_targets}
        for future in as_completed(future_to_item):
            embedding = future.result()
            embedding_results.append((embedding, future_to_item[future]))

    comments_embedding = CommentsEmbedding(keyword=q, embedding_results=embedding_results)
    comments_embedding.save()
    comments_embedding.expire(7200)


def read_comments_embedding(q):
    Migrator().run()  # 마이그레이션 실행
    keys = CommentsEmbedding.find(CommentsEmbedding.keyword == q).all()  # 키워드에 해당하는 모든 키 찾기

    if not keys:
        return None

    # 첫 번째 키에 해당하는 데이터를 압축 해제하여 반환
    content = CommentsEmbedding.get_decompressed(keys[0].pk)
    return content


def find_similar_opinion(q, user_opinion):
    comments_embedding = read_comments_embedding(q)

    if not comments_embedding:
        return None
    user_opinion_embedding = get_embedding(user_opinion)
    embedding_results = comments_embedding.embedding_results
    for i in range(len(embedding_results)):
        embedding, item = embedding_results[i]
        embedding_results[i][1]['similarity'] = cosine_similarity(user_opinion_embedding, embedding)

    embedding_results.sort(key=lambda comment: comment[1]['similarity'], reverse=True)

    return [item for embedding, item in embedding_results]

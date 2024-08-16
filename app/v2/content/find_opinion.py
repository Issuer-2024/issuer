import os
import time
import numpy as np
from app.v2.external_request.request_embedding_v2 import EmbeddingV2Executor
from dotenv import load_dotenv

from app.v2.redis.model.comments_embedding import CommentsEmbedding

load_dotenv()


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

    embedding_v2_executor = EmbeddingV2Executor(
        host='clovastudio.apigw.ntruss.com',
        api_key=os.getenv('CLOVA_EMBEDDING_CLIENT_KEY'),
        api_key_primary_val=os.getenv('CLOVA_EMBEDDING_CLIENT_KEY_PRIMARY_VAR'),
        request_id=os.getenv('CLOVA_EMBEDDING_V2_REQUEST_ID')
    )

    def get_embedding(item):
        request_data = {"text": item['contents']}
        embedding = embedding_v2_executor.execute(request_data)
        while embedding == 'Error':
            embedding = embedding_v2_executor.execute(request_data)
            time.sleep(1)
        return embedding

    embedding_result = []
    sorted_by_sympathy_count = comments_df.sort_values(by='sympathy_count', ascending=False)

    for index, row in sorted_by_sympathy_count.head(20).iterrows():
        embedding = get_embedding(row)
        embedding_result.append(embedding)
        comments_df.at[index, 'embedding'] = embedding

    comments_embedding_result = sorted_by_sympathy_count.head(20).to_dict(orient='records')

    comments_embedding = CommentsEmbedding(keyword=q, comments_embedding=comments_embedding_result)
    comments_embedding.save()


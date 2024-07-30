from app.v1.request_external_api import get_news_rank
from app.v1.util import CompletionExecutor
from dotenv import load_dotenv
import ast
import os
load_dotenv()


def get_keyword_suggestion():
    # news_issue_loader = NewsIssueLoader()
    # issue_data = news_issue_loader.crawl_issues()
    # issue_data.sort(key=lambda x: x['조회수'], reverse=True)
    # document = [item['제목'] for item in issue_data[:10]]
    document = get_news_rank()

    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY"),
        api_key_primary_val=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY_PRIMARY_VAR"),
        request_id=os.getenv("CLOVA_CHAT_COMPLETION_REQUEST_ID")
    )
    preset_text = [{"role": "system",
                    "content": "키워드를 추출하는 AI 어시스턴트 입니다."
                               "### 지시사항\n"
                               "- 문서에서 키워드를 추출합니다.\n"
                               "- 키워드는 핵심 단어 1개입니다.\n"
                               "- json 형식으로 답변합니다.\n"
                               "- 핵심 단어는 인물 이름을 우선 순위로 추출합니다."
                               "\n## 응답형식:['키워드1', '키워드2']"},
                   {"role": "user", "content": f"{document}"}]

    request_data = {
        'messages': preset_text,
        'topP': 0.8,
        'topK': 0,
        'maxTokens': 128,
        'temperature': 0.1,
        'repeatPenalty': 1.0,
        'stopBefore': [],
        'includeAiFilters': False,
        'seed': 0
    }
    result = completion_executor.execute(request_data)
    try:
        data = ast.literal_eval(result)
    except Exception as e:
        return []
    return data

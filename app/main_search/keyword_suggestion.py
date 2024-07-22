from app.util import CompletionExecutor, NewsIssueLoader
from dotenv import load_dotenv
import ast
import os
load_dotenv()


def get_keyword_suggestion():
    news_issue_loader = NewsIssueLoader()
    issue_data = news_issue_loader.crawl_issues()

    completion_executor = CompletionExecutor(
        host='https://clovastudio.stream.ntruss.com',
        api_key=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY"),
        api_key_primary_val=os.getenv("CLOVA_CHAT_COMPLETION_CLIENT_KEY_PRIMARY_VAR"),
        request_id=os.getenv("CLOVA_CHAT_COMPLETION_REQUEST_ID")
    )
    data = []
    for item in issue_data[:3]:
        preset_text = [{"role": "system",
                        "content": "댓글을 분석하는 AI 어시스턴트 입니다."
                                   "### 지시사항\n- 문서에서 핵심 키워드 최대 2개를 추출합니다.\n- 키워드는 핵심 주제와 상응하는 우선순위로 꼭 json 형식으로 답변합니다.\n- 각각의 핵심 키워드는 2단어 이하로 조합해서 추출합니다.\n## 응답형식:['키워드1', '키워드2']"},
                       {"role": "user", "content": f"{item['제목']}"}]

        request_data = {
            'messages': preset_text,
            'topP': 0.8,
            'topK': 0,
            'maxTokens': 256,
            'temperature': 0.5,
            'repeatPenalty': 1.0,
            'stopBefore': [],
            'includeAiFilters': False,
            'seed': 0
        }
        result = completion_executor.execute(request_data)
        print(result)
        try:
            tmp = ast.literal_eval(result)
            data += tmp
        except Exception as e:
            continue
    return data

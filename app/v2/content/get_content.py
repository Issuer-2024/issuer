import json
import pprint
from datetime import datetime, timedelta

from pyee import BaseEventEmitter

from app.v2.content.find_opinion import save_comments_embedding
from app.v2.content.get_estimated_search_amount import get_estimated_search_amount
from app.v2.content.issue_info import collect_issues, create_embedding_result, cluster_issues, create_group_title, \
    create_group_content
from app.v2.content.public_opinion import get_public_opinion
from app.v2.content.suggestion_trend import get_suggestions_trend_data
from app.v2.external_request import RequestTrend
from app.v2.model.content import Content
from app.v2.redis.redis_manager import RedisManager

emitter = BaseEventEmitter()
all_q = []


def get_content(keyword: str):
    content = RedisManager.read_content(keyword)
    if content:
        return content
    return None


def create_content(q: str):
    print(q)
    emitter.emit('content_loader', {'target': q, 'message': '수집 준비중', 'ratio': 0})
    title = q
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    today = datetime.today()
    one_months_ago = (today - timedelta(days=30)).replace(day=1).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')

    keyword_groups = [
        {'groupName': q, 'keywords': [q]}
    ]

    trend_search_data = RequestTrend.get_naver_trend_search_data(one_months_ago,
                                                                 today,
                                                                 'date',
                                                                 keyword_groups)[0]['data']
    estimated_search_amount = get_estimated_search_amount(q, trend_search_data)

    emitter.emit('content_loader', {'target': q, 'message': '이슈 수집중', 'ratio': 20})
    issues = collect_issues(q)
    embedding_result = create_embedding_result(issues)
    emitter.emit('content_loader', {'target': q, 'message': '이슈 요약중', 'ratio': 40})
    clustered_issues = cluster_issues(embedding_result)
    group_title = create_group_title(clustered_issues)
    group_content = create_group_content(clustered_issues)

    emitter.emit('content_loader', {'target': q, 'message': '여론 분석중', 'ratio': 60})
    (comments_df,
     public_opinion_word_frequency,
     public_opinion_sentiment,
     public_opinion_trend,
     public_opinion_summary) = get_public_opinion(clustered_issues)

    save_comments_embedding(q, comments_df)

    emitter.emit('content_loader', {'target': q, 'message': '보고서 생성중', 'ratio': 80})
    keyword_suggestions_data = get_suggestions_trend_data(q)

    table_of_contents = [{'title': "개요", 'depth': 0, 'num': '1'}, {'title': "현재 이슈", 'depth': 0, 'num': '2'}]
    table_of_contents += [
        {'title': title, 'depth': 1, 'num': '2.' + str(i + 1)} for i, title in enumerate(group_title.values())
    ]

    body = [{'title': "개요", 'content': "", 'num': '1'}, {'title': "현재 이슈", 'content': "", 'num': '2'}]
    body += [
        {'ref': ref,
         'title': title,
         'content': content, 'num': '2.' + str(i + 1)
         }
        for i, (ref, title, content) in
        enumerate(zip(clustered_issues.values(), group_title.values(), group_content.values()))
    ]

    table_of_public_opinion = [
        {'title': "여론 요약", 'depth': 0, 'num': '1'},
        {'title': "공감 수가 높은 댓글", 'depth': 0, 'num': '2'},
        {'title': "상호 작용이 많은 댓글", 'depth': 0, 'num': '3'},
        {'title': "키워드 별 댓글", 'depth': 0, 'num': '4'}
    ]

    keywords = [item['keyword'] for item in public_opinion_word_frequency[:10]]
    table_of_public_opinion += [{'title': keyword, 'depth': 1, 'num': '4.' + str(i + 1)}
                                for i, keyword in enumerate(keywords)]
    table_of_public_opinion += [{'title': "감정별 댓글", 'depth': 0, 'num': '5'}]

    result = Content(title,
                     created_at,
                     estimated_search_amount,
                     keyword_suggestions_data,
                     public_opinion_sentiment,
                     public_opinion_word_frequency,
                     table_of_contents,
                     body,
                     table_of_public_opinion,
                     public_opinion_trend,
                     public_opinion_summary)

    RedisManager.save_content(result)
    emitter.emit('content_loader', {'target': q, 'message': '완료', 'ratio': 100})

    RedisManager.remove_creating(q)


@emitter.on('content_loader')
def event_listener(message):
    creating = RedisManager.read_creating(message['target'])
    creating.ratio = message['ratio']
    creating.status = message['message']
    creating.save()
    for q in all_q:
        q.put(message)


if __name__ == '__main__':
    emitter = BaseEventEmitter()
    create_content("코스피")

import queue
import time
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
from app.v2.redis.redis_util import read_cache_content, save_to_caching, save_creating, remove_creating, read_creating

emitter = BaseEventEmitter()


def get_content(q: str):
    caching = read_cache_content(q)
    if caching:
        return caching
    return None


def create_content(q: str):

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
    a = collect_issues(q)
    b = create_embedding_result(a)
    emitter.emit('content_loader', {'target': q, 'message': '이슈 요약중', 'ratio': 40})
    c = cluster_issues(b)
    d = create_group_title(c)
    e = create_group_content(c)

    emitter.emit('content_loader', {'target': q, 'message': '여론 분석중', 'ratio': 60})
    (comments_df,
     public_opinion_word_frequency,
     public_opinion_sentiment,
     public_opinion_trend,
     public_opinion_summary) = get_public_opinion(c)

    save_comments_embedding(q, comments_df)

    emitter.emit('content_loader', {'target': q, 'message': '보고서 생성중', 'ratio': 80})
    keyword_suggestions_data = get_suggestions_trend_data(q)

    table_of_contents = [{'title': "개요", 'depth': 0, 'num': '1'}, {'title': "현재 이슈", 'depth': 0, 'num': '2'}]
    table_of_contents += [{'title': title, 'depth': 1, 'num': '2.' + str(i + 1)} for i, title in enumerate(d.values())]

    body = [{'title': "개요", 'content': "", 'num': '1'}, {'title': "현재 이슈", 'content': "", 'num': '2'}]
    body += [{'ref': ref, 'title': title, 'content': content, 'num': '2.' + str(i + 1)}
             for i, (ref, title, content) in enumerate(zip(c.values(), d.values(), e.values()))]

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
    save_to_caching(result)
    emitter.emit('content_loader', {'target': q, 'message': '완료', 'ratio': 100})

    remove_creating(q)


event_queue = queue.Queue()
all_q = []

@emitter.on('content_loader')
def event_listener(message):

    creating = read_creating(message['target'])
    creating.ratio = message['ratio']
    creating.status = message['message']
    creating.save()
    for q in all_q:
        q.put(message)


if __name__ == '__main__':
    q = "쯔양"
    title = q
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Record the start time of the entire process
    start_time = time.time()

    today = datetime.today()
    one_months_ago = (today - timedelta(days=30)).replace(day=1).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')

    # Record the time taken for setting up date variables
    date_setup_time = time.time()
    print(f"Time taken for date setup: {date_setup_time - start_time} seconds")

    keyword_groups = [
        {'groupName': q, 'keywords': [q]}
    ]

    # Measure time for trend search data retrieval
    trend_search_start = time.time()
    trend_search_data = RequestTrend.get_naver_trend_search_data(one_months_ago, today, 'date', keyword_groups)[0][
        'data']
    trend_search_time = time.time()
    print(f"Time taken for trend search data retrieval: {trend_search_time - trend_search_start} seconds")

    # Measure time for estimated search amount calculation
    estimated_search_start = time.time()
    estimated_search_amount = get_estimated_search_amount(q, trend_search_data)
    estimated_search_time = time.time()
    print(
        f"Time taken for estimated search amount calculation: {estimated_search_time - estimated_search_start} seconds")

    # Measure time for collecting issues
    collect_issues_start = time.time()
    a = collect_issues(q, estimated_search_amount)
    collect_issues_time = time.time()
    print(f"Time taken for collecting issues: {collect_issues_time - collect_issues_start} seconds")

    # Measure time for creating embedding result
    embedding_result_start = time.time()
    b = create_embedding_result(a)
    embedding_result_time = time.time()
    print(f"Time taken for creating embedding result: {embedding_result_time - embedding_result_start} seconds")

    # Measure time for clustering issues
    cluster_issues_start = time.time()
    c = cluster_issues(b)
    cluster_issues_time = time.time()
    print(f"Time taken for clustering issues: {cluster_issues_time - cluster_issues_start} seconds")

    # Measure time for creating group title
    group_title_start = time.time()
    d = create_group_title(c)
    group_title_time = time.time()
    print(f"Time taken for creating group title: {group_title_time - group_title_start} seconds")

    # Measure time for creating group content
    group_content_start = time.time()
    e = create_group_content(c)
    group_content_time = time.time()
    print(f"Time taken for creating group content: {group_content_time - group_content_start} seconds")

    # Measure time for getting public opinion data
    public_opinion_start = time.time()
    public_opinion_word_frequency, public_opinion_sentiment, public_opinion_trend, public_opinion_summary = get_public_opinion(
        c)
    public_opinion_time = time.time()
    print(f"Time taken for public opinion analysis: {public_opinion_time - public_opinion_start} seconds")

    # Measure time for getting keyword suggestions
    keyword_suggestions_start = time.time()
    keyword_suggestions_data = get_suggestions_trend_data(q)
    keyword_suggestions_time = time.time()
    print(f"Time taken for keyword suggestions: {keyword_suggestions_time - keyword_suggestions_start} seconds")

    # Record the end time of the entire process
    end_time = time.time()
    print(f"Total time taken: {end_time - start_time} seconds")

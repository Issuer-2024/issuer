from datetime import datetime, timedelta

from app.v2.content.get_estimated_search_amount import get_estimated_search_amount
from app.v2.content.issue_info import collect_issues, create_embedding_result, cluster_issues, create_group_title, \
    create_group_content
from app.v2.content.public_opinion import get_public_opinion_activity_data, get_public_opinion_statistic
from app.v2.content.suggestion_trend import get_suggestions_trend_data
from app.v2.external_request import RequestTrend
from app.v2.model.content import Content
from app.v2.redis.redis_util import read_cache_content, save_to_caching, save_creating, remove_creating, read_creating


def get_content(q: str):
    caching = read_cache_content(q)
    if caching:
        return caching
    return None


def create_content(q: str, background_task):
    if read_creating(q):
        return

    save_creating(q)
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

    a = collect_issues(q, estimated_search_amount)
    b = create_embedding_result(a)
    c = cluster_issues(b)
    d = create_group_title(c)
    e = create_group_content(c)

    public_opinion_activity_data, public_opinion_word_frequency = get_public_opinion_statistic(q, c)
    keyword_suggestions_data = get_suggestions_trend_data(q)

    table_of_contents = [{'title': "개요", 'depth': 0, 'num': '1'}, {'title': "현재 이슈", 'depth': 0, 'num': '2'}]
    table_of_contents += [{'title': title, 'depth': 1, 'num': '2.' + str(i + 1)} for i, title in enumerate(d.values())]

    body = [{'title': "개요", 'content': "", 'num': '1'}, {'title': "현재 이슈", 'content': "", 'num': '2'}]
    body += [{'ref': ref, 'title': title, 'content': content, 'num': '2.' + str(i + 1)}
             for i, (ref, title, content) in enumerate(zip(c.values(), d.values(), e.values()))]
    result = Content(title,
                     created_at,
                     estimated_search_amount,
                     keyword_suggestions_data,
                     public_opinion_activity_data,
                     public_opinion_word_frequency,
                     table_of_contents,
                     body)
    save_to_caching(result, background_task)

    remove_creating(q)


if __name__ == '__main__':
    q = "쯔양"
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

    a = collect_issues(q, estimated_search_amount)
    b = create_embedding_result(a)
    c = cluster_issues(b)
    import pprint

    pprint.pprint(c)
    # start_time = time.time()
    #
    # step_start = time.time()
    # a = collect_issues("쯔양")
    # print(f"collect_issues took {time.time() - step_start:.2f} seconds")
    #
    # step_start = time.time()
    # b = create_embedding_result(a)
    # print(f"create_embedding_result took {time.time() - step_start:.2f} seconds")
    #
    # step_start = time.time()
    # c = cluster_issues(b)
    # print(f"cluster_issues took {time.time() - step_start:.2f} seconds")
    #
    # step_start = time.time()
    # d = create_group_title(c)
    # print(f"create_group_title took {time.time() - step_start:.2f} seconds")
    #
    # step_start = time.time()
    # e = create_group_content(c)
    # print(f"create_group_content took {time.time() - step_start:.2f} seconds")
    #
    # body = {"개요": "", "현재 이슈": {
    #     cluster_num: {
    #         "title": title,
    #         "content": ""
    #     } for cluster_num, title in d.items()
    # }}
    #
    # for cluster_num, content in e.items():
    #     body["현재 이슈"][cluster_num]["content"] = content
    #
    # pprint.pprint(body)
    # print(f"Total execution took {time.time() - start_time:.2f} seconds")

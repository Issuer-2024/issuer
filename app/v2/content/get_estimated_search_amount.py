from app.v2.external_request.request_naver_ad import get_search_amount


def get_estimated_search_amount(q, trend_search_data):
    search_amount = get_search_amount(q)
    if not search_amount:
        search_amount = sum(item['ratio'] for item in trend_search_data)

    total_ratio = sum(item['ratio'] for item in trend_search_data)
    per = search_amount / (total_ratio+1)
    estimated_search_amount = trend_search_data
    for i in range(len(trend_search_data)):
        estimated_search_amount[i]['estimated'] = round(estimated_search_amount[i]['ratio'] * per, 2)

    return estimated_search_amount


if __name__ == '__main__':
    keyword = "쯔양"
    from datetime import datetime, timedelta

    today = datetime.today()
    one_months_ago = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')

    keyword_groups = [
        {'groupName': keyword, 'keywords': [keyword]}
    ]
    from app.v2.external_request import RequestTrend

    trend_search_data = RequestTrend.get_naver_trend_search_data(one_months_ago,
                                                                 today,
                                                                 'date',
                                                                 keyword_groups)[0]['data']
    import pprint

    pprint.pprint(get_estimated_search_amount(keyword, trend_search_data))

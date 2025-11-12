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

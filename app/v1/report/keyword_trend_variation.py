from datetime import datetime, timedelta

from app.v1.request_external_api import RequestTrend, RequestSuggestions


def get_keyword_trend_variation(q: str) -> dict:
    today = datetime.today()
    two_months_ago = (today - timedelta(days=60)).replace(day=1)
    two_months_ago = two_months_ago.strftime('%Y-%m-01')
    today = today.strftime('%Y-%m-%d')

    keyword_groups = [
        {'groupName': q, 'keywords': [suggestion for suggestion in RequestSuggestions.get_suggestions(q)]}]
    if not keyword_groups[0]['keywords']: keyword_groups[0]['keywords'].append(q)

    trend_search_data = RequestTrend.get_naver_trend_search_data(two_months_ago, today, 'date', keyword_groups)[0]['data']
    daily_variation = 0
    weekly_variation = 0
    monthly_variation = 0

    if len(trend_search_data) >= 2:
        daily_variation = (trend_search_data[-1]['ratio'] / (trend_search_data[-2]['ratio']+1) * 100) - 100
    if len(trend_search_data) >= 14:
        two_weeks_ago_ratio = sum([entry['ratio'] for entry in trend_search_data[-14:-7]])
        one_weeks_ago_ratio = sum([entry['ratio'] for entry in trend_search_data[-7:]])
        weekly_variation = (one_weeks_ago_ratio / (two_weeks_ago_ratio+1) * 100) - 100
    if len(trend_search_data) >= 60:
        two_months_ago_ratio = sum([entry['ratio'] for entry in trend_search_data[-60:30]])
        one_months_ago_ratio = sum([entry['ratio'] for entry in trend_search_data[-30:]])
        monthly_variation = (one_months_ago_ratio / (two_months_ago_ratio+1) * 100) - 100

    today = datetime.now()
    yesterday = today - timedelta(days=1)
    one_weeks_ago = today - timedelta(days=7)
    one_months_ago = today - timedelta(days=30)
    today_str = today.strftime('%Y.%m.%d')
    yesterday_str = yesterday.strftime('%Y.%m.%d')
    one_weeks_ago_str = one_weeks_ago.strftime('%Y.%m.%d')
    one_months_ago_str = one_months_ago.strftime('%Y.%m.%d')

    trend_variation = {"date": {'ratio': daily_variation,
                                'duration': f"{today_str} ~ {yesterday_str}"},
                       "week": {
                           'ratio': weekly_variation,
                           'duration': f"{today_str} ~ {one_weeks_ago_str}"},
                       "month": {
                           'ratio': monthly_variation,
                           'duration': f"{today_str} ~ {one_months_ago_str}"}}

    return trend_variation

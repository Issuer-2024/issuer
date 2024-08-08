from datetime import datetime, timedelta

from app.v2.external_request import RequestTrend
from app.v2.external_request.request_naver_ad import get_search_amount
from app.v2.external_request.request_suggestions import RequestSuggestions


def get_suggestion_trend(q: str):  # 키워드의 제안 검색어의 일주일 트랜드 데이터를 가져옵니다.
    today = datetime.today()
    one_week_ago = (today - timedelta(days=7)).strftime('%Y-%m-%d')
    today = today.strftime('%Y-%m-%d')
    suggestions = RequestSuggestions.get_suggestions(q)
    keyword_groups = []
    if len(suggestions) <= 1:
        keyword_groups = [{'groupName': q, 'keywords': [q]}]
    else:
        keyword_groups = [{'groupName': suggestion, 'keywords': [suggestion]} for suggestion in suggestions[1:6]]
    return RequestTrend.get_naver_trend_search_data(one_week_ago, today, 'date', keyword_groups)


def get_suggestion_trend_score(trend_data: list):  # 제안 검색어의 일자 별 검색 비율의 총합을 더한다.
    score = 0
    for data in trend_data:
        score += data['ratio']
    return score


def get_most_trend_day(trend_data: list):  # 가장 인기 있었던 날의 일자를 반환한다.
    # 'ratio' 필드가 있는 항목만 필터링
    filtered_trend_data = list(filter(lambda x: 'ratio' in x, trend_data))

    # 필터링된 데이터가 비어 있지 않으면, 최대 ratio 값을 가진 항목을 찾습니다.
    if filtered_trend_data:
        max_ratio_entry = max(filtered_trend_data, key=lambda x: x['ratio'])
        return max_ratio_entry['period']
    else:
        return None  # 'ratio' 필드가 있는 항목이 없는 경우 None을 반환합니다.


def get_suggestions_trend_data(q: str):
    suggestion_entire_data = []
    suggestion_trend = get_suggestion_trend(q)
    for i, data in enumerate(suggestion_trend):  # title, keywords, data
        search_amount = get_search_amount(data['title'])
        if not search_amount:
            search_amount = 0
        tmp = {'id': i, 'keyword': data['title'], 'trend': data['data'],
               'score': get_suggestion_trend_score(data['data']),
               'most_trend_day': get_most_trend_day(data['data']),
               'search_amount': search_amount
               }
        suggestion_entire_data.append(tmp)

    total_score = sum(item['score'] for item in suggestion_entire_data)
    for i in range(len(suggestion_entire_data)):
        suggestion_entire_data[i]['trend_proportion'] = suggestion_entire_data[i]['score'] / (total_score + 1) * 100
    suggestion_entire_data.sort(key=lambda x: x['search_amount'], reverse=True)
    return suggestion_entire_data


if __name__ == '__main__':
    print(get_suggestions_trend_data("슈가"))

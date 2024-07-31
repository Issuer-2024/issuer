from app.v2.external_request import get_google_trend_daily_rank
from app.v2.model.keyword_rank import KeywordRank


def get_keyword_rank():
    keywords = get_google_trend_daily_rank()

    keyword_rank_list = [KeywordRank(keyword, i) for i, keyword in enumerate(keywords[:10])]
    return keyword_rank_list

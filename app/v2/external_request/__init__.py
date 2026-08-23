from importlib import import_module


_EXPORTS = {
    "ClovaSummary": (".summary", "ClovaSummary"),
    "CompletionExecutor": (".request_llm_dash", "CompletionExecutor"),
    "EmbeddingExecutor": (".request_embedding", "EmbeddingExecutor"),
    "EmbeddingV2Executor": (".request_embedding_v2", "EmbeddingV2Executor"),
    "HCX003Chat": (".request_llm_003", "HCX003Chat"),
    "RequestSuggestions": (".suggestion", "RequestSuggestions"),
    "RequestTrend": (".request_trend", "RequestTrend"),
    "get_clova_sentiment": (".sentiment", "get_clova_sentiment"),
    "get_google_trend_daily_rank": (".request_google_trend_daily_rank", "get_google_trend_daily_rank"),
    "get_naver_news": (".request_news", "get_naver_news"),
    "get_news_summary": (".summary", "get_news_summary"),
}


def __getattr__(name):
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as error:
        raise AttributeError(name) from error
    return getattr(import_module(module_name, __name__), attribute_name)

__all__ = [
    *sorted(_EXPORTS),
]

from dataclasses import dataclass


@dataclass
class Content:
    keyword: str
    created_at: str
    keyword_trend_data: list
    keyword_suggestions_data: list
    public_opinion_sentiment: list
    public_opinion_word_frequency: list
    table_of_contents: list
    body: list
    table_of_public_opinion: list
    public_opinion_trend: list
    public_opinion_summary: str

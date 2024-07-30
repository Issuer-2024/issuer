from dataclasses import dataclass


@dataclass
class Content:
    keyword: str
    created_at: str
    keyword_trend_data: list
    table_of_contents: list
    body: list

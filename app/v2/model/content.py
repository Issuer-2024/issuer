from dataclasses import dataclass


@dataclass
class Content:
    keyword: str
    created_at: str
    keyword_trend_data: list
    table: list[str or list]
    detail: dict[str, str]

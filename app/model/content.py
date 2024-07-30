from dataclasses import dataclass
from datetime import date


@dataclass
class Content:
    keyword: str
    created_at: date
    keyword_trend_data: list
    table: list[str or list]
    detail: dict[str, str]

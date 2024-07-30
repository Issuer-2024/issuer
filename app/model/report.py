from dataclasses import dataclass

from app.model.content import Content
from app.model.keyword_rank import KeywordRank
from app.model.recently_added import RecentlyAdded


@dataclass
class Report:
    content: Content
    recently_added_list: list[RecentlyAdded]
    keyword_rank_list: list[KeywordRank]

from dataclasses import dataclass

from app.v2.model.content import Content
from app.v2.model.keyword_rank import KeywordRank
from app.v2.model.recently_added import RecentlyAdded


@dataclass
class Report:
    content: Content
    recently_added_list: list[RecentlyAdded]
    keyword_rank_list: list[KeywordRank]

from dataclasses import dataclass


@dataclass
class KeywordRank:
    keyword: str
    rank: int


@dataclass
class KeywordRankList:
    rank_list: list[KeywordRank]

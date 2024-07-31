from dataclasses import dataclass
from datetime import date


@dataclass
class RecentlyAdded:
    keyword: str
    elapsed_time: str

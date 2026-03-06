from dataclasses import dataclass

@dataclass
class SearchResult:
    title: str
    link: str
    snippet: str
    position: int
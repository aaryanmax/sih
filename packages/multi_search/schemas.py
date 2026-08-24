from dataclasses import dataclass, field
from typing import List, Optional

from packages.retrieval.late_interaction import SceneResult


@dataclass
class SearchIntent:
    intent: str
    objective: str


@dataclass
class MultiSearchPlan:
    topic: str
    searches: List[SearchIntent]


@dataclass
class IntentResult:
    intent: str
    objective: str
    results: List[SceneResult] = field(default_factory=list)


@dataclass
class MultiSearchResult:
    topic: str
    intents: List[IntentResult] = field(default_factory=list)

from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from .backend import VideoSearchBackend
from .planner import MultiSearchPlanner
from .ranking import rank_results
from .schemas import IntentResult, MultiSearchResult, SearchIntent


class MultiIntentEngine:
    """
    Orchestrates end-to-end multi-intent visual video search:
        1. User query -> Intent decomposition (MultiSearchPlanner)
        2. Concurrent visual retrieval per intent (VideoSearchBackend)
        3. Intent-level deduplication & score normalization (rank_results)
        4. Structured MultiSearchResult assembly
    """

    def __init__(
        self,
        backend: VideoSearchBackend,
        planner: Optional[MultiSearchPlanner] = None,
        max_workers: int = 4,
    ):
        self.backend = backend
        self.planner = planner or MultiSearchPlanner()
        self.max_workers = max_workers

    def search(
        self,
        user_query: str,
        video_source=None,
        top_k: int = 10,
    ) -> MultiSearchResult:
        """
        Executes multi-intent search for the given user query.
        """
        plan = self.planner.plan(user_query)

        def _execute_intent_search(search_intent: SearchIntent) -> IntentResult:
            raw_results = self.backend.search(
                objective=search_intent.objective,
                video_source=video_source,
                top_k=top_k,
            )
            ranked_results = rank_results(raw_results, top_k=top_k)
            return IntentResult(
                intent=search_intent.intent,
                objective=search_intent.objective,
                results=ranked_results,
            )

        # Concurrently execute searches for each intent
        if len(plan.searches) > 1:
            with ThreadPoolExecutor(max_workers=min(len(plan.searches), self.max_workers)) as executor:
                intent_results = list(executor.map(_execute_intent_search, plan.searches))
        else:
            intent_results = [_execute_intent_search(intent) for intent in plan.searches]

        return MultiSearchResult(
            topic=plan.topic,
            intents=intent_results,
        )

from __future__ import annotations

from dataclasses import dataclass

from pcae.repository_intelligence.query.query_request import (
    SUPPORTED_QUERY_CATEGORIES,
    QueryRequest,
)

#: Categories the 122D plan authorizes an Advisory context request to
#: translate into. Identical to the Track 121 Query Layer's own
#: supported categories (122B S7) -- this module introduces no new
#: category.
SUPPORTED_CONTEXT_CATEGORIES = SUPPORTED_QUERY_CATEGORIES


@dataclass(frozen=True)
class AdvisoryContextRequest:
    """A bounded, declared-purpose request for Repository-Intelligence-
    sourced Advisory context (122A S6 / 122D S6.1).

    Carries no query language, grammar, or parser -- it is translated
    into an existing Track 121 ``QueryRequest`` unchanged (122D S6.2).
    """

    category: str
    advisory_purpose: str
    target: str | None = None
    max_records: int | None = None

    def to_query_request(self) -> QueryRequest:
        """Translate into the existing Track 121 query request shape.

        Never invents a query category outside the Query Layer's
        existing six (122D S6.2).
        """
        return QueryRequest(category=self.category, target=self.target)

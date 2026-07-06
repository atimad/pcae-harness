"""Phase 115S: First Advisory Provider Integration (Current Acting Model).

Implements ``CurrentActingModelAdvisoryProvider`` -- the first *real*
(non-mock) ``AdvisoryProvider`` (115R's abstraction, unmodified) --
scoped to exactly one bounded pilot question: "Is the repository state
internally consistent?" (operationalized as
``RepositoryConsistencyAdvisorySkill.objective ==
'repository_consistency_review'``, 115R's own first Advisory
Repository Skill, reused unmodified).

No backend selection, no model configuration, no DeepSeek/GLM-specific
integration, no provider registry, no multi-model mode, and no
execution capability exist anywhere in this module. There is no live
model API call, no network invocation, no subprocess, and no MCP tool
call in this class -- "the current acting model" means whichever
agent is operating a PCAE session at the moment one bounded
``AdvisoryRequest`` is answered. That answer is supplied once, at
construction time, exactly as a human operator would type one in;
this module's only job is to shepherd that single supplied answer
through the identical, unmodified Normalizer
(``normalize_advisory_response``) and Evidence Builder
(``build_evidence_from_normalized``) 115R already froze into code --
never to bypass either.

Stateless. One instance answers exactly one ``AdvisoryRequest``: a
second ``invoke()`` call on the same instance raises rather than
silently returning a second (possibly different) answer, satisfying
"one request / one response / one EvidenceCollection", "no retries",
and "no multi-turn conversation" simultaneously. No conversation
memory, no self-reflection loop, no repository mutation, no command
execution.

Not wired into ``pcae phase complete``, ``pcae task finish``, ``pcae
push``, ``pcae notify``, ``pcae agent verify-handoff``, or ``pcae
runtime inspect`` as an authority -- this module is invoked only by
tests or the explicit :func:`build_repository_consistency_skill_with_current_model`
prototype helper below.
"""

from __future__ import annotations

from pcae.core.advisory_repository_skills import (
    AdvisoryProvider,
    AdvisoryRequest,
    RawAdvisoryResponse,
    RepositoryConsistencyAdvisorySkill,
)
from pcae.core.evidence import EvidenceDeterminism

#: The one bounded pilot question this integration answers. Never
#: parameterized, never expanded to a second question -- code review,
#: architecture review, planning, refactoring advice, bug finding,
#: security review, and autonomous repair are all explicitly out of
#: scope for this pilot.
PILOT_QUESTION = "Is the repository state internally consistent?"


class CurrentActingModelAdvisoryProvider(AdvisoryProvider):
    """The first real ``AdvisoryProvider``: the current acting model
    as a one-shot, stateless evidence producer for exactly one
    bounded pilot question.

    Conforms to 115R's ``AdvisoryProvider`` interface unmodified
    (``provider_id``, ``backend_kind``, ``determinism``, single
    ``invoke()``). Returns ``RawAdvisoryResponse`` only -- never a
    PCAE ``Evidence`` object, never any other trusted PCAE type.
    """

    backend_kind = "current_acting_model"
    determinism = EvidenceDeterminism.PROBABILISTIC
    provider_id = "current_acting_model_advisory_provider"

    def __init__(self, raw_content: str, *, succeeded: bool = True) -> None:
        if succeeded and not raw_content:
            raise ValueError(
                "CurrentActingModelAdvisoryProvider raw_content must be non-empty "
                "when succeeded=True -- construct with succeeded=False to represent "
                "the current model advisory being unavailable this turn"
            )
        self._raw_content = raw_content
        self._succeeded = succeeded
        self._invoked = False

    def invoke(self, request: AdvisoryRequest) -> RawAdvisoryResponse:
        """Answer the single ``AdvisoryRequest`` this instance was
        constructed to answer. Raises on a second call -- this
        provider is single-use and stateless by design; there is no
        retry path and no multi-turn conversation to resume."""
        if self._invoked:
            raise RuntimeError(
                "CurrentActingModelAdvisoryProvider is stateless and single-use: "
                "construct a new instance per AdvisoryRequest, never reuse one "
                "across multiple invoke() calls"
            )
        self._invoked = True
        return RawAdvisoryResponse(
            raw_content=self._raw_content,
            provider_id=self.provider_id,
            succeeded=self._succeeded,
        )


def build_repository_consistency_skill_with_current_model(
    raw_content: str, *, succeeded: bool = True,
) -> RepositoryConsistencyAdvisorySkill:
    """Explicit prototype helper (115S Objective 7): wires a
    ``CurrentActingModelAdvisoryProvider`` carrying one already-
    supplied answer into 115R's unmodified
    ``RepositoryConsistencyAdvisorySkill`` -- the same skill class
    115R used with ``MockAdvisoryProvider``, substituting only the
    provider, exactly demonstrating the backend-agnostic principle
    (115Q). Not called by any lifecycle command; exists for tests and
    explicit prototype use only."""
    provider = CurrentActingModelAdvisoryProvider(raw_content, succeeded=succeeded)
    return RepositoryConsistencyAdvisorySkill(provider)

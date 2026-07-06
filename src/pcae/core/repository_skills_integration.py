"""Phase 115M: Repository Skills Integration Prototype.

Implements Stage 3 of 115L's frozen migration strategy
(``docs/PCAE_REPOSITORY_SKILLS_INTEGRATION_ARCHITECTURE.md`` Section 6):
Repository Skills (115H design, 115I contract freeze, 115J prototype,
115K verification) become an available evidence-acquisition path for
Decision Evaluation, alongside -- not instead of -- the existing
Evidence Provider path.

This module is the "future adapter" 115L's architecture document
anticipated for Stage 3: it sits *above* Repository Skills, Evidence
Providers, Evidence, and Decision Evaluation, gluing them together for
any caller that wants an ``EvidenceCollection`` or a ready-to-evaluate
``EvaluationContext``. It is not itself Decision Evaluation, a
Repository Skill, or an Evidence Provider, and none of those modules
import it -- 115L's frozen "Integration Boundary" (Section 2) and
"Dependency Direction" (Section 7) are preserved exactly:

- ``core/decision_evaluation.py`` still imports only
  ``pcae.core.evidence`` -- never this module, never
  ``evidence_providers``, never ``repository_skills``.
- ``core/repository_skills.py`` still never imports
  ``decision_evaluation`` or ``repository_transition_validator``
  (115K-verified, unchanged).
- ``core/repository_transition_validator.py`` still never imports
  ``evidence_providers`` or ``repository_skills`` directly (unchanged).

Two acquisition paths are exposed, deliberately symmetric:

- :func:`collect_evidence_via_evidence_providers` -- the pre-115M path,
  instantiating 115D's four Evidence Providers directly. Preserved
  unmodified; nothing before 115M is deleted or disabled.
- :func:`collect_evidence_via_repository_skills` -- the 115M path,
  delegating exclusively to a ``RepositorySkillRegistry`` (115J/115K).

Both paths are proven semantically equivalent by
``tests/test_repository_skills_integration_115m.py`` -- same Evidence
IDs, same observed values, same Decision Evaluation results, same
Repository Transition Validator verdicts. This module is not wired
into ``pcae phase complete``, ``pcae task finish``, ``pcae push``,
``pcae notify``, or any other lifecycle command: it exists for callers
(today, only tests) that explicitly choose to use it. No AI/SLM/LLM
skill is introduced or invoked here; only 115J's four deterministic
skills are used. Execution capability remains unavailable.
"""

from __future__ import annotations

from datetime import datetime, timezone

from pcae.core.decision_evaluation import EvaluationContext
from pcae.core.evidence import EvidenceCollection
from pcae.core.evidence_providers import (
    EvidenceProviderContext,
    GitEvidenceProvider,
    MetadataEvidenceProvider,
    ReportEvidenceProvider,
    RuntimeEvidenceProvider,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_skills import (
    RepositorySkillContext,
    RepositorySkillRegistry,
    build_default_registry,
)

#: Fixed declaration order -- the same order 115J's ``build_default_registry``
#: registers its four wrapping skills in, so the two acquisition paths below
#: merge evidence in the same order and are trivially comparable.
_DEFAULT_PROVIDER_CLASSES = (
    GitEvidenceProvider,
    RuntimeEvidenceProvider,
    ReportEvidenceProvider,
    MetadataEvidenceProvider,
)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_evidence_via_evidence_providers(
    root: HarnessPath, *, strict: bool = False,
) -> EvidenceCollection:
    """The pre-115M path: collect evidence by calling 115D's four
    Evidence Providers directly, in fixed order, and merging their
    output into one ``EvidenceCollection``.

    Preserved for callers not (yet) adopting Repository Skills, and as
    the equivalence baseline 115M's skill-based path is measured
    against. Performs no orchestration a Repository Skill doesn't
    already perform identically -- see
    :func:`collect_evidence_via_repository_skills`.
    """
    context = EvidenceProviderContext(root=root, strict=strict)
    items = []
    for provider_cls in _DEFAULT_PROVIDER_CLASSES:
        items.extend(provider_cls().collect(context).evidence.items)
    return EvidenceCollection(tuple(items))


def collect_evidence_via_repository_skills(
    root: HarnessPath,
    *,
    strict: bool = False,
    registry: RepositorySkillRegistry | None = None,
) -> EvidenceCollection:
    """The 115M path: collect evidence exclusively through a
    ``RepositorySkillRegistry`` (115J/115K), never by constructing,
    discovering, or calling an Evidence Provider directly from this
    function's caller's perspective -- provider orchestration happens
    entirely inside each registered ``RepositorySkill``.

    Uses :func:`build_default_registry` (115J's four deterministic
    skills: Git/Runtime/Report/Metadata) unless a caller supplies its
    own ``registry``. Semantically identical to
    :func:`collect_evidence_via_evidence_providers` given the same
    ``root`` at the same instant, since every default skill wraps its
    corresponding provider unmodified (115K-verified).
    """
    active_registry = registry if registry is not None else build_default_registry()
    context = RepositorySkillContext(root=root, strict=strict)
    results = active_registry.invoke_all(context)
    return active_registry.merge_evidence(results)


def build_evaluation_context_from_evidence_providers(
    root: HarnessPath,
    *,
    evaluation_id: str,
    repository_snapshot_reference: str,
    evaluation_version: str = "1.0",
    evaluation_timestamp: str | None = None,
    strict: bool = False,
) -> EvaluationContext:
    """Compatibility helper: build a Decision Evaluation
    ``EvaluationContext`` from the old provider-based evidence path.
    Kept alongside :func:`build_evaluation_context_from_repository_skills`
    so callers may switch between the two paths without changing
    anything downstream of the returned context."""
    evidence = collect_evidence_via_evidence_providers(root, strict=strict)
    return EvaluationContext(
        evidence=evidence,
        evaluation_id=evaluation_id,
        evaluation_timestamp=evaluation_timestamp or _now_utc_iso(),
        repository_snapshot_reference=repository_snapshot_reference,
        evaluation_version=evaluation_version,
    )


def build_evaluation_context_from_repository_skills(
    root: HarnessPath,
    *,
    evaluation_id: str,
    repository_snapshot_reference: str,
    evaluation_version: str = "1.0",
    evaluation_timestamp: str | None = None,
    strict: bool = False,
    registry: RepositorySkillRegistry | None = None,
) -> EvaluationContext:
    """Build a Decision Evaluation ``EvaluationContext`` from the 115M
    Repository Skills evidence path. This is the concrete Stage 3
    adapter 115L's architecture document anticipated: Decision
    Evaluation itself is unchanged and unaware this function exists --
    it still only ever consumes the ``EvaluationContext``/
    ``EvidenceCollection`` a caller hands it."""
    evidence = collect_evidence_via_repository_skills(root, strict=strict, registry=registry)
    return EvaluationContext(
        evidence=evidence,
        evaluation_id=evaluation_id,
        evaluation_timestamp=evaluation_timestamp or _now_utc_iso(),
        repository_snapshot_reference=repository_snapshot_reference,
        evaluation_version=evaluation_version,
    )

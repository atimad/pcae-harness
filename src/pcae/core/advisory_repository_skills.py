"""Phase 115R: Advisory Repository Skills Prototype.

Implements the framework 115P designed and 115Q froze as contract --
``AdvisoryRequest``, ``RawAdvisoryResponse``, ``NormalizedAdvisoryResponse``,
the backend-agnostic ``AdvisoryProvider`` interface, a Prompt Builder,
a Response Normalizer, an Evidence Builder, and the first concrete
Advisory Repository Skill -- using **only** a deterministic
``MockAdvisoryProvider``. No real model backend is implemented or
invoked anywhere in this module.

Build the framework. Do not build AI integration.

Absolutely forbidden, and absent from this module: DeepSeek, Claude
API, OpenAI, GLM, Qwen, Codex backend, local SLM, network calls,
subprocess model execution, MCP model invocation, execution capability
of any kind. ``MockAdvisoryProvider`` is deterministic, pure,
repeatable, uses no randomness, performs no network I/O, no filesystem
writes, and invokes nothing -- it is a plain in-memory lookup over
canned ``RawAdvisoryResponse`` values supplied by its caller.

Disconnected by design (115R scope): this module is never imported by
``core/decision_evaluation.py``, ``core/repository_transition_validator.py``,
``core/repository_skills_integration.py``, any lifecycle command, or
``core/repository_skills.py``'s own ``build_default_registry()`` (which
remains deterministic-skills-only, unchanged). A future integration
phase decides how (if at all) an Advisory Repository Skill's evidence
is actually consumed in a real evaluation; this phase only proves the
framework works end-to-end against a mock backend.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from pcae.core.evidence import (
    Evidence,
    EvidenceCategory,
    EvidenceCollection,
    EvidenceConfidence,
    EvidenceDeterminism,
    EvidenceFreshness,
    EvidenceProvenance,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_skills import (
    RepositorySkill,
    RepositorySkillCapability,
    RepositorySkillContext,
    RepositorySkillManifest,
    RepositorySkillResult,
    RepositorySkillStatus,
)

#: 115Q Section 2 -- the three normalization outcomes a Normalizer may
#: report. No fourth value exists.
NORMALIZATION_STATUSES: tuple[str, ...] = ("succeeded", "partial", "failed")

#: 115Q's Model Boundary section -- a Raw Response claiming any of
#: these top-level keys is rejected outright by the Normalizer, never
#: partially accepted.
_UNAUTHORIZED_RESPONSE_FIELDS: frozenset[str] = frozenset({
    "verdict", "commit", "push", "authorized", "execute", "finalize",
})


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════
# AdvisoryRequest / RawAdvisoryResponse / NormalizedAdvisoryResponse
# -- 115Q Section 2, frozen field sets
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class AdvisoryRequest:
    """The bounded input to one ``AdvisoryProvider.invoke()`` call
    (115Q Section 2). Built exclusively by the Prompt Builder
    (:func:`build_advisory_request`); never constructed directly by an
    ``AdvisoryProvider`` or an ``AdvisoryRepositorySkill``."""

    bounded_context: str
    question: str
    response_schema_hint: str
    timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        if not self.bounded_context:
            raise ValueError("AdvisoryRequest bounded_context must be non-empty")
        if not self.question:
            raise ValueError("AdvisoryRequest question must be non-empty")
        if self.timeout_seconds <= 0:
            raise ValueError("AdvisoryRequest timeout_seconds must be positive")


@dataclass(frozen=True)
class RawAdvisoryResponse:
    """The untrusted, unprocessed output of one ``AdvisoryProvider.
    invoke()`` call (115Q Section 2). Never consumed by Decision
    Evaluation, the Validator, or any lifecycle command in this form --
    it must pass through :func:`normalize_advisory_response` first."""

    raw_content: str
    provider_id: str
    succeeded: bool

    def __post_init__(self) -> None:
        if not self.provider_id:
            raise ValueError("RawAdvisoryResponse provider_id must be non-empty")


@dataclass(frozen=True)
class NormalizedAdvisoryResponse:
    """The Normalizer's validated output (115Q Section 2) -- the only
    shape :func:`build_evidence_from_normalized` may consume. Only
    canonical ``Evidence`` may be built from this type; nothing else
    in this module accepts a ``RawAdvisoryResponse`` directly."""

    findings: tuple[str, ...]
    confidence_signal: float | None
    references: tuple[str, ...]
    limitations: str
    normalization_status: str

    def __post_init__(self) -> None:
        if self.normalization_status not in NORMALIZATION_STATUSES:
            raise ValueError(
                f"NormalizedAdvisoryResponse normalization_status must be one of "
                f"{NORMALIZATION_STATUSES}, got {self.normalization_status!r}"
            )
        if self.normalization_status != "failed" and not self.findings:
            raise ValueError(
                "NormalizedAdvisoryResponse with a non-failed normalization_status "
                "must carry at least one finding"
            )
        if not self.limitations:
            raise ValueError(
                "NormalizedAdvisoryResponse limitations must be non-empty "
                "(115Q Evidence Builder contract: 'must include limitations')"
            )
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "references", tuple(self.references))


# ═══════════════════════════════════════════════════════════════════════
# AdvisoryProvider -- 115Q Section 2, backend-agnostic interface only
# ═══════════════════════════════════════════════════════════════════════

class AdvisoryProvider(ABC):
    """The backend-agnostic interface an Advisory Repository Skill
    talks to (115Q Section 2). No provider-specific code lives here --
    only the interface. An ``AdvisoryProvider`` never returns a trusted
    PCAE object, never mutates repository state, and exposes exactly
    one operation."""

    provider_id: str
    backend_kind: str
    determinism: EvidenceDeterminism

    @abstractmethod
    def invoke(self, request: AdvisoryRequest) -> RawAdvisoryResponse:
        """Answer one ``AdvisoryRequest`` with one ``RawAdvisoryResponse``.
        No streaming, no multi-turn, no tool-call callback, no side
        channel."""


# ═══════════════════════════════════════════════════════════════════════
# MockAdvisoryProvider -- deterministic, pure, no real backend
# ═══════════════════════════════════════════════════════════════════════

class MockAdvisoryProvider(AdvisoryProvider):
    """A deterministic ``backend_kind='deterministic_mock'`` provider
    (115Q Section 2 explicitly permits ``DETERMINISTIC`` determinism
    for this one provider kind). Returns predefined
    ``RawAdvisoryResponse`` values for test scenarios via a plain
    in-memory lookup keyed by ``AdvisoryRequest.question`` -- no
    randomness, no network, no filesystem writes, no execution. The
    same request always produces the same response."""

    backend_kind = "deterministic_mock"
    determinism = EvidenceDeterminism.DETERMINISTIC

    def __init__(
        self,
        responses: Mapping[str, RawAdvisoryResponse] | None = None,
        *,
        default_response: RawAdvisoryResponse | None = None,
        provider_id: str = "mock_advisory_provider",
    ) -> None:
        self.provider_id = provider_id
        self._responses: dict[str, RawAdvisoryResponse] = dict(responses or {})
        self._default_response = default_response or RawAdvisoryResponse(
            raw_content=json.dumps({
                "findings": ["No scenario configured for this question."],
                "confidence_signal": 0.0,
                "references": [],
                "limitations": "MockAdvisoryProvider has no canned response for this question.",
            }),
            provider_id=provider_id,
            succeeded=True,
        )

    def invoke(self, request: AdvisoryRequest) -> RawAdvisoryResponse:
        return self._responses.get(request.question, self._default_response)


# ═══════════════════════════════════════════════════════════════════════
# Prompt Builder -- 115Q Section 5, prompt boundary
# ═══════════════════════════════════════════════════════════════════════

#: Constraints every advisory request declares -- documents the 115Q
#: Section 5 prompt boundary in the request itself. Never enforced by
#: string content alone; enforcement is structural (this module grants
#: no execution/command capability anywhere), this is a declaration.
DEFAULT_ADVISORY_CONSTRAINTS: tuple[str, ...] = (
    "no_secrets",
    "no_unrestricted_command_capability",
    "no_execution_request",
    "advisory_request_only",
)


def build_advisory_request(
    root: HarnessPath,
    *,
    evidence_categories: tuple[EvidenceCategory, ...],
    objective: str,
    constraints: tuple[str, ...] = DEFAULT_ADVISORY_CONSTRAINTS,
) -> AdvisoryRequest:
    """Prompt Builder (115Q Section 5): assembles one ``AdvisoryRequest``
    from bounded repository context, requested evidence categories, an
    explicit objective, and prompt constraints. Never includes secrets
    or unrestricted repository access -- ``bounded_context`` is a small,
    deterministic summary, never a raw filesystem dump.

    Deliberately does not import, accept, or branch on any
    ``AdvisoryProvider`` -- the Prompt Builder must not know which
    provider will answer the request it builds (115Q Objective 4)."""
    if not objective:
        raise ValueError("build_advisory_request objective must be non-empty")
    if not evidence_categories:
        raise ValueError("build_advisory_request evidence_categories must be non-empty")

    bounded_context = (
        f"repository_root_present={root.path.exists()}; "
        f"requested_evidence_categories={sorted(c.value for c in evidence_categories)}; "
        f"constraints={list(constraints)}"
    )
    return AdvisoryRequest(
        bounded_context=bounded_context,
        question=objective,
        response_schema_hint=(
            "JSON object with keys: findings (non-empty list of strings), "
            "confidence_signal (number 0.0-1.0, optional), "
            "references (list of strings, optional), "
            "limitations (string)."
        ),
    )


# ═══════════════════════════════════════════════════════════════════════
# Response Normalizer -- 115Q Section 6, response boundary
# ═══════════════════════════════════════════════════════════════════════

def _failed_normalization(limitations: str) -> NormalizedAdvisoryResponse:
    return NormalizedAdvisoryResponse(
        findings=(), confidence_signal=None, references=(),
        limitations=limitations, normalization_status="failed",
    )


def normalize_advisory_response(response: RawAdvisoryResponse) -> NormalizedAdvisoryResponse:
    """Normalizer (115Q Section 6): the sole permitted conversion point
    from untrusted ``RawAdvisoryResponse`` to validated
    ``NormalizedAdvisoryResponse``. Rejects malformed, unparseable,
    out-of-schema, or unauthorized-field content outright -- never
    coerces it into a best-effort guess."""
    if not response.succeeded:
        return _failed_normalization("Advisory provider invocation did not succeed.")

    try:
        payload = json.loads(response.raw_content)
    except (TypeError, ValueError):
        return _failed_normalization("Raw advisory response could not be parsed as JSON.")

    if not isinstance(payload, dict):
        return _failed_normalization("Raw advisory response JSON was not an object.")

    unauthorized = _UNAUTHORIZED_RESPONSE_FIELDS & payload.keys()
    if unauthorized:
        return _failed_normalization(
            f"Raw advisory response claimed unauthorized field(s): {sorted(unauthorized)}."
        )

    raw_findings = payload.get("findings")
    if not isinstance(raw_findings, list) or not raw_findings:
        return _failed_normalization("Raw advisory response contained no findings.")

    valid_findings: list[str] = []
    dropped = 0
    for item in raw_findings:
        if isinstance(item, str) and item.strip():
            valid_findings.append(item.strip())
        elif isinstance(item, dict) and isinstance(item.get("finding"), str) and item["finding"].strip():
            valid_findings.append(item["finding"].strip())
        else:
            dropped += 1

    if not valid_findings:
        return _failed_normalization("No valid findings survived normalization.")

    confidence_signal = payload.get("confidence_signal")
    if not isinstance(confidence_signal, (int, float)) or isinstance(confidence_signal, bool):
        confidence_signal = None

    references = tuple(
        str(r) for r in payload.get("references", []) if isinstance(r, (str, int)) and not isinstance(r, bool)
    )

    limitations = payload.get("limitations")
    if not isinstance(limitations, str) or not limitations.strip():
        limitations = "Advisory provider did not report limitations."

    status = "succeeded" if dropped == 0 else "partial"
    return NormalizedAdvisoryResponse(
        findings=tuple(valid_findings),
        confidence_signal=confidence_signal,
        references=references,
        limitations=limitations,
        normalization_status=status,
    )


# ═══════════════════════════════════════════════════════════════════════
# Evidence Builder -- 115Q Section 7
# ═══════════════════════════════════════════════════════════════════════

def _confidence_from_signal(signal: float | None) -> EvidenceConfidence:
    if signal is None:
        return EvidenceConfidence.LOW
    if signal >= 0.75:
        return EvidenceConfidence.HIGH
    if signal >= 0.4:
        return EvidenceConfidence.MEDIUM
    return EvidenceConfidence.LOW


def build_evidence_from_normalized(
    normalized: NormalizedAdvisoryResponse,
    *,
    provider_id: str,
    producer: str,
    category: EvidenceCategory,
    scope: str,
    evidence_id_prefix: str,
) -> EvidenceCollection:
    """Evidence Builder (115Q Section 7): converts one
    ``NormalizedAdvisoryResponse`` into an ``EvidenceCollection``. Every
    item is probabilistic, model-produced (via ``provenance``),
    advisory only, confidence-labelled, limitation-labelled, and
    provenance-preserving. Produces ``UNKNOWN``-freshness evidence when
    ``normalized.normalization_status == 'failed'`` -- never fabricates
    a passing observation."""
    provenance = EvidenceProvenance(
        producer=producer,
        produced_from=f"AdvisoryProvider:{provider_id}",
        timestamp=_now_utc_iso(),
        deterministic_origin=False,
    )

    if normalized.normalization_status == "failed":
        return EvidenceCollection((
            Evidence(
                evidence_id=f"{evidence_id_prefix}-001",
                source="Advisory Repository Skill",
                category=category,
                producer=producer,
                timestamp_utc=_now_utc_iso(),
                freshness=EvidenceFreshness.UNKNOWN,
                confidence=EvidenceConfidence.UNKNOWN,
                determinism=EvidenceDeterminism.PROBABILISTIC,
                scope=scope,
                references=(),
                observed_value="unavailable",
                explanation="Advisory provider could not produce usable findings.",
                provenance=provenance,
                limitations=normalized.limitations,
            ),
        ))

    confidence = _confidence_from_signal(normalized.confidence_signal)
    items = tuple(
        Evidence(
            evidence_id=f"{evidence_id_prefix}-{index:03d}",
            source="Advisory Repository Skill",
            category=category,
            producer=producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.CURRENT,
            confidence=confidence,
            determinism=EvidenceDeterminism.PROBABILISTIC,
            scope=scope,
            references=normalized.references,
            observed_value=finding,
            explanation=finding,
            provenance=provenance,
            limitations=normalized.limitations,
        )
        for index, finding in enumerate(normalized.findings, start=1)
    )
    return EvidenceCollection(items)


# ═══════════════════════════════════════════════════════════════════════
# AdvisoryRepositorySkill -- 115Q Section 1, first concrete pilot skill
# ═══════════════════════════════════════════════════════════════════════

class AdvisoryRepositorySkill(RepositorySkill):
    """Base class for an Advisory Repository Skill (115Q Section 1):
    talks only to the ``AdvisoryProvider`` interface (never a specific
    backend), builds a prompt/request, consumes a normalized advisory
    response, and produces ``EvidenceCollection``. Never decides,
    mutates, authorizes, promotes, notifies, commits, pushes, or
    finalizes -- identical prohibitions to every other
    ``RepositorySkill`` (115H/115I), restated here because this class
    is the one most likely to eventually wrap an execution-capable
    backend."""

    evidence_category: EvidenceCategory
    objective: str
    evidence_id_prefix: str

    def __init__(self, provider: AdvisoryProvider) -> None:
        self._provider = provider

    def invoke(self, context: RepositorySkillContext) -> RepositorySkillResult:
        try:
            request = build_advisory_request(
                context.root,
                evidence_categories=(self.evidence_category,),
                objective=self.objective,
            )
            raw_response = self._provider.invoke(request)
            normalized = normalize_advisory_response(raw_response)
            evidence = build_evidence_from_normalized(
                normalized,
                provider_id=self._provider.provider_id,
                producer=self.manifest.name,
                category=self.evidence_category,
                scope=self.objective,
                evidence_id_prefix=self.evidence_id_prefix,
            )
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.SUCCESS,
                evidence=evidence,
            )
        except Exception as exc:
            if context.strict:
                raise
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.FAILED,
                failure_reason=f"Advisory Repository Skill invocation raised: {exc!r}",
            )


class RepositoryConsistencyAdvisorySkill(AdvisoryRepositorySkill):
    """The first Advisory Repository Skill (115Q Section 10's first
    pilot scope: exactly one of repository/documentation/report
    consistency review -- this one is repository consistency review).
    Uses a ``MockAdvisoryProvider`` by default; any ``AdvisoryProvider``
    may be substituted without changing this class."""

    manifest = RepositorySkillManifest(
        skill_id="repository_consistency_advisory_skill",
        name="Repository Consistency Advisory Skill",
        version="1.0",
        capabilities=(RepositorySkillCapability.AI_REVIEW,),
        determinism=EvidenceDeterminism.PROBABILISTIC,
        confidence_policy=EvidenceConfidence.LOW,
        evidence_categories=(EvidenceCategory.AI_REVIEW,),
        required_inputs=("AdvisoryProvider.invoke",),
        timeout_seconds=10.0,
        failure_policy="unknown_evidence",
        model_produced=True,
    )

    evidence_category = EvidenceCategory.AI_REVIEW
    objective = "repository_consistency_review"
    evidence_id_prefix = "E-advisory-repo-consistency"

    def __init__(self, provider: AdvisoryProvider | None = None) -> None:
        super().__init__(provider or MockAdvisoryProvider())

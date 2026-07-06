"""Phase 115J: Repository Skills Prototype.

Implements the first Repository Skills framework on top of 115I's
frozen contract (``docs/PCAE_REPOSITORY_SKILLS_CONTRACT.md``):
``RepositorySkill``, ``RepositorySkillContext``,
``RepositorySkillResult``, ``RepositorySkillRegistry``,
``RepositorySkillCapability``, and ``RepositorySkillManifest``, plus
four deterministic skills (``GitRepositorySkill``,
``RuntimeRepositorySkill``, ``ReportRepositorySkill``,
``MetadataRepositorySkill``) that each wrap one of 115D's existing
Evidence Providers unmodified.

Core principle (115H/115I, restated here): Repository Skills never
decide. Repository Skills produce Evidence. Repository Skills are
model-agnostic. Every skill in this module:

- collects evidence by delegating to an existing 115D
  ``EvidenceProvider`` and returns its ``EvidenceCollection`` unchanged
- never mutates repository state
- never decides, votes, authorizes, or promotes an artifact
- never sends a notification
- never bypasses the Repository Transition Validator
- never invokes execution
- carries no model/agent/backend/vendor identity field anywhere in its
  manifest or output

Disconnected by design (115J scope): no AI/SLM/LLM skill, no DeepSeek
integration, no lifecycle integration (not called by ``pcae phase
complete``, ``pcae task finish``, or ``pcae push``), no Decision
Evaluation integration (``pcae.core.decision_evaluation`` is never
imported here), no Repository Transition Validator integration
(``pcae.core.repository_transition_validator`` is never imported
here), and no execution capability. A future integration phase decides
how (if at all) these skills feed a Decision Framework.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar

from pcae.core.evidence import (
    EvidenceCategory,
    EvidenceCollection,
    EvidenceConfidence,
    EvidenceDeterminism,
)
from pcae.core.evidence_providers import (
    EvidenceProviderContext,
    GitEvidenceProvider,
    MetadataEvidenceProvider,
    ReportEvidenceProvider,
    RuntimeEvidenceProvider,
)
from pcae.core.paths import HarnessPath


# ═══════════════════════════════════════════════════════════════════════
# RepositorySkillCapability — 115I Section 2, frozen minimum set
# ═══════════════════════════════════════════════════════════════════════

class RepositorySkillCapability(str, Enum):
    """The frozen minimum capability set (115I Section 2). A capability
    describes what evidence a skill may produce, never how it produces
    it -- two skills may declare the same capability while using
    entirely different internal logic."""

    GIT_ANALYSIS = "git_analysis"
    RUNTIME_ANALYSIS = "runtime_analysis"
    ARCHITECTURE_ANALYSIS = "architecture_analysis"
    DOCUMENTATION_ANALYSIS = "documentation_analysis"
    REPORT_ANALYSIS = "report_analysis"
    METADATA_ANALYSIS = "metadata_analysis"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    AI_REVIEW = "ai_review"


# ═══════════════════════════════════════════════════════════════════════
# RepositorySkillManifest — 115I Section 3, frozen field set
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RepositorySkillManifest:
    """The frozen manifest fields (115I Section 3). No model/agent/
    backend/vendor identity field exists on this shape -- a skill is
    model-agnostic by construction, not by convention."""

    skill_id: str
    name: str
    version: str
    capabilities: tuple[RepositorySkillCapability, ...]
    determinism: EvidenceDeterminism
    confidence_policy: EvidenceConfidence
    evidence_categories: tuple[EvidenceCategory, ...]
    required_inputs: tuple[str, ...]
    optional_inputs: tuple[str, ...] = ()
    timeout_seconds: float = 10.0
    failure_policy: str = "unknown_evidence"
    side_effect_policy: str = "none"
    model_produced: bool = False
    experimental: bool = False

    def __post_init__(self) -> None:
        if not self.skill_id:
            raise ValueError("RepositorySkillManifest skill_id must be non-empty")
        if not self.name:
            raise ValueError("RepositorySkillManifest name must be non-empty")
        if not self.version:
            raise ValueError("RepositorySkillManifest version must be non-empty")
        if not self.capabilities:
            raise ValueError("RepositorySkillManifest capabilities must be non-empty")
        if self.side_effect_policy != "none":
            raise ValueError(
                "RepositorySkillManifest side_effect_policy must be 'none' "
                f"(115I Section 1/6/7 forbid any skill side effect), got {self.side_effect_policy!r}"
            )
        if self.failure_policy not in ("unknown_evidence", "explicit_failure"):
            raise ValueError(
                "RepositorySkillManifest failure_policy must be 'unknown_evidence' "
                f"or 'explicit_failure' (115I Section 5), got {self.failure_policy!r}"
            )
        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        object.__setattr__(self, "evidence_categories", tuple(self.evidence_categories))
        object.__setattr__(self, "required_inputs", tuple(self.required_inputs))
        object.__setattr__(self, "optional_inputs", tuple(self.optional_inputs))


# ═══════════════════════════════════════════════════════════════════════
# RepositorySkillContext / RepositorySkillResult
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class RepositorySkillContext:
    """Read-only handle to repository state passed to every skill.

    Mirrors 115D's ``EvidenceProviderContext`` exactly: skills read
    from ``root``, they never write to it. ``strict``, when ``True``,
    re-raises an unexpected invocation failure instead of degrading to
    an explicit failure result -- default ``False`` preserves the
    fail-closed-to-evidence behavior every skill uses by default.
    """

    root: HarnessPath
    strict: bool = False


class RepositorySkillStatus(str, Enum):
    """The two honest outcomes a skill invocation may report (115I
    Section 5). There is no third, ambiguous status."""

    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True)
class RepositorySkillResult:
    """The outcome of one skill invocation.

    ``status`` is ``SUCCESS`` whenever the skill ran to completion and
    returned evidence -- including evidence that is itself honestly
    ``UNKNOWN`` (115D's established provider-failure pattern, reused
    unmodified here). ``status`` is ``FAILED`` only when the skill
    invocation itself could not complete (an explicit failure outcome,
    115I Section 5's second option), in which case ``evidence`` is
    empty and ``failure_reason`` is populated. There is never a silent
    success: a ``FAILED`` result is never disguised as an empty-but-
    successful ``EvidenceCollection``.
    """

    skill_id: str
    status: RepositorySkillStatus
    evidence: EvidenceCollection = field(default_factory=EvidenceCollection)
    failure_reason: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", RepositorySkillStatus(self.status))
        if self.status == RepositorySkillStatus.FAILED and not self.failure_reason:
            raise ValueError(
                "RepositorySkillResult with status=FAILED must carry a non-empty "
                "failure_reason (115I Section 5: never silent failure)"
            )


# ═══════════════════════════════════════════════════════════════════════
# RepositorySkill — 115I Section 1, frozen interface
# ═══════════════════════════════════════════════════════════════════════

class RepositorySkill(ABC):
    """Common contract every Repository Skill implements (115I Section
    1). A skill never mutates ``context.root``, never decides, votes,
    authorizes, promotes an artifact, sends a notification, bypasses
    the Repository Transition Validator, or invokes execution -- and
    carries no field identifying a proposing agent/model/backend/
    vendor anywhere in its manifest or output.
    """

    manifest: ClassVar[RepositorySkillManifest]

    @abstractmethod
    def invoke(self, context: RepositorySkillContext) -> RepositorySkillResult:
        """Produce an ``EvidenceCollection`` (via a ``RepositorySkillResult``).
        Never decides, mutates, promotes, notifies, or executes."""


# ═══════════════════════════════════════════════════════════════════════
# Deterministic skills — each wraps one 115D Evidence Provider unmodified
# ═══════════════════════════════════════════════════════════════════════

def _provider_context(context: RepositorySkillContext) -> EvidenceProviderContext:
    return EvidenceProviderContext(root=context.root, strict=context.strict)


class GitRepositorySkill(RepositorySkill):
    """Wraps 115D's ``GitEvidenceProvider`` unmodified."""

    manifest = RepositorySkillManifest(
        skill_id="git_repository_skill",
        name="Git Repository Skill",
        version="1.0",
        capabilities=(RepositorySkillCapability.GIT_ANALYSIS,),
        determinism=EvidenceDeterminism.DETERMINISTIC,
        confidence_policy=EvidenceConfidence.HIGH,
        evidence_categories=(EvidenceCategory.GIT, EvidenceCategory.PUSH_STATE),
        required_inputs=GitEvidenceProvider.required_inputs,
        timeout_seconds=10.0,
        failure_policy="unknown_evidence",
    )

    def invoke(self, context: RepositorySkillContext) -> RepositorySkillResult:
        try:
            result = GitEvidenceProvider().collect(_provider_context(context))
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.SUCCESS,
                evidence=result.evidence,
            )
        except Exception as exc:
            if context.strict:
                raise
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.FAILED,
                failure_reason=f"GitEvidenceProvider.collect raised: {exc!r}",
            )


class RuntimeRepositorySkill(RepositorySkill):
    """Wraps 115D's ``RuntimeEvidenceProvider`` unmodified."""

    manifest = RepositorySkillManifest(
        skill_id="runtime_repository_skill",
        name="Runtime Repository Skill",
        version="1.0",
        capabilities=(RepositorySkillCapability.RUNTIME_ANALYSIS,),
        determinism=EvidenceDeterminism.DETERMINISTIC,
        confidence_policy=EvidenceConfidence.HIGH,
        evidence_categories=(EvidenceCategory.RUNTIME,),
        required_inputs=RuntimeEvidenceProvider.required_inputs,
        timeout_seconds=10.0,
        failure_policy="unknown_evidence",
    )

    def invoke(self, context: RepositorySkillContext) -> RepositorySkillResult:
        try:
            result = RuntimeEvidenceProvider().collect(_provider_context(context))
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.SUCCESS,
                evidence=result.evidence,
            )
        except Exception as exc:
            if context.strict:
                raise
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.FAILED,
                failure_reason=f"RuntimeEvidenceProvider.collect raised: {exc!r}",
            )


class ReportRepositorySkill(RepositorySkill):
    """Wraps 115D's ``ReportEvidenceProvider`` unmodified."""

    manifest = RepositorySkillManifest(
        skill_id="report_repository_skill",
        name="Report Repository Skill",
        version="1.0",
        capabilities=(RepositorySkillCapability.REPORT_ANALYSIS,),
        determinism=EvidenceDeterminism.DETERMINISTIC,
        confidence_policy=EvidenceConfidence.HIGH,
        evidence_categories=(EvidenceCategory.REPORT,),
        required_inputs=ReportEvidenceProvider.required_inputs,
        timeout_seconds=10.0,
        failure_policy="unknown_evidence",
    )

    def invoke(self, context: RepositorySkillContext) -> RepositorySkillResult:
        try:
            result = ReportEvidenceProvider().collect(_provider_context(context))
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.SUCCESS,
                evidence=result.evidence,
            )
        except Exception as exc:
            if context.strict:
                raise
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.FAILED,
                failure_reason=f"ReportEvidenceProvider.collect raised: {exc!r}",
            )


class MetadataRepositorySkill(RepositorySkill):
    """Wraps 115D's ``MetadataEvidenceProvider`` unmodified."""

    manifest = RepositorySkillManifest(
        skill_id="metadata_repository_skill",
        name="Metadata Repository Skill",
        version="1.0",
        capabilities=(RepositorySkillCapability.METADATA_ANALYSIS,),
        determinism=EvidenceDeterminism.DETERMINISTIC,
        confidence_policy=EvidenceConfidence.HIGH,
        evidence_categories=(EvidenceCategory.METADATA,),
        required_inputs=MetadataEvidenceProvider.required_inputs,
        timeout_seconds=10.0,
        failure_policy="unknown_evidence",
    )

    def invoke(self, context: RepositorySkillContext) -> RepositorySkillResult:
        try:
            result = MetadataEvidenceProvider().collect(_provider_context(context))
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.SUCCESS,
                evidence=result.evidence,
            )
        except Exception as exc:
            if context.strict:
                raise
            return RepositorySkillResult(
                skill_id=self.manifest.skill_id,
                status=RepositorySkillStatus.FAILED,
                failure_reason=f"MetadataEvidenceProvider.collect raised: {exc!r}",
            )


# ═══════════════════════════════════════════════════════════════════════
# RepositorySkillRegistry
# ═══════════════════════════════════════════════════════════════════════

class RepositorySkillRegistry:
    """Registers, looks up, filters, and invokes Repository Skills.

    The registry itself never decides, mutates, promotes, or notifies
    -- it is purely a lookup/dispatch/merge structure over skills that
    themselves only ever produce evidence.
    """

    def __init__(self) -> None:
        self._skills: dict[str, RepositorySkill] = {}

    def register(self, skill: RepositorySkill) -> None:
        skill_id = skill.manifest.skill_id
        if skill_id in self._skills:
            raise ValueError(f"Duplicate skill_id, already registered: {skill_id!r}")
        self._skills[skill_id] = skill

    def get(self, skill_id: str) -> RepositorySkill | None:
        return self._skills.get(skill_id)

    def list_skills(self) -> tuple[RepositorySkill, ...]:
        return tuple(self._skills.values())

    def list_manifests(self) -> tuple[RepositorySkillManifest, ...]:
        return tuple(skill.manifest for skill in self._skills.values())

    def filter_by_capability(self, capability: RepositorySkillCapability) -> tuple[RepositorySkill, ...]:
        return tuple(
            skill for skill in self._skills.values()
            if capability in skill.manifest.capabilities
        )

    def filter_by_category(self, category: EvidenceCategory) -> tuple[RepositorySkill, ...]:
        return tuple(
            skill for skill in self._skills.values()
            if category in skill.manifest.evidence_categories
        )

    def invoke(self, skill_id: str, context: RepositorySkillContext) -> RepositorySkillResult:
        skill = self._skills.get(skill_id)
        if skill is None:
            return RepositorySkillResult(
                skill_id=skill_id,
                status=RepositorySkillStatus.FAILED,
                failure_reason=f"No skill registered with skill_id {skill_id!r}",
            )
        return skill.invoke(context)

    def invoke_many(
        self, skill_ids: tuple[str, ...], context: RepositorySkillContext,
    ) -> tuple[RepositorySkillResult, ...]:
        return tuple(self.invoke(skill_id, context) for skill_id in skill_ids)

    def invoke_all(self, context: RepositorySkillContext) -> tuple[RepositorySkillResult, ...]:
        return tuple(skill.invoke(context) for skill in self._skills.values())

    @staticmethod
    def merge_evidence(results: tuple[RepositorySkillResult, ...]) -> EvidenceCollection:
        """Merges the ``EvidenceCollection`` of every ``SUCCESS`` result
        into one collection. ``FAILED`` results contribute no evidence
        (115I Section 5: a failure is never disguised as evidence).
        Raises ``ValueError`` (via ``EvidenceCollection``'s own
        construction check) if two skills produce colliding Evidence
        IDs -- this registry never silently drops or overrides one."""
        items = []
        for result in results:
            if result.status == RepositorySkillStatus.SUCCESS:
                items.extend(result.evidence.items)
        return EvidenceCollection(tuple(items))


def build_default_registry() -> RepositorySkillRegistry:
    """Convenience constructor registering the four 115J deterministic
    skills. Not itself wired into any lifecycle command, Decision
    Evaluation, or the Repository Transition Validator."""
    registry = RepositorySkillRegistry()
    for skill in (
        GitRepositorySkill(),
        RuntimeRepositorySkill(),
        ReportRepositorySkill(),
        MetadataRepositorySkill(),
    ):
        registry.register(skill)
    return registry

"""Phase 115D: Repository Evidence Provider Prototype.

Implements the first deterministic Repository Evidence Providers on top
of 115C's runtime Evidence objects (``core/evidence.py``): a common
``EvidenceProvider`` contract plus four concrete providers
(``GitEvidenceProvider``, ``RuntimeEvidenceProvider``,
``ReportEvidenceProvider``, ``MetadataEvidenceProvider``), each producing
an ``EvidenceCollection`` from real, read-only repository state.

Providers collect evidence. They never decide (115B "Evidence Provider
Contract Summary"). Nothing in this module:

- decides, votes on, or evaluates a transition
- mutates repository state
- promotes artifacts
- sends notifications
- bypasses the Repository Transition Validator
- authorizes or invokes execution
- depends on model/agent identity

Disconnected by design: not wired into the Repository Transition
Validator, any Decision Framework, any lifecycle command (``pcae phase
complete``, ``pcae task finish``, ``pcae push``), Notification Policy,
``pcae agent verify-handoff``, or ``pcae runtime inspect``. Read
directly by tests today; a future integration phase decides how (if at
all) these providers feed a Decision Framework.

No SLM/LLM/AI evidence provider is implemented here -- all four
providers declare ``EvidenceDeterminism.DETERMINISTIC``.
"""

from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar

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


@dataclass(frozen=True)
class EvidenceProviderContext:
    """Read-only handle to repository state passed to every provider.

    Providers read from ``root``; they never write to it, never invoke
    git/subprocess commands that mutate anything, and never touch
    anything outside the repository tree. ``strict``, when ``True``,
    tells a provider to re-raise an unexpected collection failure
    instead of degrading to unknown/unavailable evidence (Objective 5) --
    default ``False`` preserves the fail-closed-to-evidence behavior
    every provider uses by default.
    """

    root: HarnessPath
    strict: bool = False


@dataclass(frozen=True)
class EvidenceProviderResult:
    """The declared contract plus output of one provider's ``collect()``
    call, mirroring 115B's Evidence Provider Contract table: Provider ID,
    Producer label, Determinism class, Evidence categories produced,
    Required repository inputs, Scope, and Limitations."""

    provider_id: str
    producer: str
    determinism: EvidenceDeterminism
    categories: tuple[EvidenceCategory, ...]
    required_inputs: tuple[str, ...]
    scope: str
    limitations: tuple[str, ...]
    evidence: EvidenceCollection


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_git(args: list[str], root: HarnessPath, timeout: int = 10) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            args, cwd=str(root.path), capture_output=True, text=True, timeout=timeout,
        )
    except Exception:
        return None


class EvidenceProvider(ABC):
    """Common contract every Evidence Provider implements.

    Class attributes are the provider's declaration (115B Provider
    Contract); ``collect()`` is the one read-only operation a provider
    performs. A provider never mutates ``context.root``, never sends
    notifications, never invokes execution, and carries no field
    identifying the calling agent/model anywhere in its declaration or
    output.
    """

    provider_id: ClassVar[str]
    producer: ClassVar[str]
    determinism: ClassVar[EvidenceDeterminism]
    categories: ClassVar[tuple[EvidenceCategory, ...]]
    required_inputs: ClassVar[tuple[str, ...]]
    scope: ClassVar[str]
    limitations: ClassVar[tuple[str, ...]] = ()

    @abstractmethod
    def collect(self, context: EvidenceProviderContext) -> EvidenceProviderResult:
        """Collect evidence from ``context.root``. Never decides,
        mutates, promotes, notifies, or executes."""

    def _provenance(self, produced_from: str) -> EvidenceProvenance:
        return EvidenceProvenance(
            producer=self.producer,
            produced_from=produced_from,
            timestamp=_now_utc_iso(),
            deterministic_origin=True,
        )

    def _result(self, evidence: tuple[Evidence, ...]) -> EvidenceProviderResult:
        return EvidenceProviderResult(
            provider_id=self.provider_id,
            producer=self.producer,
            determinism=self.determinism,
            categories=self.categories,
            required_inputs=self.required_inputs,
            scope=self.scope,
            limitations=self.limitations,
            evidence=EvidenceCollection(evidence),
        )

    def _unknown_evidence(
        self,
        evidence_id: str,
        category: EvidenceCategory,
        scope: str,
        produced_from: str,
        explanation: str,
        limitation: str,
    ) -> Evidence:
        """The graceful-failure evidence item every provider emits in
        place of crashing (Objective 5), when ``context.strict`` is
        ``False``: an honestly unknown/unavailable observation, never a
        fabricated value."""
        return Evidence(
            evidence_id=evidence_id,
            source=self.producer,
            category=category,
            producer=self.producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.UNKNOWN,
            confidence=EvidenceConfidence.UNKNOWN,
            determinism=self.determinism,
            scope=scope,
            references=(),
            observed_value="unavailable",
            explanation=explanation,
            provenance=self._provenance(produced_from),
            limitations=limitation,
        )


# ═══════════════════════════════════════════════════════════════════════
# GitEvidenceProvider
# ═══════════════════════════════════════════════════════════════════════

class GitEvidenceProvider(EvidenceProvider):
    """Deterministic git-derived evidence: branch, working tree
    cleanliness, origin/main ahead/behind counts, and pushed status."""

    provider_id = "git_provider"
    producer = "GitEvidenceProvider"
    determinism = EvidenceDeterminism.DETERMINISTIC
    categories = (EvidenceCategory.GIT, EvidenceCategory.PUSH_STATE)
    required_inputs = (
        "git branch --show-current",
        "git status --porcelain",
        "git rev-list --count origin/main..HEAD",
        "git rev-list --count HEAD..origin/main",
    )
    scope = "repository git state"
    limitations = (
        "Requires a git repository with a resolvable origin/main "
        "remote-tracking ref; ahead/behind/pushed evidence degrades to "
        "unknown when origin/main cannot be resolved.",
    )

    def collect(self, context: EvidenceProviderContext) -> EvidenceProviderResult:
        root = context.root
        evidence: list[Evidence] = []

        try:
            branch_result = _run_git(["git", "branch", "--show-current"], root)
            if branch_result is not None and branch_result.returncode == 0:
                branch = branch_result.stdout.strip() or "HEAD"
                evidence.append(Evidence(
                    evidence_id="E-git-001",
                    source="Git",
                    category=EvidenceCategory.GIT,
                    producer=self.producer,
                    timestamp_utc=_now_utc_iso(),
                    freshness=EvidenceFreshness.CURRENT,
                    confidence=EvidenceConfidence.HIGH,
                    determinism=self.determinism,
                    scope="repository git state",
                    references=(),
                    observed_value=branch,
                    explanation=f"Current branch is {branch!r}.",
                    provenance=self._provenance("git branch --show-current"),
                ))
            else:
                evidence.append(self._unknown_evidence(
                    "E-git-001", EvidenceCategory.GIT, "repository git state",
                    "git branch --show-current",
                    "Could not determine current branch.",
                    "git branch --show-current failed or timed out.",
                ))
        except Exception:
            if context.strict:
                raise
            evidence.append(self._unknown_evidence(
                "E-git-001", EvidenceCategory.GIT, "repository git state",
                "git branch --show-current",
                "Could not determine current branch.",
                "Unexpected failure collecting branch evidence.",
            ))

        try:
            status_result = _run_git(["git", "status", "--porcelain"], root)
            if status_result is not None and status_result.returncode == 0:
                dirty = bool(status_result.stdout.strip())
                evidence.append(Evidence(
                    evidence_id="E-git-002",
                    source="Git",
                    category=EvidenceCategory.GIT,
                    producer=self.producer,
                    timestamp_utc=_now_utc_iso(),
                    freshness=EvidenceFreshness.CURRENT,
                    confidence=EvidenceConfidence.HIGH,
                    determinism=self.determinism,
                    scope="repository git state",
                    references=(),
                    observed_value="dirty" if dirty else "clean",
                    explanation=(
                        "Working tree has uncommitted changes." if dirty
                        else "Working tree is clean."
                    ),
                    provenance=self._provenance("git status --porcelain"),
                ))
            else:
                evidence.append(self._unknown_evidence(
                    "E-git-002", EvidenceCategory.GIT, "repository git state",
                    "git status --porcelain",
                    "Could not determine working tree cleanliness.",
                    "git status --porcelain failed or timed out.",
                ))
        except Exception:
            if context.strict:
                raise
            evidence.append(self._unknown_evidence(
                "E-git-002", EvidenceCategory.GIT, "repository git state",
                "git status --porcelain",
                "Could not determine working tree cleanliness.",
                "Unexpected failure collecting working tree evidence.",
            ))

        for evidence_id, args, direction, note in (
            ("E-git-003", ["git", "rev-list", "--count", "origin/main..HEAD"], "ahead", "HEAD is ahead of origin/main by"),
            ("E-git-004", ["git", "rev-list", "--count", "HEAD..origin/main"], "behind", "HEAD is behind origin/main by"),
        ):
            try:
                result = _run_git(args, root)
                if result is not None and result.returncode == 0 and result.stdout.strip().isdigit():
                    count = int(result.stdout.strip())
                    evidence.append(Evidence(
                        evidence_id=evidence_id,
                        source="Git",
                        category=EvidenceCategory.PUSH_STATE,
                        producer=self.producer,
                        timestamp_utc=_now_utc_iso(),
                        freshness=EvidenceFreshness.CURRENT,
                        confidence=EvidenceConfidence.HIGH,
                        determinism=self.determinism,
                        scope="repository push state",
                        references=(),
                        observed_value=count,
                        explanation=f"{note} {count} commit(s).",
                        provenance=self._provenance(" ".join(args)),
                    ))
                else:
                    evidence.append(self._unknown_evidence(
                        evidence_id, EvidenceCategory.PUSH_STATE, "repository push state",
                        " ".join(args),
                        f"Could not determine origin/main {direction} count.",
                        "origin/main is not resolvable or the git command failed.",
                    ))
            except Exception:
                if context.strict:
                    raise
                evidence.append(self._unknown_evidence(
                    evidence_id, EvidenceCategory.PUSH_STATE, "repository push state",
                    " ".join(args),
                    f"Could not determine origin/main {direction} count.",
                    "Unexpected failure collecting push-state evidence.",
                ))

        ahead_item = next((e for e in evidence if e.evidence_id == "E-git-003"), None)
        behind_item = next((e for e in evidence if e.evidence_id == "E-git-004"), None)
        if (
            ahead_item is not None and behind_item is not None
            and isinstance(ahead_item.observed_value, int)
            and isinstance(behind_item.observed_value, int)
        ):
            ahead = ahead_item.observed_value
            behind = behind_item.observed_value
            if ahead == 0 and behind == 0:
                pushed_status = "pushed"
            elif ahead > 0:
                pushed_status = "not_pushed"
            else:
                pushed_status = "behind_only"
            evidence.append(Evidence(
                evidence_id="E-git-005",
                source="Git",
                category=EvidenceCategory.PUSH_STATE,
                producer=self.producer,
                timestamp_utc=_now_utc_iso(),
                freshness=EvidenceFreshness.CURRENT,
                confidence=EvidenceConfidence.HIGH,
                determinism=self.determinism,
                scope="repository push state",
                references=(),
                observed_value=pushed_status,
                explanation=f"Derived pushed status: {pushed_status}.",
                provenance=self._provenance("derived from ahead/behind counts"),
            ))
        else:
            evidence.append(self._unknown_evidence(
                "E-git-005", EvidenceCategory.PUSH_STATE, "repository push state",
                "derived from ahead/behind counts",
                "Could not determine pushed status.",
                "Ahead/behind counts were not both determinable.",
            ))

        return self._result(tuple(evidence))


# ═══════════════════════════════════════════════════════════════════════
# RuntimeEvidenceProvider
# ═══════════════════════════════════════════════════════════════════════

class RuntimeEvidenceProvider(EvidenceProvider):
    """Deterministic runtime-derived evidence: runtime state, execution
    availability, and maximum plugin capability, reusing 111B/112E's own
    read-only introspection (``build_runtime_snapshot``) unmodified."""

    provider_id = "runtime_provider"
    producer = "RuntimeEvidenceProvider"
    determinism = EvidenceDeterminism.DETERMINISTIC
    categories = (EvidenceCategory.RUNTIME,)
    required_inputs = ("pcae.core.runtime_snapshot.build_runtime_snapshot",)
    scope = "runtime state and execution availability"
    limitations = (
        "Reflects only what 111B/112E's introspection already exposes; "
        "does not itself query external plugin processes.",
    )

    def collect(self, context: EvidenceProviderContext) -> EvidenceProviderResult:
        root = context.root
        try:
            from pcae.core.runtime_registry import RuntimeRegistry
            from pcae.core.runtime_snapshot import build_runtime_snapshot

            registry = RuntimeRegistry()
            snapshot = build_runtime_snapshot(root, registry)
            health = snapshot.health
        except Exception:
            if context.strict:
                raise
            return self._result((
                self._unknown_evidence(
                    "E-runtime-001", EvidenceCategory.RUNTIME, self.scope,
                    "build_runtime_snapshot",
                    "Could not build a runtime snapshot.",
                    "Unexpected failure building the runtime snapshot.",
                ),
            ))

        evidence = (
            Evidence(
                evidence_id="E-runtime-001",
                source="Runtime Inspect",
                category=EvidenceCategory.RUNTIME,
                producer=self.producer,
                timestamp_utc=_now_utc_iso(),
                freshness=EvidenceFreshness.CURRENT,
                confidence=EvidenceConfidence.HIGH,
                determinism=self.determinism,
                scope=self.scope,
                references=(),
                observed_value=health.current_runtime_state,
                explanation=f"Current runtime state is {health.current_runtime_state!r}.",
                provenance=self._provenance("build_runtime_snapshot().health.current_runtime_state"),
            ),
            Evidence(
                evidence_id="E-runtime-002",
                source="Runtime Inspect",
                category=EvidenceCategory.RUNTIME,
                producer=self.producer,
                timestamp_utc=_now_utc_iso(),
                freshness=EvidenceFreshness.CURRENT,
                confidence=EvidenceConfidence.HIGH,
                determinism=self.determinism,
                scope=self.scope,
                references=(),
                observed_value=health.execution_availability,
                explanation=f"Execution availability is {health.execution_availability!r}.",
                provenance=self._provenance("build_runtime_snapshot().health.execution_availability"),
            ),
            Evidence(
                evidence_id="E-runtime-003",
                source="Runtime Inspect",
                category=EvidenceCategory.RUNTIME,
                producer=self.producer,
                timestamp_utc=_now_utc_iso(),
                freshness=EvidenceFreshness.CURRENT,
                confidence=EvidenceConfidence.HIGH,
                determinism=self.determinism,
                scope=self.scope,
                references=(),
                observed_value=health.current_maximum_plugin_capability,
                explanation=(
                    f"Maximum plugin capability is "
                    f"{health.current_maximum_plugin_capability!r}."
                ),
                provenance=self._provenance("build_runtime_snapshot().health.current_maximum_plugin_capability"),
            ),
        )
        return self._result(evidence)


# ═══════════════════════════════════════════════════════════════════════
# ReportEvidenceProvider
# ═══════════════════════════════════════════════════════════════════════

class ReportEvidenceProvider(EvidenceProvider):
    """Deterministic evidence from the canonical latest phase report
    (``.pcae/phase-reports/latest.json``)."""

    provider_id = "report_provider"
    producer = "ReportEvidenceProvider"
    determinism = EvidenceDeterminism.DETERMINISTIC
    categories = (EvidenceCategory.REPORT,)
    required_inputs = (".pcae/phase-reports/latest.json",)
    scope = "latest canonical phase report"
    limitations = (
        "Reads only the canonical latest.json artifact; does not read "
        "quarantined or historical phase reports.",
    )

    _LATEST_JSON = Path(".pcae") / "phase-reports" / "latest.json"

    def collect(self, context: EvidenceProviderContext) -> EvidenceProviderResult:
        root = context.root
        path = root.join(self._LATEST_JSON)

        try:
            exists = path.is_file()
            data: dict[str, Any] | None = None
            if exists:
                data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            if context.strict:
                raise
            return self._result((
                self._unknown_evidence(
                    "E-report-001", EvidenceCategory.REPORT, self.scope,
                    str(self._LATEST_JSON),
                    "Could not read the latest phase report.",
                    "latest.json exists but could not be parsed as JSON.",
                ),
            ))

        evidence = [
            Evidence(
                evidence_id="E-report-001",
                source="Phase Report",
                category=EvidenceCategory.REPORT,
                producer=self.producer,
                timestamp_utc=_now_utc_iso(),
                freshness=EvidenceFreshness.CURRENT,
                confidence=EvidenceConfidence.HIGH,
                determinism=self.determinism,
                scope=self.scope,
                references=(),
                observed_value=exists,
                explanation=(
                    "Canonical latest phase report exists." if exists
                    else "No canonical latest phase report found."
                ),
                provenance=self._provenance(str(self._LATEST_JSON)),
            ),
        ]

        if not exists or data is None:
            for evidence_id, field_name in (
                ("E-report-002", "phase_id"),
                ("E-report-003", "report_completeness"),
                ("E-report-004", "recommended_next_phase"),
                ("E-report-005", "report_consistency"),
            ):
                evidence.append(self._unknown_evidence(
                    evidence_id, EvidenceCategory.REPORT, self.scope,
                    str(self._LATEST_JSON),
                    f"Could not determine {field_name}.",
                    "No canonical latest phase report exists yet.",
                ))
            return self._result(tuple(evidence))

        phase_id = data.get("phase_id", "")
        evidence.append(Evidence(
            evidence_id="E-report-002",
            source="Phase Report",
            category=EvidenceCategory.REPORT,
            producer=self.producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.HIGH,
            determinism=self.determinism,
            scope=self.scope,
            references=(),
            observed_value=phase_id,
            explanation=f"Latest canonical report phase_id is {phase_id!r}.",
            provenance=self._provenance(f"{self._LATEST_JSON}#phase_id"),
        ))

        completeness = data.get("report_completeness", "")
        evidence.append(Evidence(
            evidence_id="E-report-003",
            source="Phase Report",
            category=EvidenceCategory.REPORT,
            producer=self.producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.HIGH,
            determinism=self.determinism,
            scope=self.scope,
            references=(),
            observed_value=completeness,
            explanation=f"Latest canonical report completeness is {completeness!r}.",
            provenance=self._provenance(f"{self._LATEST_JSON}#report_completeness"),
        ))

        recommended_next = data.get("recommended_next_phase", "")
        evidence.append(Evidence(
            evidence_id="E-report-004",
            source="Phase Report",
            category=EvidenceCategory.REPORT,
            producer=self.producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.HIGH,
            determinism=self.determinism,
            scope=self.scope,
            references=(),
            observed_value=recommended_next,
            explanation=f"Recommended next phase per latest report: {recommended_next!r}.",
            provenance=self._provenance(f"{self._LATEST_JSON}#recommended_next_phase"),
        ))

        canonical_used = data.get("canonical_report_used")
        trust_warnings = data.get("trust_warnings") or []
        if isinstance(canonical_used, bool):
            consistent = canonical_used and not trust_warnings
            evidence.append(Evidence(
                evidence_id="E-report-005",
                source="Phase Report",
                category=EvidenceCategory.REPORT,
                producer=self.producer,
                timestamp_utc=_now_utc_iso(),
                freshness=EvidenceFreshness.CURRENT,
                confidence=(
                    EvidenceConfidence.HIGH if not trust_warnings
                    else EvidenceConfidence.MEDIUM
                ),
                determinism=self.determinism,
                scope=self.scope,
                references=(),
                observed_value="consistent" if consistent else "inconsistent",
                explanation=(
                    "Canonical report used and no trust warnings present."
                    if consistent else
                    "Canonical report validation failed or trust warnings present."
                ),
                provenance=self._provenance(f"{self._LATEST_JSON}#canonical_report_used,trust_warnings"),
                limitations="report_consistency is not part of 115B's frozen field set; derived here for convenience.",
            ))
        else:
            evidence.append(self._unknown_evidence(
                "E-report-005", EvidenceCategory.REPORT, self.scope,
                str(self._LATEST_JSON),
                "Could not determine report consistency.",
                "canonical_report_used field missing from latest.json.",
            ))

        return self._result(tuple(evidence))


# ═══════════════════════════════════════════════════════════════════════
# MetadataEvidenceProvider
# ═══════════════════════════════════════════════════════════════════════

class MetadataEvidenceProvider(EvidenceProvider):
    """Deterministic evidence from declared phase-completion metadata
    (``.pcae/phase-completion-metadata.json``)."""

    provider_id = "metadata_provider"
    producer = "MetadataEvidenceProvider"
    determinism = EvidenceDeterminism.DETERMINISTIC
    categories = (EvidenceCategory.METADATA,)
    required_inputs = (".pcae/phase-completion-metadata.json",)
    scope = "declared phase-completion metadata"
    limitations = (
        "Reads declared metadata only -- does not cross-check it against "
        "live git state (that is Push-State Reconciliation's job, not "
        "this provider's).",
    )

    _METADATA_JSON = Path(".pcae") / "phase-completion-metadata.json"

    def collect(self, context: EvidenceProviderContext) -> EvidenceProviderResult:
        root = context.root
        path = root.join(self._METADATA_JSON)

        try:
            exists = path.is_file()
            data: dict[str, Any] | None = None
            if exists:
                data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            if context.strict:
                raise
            return self._result((
                self._unknown_evidence(
                    "E-metadata-001", EvidenceCategory.METADATA, self.scope,
                    str(self._METADATA_JSON),
                    "Could not read declared phase-completion metadata.",
                    "phase-completion-metadata.json exists but could not be parsed as JSON.",
                ),
            ))

        evidence = [
            Evidence(
                evidence_id="E-metadata-001",
                source="Phase Metadata",
                category=EvidenceCategory.METADATA,
                producer=self.producer,
                timestamp_utc=_now_utc_iso(),
                freshness=EvidenceFreshness.CURRENT,
                confidence=EvidenceConfidence.HIGH,
                determinism=self.determinism,
                scope=self.scope,
                references=(),
                observed_value=exists,
                explanation=(
                    "Declared phase-completion metadata exists." if exists
                    else "No declared phase-completion metadata found."
                ),
                provenance=self._provenance(str(self._METADATA_JSON)),
            ),
        ]

        if not exists or data is None:
            for evidence_id, field_name in (
                ("E-metadata-002", "phase_id"),
                ("E-metadata-003", "pushed_status"),
                ("E-metadata-004", "origin_main_head_count"),
                ("E-metadata-005", "recommended_next_phase"),
            ):
                evidence.append(self._unknown_evidence(
                    evidence_id, EvidenceCategory.METADATA, self.scope,
                    str(self._METADATA_JSON),
                    f"Could not determine {field_name}.",
                    "No declared phase-completion metadata exists yet.",
                ))
            return self._result(tuple(evidence))

        phase_id = data.get("phase_id", "")
        evidence.append(Evidence(
            evidence_id="E-metadata-002",
            source="Phase Metadata",
            category=EvidenceCategory.METADATA,
            producer=self.producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.HIGH,
            determinism=self.determinism,
            scope=self.scope,
            references=(),
            observed_value=phase_id,
            explanation=f"Declared metadata phase_id is {phase_id!r}.",
            provenance=self._provenance(f"{self._METADATA_JSON}#phase_id"),
        ))

        pushed_status = data.get("pushed_status", "")
        evidence.append(Evidence(
            evidence_id="E-metadata-003",
            source="Phase Metadata",
            category=EvidenceCategory.METADATA,
            producer=self.producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.MEDIUM,
            determinism=self.determinism,
            scope=self.scope,
            references=(),
            observed_value=pushed_status,
            explanation=(
                f"Declared metadata pushed_status is {pushed_status!r} "
                "(declared, not reconciled against live git state)."
            ),
            provenance=self._provenance(f"{self._METADATA_JSON}#pushed_status"),
            limitations="Declared value only; may be stale relative to live git state.",
        ))

        origin_main_head_count = data.get("origin_main_head_count", 0)
        evidence.append(Evidence(
            evidence_id="E-metadata-004",
            source="Phase Metadata",
            category=EvidenceCategory.METADATA,
            producer=self.producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.MEDIUM,
            determinism=self.determinism,
            scope=self.scope,
            references=(),
            observed_value=origin_main_head_count,
            explanation=(
                f"Declared metadata origin_main_head_count is "
                f"{origin_main_head_count!r} (declared, not reconciled "
                "against live git state)."
            ),
            provenance=self._provenance(f"{self._METADATA_JSON}#origin_main_head_count"),
            limitations="Declared value only; may be stale relative to live git state.",
        ))

        recommended_next = data.get("recommended_next_phase", "")
        evidence.append(Evidence(
            evidence_id="E-metadata-005",
            source="Phase Metadata",
            category=EvidenceCategory.METADATA,
            producer=self.producer,
            timestamp_utc=_now_utc_iso(),
            freshness=EvidenceFreshness.CURRENT,
            confidence=EvidenceConfidence.HIGH,
            determinism=self.determinism,
            scope=self.scope,
            references=(),
            observed_value=recommended_next,
            explanation=f"Declared metadata recommended_next_phase is {recommended_next!r}.",
            provenance=self._provenance(f"{self._METADATA_JSON}#recommended_next_phase"),
        ))

        return self._result(tuple(evidence))

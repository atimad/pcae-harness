"""Canonical artifact promotion pipeline.

Phase 114A hardens the final artifact step after Repository Transition
Validator acceptance. The module is intentionally generic: phase reports are
the first caller, but future artifact classes can pass their own versioned and
canonical path/content maps through the same state machine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Mapping


class ArtifactState(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    CERTIFIED = "certified"
    CANONICAL = "canonical"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"


ALLOWED_STATE_TRANSITIONS: dict[ArtifactState, frozenset[ArtifactState]] = {
    ArtifactState.DRAFT: frozenset({ArtifactState.VALIDATED, ArtifactState.REJECTED}),
    ArtifactState.VALIDATED: frozenset({ArtifactState.CERTIFIED, ArtifactState.REJECTED, ArtifactState.QUARANTINED}),
    ArtifactState.CERTIFIED: frozenset({ArtifactState.CANONICAL, ArtifactState.QUARANTINED}),
    ArtifactState.CANONICAL: frozenset(),
    ArtifactState.REJECTED: frozenset(),
    ArtifactState.QUARANTINED: frozenset(),
}


@dataclass(frozen=True)
class PromotionDiagnostics:
    status: str
    message: str


@dataclass(frozen=True)
class ArtifactPromotionResult:
    artifact_type: str
    artifact_id: str
    source_state: ArtifactState
    target_state: ArtifactState
    promoted: bool
    paths: dict[str, str] = field(default_factory=dict)
    diagnostics: tuple[PromotionDiagnostics, ...] = ()


def can_transition(current: ArtifactState, target: ArtifactState) -> bool:
    return target in ALLOWED_STATE_TRANSITIONS[current]


def promote_artifact(
    *,
    artifact_type: str,
    artifact_id: str,
    source_state: ArtifactState,
    versioned_artifacts: Mapping[Path, str],
    canonical_artifacts: Mapping[Path, str],
) -> ArtifactPromotionResult:
    """Promote a certified artifact to canonical paths.

    The function is fail-closed: only ``Certified -> Canonical`` writes any
    files. Rejected and quarantined states remain diagnosable through the
    returned diagnostics but never touch canonical paths.
    """
    diagnostics: list[PromotionDiagnostics] = [
        PromotionDiagnostics("validated", f"{artifact_type} {artifact_id} promotion request validated"),
    ]

    if source_state != ArtifactState.CERTIFIED:
        diagnostics.append(
            PromotionDiagnostics(
                "rejected",
                f"{artifact_type} {artifact_id} is {source_state.value}, not certified",
            )
        )
        return ArtifactPromotionResult(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            source_state=source_state,
            target_state=source_state,
            promoted=False,
            diagnostics=tuple(diagnostics),
        )

    if not can_transition(source_state, ArtifactState.CANONICAL):
        diagnostics.append(
            PromotionDiagnostics(
                "rejected",
                f"{source_state.value} cannot transition to canonical",
            )
        )
        return ArtifactPromotionResult(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            source_state=source_state,
            target_state=source_state,
            promoted=False,
            diagnostics=tuple(diagnostics),
        )

    diagnostics.append(PromotionDiagnostics("certified", f"{artifact_type} {artifact_id} is certified"))

    written: dict[str, str] = {}
    for path, content in versioned_artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        written[path.name] = str(path)
    for path, content in canonical_artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        written[path.name] = str(path)

    diagnostics.append(PromotionDiagnostics("promoted", f"{artifact_type} {artifact_id} promoted to canonical"))
    return ArtifactPromotionResult(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        source_state=source_state,
        target_state=ArtifactState.CANONICAL,
        promoted=True,
        paths=written,
        diagnostics=tuple(diagnostics),
    )


def quarantine_artifact(
    *,
    artifact_type: str,
    artifact_id: str,
    quarantine_artifacts: Mapping[Path, str],
    blockers: tuple[str, ...],
) -> ArtifactPromotionResult:
    """Persist quarantined artifacts without touching canonical paths."""
    written: dict[str, str] = {}
    for path, content in quarantine_artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        written[path.name] = str(path)
    return ArtifactPromotionResult(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
        source_state=ArtifactState.QUARANTINED,
        target_state=ArtifactState.QUARANTINED,
        promoted=False,
        paths=written,
        diagnostics=(
            PromotionDiagnostics("quarantined", f"{artifact_type} {artifact_id} quarantined"),
            PromotionDiagnostics("rejected", "; ".join(blockers) if blockers else "not eligible for canonical promotion"),
        ),
    )

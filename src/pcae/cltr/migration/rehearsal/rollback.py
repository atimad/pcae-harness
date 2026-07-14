"""Stage 2 rollback rehearsal (135Q §33/§36/§37/§38, implemented in 135U).

Rehearses rolling the *rehearsal-only* pointer back to a prior, already
finalized, verified rehearsal generation. Never touches production
state: no production pointer, report, checkpoint, promotion,
notification, marker, or receipt is read for mutation, only the
rehearsal-only ``current-rehearsal`` pointer and this package's own
rollback evidence.

Frozen scope (135Q §36):

    May rehearse: retaining the prior pointer (no-op); switching the
    pointer to a prior verified generation; recording rollback evidence;
    invalidating progression eligibility for the generation rolled back
    from; epoch reconciliation if the rollback crosses an epoch
    boundary (not implemented -- see ``RollbackRejectedError`` raised
    for any cross-epoch target, disclosed as a Stage 2 follow-on, never
    silently mixed); preserving all generations and evidence.

    Must not: change production pointers, roll back the production
    report, undo external delivery, alter the production marker or
    receipt, or rewrite history.

Roll-forward (135Q §37) is deliberately **not implemented** here: no
code path re-promotes a previously-rolled-back generation to current
automatically or via a "roll forward" request. A generation that was
rolled back away from remains reachable only via an explicit *new*
rollback request naming it as the target again (ordinary rollback
semantics, not a distinct roll-forward primitive) -- this phase adds no
additional mechanism, matching the 135U phase brief's instruction to
implement only roll-forward behavior explicitly frozen by the contract,
and 135Q §37 freezes only a *preference* (prefer reconciliation over
rollback in specific scenarios), not a roll-forward command or state
machine.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Callable, Optional

from pcae.cltr.canonicalization import canonicalize_dict
from pcae.cltr.digest import compute_dict_digest
from pcae.cltr.migration.disclosure import NON_AUTHORITY_DISCLOSURE
from pcae.cltr.migration.persistence import PathContainmentError, is_safe_segment, timestamp, write_atomic, write_immutable
from pcae.cltr.migration.rehearsal.configuration import MANIFEST_SCHEMA_ID, MANIFEST_SCHEMA_VERSION
from pcae.cltr.migration.rehearsal.digest import compute_artifact_digest, compute_generation_digest
from pcae.cltr.migration.rehearsal.enums import RollbackOutcome
from pcae.cltr.migration.rehearsal.identity import PRODUCTION_AUTHORITY_DISCLOSURE, compute_rollback_request_id
from pcae.cltr.migration.rehearsal.models import RollbackEvidenceRecord, RollbackRequest
from pcae.cltr.migration.rehearsal.persistence import (
    DEFAULT_MIGRATION_ROOT,
    generations_dir,
    quarantine_dir,
    read_json,
    rollback_conflicts_dir,
    rollback_request_path,
    rollbacks_dir,
)
from pcae.cltr.migration.rehearsal.pointer import PointerRejectedError, publish_generation, read_pointer

ROLLBACK_EVIDENCE_SCHEMA_VERSION = "1.0.0"
ROLLBACK_STAGE = "stage_2_rollback_rehearsal"

FaultInjector = Callable[[str], None]


def _no_op_injector(_step: str) -> None:
    return None


class RollbackRejectedError(ValueError):
    """Fail-closed: every rejection reason is explicit, mirroring
    ``PointerRejectedError``'s discipline for ordinary forward
    publication."""


@dataclasses.dataclass(frozen=True)
class RollbackResult:
    outcome: RollbackOutcome
    rollback_request_id: Optional[str] = None
    source_rehearsal_generation_id: Optional[str] = None
    target_rehearsal_generation_id: Optional[str] = None
    limitations: tuple[str, ...] = ()


def _evidence_path(migration_root: Path, migration_epoch: str, transition_id: str, rollback_request_id: str) -> Path:
    directory = rollbacks_dir(migration_root, migration_epoch, transition_id)
    if not is_safe_segment(f"{rollback_request_id}.evidence.json"):
        raise PathContainmentError(f"unsafe rollback request id: {rollback_request_id!r}")
    return directory / f"{rollback_request_id}.evidence.json"


def build_rollback_request(
    *,
    phase_id: str,
    transition_id: str,
    migration_epoch: str,
    authority_epoch: str,
    target_rehearsal_generation_id: str,
    reason: str,
    migration_root: Path = DEFAULT_MIGRATION_ROOT,
) -> RollbackRequest:
    """Binds the request to the *currently observed* pointer state --
    never inferred from newest/oldest file, timestamps, titles, or Git
    history. If the live pointer has moved by the time
    ``execute_rollback`` runs, the request's ``expected_pointer_
    generation_id`` will no longer match and execution fails closed
    (135U's "stale current-pointer expectation" containment
    requirement)."""

    if not is_safe_segment(target_rehearsal_generation_id):
        raise RollbackRejectedError(f"unsafe target generation id: {target_rehearsal_generation_id!r}")

    pointer = read_pointer(migration_root, migration_epoch, transition_id)
    current_generation_id = pointer.get("rehearsal_generation_id") if pointer else None
    source_digest = pointer.get("generation_digest") if pointer else None

    rollback_request_id = compute_rollback_request_id(
        phase_id=phase_id,
        transition_id=transition_id,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        source_rehearsal_generation_id=current_generation_id,
        target_rehearsal_generation_id=target_rehearsal_generation_id,
        reason=reason,
    )
    return RollbackRequest(
        rollback_request_id=rollback_request_id,
        phase_id=phase_id,
        transition_id=transition_id,
        migration_epoch=migration_epoch,
        authority_epoch=authority_epoch,
        current_rehearsal_generation_id=current_generation_id,
        target_rehearsal_generation_id=target_rehearsal_generation_id,
        source_result_evidence_digest=source_digest,
        expected_pointer_generation_id=current_generation_id,
        reason=reason,
        non_authority_disclosure=dict(NON_AUTHORITY_DISCLOSURE),
    )


def _verify_generation_on_disk(
    migration_root: Path, migration_epoch: str, transition_id: str, generation_id: str, expected_digest: Optional[str]
) -> dict:
    """135U rollback-target validation: manifest presence, schema,
    digest, and per-artifact tamper detection, all re-derived from bytes
    on disk -- never trusted from an in-memory/cached value."""

    generation_dir = generations_dir(migration_root, migration_epoch, transition_id, generation_id)
    if generation_dir.is_symlink():
        raise RollbackRejectedError(f"refusing symlinked rehearsal generation path: {generation_dir}")
    manifest = read_json(generation_dir / "manifest.json")
    if manifest is None:
        raise RollbackRejectedError(f"rollback target has no manifest.json: {generation_dir}")
    if manifest.get("manifest_schema_id") != MANIFEST_SCHEMA_ID or manifest.get("manifest_schema_version") != MANIFEST_SCHEMA_VERSION:
        raise RollbackRejectedError("unsupported manifest schema for rollback target")
    if manifest.get("migration_epoch") != migration_epoch or manifest.get("transition_id") != transition_id:
        raise RollbackRejectedError("rollback target is bound to a different migration_epoch/transition_id")
    if expected_digest is not None and manifest.get("generation_digest") != expected_digest:
        raise RollbackRejectedError("generation digest mismatch for rollback target")

    inventory = manifest.get("artifact_inventory", [])
    ordered_digests = []
    for entry in inventory:
        artifact_path = generation_dir / entry["path"]
        if artifact_path.is_symlink():
            raise RollbackRejectedError(f"refusing symlinked rollback-target artifact: {artifact_path}")
        content = read_json(artifact_path)
        if content is None:
            raise RollbackRejectedError(f"missing or unreadable rollback-target artifact: {artifact_path}")
        recomputed = compute_artifact_digest(content)
        if recomputed != entry.get("digest"):
            raise RollbackRejectedError(f"artifact digest mismatch for rollback target: {entry.get('path')}")
        if content.get("rehearsal_generation_id") != generation_id:
            raise RollbackRejectedError(f"split-brain: {entry.get('path')} bound to a different rehearsal_generation_id")
        if content.get("transition_id") != transition_id:
            raise RollbackRejectedError(f"split-brain: {entry.get('path')} bound to a different transition_id")
        ordered_digests.append(recomputed)

    recomputed_generation_digest = compute_generation_digest(
        artifact_digests_in_order=tuple(ordered_digests),
        rehearsal_generation_id=generation_id,
        migration_epoch=migration_epoch,
        authority_epoch=manifest.get("authority_epoch"),
        transition_id=transition_id,
    )
    if recomputed_generation_digest != manifest.get("generation_digest"):
        raise RollbackRejectedError("recomputed generation digest mismatch for rollback target")
    return manifest


def validate_rollback_target(*, migration_root: Path, request: RollbackRequest) -> dict:
    target_id = request.target_rehearsal_generation_id
    if not is_safe_segment(target_id):
        raise RollbackRejectedError(f"unsafe target generation id: {target_id!r}")
    if not request.authority_epoch or request.authority_epoch.split("|", 1)[0].lower() != "legacy":
        raise RollbackRejectedError("rollback rehearsal requires a legacy-authoritative authority_epoch")

    quarantine_record = quarantine_dir(migration_root, request.migration_epoch, request.transition_id, target_id) / "quarantine_record.json"
    if quarantine_record.exists():
        raise RollbackRejectedError("refusing to roll back to a quarantined generation")

    manifest = _verify_generation_on_disk(
        migration_root, request.migration_epoch, request.transition_id, target_id, expected_digest=None
    )
    if manifest.get("verification_status") != "verified":
        raise RollbackRejectedError("refusing to roll back to an unverified rehearsal generation")
    if manifest.get("candidate_or_authoritative_role") != "rehearsal_candidate_generation":
        raise RollbackRejectedError("rollback target does not carry the expected rehearsal-candidate role")
    return manifest


def _build_evidence(
    *,
    request: RollbackRequest,
    pointer_before: Optional[dict],
    pointer_after: Optional[dict],
    target_manifest: Optional[dict],
    outcome: RollbackOutcome,
    verification_result: str,
    publication_result: str,
    limitations: tuple[str, ...] = (),
) -> RollbackEvidenceRecord:
    evidence_id = compute_dict_digest(
        {"rollback_request_id": request.rollback_request_id, "outcome": outcome.value}
    )
    record = RollbackEvidenceRecord(
        evidence_id=evidence_id,
        schema_version=ROLLBACK_EVIDENCE_SCHEMA_VERSION,
        migration_stage=ROLLBACK_STAGE,
        migration_epoch=request.migration_epoch,
        authority_epoch=request.authority_epoch,
        production_authority=PRODUCTION_AUTHORITY_DISCLOSURE,
        transition_id=request.transition_id,
        phase_id=request.phase_id,
        rollback_request_id=request.rollback_request_id,
        source_rehearsal_generation_id=request.current_rehearsal_generation_id,
        target_rehearsal_generation_id=request.target_rehearsal_generation_id,
        pointer_state_before=pointer_before,
        pointer_state_after=pointer_after,
        target_manifest_digest=(target_manifest or {}).get("generation_digest"),
        target_generation_digest=(target_manifest or {}).get("generation_digest"),
        outcome=outcome,
        verification_result=verification_result,
        publication_result=publication_result,
        limitations=tuple(limitations),
        non_authority_disclosure=dict(NON_AUTHORITY_DISCLOSURE),
        created_at=timestamp(),
    )
    digest = compute_dict_digest(record.digestible_payload())
    return record.with_digest(digest)


def _persist_evidence(migration_root: Path, record: RollbackEvidenceRecord) -> None:
    path = _evidence_path(migration_root, record.migration_epoch, record.transition_id, record.rollback_request_id)
    payload = record.digestible_payload()
    payload["record_digest"] = record.record_digest
    write_atomic(path, canonicalize_dict(payload))


def _reject(
    migration_root: Path,
    request: RollbackRequest,
    pointer_before: Optional[dict],
    target_manifest: Optional[dict],
    reason: str,
) -> RollbackResult:
    record = _build_evidence(
        request=request,
        pointer_before=pointer_before,
        pointer_after=pointer_before,
        target_manifest=target_manifest,
        outcome=RollbackOutcome.REJECTED,
        verification_result="rejected",
        publication_result="not_attempted",
        limitations=(reason,),
    )
    _persist_evidence(migration_root, record)
    return RollbackResult(
        outcome=RollbackOutcome.REJECTED,
        rollback_request_id=request.rollback_request_id,
        source_rehearsal_generation_id=request.current_rehearsal_generation_id,
        target_rehearsal_generation_id=request.target_rehearsal_generation_id,
        limitations=(reason,),
    )


def execute_rollback(
    *,
    request: RollbackRequest,
    migration_root: Path = DEFAULT_MIGRATION_ROOT,
    fault_injector: FaultInjector = _no_op_injector,
) -> RollbackResult:
    """135U's frozen rollback sequence (11 steps): load pointer; verify
    current pointer/generation; validate request identity (idempotency /
    conflicting replay); validate target; write durable intent evidence;
    prepare pointer content (no separate temp-file primitive needed --
    ``write_atomic``/``write_pointer_atomic`` already perform an atomic
    tmp-write + ``os.replace``); atomically replace the pointer; read
    back; verify the target generation; persist final evidence; expose
    read-only status/reconciliation (``status.py``/``reconciliation.py``,
    unchanged by this module, already read the pointer/evidence this
    function writes)."""

    step = "load_current_pointer"
    try:
        fault_injector(step)
        pointer_before = read_pointer(migration_root, request.migration_epoch, request.transition_id)
        live_current_id = pointer_before.get("rehearsal_generation_id") if pointer_before else None

        step = "request_identity_conflict_check"
        fault_injector(step)
        request_path = rollback_request_path(migration_root, request.migration_epoch, request.transition_id, request.rollback_request_id)
        request_payload = canonicalize_dict(dataclasses.asdict(request))
        stored_request_bytes = read_json(request_path)
        already_registered = stored_request_bytes is not None
        try:
            write_immutable(request_path, request_payload)
        except ValueError:
            conflict_dir = rollback_conflicts_dir(migration_root, request.migration_epoch, request.transition_id)
            write_atomic(conflict_dir / f"{request.rollback_request_id}-{timestamp()}.json", request_payload)
            return RollbackResult(
                outcome=RollbackOutcome.CONFLICT,
                rollback_request_id=request.rollback_request_id,
                source_rehearsal_generation_id=request.current_rehearsal_generation_id,
                target_rehearsal_generation_id=request.target_rehearsal_generation_id,
                limitations=("rollback_request_id reused with different request content; never published",),
            )

        step = "idempotency_check"
        fault_injector(step)
        existing_evidence = read_json(_evidence_path(migration_root, request.migration_epoch, request.transition_id, request.rollback_request_id))
        if (
            already_registered
            and existing_evidence is not None
            and existing_evidence.get("outcome") in (RollbackOutcome.PUBLISHED.value, RollbackOutcome.VERIFIED.value)
            and live_current_id == request.target_rehearsal_generation_id
        ):
            # Byte-identical replay of a request that has already durably
            # achieved its own target: reported idempotent-replay, no
            # further pointer/evidence churn, regardless of whether this
            # specific request's own ``expected_pointer_generation_id``
            # would now read as stale against the (post-success) live
            # pointer -- the live pointer *is* this request's own prior
            # success, not a foreign, concurrent mutation.
            return RollbackResult(
                outcome=RollbackOutcome.IDEMPOTENT_REPLAY,
                rollback_request_id=request.rollback_request_id,
                source_rehearsal_generation_id=request.current_rehearsal_generation_id,
                target_rehearsal_generation_id=request.target_rehearsal_generation_id,
            )

        step = "recovery_already_at_target_check"
        fault_injector(step)
        if already_registered and live_current_id == request.target_rehearsal_generation_id:
            # This exact rollback_request_id was durably registered before
            # (135U crash-matrix: "after_pointer_replace" fault) and the
            # live pointer already reflects its own target -- the atomic
            # replace itself already succeeded; only evidence completion
            # was interrupted. Complete it now rather than rejecting a
            # replay of the request's *own* prior, already-durable
            # success as a stale foreign mutation (135U phase brief:
            # "prefer reconciliation/roll-forward over rollback ... never
            # silently replay uncertain publication").
            try:
                target_manifest = validate_rollback_target(migration_root=migration_root, request=request)
            except (RollbackRejectedError, PathContainmentError) as exc:
                return _reject(migration_root, request, pointer_before, None, str(exc))
            record = _build_evidence(
                request=request, pointer_before=pointer_before, pointer_after=pointer_before,
                target_manifest=target_manifest, outcome=RollbackOutcome.PUBLISHED,
                verification_result="verified", publication_result="published",
                limitations=("evidence completed on recovery replay; pointer replace had already durably succeeded",),
            )
            _persist_evidence(migration_root, record)
            return RollbackResult(
                outcome=RollbackOutcome.PUBLISHED,
                rollback_request_id=request.rollback_request_id,
                source_rehearsal_generation_id=request.current_rehearsal_generation_id,
                target_rehearsal_generation_id=request.target_rehearsal_generation_id,
            )

        step = "stale_pointer_expectation_check"
        fault_injector(step)
        if live_current_id != request.expected_pointer_generation_id:
            return _reject(
                migration_root, request, pointer_before, None,
                f"stale current-pointer expectation: request expected {request.expected_pointer_generation_id!r}, "
                f"live pointer is {live_current_id!r}",
            )

        step = "verify_current_generation"
        fault_injector(step)
        if live_current_id is not None:
            _verify_generation_on_disk(
                migration_root, request.migration_epoch, request.transition_id, live_current_id,
                pointer_before.get("generation_digest") if pointer_before else None,
            )

        step = "validate_target"
        fault_injector(step)
        try:
            target_manifest = validate_rollback_target(migration_root=migration_root, request=request)
        except (RollbackRejectedError, PathContainmentError) as exc:
            return _reject(migration_root, request, pointer_before, None, str(exc))

        if request.target_rehearsal_generation_id == live_current_id:
            step = "no_op_retain"
            record = _build_evidence(
                request=request, pointer_before=pointer_before, pointer_after=pointer_before,
                target_manifest=target_manifest, outcome=RollbackOutcome.VERIFIED,
                verification_result="verified", publication_result="retained_no_op",
                limitations=("target already current; rollback rehearsed as a no-op retain (135Q §36)",),
            )
            _persist_evidence(migration_root, record)
            return RollbackResult(
                outcome=RollbackOutcome.VERIFIED,
                rollback_request_id=request.rollback_request_id,
                source_rehearsal_generation_id=live_current_id,
                target_rehearsal_generation_id=request.target_rehearsal_generation_id,
            )

        step = "write_intent_evidence"
        fault_injector(step)
        intent_record = _build_evidence(
            request=request, pointer_before=pointer_before, pointer_after=None,
            target_manifest=target_manifest, outcome=RollbackOutcome.REQUESTED,
            verification_result="verified", publication_result="not_attempted",
        )
        _persist_evidence(migration_root, intent_record)

        step = "prepare_temporary_pointer"
        fault_injector(step)

        step = "atomic_pointer_replace"
        fault_injector("before_pointer_replace")
        try:
            publish_generation(
                migration_root=migration_root,
                migration_epoch=request.migration_epoch,
                authority_epoch=request.authority_epoch,
                transition_id=request.transition_id,
                rehearsal_generation_id=request.target_rehearsal_generation_id,
                generation_digest=target_manifest.get("generation_digest"),
            )
        except PointerRejectedError as exc:
            return _reject(migration_root, request, pointer_before, target_manifest, str(exc))
        fault_injector("after_pointer_replace")

        step = "pointer_readback"
        fault_injector(step)
        pointer_after = read_pointer(migration_root, request.migration_epoch, request.transition_id)
        readback_ok = pointer_after is not None and pointer_after.get("rehearsal_generation_id") == request.target_rehearsal_generation_id

        step = "verify_target_generation_post_write"
        fault_injector(step)
        outcome = RollbackOutcome.PUBLISHED if readback_ok else RollbackOutcome.PUBLICATION_UNCERTAIN

        step = "final_evidence_recording"
        fault_injector("before_final_evidence")
        record = _build_evidence(
            request=request, pointer_before=pointer_before, pointer_after=pointer_after,
            target_manifest=target_manifest, outcome=outcome,
            verification_result="verified" if readback_ok else "uncertain",
            publication_result="published" if readback_ok else "publication_uncertain",
            limitations=() if readback_ok else ("pointer readback did not confirm the rollback target; treated as uncertain, not silently retried",),
        )
        _persist_evidence(migration_root, record)
        fault_injector("after_final_evidence")

        return RollbackResult(
            outcome=outcome,
            rollback_request_id=request.rollback_request_id,
            source_rehearsal_generation_id=request.current_rehearsal_generation_id,
            target_rehearsal_generation_id=request.target_rehearsal_generation_id,
        )
    except Exception as exc:  # noqa: BLE001 - rollback failure must never affect production finalization
        return RollbackResult(
            outcome=RollbackOutcome.RECOVERY_REQUIRED,
            rollback_request_id=getattr(request, "rollback_request_id", None),
            limitations=(f"{step}: {type(exc).__name__}: {exc}",),
        )


def rollback_recovery_state(
    migration_root: Path, migration_epoch: str, transition_id: str, rollback_request_id: str
) -> Optional[dict]:
    """Read-only: classifies an in-flight or completed rollback purely
    from recorded evidence -- never from titles, Git history, or
    "latest file present" heuristics (mirrors ``recovery.classify``)."""

    return read_json(_evidence_path(migration_root, migration_epoch, transition_id, rollback_request_id))


def list_rollback_evidence(migration_root: Path, migration_epoch: str, transition_id: str) -> list[dict]:
    directory = rollbacks_dir(migration_root, migration_epoch, transition_id)
    if not directory.exists():
        return []
    records = []
    for path in sorted(directory.glob("*.evidence.json")):
        payload = read_json(path)
        if payload is not None:
            records.append(payload)
    return records


def rollback_status(phase_id: str, migration_root: Path = DEFAULT_MIGRATION_ROOT) -> dict:
    """Read-only rollback-readiness inspection (135Q §34's read-only
    status pattern, applied to rollback targets). Never derives,
    finalizes, publishes, or mutates anything."""

    from pcae.cltr.migration.rehearsal.reconciliation import _find_rehearsal_transitions_for_phase

    matches = _find_rehearsal_transitions_for_phase(Path(migration_root), phase_id)
    if not matches:
        return {
            "phase_id": phase_id,
            "found": False,
            "blockers": ["no rehearsal evidence exists for this phase_id"],
            **NON_AUTHORITY_DISCLOSURE,
        }

    transitions = []
    for match in matches:
        migration_epoch = match["migration_epoch"]
        transition_id = match["transition_id"]
        current_generation_id = match["rehearsal_generation_id"]
        generations_root = generations_dir(Path(migration_root), migration_epoch, transition_id, current_generation_id).parent
        rollback_targets = []
        if generations_root.exists():
            for entry in sorted(p.name for p in generations_root.iterdir() if p.is_dir()):
                manifest = read_json(generations_root / entry / "manifest.json")
                quarantined = (
                    quarantine_dir(Path(migration_root), migration_epoch, transition_id, entry) / "quarantine_record.json"
                ).exists()
                rollback_targets.append(
                    {
                        "rehearsal_generation_id": entry,
                        "is_current": entry == current_generation_id,
                        "verification_status": manifest.get("verification_status") if manifest else None,
                        "quarantined": quarantined,
                        "eligible_rollback_target": bool(manifest) and manifest.get("verification_status") == "verified" and not quarantined,
                    }
                )
        transitions.append(
            {
                "transition_id": transition_id,
                "migration_epoch": migration_epoch,
                "current_rehearsal_generation_id": current_generation_id,
                "rollback_targets": rollback_targets,
                "rollback_history": list_rollback_evidence(Path(migration_root), migration_epoch, transition_id),
            }
        )

    return {
        "phase_id": phase_id,
        "found": True,
        "transitions": transitions,
        "blockers": [],
        **NON_AUTHORITY_DISCLOSURE,
    }

"""Fixture-driven generator (135E §3, §17, §26 Stage 4).

`generate()` consumes an explicit, immutable fixture bundle (a plain dict —
see `docs/PHASE_135_CANONICAL_TRANSITION_RECORD_READ_ONLY_PROTOTYPE.md` for
the bundle shape) and orchestrates identity resolution, the state-machine
transition sequence, commit-ownership classification, invariant evaluation,
and digest sealing into one candidate `TransitionRecord`.

It never reads a production "latest" file, never infers an active phase,
never updates a production artifact, and never invokes a subprocess.
"""

from __future__ import annotations

from dataclasses import dataclass

from pcae.cltr_prototype import digest as digest_mod
from pcae.cltr_prototype import identity as identity_mod
from pcae.cltr_prototype import invariants as invariants_mod
from pcae.cltr_prototype import state_machine as sm
from pcae.cltr_prototype.models import (
    CommitClassificationResult,
    CommitDeclaration,
    CommitOwnershipClassification,
    CommitRole,
    EvidenceRef,
    EvidenceType,
    EvidenceVerificationStatus,
    TransitionRecord,
)


class GeneratorError(Exception):
    pass


class MissingInputAuthorityError(GeneratorError):
    pass


class UnsupportedStateError(GeneratorError):
    pass


class UnsupportedContractVersionError(GeneratorError):
    pass


class UnsupportedSchemaVersionError(GeneratorError):
    pass


class InvariantFailureError(GeneratorError):
    def __init__(self, failures):
        self.failures = failures
        super().__init__(f"{len(failures)} applicable Blocking invariant(s) failed during generation")


_SUPPORTED_SCHEMA_VERSIONS = {"cltr-prototype-0.1"}
_SUPPORTED_CONTRACT_VERSIONS = {"CLTR-001/1.0"}


def _evidence_ref_from_dict(d: dict, *, transition_id: str, phase_id: str) -> EvidenceRef:
    return EvidenceRef(
        evidence_id=d["evidence_id"],
        evidence_type=EvidenceType(d["evidence_type"]),
        transition_id=d.get("transition_id", transition_id),
        phase_id=d.get("phase_id", phase_id),
        verification_status=EvidenceVerificationStatus(d["verification_status"]),
        source_path=d.get("source_path"),
        digest=d.get("digest"),
        source_revision=d.get("source_revision"),
        observation_timestamp=d.get("observation_timestamp"),
        limitation=d.get("limitation"),
    )


_STEP_HANDLERS = {
    "T1_propose_transition": None,  # handled specially (creates the record)
    "T2_begin_certification": sm.t2_begin_certification,
    "T3_certify": sm.t3_certify,
    "T4_certification_fail": sm.t4_certification_fail,
    "T5_begin_promotion": sm.t5_begin_promotion,
    "T6_promote_succeed": sm.t6_promote_succeed,
    "T7_promote_fail": sm.t7_promote_fail,
    "T8_begin_notification": sm.t8_begin_notification,
    "T9_notify_confirm": sm.t9_notify_confirm,
    "T10_notify_unconfirmed": sm.t10_notify_unconfirmed,
    "T11_notify_retry": sm.t11_notify_retry,
    "T12_reconcile_receipt": sm.t12_reconcile_receipt,
    "T13_close_success": sm.t13_close_success,
    "T14_close_partial": sm.t14_close_partial,
    "T15_quarantine": sm.t15_quarantine,
    "T16_supersede": sm.t16_supersede,
}

_BINDING_KWARG_NAMES = frozenset(
    {
        "report_binding",
        "metadata_binding",
        "snapshot_binding",
        "checkpoint_binding",
        "promotion_binding",
        "notification_binding",
        "marker_binding",
        "receipt_binding",
        "architecture_status_binding",
        "receipt_binding",
    }
)


def _resolve_step_kwargs(raw_kwargs: dict, *, transition_id: str, phase_id: str) -> dict:
    resolved = {}
    for key, value in raw_kwargs.items():
        if key == "at":
            resolved[key] = value
            continue
        if key in _BINDING_KWARG_NAMES and isinstance(value, dict):
            resolved[key] = _evidence_ref_from_dict(value, transition_id=transition_id, phase_id=phase_id)
        else:
            resolved[key] = value
    return resolved


@dataclass(frozen=True)
class GenerationResult:
    record: TransitionRecord
    invariant_results: list
    commit_classifications: tuple


def classify_commits(
    declared_commits: tuple,
    classification_hints: dict,
    *,
    repository_identity: str,
    branch_identity: str,
    source_revision: str,
) -> tuple:
    """Classify each declared commit into the frozen three-outcome model
    (135E §12.1). `classification_hints` is an explicit, caller-supplied
    dict of {commit_hash: {"classification": ..., "reason": ...}} — the
    prototype never infers this from Git history scanning by default; the
    integration-fixture mode (bounded, explicit `git log -1 <hash>`) is out
    of scope for this generator and is exercised only by comparison.py's
    integration fixtures, per 135E §3.2/§12.
    """

    results = []
    for commit in declared_commits:
        hint = classification_hints.get(commit.commit_hash)
        if hint is None:
            # No explicit resolution supplied: fail closed as unverifiable,
            # never silently 'verified' (135E §12, CLTR-COMMIT-3).
            results.append(
                CommitClassificationResult(
                    commit_hash=commit.commit_hash,
                    classification=CommitOwnershipClassification.UNVERIFIABLE,
                    reason="no explicit classification hint supplied; hash cannot be resolved against the bound repository identity/revision without live inspection",
                )
            )
            continue
        requested = CommitOwnershipClassification(hint["classification"])
        if requested == CommitOwnershipClassification.VERIFIED:
            proof_bound = (
                hint.get("resolvable") is True
                and hint.get("repository_identity") == repository_identity
                and hint.get("branch_identity") == branch_identity
                and hint.get("source_revision") == source_revision
            )
            if not proof_bound:
                results.append(
                    CommitClassificationResult(
                        commit_hash=commit.commit_hash,
                        classification=CommitOwnershipClassification.UNVERIFIABLE,
                        reason="verified hint lacked matching resolvability, repository, branch, or revision evidence; downgraded fail-closed",
                    )
                )
                continue
        results.append(
            CommitClassificationResult(
                commit_hash=commit.commit_hash,
                classification=requested,
                reason=hint.get("reason", ""),
            )
        )
    return tuple(results)


def generate(bundle: dict, *, fail_closed_on_invariant_failure: bool = False) -> GenerationResult:
    """Generate a candidate CLTR record from an explicit fixture bundle.

    `bundle` must be a plain dict with keys: `schema_version`,
    `contract_version`, `identity` (explicit declared-field dict, see
    `identity.resolve_identity`), `source_revision`, optionally
    `declared_commits`, `commit_classifications` (explicit hints), and
    `steps` (an ordered list of `{"transition": <name>, ...kwargs}`).

    Never reads a production "latest" file, never infers active phase
    identity, never performs a Git or filesystem scan, never invokes a
    subprocess.
    """

    schema_version = bundle.get("schema_version")
    contract_version = bundle.get("contract_version")
    if schema_version is not None and schema_version not in _SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedSchemaVersionError(f"unsupported schema_version: {schema_version!r}")
    if contract_version is not None and contract_version not in _SUPPORTED_CONTRACT_VERSIONS:
        raise UnsupportedContractVersionError(f"unsupported contract_version: {contract_version!r}")

    if "identity" not in bundle:
        raise MissingInputAuthorityError("bundle is missing 'identity'")
    if "source_revision" not in bundle or not bundle["source_revision"]:
        raise MissingInputAuthorityError("bundle is missing 'source_revision'")
    if "steps" not in bundle or not bundle["steps"]:
        raise MissingInputAuthorityError("bundle is missing 'steps'")

    ident = identity_mod.resolve_identity(bundle["identity"])

    declared_commits = tuple(
        CommitDeclaration(commit_hash=c["commit_hash"], declared_role=CommitRole(c["declared_role"]))
        for c in bundle.get("declared_commits", [])
    )
    classification_hints = {c["commit_hash"]: c for c in bundle.get("commit_classifications", [])}
    commit_classifications = classify_commits(
        declared_commits,
        classification_hints,
        repository_identity=ident.repository_identity,
        branch_identity=ident.branch_identity,
        source_revision=bundle["source_revision"],
    )

    steps = bundle["steps"]
    first_step = steps[0]
    if first_step.get("transition") != "T1_propose_transition":
        raise MissingInputAuthorityError("the first step must be T1_propose_transition")

    record = sm.t1_propose_transition(
        ident,
        bundle["source_revision"],
        at=first_step["at"],
        declared_commits=declared_commits,
        evidence_refs=tuple(
            _evidence_ref_from_dict(e, transition_id=ident.transition_id, phase_id=ident.phase_id)
            for e in bundle.get("evidence_refs", [])
        ),
    ).new_record

    for step in steps[1:]:
        transition_name = step.get("transition")
        handler = _STEP_HANDLERS.get(transition_name)
        if handler is None:
            raise UnsupportedStateError(f"unknown or unsupported transition step: {transition_name!r}")
        kwargs = {k: v for k, v in step.items() if k != "transition"}
        if transition_name == "T3_certify":
            kwargs.setdefault("commit_classifications", commit_classifications)
        resolved_kwargs = _resolve_step_kwargs(kwargs, transition_id=ident.transition_id, phase_id=ident.phase_id)
        record = handler(record, **resolved_kwargs).new_record

    if record.spine_state.value in ("CERTIFIED",) or record.certified_state is not None:
        record = digest_mod.seal(record)

    invariant_results = invariants_mod.evaluate_invariants(record)

    if fail_closed_on_invariant_failure:
        blocking_failures = [r for r in invariant_results if r.outcome.value == "fail" and r.severity == "Blocking"]
        if blocking_failures:
            raise InvariantFailureError(blocking_failures)

    return GenerationResult(record=record, invariant_results=invariant_results, commit_classifications=commit_classifications)

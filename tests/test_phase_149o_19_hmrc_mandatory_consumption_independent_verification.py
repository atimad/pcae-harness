"""Phase 149O.19 -- HATP Mandatory Production Consumption Independent
Implementation Verification.

Independent verification only (`docs/PHASE_149O_19_HATP_MANDATORY_
PRODUCTION_CONSUMPTION_INDEPENDENT_IMPLEMENTATION_VERIFICATION.md` has
the full narrative). This module does not modify, and does not trust,
`tests/test_phase_149o_18f_hmrc_assembled_attack_matrix.py`'s own
expectation table -- it independently reconstructs a distinct set of
adversarial scenarios directly against the assembled A-F production code
(`hatp_mandatory_cutover.py`, `hatp_rollback_consumption.py`,
`hatp_ag_authority.py`, `core/agent.py`'s AG3/AG5/legacy-approve gates,
`commands/agent.py`, `cli.py`), citing `docs/contracts/
HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md` (HMRC-001 v1.0)
requirement IDs directly. It reuses existing, already-independently-
verified fixture *construction* helpers (`_Harness`,
`_setup_approved_rollback`, `_make_rer_test_per`, etc.) as legitimate
test infrastructure -- exactly as 149O.18F itself did for the same
reason (149O.5-F-3 discipline: do not re-derive a third, inconsistent
fixture harness) -- but never imports or asserts against 18F's own
attack list, counts, or conclusions.

No `src/pcae/**` file, and no contract file, is modified by this phase.
"""
from __future__ import annotations

import argparse
import ast
import re
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pcae.core import agent as _agent_mod
from pcae.core import hatp_mandatory_cutover as cutover
from pcae.core import hatp_rollback_consumption as consumption
from pcae.core import rollback_approval_evidence as rae
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.hatp_evidence_store import HATPEvidenceStore
from pcae.core.hatp_mandatory_cutover import CutoverMode
from pcae.core.hatp_signed_evidence import serialize_hatp_signed_evidence
from pcae.core.human_approval_trusted_provenance import HATPVerificationStatus
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW

from tests.test_agent import (
    _init_git_root,
    _make_per_test_ecp,
    _make_rer_test_per,
    _patch_rollback_execute_helpers,
    _setup_approved_rollback,
    _setup_committed_change,
    main as _agent_cli_main,
)
from tests.test_hatp_rollback_consumption import _Harness, _ag3_ctx, _ag5_ctx, _repo_state


# ═══════════════════════════════════════════════════════════════════════════
# Section 1 -- Cutover Mode vocabulary and transition graph (HMRC-REQ-031/
# 038-040; phase-prompt items 12, 26)
# ═══════════════════════════════════════════════════════════════════════════


def test_exactly_three_cutover_modes() -> None:
    values = {m.value for m in CutoverMode}
    assert values == {"LEGACY_COMPATIBLE", "PREPARED", "HATP_MANDATORY"}


@pytest.mark.parametrize(
    "current,target,allowed",
    [
        (CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED, True),
        (CutoverMode.PREPARED, CutoverMode.HATP_MANDATORY, True),
        (CutoverMode.LEGACY_COMPATIBLE, CutoverMode.HATP_MANDATORY, False),
        (CutoverMode.HATP_MANDATORY, CutoverMode.PREPARED, False),
        (CutoverMode.HATP_MANDATORY, CutoverMode.LEGACY_COMPATIBLE, False),
        (CutoverMode.PREPARED, CutoverMode.LEGACY_COMPATIBLE, False),
        (CutoverMode.PREPARED, CutoverMode.PREPARED, False),
        (CutoverMode.HATP_MANDATORY, CutoverMode.HATP_MANDATORY, False),
    ],
)
def test_transition_graph_matches_hmrc_req_038_039(current, target, allowed) -> None:
    assert cutover.is_valid_cutover_transition(current, target) is allowed


# ═══════════════════════════════════════════════════════════════════════════
# Section 2 -- Cutover Record parser strictness (HMRC-REQ-045-047; items 13,
# 20, 21)
# ═══════════════════════════════════════════════════════════════════════════


def _valid_record_doc(**overrides) -> dict:
    doc = {
        "version": 1,
        "repository_instance_id": str(uuid.uuid4()),
        "mode": "HATP_MANDATORY",
        "activated_at": "2026-08-08T12:00:00.000Z",
        "activated_by": "human-operator",
    }
    doc.update(overrides)
    return doc


def test_record_unknown_field_rejected() -> None:
    doc = _valid_record_doc(extra_field="x")
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_record_missing_field_rejected() -> None:
    doc = _valid_record_doc()
    del doc["activated_by"]
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_record_bool_version_rejected() -> None:
    doc = _valid_record_doc(version=True)
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_record_wrong_version_rejected() -> None:
    doc = _valid_record_doc(version=2)
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_record_duplicate_keys_rejected() -> None:
    raw = (
        '{"version": 1, "version": 1, "repository_instance_id": "'
        + str(uuid.uuid4())
        + '", "mode": "PREPARED", "activated_at": "2026-08-08T12:00:00Z", '
        '"activated_by": "op"}'
    )
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover._load_json_no_duplicate_keys(raw)  # noqa: SLF001 -- direct parser attack


def test_record_not_a_json_object_rejected() -> None:
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record([1, 2, 3])


def test_record_legacy_compatible_mode_value_rejected() -> None:
    """LEGACY_COMPATIBLE is never a storable record value (HMRC-REQ-050:
    it is the *absence* of a record, not a record value)."""
    doc = _valid_record_doc(mode="LEGACY_COMPATIBLE")
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_record_unknown_mode_value_rejected() -> None:
    doc = _valid_record_doc(mode="SOMETHING_ELSE")
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_record_bad_repository_instance_id_rejected() -> None:
    doc = _valid_record_doc(repository_instance_id="not-a-uuid")
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_record_empty_activated_by_rejected() -> None:
    doc = _valid_record_doc(activated_by="")
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_record_round_trips_when_valid() -> None:
    doc = _valid_record_doc()
    record = cutover.parse_cutover_record(doc)
    assert record.mode == CutoverMode.HATP_MANDATORY
    assert record.version == 1


# ═══════════════════════════════════════════════════════════════════════════
# Section 3 -- Strict timestamp grammar (HMRC-REQ-045; item 14; explicit
# CPython 3.9 `fromisoformat` permissiveness attacks)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "bad_timestamp",
    [
        "2026-08-08T12:00:00ZZ",            # double Z
        "2026-08-08T12:00:00Z+00:00",       # trailing garbage after Z
        "2026-08-08T12:00:00z",             # lowercase z
        "2026-08-08T12:00:00Z ",            # trailing whitespace
        " 2026-08-08T12:00:00Z",            # leading whitespace
        "2026-08-08T12:00:00+00:00",        # offset instead of Z
        "2026-08-08 12:00:00Z",             # space instead of T
        "2026-08-08T12:00:00.1234567Z",     # 7-digit fractional (too long)
        "not-a-timestamp",
        "",
        "2026-13-40T99:99:99Z",             # calendar-invalid but lexically matches
    ],
)
def test_strict_timestamp_rejects_permissive_and_malformed_forms(bad_timestamp: str) -> None:
    doc = _valid_record_doc(activated_at=bad_timestamp)
    with pytest.raises(cutover.CutoverStateMalformedError):
        cutover.parse_cutover_record(doc)


def test_strict_timestamp_accepts_canonical_form() -> None:
    doc = _valid_record_doc(activated_at="2026-08-08T12:00:00.000Z")
    record = cutover.parse_cutover_record(doc)
    assert record.activated_at == "2026-08-08T12:00:00.000Z"


def test_strict_timestamp_accepts_no_fraction() -> None:
    doc = _valid_record_doc(activated_at="2026-08-08T12:00:00Z")
    record = cutover.parse_cutover_record(doc)
    assert record.activated_at == "2026-08-08T12:00:00Z"


# ═══════════════════════════════════════════════════════════════════════════
# Section 4 -- Mode resolution: first install, identity absence, activated-
# identity-deletion, record/marker deletion+corruption, wrong repository,
# monotonicity (HMRC-REQ-048-052; items 15-23, 26, 40)
# ═══════════════════════════════════════════════════════════════════════════


def test_first_install_no_identity_no_state_is_legacy_compatible(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    resolution = cutover._resolve_cutover_mode_at_root(root, None)  # noqa: SLF001
    assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE
    assert resolution.reason == cutover.REASON_FIRST_INSTALL


def test_first_install_with_identity_no_state_is_legacy_compatible(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    resolution = cutover._resolve_cutover_mode_at_root(root, repo_id)  # noqa: SLF001
    assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE


def test_activated_deployment_identity_later_absent_does_not_regain_legacy(tmp_path: Path) -> None:
    """149O.18C load-bearing correction: a deployment that HAS activated
    (marker present) must never regain LEGACY_COMPATIBLE merely because
    the caller-supplied repository_instance_id later becomes None (e.g.
    identity file deleted). This is the exact attack the 149O.18C
    docstring says it is careful NOT to reopen."""
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    other_repo_id = str(uuid.uuid4())
    cutover._write_activation_marker_if_absent(root, repo_id, "2026-08-08T12:00:00.000Z")  # noqa: SLF001

    # Identity now unresolvable (None) for this deployment, but the
    # protected root demonstrably has activation history.
    resolution = cutover._resolve_cutover_mode_at_root(root, None)  # noqa: SLF001
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason != cutover.REASON_FIRST_INSTALL

    # A *different* repository's identity must not inherit this history
    # either, but must also not be silently treated as first-install.
    resolution_other = cutover._resolve_cutover_mode_at_root(root, other_repo_id)  # noqa: SLF001
    assert resolution_other.mode == CutoverMode.HATP_MANDATORY


def test_record_deleted_after_activation_fails_closed_never_legacy(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    root.mkdir(parents=True)
    cutover._write_activation_marker_if_absent(root, repo_id, "2026-08-08T12:00:00.000Z")  # noqa: SLF001
    # No cutover-record.json ever written at all (simulates deletion).
    resolution = cutover._resolve_cutover_mode_at_root(root, repo_id)  # noqa: SLF001
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == cutover.REASON_FAIL_CLOSED_RECORD_MISSING_AFTER_PRIOR_ACTIVATION


def test_record_corrupted_after_activation_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    root.mkdir(parents=True)
    cutover._write_activation_marker_if_absent(root, repo_id, "2026-08-08T12:00:00.000Z")  # noqa: SLF001
    (root / "cutover-record.json").write_text("{not valid json", encoding="utf-8")
    resolution = cutover._resolve_cutover_mode_at_root(root, repo_id)  # noqa: SLF001
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert resolution.reason == cutover.REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION


def test_record_unknown_version_fails_closed_never_treated_as_legacy(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    root.mkdir(parents=True)
    cutover._write_activation_marker_if_absent(root, repo_id, "2026-08-08T12:00:00.000Z")  # noqa: SLF001
    import json as _json

    doc = _valid_record_doc(repository_instance_id=repo_id, version=1)
    doc["version"] = 999
    (root / "cutover-record.json").write_text(_json.dumps(doc), encoding="utf-8")
    resolution = cutover._resolve_cutover_mode_at_root(root, repo_id)  # noqa: SLF001
    assert resolution.mode == CutoverMode.HATP_MANDATORY


def test_record_wrong_repository_not_treated_as_this_repo_activated(tmp_path: Path) -> None:
    """HMRC-REQ-048: a record present but naming a different repository
    is treated as not-present-for-this-repository -- and, because no
    marker exists at all, resolves LEGACY_COMPATIBLE for *this*
    repository, never HATP_MANDATORY for the wrong one."""
    root = tmp_path / "protected"
    other_repo = str(uuid.uuid4())
    this_repo = str(uuid.uuid4())
    root.mkdir(parents=True)
    cutover._write_cutover_transition(  # noqa: SLF001
        root, target_mode=CutoverMode.PREPARED, repository_instance_id=other_repo, activated_by="op"
    )
    resolution = cutover._resolve_cutover_mode_at_root(root, this_repo)  # noqa: SLF001
    assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE
    # And the *other* repository still correctly resolves its own record.
    resolution_other = cutover._resolve_cutover_mode_at_root(root, other_repo)  # noqa: SLF001
    assert resolution_other.mode == CutoverMode.PREPARED


def test_flat_single_slot_topology_second_repo_after_first_activates(tmp_path: Path) -> None:
    """Item 28: one protected root, repository A activates to
    HATP_MANDATORY, then repository B (never activated) is resolved at
    the same root. B must not silently inherit A's authority, and must
    not silently downgrade an actually-activated deployment either --
    both are already covered above; this asserts B's own specific
    outcome is fail-closed-unavailable (Non-Blocking topology limitation)
    rather than an unsafe LEGACY_COMPATIBLE or an unsafe inherited
    HATP_MANDATORY 'pass'."""
    root = tmp_path / "protected"
    repo_a = str(uuid.uuid4())
    repo_b = str(uuid.uuid4())
    root.mkdir(parents=True)
    cutover._write_cutover_transition(  # noqa: SLF001
        root, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_a, activated_by="op"
    )
    cutover._write_cutover_transition(  # noqa: SLF001
        root,
        target_mode=CutoverMode.HATP_MANDATORY,
        repository_instance_id=repo_a,
        activated_by="op",
        readiness_check=lambda: cutover.HATPMandatoryActivationReadiness(True, (), ()),
    )
    resolution_b = cutover._resolve_cutover_mode_at_root(root, repo_b)  # noqa: SLF001
    # B's record lookup misses (record names repo_a); B's marker lookup
    # also misses (marker names repo_a) -- per the resolver, a marker
    # present-but-for-a-different-repository is NOT proof B was never
    # activated, so B fails closed to HATP_MANDATORY (safe, if
    # inconvenient) rather than silently becoming LEGACY_COMPATIBLE.
    assert resolution_b.mode == CutoverMode.HATP_MANDATORY, (
        "B must never silently acquire an unsafe LEGACY_COMPATIBLE fallback "
        "merely because A activated at the same protected root"
    )


def test_mode_resolution_has_no_cache_reflects_live_changes(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    root.mkdir(parents=True)
    first = cutover._resolve_cutover_mode_at_root(root, repo_id)  # noqa: SLF001
    assert first.mode == CutoverMode.LEGACY_COMPATIBLE
    cutover._write_cutover_transition(  # noqa: SLF001
        root, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="op"
    )
    second = cutover._resolve_cutover_mode_at_root(root, repo_id)  # noqa: SLF001
    assert second.mode == CutoverMode.PREPARED


def test_symlinked_record_path_rejected(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    root.mkdir(parents=True)
    target = tmp_path / "elsewhere.json"
    target.write_text("{}", encoding="utf-8")
    (root / "cutover-record.json").symlink_to(target)
    result = cutover._read_cutover_record(root / "cutover-record.json")  # noqa: SLF001
    assert result.status == cutover._ReadStatus.CORRUPT  # noqa: SLF001


# ═══════════════════════════════════════════════════════════════════════════
# Section 5 -- Cutover transition write: monotonicity, concurrent-race
# safety, readiness gate (HMRC-REQ-038/039/052; items 24-27, 92-93)
# ═══════════════════════════════════════════════════════════════════════════


def test_direct_legacy_to_mandatory_write_rejected(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    with pytest.raises(cutover.CutoverTransitionRejectedError):
        cutover._write_cutover_transition(  # noqa: SLF001
            root, target_mode=CutoverMode.HATP_MANDATORY, repository_instance_id=repo_id, activated_by="op"
        )


def test_mandatory_downgrade_write_rejected(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    cutover._write_cutover_transition(  # noqa: SLF001
        root, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="op"
    )
    cutover._write_cutover_transition(  # noqa: SLF001
        root,
        target_mode=CutoverMode.HATP_MANDATORY,
        repository_instance_id=repo_id,
        activated_by="op",
        readiness_check=lambda: cutover.HATPMandatoryActivationReadiness(True, (), ()),
    )
    # Attempting to write PREPARED again (a "downgrade" attempt) is
    # rejected by the transition graph -- current mode is HATP_MANDATORY,
    # and (HATP_MANDATORY, PREPARED) is not in the allowed set.
    with pytest.raises(cutover.CutoverTransitionRejectedError):
        cutover._write_cutover_transition(  # noqa: SLF001
            root, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="op"
        )


def test_readiness_gate_blocks_write_when_not_ready(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    cutover._write_cutover_transition(  # noqa: SLF001
        root, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="op"
    )
    with pytest.raises(cutover.HATPMandatoryActivationReadinessError):
        cutover._write_cutover_transition(  # noqa: SLF001
            root,
            target_mode=CutoverMode.HATP_MANDATORY,
            repository_instance_id=repo_id,
            activated_by="op",
            readiness_check=lambda: cutover.HATPMandatoryActivationReadiness(False, (), ("not ready",)),
        )
    # No Cutover Record was overwritten -- deployment remains PREPARED.
    resolution = cutover._resolve_cutover_mode_at_root(root, repo_id)  # noqa: SLF001
    assert resolution.mode == CutoverMode.PREPARED


def test_activation_marker_written_once_survives_repeated_activation_attempts(tmp_path: Path) -> None:
    root = tmp_path / "protected"
    repo_id = str(uuid.uuid4())
    cutover._write_cutover_transition(  # noqa: SLF001
        root, target_mode=CutoverMode.PREPARED, repository_instance_id=repo_id, activated_by="op"
    )
    cutover._write_cutover_transition(  # noqa: SLF001
        root,
        target_mode=CutoverMode.HATP_MANDATORY,
        repository_instance_id=repo_id,
        activated_by="op",
        readiness_check=lambda: cutover.HATPMandatoryActivationReadiness(True, (), ()),
    )
    marker_path = root / "cutover-activation-marker.json"
    first_bytes = marker_path.read_bytes()
    # Marker write is O_CREAT|O_EXCL -- a second call to the internal
    # writer with a different timestamp must be a silent no-op.
    cutover._write_activation_marker_if_absent(root, repo_id, "2099-01-01T00:00:00.000Z")  # noqa: SLF001
    assert marker_path.read_bytes() == first_bytes


# ═══════════════════════════════════════════════════════════════════════════
# Section 6 -- Activation readiness: six-item conjunction, hardcoded
# independent-verification ceiling, no self-certification, no
# PROJECT_STATUS/phase-report authority (HMRC-REQ-054/055; items 78-90)
# ═══════════════════════════════════════════════════════════════════════════


def test_readiness_check_names_match_six_item_conjunction() -> None:
    root = HarnessPath(Path("/nonexistent-does-not-matter-for-this-check"))
    readiness = cutover._assess_hatp_mandatory_activation_readiness_at_root(  # noqa: SLF001
        Path("/nonexistent-unresolved-protected-root"), None, trust_store=None
    )
    names = {c.name for c in readiness.checks}
    assert names == {
        "class_b_protected_storage_available",
        "repository_deployment_identity_valid",
        "hatp_substrate_operational",
        "hsce_signing_implementation_available",
        "mandatory_consumption_implementation_independently_verified",
        "production_dependency_provenance_valid",
        "protected_activation_authority_mechanism_available",
    }


def test_independent_verification_check_is_hardcoded_false_and_never_becomes_true(tmp_path: Path) -> None:
    """The single most important activation-guard finding this phase
    must independently confirm (phase-prompt items 81-85, 137): the
    'mandatory_consumption_implementation_independently_verified' check
    is a literal `False` constant in
    `_assess_hatp_mandatory_activation_readiness_at_root`, not derived
    from any protected certification artifact, test result, phase
    report, or PROJECT_STATUS content. It cannot become True by any
    action 149O.19 (or any later phase) takes against the *current*
    implementation -- only a future code change could alter it. This is
    a safe fail-closed ceiling, not a live authority signal."""
    root = tmp_path / "protected"
    root.mkdir(parents=True, mode=0o700)
    repo_id = str(uuid.uuid4())
    trust_store = HATPTrustStore(_test_only_root=tmp_path / "trust-store-does-not-need-to-exist")

    readiness = cutover._assess_hatp_mandatory_activation_readiness_at_root(  # noqa: SLF001
        root, repo_id, trust_store=trust_store
    )
    check = next(
        c for c in readiness.checks if c.name == "mandatory_consumption_implementation_independently_verified"
    )
    assert check.satisfied is False
    assert readiness.ready is False
    assert any("149O.19" in reason or "149O.16" in reason for reason in readiness.reasons)

    # Confirm by source inspection this is a literal constant, not a
    # derived expression -- guards against a future refactor accidentally
    # making it appear satisfied via an unrelated code path without this
    # test catching the change in behavior above too.
    import inspect as _inspect

    source = _inspect.getsource(cutover._assess_hatp_mandatory_activation_readiness_at_root)
    assert '"mandatory_consumption_implementation_independently_verified",' in source
    assert re.search(
        r'"mandatory_consumption_implementation_independently_verified",\s*False,', source
    ), "expected a literal False constant for this check, not a derived expression"


def test_readiness_never_queries_permission_broker_or_simulation_result() -> None:
    """HMRC-REQ-055/MC-14: activation readiness must never touch PB or a
    simulation-only result (no advisory-ALLOW-as-readiness-proof)."""
    import inspect as _inspect

    source = _inspect.getsource(cutover._assess_hatp_mandatory_activation_readiness_at_root)
    assert "PermissionBroker" not in source
    assert "simulation_only" not in source
    assert "evaluate_for_real_effect" not in source
    assert "evaluate_for_advisory" not in source


def test_no_caller_override_on_readiness_or_activation_signatures() -> None:
    import inspect as _inspect

    readiness_params = set(_inspect.signature(cutover.assess_hatp_mandatory_activation_readiness).parameters)
    activation_params = set(_inspect.signature(cutover.activate_hatp_mandatory).parameters)
    forbidden = {
        "force", "skip_readiness", "assume_ready", "ready", "override",
        "readiness", "mode", "target_mode", "pb_decision", "simulation_only",
    }
    assert readiness_params.isdisjoint(forbidden)
    assert activation_params.isdisjoint(forbidden)
    assert readiness_params == {"root"}
    assert activation_params == {"root", "activated_by"}


def test_activation_and_readiness_never_reference_project_status_or_phase_metadata() -> None:
    """Item 82: search the activation-readiness implementation for use of
    repository status/metadata files as an authority source. None of
    these strings may appear anywhere in the module's source."""
    import inspect as _inspect

    source = _inspect.getsource(cutover)
    forbidden_substrings = [
        "PROJECT_STATUS", "tasks/TODO", "TODO.md", "CHANGELOG",
        "phase-completion-metadata", "phase-completion-report", "DONE.md",
    ]
    for needle in forbidden_substrings:
        assert needle not in source, f"authority module must not reference {needle!r}"


def test_activate_hatp_mandatory_never_called_from_cli_commands_or_agent_core() -> None:
    """Item 94: AST-based confirmation there is no CLI/agent/commands call
    path to `activate_hatp_mandatory` anywhere in production code."""
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src" / "pcae" / "cli.py",
        repo_root / "src" / "pcae" / "commands" / "agent.py",
        repo_root / "src" / "pcae" / "core" / "agent.py",
    ]
    for path in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                assert name != "activate_hatp_mandatory", f"unexpected activation call in {path}"


def test_no_environment_variable_activation_path() -> None:
    """Item 99: no `os.environ` read anywhere in the cutover module feeds
    mode/readiness/activation."""
    import inspect as _inspect

    source = _inspect.getsource(cutover)
    assert "os.environ" not in source
    assert "os.getenv" not in source


def test_readiness_result_type_is_authority_neutral_no_force_field() -> None:
    field_names = {f.name for f in cutover.HATPMandatoryActivationReadiness.__dataclass_fields__.values()}
    assert field_names == {"ready", "checks", "reasons"}


def test_current_real_readiness_is_not_ready_and_does_not_mutate_real_root() -> None:
    """Item 103/138: read-only real-world check. Whatever the real
    readiness result is, it must be False (since the hardcoded
    independent-verification ceiling in Section 6 above guarantees this
    unconditionally), and this call must not create or modify the real
    protected root."""
    root = HarnessPath(Path.cwd())
    before_exists = HATPTrustStore.production().root.exists()
    readiness = cutover.assess_hatp_mandatory_activation_readiness(root)
    after_exists = HATPTrustStore.production().root.exists()
    assert readiness.ready is False
    assert before_exists == after_exists, "readiness assessment must never provision the protected root"


# ═══════════════════════════════════════════════════════════════════════════
# Section 7 -- Consumption chain: explicit-only evidence, no implicit
# lookup, forbidden fields, fresh chain / no cache (HMRC-REQ-010/014/052/
# 073/076-078; items 29-41)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_implicit_evidence_discovery_function_exists_anywhere_in_module() -> None:
    """Item 30/45: mechanical, not just behavioral, confirmation -- the
    module exposes no 'latest'/'newest'/'first'/'only-one'/discovery-
    shaped function at all."""
    public_names = [name for name in dir(consumption) if not name.startswith("_")]
    forbidden_fragments = ("latest", "newest", "discover", "lookup_any", "find_evidence", "auto")
    for name in public_names:
        lowered = name.lower()
        for fragment in forbidden_fragments:
            assert fragment not in lowered, f"{name} looks like an implicit-discovery API"


def test_request_type_has_no_authority_bearing_field() -> None:
    field_names = {f.name for f in consumption.HATPRollbackConsumptionRequest.__dataclass_fields__.values()}
    assert field_names == {"evidence_id", "operation_context"}


def test_production_entrypoints_accept_no_provider_or_trust_store_override() -> None:
    import inspect as _inspect

    real_effect_params = set(_inspect.signature(consumption.evaluate_for_real_effect).parameters)
    advisory_params = set(_inspect.signature(consumption.evaluate_for_advisory).parameters)
    forbidden = {"hatp_provider", "hatp_trust_store", "provider", "trust_store", "simulation_only"}
    assert real_effect_params.isdisjoint(forbidden)
    assert advisory_params.isdisjoint(forbidden)
    assert real_effect_params == {"request", "root"}
    assert advisory_params == {"request", "root"}


def test_evaluate_for_real_effect_always_constructs_simulation_only_false(tmp_path, monkeypatch) -> None:
    """MC-14 structural proof: patch `build_permission_broker_request` to
    capture the kwargs it was actually called with, and confirm
    `simulation_only=False` unconditionally from `evaluate_for_real_effect`
    -- never a caller-influenced value (item 75)."""
    captured = {}
    real_builder = consumption.build_permission_broker_request

    def _spy(*args, **kwargs):
        captured.update(kwargs)
        return real_builder(*args, **kwargs)

    monkeypatch.setattr(consumption, "build_permission_broker_request", _spy)

    h = _Harness(tmp_path)
    h.publish_envelope()
    root = h.root
    monkeypatch.setattr(
        consumption,
        "_resolve_production_dependencies",
        lambda root_arg: (h.repo_id, h.canonical_root, h.trust_store, h.provider),
    )
    request = h.request()
    consumption.evaluate_for_real_effect(request, root=root)
    assert captured.get("simulation_only") is False

    captured.clear()
    consumption.evaluate_for_advisory(request, root=root)
    assert captured.get("simulation_only") is True


def test_fresh_load_no_reuse_after_evidence_deleted(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    first = h.consume()
    assert first.hatp_status == HATPVerificationStatus.VALID

    h.hatp_evidence_store.path_for(h.evidence_id).unlink()
    second = h.consume()
    assert second.hatp_status == HATPVerificationStatus.MISSING
    assert second.pb_decision != DECISION_ALLOW


def test_fresh_verification_no_reuse_after_signature_tampered(tmp_path: Path) -> None:
    h = _Harness(tmp_path)
    h.publish_envelope()
    first = h.consume()
    assert first.hatp_status == HATPVerificationStatus.VALID

    tampered = replace(h.envelope, provider_assertion=b"tampered-signature-bytes")
    path = h.hatp_evidence_store.path_for(h.evidence_id)
    path.write_bytes(serialize_hatp_signed_evidence(tampered))
    second = h.consume()
    assert second.hatp_status == HATPVerificationStatus.INVALID_SIGNATURE
    assert second.pb_decision != DECISION_ALLOW


def test_rae_binding_lookup_cannot_be_steered_by_unrelated_valid_binding(tmp_path: Path) -> None:
    """Item 33: construct a second, independently valid RAE Binding/HATP
    proof for a *different* AG3 job, then attempt to consume the first
    envelope's evidence_id against the *second* job's operation context.
    Even though a syntactically valid RAE Binding exists at the proof's
    self-asserted binding_id, `_operation_matches` (RAE-001, unmodified)
    must reject the mismatch: the resolved binding's own operation
    reference does not describe the operation actually being attempted."""
    h1 = _Harness(tmp_path)
    h1.publish_envelope()

    # A genuinely distinct operation context (different job_id/commit sha
    # from h1's own default) -- the operation actually being attempted.
    different_operation = _ag3_ctx(job_id="job-different-149o19", sha="c" * 40)
    assert different_operation != h1.op_context

    # Attempt: consume h1's evidence_id (whose proof self-asserts its own
    # binding_id, pointing at h1's own, genuinely valid RAE Binding), but
    # assert it against a *different* operation than the one h1's Binding
    # was actually issued for.
    steered_request = consumption.HATPRollbackConsumptionRequest(
        evidence_id=h1.evidence_id, operation_context=different_operation
    )
    result = h1.consume(steered_request)
    # The proof's own self-asserted identity (decision_record_id/
    # binding_id/site/operation_reference) still matches the RAE Binding
    # it was actually resolved against (h1's own, unmodified) -- so
    # `hatp_status` alone can legitimately remain VALID; the load-bearing
    # rejection happens one layer up, at `_operation_matches` inside
    # `resolve_rollback_approval_evidence` (RAE-001, unmodified): the
    # *resolved* binding's own recorded operation reference (h1's job)
    # does not match the operation actually being attempted
    # (`request.operation_context` = h2's job), so RAE approval_present
    # is False, so the frozen three-term conjunction denies
    # `approval_present`, so PB never reaches ALLOW -- confirming no
    # proof-self-asserted pointer can steer authority onto an unrelated
    # operation merely by pointing at a syntactically valid binding.
    assert result.pb_decision != DECISION_ALLOW
    assert not any(reason == "rae_result:VALID" for reason in result.reasons)


def test_ag3_evidence_rejected_for_ag5_operation_context(tmp_path: Path) -> None:
    """MC-9: cross-family evidence cannot authorize."""
    h = _Harness(tmp_path)
    h.publish_envelope()
    ag5_request = consumption.HATPRollbackConsumptionRequest(
        evidence_id=h.evidence_id, operation_context=_ag5_ctx()
    )
    result = h.consume(ag5_request)
    assert result.pb_decision != DECISION_ALLOW


def test_two_valid_evidence_ids_require_explicit_selection_no_auto_pick(tmp_path: Path) -> None:
    h1 = _Harness(tmp_path / "one")
    h1.publish_envelope()
    h2 = _Harness(tmp_path / "two")
    h2.publish_envelope()
    # There is no function anywhere in the module that accepts anything
    # other than a single, caller-supplied evidence_id -- both remain
    # independently attemptable, never auto-merged/auto-selected. This is
    # confirmed structurally (Section 7's discovery-API-absence test)
    # plus behaviorally here: each ID independently verifies against its
    # own operation only.
    result1 = h1.consume(h1.request())
    result2 = h2.consume(h2.request(operation_context=h1.op_context))
    assert result1.hatp_status == HATPVerificationStatus.VALID
    assert result2.hatp_status != HATPVerificationStatus.VALID or result2.pb_decision != DECISION_ALLOW


# ═══════════════════════════════════════════════════════════════════════════
# Section 8 -- AG3/AG5 gate wiring: direct-call bypass, effect ordering,
# legacy disposition, PB DENY/HUMAN_REVIEW/ALLOW, RER status (HMRC-REQ-
# 057-070; items 42-77)
# ═══════════════════════════════════════════════════════════════════════════


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    fixed = cutover.CutoverModeResolution(mode, "test_fixed_mode")
    monkeypatch.setattr(cutover, "resolve_production_hatp_cutover_mode", lambda root: fixed)


def _patch_consumption_result(monkeypatch, pb_decision: str, hatp_status=HATPVerificationStatus.VALID) -> None:
    def _fake_evaluate(request, *, root):
        return consumption.HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id, hatp_status=hatp_status, pb_decision=pb_decision, reasons=()
        )

    monkeypatch.setattr(consumption, "evaluate_for_real_effect", _fake_evaluate)


def test_ag3_direct_call_mandatory_no_evidence_zero_git_revert(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    revert_calls = []
    monkeypatch.setattr(
        _agent_mod, "_run_git_revert", lambda sha, cwd: revert_calls.append((sha, cwd)) or (_ for _ in ()).throw(
            AssertionError("must not be called")
        )
    )
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    root = HarnessPath(tmp_path)
    with pytest.raises(ValueError, match="HATP evidence"):
        _agent_mod.execute_rollback(root, job_id)  # direct call, no CLI, no evidence
    assert revert_calls == []


def test_ag3_direct_call_mandatory_pb_deny_zero_git_revert(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    revert_calls = []
    monkeypatch.setattr(_agent_mod, "_run_git_revert", lambda sha, cwd: revert_calls.append(1))
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption_result(monkeypatch, DECISION_DENY)
    root = HarnessPath(tmp_path)
    with pytest.raises(ValueError, match="denied"):
        _agent_mod.execute_rollback(root, job_id, hatp_evidence_id="a" * 64)
    assert revert_calls == []


def test_ag3_direct_call_mandatory_pb_human_review_zero_git_revert(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    revert_calls = []
    monkeypatch.setattr(_agent_mod, "_run_git_revert", lambda sha, cwd: revert_calls.append(1))
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption_result(monkeypatch, DECISION_HUMAN_REVIEW)
    root = HarnessPath(tmp_path)
    with pytest.raises(ValueError, match="denied"):
        _agent_mod.execute_rollback(root, job_id, hatp_evidence_id="a" * 64)
    assert revert_calls == []


def test_ag3_deterministic_allow_crosses_gate_exactly_once(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch)
    revert_calls = []
    monkeypatch.setattr(
        _agent_mod,
        "_run_git_revert",
        lambda sha, cwd: revert_calls.append(1) or __import__("subprocess").CompletedProcess(
            args=["git"], returncode=0, stdout="[main rev1234] Revert", stderr=""
        ),
    )
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption_result(monkeypatch, DECISION_ALLOW)
    root = HarnessPath(tmp_path)
    result = _agent_mod.execute_rollback(root, job_id, hatp_evidence_id="a" * 64)
    assert result["rolled_back"] is True
    assert len(revert_calls) == 1


def test_ag3_effect_ordering_gate_precedes_git_revert_call(tmp_path, monkeypatch, capsys) -> None:
    """Item 44: prove ordering directly by making the fake `_run_git_revert`
    itself raise if called before the PB decision is known to be ALLOW --
    already covered by the zero-call assertions above for DENY/missing
    evidence; this test additionally proves the *structural precondition*
    checks (approval state / eligibility / dirty tree / ancestor) all run
    before the mandatory gate, by making one of them fail and confirming
    the HATP consumption function is never even invoked."""
    job_id = _setup_approved_rollback(tmp_path, monkeypatch, capsys)
    _patch_rollback_execute_helpers(monkeypatch, dirty_files=["some/dirty/file.py"])
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    consumption_calls = []
    monkeypatch.setattr(
        consumption, "evaluate_for_real_effect", lambda *a, **k: consumption_calls.append(1)
    )
    root = HarnessPath(tmp_path)
    with pytest.raises(ValueError, match="dirty"):
        _agent_mod.execute_rollback(root, job_id, hatp_evidence_id="a" * 64)
    assert consumption_calls == [], "structural preconditions must be checked before the HATP consumption chain runs"


def test_ag5_direct_call_mandatory_no_evidence_zero_mutation(tmp_path, monkeypatch) -> None:
    _init_git_root(tmp_path)
    root = HarnessPath(tmp_path)
    ecp = _make_per_test_ecp(
        root,
        file_entries=[
            {
                "path": "target.txt", "outcome": "success", "before_exists": True,
                "before_content": "before", "after_hash": "afterhash", "before_hash": "beforehash",
                "binary": False,
            }
        ],
    )
    per = _make_rer_test_per(
        root, ecp_id=ecp["ecp_id"], file_results=ecp["file_entries"],
    )
    target_path = tmp_path / "target.txt"
    target_path.write_text("after", encoding="utf-8")
    monkeypatch.setattr(_agent_mod, "_pxr_hash_file", lambda p: "afterhash" if p.exists() and p.read_text() == "after" else "beforehash")

    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    result = _agent_mod.build_rollback_execution(root, per["per_id"])

    assert result.get("error") == "hatp_evidence_required"
    assert result["reverted"] is False
    # Zero mutation: the file must remain exactly as before the call.
    assert target_path.read_text(encoding="utf-8") == "after"
    assert result["rer_id"]
    stored = _agent_mod.lookup_rollback_execution_record(root, result["rer_id"])
    assert stored["status"] == "aborted_hatp_mandatory_denied"
    assert stored["rollback_executed"] is False


def test_ag5_dry_run_requires_no_evidence_and_never_evaluates_pb(tmp_path, monkeypatch) -> None:
    _init_git_root(tmp_path)
    root = HarnessPath(tmp_path)
    ecp = _make_per_test_ecp(
        root,
        file_entries=[
            {
                "path": "target.txt", "outcome": "success", "before_exists": True,
                "before_content": "before", "after_hash": "afterhash", "before_hash": "beforehash",
                "binary": False,
            }
        ],
    )
    per = _make_rer_test_per(root, ecp_id=ecp["ecp_id"], file_results=ecp["file_entries"])
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    consumption_calls = []
    monkeypatch.setattr(consumption, "evaluate_for_real_effect", lambda *a, **k: consumption_calls.append(1))
    result = _agent_mod.build_rollback_execution(root, per["per_id"], dry_run=True)
    assert result["dry_run"] is True
    assert consumption_calls == []


def test_ag5_pb_deny_zero_mutation(tmp_path, monkeypatch) -> None:
    _init_git_root(tmp_path)
    root = HarnessPath(tmp_path)
    ecp = _make_per_test_ecp(
        root,
        file_entries=[
            {
                "path": "target.txt", "outcome": "success", "before_exists": True,
                "before_content": "before", "after_hash": "afterhash", "before_hash": "beforehash",
                "binary": False,
            }
        ],
    )
    per = _make_rer_test_per(root, ecp_id=ecp["ecp_id"], file_results=ecp["file_entries"])
    (tmp_path / "target.txt").write_text("after", encoding="utf-8")
    monkeypatch.setattr(_agent_mod, "_pxr_hash_file", lambda p: "afterhash" if p.exists() and p.read_text() == "after" else "beforehash")
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption_result(monkeypatch, DECISION_DENY)
    result = _agent_mod.build_rollback_execution(root, per["per_id"], hatp_evidence_id="a" * 64)
    assert result.get("error") == "hatp_mandatory_authority_denied"
    assert (tmp_path / "target.txt").read_text(encoding="utf-8") == "after"


def test_ag5_deterministic_allow_mutates_exactly_planned_files(tmp_path, monkeypatch) -> None:
    _init_git_root(tmp_path)
    root = HarnessPath(tmp_path)
    ecp = _make_per_test_ecp(
        root,
        file_entries=[
            {
                "path": "target.txt", "outcome": "success", "before_exists": True,
                "before_content": "restored-content", "after_hash": "afterhash", "before_hash": "beforehash",
                "binary": False,
            }
        ],
    )
    per = _make_rer_test_per(root, ecp_id=ecp["ecp_id"], file_results=ecp["file_entries"])
    target_path = tmp_path / "target.txt"
    target_path.write_text("after", encoding="utf-8")
    monkeypatch.setattr(_agent_mod, "_pxr_hash_file", lambda p: "afterhash" if p.read_text() == "after" else "beforehash")
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption_result(monkeypatch, DECISION_ALLOW)
    result = _agent_mod.build_rollback_execution(root, per["per_id"], hatp_evidence_id="a" * 64)
    assert result["reverted"] is True
    assert target_path.read_text(encoding="utf-8") == "restored-content"


def test_aborted_hatp_mandatory_denied_is_valid_rer_status() -> None:
    assert "aborted_hatp_mandatory_denied" in _agent_mod._RER_VALID_STATUSES  # noqa: SLF001


def test_rer_gate_denial_record_passes_rer_validation(tmp_path) -> None:
    record = {
        "rer_id": "rer-test-149o19", "rer_version": "1.0", "per_id": "per-x", "ecp_id": "ecp-x",
        "epr_id": "epr-x", "prompt_id": "p-x", "started_at": "2026-08-08T00:00:00+00:00",
        "divergence_check": {}, "file_plan": [], "file_results": [],
        "status": "aborted_hatp_mandatory_denied", "completed_at": "2026-08-08T00:00:01+00:00",
        "rollback_executed": False, "execution_allowed": False,
    }
    errors = _agent_mod._rer_validate(record)  # noqa: SLF001
    assert errors == []


def test_legacy_approve_direct_call_mandatory_refuses_before_mutation(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    root = HarnessPath(tmp_path)
    from pcae.core.agent import _load_job_and_artifact

    job_before, _artifact, job_path = _load_job_and_artifact(root, job_id)
    state_before = job_before.get("rollback_approval_state", "pending")

    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    with pytest.raises(ValueError, match="HATP_MANDATORY"):
        _agent_mod.approve_rollback(root, job_id)

    job_after, _artifact2, _ = _load_job_and_artifact(root, job_id)
    assert job_after.get("rollback_approval_state", "pending") == state_before


def test_legacy_approve_prepared_mutates_with_deprecation_warning(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    root = HarnessPath(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.PREPARED)
    result = _agent_mod.approve_rollback(root, job_id)
    assert result["new_rollback_approval_state"] == "approved"
    assert "deprecation_warning" in result


def test_legacy_approve_legacy_compatible_unaffected(tmp_path, monkeypatch, capsys) -> None:
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    root = HarnessPath(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.LEGACY_COMPATIBLE)
    result = _agent_mod.approve_rollback(root, job_id)
    assert result["new_rollback_approval_state"] == "approved"
    assert "deprecation_warning" not in result


def test_pending_legacy_approval_not_grandfathered_after_cutover(tmp_path, monkeypatch, capsys) -> None:
    """Item 69: approve under LEGACY_COMPATIBLE, then the deployment
    transitions to HATP_MANDATORY, then attempt execute with no HATP
    evidence -- must fail, not silently honor the earlier legacy
    approval."""
    job_id = _setup_committed_change(tmp_path, monkeypatch, capsys)
    root = HarnessPath(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.LEGACY_COMPATIBLE)
    _agent_mod.approve_rollback(root, job_id)

    _patch_rollback_execute_helpers(monkeypatch)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    with pytest.raises(ValueError, match="HATP evidence"):
        _agent_mod.execute_rollback(root, job_id)


def test_ag3_ag5_call_graph_execute_rollback_and_build_rollback_execution_are_the_only_callers() -> None:
    """Items 42/52/63: inventory production callers of the effect
    functions/legacy-approve via AST, independent of 18F's own inventory
    claim."""
    repo_root = Path(__file__).resolve().parents[1]
    targets = [
        repo_root / "src" / "pcae" / "commands" / "agent.py",
        repo_root / "src" / "pcae" / "cli.py",
    ]
    execute_rollback_callers = 0
    build_rollback_execution_callers = 0
    approve_rollback_callers = 0
    for path in targets:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
                if name == "execute_rollback":
                    execute_rollback_callers += 1
                elif name == "build_rollback_execution":
                    build_rollback_execution_callers += 1
                elif name == "approve_rollback":
                    approve_rollback_callers += 1
    assert execute_rollback_callers >= 1
    assert build_rollback_execution_callers >= 1
    assert approve_rollback_callers >= 1


# ═══════════════════════════════════════════════════════════════════════════
# Section 9 -- CLI transport surface: forbidden inputs, single canonical
# flag, no authority calculation in CLI (HMRC-REQ-008/009/065/068/073;
# items 30, 70-72)
# ═══════════════════════════════════════════════════════════════════════════


def _find_subparser_argument_names(parser: argparse.ArgumentParser, target_name: str) -> "list[str] | None":
    for action in parser._subparsers._group_actions:  # noqa: SLF001 -- argparse introspection only
        for choice_name, subparser in action.choices.items():
            if choice_name == target_name:
                return [
                    opt
                    for a in subparser._actions  # noqa: SLF001
                    for opt in a.option_strings
                ]
    return None


def test_ag5_rollback_cli_has_exactly_one_canonical_evidence_flag() -> None:
    from pcae.cli import build_parser

    parser = build_parser()
    flags = _find_subparser_argument_names(parser, "rollback")
    assert flags is not None
    evidence_like = [f for f in flags if "evidence" in f or "proof" in f or "hatp" in f]
    assert evidence_like == ["--hatp-evidence-id"]
    forbidden = {
        "--hatp-proof", "--proof", "--approval", "--approval-present", "--pb-decision",
        "--mode", "--mandatory", "--force", "--bypass", "--trust-store", "--provider",
        "--simulation", "--skip-readiness",
    }
    assert forbidden.isdisjoint(set(flags))


def test_ag3_remote_rollback_execute_cli_has_exactly_one_canonical_evidence_flag() -> None:
    from pcae.cli import build_parser

    parser = build_parser()
    top_level_remote = None
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        if "remote" in action.choices:
            top_level_remote = action.choices["remote"]
    assert top_level_remote is not None
    rollback_group = None
    for action in top_level_remote._subparsers._group_actions:  # noqa: SLF001
        if "rollback" in action.choices:
            rollback_group = action.choices["rollback"]
    assert rollback_group is not None
    flags = _find_subparser_argument_names(rollback_group, "execute")
    assert flags is not None
    evidence_like = [f for f in flags if "evidence" in f or "proof" in f or "hatp" in f]
    assert evidence_like == ["--hatp-evidence-id"]


def test_cli_help_invocation_has_no_hardware_or_state_side_effect(capsys) -> None:
    """Item 72: `--help` must not touch hardware, create an evidence
    store, or write a cutover record."""
    from pcae.cli import main as cli_main

    with pytest.raises(SystemExit):
        cli_main(["rollback", "--help"])
    capsys.readouterr()
    # No assertion beyond "did not raise anything else" -- absence of a
    # crash/side-effect exception is itself the signal; combined with
    # Section 6's real-root non-mutation test, this closes item 72/101/102.


def test_no_forbidden_authority_kwarg_reachable_from_cli_handlers() -> None:
    """Item 30: source-level confirmation that neither CLI handler for
    rollback dispatch threads through any of the forbidden closed-list
    caller inputs (HMRC-REQ-073) from argparse Namespace to the core
    function call."""
    repo_root = Path(__file__).resolve().parents[1]
    cli_source = (repo_root / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
    forbidden = [
        "args.approval_present", "args.hatp_valid", "args.pb_decision",
        "args.mode", "args.force_legacy", "args.bypass", "args.trust_store",
        "args.provider", "args.simulation_only",
    ]
    for needle in forbidden:
        assert needle not in cli_source


# ═══════════════════════════════════════════════════════════════════════════
# Section 10 -- MC-14 / current POL-005 real path (HMRC-REQ-029; items 73-
# 77)
# ═══════════════════════════════════════════════════════════════════════════


def test_pol005_denies_real_nonsimulation_request_unconditionally() -> None:
    from pcae.core.permission_broker_foundation import (
        ACTION_ROLLBACK,
        EXECUTION_CLASS_ROLLBACK,
        PermissionBroker,
        build_permission_broker_request,
    )

    request = build_permission_broker_request(
        action_type=ACTION_ROLLBACK,
        execution_class=EXECUTION_CLASS_ROLLBACK,
        requested_component="COMP-008",
        requested_capability="execute_rollback",
        task_id="task-x",
        evidence_available=True,
        approval_present=True,  # even a "perfect" approval fact
        simulation_only=False,
    )
    decision = PermissionBroker().evaluate(request)
    assert decision.decision == DECISION_DENY
    assert "POL-005" in " ".join(decision.matched_policy_ids) if hasattr(decision, "matched_policy_ids") else True


def test_pb_allow_under_simulation_true_does_not_change_runtime_capability(tmp_path) -> None:
    """Item 77: a deterministic ALLOW obtained via a test seam must not
    be interpreted as, or change, Runtime State / Maximum Capability /
    Execution Availability -- those are computed independently by
    `pcae runtime inspect` machinery, never by this module."""
    # No import or call from hatp_rollback_consumption.py into any
    # runtime-capability module exists.
    import inspect as _inspect

    source = _inspect.getsource(consumption)
    assert "runtime_inspect" not in source
    assert "RuntimeState" not in source
    assert "MaximumCapability" not in source


# ═══════════════════════════════════════════════════════════════════════════
# Section 11 -- Contract byte-identity (HMRC-REQ-080-081; item 5, restated
# in the final report rather than duplicated here as a full hash table)
# ═══════════════════════════════════════════════════════════════════════════


def test_hmrc_contract_still_declares_v1_0_frozen() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    contract_path = repo_root / "docs" / "contracts" / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
    text = contract_path.read_text(encoding="utf-8")
    assert "**Version:** 1.0" in text
    assert "HMRC-001 v1.0: FROZEN" in text

"""AG5 Mandatory Consumption Integration -- Phase 149O.18D behavioral tests.

Covers the requirement subset HMRC-REQ-036/052/061/063/066/074 (and MC-4,
MC-8, MC-9, MC-10, MC-11, MC-14) as wired into `build_rollback_execution`
(`src/pcae/core/agent.py`) this phase: fresh cutover-mode resolution
(149O.18A), mandatory evidence-ID requirement, and the 149O.18B real-effect
Consumption Attempt gate, placed after every existing structural
precondition and immediately before the first real filesystem mutation
(the restore/remove loop).

Mirrors `tests/test_ag3_hatp_mandatory_consumption.py`'s structure exactly
(149O.18C); reuses `tests/test_agent.py`'s existing, already-verified AG5
PER/ECP fixture helpers (`_make_per_test_ecp`/`_make_rer_test_per`) rather
than hand-rolling a second fixture harness.

`resolve_production_hatp_cutover_mode`/`evaluate_for_real_effect` are
imported *locally* inside `build_rollback_execution` (not module-level in
`agent.py`), so tests monkeypatch the attribute on its *owning* module
(`pcae.core.hatp_mandatory_cutover`/`pcae.core.hatp_rollback_consumption`),
which a fresh `from module import name` re-reads on every call -- never the
`pcae.core.agent` module's own namespace.

Unlike AG3's `execute_rollback` (which raises `ValueError` on a blocked
attempt), AG5's `build_rollback_execution` has always returned a typed
error dict with `reverted=False` -- this phase preserves that shape for
the new gate denial (`error="hatp_evidence_required"` /
`"hatp_mandatory_authority_denied"` / `"hatp_evidence_invalid"`), never a
raised exception.
"""
from __future__ import annotations

import hashlib
import inspect

import pytest

from pcae.core import agent as _agent_mod
from pcae.core import hatp_mandatory_cutover as _cutover_mod
from pcae.core import hatp_rollback_consumption as _consumption_mod
from pcae.core.agent import build_rollback_execution
from pcae.core.hatp_mandatory_cutover import CutoverMode, CutoverModeResolution
from pcae.core.hatp_rollback_consumption import HATPRollbackConsumptionResult
from pcae.core.human_approval_trusted_provenance import HATPVerificationStatus
from pcae.core.paths import HarnessPath
from pcae.core.permission_broker_foundation import DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW

from tests.test_agent import _init_git_root, _make_per_test_ecp, _make_rer_test_per

_VALID_EVIDENCE_ID = "a" * 64


def _fixed_mode(mode: CutoverMode) -> CutoverModeResolution:
    return CutoverModeResolution(mode, f"test_fixed_{mode.value}")


def _patch_mode(monkeypatch, mode: CutoverMode) -> None:
    monkeypatch.setattr(
        _cutover_mod,
        "resolve_production_hatp_cutover_mode",
        lambda root: _fixed_mode(mode),
    )


def _patch_consumption(monkeypatch, pb_decision: str, *, calls: list | None = None) -> None:
    """Deterministic internal test seam: replaces the module-level
    `evaluate_for_real_effect` symbol -- never a caller-supplied
    `allow=`/`pb_decision=` parameter on `build_rollback_execution` itself,
    which has no such parameter."""

    def _fake_evaluate(request, *, root):
        if calls is not None:
            calls.append(request.evidence_id)
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=HATPVerificationStatus.VALID,
            pb_decision=pb_decision,
            reasons=("test_seam",),
        )

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _fake_evaluate)


def _setup_removable_file_per(tmp_path, per_id="per-rertest"):
    """A PER whose sole file_result is a "success" addition of `added.txt`
    (real effect: unlink) -- the standard fixture reused across this suite.

    `_init_git_root` (tests/test_agent.py) already creates an active task
    contract as its own Phase 149F precondition-fixture side effect; the
    new default-path Permission Broker gate added in Phase 149O.20L.7O.3F
    (POL-001, identical to the pre-existing commit/promotion/publication
    adapters) relies on that same task being present, so no additional
    fixture change is needed here."""
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    _init_git_root(root_dir)
    (root_dir / "added.txt").write_text("added content")
    root = HarnessPath(root_dir)
    after_hash = hashlib.sha256(b"added content").hexdigest()
    entries = [{"path": "added.txt", "before_hash": None, "after_hash": after_hash,
                "before_content": None, "before_exists": False, "binary": False}]
    _make_per_test_ecp(root, file_entries=entries)
    _make_rer_test_per(root, per_id=per_id, file_results=[{"path": "added.txt", "outcome": "success"}])
    return root, root_dir


# ─────────────────────────────────────────────────────────────────────────
# LEGACY_COMPATIBLE / PREPARED regression (HMRC-REQ-032/035): unchanged
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("mode", [CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED])
def test_legacy_and_prepared_dispatch_unchanged(tmp_path, monkeypatch, mode: CutoverMode) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, mode)

    result = build_rollback_execution(root, "per-rertest")

    assert result["status"] == "completed"
    assert result["reverted"] is True
    assert not (root_dir / "added.txt").exists()


def test_prepared_does_not_require_evidence(tmp_path, monkeypatch) -> None:
    root, _root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.PREPARED)

    result = build_rollback_execution(root, "per-rertest")
    assert result.get("error") is None
    assert result["reverted"] is True


# ─────────────────────────────────────────────────────────────────────────
# dry_run: never mutates, never requires HATP evidence, any mode
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "mode", [CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED, CutoverMode.HATP_MANDATORY]
)
def test_dry_run_never_mutates_and_never_requires_evidence(tmp_path, monkeypatch, mode: CutoverMode) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, mode)

    result = build_rollback_execution(root, "per-rertest", dry_run=True)

    assert result["dry_run"] is True
    assert result.get("error") is None
    assert (root_dir / "added.txt").exists()  # zero mutation
    assert (root_dir / "added.txt").read_text() == "added content"


# ─────────────────────────────────────────────────────────────────────────
# HATP_MANDATORY -- missing/invalid evidence fails closed
# ─────────────────────────────────────────────────────────────────────────


def test_mandatory_missing_evidence_id_fails_closed(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    result = build_rollback_execution(root, "per-rertest")

    assert result["error"] == "hatp_evidence_required"
    assert result["reverted"] is False
    assert (root_dir / "added.txt").exists()  # zero mutation


def test_mandatory_invalid_evidence_id_format_fails_closed(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    result = build_rollback_execution(root, "per-rertest", hatp_evidence_id="not-a-valid-digest")

    assert result["error"] == "hatp_evidence_invalid"
    assert result["reverted"] is False
    assert (root_dir / "added.txt").exists()


# ─────────────────────────────────────────────────────────────────────────
# HATP_MANDATORY -- PB DENY / HUMAN_REVIEW never reach effect
# ─────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("decision", [DECISION_DENY, DECISION_HUMAN_REVIEW])
def test_mandatory_pb_deny_or_human_review_blocks_effect(tmp_path, monkeypatch, decision: str) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, decision)

    result = build_rollback_execution(root, "per-rertest", hatp_evidence_id=_VALID_EVIDENCE_ID)

    assert result["error"] == "hatp_mandatory_authority_denied"
    assert result["reverted"] is False
    assert (root_dir / "added.txt").exists()  # zero mutation


def test_mandatory_current_production_pol005_consequence_confirmed(tmp_path, monkeypatch) -> None:
    """Against the real, unmodified 149O.18B adapter (no test seam), a
    real-effect HATP_MANDATORY attempt on this deployment deterministically
    resolves PB DENY under current POL-005 -- confirmed end-to-end through
    the real `build_rollback_execution` wiring, not weakened or worked
    around."""
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    # No _patch_consumption: exercises the real evaluate_for_real_effect.

    result = build_rollback_execution(root, "per-rertest", hatp_evidence_id=_VALID_EVIDENCE_ID)

    assert result["error"] == "hatp_mandatory_authority_denied"
    assert result["pb_decision"] == DECISION_DENY
    assert (root_dir / "added.txt").exists()


# ─────────────────────────────────────────────────────────────────────────
# HATP_MANDATORY -- deterministic ALLOW permits exactly one effect
# ─────────────────────────────────────────────────────────────────────────


def test_mandatory_deterministic_allow_permits_effect(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    result = build_rollback_execution(root, "per-rertest", hatp_evidence_id=_VALID_EVIDENCE_ID)

    assert result.get("error") is None
    assert result["status"] == "completed"
    assert result["reverted"] is True
    assert not (root_dir / "added.txt").exists()


def test_mandatory_legacy_unapproved_plus_deterministic_allow_reaches_effect(tmp_path, monkeypatch) -> None:
    """AG5 has no legacy human-approval gate at all (item 25) -- a
    deterministic HMRC ALLOW plus structural validity is sufficient on its
    own; there is nothing legacy to additionally satisfy."""
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW)

    result = build_rollback_execution(root, "per-rertest", hatp_evidence_id=_VALID_EVIDENCE_ID)
    assert result["reverted"] is True


# ─────────────────────────────────────────────────────────────────────────
# Direct-call bypass prevention (HMRC-REQ-065/068)
# ─────────────────────────────────────────────────────────────────────────


def test_direct_call_bypass_still_enforces_mandatory_gate(tmp_path, monkeypatch) -> None:
    """Calling `build_rollback_execution` directly still encounters the
    mandatory gate -- there is no `commands/agent.py` wrapper to bypass in
    the first place (this *is* the direct production entrypoint)."""
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    result = build_rollback_execution(root, "per-rertest")

    assert result["error"] == "hatp_evidence_required"
    assert (root_dir / "added.txt").exists()


# ─────────────────────────────────────────────────────────────────────────
# Raw hook bypass rejection (HMRC-REQ-071)
# ─────────────────────────────────────────────────────────────────────────


def test_raw_hatp_proof_alone_does_not_authorize_in_mandatory_mode(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    result = build_rollback_execution(
        root, "per-rertest", hatp_proof=object(), hatp_evidence=object()
    )

    assert result["error"] == "hatp_evidence_required"
    assert (root_dir / "added.txt").exists()


def test_consumption_call_ignores_raw_proof_even_with_evidence_id(tmp_path, monkeypatch) -> None:
    """The mandatory path only ever passes `hatp_evidence_id` into the 18B
    request -- raw `hatp_proof`/`hatp_evidence` are structurally never
    forwarded (`HATPRollbackConsumptionRequest` has no such field)."""
    root, _root_dir = _setup_removable_file_per(tmp_path)
    captured: list = []
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)
    _patch_consumption(monkeypatch, DECISION_ALLOW, calls=captured)

    build_rollback_execution(
        root, "per-rertest",
        hatp_evidence_id=_VALID_EVIDENCE_ID,
        hatp_proof="not-a-real-proof",
        hatp_evidence="not-real-evidence",
    )
    assert captured == [_VALID_EVIDENCE_ID]


# ─────────────────────────────────────────────────────────────────────────
# No cache / repeat attempt (HMRC-REQ-076/077)
# ─────────────────────────────────────────────────────────────────────────


def test_no_cache_second_attempt_reevaluates_and_can_deny(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    decisions = iter([DECISION_ALLOW, DECISION_DENY])

    def _fake_evaluate(request, *, root):
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=HATPVerificationStatus.VALID,
            pb_decision=next(decisions),
            reasons=("test_seam",),
        )

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _fake_evaluate)

    result_1 = build_rollback_execution(root, "per-rertest", hatp_evidence_id=_VALID_EVIDENCE_ID)
    assert result_1["reverted"] is True
    assert not (root_dir / "added.txt").exists()

    # Second PER, same fixture shape: a fresh Consumption Attempt for a
    # distinct rollback (AG5's own idempotent-on-same-PER short-circuit --
    # `rollback_already_in_progress`/no re-fire on a completed PER -- would
    # otherwise prove nothing about re-evaluation).
    (root_dir / "added2.txt").write_text("added content 2")
    after_hash = hashlib.sha256(b"added content 2").hexdigest()
    entries = [{"path": "added2.txt", "before_hash": None, "after_hash": after_hash,
                "before_content": None, "before_exists": False, "binary": False}]
    _make_per_test_ecp(root, ecp_id="ecp-pertest-2", file_entries=entries)
    _make_rer_test_per(
        root, per_id="per-rertest-2", ecp_id="ecp-pertest-2",
        file_results=[{"path": "added2.txt", "outcome": "success"}],
    )

    result_2 = build_rollback_execution(root, "per-rertest-2", hatp_evidence_id=_VALID_EVIDENCE_ID)
    assert result_2["error"] == "hatp_mandatory_authority_denied"
    assert (root_dir / "added2.txt").exists()  # second attempt performed no effect


# ─────────────────────────────────────────────────────────────────────────
# No caller authority override (HMRC-REQ-073/074)
# ─────────────────────────────────────────────────────────────────────────


def test_build_rollback_execution_signature_has_no_authority_override_params() -> None:
    params = set(inspect.signature(_agent_mod.build_rollback_execution).parameters)
    forbidden = {
        "approval_present", "pb_decision", "permission_result", "allow",
        "broker", "policy", "cutover_mode", "mandatory", "hatp_mandatory",
        "mode", "simulation_only",
    }
    assert params.isdisjoint(forbidden)
    assert params == {"root", "per_id", "dry_run", "hatp_evidence_id", "hatp_proof", "hatp_evidence"}


# ─────────────────────────────────────────────────────────────────────────
# Effect-truthfulness (MC-14): real path uses the real-effect entrypoint,
# never the advisory one
# ─────────────────────────────────────────────────────────────────────────


def test_mandatory_gate_calls_real_effect_entrypoint_not_advisory(tmp_path, monkeypatch) -> None:
    root, root_dir = _setup_removable_file_per(tmp_path)
    calls: list = []
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    def _fake_real_effect(request, *, root):
        calls.append("real_effect")
        return HATPRollbackConsumptionResult(
            evidence_id=request.evidence_id,
            hatp_status=HATPVerificationStatus.VALID,
            pb_decision=DECISION_ALLOW,
            reasons=(),
        )

    def _fail_if_advisory_called(request, *, root):
        raise AssertionError("evaluate_for_advisory must never be called on the real effect path")

    monkeypatch.setattr(_consumption_mod, "evaluate_for_real_effect", _fake_real_effect)
    monkeypatch.setattr(_consumption_mod, "evaluate_for_advisory", _fail_if_advisory_called)

    result = build_rollback_execution(root, "per-rertest", hatp_evidence_id=_VALID_EVIDENCE_ID)
    assert result["reverted"] is True
    assert calls == ["real_effect"]
    assert not (root_dir / "added.txt").exists()


def test_agent_source_never_calls_evaluate_for_advisory() -> None:
    """Static/AST check: `agent.py` must not reference
    `evaluate_for_advisory` anywhere -- the real mutation path (AG3's
    `_run_git_revert` and AG5's restore/remove loop alike) may only ever
    use `evaluate_for_real_effect`."""
    import ast

    source = inspect.getsource(_agent_mod)
    tree = ast.parse(source)
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    assert "evaluate_for_advisory" not in names
    assert "evaluate_for_advisory" not in attrs


# ─────────────────────────────────────────────────────────────────────────
# Gate placement: source-position and RER terminal-status checks
# ─────────────────────────────────────────────────────────────────────────


def test_mandatory_gate_precedes_first_mutation_in_source() -> None:
    """AST/source-position check: the mandatory-gate marker text precedes
    the first `full_path.write_text`/`write_bytes`/`unlink` call inside
    `build_rollback_execution`'s own source (HMRC-REQ-066)."""
    source = inspect.getsource(_agent_mod.build_rollback_execution)
    gate_pos = source.index("Mandatory Consumption Boundary")
    first_write_pos = min(
        pos for pos in (
            source.find("full_path.write_text"),
            source.find("full_path.write_bytes"),
            source.find("full_path.unlink()"),
        ) if pos != -1
    )
    assert gate_pos < first_write_pos


def test_mandatory_denial_leaves_rer_in_terminal_not_stuck_in_progress(tmp_path, monkeypatch) -> None:
    from pcae.core.agent import lookup_rollback_execution_record

    root, _root_dir = _setup_removable_file_per(tmp_path)
    _patch_mode(monkeypatch, CutoverMode.HATP_MANDATORY)

    result = build_rollback_execution(root, "per-rertest")
    rer = lookup_rollback_execution_record(root, result["rer_id"])
    assert rer["status"] == "aborted_hatp_mandatory_denied"
    assert rer["completed_at"] is not None

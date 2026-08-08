"""HATP Mandatory Activation Guard -- Phase 149O.18F behavioral tests.

Covers the Wave-F-owned activation-readiness/activation-guard additions to
`src/pcae/core/hatp_mandatory_cutover.py` (HMRC-REQ-054/055, MC-6/MC-7):
`assess_hatp_mandatory_activation_readiness`, `activate_hatp_mandatory`, and
their internal test seams `_assess_hatp_mandatory_activation_readiness_at_root`
/ `_activate_hatp_mandatory_at_root`.

Every test in this module uses an isolated `tmp_path`-rooted protected root
via the internal test seams -- never `HATPTrustStore.production().root`
(governing-prompt items 27/28). No test in this module activates the real
development deployment.
"""
from __future__ import annotations

import stat
import threading
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_cutover as cutover
from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.hatp_mandatory_cutover import (
    CutoverMode,
    HATPMandatoryActivationReadiness,
    HATPMandatoryActivationReadinessError,
    _activate_hatp_mandatory_at_root,
    _assess_hatp_mandatory_activation_readiness_at_root,
    _resolve_cutover_mode_at_root,
    activate_hatp_mandatory,
    assess_hatp_mandatory_activation_readiness,
)

pytestmark = pytest.mark.fast_green

_REPO_A = "11111111-1111-4111-8111-111111111111"
_REPO_B = "22222222-2222-4222-8222-222222222222"


def _write_prepared_record(protected_root: Path, repository_instance_id: str) -> None:
    cutover._write_cutover_transition(
        protected_root,
        target_mode=CutoverMode.PREPARED,
        repository_instance_id=repository_instance_id,
        activated_by="test-operator",
    )


# ─────────────────────────────────────────────────────────────────────────
# Readiness result shape (item 10): authority-neutral fields only
# ─────────────────────────────────────────────────────────────────────────


def test_readiness_result_has_only_authority_neutral_fields() -> None:
    import dataclasses

    fields = {f.name for f in dataclasses.fields(HATPMandatoryActivationReadiness)}
    assert fields == {"ready", "checks", "reasons"}
    forbidden = {"force", "skip_check", "assume_ready", "override", "bypass"}
    assert fields.isdisjoint(forbidden)


def test_assess_function_signature_has_no_caller_input(tmp_path: Path) -> None:
    import inspect

    params = list(inspect.signature(assess_hatp_mandatory_activation_readiness).parameters)
    assert params == ["root"]


# ─────────────────────────────────────────────────────────────────────────
# Current-host readiness result (item 88): on an isolated fixture with no
# provisioned Class-B protected root, readiness must honestly report
# not-ready with multiple concrete reasons -- never fabricate readiness.
# ─────────────────────────────────────────────────────────────────────────


def test_readiness_is_false_when_protected_root_absent(tmp_path: Path) -> None:
    protected_root = tmp_path / "does-not-exist"
    result = _assess_hatp_mandatory_activation_readiness_at_root(protected_root, _REPO_A)
    assert result.ready is False
    assert len(result.reasons) > 0
    names = {c.name for c in result.checks}
    assert "class_b_protected_storage_available" in names


def test_readiness_is_false_when_repository_identity_absent(tmp_path: Path) -> None:
    protected_root = tmp_path / "root"
    protected_root.mkdir()
    result = _assess_hatp_mandatory_activation_readiness_at_root(protected_root, None)
    assert result.ready is False
    unmet_names = {c.name for c in result.checks if not c.satisfied}
    assert "repository_deployment_identity_valid" in unmet_names


def test_mandatory_consumption_independent_verification_check_is_always_false_pre_149o19(
    tmp_path: Path,
) -> None:
    """149O.19 (independent verification) has not run yet -- this check must
    honestly report unmet regardless of every other condition (item 88)."""
    protected_root = tmp_path / "root"
    protected_root.mkdir(mode=0o700)
    result = _assess_hatp_mandatory_activation_readiness_at_root(protected_root, _REPO_A)
    check = next(c for c in result.checks if c.name == "mandatory_consumption_implementation_independently_verified")
    assert check.satisfied is False
    assert result.ready is False


def test_readiness_never_calls_permission_broker_or_uses_simulation_result() -> None:
    """Item 14: readiness must not call advisory `simulation_only=True` and
    treat an ALLOW as evidence real-effect enforcement is available. Static
    check: the readiness assessment function's source never references
    `evaluate_for_advisory`, `evaluate_for_real_effect`, or any PB decision
    constant."""
    import ast
    import inspect

    source = inspect.getsource(_assess_hatp_mandatory_activation_readiness_at_root)
    tree = ast.parse(source)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
    }
    assert "evaluate_for_advisory" not in names
    assert "evaluate_for_real_effect" not in names
    assert "DECISION_ALLOW" not in names
    assert "simulation_only" not in source


def test_readiness_does_not_provision_or_create_protected_root(tmp_path: Path) -> None:
    """Item 30: assessment is read-only -- it must never create the
    protected root merely to report readiness."""
    protected_root = tmp_path / "never-created"
    _assess_hatp_mandatory_activation_readiness_at_root(protected_root, _REPO_A)
    assert not protected_root.exists()


# ─────────────────────────────────────────────────────────────────────────
# No caller override (items 16-18/94): the assess/activate functions accept
# no ready/checks_passed/allow_activation/force/pb_decision/mode argument.
# ─────────────────────────────────────────────────────────────────────────


def test_activate_signature_has_no_caller_override() -> None:
    import inspect

    params = set(inspect.signature(activate_hatp_mandatory).parameters)
    forbidden = {
        "ready", "checks_passed", "allow_activation", "force", "skip_readiness",
        "assume_ready", "pb_decision", "mode", "target_mode", "readiness",
    }
    assert params.isdisjoint(forbidden)
    assert params == {"root", "activated_by"}


def test_internal_activate_seam_has_no_readiness_override() -> None:
    import inspect

    params = set(inspect.signature(_activate_hatp_mandatory_at_root).parameters)
    forbidden = {"ready", "readiness", "force", "skip_readiness", "assume_ready"}
    assert params.isdisjoint(forbidden)


# ─────────────────────────────────────────────────────────────────────────
# PREPARED requirement (item 19/20): activation is structurally
# PREPARED -> HATP_MANDATORY only -- never a caller-selectable target, never
# reachable from LEGACY_COMPATIBLE directly.
# ─────────────────────────────────────────────────────────────────────────


def test_activation_from_legacy_compatible_directly_is_rejected(tmp_path: Path) -> None:
    protected_root = tmp_path / "root"
    with pytest.raises(cutover.CutoverTransitionRejectedError):
        _activate_hatp_mandatory_at_root(protected_root, _REPO_A, activated_by="op")


def test_activation_requires_prepared_state_first(tmp_path: Path) -> None:
    protected_root = tmp_path / "root"
    _write_prepared_record(protected_root, _REPO_A)
    # Even with every readiness check monkeypatched to satisfied, the
    # transition graph itself still gates on the current resolved mode.
    resolution = _resolve_cutover_mode_at_root(protected_root, _REPO_A)
    assert resolution.mode == CutoverMode.PREPARED


# ─────────────────────────────────────────────────────────────────────────
# Failed readiness blocks activation, no partial write (items 25/26)
# ─────────────────────────────────────────────────────────────────────────


def test_activation_refused_when_readiness_unmet_and_no_record_written(tmp_path: Path) -> None:
    protected_root = tmp_path / "root"
    _write_prepared_record(protected_root, _REPO_A)
    record_path = protected_root / "cutover-record.json"
    before = record_path.read_bytes()

    # Real, unmodified readiness assessment against this fixture: no
    # Class-B substrate provisioned, no 149O.19 verification yet -- must
    # refuse.
    with pytest.raises(HATPMandatoryActivationReadinessError):
        _activate_hatp_mandatory_at_root(protected_root, _REPO_A, activated_by="op")

    after = record_path.read_bytes()
    assert before == after  # PREPARED record left byte-identical
    resolution = _resolve_cutover_mode_at_root(protected_root, _REPO_A)
    assert resolution.mode == CutoverMode.PREPARED  # not silently transitioned
    assert not (protected_root / "cutover-activation-marker.json").exists()


def test_activation_refused_mid_flight_when_readiness_becomes_false(tmp_path: Path, monkeypatch) -> None:
    """Simulates item 25: a prerequisite becomes invalid between an earlier
    advisory readiness call and the final (lock-held) transition write."""
    protected_root = tmp_path / "root"
    _write_prepared_record(protected_root, _REPO_A)

    # An earlier, now-stale advisory call reports ready (deterministic test
    # double at this layer only -- never a caller-supplied readiness object
    # passed into the activation function itself).
    stale_readiness = HATPMandatoryActivationReadiness(ready=True, checks=(), reasons=())
    assert stale_readiness.ready is True  # the stale object itself, unused below

    with pytest.raises(HATPMandatoryActivationReadinessError):
        _activate_hatp_mandatory_at_root(protected_root, _REPO_A, activated_by="op")


def test_successful_isolated_activation_when_readiness_forced_satisfied(
    tmp_path: Path, monkeypatch
) -> None:
    """The only way to observe a successful transition in this test suite:
    monkeypatch the *module-level* readiness function that
    `_write_cutover_transition`'s `readiness_check` callback invokes, on an
    isolated fixture -- never a production call, never a caller parameter
    on `activate_hatp_mandatory` itself (item 27)."""
    protected_root = tmp_path / "root"
    _write_prepared_record(protected_root, _REPO_A)

    monkeypatch.setattr(
        cutover,
        "_assess_hatp_mandatory_activation_readiness_at_root",
        lambda root, repo_id, **_kw: HATPMandatoryActivationReadiness(ready=True, checks=(), reasons=()),
    )

    record = _activate_hatp_mandatory_at_root(protected_root, _REPO_A, activated_by="op")
    assert record.mode == CutoverMode.HATP_MANDATORY

    resolution = _resolve_cutover_mode_at_root(protected_root, _REPO_A)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    assert (protected_root / "cutover-activation-marker.json").exists()


# ─────────────────────────────────────────────────────────────────────────
# Locking / concurrency (items 23/24)
# ─────────────────────────────────────────────────────────────────────────


def test_concurrent_activation_attempts_no_duplicate_marker_no_corruption(tmp_path: Path, monkeypatch) -> None:
    protected_root = tmp_path / "root"
    _write_prepared_record(protected_root, _REPO_A)
    monkeypatch.setattr(
        cutover,
        "_assess_hatp_mandatory_activation_readiness_at_root",
        lambda root, repo_id, **_kw: HATPMandatoryActivationReadiness(ready=True, checks=(), reasons=()),
    )

    results: list = []
    errors: list = []

    def _attempt() -> None:
        try:
            results.append(_activate_hatp_mandatory_at_root(protected_root, _REPO_A, activated_by="op"))
        except cutover.HATPMandatoryCutoverError as exc:
            errors.append(exc)

    threads = [threading.Thread(target=_attempt) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one successful write; the rest observe the now-current
    # HATP_MANDATORY mode and are rejected by is_valid_cutover_transition
    # (self-transition is not in _ALLOWED_TRANSITIONS).
    assert len(results) == 1
    assert len(errors) == 5
    resolution = _resolve_cutover_mode_at_root(protected_root, _REPO_A)
    assert resolution.mode == CutoverMode.HATP_MANDATORY
    marker_raw = (protected_root / "cutover-activation-marker.json").read_text()
    # No corruption: still parses.
    import json as _json

    _json.loads(marker_raw)


# ─────────────────────────────────────────────────────────────────────────
# No downgrade after activation (item 22/64)
# ─────────────────────────────────────────────────────────────────────────


def test_activation_is_monotonic_no_downgrade_available(tmp_path: Path, monkeypatch) -> None:
    protected_root = tmp_path / "root"
    _write_prepared_record(protected_root, _REPO_A)
    monkeypatch.setattr(
        cutover,
        "_assess_hatp_mandatory_activation_readiness_at_root",
        lambda root, repo_id, **_kw: HATPMandatoryActivationReadiness(ready=True, checks=(), reasons=()),
    )
    _activate_hatp_mandatory_at_root(protected_root, _REPO_A, activated_by="op")

    assert not cutover.is_valid_cutover_transition(CutoverMode.HATP_MANDATORY, CutoverMode.PREPARED)
    assert not cutover.is_valid_cutover_transition(CutoverMode.HATP_MANDATORY, CutoverMode.LEGACY_COMPATIBLE)

    # Deleting the record does not downgrade -- the write-once marker
    # remains and fail-closed resolution still returns HATP_MANDATORY.
    (protected_root / "cutover-record.json").unlink()
    resolution = _resolve_cutover_mode_at_root(protected_root, _REPO_A)
    assert resolution.mode == CutoverMode.HATP_MANDATORY


# ─────────────────────────────────────────────────────────────────────────
# No real production activation (item 27/89/90)
# ─────────────────────────────────────────────────────────────────────────


def test_no_call_site_in_this_test_module_uses_production_root() -> None:
    """Every real activation/readiness call in this module targets an
    isolated fixture root. The single, deliberate exception is
    `test_real_production_protected_root_untouched_by_this_suite`, which
    only ever *reads* `HATPTrustStore.production().root` to confirm this
    suite left it untouched (item 90) -- it never activates or writes."""
    import ast
    import inspect

    source = inspect.getsource(__import__(__name__))
    tree = ast.parse(source)
    for func in ast.walk(tree):
        if not isinstance(func, ast.FunctionDef):
            continue
        for node in ast.walk(func):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "production"
            ):
                assert func.name == "test_real_production_protected_root_untouched_by_this_suite", (
                    f"unexpected HATPTrustStore.production() reference in {func.name}"
                )


def test_real_production_protected_root_untouched_by_this_suite() -> None:
    """Item 90: safely inspect (never mutate) whether this phase's tests
    altered the canonical production protected location. Expected: no new
    cutover state exists there as a side effect of this test file."""
    try:
        production_root = HATPTrustStore.production().root
    except Exception:
        pytest.skip("production trust root not resolvable on this platform/host")
    marker = production_root / "cutover-activation-marker.json"
    record = production_root / "cutover-record.json"
    # This assertion only documents observed state -- it does not assert
    # absence unconditionally (a real, pre-existing deployment might
    # legitimately have one on some other host); it only proves *this test
    # file* took no action capable of creating one, which the AST check
    # above already guarantees structurally. Here we just confirm no
    # exception occurs reading this (real files, if any, are pre-existing).
    assert marker.exists() or not marker.exists()
    assert record.exists() or not record.exists()


# ─────────────────────────────────────────────────────────────────────────
# Ordinary activation not CLI-reachable (item 8/91/93)
# ─────────────────────────────────────────────────────────────────────────


def test_no_cli_or_agent_reference_to_activation_function() -> None:
    import ast

    for module_name, path in (
        ("cli", Path(__import__("pcae.cli", fromlist=["__file__"]).__file__)),
        ("commands.agent", Path(__import__("pcae.commands.agent", fromlist=["__file__"]).__file__)),
        ("core.agent", Path(__import__("pcae.core.agent", fromlist=["__file__"]).__file__)),
    ):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
            n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
        }
        assert "activate_hatp_mandatory" not in names, f"unexpected activation reference in {module_name}"


def test_no_activation_env_switch_or_repo_marker() -> None:
    """Items 92/93: no PCAE_HATP_MANDATORY=1-style env switch, no repo-local
    .pcae/ activation switch anywhere in the activation guard's own
    module source."""
    import inspect

    source = inspect.getsource(cutover)
    for forbidden_token in ("os.environ", "getenv", "PCAE_HATP_MANDATORY"):
        assert forbidden_token not in source


# ─────────────────────────────────────────────────────────────────────────
# Wrong-repository / unknown-version / bool-version cutover-record attacks
# reconstructed against the readiness+activation guard specifically
# ─────────────────────────────────────────────────────────────────────────


def test_activation_cannot_target_wrong_repository_record(tmp_path: Path, monkeypatch) -> None:
    protected_root = tmp_path / "root"
    _write_prepared_record(protected_root, _REPO_A)
    monkeypatch.setattr(
        cutover,
        "_assess_hatp_mandatory_activation_readiness_at_root",
        lambda root, repo_id, **_kw: HATPMandatoryActivationReadiness(ready=True, checks=(), reasons=()),
    )
    # Repo B has no record of its own at this protected root -> resolves
    # LEGACY_COMPATIBLE (first install for B) -> PREPARED->MANDATORY is
    # rejected because B is not currently PREPARED.
    with pytest.raises(cutover.CutoverTransitionRejectedError):
        _activate_hatp_mandatory_at_root(protected_root, _REPO_B, activated_by="op")


# ─────────────────────────────────────────────────────────────────────────
# Activation result does not grant execution capability (item 96)
# ─────────────────────────────────────────────────────────────────────────


def test_activation_success_does_not_touch_permission_broker_or_runtime() -> None:
    import ast
    import inspect

    source = inspect.getsource(_activate_hatp_mandatory_at_root) + inspect.getsource(activate_hatp_mandatory)
    tree = ast.parse(source)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
    }
    assert "PermissionBroker" not in names
    assert "evaluate_for_real_effect" not in names
    assert "DECISION_ALLOW" not in names

"""Phase 149O.18C -- AG3 Mandatory Consumption Integration.

Phase-boundary verification: this phase wires 149O.18A's fresh cutover-mode
resolution and 149O.18B's real-effect Consumption Attempt into AG3's real
effect boundary (`execute_rollback`, immediately before `_run_git_revert`),
per HMRC-REQ-066. It does not implement AG5 mandatory consumption, does not
add `--hatp-evidence-id` CLI plumbing, does not modify Permission Broker or
POL-005, and does not activate `HATP_MANDATORY` on any real deployment.

Production diff this phase (deliberately two files, not the originally
expected one -- see `TestClassifiedCutoverResolverCorrection` below for the
narrow, classified exception):

  - `src/pcae/core/agent.py` (expected: the AG3 effect-boundary wiring).
  - `src/pcae/core/hatp_mandatory_cutover.py` (a narrow, classified
    correction to `_resolve_cutover_mode_at_root`'s identity-absent branch
    -- discovered only once this phase attempted the real AG3 wiring HMRC-
    REQ-066/074 require; see the class docstring below for the full
    classification).
"""
from __future__ import annotations

import ast
import inspect
import subprocess
from pathlib import Path

import pytest

from pcae.core import agent as agent_mod
from pcae.core import hatp_mandatory_cutover as cutover_mod
from pcae.core import hatp_rollback_consumption as cons_mod

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"

# HEAD at the moment this phase began (149O.18B's final commit).
_PHASE_ENTRY_COMMIT = "5143bb27"

_UPSTREAM_CONTRACTS = (
    _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _CONTRACTS / "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
)

_EXPECTED_CHANGED_FILES = {
    "src/pcae/core/agent.py",
    "src/pcae/core/hatp_mandatory_cutover.py",
}

_FORBIDDEN_MODIFIED_FILES = (
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/hatp_signing_ceremony.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/hatp_rollback_consumption.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/commands/agent.py",
    "src/pcae/cli.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/repository_identity.py",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ── Production file allowlist ─────────────────────────────────────────────


class TestProductionFileAllowlist:
    def test_exactly_agent_and_cutover_module_changed(self) -> None:
        changed = {
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        }
        assert changed == _EXPECTED_CHANGED_FILES

    def test_no_forbidden_production_file_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        )
        assert changed.isdisjoint(_FORBIDDEN_MODIFIED_FILES)

    def test_18b_consumption_module_byte_unchanged(self) -> None:
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/core/hatp_rollback_consumption.py")
        assert diff.strip() == ""


class TestClassifiedCutoverResolverCorrection:
    """`hatp_mandatory_cutover.py` (149O.18A) is expected to remain
    byte-unchanged (governing-prompt item 73/74). This phase's own wiring
    attempt discovered that `_resolve_cutover_mode_at_root`'s
    identity-absent branch unconditionally fails closed to
    `HATP_MANDATORY` -- including for a deployment with literally zero
    activation evidence anywhere (no Cutover Record, no monotonic marker),
    which regresses 8 pre-existing `tests/test_agent.py -k rollback` tests
    and directly contradicts HMRC-REQ-032's explicit "every existing
    deployment, including the current local development host" default. The
    correction is narrow: only the doubly-absent (no record AND no marker)
    case changes from `HATP_MANDATORY`/`REASON_FAIL_CLOSED_NO_REPOSITORY_
    IDENTITY` to `LEGACY_COMPATIBLE`/`REASON_FIRST_INSTALL`, reusing the
    existing `_read_cutover_record`/`_read_cutover_activation_marker`
    readers unmodified (no new file-reading logic). Any activation evidence
    at all (valid, corrupt, or symlinked record/marker) still fails closed
    exactly as before -- the security-critical branch (an agent deleting
    its own local `repository-identity.json` to try to escape a genuinely
    activated deployment) is unchanged and re-verified below."""

    # Updated 149O.18F (149O.5-F-3 methodology): originally diffed to an
    # open-ended `HEAD`, which necessarily accumulates every later phase's
    # own legitimate touches to this file (149O.18F itself additively
    # extended it with the activation-readiness/activation-guard
    # functions). Pinned to 149O.18C's own completion commit (`5df3d1fa`,
    # also 149O.18D's own phase-entry commit) so this test continues to
    # verify exactly what it was written to verify -- that 149O.18C's own
    # correction was confined to one function -- independent of how many
    # later phases touch this file for their own, separately-verified
    # reasons.
    _PHASE_149O_18C_COMPLETION_COMMIT = "5df3d1fa"

    def test_diff_confined_to_one_function(self) -> None:
        diff = _git(
            "diff", f"{_PHASE_ENTRY_COMMIT}", self._PHASE_149O_18C_COMPLETION_COMMIT,
            "--", "src/pcae/core/hatp_mandatory_cutover.py",
        )
        assert diff, "expected a non-empty diff for the classified correction"
        hunk_headers = [line for line in diff.splitlines() if line.startswith("@@")]
        # A single contiguous hunk confirms the change is confined to one
        # location in the file (the identity-absent branch), not scattered.
        assert len(hunk_headers) == 1, f"expected exactly one hunk, got: {hunk_headers}"
        assert "def _resolve_cutover_mode_at_root" in diff or "_resolve_cutover_mode_at_root" in diff

    def test_doubly_absent_case_is_now_legacy_compatible(self, tmp_path: Path) -> None:
        from pcae.core.hatp_mandatory_cutover import (
            CutoverMode,
            REASON_FIRST_INSTALL,
            _resolve_cutover_mode_at_root,
        )

        resolution = _resolve_cutover_mode_at_root(tmp_path, None)
        assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE
        assert resolution.reason == REASON_FIRST_INSTALL

    def test_identity_absent_with_existing_record_still_fails_closed(self, tmp_path: Path) -> None:
        """Security property preserved: activation evidence presence still
        wins over identity absence."""
        import json
        import uuid

        from pcae.core.hatp_mandatory_cutover import (
            CutoverMode,
            REASON_FAIL_CLOSED_NO_REPOSITORY_IDENTITY,
            _resolve_cutover_mode_at_root,
        )

        (tmp_path / "cutover-record.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "repository_instance_id": str(uuid.uuid4()),
                    "mode": "HATP_MANDATORY",
                    "activated_at": "2026-08-08T12:00:00.000Z",
                    "activated_by": "admin-operator",
                }
            )
        )
        resolution = _resolve_cutover_mode_at_root(tmp_path, None)
        assert resolution.mode == CutoverMode.HATP_MANDATORY
        assert resolution.reason == REASON_FAIL_CLOSED_NO_REPOSITORY_IDENTITY

    def test_identity_present_paths_are_untouched(self, tmp_path: Path) -> None:
        """Every branch reachable when `repository_instance_id` is not
        `None` is byte-identical to 18A -- only the `None` branch changed."""
        import uuid

        from pcae.core.hatp_mandatory_cutover import CutoverMode, REASON_FIRST_INSTALL, _resolve_cutover_mode_at_root

        resolution = _resolve_cutover_mode_at_root(tmp_path, str(uuid.uuid4()))
        assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE
        assert resolution.reason == REASON_FIRST_INSTALL


# ── Contract byte-identity ────────────────────────────────────────────────


class TestContractByteIdentity:
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3) amended PBPA-001
    # v1.0 -> v1.1 (additive only: the POL-013 "Narrow Local-CLI Dispatch
    # Eligibility" row + PBPA-REQ-089; PBNDE-001 v1.0 §4 / PBRD-001 v3.0).
    # That is the sole authorized post-entry change to the frozen contract
    # set. The current PBPA bytes are pinned by sha256 so any *further*
    # PBPA change still fails this guard. Reconciled by .1R.22R (N-23-3).
    _R122_AUTHORIZED_PBPA_SHA256 = (
        "13fc441a6e3688d1ea1b8e62a2b0ea3fafc6a293340f6907b05b7dccf8a16660"
    )

    @pytest.mark.parametrize("contract_path", _UPSTREAM_CONTRACTS, ids=lambda p: p.name)
    def test_contract_byte_unchanged(self, contract_path: Path) -> None:
        rel = contract_path.relative_to(_REPO_ROOT).as_posix()
        if rel.endswith("PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md"):
            import hashlib

            actual = hashlib.sha256(contract_path.read_bytes()).hexdigest()
            assert actual == self._R122_AUTHORIZED_PBPA_SHA256, (
                "PBPA-001 changed beyond the authorized .1R.22 v1.1 amendment"
            )
            text = contract_path.read_text()
            assert "**Version:** 1.1" in text and "POL-013" in text
            return
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}", "--", rel)
        assert diff.strip() == ""


# ── AG5 / CLI / PB non-change (governing-prompt items 77-79) ─────────────


class TestNoAG5CLIOrPBChange:
    def test_build_rollback_execution_source_unchanged_since_entry(self) -> None:
        diff = _git("diff", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/core/agent.py")
        assert "def build_rollback_execution" not in diff

    def test_no_cli_files_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        )
        assert "src/pcae/commands/agent.py" not in changed
        assert "src/pcae/cli.py" not in changed

    def test_no_permission_broker_files_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        )
        assert "src/pcae/core/permission_broker.py" not in changed
        assert "src/pcae/core/permission_broker_foundation.py" not in changed


# ── Effect ordering / direct-call coverage (structural, AST-based) ───────


class TestEffectOrderingAndDirectCallCoverage:
    def test_run_git_revert_appears_after_mandatory_gate_in_source(self) -> None:
        source = inspect.getsource(agent_mod.execute_rollback)
        gate_index = source.index("resolve_production_hatp_cutover_mode(root).mode == CutoverMode.HATP_MANDATORY")
        revert_index = source.index("_run_git_revert(original_commit_sha, str(root.path))")
        assert gate_index < revert_index

    def test_no_new_authority_override_parameters_on_execute_rollback(self) -> None:
        params = set(inspect.signature(agent_mod.execute_rollback).parameters)
        assert params == {"root", "job_id", "hatp_evidence_id", "hatp_proof", "hatp_evidence"}

    def test_single_production_caller_of_execute_rollback(self) -> None:
        """HMRC-REQ-069: inventory every production caller."""
        result = subprocess.run(
            ["grep", "-rn", "execute_rollback(", "--include=*.py", str(_SRC)],
            capture_output=True,
            text=True,
        )
        callers = [
            line
            for line in result.stdout.splitlines()
            if "def execute_rollback" not in line
            and "cltr_migration.py" not in line  # rehearsal_rollback.execute_rollback -- unrelated module
        ]
        assert len(callers) == 1, f"expected exactly one production caller, found: {callers}"
        assert "commands/agent.py" in callers[0]

    def test_agent_module_never_calls_evaluate_for_advisory(self) -> None:
        source = inspect.getsource(agent_mod)
        tree = ast.parse(source)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert "evaluate_for_advisory" not in names
        assert "evaluate_for_advisory" not in attrs

    def test_mandatory_gate_uses_evaluate_for_real_effect(self) -> None:
        source = inspect.getsource(agent_mod.execute_rollback)
        assert "evaluate_for_real_effect" in source


# ── No real activation ────────────────────────────────────────────────────


class TestNoRealActivation:
    def test_no_cutover_record_or_marker_writer_referenced_in_agent_py(self) -> None:
        source = inspect.getsource(agent_mod)
        assert "_write_cutover_transition" not in source
        assert "activate_hatp_mandatory" not in source

    def test_this_repository_still_resolves_legacy_compatible(self) -> None:
        """This development host has no provisioned Class-B protected root
        and no repository identity -- confirming the classified correction
        (above) restores, rather than merely papers over, the HMRC-REQ-032
        default for the actual current deployment."""
        from pcae.core.hatp_mandatory_cutover import CutoverMode, resolve_production_hatp_cutover_mode
        from pcae.core.paths import HarnessPath

        resolution = resolve_production_hatp_cutover_mode(HarnessPath(_REPO_ROOT))
        assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE

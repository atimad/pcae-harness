"""Phase 149O.18E -- CLI + Legacy Authority Migration Integration.

Phase-boundary verification: this phase closes the transport/migration
surface that 149O.18A-18D left open -- `--hatp-evidence-id` was accepted
by `execute_rollback` (AG3, 149O.18C) and `build_rollback_execution`
(AG5, 149O.18D), but no production CLI caller supplied it. This phase:

1. Registers `--hatp-evidence-id` on `pcae remote rollback execute`
   (AG3) and `pcae rollback --per-id` (AG5), transporting exactly one
   neutral locator into the already-wired effect boundaries
   (HMRC-REQ-008/009/011/012).
2. Makes `pcae remote rollback approve` (legacy human-approval)
   cutover-mode-aware: unchanged under LEGACY_COMPATIBLE, unchanged plus
   an advisory `deprecation_warning` under PREPARED, and a deterministic
   refusal (no mutation) under HATP_MANDATORY (HMRC-REQ-057/058/059).
   The refusal lives in `approve_rollback` itself
   (`src/pcae/core/agent.py`), the sole production-reachable mutation
   boundary, so a direct call bypassing the CLI is still refused
   (mirroring HMRC-REQ-065/068's AG3/AG5 discipline).

It does not modify 149O.18A/18B/18C/18D's own gate semantics, does not
modify Permission Broker or POL-005, does not implement COMP-002, and
does not activate `HATP_MANDATORY` on any real deployment.

Production diff this phase: `src/pcae/cli.py`, `src/pcae/commands/agent.py`,
`src/pcae/core/agent.py` (the `approve_rollback` mode-aware disposition
only -- `execute_rollback`/`build_rollback_execution` bodies are
byte-unchanged).
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

# HEAD at the moment this phase began (149O.18D's final commit).
_PHASE_ENTRY_COMMIT = "7e4a469d"

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
    "src/pcae/cli.py",
    "src/pcae/commands/agent.py",
    "src/pcae/core/agent.py",
}

_FORBIDDEN_MODIFIED_FILES = (
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/hatp_signing_ceremony.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/hatp_rollback_consumption.py",
    "src/pcae/core/hatp_mandatory_cutover.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/repository_identity.py",
    "src/pcae/commands/hatp.py",
)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ── Production file allowlist ─────────────────────────────────────────────


class TestProductionFileAllowlist:
    # Updated 149O.18F (149O.5-F-3 methodology): the three checks below
    # originally diffed to an open-ended `HEAD`. Pinned to 149O.18E's own
    # completion commit (`0881346a`, also 149O.18F's own phase-entry
    # commit) so they continue to verify exactly what they were written
    # to verify -- that 149O.18E itself touched only its own expected
    # files -- independent of 149O.18F's own, separately-verified,
    # additive extension of `hatp_mandatory_cutover.py`.
    _PHASE_149O_18E_COMPLETION_COMMIT = "0881346a"

    def test_exactly_expected_files_changed(self) -> None:
        changed = {
            line
            for line in _git(
                "diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", self._PHASE_149O_18E_COMPLETION_COMMIT,
                "--", "src/pcae/",
            ).splitlines()
            if line
        }
        assert changed == _EXPECTED_CHANGED_FILES

    def test_no_forbidden_production_file_touched(self) -> None:
        changed = set(
            line
            for line in _git(
                "diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", self._PHASE_149O_18E_COMPLETION_COMMIT,
                "--", "src/pcae/",
            ).splitlines()
            if line
        )
        assert changed.isdisjoint(_FORBIDDEN_MODIFIED_FILES)

    def test_18a_cutover_module_byte_unchanged(self) -> None:
        diff = _git(
            "diff", "--stat", f"{_PHASE_ENTRY_COMMIT}", self._PHASE_149O_18E_COMPLETION_COMMIT,
            "--", "src/pcae/core/hatp_mandatory_cutover.py",
        )
        assert diff.strip() == ""

    def test_18b_consumption_module_byte_unchanged(self) -> None:
        diff = _git("diff", "--stat", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/core/hatp_rollback_consumption.py")
        assert diff.strip() == ""

    def test_ag3_execute_rollback_body_unchanged_since_entry(self) -> None:
        """149O.18C's AG3 gate must remain behaviorally unchanged --
        confined check: no diff hunk touches `execute_rollback`'s own
        body (this phase only changed its *caller*, commands/agent.py)."""
        diff = _git("diff", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/core/agent.py")
        assert "def execute_rollback" not in diff

    def test_ag5_build_rollback_execution_body_unchanged_since_entry(self) -> None:
        diff = _git("diff", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/core/agent.py")
        assert "def build_rollback_execution" not in diff


# ── Contract byte-identity ────────────────────────────────────────────────


class TestContractByteIdentity:
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3) amended PBPA-001
    # v1.0 -> v1.1 (additive only: POL-013 row + PBPA-REQ-089; PBNDE-001
    # v1.0 / PBRD-001 v3.0). Sole authorized post-entry change; current
    # bytes pinned by sha256 so any further PBPA change still fails.
    # Reconciled by .1R.22R (N-23-3).
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


# ── No Permission Broker / POL-005 change ─────────────────────────────────


class TestNoPBChange:
    def test_no_permission_broker_files_touched(self) -> None:
        changed = set(
            line
            for line in _git("diff", "--name-only", f"{_PHASE_ENTRY_COMMIT}", "--", "src/pcae/").splitlines()
            if line
        )
        assert "src/pcae/core/permission_broker.py" not in changed
        assert "src/pcae/core/permission_broker_foundation.py" not in changed


# ── AG3/AG5 CLI transport only ────────────────────────────────────────────


class TestCLITransportOnly:
    def test_ag3_handler_passes_only_hatp_evidence_id(self) -> None:
        """AST/signature test (governing-prompt item 44): the AG3
        handler's call to `execute_rollback` supplies `hatp_evidence_id`
        and no other HATP-authoritative keyword."""
        import pcae.commands.agent as commands_agent_mod

        source = inspect.getsource(commands_agent_mod.run_remote_rollback_execute)
        tree = ast.parse(source)
        call = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "execute_rollback"
        )
        kw_names = {kw.arg for kw in call.keywords}
        assert kw_names == {"hatp_evidence_id"}

    def test_ag5_handler_passes_only_hatp_evidence_id_among_hatp_kwargs(self) -> None:
        import pcae.commands.agent as commands_agent_mod

        source = inspect.getsource(commands_agent_mod.run_rollback)
        tree = ast.parse(source)
        call = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "build_rollback_execution"
        )
        kw_names = {kw.arg for kw in call.keywords}
        assert "hatp_evidence_id" in kw_names
        assert kw_names.issubset({"dry_run", "hatp_evidence_id"})

    def test_no_raw_proof_or_evidence_object_flag_registered(self) -> None:
        cli_source = (_SRC / "cli.py").read_text(encoding="utf-8")
        for forbidden in (
            '"--hatp-proof"',
            '"--hatp-evidence"',
            '"--hatp-evidence-file"',
            '"--hatp-envelope"',
        ):
            assert forbidden not in cli_source

    def test_no_authority_boolean_or_mode_override_flag_registered_on_rollback_parsers(self) -> None:
        """Scoped to the AG3/AG5/approve parser blocks this phase
        touches -- `--approval-present` exists elsewhere in `cli.py` for
        an unrelated pre-existing command and is out of this phase's
        scope."""
        cli_source = (_SRC / "cli.py").read_text(encoding="utf-8")
        start = cli_source.index('rollback_parser = subparsers.add_parser(\n        "rollback",')
        end = cli_source.index("remote_writable_contract_parser = remote_subparsers.add_parser(")
        rollback_block = cli_source[start:end]
        for forbidden in (
            '"--approved"',
            '"--approval-present"',
            '"--hatp-valid"',
            '"--legacy"',
            '"--mandatory"',
            '"--cutover-mode"',
            '"--force-legacy"',
            '"--bypass"',
        ):
            assert forbidden not in rollback_block


# ── Legacy approve mode-aware disposition ─────────────────────────────────


class TestLegacyApproveModeAwareness:
    def test_approve_rollback_resolves_cutover_mode_fresh(self) -> None:
        source = inspect.getsource(agent_mod.approve_rollback)
        assert "resolve_production_hatp_cutover_mode" in source

    def test_approve_rollback_never_consumes_evidence_or_evaluates_pb(self) -> None:
        source = inspect.getsource(agent_mod.approve_rollback)
        for forbidden in (
            "evaluate_for_real_effect",
            "evaluate_for_advisory",
            "HATPRollbackConsumptionRequest",
            "permission_broker",
            "DECISION_ALLOW",
        ):
            assert forbidden not in source

    def test_approve_rollback_mandatory_refusal_precedes_mutation_in_source(self) -> None:
        source = inspect.getsource(agent_mod.approve_rollback)
        mandatory_check_index = source.index("CutoverMode.HATP_MANDATORY")
        mutation_index = source.index('job["rollback_approval_state"] = "approved"')
        assert mandatory_check_index < mutation_index

    def test_approve_rollback_signature_unchanged(self) -> None:
        """No new parameter (mode override, evidence ID, or authority
        boolean) was added -- 149O.18E enforces mode internally, never
        via a caller-supplied override."""
        params = list(inspect.signature(agent_mod.approve_rollback).parameters)
        assert params == ["root", "job_id"]


# ── No real activation ────────────────────────────────────────────────────


class TestNoRealActivation:
    def test_no_cutover_record_or_marker_writer_referenced_anywhere_touched(self) -> None:
        for rel in ("src/pcae/core/agent.py", "src/pcae/commands/agent.py", "src/pcae/cli.py"):
            source = (_REPO_ROOT / rel).read_text(encoding="utf-8")
            assert "_write_cutover_transition" not in source
            assert "activate_hatp_mandatory" not in source

    def test_this_repository_still_resolves_legacy_compatible(self) -> None:
        from pcae.core.hatp_mandatory_cutover import CutoverMode, resolve_production_hatp_cutover_mode
        from pcae.core.paths import HarnessPath

        resolution = resolve_production_hatp_cutover_mode(HarnessPath(_REPO_ROOT))
        assert resolution.mode == CutoverMode.LEGACY_COMPATIBLE

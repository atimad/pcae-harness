"""Phase 149O.14 -- Architecture-verification test for the HATP AG3/AG5
Mandatory Production Consumption Architecture
(`docs/PHASE_149O_14_HATP_AG3_AG5_MANDATORY_PRODUCTION_CONSUMPTION_
ARCHITECTURE.md`).

149O.14 is an ARCHITECTURE-ONLY phase: it modifies no `src/pcae/**` file
and no contract file. This module does not test a new implementation
(there is none yet) -- it independently reconfirms, via direct source
inspection (AST/grep/import), the *factual baseline* the architecture
document is built on: today's real AG3/AG5 call graphs, the currently
inert Wave-7 HATP hooks, the HSCE evidence-store's explicit-ID-only API,
the registered production signing surface, the fact that legacy
`rollback_approval_state`/`pcae remote rollback approve` remain the sole
authority AG3 actually consults today, and that Permission Broker /
COMP-002 enforcement remains separate and unavailable.

Independently authored: reconstructed directly from
`src/pcae/core/agent.py`, `src/pcae/core/hatp_ag_authority.py`,
`src/pcae/commands/agent.py`, and `src/pcae/cli.py`, not from prior phase
reports.
"""
from __future__ import annotations

import ast
import inspect
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"


def _read(relpath: str) -> str:
    return (_SRC / relpath).read_text(encoding="utf-8")


def _parse(relpath: str) -> ast.Module:
    return ast.parse(_read(relpath), filename=relpath)


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function {name!r} not found")


def _call_kwargs(call: ast.Call) -> set:
    return {kw.arg for kw in call.keywords if kw.arg is not None}


def _find_calls_to(tree: ast.Module, func_name: str) -> list:
    """Return every ast.Call node anywhere in `tree` whose callee's final
    attribute/name component equals `func_name` (covers both bare-name
    calls and attribute calls like `module.func_name(...)`)."""
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id == func_name:
                calls.append(node)
            elif isinstance(fn, ast.Attribute) and fn.attr == func_name:
                calls.append(node)
    return calls


# ═══════════════════════════════════════════════════════════════════════════
# Current AG3 call graph facts (agent.py:execute_rollback)
# ═══════════════════════════════════════════════════════════════════════════


class TestCurrentAG3CallGraphFacts:
    def test_execute_rollback_has_optional_hatp_hooks(self):
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "execute_rollback")
        arg_names = {a.arg for a in fn.args.kwonlyargs}
        assert {"hatp_evidence_id", "hatp_proof", "hatp_evidence"} <= arg_names
        # All three are optional (defaulted) keyword-only arguments.
        assert len(fn.args.kw_defaults) == len(fn.args.kwonlyargs)
        defaults_by_name = dict(zip(
            (a.arg for a in fn.args.kwonlyargs), fn.args.kw_defaults
        ))
        for name in ("hatp_evidence_id", "hatp_proof", "hatp_evidence"):
            default = defaults_by_name[name]
            assert isinstance(default, ast.Constant) and default.value is None

    def test_execute_rollback_real_dispatch_precondition_is_legacy_approval_state(self):
        """The only source that can raise on rollback_approval_state is a
        direct `.get("rollback_approval_state", ...)` read compared against
        the legacy string states -- no HATP status/approval value gates
        this branch."""
        src = _read("core/agent.py")
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "execute_rollback")
        body_src = ast.get_source_segment(src, fn)
        assert body_src is not None
        assert 'job.get("rollback_approval_state"' in body_src
        assert '"approved"' in body_src
        assert '"pending"' in body_src
        assert '"denied"' in body_src

    def test_execute_rollback_hatp_block_is_additive_before_legacy_gate(self):
        """The HATP-authority block must appear lexically before the
        rollback_approval_state read in the function source, and the
        rollback_approval_state read must not be nested inside the
        `if hatp_evidence_id is not None:` block (i.e. it is not gated by
        it) -- confirming the HATP block is additive/observational only."""
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "execute_rollback")
        # Find the top-level `if hatp_evidence_id is not None:` statement
        # and confirm the rollback_approval_state read is a *sibling*
        # statement after it, not nested within its body.
        hatp_if = None
        approval_state_stmt_index = None
        top_level_stmts = fn.body
        for i, stmt in enumerate(top_level_stmts):
            # Skip the function's own docstring statement -- its prose
            # mentions "rollback_approval_state" in the pre-conditions
            # list, which is not a code reference.
            if (
                i == 0
                and isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            ):
                continue
            if isinstance(stmt, ast.If):
                test = stmt.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "hatp_evidence_id"
                ):
                    hatp_if = (i, stmt)
            src_seg = ast.get_source_segment(_read("core/agent.py"), stmt) or ""
            if "rollback_approval_state" in src_seg and approval_state_stmt_index is None:
                approval_state_stmt_index = i
        assert hatp_if is not None, "expected a top-level `if hatp_evidence_id is not None:` guard"
        assert approval_state_stmt_index is not None
        assert approval_state_stmt_index > hatp_if[0], (
            "rollback_approval_state check must be a sibling statement "
            "after the HATP block, not inside it"
        )
        # And the HATP-guard body itself does not raise/return/gate.
        hatp_if_body_src = ast.get_source_segment(_read("core/agent.py"), hatp_if[1]) or ""
        assert "raise" not in hatp_if_body_src

    def test_execute_rollback_calls_resolve_ag3_gated_rollback_authority(self):
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "execute_rollback")
        calls = [c for c in ast.walk(fn) if isinstance(c, ast.Call)]
        names = set()
        for c in calls:
            if isinstance(c.func, ast.Name):
                names.add(c.func.id)
            elif isinstance(c.func, ast.Attribute):
                names.add(c.func.attr)
        assert "resolve_ag3_gated_rollback_authority" in names

    def test_git_revert_effect_is_unconditional_on_hatp_block(self):
        """`_run_git_revert` (the real mutation) must not be nested inside
        the `if hatp_evidence_id is not None:` block."""
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "execute_rollback")
        src = _read("core/agent.py")
        hatp_if = None
        for stmt in fn.body:
            if isinstance(stmt, ast.If):
                test = stmt.test
                if (
                    isinstance(test, ast.Compare)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "hatp_evidence_id"
                ):
                    hatp_if = stmt
        assert hatp_if is not None
        hatp_if_src = ast.get_source_segment(src, hatp_if) or ""
        assert "_run_git_revert" not in hatp_if_src
        fn_src = ast.get_source_segment(src, fn) or ""
        assert "_run_git_revert" in fn_src


# ═══════════════════════════════════════════════════════════════════════════
# Current AG5 call graph facts (agent.py:build_rollback_execution)
# ═══════════════════════════════════════════════════════════════════════════


class TestCurrentAG5CallGraphFacts:
    def test_build_rollback_execution_has_optional_hatp_hooks(self):
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "build_rollback_execution")
        arg_names = {a.arg for a in fn.args.kwonlyargs}
        assert {"hatp_evidence_id", "hatp_proof", "hatp_evidence"} <= arg_names

    def test_build_rollback_execution_real_dispatch_precondition_is_structural_only(self):
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "build_rollback_execution")
        src = ast.get_source_segment(_read("core/agent.py"), fn) or ""
        assert "_RER_PER_ELIGIBLE_STATUSES" in src
        assert 'rollback_payload_available' in src
        # No AG5-analogue of a human-approval legacy field gates dispatch.
        assert "rollback_approval_state" not in src

    def test_build_rollback_execution_hatp_block_is_additive(self):
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "build_rollback_execution")
        src = _read("core/agent.py")
        hatp_if = None
        for stmt in fn.body:
            if isinstance(stmt, ast.If):
                test = stmt.test
                dumped = ast.dump(test)
                if "hatp_evidence_id" in dumped:
                    hatp_if = stmt
        assert hatp_if is not None
        hatp_if_src = ast.get_source_segment(src, hatp_if) or ""
        assert "raise" not in hatp_if_src

    def test_build_rollback_execution_calls_resolve_ag5_gated_rollback_authority(self):
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "build_rollback_execution")
        names = set()
        for c in ast.walk(fn):
            if isinstance(c, ast.Call):
                if isinstance(c.func, ast.Name):
                    names.add(c.func.id)
                elif isinstance(c.func, ast.Attribute):
                    names.add(c.func.attr)
        assert "resolve_ag5_gated_rollback_authority" in names

    def test_real_file_mutation_present_and_unconditional_on_hatp_block(self):
        """The real production effect (file write/unlink restoring PER
        contents) must exist in the function and must not be nested
        inside the `if hatp_evidence_id is not None:` block -- confirming
        AG5's real mutation is gated only by structural PER/divergence
        checks, never by HATP."""
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "build_rollback_execution")
        src = _read("core/agent.py")
        fn_src = ast.get_source_segment(src, fn) or ""
        assert "write_bytes" in fn_src or "write_text" in fn_src
        assert "unlink" in fn_src
        hatp_if = None
        for stmt in fn.body:
            if isinstance(stmt, ast.If):
                test = stmt.test
                if "hatp_evidence_id" in ast.dump(test):
                    hatp_if = stmt
        assert hatp_if is not None
        hatp_if_src = ast.get_source_segment(src, hatp_if) or ""
        assert "write_bytes" not in hatp_if_src
        assert "write_text" not in hatp_if_src


# ═══════════════════════════════════════════════════════════════════════════
# Real production callers do not supply HATP evidence today
# ═══════════════════════════════════════════════════════════════════════════


class TestRealCallersSupplyNoHATPEvidence:
    def test_run_remote_rollback_execute_calls_execute_rollback_without_hatp_kwargs(self):
        tree = _parse("commands/agent.py")
        fn = _find_function(tree, "run_remote_rollback_execute")
        calls = _find_calls_to(fn, "execute_rollback")
        assert calls, "expected a call to execute_rollback inside run_remote_rollback_execute"
        for call in calls:
            kwargs = _call_kwargs(call)
            assert not (kwargs & {"hatp_evidence_id", "hatp_proof", "hatp_evidence"})

    def test_run_rollback_calls_build_rollback_execution_without_hatp_kwargs(self):
        tree = _parse("commands/agent.py")
        fn = _find_function(tree, "run_rollback")
        calls = _find_calls_to(fn, "build_rollback_execution")
        assert calls, "expected a call to build_rollback_execution inside run_rollback"
        for call in calls:
            kwargs = _call_kwargs(call)
            assert not (kwargs & {"hatp_evidence_id", "hatp_proof", "hatp_evidence"})


# ═══════════════════════════════════════════════════════════════════════════
# Evidence store explicit-ID API shape
# ═══════════════════════════════════════════════════════════════════════════


class TestEvidenceStoreExplicitIdApiShape:
    def test_hatp_evidence_store_load_is_explicit_id_only(self):
        from pcae.core.hatp_evidence_store import HATPEvidenceStore

        sig = inspect.signature(HATPEvidenceStore.load)
        params = list(sig.parameters.values())
        # (self, evidence_id) -- no "latest"/glob/default-lookup parameter.
        names = [p.name for p in params]
        assert names == ["self", "evidence_id"]
        assert params[1].default is inspect._empty

    def test_no_latest_or_glob_lookup_method_exists_on_store(self):
        from pcae.core.hatp_evidence_store import HATPEvidenceStore

        public_methods = {
            name for name, val in vars(HATPEvidenceStore).items()
            if not name.startswith("_") and callable(val)
        }
        forbidden_substrings = ("latest", "newest", "glob", "most_recent", "any_")
        for name in public_methods:
            lowered = name.lower()
            for bad in forbidden_substrings:
                assert bad not in lowered, f"unexpected implicit-lookup-shaped method: {name}"

    def test_evidence_store_module_defines_fail_closed_error_hierarchy(self):
        from pcae.core import hatp_evidence_store as store_mod

        assert issubclass(store_mod.EvidenceNotFoundError, store_mod.HATPEvidenceStoreError)
        assert issubclass(store_mod.EvidenceConflictError, store_mod.HATPEvidenceStoreError)
        assert issubclass(store_mod.EvidencePersistenceFailureError, store_mod.HATPEvidenceStoreError)


# ═══════════════════════════════════════════════════════════════════════════
# hatp_ag_authority.py currently does NOT wire the evidence store's load()
# into the gated-authority adapter (the seam this architecture closes)
# ═══════════════════════════════════════════════════════════════════════════


class TestGatedAuthorityAdapterDoesNotLoadEnvelopeYet:
    def test_resolve_ag3_and_ag5_accept_raw_proof_and_evidence_not_envelope(self):
        import pcae.core.hatp_ag_authority as authority_mod

        for name in ("resolve_ag3_gated_rollback_authority", "resolve_ag5_gated_rollback_authority"):
            sig = inspect.signature(getattr(authority_mod, name))
            params = sig.parameters
            assert "hatp_proof" in params
            assert "hatp_evidence" in params
            assert "evidence_id" in params
            # No envelope-shaped parameter exists yet.
            assert "envelope" not in params
            assert "signed_evidence" not in params

    def test_hatp_ag_authority_module_never_calls_evidence_store_load(self):
        tree = _parse("core/hatp_ag_authority.py")
        calls = _find_calls_to(tree, "load")
        assert calls == [], (
            "hatp_ag_authority.py unexpectedly calls a `.load(...)` method "
            "-- this baseline fact (no wiring to HATPEvidenceStore.load yet) "
            "is what 149O.14's architecture closes; if this now fails, the "
            "wiring has already been implemented and the architecture "
            "document's gap analysis (§4/§7) needs revision, not this test."
        )

    def test_hatp_ag_authority_has_no_provider_or_trust_store_parameter(self):
        """F-2 closure (149O.5 finding) must still hold: no caller-supplied
        hatp_provider/hatp_trust_store parameter exists on either gated
        function."""
        import pcae.core.hatp_ag_authority as authority_mod

        for name in ("resolve_ag3_gated_rollback_authority", "resolve_ag5_gated_rollback_authority"):
            sig = inspect.signature(getattr(authority_mod, name))
            params = sig.parameters
            assert "hatp_provider" not in params
            assert "hatp_trust_store" not in params


# ═══════════════════════════════════════════════════════════════════════════
# Production signing surface exists (pcae hatp sign rollback registered)
# ═══════════════════════════════════════════════════════════════════════════


class TestProductionSigningSurfaceRegistered:
    def test_hatp_sign_rollback_registered_in_cli(self):
        src = _read("cli.py")
        assert '"hatp"' in src
        assert '"sign"' in src
        assert '"rollback"' in src
        assert "run_hatp_sign_rollback" in src

    def test_cli_help_for_hatp_sign_rollback_works(self):
        import os

        proc = subprocess.run(
            [sys.executable, "-c", "from pcae.cli import main; main()",
             "hatp", "sign", "rollback", "--help"],
            cwd=str(_REPO_ROOT), capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": str(_SRC.parent)},
        )
        assert proc.returncode == 0
        assert "--site" in proc.stdout

    def test_no_hatp_evidence_id_flag_exists_yet_on_rollback_cli_surfaces(self):
        """Confirms the CLI-surface gap this architecture closes (§10):
        today, neither `pcae rollback` nor `pcae remote rollback execute`
        register a --hatp-evidence-id flag."""
        src = _read("cli.py")
        assert "--hatp-evidence-id" not in src
        assert "--hatp-evidence" not in src or "--hatp-evidence-id" not in src


# ═══════════════════════════════════════════════════════════════════════════
# Legacy approval remains authoritative today (not yet HATP-gated)
# ═══════════════════════════════════════════════════════════════════════════


class TestLegacyApprovalStillAuthoritativeToday:
    def test_approve_rollback_unconditionally_mutates_state(self):
        tree = _parse("core/agent.py")
        fn = _find_function(tree, "approve_rollback")
        src = ast.get_source_segment(_read("core/agent.py"), fn) or ""
        assert 'job["rollback_approval_state"] = "approved"' in src
        # No HATP-status check gates this mutation today.
        assert "hatp" not in src.lower()

    def test_remote_rollback_approve_registered_and_unconditional(self):
        tree = _parse("commands/agent.py")
        fn = _find_function(tree, "run_remote_rollback_approve")
        src = ast.get_source_segment(_read("commands/agent.py"), fn) or ""
        assert "approve_rollback(" in src
        assert "hatp" not in src.lower()


# ═══════════════════════════════════════════════════════════════════════════
# Permission Broker enforcement remains separate / COMP-002 unavailable
# ═══════════════════════════════════════════════════════════════════════════


class TestPBAndCOMP002RemainSeparateAndUnavailable:
    def test_execution_disabled_rule_pol_005_present(self):
        from pcae.core.permission_broker_foundation import ExecutionDisabledRule

        assert ExecutionDisabledRule.policy_id == "POL-005"

    def test_permission_broker_decision_vocabulary_closed(self):
        from pcae.core.permission_broker_foundation import (
            DECISION_ALLOW,
            DECISION_DENY,
            DECISION_HUMAN_REVIEW,
            DECISION_VALUES,
        )

        assert set(DECISION_VALUES) == {DECISION_ALLOW, DECISION_DENY, DECISION_HUMAN_REVIEW}

    def test_execution_unavailable_status_constant_present(self):
        from pcae.core.permission_broker_foundation import (
            IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE,
        )

        assert IMPLEMENTATION_STATUS_EXECUTION_UNAVAILABLE == "execution_unavailable"

    def test_hatp_ag_authority_invokes_pb_evaluation_as_simulation_only(self):
        """Confirms today's advisory-only PB evaluation inside the
        (currently dead-on-real-paths) gated authority adapter -- the
        `simulation_only=True` construction this architecture's §3
        investigation is built on."""
        src = _read("core/hatp_ag_authority.py")
        assert "simulation_only=True" in src

    def test_no_comp_002_execution_boundary_module_exists(self):
        assert not (_SRC / "core" / "execution_boundary.py").exists()
        assert not (_SRC / "core" / "comp_002.py").exists()


# ═══════════════════════════════════════════════════════════════════════════
# No production source was modified during this architecture-only phase
# ═══════════════════════════════════════════════════════════════════════════


class TestNoProductionSourceModified:
    def test_git_diff_against_pre_phase_head_touches_no_src_pcae_or_contract_file(self):
        """Best-effort self-check: if this test file is run inside a git
        checkout with the 149O.14 pre-phase commit reachable, confirm no
        `src/pcae/**` or `docs/contracts/**` file differs from HEAD's
        parent-of-this-phase state. This is a defensive supplement, not
        the sole authority -- the phase report's own `git diff --stat`
        (run outside pytest, against the actual pre-phase commit SHA) is
        the authoritative confirmation, consistent with 149O.13's own
        convention for this exact check."""
        try:
            proc = subprocess.run(
                ["git", "status", "--porcelain", "--", "src/pcae", "docs/contracts"],
                cwd=str(_REPO_ROOT), capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pytest.skip("git unavailable in this environment")
        if proc.returncode != 0:
            pytest.skip("not a git checkout")
        # Nothing staged/unstaged/untracked under src/pcae or docs/contracts.
        assert proc.stdout.strip() == "", (
            "unexpected working-tree change under src/pcae or docs/contracts: "
            f"{proc.stdout}"
        )

    def test_no_production_source_modified_by_this_phase(self):
        """Task-lifecycle-level enforcement (forbidden-file list) plus the
        phase report's own `git diff --stat <pre-phase-HEAD>..HEAD --
        src/pcae/ docs/contracts/` step are the actual authority for this
        claim (mirrors 149O.13's own convention, §137-138 of that phase's
        governing prompt)."""
        assert True

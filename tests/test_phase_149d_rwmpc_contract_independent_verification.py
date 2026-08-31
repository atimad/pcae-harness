"""Phase 149D — Repository-Wide Mutation Permission Coverage Contract
Independent Verification.

Independent adversarial verification of RWMPC-001 v1.0 (frozen by Phase
149C). This suite does NOT trust Phase 149C's own summary, table, or
comments as evidence; every assertion here is derived from independently
re-reading current production source and independently exercising the
real, unmodified Permission Broker Foundation
(`pcae.core.permission_broker_foundation`). No production code is
exercised for its *execution* effects (no git command is ever actually
run by this suite against a real mutation) — every mutation dispatch
site is verified by source inspection (grep/AST-adjacent string search),
not by triggering it. Live Foundation calls are made only against
hand-constructed `PermissionBrokerRequest` instances, never against a
mocked or simulated broker.

This is a read-only verification suite. It does not implement, wire, or
activate any Permission Broker consumer, and it modifies no production
file.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from pcae.core import permission_broker_foundation as pbf

REPO_ROOT = Path(__file__).resolve().parent.parent

# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3) amended PBPA-001 v1.0 -> v1.1
# (additive only: the POL-013 "Narrow Local-CLI Dispatch Eligibility" row +
# PBPA-REQ-089; PBNDE-001 v1.0 §4 / PBRD-001 v3.0 §16). That is the sole
# authorized post-hoc change to the contract set these guards freeze. The
# current file bytes are pinned by sha256 so that any *further* change to
# PBPA — and any change at all to the other contracts — still fails.
# Reconciled by Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22R (N-23-3).
_AUTHORIZED_POST_HOC_CONTRACT_SHA256 = {
    "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md":
        "13fc441a6e3688d1ea1b8e62a2b0ea3fafc6a293340f6907b05b7dccf8a16660",
}


def _assert_unchanged_except_authorized_r122(baseline: str, rel_paths) -> None:
    import hashlib
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only", f"{baseline}..HEAD", "--", *rel_paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    changed = [line for line in result.stdout.split() if line]
    for path in changed:
        assert path in _AUTHORIZED_POST_HOC_CONTRACT_SHA256, (
            f"unauthorized contract change since {baseline}: {path}"
        )
        actual = hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
        assert actual == _AUTHORIZED_POST_HOC_CONTRACT_SHA256[path], (
            f"{path} changed beyond the authorized .1R.22 v1.1 amendment"
        )
    # Semantic anchor: the authorized PBPA change is exactly the v1.1
    # POL-013 additive amendment, nothing else.
    pbpa = (REPO_ROOT / "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md").read_text()
    assert "**Version:** 1.1" in pbpa
    assert "POL-013" in pbpa
PUSH_PY = REPO_ROOT / "src" / "pcae" / "commands" / "push.py"
AGENT_PY = REPO_ROOT / "src" / "pcae" / "core" / "agent.py"
TASK_PY = REPO_ROOT / "src" / "pcae" / "commands" / "task.py"
PHASE_PY = REPO_ROOT / "src" / "pcae" / "commands" / "phase.py"

_GIT_MUTATION_RE = re.compile(
    r'\[\s*"git"\s*,\s*"(commit|push|revert|reset)"'
)


def _count_git_mutation_dispatches(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(_GIT_MUTATION_RE.findall(text))


# ── 1. Exact 13-site current inventory (independently re-derived) ──────


class TestMutationInventory:
    def test_thirteen_sites_across_four_files(self):
        """Phase 149F (RWMPC-001 v1.0 Wave 1, RWMPC-REQ-035) intentionally
        changed this count for `phase.py`: PH2 and PH3 no longer construct
        their own independent `["git", "push", ...]` dispatch literal --
        they now route through `agent.py`'s shared
        `_dispatch_governed_push` (which itself calls the same
        `_run_git_push` AG2 already used), per the contract's explicit
        "no alternate code path... constructs a competing... request"
        non-bypassability requirement (RWMPC-REQ-036/037). This is the
        literal, intended effect of routing, not a regression: `phase.py`'s
        raw regex count drops from 3 to 2 (PH1's own `git commit` literal,
        plus the still-present `push_command = ["git", "push", "origin",
        "main"]` diagnostic-only list literal PH2 retains for its return
        payload -- never passed to `subprocess.run` anymore). `agent.py`'s
        count is unchanged at 3 (AG1 commit, AG2 push, AG3 revert) because
        AG2's own dispatch line was already there and is now additionally
        the sole shared dispatch point PH2/PH3 route into.
        """
        counts = {
            PUSH_PY: _count_git_mutation_dispatches(PUSH_PY),
            AGENT_PY: _count_git_mutation_dispatches(AGENT_PY),
            TASK_PY: _count_git_mutation_dispatches(TASK_PY),
            PHASE_PY: _count_git_mutation_dispatches(PHASE_PY),
        }
        # push.py: 2 (PU1, PU2); agent.py: 3 git-subprocess (AG1, AG2, AG3)
        # + 2 direct-file-write sites (AG4, AG5, not git subprocess, counted
        # separately below); task.py: 3 (TK1, TK2, TK3); phase.py: 2 post-
        # Wave-1 routing (PH1's own commit literal, plus PH2's residual
        # diagnostic-only push-command literal; PH2/PH3's actual dispatch
        # now lives in agent.py behind the shared routed adapter).
        assert counts[PUSH_PY] == 2
        assert counts[AGENT_PY] == 3
        assert counts[TASK_PY] == 3
        assert counts[PHASE_PY] == 2
        git_subprocess_total = sum(counts.values())
        assert git_subprocess_total == 10
        # Plus AG4 (promotion apply) and AG5 (promotion restore) direct
        # file write/unlink sites = 12 literal-regex-visible dispatches;
        # the 13th (PH3's push) is real and CLI-reachable but, per
        # Wave-1's intentional routing, is no longer independently
        # constructed in phase.py -- it dispatches through the same
        # `_run_git_push` call agent.py's count of 3 already includes.
        # `test_ph2_ph3_route_through_shared_alternate_push_dispatcher`
        # below independently confirms the routing (not merely the
        # absence of a literal) for both PH2 and PH3.
        assert git_subprocess_total + 2 == 12

    def test_ph2_ph3_route_through_shared_alternate_push_dispatcher(self):
        """RWMPC-REQ-035 non-bypassability, confirmed by source inspection
        (not by triggering a real push): PH2 and PH3 no longer contain an
        independent `subprocess.run(["git", "push", ...])`/`_sp.run(["git",
        "push", ...])` call -- both call `_dispatch_governed_push` instead,
        the same function AG2 uses (imported from `pcae.core.agent`)."""
        text = PHASE_PY.read_text(encoding="utf-8")
        assert "_dispatch_governed_push" in text
        push_dispatch_re = re.compile(
            r'_sp\.run\(\s*\[\s*"git"\s*,\s*"push"'
        )
        assert not push_dispatch_re.findall(text), (
            "phase.py retains an independent git-push subprocess dispatch; "
            "PH2/PH3 must route through _dispatch_governed_push instead"
        )

    def test_no_additional_git_mutation_site_elsewhere_in_src(self):
        """A repo-wide search (not just the four named files) must not
        turn up a 14th git-mutation dispatch site — otherwise the
        four-file scope in RWMPC-001 Section 4 would be under-inclusive."""
        src_dir = REPO_ROOT / "src" / "pcae"
        scoped = {PUSH_PY, AGENT_PY, TASK_PY, PHASE_PY}
        total_outside_scope = 0
        for path in src_dir.rglob("*.py"):
            if path in scoped:
                continue
            total_outside_scope += _count_git_mutation_dispatches(path)
        assert total_outside_scope == 0

    def test_promotion_apply_and_restore_are_direct_file_writes_not_git(self):
        text = AGENT_PY.read_text(encoding="utf-8")
        assert "def build_promotion_execution(" in text
        assert "def build_rollback_execution(" in text
        # Both perform direct filesystem writes/unlinks, not git
        # subprocess dispatch, within their respective functions.
        apply_start = text.index("def build_promotion_execution(")
        apply_end = text.index("def ", apply_start + 10)
        apply_body = text[apply_start:apply_end]
        assert "write_text(" in apply_body or "write_bytes(" in apply_body
        assert "unlink()" in apply_body
        assert '"git"' not in apply_body

        restore_start = text.index("def build_rollback_execution(")
        restore_end = text.index("def ", restore_start + 10)
        restore_body = text[restore_start:restore_end]
        assert "write_text(" in restore_body or "write_bytes(" in restore_body
        assert '"git"' not in restore_body


# ── 2. AG5 is a standalone command, not an automatic failure-restore ───


class TestAG5IsStandaloneNotAutomaticRestore:
    def test_build_promotion_execution_does_not_call_rollback_on_failure(self):
        text = AGENT_PY.read_text(encoding="utf-8")
        start = text.index("def build_promotion_execution(")
        end = text.index("def ", start + 10)
        body = text[start:end]
        # A failed per-file write is recorded and the loop continues; no
        # automatic call to build_rollback_execution occurs within this
        # function.
        assert "build_rollback_execution(" not in body

    def test_rollback_is_cli_reachable_as_independent_command(self):
        cli_py = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
        assert '"rollback"' in cli_py
        assert "run_rollback" in cli_py


# ── 3. Truthful requests for every in-scope operation class ────────────


def _truthful_request(*, action_type, execution_class, approval_present, simulation_only):
    return pbf.build_permission_broker_request(
        action_type=action_type,
        execution_class=execution_class,
        requested_component="COMP-001",
        requested_capability="verify_149d",
        task_id="task-149d-verify",
        phase_id="149D",
        evidence_available=True,
        approval_present=approval_present,
        simulation_only=simulation_only,
    )


class TestTruthfulRequestsAgainstLiveFoundation:
    def setup_method(self):
        self.broker = pbf.PermissionBroker()

    def test_commit_satisfiable(self):
        req = _truthful_request(
            action_type=pbf.ACTION_COMMIT,
            execution_class=pbf.EXECUTION_CLASS_MUTATION,
            approval_present=False,
            simulation_only=True,
        )
        decision = self.broker.evaluate(req)
        assert decision.decision == pbf.DECISION_ALLOW
        assert "POL-004" in decision.non_applicable_policy_ids

    def test_push_alternate_dispatch_satisfiable(self):
        req = _truthful_request(
            action_type=pbf.ACTION_PUSH,
            execution_class=pbf.EXECUTION_CLASS_MUTATION,
            approval_present=False,
            simulation_only=True,
        )
        decision = self.broker.evaluate(req)
        assert decision.decision == pbf.DECISION_ALLOW

    def test_promotion_apply_satisfiable(self):
        req = _truthful_request(
            action_type=pbf.ACTION_SOURCE_MUTATION,
            execution_class=pbf.EXECUTION_CLASS_MUTATION,
            approval_present=False,
            simulation_only=True,
        )
        decision = self.broker.evaluate(req)
        assert decision.decision == pbf.DECISION_ALLOW

    def test_rollback_truthful_request_is_human_review_not_allow(self):
        """A truthful rollback request (approval_present=False, since no
        trusted evidence source exists) SHALL resolve to HUMAN_REVIEW, not
        ALLOW and not DENY -- zero dispatch, per POL-004."""
        req = _truthful_request(
            action_type=pbf.ACTION_ROLLBACK,
            execution_class=pbf.EXECUTION_CLASS_ROLLBACK,
            approval_present=False,
            simulation_only=True,
        )
        decision = self.broker.evaluate(req)
        assert decision.decision == pbf.DECISION_HUMAN_REVIEW
        assert "POL-004" in decision.causing_policy_ids

    def test_rollback_hypothetical_approval_present_would_allow(self):
        """Isolates the rollback gap to evidence availability alone: if a
        trusted approval_present=True existed, the request would resolve
        to ALLOW -- no other policy or applicability defect blocks it."""
        req = _truthful_request(
            action_type=pbf.ACTION_ROLLBACK,
            execution_class=pbf.EXECUTION_CLASS_ROLLBACK,
            approval_present=True,
            simulation_only=True,
        )
        decision = self.broker.evaluate(req)
        assert decision.decision == pbf.DECISION_ALLOW


# ── 4. simulation_only=False POL-005 control ────────────────────────────


class TestSimulationOnlyFalsePOL005Control:
    def setup_method(self):
        self.broker = pbf.PermissionBroker()

    @pytest.mark.parametrize(
        "execution_class,approval_present",
        [
            (pbf.EXECUTION_CLASS_MUTATION, False),
            (pbf.EXECUTION_CLASS_ROLLBACK, True),
        ],
    )
    def test_simulation_only_false_unconditionally_denies(
        self, execution_class, approval_present
    ):
        req = _truthful_request(
            action_type=pbf.ACTION_COMMIT
            if execution_class == pbf.EXECUTION_CLASS_MUTATION
            else pbf.ACTION_ROLLBACK,
            execution_class=execution_class,
            approval_present=approval_present,
            simulation_only=False,
        )
        decision = self.broker.evaluate(req)
        assert decision.decision == pbf.DECISION_DENY
        assert "POL-005" in decision.causing_policy_ids

    def test_simulation_only_is_foundation_wide_not_push_specific(self):
        """RWMPC-REQ-015's claim: the simulation_only=False -> POL-005 DENY
        rule is a Foundation-wide fact, not a push-specific carve-out --
        verified here for a non-push execution class (mutation via commit)
        rather than only re-testing pcae push's own already-certified
        behavior."""
        req = _truthful_request(
            action_type=pbf.ACTION_COMMIT,
            execution_class=pbf.EXECUTION_CLASS_MUTATION,
            approval_present=False,
            simulation_only=False,
        )
        decision = self.broker.evaluate(req)
        assert decision.decision == pbf.DECISION_DENY
        assert decision.decision_reason == "execution_boundary_unavailable"


# ── 5. Self-declared flags do not count as approval ─────────────────────


class TestApprovalEvidenceNotSelfDeclared:
    @pytest.mark.parametrize(
        "flag_pattern",
        [
            r"--promotion-authorized",
            r"--reviewed-by",
            r"--approve-keep",
            r"--approved-by",
            r"--reason",
        ],
    )
    def test_legacy_flag_never_assigned_directly_to_approval_present(self, flag_pattern):
        """No production source may pipe a legacy CLI flag's value
        directly into approval_present= without an intervening trust
        boundary. This is a structural grep, not a claim about future
        code -- it fails if a future change wires a self-declared flag
        straight into approval_present."""
        for path in (PUSH_PY, AGENT_PY, TASK_PY, PHASE_PY):
            text = path.read_text(encoding="utf-8")
            # A dangerous pattern would look like:
            #   approval_present=args.approved_by
            # or similar direct flag-to-field wiring. None should exist.
            danger = re.search(
                r"approval_present\s*=\s*args\.", text
            )
            assert danger is None, f"{path} wires an arg directly into approval_present"


# ── 6. No caller-selectable classification/policy mechanism ────────────


class TestNoCallerPolicySelectionSurface:
    @pytest.mark.parametrize(
        "forbidden",
        [
            "--execution-class",
            "--policy-profile",
            "exclude_policies",
            "selected_policy_ids",
            "--skip-policy",
        ],
    )
    def test_forbidden_flag_absent_from_all_four_files(self, forbidden):
        for path in (PUSH_PY, AGENT_PY, TASK_PY, PHASE_PY):
            text = path.read_text(encoding="utf-8")
            assert forbidden not in text, f"{forbidden} found in {path}"


# ── 7. POL-004 applicability matches PBPA-001's frozen scope exactly ────


class TestPOL004ApplicabilityIndependentReconfirmation:
    def test_pol004_scoped_execution_classes(self):
        rule = next(
            r
            for r in pbf.DEFAULT_POLICY_RULES
            if r.policy_id == "POL-004"
        )
        assert rule.applicable_execution_classes == frozenset({
            pbf.EXECUTION_CLASS_SHELL,
            pbf.EXECUTION_CLASS_BACKEND,
            pbf.EXECUTION_CLASS_ADAPTER,
            pbf.EXECUTION_CLASS_ROLLBACK,
        })
        assert pbf.EXECUTION_CLASS_MUTATION not in rule.applicable_execution_classes
        assert pbf.EXECUTION_CLASS_NONE not in rule.applicable_execution_classes


# ── 8. PBPC/PBPA compatibility: contracts unamended ─────────────────────


class TestContractsUnamended:
    def test_pbpc_and_pbpa_contract_files_unchanged_since_before_chapter_149(self):
        # PBPC-001 unchanged; PBPA-001 carries only the authorized
        # .1R.22 v1.1 additive amendment (pinned by sha256). See .1R.22R.
        _assert_unchanged_except_authorized_r122(
            "45e32236",
            [
                "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
                "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
            ],
        )


# ── 9. No production modification by this verification phase ───────────


class TestNoProductionModification:
    def test_src_pcae_untouched_by_phase_149d(self):
        import subprocess

        # Baseline: last commit before 149D's own work began (149C's
        # close-out commit).
        result = subprocess.run(
            ["git", "diff", "--name-only", "93a70b14..HEAD", "--", "src/pcae/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_existing_contract_text_not_amended_by_phase_149d(self):
        # 149D amended none of these. The only post-149D change to the set
        # is the authorized .1R.22 PBPA-001 v1.1 additive amendment (pinned
        # by sha256); RWMPC-001 and PBPC-001 remain byte-unchanged. .1R.22R.
        _assert_unchanged_except_authorized_r122(
            "93a70b14",
            [
                "docs/contracts/REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
                "docs/contracts/PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
                "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
            ],
        )

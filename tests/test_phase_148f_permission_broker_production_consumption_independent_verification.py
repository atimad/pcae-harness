"""Phase 148F — Permission Broker Production Consumption Independent
Implementation Verification.

Independent adversarial verification of Phase 148E's PBPC-001 v1.2
production consumption wiring in `pcae push`. This suite does NOT trust
Phase 148E's own test suite, implementation document, or comments as
evidence; every assertion here is derived from independently reading the
current production source and independently exercising the real CLI
entry point (`pcae.cli.main(["push", ...])`) or the real adapter
(`push_module._evaluate_push_permission`) against the unmodified,
canonical Permission Broker Foundation.

Coverage deliberately different from
`tests/test_permission_broker_push_production_consumption.py`:

- repository-wide git-push dispatch-site inventory assertion (not just
  the two sites 148E claims);
- a duck-typed fake decision object (has a `.decision == "ALLOW"`
  attribute but is not a `PermissionBrokerDecision` instance) -- broader
  than 148E's plain-string invalid-result test;
- broker *construction* failure (registry construction raising),
  distinct from 148E's broker *evaluation* failure test;
- the reverse stale-decision sequence (DENY then ALLOW), proving no
  stale *denial* is cached either, complementing 148E's ALLOW-then-DENY
  test;
- a scoped repository-wide Permission Broker consumer inventory,
  independently classifying every consumer rather than trusting 148E's
  claimed "one production file changed";
- a mechanical-block-cannot-be-overridden-by-ALLOW case (force-push
  required) using a real forced ALLOW decision;
- HARD_BLOCK_REGISTRY recount tied to this phase, independent of 148E's
  own recount claim.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.integration]

from pcae.cli import main
from pcae.commands import push as push_module
from pcae.commands.init import init_harness
from pcae.core import permission_broker_foundation as pbf
from pcae.core.paths import HarnessPath
from pcae.core.tasks import create_task_contract

REPO_ROOT = Path(__file__).resolve().parent.parent


# ── shared fixtures (independently written; same shape as 148E's for a
# working local bare-remote repo, since that plumbing is not itself
# under test) ────────────────────────────────────────────────────────


def _init_with_remote(tmp_path: Path, monkeypatch, with_task: bool = True) -> Path:
    bare = tmp_path / "remote.git"
    bare.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=bare, check=True, capture_output=True)

    work = tmp_path / "work"
    work.mkdir()
    init_harness(HarnessPath(work))
    subprocess.run(["git", "init"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=work, check=True, capture_output=True)
    if with_task:
        create_task_contract(
            HarnessPath(work),
            "148F independent verification test task",
            created_at=datetime(2026, 8, 2, 20, 0, tzinfo=timezone.utc),
        )
    subprocess.run(["git", "add", "."], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "branch", "-M", "main"], cwd=work, capture_output=True, text=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd=work, check=True, capture_output=True)
    monkeypatch.chdir(work)
    return work


def _create_unpushed_commit(root: Path, filename: str = "impl.py", msg: str = "implementation") -> None:
    p = root / filename
    p.write_text(f"# {msg}\n", encoding="utf-8")
    subprocess.run(["git", "add", filename], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", msg, "--", filename], cwd=root, check=True, capture_output=True)


def _spy_git_push(monkeypatch) -> dict:
    real_run = subprocess.run
    calls = {"count": 0}

    def fake_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) >= 2 and cmd[0] == "git" and cmd[1] == "push":
            calls["count"] += 1
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(push_module.subprocess, "run", fake_run)
    return calls


# ── 1. Repository-wide git-push dispatch-site inventory ──────────────────


def test_repository_wide_git_push_dispatch_site_inventory():
    """Independently (re-)establish the full set of real `git push`
    dispatch call sites across the entire `src/pcae` tree, not just the
    two 148E claims inside `push.py`. Confirms: exactly two such sites
    exist within `push.py` itself, and any additional real dispatch
    sites found elsewhere are NOT reachable through the `pcae push` CLI
    verb (which dispatches only to `run_push`), so they fall outside
    this contract's non-bypassability guarantee -- but their existence
    must be surfaced, not silently assumed away.
    """
    import ast

    push_only_sites = []
    other_sites = []
    for path in sorted((REPO_ROOT / "src" / "pcae").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if '"push"' not in source and "'push'" not in source:
            continue
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            is_subprocess_like = (
                (isinstance(func, ast.Attribute) and func.attr == "run")
                or (isinstance(func, ast.Name) and func.id == "run")
            )
            if not is_subprocess_like or not node.args:
                continue
            first_arg = node.args[0]
            if not isinstance(first_arg, ast.List):
                continue
            elts = first_arg.elts
            if len(elts) < 2:
                continue
            values = [e.value for e in elts if isinstance(e, ast.Constant)]
            if len(values) >= 2 and values[0] == "git" and values[1] == "push":
                rel = path.relative_to(REPO_ROOT)
                site = (str(rel), node.lineno)
                if str(rel) == "src/pcae/commands/push.py":
                    push_only_sites.append(site)
                else:
                    other_sites.append(site)

    # The critical invariant: exactly two real dispatch sites inside
    # push.py itself (the module `pcae push` actually dispatches to).
    assert len(push_only_sites) == 2, f"expected exactly 2 git-push sites in push.py, found {push_only_sites}"

    # Any other real git-push dispatch sites in the tree are documented
    # here as pre-existing, separate CLI verbs (`pcae agent`, `pcae
    # phase ...`), not reachable through `pcae push`, and therefore not
    # claimed to be covered by PBPC-001. This assertion fails loudly if
    # a NEW one appears that nobody has classified.
    known_other_sites = {
        "src/pcae/core/agent.py",
        "src/pcae/commands/phase.py",
    }
    unexpected = [s for s in other_sites if s[0] not in known_other_sites]
    assert not unexpected, f"unclassified git-push dispatch site(s) found: {unexpected}"


def test_ungated_dispatch_sites_are_not_reachable_through_pcae_push():
    """The non-push.py dispatch sites found above are real, but they
    belong to `pcae agent ...` and `pcae phase ...`, not `pcae push`.
    `push.py` does import one unrelated helper from `commands.phase`
    (`_finalize_report_and_notify`, used only for post-push lifecycle
    reconciliation) -- confirm specifically that it never imports or
    calls either of the two ungated dispatch functions identified by
    the repository-wide inventory
    (`_build_backend_created_output_adoption_push_execution` /
    `_build_final_verification_tooling_push_decision`), nor anything
    from `core/agent.py`.
    """
    push_source = (REPO_ROOT / "src" / "pcae" / "commands" / "push.py").read_text(encoding="utf-8")
    assert "core.agent" not in push_source
    assert "_build_backend_created_output_adoption_push_execution" not in push_source
    assert "_build_final_verification_tooling_push_decision" not in push_source
    assert "push_file_changes" not in push_source


# ── 2. Duck-typed fake ALLOW rejection (broader than a plain string) ────


class _FakeAllowDecision:
    """Deliberately mimics the *shape* of an ALLOW decision (has a
    `.decision` attribute equal to the canonical ALLOW string) without
    being an actual `PermissionBrokerDecision` instance. If the adapter
    ever weakens its `isinstance` check to a duck-typed attribute check,
    this must dispatch; today it must not.
    """

    decision = pbf.DECISION_ALLOW
    decision_reason = "forged"
    causing_policy_ids = ()


def test_ordinary_path_rejects_duck_typed_fake_allow(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def fake_evaluate(self, request):
        return _FakeAllowDecision()

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)

    exit_code = main(["push"])
    capsys.readouterr()

    assert exit_code == 1
    assert dispatch_calls["count"] == 0


def test_staged_file_aware_rejects_duck_typed_fake_allow(tmp_path, monkeypatch, capsys):
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def fake_evaluate(self, request):
        return _FakeAllowDecision()

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", fake_evaluate)

    exit_code = main(["push", "--staged-file-aware"])
    capsys.readouterr()

    assert exit_code == 1
    assert dispatch_calls["count"] == 0


# ── 3. Broker CONSTRUCTION failure (distinct from evaluate() failure) ──


def test_ordinary_path_broker_construction_failure_does_not_dispatch(tmp_path, monkeypatch, capsys):
    """148E's suite only forces `PermissionBroker.evaluate()` to raise --
    that call site is wrapped in a `try/except Exception`. Independently
    attack the earlier boundary: `permission_broker_foundation
    .PermissionBroker()` construction itself raising, on the line
    immediately before the try block (`push.py`'s
    `_evaluate_push_permission`: `broker_instance = broker if broker is
    not None else permission_broker_foundation.PermissionBroker()` sits
    OUTSIDE its own subsequent `try:`).

    FINDING (148F, NON-BLOCKING; repaired 148G.1, F-148F-1): this was not
    wrapped, so a construction failure used to be an *unhandled*
    exception that propagated out of `pcae.cli.main()` itself, rather
    than the clean fail-closed diagnostic
    (`"Push blocked: Permission Broker evaluation failed (...)"`, exit
    code 1) the `evaluate()`-failure path already produced. The core
    security invariant held either way (zero dispatch), but this was a
    genuine diagnostics-quality gap against the "any broker failure ...
    fail closed" claim in `_evaluate_push_permission`'s own docstring and
    against PBPC-001 v1.2's diagnostics contract (Section 19). Phase
    148G.1 widened `_evaluate_push_permission`'s `try:` to cover
    `PermissionBroker()` construction, so this now asserts the repaired,
    graceful behavior: a controlled diagnostic and exit code 1, not a
    raw traceback.
    """
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def broken_init(self, registry=None):
        raise RuntimeError("simulated registry construction failure")

    monkeypatch.setattr(pbf.PermissionBroker, "__init__", broken_init)

    exit_code = main(["push"])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "Push blocked: Permission Broker evaluation failed" in out
    assert "simulated registry construction failure" in out
    assert dispatch_calls["count"] == 0


def test_staged_file_aware_broker_construction_failure_does_not_dispatch(tmp_path, monkeypatch, capsys):
    """Staged-file-aware-path counterpart to the ordinary-path test above
    -- same construction call, same finding, repaired by the same 148G.1
    `try:` widening (shared `_evaluate_push_permission` helper)."""
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work)
    dispatch_calls = _spy_git_push(monkeypatch)

    def broken_init(self, registry=None):
        raise RuntimeError("simulated registry construction failure")

    monkeypatch.setattr(pbf.PermissionBroker, "__init__", broken_init)

    exit_code = main(["push", "--staged-file-aware"])
    out = capsys.readouterr().out

    assert exit_code == 1
    assert "BROKER_FAILURE" in out
    assert "simulated registry construction failure" in out
    assert dispatch_calls["count"] == 0


# ── 4. Reverse stale-decision sequence: DENY then ALLOW ─────────────────


def test_ordinary_path_denial_is_not_cached_across_attempts(tmp_path, monkeypatch, capsys):
    """Complement to 148E's ALLOW-then-DENY test: force a DENY on the
    first attempt, then a genuine ALLOW on the second, proving no stale
    *denial* is cached or reused to block a later, independently
    legitimate attempt either.
    """
    work = _init_with_remote(tmp_path, monkeypatch)
    _create_unpushed_commit(work, filename="first.py", msg="first")
    dispatch_calls = _spy_git_push(monkeypatch)

    call_count = {"n": 0}
    real_evaluate = pbf.PermissionBroker.evaluate

    def deny_once_then_real(self, request):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return pbf.PermissionBrokerDecision(
                decision=pbf.DECISION_DENY,
                decision_reason="forced_first_denial",
                matched_no_go_ids=(),
                matched_invariants=(),
                required_remediation=(),
                requires_human=False,
                simulation_only=True,
                causing_policy_ids=("POL-001",),
            )
        return real_evaluate(self, request)

    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", deny_once_then_real)

    exit_code_1 = main(["push"])
    capsys.readouterr()
    assert exit_code_1 == 1
    assert dispatch_calls["count"] == 0

    # Second attempt: broker now genuinely evaluates (task exists,
    # simulation_only=True, mutation exempt from POL-004) -> real ALLOW.
    exit_code_2 = main(["push"])
    capsys.readouterr()
    assert exit_code_2 == 0
    assert dispatch_calls["count"] == 1
    assert call_count["n"] == 2


# ── 5. Independent Permission Broker consumer scope inventory ───────────


def test_permission_broker_consumer_scope_inventory():
    """Repository-wide search for every module that imports the
    Foundation broker or constructs `PermissionBroker(`, independently
    classified.

    Phase 149F (RWMPC-001 v1.0 Wave 1) intentionally added a second
    authorized production consumer, `src/pcae/core/mutation_permission.py`
    -- the sole module permitted to construct a `PermissionBrokerRequest`
    for a non-`pcae push` mutation site (RWMPC-REQ-013), consumed by AG1/
    AG2/AG4 (`pcae.core.agent`) and PH1/PH2/PH3 (`pcae.commands.phase`),
    which route through it rather than constructing their own request --
    this is the narrowed invariant this test now protects: `push.py` and
    `mutation_permission.py` are the *only* two authorized production
    mutation consumers; every other module must remain a pre-existing,
    observation/read-only touchpoint that predates Phase 148E (i.e. the
    diff between the pre-148E baseline and today's HEAD must not touch
    them), and no *third* new consumer may appear undetected.
    """
    src_root = REPO_ROOT / "src" / "pcae"
    consumers = []
    for path in sorted(src_root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        if "permission_broker_foundation" in source or "PermissionBroker(" in source:
            consumers.append(path.relative_to(REPO_ROOT))

    authorized_production_consumer = Path("src/pcae/commands/push.py")
    authorized_wave1_consumer = Path("src/pcae/core/mutation_permission.py")
    pre_existing_observational = {
        Path("src/pcae/core/runtime_context.py"),
        Path("src/pcae/core/command_path_observation.py"),
        Path("src/pcae/core/runtime_introspection.py"),
        Path("src/pcae/core/runtime_registry.py"),
        Path("src/pcae/core/permission_broker_foundation.py"),
    }

    assert authorized_production_consumer in consumers
    assert authorized_wave1_consumer in consumers
    unexpected = [
        c for c in consumers
        if c != authorized_production_consumer
        and c != authorized_wave1_consumer
        and c not in pre_existing_observational
    ]
    assert not unexpected, f"unexpected new Permission Broker consumer(s): {unexpected}"

    # Chapter 148 MVP scope, narrowed by Chapter 149 (RWMPC-001 Wave 1):
    # commit.py/task.py remain wholly unwired (TK1-3 explicitly deferred,
    # RWMPC-001 Section 14); phase.py and core/agent.py are now authorized
    # to *consume* mutation_permission.py's adapters (PH1/PH2/PH3, AG1/
    # AG2/AG4) but SHALL NOT themselves construct a `PermissionBrokerRequest`
    # or reference the Foundation/broker directly -- that remains
    # mutation_permission.py's exclusive responsibility (RWMPC-REQ-013).
    for unwired in ("commit.py", "task.py"):
        p = src_root / "commands" / unwired
        text = p.read_text(encoding="utf-8")
        assert "permission_broker_foundation" not in text
        assert "PermissionBroker(" not in text

    for consolidated in (src_root / "commands" / "phase.py", src_root / "core" / "agent.py"):
        text = consolidated.read_text(encoding="utf-8")
        assert "permission_broker_foundation" not in text
        assert "PermissionBroker(" not in text


# ── 6. Mechanical block cannot be overridden by a genuine ALLOW ─────────


def test_staged_file_aware_force_push_block_not_overridden_by_allow(tmp_path, monkeypatch, capsys):
    """`_run_push_staged_file_aware`'s force-push-required mechanical
    check runs strictly before the Permission Broker is even
    constructed. Independently force the broker to genuinely ALLOW
    (not merely leave it unforced) and confirm the mechanical block
    still wins -- permission is not mechanical validity (PBPC's own
    stated distinction).
    """
    work = _init_with_remote(tmp_path, monkeypatch)
    # Push a commit to origin/main first, then rewrite local history on
    # top of an earlier ancestor -- origin/main is then genuinely NOT an
    # ancestor of the new local HEAD, requiring a real force push.
    _create_unpushed_commit(work, filename="pushed.py", msg="pushed")
    subprocess.run(["git", "push", "origin", "main"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=work, check=True, capture_output=True)
    (work / "other.py").write_text("# other\n", encoding="utf-8")
    subprocess.run(["git", "add", "other.py"], cwd=work, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "diverge"], cwd=work, check=True, capture_output=True)

    dispatch_calls = _spy_git_push(monkeypatch)
    broker_constructed = {"count": 0}
    real_init = pbf.PermissionBroker.__init__

    def counting_init(self, registry=None):
        broker_constructed["count"] += 1
        real_init(self, registry)

    def force_allow(self, request):
        return pbf.PermissionBrokerDecision(
            decision=pbf.DECISION_ALLOW,
            decision_reason="forced_allow_for_mechanical_override_test",
            matched_no_go_ids=(),
            matched_invariants=(),
            required_remediation=(),
            requires_human=False,
            simulation_only=True,
            causing_policy_ids=(),
        )

    monkeypatch.setattr(pbf.PermissionBroker, "__init__", counting_init)
    monkeypatch.setattr(pbf.PermissionBroker, "evaluate", force_allow)

    exit_code = main(["push", "--staged-file-aware"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "force push" in output.lower()
    assert dispatch_calls["count"] == 0
    # The mechanical block must occur before the broker is even
    # constructed for this attempt.
    assert broker_constructed["count"] == 0


# ── 7. HARD_BLOCK_REGISTRY recount (independent of 148E's claim) ────────


def test_hard_block_registry_count_and_identity_unchanged():
    from pcae.core.permission_broker import HARD_BLOCK_REGISTRY

    assert len(HARD_BLOCK_REGISTRY) == 12
    reason_codes = {hb.reason_code for hb in HARD_BLOCK_REGISTRY}
    assert reason_codes == {
        "blocked_by_raw_git_commit",
        "blocked_by_raw_git_push",
        "blocked_by_force_push",
        "blocked_by_no_verify",
        "blocked_by_destructive_filesystem",
        "blocked_by_unknown_command_class",
        "blocked_by_out_of_scope",
        "blocked_by_policy_forbidden_file",
        "blocked_by_forbidden_path",
        "blocked_by_missing_task",
        "blocked_by_enforcement_not_ready",
        "blocked_by_enforcement_not_authorized",
    }


# ── 8. execution_class / approval / simulation cannot be caller-selected ─


def test_cli_push_parser_exposes_no_permission_override_flags():
    """Independently inspect the actual argparse wiring for `pcae push`
    (not push.py's internals) to confirm no CLI flag exists that could
    let a caller select `execution_class`, `approval_present`, or
    `simulation_only`, or exclude/select policies."""
    import pcae.cli as cli_module

    cli_source = Path(cli_module.__file__).read_text(encoding="utf-8")
    # Isolate the push subparser construction block.
    start = cli_source.index('push_parser = subparsers.add_parser(\n        "push",')
    end = cli_source.index("push_subparsers.add_parser", start)
    push_block = cli_source[start:end]

    for forbidden in (
        "execution_class", "approval_present", "simulation_only",
        "exclude_policies", "selected_policy_ids", "skip_policy", "policy_profile",
    ):
        assert forbidden not in push_block, f"unexpected permission-override surface in push CLI: {forbidden}"

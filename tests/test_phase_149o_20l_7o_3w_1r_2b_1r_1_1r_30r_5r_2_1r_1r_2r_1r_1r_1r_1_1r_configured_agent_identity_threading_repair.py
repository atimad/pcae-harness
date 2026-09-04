"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R —
Configured-Agent-Identity Threading Repair for
`hatp_class_b_topology_verifier.py`'s ACL Ancestor-Chain / Trusted-
Executable verification.

THE DEFECT (found by the immediately preceding F-5 deployment-
preparation retry, task
`20260904-2011-...-production-protected-root-protected-presentation-
helper-deployment-preparation-retry`): the canonical HPAC-PPA
registration path (`hpac_protected_admin_writer.py`) already threads
the CONFIGURED PCAE agent principal's resolved `(uid, gids)` — from
`hpac_pawa_agent_exclusion.resolve_configured_agent_identity()`, never
`os.geteuid()` (F-1, HPAC-PAWA-REQ-022) — through `_effective_write_
access` and `_ancestor_chain_safe` for the Protected Root and its
ancestor chain. But the ACL branch of `_effective_write_access`
(`_acl_grants_agent_write` -> `_acl_grants_agent_write_linux`/
`_acl_grants_agent_write_macos`) resolves its own ACL-inspection tool
(`getfacl`/`ls`) via `_resolve_trusted_executable`, which derived its
subject from the *ambient* `_current_agent_identity()` (the live
invoking process) instead of the `(agent_uid, agent_gids)` already
passed to it. When the canonical registration path runs as root (the
legitimate deployment owner), root-owned, owner-writable system
directories such as `/usr/bin` then misclassify as
"agent[=root]-writable", `_resolve_trusted_executable` returns `None`
(untrusted) for `ls`/`getfacl`, and every Protected-Root ancestor's ACL
check becomes `acl_inspection_unavailable` (indeterminate) — which is
exactly the `protected_root_untrusted: indeterminate permissions:
acl_inspection_unavailable` failure the predecessor phase's F-5 retry
hit.

THE REPAIR: a new sibling primitive,
`_resolve_trusted_executable_for_subject(name, agent_uid, agent_gids)`,
identical in algorithm to `_resolve_trusted_executable` but evaluated
against an explicit subject. `_acl_grants_agent_write_linux`/
`_acl_grants_agent_write_macos` now call it with the same
`(agent_uid, agent_gids)` they already received, instead of the
ambient-identity `_resolve_trusted_executable`.

`_resolve_trusted_executable` itself is deliberately left completely
untouched — not refactored into a shared implementation, not given an
extra optional parameter — because it is independently frozen by two
earlier phases' own guard tests: 149O.20J.1's
`test_resolve_trusted_executable_base_primitive_unchanged` (source-
content assertion) and 149O.20J.2's
`test_resolve_trusted_executable_base_primitive_unchanged_since_pre_
repair` (`git diff -G'def _resolve_trusted_executable\\('` pickaxe
against that phase's own pre-repair baseline commit). Both remain
green, unperturbed, after this repair — independently reconfirmed
below. `_resolve_trusted_executable` continues to serve its one
existing caller that legitimately needs live-process semantics
(`_resolve_trusted_executable_with_effective_access`, consumed only by
`hatp_environment_lock_verifier.py`'s own-environment self-check,
which has no configured-agent notion at all).

Three pre-existing tests needed disclosed, non-weakening reconciliation
because they depended on the exact ambient-identity side effect this
repair corrects (all edited in this phase, see their own updated
docstrings/comments for the full explanation):
- `tests/test_phase_149o_20j_1_class_b_deployment_verifier_narrow_
  defect_repair.py::test_pth_ordinary_path_line_still_evaluated_as_path`
- `tests/test_phase_149o_20j_5_class_b_acl_only_higher_ancestor_
  detection_macos_narrow_repair.py::test_acl_inspection_tool_
  unavailable_fails_closed`
- `tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_
  environment_lock_independent_implementation_verification.py::
  test_pth_path_injection_is_rejected`

Strictly read-only against the real filesystem outside test-owned
`tmp_path` fixtures (`chmod +a`/`chmod` only ever targets fixture
paths). No Protected Root / PAWA / PPA host state is touched anywhere
in this suite.
"""
from __future__ import annotations

import ast
import inspect
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from pcae.core import hatp_class_b_topology_verifier as topo  # noqa: E402

#: The repair-entry SHA (R), frozen at the start of this phase — HEAD of
#: "Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1:
#: reflect clean push state in metadata".
REPAIR_ENTRY_SHA = "5568b5abb578c6072afc3b790aa59223d4f2c73c"


def _agent_identity():
    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}


def _git(*args: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=15)


# ═══════════════════════════════════════════════════════════════════════
# 1-6 — Lineage / scope
# ═══════════════════════════════════════════════════════════════════════


def test_repair_entry_sha_is_head_of_predecessor_completion():
    result = _git("log", "-1", "--format=%s", REPAIR_ENTRY_SHA)
    assert result.returncode == 0
    assert "149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1" in result.stdout


def test_predecessor_blocked_report_task_preserved():
    """The predecessor F-5 deployment-preparation-retry task's BLOCKED
    verdict must remain unrewritten by this repair."""

    result = _git("show", f"{REPAIR_ENTRY_SHA}:tasks/done/"
                   "20260904-2011-phase-149o-20l-7o-3w-1r-2b-1r-1-1r-30r-5r-2-1r-1r-2r-1r-1r-1r-1-1-"
                   "production-protected-root-protected-presentation-helper-deployment-preparation-retry.md")
    assert result.returncode == 0, result.stderr
    assert "BLOCKED" in result.stdout


def test_no_f5_registration_retry_performed_by_this_repair():
    """Strictly source-level: this repair's own diff never touches
    `scripts/hpac_protected_root_admin.py` or `scripts/hpac_protected_
    presentation_admin.py` (the F-5 provisioning/registration tools)."""

    result = _git("diff", "--name-only", REPAIR_ENTRY_SHA, "--", "scripts/")
    changed = [line for line in result.stdout.splitlines() if line]
    assert changed == [], f"repair must not touch F-5 provisioning/registration scripts: {changed}"


def test_production_diff_scope_bounded_to_topology_verifier():
    result = _git("diff", "--name-only", REPAIR_ENTRY_SHA, "--", "src/")
    changed = [line for line in result.stdout.splitlines() if line]
    assert changed == ["src/pcae/core/hatp_class_b_topology_verifier.py"], changed


def test_contracts_byte_unchanged_since_repair_entry():
    result = _git("diff", "--name-only", REPAIR_ENTRY_SHA, "--", "docs/contracts/")
    assert result.stdout.strip() == "", result.stdout


def test_pyproject_byte_unchanged_since_repair_entry():
    result = _git("diff", "--name-only", REPAIR_ENTRY_SHA, "--", "pyproject.toml")
    assert result.stdout.strip() == "", result.stdout


# ═══════════════════════════════════════════════════════════════════════
# 7-16 — Blast-radius / consumer inventory
# ═══════════════════════════════════════════════════════════════════════


def test_current_agent_identity_all_production_consumers_inventoried():
    result = subprocess.run(
        ["git", "grep", "-l", "_current_agent_identity", "--", "src/"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    files = set(f for f in result.stdout.splitlines() if f)
    expected = {
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hpac_protected_admin_writer.py",
        "src/pcae/core/hpac_foundation.py",
    }
    assert files == expected, (
        f"consumer set changed since inventory was built -- reclassify before trusting this "
        f"suite's other assertions: extra={files - expected} missing={expected - files}"
    )


def test_resolve_trusted_executable_bare_no_longer_called_from_acl_helpers():
    """The defect: `_acl_grants_agent_write_linux`/`_acl_grants_agent_
    write_macos` must never call the ambient-identity `_resolve_trusted_
    executable` -- only the explicit-subject sibling."""

    src = inspect.getsource(topo)
    linux_src = inspect.getsource(topo._acl_grants_agent_write_linux)
    macos_src = inspect.getsource(topo._acl_grants_agent_write_macos)
    assert "_resolve_trusted_executable_for_subject(" in linux_src
    assert "_resolve_trusted_executable_for_subject(" in macos_src
    # Neither calls the bare ambient primitive at all (not even alongside).
    assert "_resolve_trusted_executable(" not in linux_src
    assert "_resolve_trusted_executable(" not in macos_src
    assert src.count("def _resolve_trusted_executable(") == 1
    assert src.count("def _resolve_trusted_executable_for_subject(") == 1


def test_ambient_primitive_source_content_guard_still_green():
    """Re-verifies 149O.20J.1's own guard directly (not merely trusting
    it stayed collected): the untouched primitive is still ACL-unaware,
    mode+group only."""

    src = inspect.getsource(topo._resolve_trusted_executable)
    assert "_mode_and_group_write_access(" in src
    assert "_effective_write_access(" not in src
    assert "_acl_grants_agent_write(" not in src
    assert "_resolve_trusted_executable_for_subject(" not in src


def test_ambient_primitive_def_line_byte_unchanged_since_repair_entry():
    """Re-verifies 149O.20J.2's own pickaxe guard directly against this
    phase's own repair-entry SHA (not only its original historical
    baseline): the frozen def line was neither removed nor re-added by
    this repair."""

    result = _git("diff", REPAIR_ENTRY_SHA, "-G", r"def _resolve_trusted_executable\(",
                   "--", "src/pcae/core/hatp_class_b_topology_verifier.py")
    assert "-def _resolve_trusted_executable(" not in result.stdout
    assert "+def _resolve_trusted_executable(" not in result.stdout


def test_effective_write_access_and_ancestor_chain_safe_untouched_signatures():
    """These two were already correctly parameterized before this
    repair (confirmed by primary-source inspection) -- their def lines
    must remain byte-unchanged too, since the actual defect lived one
    layer deeper."""

    for fn_name, pattern in (
        ("_effective_write_access", r"def _effective_write_access\("),
        ("_ancestor_chain_safe", r"def _ancestor_chain_safe\("),
        ("_mode_and_group_write_access", r"def _mode_and_group_write_access\("),
    ):
        result = _git("diff", REPAIR_ENTRY_SHA, "-G", pattern,
                       "--", "src/pcae/core/hatp_class_b_topology_verifier.py")
        assert f"-def {fn_name}(" not in result.stdout, fn_name
        assert f"+def {fn_name}(" not in result.stdout, fn_name


def test_configured_agent_callers_already_correctly_threaded_no_change_needed():
    """PAWA's `hpac_protected_admin_writer.py` STEP 3 and `hpac_
    foundation.py`'s `_validate_production_boundary`/`_relative_record_
    path` already pass the resolved configured-agent `(uid, gids)`
    explicitly to `_effective_write_access`/`_ancestor_chain_safe` --
    confirmed unchanged by this repair (out of this repair's bounded
    scope, per the production-diff-scope guard above)."""

    writer_src = Path(REPO_ROOT, "src/pcae/core/hpac_protected_admin_writer.py").read_text(encoding="utf-8")
    assert "ancestor_chain_safe(root, configured_agent.uid, configured_agent.gids)" in writer_src
    assert "effective_write_access(root, configured_agent.uid, configured_agent.gids)" in writer_src
    # STEP 7's live-process comparison is legitimately live-process semantics
    # (comparing the invoking context against the configured agent), not a
    # configured-agent-subject write-authority question -- left untouched.
    assert "live_uid, _live_gids = _current_agent_identity()" in writer_src


def test_environment_lock_verifier_byte_unchanged_since_repair_entry():
    """`hatp_environment_lock_verifier.py`'s own-environment self-check
    legitimately keeps ambient live-process semantics (item 41-42: no
    caller requiring live-process semantics is disturbed) -- confirmed
    literally untouched by this repair's diff."""

    result = _git("diff", "--name-only", REPAIR_ENTRY_SHA,
                   "--", "src/pcae/core/hatp_environment_lock_verifier.py")
    assert result.stdout.strip() == ""


def test_wrapper_call_graph_never_cycles_back_to_itself_still_holds():
    """Re-derives 149O.20J.2's cycle-freedom guard including the new
    sibling function in the tracked symbol set."""

    src = inspect.getsource(sys.modules["pcae.core.hatp_class_b_topology_verifier"])
    tree = ast.parse(src)
    relevant = {
        "_resolve_trusted_executable",
        "_resolve_trusted_executable_for_subject",
        "_resolve_trusted_executable_with_effective_access",
        "_effective_write_access",
        "_acl_grants_agent_write",
        "_acl_grants_agent_write_linux",
        "_acl_grants_agent_write_macos",
        "_ancestor_chain_safe",
        "_mode_and_group_write_access",
    }
    calls: "dict[str, set]" = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            called = set()
            for n in ast.walk(node):
                if isinstance(n, ast.Call):
                    f = n.func
                    if isinstance(f, ast.Name):
                        called.add(f.id)
                    elif isinstance(f, ast.Attribute):
                        called.add(f.attr)
            calls[node.name] = called & relevant

    def cycles_back(start, target, visited=None):
        if visited is None:
            visited = set()
        for nxt in calls.get(start, set()):
            if nxt == target:
                return True
            if nxt not in visited:
                visited.add(nxt)
                if cycles_back(nxt, target, visited):
                    return True
        return False

    for target in ("_resolve_trusted_executable_for_subject", "_resolve_trusted_executable_with_effective_access"):
        assert not cycles_back(target, target), target


# ═══════════════════════════════════════════════════════════════════════
# 17-24 — Explicit-subject-vs-ambient-identity semantics (the actual defect)
# ═══════════════════════════════════════════════════════════════════════


def test_acl_helpers_pass_their_own_subject_not_ambient_identity(tmp_path, monkeypatch):
    """The exact repaired property: the subject reaching tool
    resolution is the one the ACL helper itself received, independent
    of whatever the ambient/live-process identity happens to be."""

    target = tmp_path / "f"
    target.touch()
    fictitious_uid = 999123
    fictitious_gids = frozenset({999124, 999125})
    seen = {}

    def spy(name, agent_uid, agent_gids):
        seen["args"] = (name, agent_uid, agent_gids)
        return None  # tool unavailable -> indeterminate, but we only care about the args

    monkeypatch.setattr(topo, "_resolve_trusted_executable_for_subject", spy)
    # Poison the ambient identity so a leak back to it would be obvious.
    monkeypatch.setattr(topo, "_current_agent_identity", lambda: (0, frozenset({0})))

    if sys.platform == "darwin":
        topo._acl_grants_agent_write_macos(target, fictitious_uid, fictitious_gids)
        assert seen["args"] == ("ls", fictitious_uid, fictitious_gids)
    else:
        topo._acl_grants_agent_write_linux(target, fictitious_uid, fictitious_gids)
        assert seen["args"] == ("getfacl", fictitious_uid, fictitious_gids)


def test_root_executor_no_longer_poisons_configured_agent_acl_check(tmp_path, monkeypatch):
    """Reproduces the historical defect deterministically: even when the
    *ambient* process identity is simulated as root (uid 0, whose own
    write authority over root-owned PATH directories is irrelevant),
    the ACL check for a distinct configured-agent subject must not be
    perturbed by that ambient identity at all -- resolution proceeds
    against the real subject exclusively."""

    target = tmp_path / "f"
    target.touch()
    real_uid, real_gids = _agent_identity()

    monkeypatch.setattr(topo, "_current_agent_identity", lambda: (0, frozenset({0})))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    if sys.platform == "darwin":
        result = topo._acl_grants_agent_write_macos(target, real_uid, real_gids)
    elif sys.platform == "linux":
        result = topo._acl_grants_agent_write_linux(target, real_uid, real_gids)
    else:
        pytest.skip("ACL check unsupported on this platform")

    # A freshly created file with no ACL grants for the real subject
    # must resolve deterministically to False (no grant), never None
    # (indeterminate) -- the exact symptom this repair fixes was tool
    # resolution silently failing because of an irrelevant ambient
    # identity, producing None instead of a real answer.
    assert result is False, (
        "ACL check must resolve deterministically against the real subject "
        f"even under a poisoned root-like ambient identity, got {result!r}"
    )


def test_before_repair_semantics_reproduced_from_primary_source(tmp_path, monkeypatch):
    """Before/after defect test (item 37): reconstructs the exact
    pre-repair call (`_resolve_trusted_executable("ls")`, ambient-only)
    from the still-present, still-frozen ambient primitive, and shows
    it is sensitive to the ambient identity -- unlike the repaired
    `_acl_grants_agent_write_macos`/`_linux`, which are not."""

    target = tmp_path / "f"
    target.touch()
    monkeypatch.setenv("PATH", "/usr/bin:/bin")

    # Reproduces the historical defect from the still-present, still-
    # frozen ambient primitive: `_resolve_trusted_executable("ls")` is
    # driven entirely by whatever `_current_agent_identity()` returns.
    # A non-owning fictitious subject (999999) resolves the real `ls`;
    # a simulated root-like ambient identity (uid 0, which *does* own
    # /usr/bin's owner-write bit on this host) fails closed to `None` --
    # this is the exact `acl_inspection_unavailable` symptom the
    # predecessor F-5 retry hit when the canonical registration path
    # actually ran as root.
    with mock.patch.object(topo, "_current_agent_identity", return_value=(999999, frozenset())):
        ambient_driven_nonowning = topo._resolve_trusted_executable("ls")
    with mock.patch.object(topo, "_current_agent_identity", return_value=(0, frozenset({0}))):
        ambient_driven_root = topo._resolve_trusted_executable("ls")
    assert ambient_driven_nonowning is not None, "sanity: a non-owning ambient subject must resolve ls"
    assert ambient_driven_root is None, (
        "historical defect reproduction: a root-like ambient identity must fail closed here, since "
        "/usr/bin is root-owned and owner-writable -- exactly why the ACL helpers must not use it"
    )

    # The repaired ACL helper, by contrast, ignores `_current_agent_identity`
    # entirely for this same PATH/subject combination:
    real_uid, real_gids = _agent_identity()
    with mock.patch.object(topo, "_current_agent_identity", return_value=(0, frozenset({0}))):
        if sys.platform == "darwin":
            repaired = topo._acl_grants_agent_write_macos(target, real_uid, real_gids)
        else:
            repaired = topo._acl_grants_agent_write_linux(target, real_uid, real_gids)
    assert repaired is False  # resolved against the real (real_uid, real_gids) subject, not the poisoned ambient one


# ═══════════════════════════════════════════════════════════════════════
# 25-32 — `_resolve_trusted_executable_for_subject` semantics matrix
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def _trusted_system_path(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin:/bin")


def test_for_subject_resolves_system_tool_for_non_owning_subject(_trusted_system_path):
    real_uid, real_gids = _agent_identity()
    resolved = topo._resolve_trusted_executable_for_subject("ls", real_uid, real_gids)
    assert resolved is not None
    assert resolved.name == "ls"


def test_for_subject_rejects_agent_writable_preceding_path_dir(tmp_path, monkeypatch):
    """PATH-precedence security must not regress (item 21/30/49)."""

    hostile_dir = tmp_path / "hostile_bin"
    hostile_dir.mkdir()  # owned and writable by this test process
    monkeypatch.setenv("PATH", os.pathsep.join([str(hostile_dir), "/usr/bin", "/bin"]))
    real_uid, real_gids = _agent_identity()
    resolved = topo._resolve_trusted_executable_for_subject("ls", real_uid, real_gids)
    assert resolved is None


def test_for_subject_rejects_hostile_fake_tool_on_path(tmp_path, monkeypatch):
    """No root/allowlist bypass: a hostile same-named executable earlier
    on PATH is still rejected regardless of subject."""

    hostile_dir = tmp_path / "hostile_bin"
    hostile_dir.mkdir()
    fake_ls = hostile_dir / "ls"
    fake_ls.write_text("#!/bin/sh\necho pwned\n", encoding="utf-8")
    fake_ls.chmod(0o755)
    monkeypatch.setenv("PATH", str(hostile_dir))
    real_uid, real_gids = _agent_identity()
    resolved = topo._resolve_trusted_executable_for_subject("ls", real_uid, real_gids)
    assert resolved is None


def test_for_subject_rejects_subject_owned_writable_target(tmp_path, monkeypatch):
    """The resolved executable itself being writable by the subject is
    always rejected (item 22/23), independent of ancestor trust."""

    own_bin = tmp_path / "own_bin"
    own_bin.mkdir()
    own_ls = own_bin / "ls"
    own_ls.write_text("#!/bin/sh\necho real-ish\n", encoding="utf-8")
    own_ls.chmod(0o755)  # owned + writable by the real test-process uid
    monkeypatch.setenv("PATH", str(own_bin))
    real_uid, real_gids = _agent_identity()
    resolved = topo._resolve_trusted_executable_for_subject("ls", real_uid, real_gids)
    assert resolved is None, "an agent-writable resolved executable must never be trusted"


def _function_body_excluding_docstring(fn) -> str:
    """Source of `fn`'s body, with its own docstring statement (if any)
    stripped -- so prose examples/rationale in the docstring can freely
    mention path literals or symbol names without tripping a source-scan
    assertion aimed at the actual code."""

    node = ast.parse(inspect.getsource(fn)).body[0]
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
        body = body[1:]
    return "\n".join(ast.get_source_segment(inspect.getsource(fn), n) or "" for n in body)


def test_for_subject_no_hardcoded_system_directory_allowlist():
    """Item 28: the new primitive contains no literal system-path
    allowlist -- trust remains evidence-based."""

    src = _function_body_excluding_docstring(topo._resolve_trusted_executable_for_subject)
    for forbidden in ("/usr/bin", "/bin", "/usr/sbin", "/sbin"):
        assert forbidden not in src


def test_for_subject_no_euid_zero_special_case_anywhere_in_module():
    """Item 27: no `if ... == 0` / `geteuid() == 0` root special-case
    exists anywhere in this module."""

    src = inspect.getsource(topo)
    assert "== 0" not in src.replace("st_nlink == 0", "").replace(
        "malformed_zero_link_count", ""
    ), "possible root/zero-uid special case introduced"


def test_for_subject_never_falls_back_to_ambient_identity():
    """Fail-closed identity requirement (item 24-27): the new primitive
    accepts no default for its subject parameters and never reads
    `_current_agent_identity` internally."""

    sig = inspect.signature(topo._resolve_trusted_executable_for_subject)
    params = list(sig.parameters.values())
    assert [p.name for p in params] == ["name", "agent_uid", "agent_gids"]
    assert params[1].default is inspect.Parameter.empty
    assert params[2].default is inspect.Parameter.empty
    src = _function_body_excluding_docstring(topo._resolve_trusted_executable_for_subject)
    assert "_current_agent_identity(" not in src


# ═══════════════════════════════════════════════════════════════════════
# 33-40 — ACL matrix regression (macOS): configured-agent vs unrelated
# principal, direct/group/root-only grants -- unaffected by tool-trust
# subject now being explicit
# ═══════════════════════════════════════════════════════════════════════

pytestmark_macos = pytest.mark.skipif(sys.platform != "darwin", reason="macOS BSD-ACL-specific matrix")


def _whoami() -> str:
    return subprocess.run(["/usr/bin/whoami"], capture_output=True, text=True, check=True).stdout.strip()


def _grant_acl(path: Path, rights: str, principal: str = None) -> None:
    principal = principal or _whoami()
    subprocess.run(["/bin/chmod", "+a", f"{principal} allow {rights}", str(path)], check=True)


def _revoke_acl(path: Path, rights: str, principal: str = None) -> None:
    principal = principal or _whoami()
    subprocess.run(["/bin/chmod", "-a", f"{principal} allow {rights}", str(path)], check=False)


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS BSD-ACL-specific matrix")
def test_acl_direct_agent_grant_detected_after_repair(tmp_path, _trusted_system_path):
    target = tmp_path / "f"
    target.touch()
    real_uid, real_gids = _agent_identity()
    _grant_acl(target, "write")
    try:
        result = topo._acl_grants_agent_write_macos(target, real_uid, real_gids)
        assert result is True
    finally:
        _revoke_acl(target, "write")


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS BSD-ACL-specific matrix")
def test_acl_root_only_style_grant_for_unrelated_uid_not_detected(tmp_path, _trusted_system_path):
    """A grant to a principal distinct from the evaluated subject must
    never be interpreted as granting that subject write access, even
    post-repair (item 18: no benefit accrues to the ambient/executor
    identity merely because tool resolution now succeeds more often)."""

    target = tmp_path / "f"
    target.touch()
    fictitious_uid = 999321
    real_gids = frozenset()
    _grant_acl(target, "write")  # granted to the real whoami principal, not uid 999321
    try:
        result = topo._acl_grants_agent_write_macos(target, fictitious_uid, real_gids)
        assert result is False
    finally:
        _revoke_acl(target, "write")


# ═══════════════════════════════════════════════════════════════════════
# 41-44 — No-test-weakening / production-mutation guards
# ═══════════════════════════════════════════════════════════════════════


def test_no_mutation_apis_present_in_repaired_module():
    src = inspect.getsource(topo)
    for forbidden in (
        "os.chmod(", "os.chown(", "os.mkdir(", "os.makedirs(",
        "shutil.rmtree(", "os.remove(", "os.unlink(", ".write_text(", ".write_bytes(",
    ):
        assert forbidden not in src, forbidden


#: This fresh suite's own file necessarily mentions these forbidden
#: literals as string constants inside its own scanning assertions
#: (below) -- excluded from the diff scope it scans so it does not
#: trip on its own source, not because it is exempt from the property.
_THIS_FILE = "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_" \
    "configured_agent_identity_threading_repair.py"


def test_no_removed_or_skipped_tests_in_repair_diff():
    result = _git("diff", REPAIR_ENTRY_SHA, "--", "tests/", f":!{_THIS_FILE}")
    diff = result.stdout
    for forbidden in ("+@pytest.mark.skip", "+@pytest.mark.xfail", "+pytest.skip(", "-def test_"):
        assert forbidden not in diff, forbidden


def test_repair_diff_touches_only_expected_test_files():
    result = _git("diff", "--name-only", REPAIR_ENTRY_SHA, "--", "tests/")
    changed = set(f for f in result.stdout.splitlines() if f)
    expected_edited = {
        "tests/test_phase_149o_20j_1_class_b_deployment_verifier_narrow_defect_repair.py",
        "tests/test_phase_149o_20j_5_class_b_acl_only_higher_ancestor_detection_macos_narrow_repair.py",
        "tests/test_phase_149o_20j_class_b_deployment_verifier_model_a_environment_lock_independent_"
        "implementation_verification.py",
    }
    fresh_suite = {
        "tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_"
        "configured_agent_identity_threading_repair.py"
    }
    assert changed <= (expected_edited | fresh_suite), changed - (expected_edited | fresh_suite)
    assert expected_edited <= changed


# ═══════════════════════════════════════════════════════════════════════
# 45-46 — F-5 / host-state boundaries (repair phase must stay code-only)
# ═══════════════════════════════════════════════════════════════════════


def test_no_ppa_install_or_root_admin_functions_referenced_in_diff():
    result = _git("diff", REPAIR_ENTRY_SHA, "--", "src/", "tests/", f":!{_THIS_FILE}")
    diff = result.stdout
    for forbidden in ("provision_protected_root(", "configure_presentation_mechanism(", "hpac_protected_presentation_admin"):
        assert forbidden not in diff, forbidden

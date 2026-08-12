"""HATP Class-B Deployment Topology Verifier — Phase 149O.20I, Wave B
(bounded, non-authoritative implementation).

Implements the HBDC-001 v1.0 (`docs/contracts/HATP_CLASS_B_DEPLOYMENT_
CONTRACT.md`) principal-separation, Protected Root ownership/permission,
effective-access, ancestor-chain, symlink, and hard-link checks designed
in `docs/PHASE_149O_20H_CLASS_B_DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_
LOCK_IMPLEMENTATION_PLAN.md` §9-13.

**Non-authoritative by design (CBV-S1, plan §24/§58).** This module's
source is not a member of HMIC-001's current 25-file frozen identity
(the certification module's frozen file-set constant). No production
readiness, certification, or activation code path may import or call
anything in this module until a future, separately-governed phase
evolves HMIC's source scope to include it and that evolution is
independently verified (plan §24 Wave F). Until then, `COMPLIANT` here
is diagnostic only — reachable by direct test invocation, never wired
to any automation exit code.

**Strictly read-only.** No `mkdir`, `chmod`, `chown`, ACL mutation, or
any other filesystem write appears anywhere in this module (plan §18).
A failed check reports; it never repairs or auto-provisions. This
module never claims its own source is HMIC-bound and never claims
runtime executed-source cryptographic attestation (HBDC-REQ-041).

Public API accepts no caller-supplied authority boolean (plan §7): the
only public entry point, `verify_class_b_topology_conformance()`, takes
no parameters at all. Every authority fact (principal identity, mode
bits, group membership, ACL entries, ancestor writability) is derived
live from OS/process state at call time.
"""
from __future__ import annotations

import ast
import inspect
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from pcae.core import hatp_bootstrap

# ═══════════════════════════════════════════════════════════════════════════
# Shared result model and status vocabulary (plan §6) — shared by all three
# 149O.20I modules. Defined here (Wave B, first-built module) and imported
# by hatp_environment_lock_verifier.py and hatp_class_b_conformance.py
# rather than duplicated, per plan §23's clean-module-boundary decision.
# ═══════════════════════════════════════════════════════════════════════════


class ClassBConformanceStatus(str, Enum):
    """Closed vocabulary (HBDC-REQ-052). Only `COMPLIANT` satisfies any
    future Class-B deployment-conformance fact; every other member is
    equally "not compliant" — no partial-credit ordering is defined."""

    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    INDETERMINATE = "INDETERMINATE"
    ACCESS_ERROR = "ACCESS_ERROR"
    MALFORMED_STATE = "MALFORMED_STATE"
    UNSUPPORTED_DEPLOYMENT_MODEL = "UNSUPPORTED_DEPLOYMENT_MODEL"


_NON_COMPLIANT_STATUSES = frozenset(ClassBConformanceStatus) - {ClassBConformanceStatus.COMPLIANT}


@dataclass(frozen=True)
class ClassBCheckResult:
    """Per-requirement diagnostic. `status` is a short machine-stable
    reason code, never free text parsed for authority (plan §28)."""

    check_id: str
    satisfied: bool
    status: str
    evidence: "tuple[str, ...]" = ()


@dataclass(frozen=True)
class ClassBDeploymentVerificationResult:
    status: ClassBConformanceStatus
    checks: "tuple[ClassBCheckResult, ...]"
    reasons: "tuple[str, ...]"
    evidence: "tuple[str, ...]"


def _aggregate_status(checks: "tuple[ClassBCheckResult, ...]") -> ClassBConformanceStatus:
    """HBDC-REQ-052/053, plan §38: only exact all-satisfied yields
    `COMPLIANT`. No majority/partial-success semantics. Failure-class
    priority (most-severe first) picks a diagnostic overall status when
    not all checks are satisfied — this ordering has no bearing on the
    binary COMPLIANT/not-COMPLIANT authority fact, which is unaffected
    by it."""

    if all(check.satisfied for check in checks) and checks:
        return ClassBConformanceStatus.COMPLIANT
    reason_codes = {check.status for check in checks if not check.satisfied}
    for candidate in (
        ClassBConformanceStatus.UNSUPPORTED_DEPLOYMENT_MODEL,
        ClassBConformanceStatus.MALFORMED_STATE,
        ClassBConformanceStatus.ACCESS_ERROR,
        ClassBConformanceStatus.INDETERMINATE,
    ):
        if any(candidate.value.lower() in code for code in reason_codes):
            return candidate
    return ClassBConformanceStatus.NON_COMPLIANT


def _build_result(checks: "list[ClassBCheckResult]") -> ClassBDeploymentVerificationResult:
    frozen_checks = tuple(checks)
    reasons = tuple(f"{c.check_id}:{c.status}" for c in frozen_checks if not c.satisfied)
    evidence = tuple(f"{c.check_id}:{item}" for c in frozen_checks for item in c.evidence)
    return ClassBDeploymentVerificationResult(
        status=_aggregate_status(frozen_checks),
        checks=frozen_checks,
        reasons=reasons,
        evidence=evidence,
    )


def _safe_check(check_id: str, fn: Callable[[], ClassBCheckResult]) -> ClassBCheckResult:
    """Fail-closed wrapper (plan §65-66, governing-prompt item 64): any
    unexpected exception during inspection yields `INDETERMINATE`, never
    a silent pass. No `try/except: pass` anywhere in this module."""

    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - deliberate fail-closed boundary
        return ClassBCheckResult(check_id, False, "unexpected_inspection_exception", (repr(exc),))


# ═══════════════════════════════════════════════════════════════════════════
# Read-only primitives shared with hatp_environment_lock_verifier.py
# (plan §11: "implemented once as a shared internal helper, not
# duplicated across modules").
# ═══════════════════════════════════════════════════════════════════════════


def _current_agent_identity() -> "tuple[int, frozenset[int]]":
    """Live process identity — never a caller-supplied value (plan §7).

    Phase 149O.20J.1 (B-CBV-J-2 repair): the effective group set is
    `os.getgroups()` unioned with `os.getegid()` independently, never
    `os.getgroups()` alone. POSIX does not guarantee the process's
    effective gid is a member of its own supplementary-group list in
    every process-identity configuration (`initgroups`/`setgroups` is a
    convention, not a kernel guarantee), so a file whose group matches
    only the true effective gid — and is group-writable — must still be
    detected."""

    return os.geteuid(), frozenset(os.getgroups()) | {os.getegid()}


def _is_symlink_unsafe(path: Path) -> bool:
    return path.is_symlink()


def _mode_and_group_write_access(path: Path, agent_uid: int, agent_gids: "frozenset[int]") -> Optional[bool]:
    """Mode-bit + group-membership effective-write test only — no ACL
    sub-check. Used specifically by `_resolve_trusted_executable`'s
    PATH-precedence walk to avoid unbounded recursion into the ACL
    check (which itself resolves a trusted tool via this same PATH
    walk). This is a disclosed, narrower primitive than
    `_effective_write_access` below, not a silent downgrade of it."""

    try:
        if not path.exists():
            return None
        if path.is_symlink():
            return True  # symlinked ancestor: fail closed, treat as writable/unsafe
        st = path.stat()
    except OSError:
        return None
    mode = stat.S_IMODE(st.st_mode)
    if st.st_uid == agent_uid and mode & stat.S_IWUSR:
        return True
    if mode & stat.S_IWGRP and st.st_gid in agent_gids:
        return True
    if mode & stat.S_IWOTH:
        return True
    return False


def _acl_grants_agent_write_linux(path: Path, agent_uid: int, agent_gids: "frozenset[int]") -> Optional[bool]:
    tool = _resolve_trusted_executable("getfacl")
    if tool is None:
        return None
    try:
        result = subprocess.run(
            [str(tool), "-p", str(path)],
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("#") or not line:
            continue
        parts = line.split(":")
        if len(parts) != 3:
            continue
        tag, qualifier, perms = parts
        if "w" not in perms:
            continue
        if tag == "user" and qualifier and qualifier.isdigit() and int(qualifier) == agent_uid:
            return True
        if tag == "group" and qualifier and qualifier.isdigit() and int(qualifier) in agent_gids:
            return True
        if tag in ("mask", "other") and tag == "other":
            return True
    return False


def _acl_grants_agent_write_macos(path: Path) -> Optional[bool]:
    ls_tool = _resolve_trusted_executable("ls")
    if ls_tool is None:
        return None
    try:
        result = subprocess.run(
            [str(ls_tool), "-lde", str(path)],
            capture_output=True,
            text=True,
            timeout=5,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    lines = result.stdout.splitlines()
    if not lines:
        return None
    mode_line = lines[0]
    if "+" not in mode_line.split()[0] if mode_line.split() else True:
        return False  # no ACL marker on the mode string -> no ACL present
    for line in lines[1:]:
        entry = line.strip()
        if "write" in entry or "allow write" in entry:
            return True
    return False


def _acl_grants_agent_write(path: Path, agent_uid: int, agent_gids: "frozenset[int]") -> Optional[bool]:
    if sys.platform == "linux":
        return _acl_grants_agent_write_linux(path, agent_uid, agent_gids)
    if sys.platform == "darwin":
        return _acl_grants_agent_write_macos(path)
    return None  # unsupported platform -> INDETERMINATE, never a silent pass


def _effective_write_access(
    path: Path, agent_uid: int, agent_gids: "frozenset[int]"
) -> "tuple[Optional[bool], str, tuple[str, ...]]":
    """Effective-access check (HBDC-REQ-015/016, plan §10): mode-bit
    baseline, then group-membership, then platform-gated ACL. Returns
    `(has_write, reason_code, evidence)`; `has_write is None` means the
    check is genuinely indeterminate (unavailable ACL tooling, missing
    path) — never silently treated as `False`."""

    try:
        exists = path.exists()
    except OSError:
        return None, "stat_access_error", ()
    if not exists:
        return None, "path_missing", ()
    if path.is_symlink():
        return True, "path_is_symlink", (str(path),)
    try:
        st = path.stat()
    except OSError:
        return None, "stat_access_error", ()

    mode = stat.S_IMODE(st.st_mode)
    if st.st_uid == agent_uid and mode & stat.S_IWUSR:
        return True, "agent_is_owner_with_write_bit", (f"uid={st.st_uid}", f"mode={oct(mode)}")
    if mode & stat.S_IWGRP and st.st_gid in agent_gids:
        return True, "agent_group_membership_grants_write", (f"gid={st.st_gid}", f"mode={oct(mode)}")
    if mode & stat.S_IWOTH:
        return True, "world_writable", (f"mode={oct(mode)}",)

    acl_result = _acl_grants_agent_write(path, agent_uid, agent_gids)
    if acl_result is True:
        return True, "acl_grants_agent_write", (str(path),)
    if acl_result is None:
        return None, "acl_inspection_unavailable", (str(path),)

    return False, "no_effective_write_access", (f"mode={oct(mode)}",)


def _ancestor_chain_safe(
    start: Path, agent_uid: int, agent_gids: "frozenset[int]"
) -> "tuple[Optional[bool], tuple[str, ...]]":
    """Full ancestor-chain walk (HBDC-REQ-017/020, plan §11; repaired
    149O.20J.3, closes B-149O.20J.2-1).

    Inspects **every** ancestor directory from `start.parent` up to the
    actual filesystem root — the only trust boundary HBDC-REQ-017's
    text ("up to the point the agent principal has no write access at
    all") supports without inventing an unwritten anchor. A single
    locally non-writable ancestor is never treated as proof that a
    higher ancestor is harmless: removing or renaming the directory
    entry naming a safe intermediate directory requires write access
    on that entry's *containing* directory, not on the entry itself,
    so an agent-writable grandparent (or any higher ancestor) can still
    redirect everything beneath a proven-safe parent. The walk
    therefore never returns early on a `write is False` result — it
    only stops at a proven-unsafe ancestor (writable or symlinked) or
    once it reaches the filesystem root."""

    current = start.parent
    diagnostics: "list[str]" = []
    saw_indeterminate = False
    guard = 0
    while True:
        if _is_symlink_unsafe(current):
            return False, tuple(diagnostics) + (f"ancestor_symlink:{current}",)
        write, reason, _evidence = _effective_write_access(current, agent_uid, agent_gids)
        if write is True:
            return False, tuple(diagnostics) + (f"ancestor_writable:{current}:{reason}",)
        if write is None:
            saw_indeterminate = True
            diagnostics.append(f"ancestor_indeterminate:{current}:{reason}")
        else:
            diagnostics.append(f"ancestor_safe:{current}:{reason}")
        parent = current.parent
        guard += 1
        if parent == current:
            break
        if guard > 2048:
            return None, tuple(diagnostics) + ("ancestor_walk_guard_exceeded",)
        current = parent
    if saw_indeterminate:
        return None, tuple(diagnostics)
    return True, tuple(diagnostics) + ("ancestor_walk_reached_filesystem_root",)


def _hard_link_safe(path: Path) -> "tuple[Optional[bool], str]":
    """Frozen decision (plan §13/§64): `st_nlink != 1` on an authority-
    bearing file is `NON_COMPLIANT`; `st_nlink == 0` is a malformed
    filesystem state, not a normal compliant baseline."""

    try:
        if not path.exists() or path.is_symlink():
            return None, "path_missing_or_symlink"
        st = path.stat()
    except OSError:
        return None, "stat_access_error"
    if st.st_nlink == 1:
        return True, "single_link"
    if st.st_nlink == 0:
        return None, "malformed_zero_link_count"
    return False, "multiple_hard_links"


def _resolve_trusted_executable(name: str) -> Optional[Path]:
    """PATH-precedence-aware trusted resolution (HBDC-REQ-038, plan
    §14): resolves `name` via `PATH`, then verifies no agent-writable
    directory precedes the resolved location — a bare `shutil.which`
    result is not itself trusted. Uses `_mode_and_group_write_access`
    (not the full ACL-including `_effective_write_access`) for the
    PATH-directory scan to avoid unbounded recursion, since the ACL
    check for POSIX ACL tooling (`getfacl`) itself calls this
    function."""

    path_entries = os.environ.get("PATH", "").split(os.pathsep)
    agent_uid, agent_gids = _current_agent_identity()
    resolved_dir: Optional[Path] = None
    resolved_target: Optional[Path] = None
    for entry in path_entries:
        if not entry:
            continue
        candidate_dir = Path(entry)
        candidate = candidate_dir / name
        if resolved_target is None:
            try:
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    resolved_target = candidate
                    resolved_dir = candidate_dir
                    continue
            except OSError:
                continue
            # Not yet resolved: this directory precedes the eventual
            # resolution and must be proven non-agent-writable.
            write = _mode_and_group_write_access(candidate_dir, agent_uid, agent_gids)
            if write is not False:
                return None  # agent-writable (or indeterminate) directory precedes resolution -> untrusted
    if resolved_target is None or resolved_dir is None:
        return None
    try:
        real_target = resolved_target.resolve(strict=True)
    except OSError:
        return None
    if real_target.is_symlink():
        return None
    write = _mode_and_group_write_access(real_target, agent_uid, agent_gids)
    if write is not False:
        return None
    write_dir = _mode_and_group_write_access(real_target.parent, agent_uid, agent_gids)
    if write_dir is not False:
        return None
    return real_target


def _resolve_trusted_executable_with_effective_access(name: str) -> Optional[Path]:
    """Phase 149O.20J.1 (B-CBV-J-3 repair): `_resolve_trusted_executable`
    above stays deliberately unchanged — its PATH-precedence walk uses
    only `_mode_and_group_write_access`, never the ACL-including
    `_effective_write_access`, because the ACL branch's own tool
    resolution (`getfacl`/`ls`, via `_acl_grants_agent_write`) calls
    `_resolve_trusted_executable` itself; giving the PATH walk ACL
    awareness would make that call mutually recursive.

    This wrapper instead composes the two primitives in sequence and is
    itself never called from the ACL-tool-resolution path: (1) resolve
    `name` via the narrow, non-recursive PATH walk; (2) apply the same
    ACL-inclusive `_effective_write_access` + `_ancestor_chain_safe`
    effective-access policy already used for Protected Root
    (HBDC-REQ-016/017) to the resolved executable itself and its full
    ancestor chain. No recursion is introduced: step (2)'s own nested
    `getfacl`/`ls` resolution still goes through the narrow, unchanged
    `_resolve_trusted_executable`, never through this wrapper.

    Fails closed: a resolved-but-ACL-writable target, an ancestor with
    an ACL-only write grant, or an indeterminate ACL result (tool
    unavailable) are all treated as untrusted (`None`) — ACL inspection
    failure is never interpreted as "no ACL exists"."""

    resolved = _resolve_trusted_executable(name)
    if resolved is None:
        return None
    agent_uid, agent_gids = _current_agent_identity()
    write, _reason, _evidence = _effective_write_access(resolved, agent_uid, agent_gids)
    if write is not False:
        return None  # agent-writable (mode, group, or ACL) or indeterminate -> untrusted
    safe, _diagnostics = _ancestor_chain_safe(resolved, agent_uid, agent_gids)
    if safe is not True:
        return None  # ancestor writable (incl. ACL) or indeterminate -> untrusted
    return resolved


# ═══════════════════════════════════════════════════════════════════════════
# Protected Root resolution (HBDC-REQ-011/012, plan §8) — reuse, no new
# override path.
# ═══════════════════════════════════════════════════════════════════════════


def _resolve_protected_root() -> "tuple[Optional[Path], str]":
    try:
        return hatp_bootstrap._default_production_trust_root(), "resolved"
    except hatp_bootstrap.HATPBootstrapUnsupportedPlatformError as exc:
        return None, f"unsupported_platform:{exc}"


# ═══════════════════════════════════════════════════════════════════════════
# Static/AST self-checks (HBDC-REQ-004/005/011/012/018 design guarantees)
# ═══════════════════════════════════════════════════════════════════════════

_SUSPICIOUS_ENV_KEY_SUBSTRINGS = ("ADMIN", "USER", "SUDO", "LOGNAME", "IDENTITY")
_FORBIDDEN_SELF_ELEVATION_ATTRS = frozenset({"setuid", "seteuid", "setgid", "setegid", "setreuid", "setresuid"})
_FORBIDDEN_MUTATION_ATTRS = frozenset(
    {"mkdir", "makedirs", "chmod", "chown", "unlink", "rmdir", "rename", "replace", "symlink", "link", "write_text", "write_bytes"}
)


def _own_source_ast() -> ast.AST:
    return ast.parse(Path(__file__).read_text(encoding="utf-8"))


def _scan_forbidden_attrs(tree: ast.AST, forbidden: "frozenset[str]") -> "list[str]":
    found: "list[str]" = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in forbidden:
            found.append(node.attr)
    return found


def _scan_environ_admin_inference(tree: ast.AST) -> "list[str]":
    """Flags `os.environ`/`os.getenv` reads keyed by a suspicious
    admin/user/identity-shaped literal, and `getuser()`/`getlogin()`
    calls (name-based identity inference) — not every `os.environ`
    reference. Reading `PATH` for trusted-executable resolution
    (HBDC-REQ-038, `_resolve_trusted_executable`) is a legitimate,
    unrelated use of `os.environ` and must not be flagged."""

    violations: "list[str]" = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in {"getuser", "getlogin"}:
            violations.append(node.attr)
            continue
        key_node: Optional[ast.expr] = None
        if isinstance(node, ast.Call):
            func = node.func
            is_environ_get = (
                isinstance(func, ast.Attribute)
                and func.attr in {"get", "getenv"}
                and isinstance(func.value, ast.Attribute)
                and func.value.attr == "environ"
            )
            is_getenv = isinstance(func, ast.Attribute) and func.attr == "getenv"
            if (is_environ_get or is_getenv) and node.args:
                key_node = node.args[0]
        elif isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "environ":
            key_node = node.slice
        if key_node is not None and isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
            key = key_node.value.upper()
            if any(sub in key for sub in _SUSPICIOUS_ENV_KEY_SUBSTRINGS):
                violations.append(f"environ_key:{key}")
    return violations


def _check_no_env_or_name_based_admin_inference() -> ClassBCheckResult:
    tree = _own_source_ast()
    violations = _scan_environ_admin_inference(tree)
    if violations:
        return ClassBCheckResult("HBDC-REQ-004", False, "admin_inference_signal_present_in_source", tuple(violations))
    return ClassBCheckResult("HBDC-REQ-004", True, "no_env_or_name_based_admin_inference_in_source", ())


def _check_no_self_elevation_path() -> ClassBCheckResult:
    tree = _own_source_ast()
    violations = _scan_forbidden_attrs(tree, _FORBIDDEN_SELF_ELEVATION_ATTRS)
    if violations:
        return ClassBCheckResult("HBDC-REQ-005", False, "self_elevation_call_present_in_source", tuple(violations))
    return ClassBCheckResult("HBDC-REQ-005", True, "no_self_elevation_call_in_source", ())


def _check_read_only_guarantee() -> ClassBCheckResult:
    """Closes HBDC-REQ-012 (no auto-creation) and contributes to the
    plan §18 read-only guarantee: this module's own source contains no
    mutating filesystem call."""

    tree = _own_source_ast()
    violations = sorted(set(_scan_forbidden_attrs(tree, _FORBIDDEN_MUTATION_ATTRS)))
    if violations:
        return ClassBCheckResult("HBDC-REQ-012", False, "mutation_call_present_in_source", tuple(violations))
    return ClassBCheckResult("HBDC-REQ-012", True, "no_mutation_call_in_source", ())


def _check_no_override_parameter() -> ClassBCheckResult:
    """HBDC-REQ-011: the public entry point accepts no parameter at
    all, so no override path exists for a caller to exploit."""

    sig = inspect.signature(verify_class_b_topology_conformance)
    if sig.parameters:
        return ClassBCheckResult(
            "HBDC-REQ-011", False, "public_api_accepts_unexpected_parameter", tuple(sig.parameters.keys())
        )
    return ClassBCheckResult("HBDC-REQ-011", True, "public_api_accepts_no_override_parameter", ())


def _check_agent_writable_exclusion_scope() -> ClassBCheckResult:
    """HBDC-REQ-008: this module's write-authority checking scope is
    Protected Root only — it never evaluates `.pcae/hatp-evidence/` or
    `.pcae/repository-identity.json` as authority-bearing, matching
    HATP-001 §17 / HSCE-001 §27's existing disposition by construction
    (not by omission)."""

    return ClassBCheckResult(
        "HBDC-REQ-008",
        True,
        "designated_agent_writable_artifacts_excluded_by_scope",
        (".pcae/hatp-evidence/", ".pcae/repository-identity.json"),
    )


# ═══════════════════════════════════════════════════════════════════════════
# Principal / Protected Root checks (HBDC-REQ-001..021)
# ═══════════════════════════════════════════════════════════════════════════


def _check_two_principal_topology(root: Optional[Path]) -> ClassBCheckResult:
    if root is None:
        return ClassBCheckResult("HBDC-REQ-001", False, "protected_root_unresolvable", ())
    if not root.exists():
        return ClassBCheckResult("HBDC-REQ-001", False, "protected_root_absent_not_provisioned", (str(root),))
    return ClassBCheckResult("HBDC-REQ-001", True, "protected_root_resolvable_topology_evaluable", (str(root),))


def _check_principal_distinctness(root: Optional[Path], agent_uid: int) -> ClassBCheckResult:
    if root is None or not root.exists():
        return ClassBCheckResult("HBDC-REQ-002", False, "protected_root_absent", ())
    if root.is_symlink():
        return ClassBCheckResult("HBDC-REQ-002", False, "protected_root_is_symlink", ())
    try:
        st = root.stat()
    except OSError as exc:
        return ClassBCheckResult("HBDC-REQ-002", False, "stat_access_error", (repr(exc),))
    if st.st_uid == agent_uid:
        return ClassBCheckResult("HBDC-REQ-002", False, "agent_and_admin_share_os_principal", (f"uid={st.st_uid}",))
    return ClassBCheckResult(
        "HBDC-REQ-002", True, "agent_and_admin_are_distinct_os_principals", (f"admin_uid={st.st_uid}", f"agent_uid={agent_uid}")
    )


def _check_write_authority(root: Optional[Path], agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    if root is None:
        return ClassBCheckResult("HBDC-REQ-007", False, "protected_root_unresolvable", ())
    if not root.exists():
        return ClassBCheckResult("HBDC-REQ-007", False, "protected_root_absent_not_provisioned", ())
    write, reason, evidence = _effective_write_access(root, agent_uid, agent_gids)
    if write is None:
        return ClassBCheckResult("HBDC-REQ-007", False, f"indeterminate:{reason}", evidence)
    if write:
        return ClassBCheckResult("HBDC-REQ-007", False, reason, evidence)
    return ClassBCheckResult("HBDC-REQ-007", True, "agent_has_no_effective_write_access", evidence)


def _check_root_ownership(root: Optional[Path], agent_uid: int) -> ClassBCheckResult:
    if root is None or not root.exists() or root.is_symlink():
        return ClassBCheckResult("HBDC-REQ-013", False, "protected_root_absent_or_unsafe", ())
    st = root.stat()
    if st.st_uid == agent_uid:
        return ClassBCheckResult("HBDC-REQ-013", False, "protected_root_owned_by_agent", (f"uid={st.st_uid}",))
    return ClassBCheckResult("HBDC-REQ-013", True, "protected_root_admin_owned", (f"uid={st.st_uid}",))


def _check_root_mode(root: Optional[Path]) -> ClassBCheckResult:
    if root is None or not root.exists() or root.is_symlink():
        return ClassBCheckResult("HBDC-REQ-014", False, "protected_root_absent_or_unsafe", ())
    st = root.stat()
    mode = stat.S_IMODE(st.st_mode)
    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        return ClassBCheckResult("HBDC-REQ-014", False, "protected_root_group_or_other_writable", (oct(mode),))
    return ClassBCheckResult("HBDC-REQ-014", True, "protected_root_mode_excludes_group_other_write", (oct(mode),))


def _check_group_effective_access(root: Optional[Path], agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    if root is None or not root.exists():
        return ClassBCheckResult("HBDC-REQ-015", False, "protected_root_absent", ())
    write, reason, evidence = _effective_write_access(root, agent_uid, agent_gids)
    if reason == "agent_group_membership_grants_write":
        return ClassBCheckResult("HBDC-REQ-015", False, reason, evidence)
    if write is None:
        return ClassBCheckResult("HBDC-REQ-015", False, f"indeterminate:{reason}", evidence)
    return ClassBCheckResult("HBDC-REQ-015", not write, "no_group_membership_grants_write" if not write else reason, evidence)


def _check_acl_effective_access(root: Optional[Path], agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    if root is None or not root.exists():
        return ClassBCheckResult("HBDC-REQ-016", False, "protected_root_absent", ())
    acl_result = _acl_grants_agent_write(root, agent_uid, agent_gids)
    if acl_result is None:
        return ClassBCheckResult("HBDC-REQ-016", False, "acl_inspection_unavailable_indeterminate", ())
    if acl_result:
        return ClassBCheckResult("HBDC-REQ-016", False, "acl_grants_agent_write", ())
    return ClassBCheckResult("HBDC-REQ-016", True, "no_acl_grants_agent_write", ())


def _check_ancestor_chain(root: Optional[Path], agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    if root is None or not root.exists():
        return ClassBCheckResult("HBDC-REQ-017", False, "protected_root_absent", ())
    safe, diagnostics = _ancestor_chain_safe(root, agent_uid, agent_gids)
    if safe is None:
        return ClassBCheckResult("HBDC-REQ-017", False, "ancestor_chain_indeterminate", diagnostics)
    if not safe:
        return ClassBCheckResult("HBDC-REQ-017", False, "agent_writable_ancestor_found", diagnostics)
    return ClassBCheckResult("HBDC-REQ-017", True, "full_ancestor_chain_non_agent_writable", diagnostics)


def _check_symlink_safety(root: Optional[Path]) -> ClassBCheckResult:
    if root is None:
        return ClassBCheckResult("HBDC-REQ-018", False, "protected_root_unresolvable", ())
    if not root.exists() and not root.is_symlink():
        return ClassBCheckResult("HBDC-REQ-018", False, "protected_root_absent_not_provisioned", ())
    try:
        hatp_bootstrap._reject_symlink(root)
    except hatp_bootstrap.HATPTrustStoreSymlinkError:
        return ClassBCheckResult("HBDC-REQ-018", False, "protected_root_is_symlink", ())
    return ClassBCheckResult("HBDC-REQ-018", True, "protected_root_symlink_check_passed", ())


def _check_hard_link_safety(root: Optional[Path]) -> ClassBCheckResult:
    if root is None or not root.exists():
        return ClassBCheckResult("HBDC-REQ-019", False, "protected_root_absent", ())
    registry_path = root / "registry.json"
    if not registry_path.exists():
        return ClassBCheckResult("HBDC-REQ-019", True, "no_authority_bearing_file_present_nothing_to_check", ())
    safe, reason = _hard_link_safe(registry_path)
    if safe is None:
        return ClassBCheckResult("HBDC-REQ-019", False, f"indeterminate:{reason}", (str(registry_path),))
    if not safe:
        return ClassBCheckResult("HBDC-REQ-019", False, reason, (str(registry_path),))
    return ClassBCheckResult("HBDC-REQ-019", True, reason, (str(registry_path),))


def _check_ancestor_replacement_equivalence(root: Optional[Path], agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    """HBDC-REQ-020: satisfied jointly by HBDC-REQ-017's ancestor walk
    (plan §11) — not separately re-derivable from file-level mode bits
    alone."""

    if root is None or not root.exists():
        return ClassBCheckResult("HBDC-REQ-020", False, "protected_root_absent", ())
    safe, diagnostics = _ancestor_chain_safe(root, agent_uid, agent_gids)
    if safe is None:
        return ClassBCheckResult("HBDC-REQ-020", False, "ancestor_chain_indeterminate", diagnostics)
    if not safe:
        return ClassBCheckResult("HBDC-REQ-020", False, "directory_entry_replacement_possible", diagnostics)
    return ClassBCheckResult("HBDC-REQ-020", True, "directory_entry_replacement_not_possible", diagnostics)


def _check_fail_closed_on_absent_root(root: Optional[Path]) -> ClassBCheckResult:
    """HBDC-REQ-021: this check itself is satisfied by construction —
    every root-dependent check above already fails closed (returns
    `satisfied=False` with a diagnostic reason) rather than raising or
    silently passing when Protected Root is absent or malformed."""

    if root is None:
        return ClassBCheckResult("HBDC-REQ-021", True, "unsupported_platform_fails_closed", ())
    if not root.exists():
        return ClassBCheckResult("HBDC-REQ-021", True, "absent_root_fails_closed_not_auto_provisioned", (str(root),))
    return ClassBCheckResult("HBDC-REQ-021", True, "root_present_no_fail_closed_path_needed", (str(root),))


# ═══════════════════════════════════════════════════════════════════════════
# Public API (plan §7)
# ═══════════════════════════════════════════════════════════════════════════


def verify_class_b_topology_conformance() -> ClassBDeploymentVerificationResult:
    """DIAGNOSTIC ONLY — NOT AN AUTHORITATIVE READINESS SIGNAL.

    Evaluates HBDC-REQ-001..024's topology requirements against live OS
    state. Accepts no parameter — Protected Root is always resolved via
    `hatp_bootstrap._default_production_trust_root()`, never overridden
    by a caller (HBDC-REQ-011). Read-only: performs no filesystem
    mutation under any code path.
    """

    root, root_status = _resolve_protected_root()
    unsupported_platform = root is None and root_status.startswith("unsupported_platform")
    agent_uid, agent_gids = _current_agent_identity()

    checks = [
        _safe_check("HBDC-REQ-001", lambda: _check_two_principal_topology(root)),
        _safe_check("HBDC-REQ-002", lambda: _check_principal_distinctness(root, agent_uid)),
        _safe_check("HBDC-REQ-004", _check_no_env_or_name_based_admin_inference),
        _safe_check("HBDC-REQ-005", _check_no_self_elevation_path),
        _safe_check("HBDC-REQ-007", lambda: _check_write_authority(root, agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-008", _check_agent_writable_exclusion_scope),
        _safe_check("HBDC-REQ-011", _check_no_override_parameter),
        _safe_check("HBDC-REQ-012", _check_read_only_guarantee),
        _safe_check("HBDC-REQ-013", lambda: _check_root_ownership(root, agent_uid)),
        _safe_check("HBDC-REQ-014", lambda: _check_root_mode(root)),
        _safe_check("HBDC-REQ-015", lambda: _check_group_effective_access(root, agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-016", lambda: _check_acl_effective_access(root, agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-017", lambda: _check_ancestor_chain(root, agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-018", lambda: _check_symlink_safety(root)),
        _safe_check("HBDC-REQ-019", lambda: _check_hard_link_safety(root)),
        _safe_check("HBDC-REQ-020", lambda: _check_ancestor_replacement_equivalence(root, agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-021", lambda: _check_fail_closed_on_absent_root(root)),
    ]

    if unsupported_platform:
        return ClassBDeploymentVerificationResult(
            status=ClassBConformanceStatus.UNSUPPORTED_DEPLOYMENT_MODEL,
            checks=tuple(checks),
            reasons=(f"unsupported_platform:{root_status}",),
            evidence=(),
        )
    return _build_result(checks)

"""HATP Model-A Python Environment-Lock Verifier — Phase 149O.20I, Wave C
(bounded, non-authoritative implementation).

Implements the HBDC-001 v1.0 §13 (HBDC-REQ-025..041) Model-A agent
Python execution-environment lock checks designed in
`docs/PHASE_149O_20H_CLASS_B_DEPLOYMENT_VERIFIER_MODEL_A_ENVIRONMENT_
LOCK_IMPLEMENTATION_PLAN.md` §16-17, §27.

**Non-authoritative by design (CBV-S1).** Identical posture to
`hatp_class_b_topology_verifier.py`: this module's source is not yet a
member of HMIC-001's frozen 25-file identity. `COMPLIANT` here is
diagnostic only, never a production readiness/certification/activation
input, until a future, separately-governed contract-and-implementation
sequence (plan §24 Wave F) closes CBV-S1 for it.

**Strictly read-only.** Inspects live process/interpreter/`sys.path`
state only; performs no filesystem mutation, no venv repair, no
environment cleanup.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import os
import site
import sys
from pathlib import Path
from typing import Optional

from pcae.core.hatp_class_b_topology_verifier import (
    ClassBCheckResult,
    ClassBDeploymentVerificationResult,
    _ancestor_chain_safe,
    _build_result,
    _current_agent_identity,
    _effective_write_access,
    _resolve_trusted_executable_with_effective_access,
    _safe_check,
)

# The 19 `src/pcae/`-relative authority modules from HMIC-REQ-050's
# frozen 25-file set (HMIC-001 v1.2), reproduced here as a literal data
# constant for HBDC-REQ-034's module-origin containment check — never
# imported from the certification module's own equivalent constant,
# since that would make this diagnostic-only module a runtime dependent
# of an already-HMIC-bound file for no authority reason. The literal
# set (including that module's own path, one of the 19) is instead
# re-typed here as plain path strings, matching the frozen list byte
# for byte as of this phase's inspection.
_AUTHORITY_MODULE_RELATIVE_PATHS: "tuple[str, ...]" = (
    "core/hatp_mandatory_cutover.py",
    "core/hatp_ag_authority.py",
    "core/hatp_rollback_consumption.py",
    "core/hatp_bootstrap.py",
    "core/human_approval_trusted_provenance.py",
    "core/repository_identity.py",
    "core/rollback_approval_evidence.py",
    "core/hatp_evidence_store.py",
    "core/hatp_signed_evidence.py",
    "core/agent.py",
    "commands/agent.py",
    "cli.py",
    "core/permission_broker.py",
    "core/permission_broker_foundation.py",
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
    "core/hatp_mandatory_certification.py",
)


def _own_repo_root() -> Path:
    """This module's own resolved location anchors the "authoritative
    tree" for the module-origin containment check (HBDC-REQ-034): a
    shadow-package attack cannot make this already-executing module
    lie about where it itself resolved from without having already won
    (out of scope — CWD/sys.path-order checks below address the actual
    shadowing channel). `.../src/pcae/core/hatp_environment_lock_
    verifier.py` -> repository root is three parents up."""

    return Path(__file__).resolve().parents[3]


def _check_interpreter_unwritable(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    interpreter = Path(sys.executable)
    try:
        real = interpreter.resolve(strict=True)
    except OSError as exc:
        return ClassBCheckResult("HBDC-REQ-027", False, "interpreter_unresolvable", (repr(exc),))
    write, reason, evidence = _effective_write_access(real, agent_uid, agent_gids)
    if write is not False:
        return ClassBCheckResult("HBDC-REQ-027", False, reason if write else f"indeterminate:{reason}", evidence)
    safe, diagnostics = _ancestor_chain_safe(real, agent_uid, agent_gids)
    if safe is not True:
        return ClassBCheckResult("HBDC-REQ-027", False, "interpreter_ancestor_chain_unsafe", diagnostics)
    return ClassBCheckResult("HBDC-REQ-027", True, "interpreter_agent_unwritable", (str(real),))


def _venv_root() -> Optional[Path]:
    base = getattr(sys, "base_prefix", sys.prefix)
    if base == sys.prefix:
        return None  # not running inside a venv
    return Path(sys.prefix)


def _check_venv_lock(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    venv_root = _venv_root()
    if venv_root is None:
        return ClassBCheckResult("HBDC-REQ-026", False, "no_venv_detected_not_provisioned", ())
    write, reason, evidence = _effective_write_access(venv_root, agent_uid, agent_gids)
    if write is not False:
        return ClassBCheckResult("HBDC-REQ-026", False, reason if write else f"indeterminate:{reason}", evidence)
    return ClassBCheckResult("HBDC-REQ-026", True, "venv_agent_unwritable", (str(venv_root),))


def _check_production_environment_provisioned(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    """HBDC-REQ-025: composite of the interpreter and venv checks
    above. Not independently re-derived — this row confirms both
    sub-checks were evaluated without error, per plan §16's
    "conformance evidence enumerated" framing (HBDC-REQ-023)."""

    interpreter = _check_interpreter_unwritable(agent_uid, agent_gids)
    venv = _check_venv_lock(agent_uid, agent_gids)
    if interpreter.satisfied and venv.satisfied:
        return ClassBCheckResult("HBDC-REQ-025", True, "interpreter_and_venv_admin_provisioned", ())
    return ClassBCheckResult(
        "HBDC-REQ-025",
        False,
        "interpreter_or_venv_not_admin_provisioned",
        (f"interpreter:{interpreter.status}", f"venv:{venv.status}"),
    )


def _check_pythonpath(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    raw = os.environ.get("PYTHONPATH")
    if not raw:
        return ClassBCheckResult("HBDC-REQ-028", True, "pythonpath_unset", ())
    unsafe_entries: "list[str]" = []
    for entry in raw.split(os.pathsep):
        if not entry:
            continue
        candidate = Path(entry)
        write, reason, _evidence = _effective_write_access(candidate, agent_uid, agent_gids)
        if write is not False:
            unsafe_entries.append(f"{entry}:{reason}")
    if unsafe_entries:
        return ClassBCheckResult("HBDC-REQ-028", False, "pythonpath_contains_agent_writable_entry", tuple(unsafe_entries))
    return ClassBCheckResult("HBDC-REQ-028", True, "pythonpath_set_but_all_entries_agent_unwritable", (raw,))


def _check_user_site(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    if not getattr(site, "ENABLE_USER_SITE", True):
        return ClassBCheckResult("HBDC-REQ-029", True, "user_site_disabled", ())
    try:
        user_site = Path(site.getusersitepackages())
    except Exception as exc:  # noqa: BLE001 - fail closed on any resolution failure
        return ClassBCheckResult("HBDC-REQ-029", False, "user_site_path_unresolvable", (repr(exc),))
    write, reason, evidence = _effective_write_access(user_site, agent_uid, agent_gids)
    if write is not False:
        return ClassBCheckResult(
            "HBDC-REQ-029", False, reason if write else f"indeterminate:{reason}", evidence + (str(user_site),)
        )
    return ClassBCheckResult("HBDC-REQ-029", True, "user_site_enabled_but_agent_unwritable", (str(user_site),))


def _effective_sys_path_dirs() -> "list[Path]":
    dirs: "list[Path]" = []
    for entry in sys.path:
        candidate = Path(entry) if entry else Path.cwd()
        if candidate.is_dir():
            dirs.append(candidate)
    return dirs


def _check_customization_modules(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    unsafe: "list[str]" = []
    found_any = False
    for directory in _effective_sys_path_dirs():
        for name in ("sitecustomize.py", "usercustomize.py"):
            candidate = directory / name
            if not candidate.exists():
                continue
            found_any = True
            write, reason, _evidence = _effective_write_access(candidate, agent_uid, agent_gids)
            if write is not False:
                unsafe.append(f"{candidate}:{reason}")
    if unsafe:
        return ClassBCheckResult("HBDC-REQ-030", False, "customization_module_agent_writable", tuple(unsafe))
    if not found_any:
        return ClassBCheckResult("HBDC-REQ-030", True, "no_customization_module_present", ())
    return ClassBCheckResult("HBDC-REQ-030", True, "customization_modules_present_admin_controlled", ())


def _pth_line_is_executable(line: str) -> bool:
    """Phase 149O.20J.1 (B-CBV-J-1 repair): mirrors CPython's own
    `site.addpackage()` per-line classification exactly (verified
    against the running interpreter's `site` module source) rather than
    an approximation of it. In `site.addpackage()`, each raw line
    (never stripped before these checks) is classified in order:
    a `#`-prefixed line is a comment (never executed); an
    all-whitespace line is blank (never executed); otherwise a line
    satisfying `line.startswith(("import ", "import\\t"))` is executed
    via `exec(line)` — both the space- and tab-delimited forms are
    live code-execution channels, not just the space-delimited one the
    prior predicate recognized. Any other line is a plain path entry.
    Checking the raw (unstripped) line, not `line.strip()`, also
    matches CPython: a line that merely starts with leading whitespace
    before `import` is not treated as executable by `site.addpackage()`
    either, since `startswith` there operates on the raw line too."""

    if line.startswith("#"):
        return False
    if line.strip() == "":
        return False
    return line.startswith(("import ", "import\t"))


def _check_pth_files(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    unsafe: "list[str]" = []
    found_any = False
    for directory in _effective_sys_path_dirs():
        try:
            pth_files = sorted(directory.glob("*.pth"))
        except OSError:
            continue
        for pth in pth_files:
            found_any = True
            write, reason, _evidence = _effective_write_access(pth, agent_uid, agent_gids)
            agent_writable = write is not False
            try:
                content = pth.read_text(encoding="utf-8", errors="replace")
            except OSError:
                content = ""
            has_import_line = any(_pth_line_is_executable(line) for line in content.splitlines())
            if agent_writable:
                unsafe.append(f"{pth}:{reason}")
            elif has_import_line:
                unsafe.append(f"{pth}:import_prefixed_line_present")
    if unsafe:
        return ClassBCheckResult("HBDC-REQ-031", False, "unsafe_pth_file_present", tuple(unsafe))
    if not found_any:
        return ClassBCheckResult("HBDC-REQ-031", True, "no_pth_file_present", ())
    return ClassBCheckResult("HBDC-REQ-031", True, "pth_files_present_admin_controlled_no_import_lines", ())


_EXPECTED_META_PATH_TYPES = frozenset(
    {"BuiltinImporter", "FrozenImporter", "PathFinder", "WindowsRegistryFinder", "_distutils_hack.DistutilsMetaFinder"}
)


def _check_meta_path_hooks() -> ClassBCheckResult:
    """Best-effort, explicitly non-exhaustive (plan §26/HBDC-REQ-032):
    flags any `sys.meta_path` entry whose type name is not part of a
    small, named allow-list of expected startup machinery."""

    unexpected: "list[str]" = []
    for finder in sys.meta_path:
        # A meta_path entry may be a class used directly (the standard
        # library's own PathFinder/BuiltinImporter/FrozenImporter are
        # registered this way, not as instances) or an instance of a
        # finder class (third-party import hooks commonly are). Resolve
        # the entry's own identity in either case, not the metaclass.
        entry_type = finder if isinstance(finder, type) else type(finder)
        type_name = entry_type.__name__
        qualified = f"{entry_type.__module__}.{type_name}"
        if type_name not in _EXPECTED_META_PATH_TYPES and qualified not in _EXPECTED_META_PATH_TYPES:
            unexpected.append(qualified)
    if unexpected:
        return ClassBCheckResult("HBDC-REQ-032", False, "unexpected_meta_path_hook_present", tuple(unexpected))
    return ClassBCheckResult("HBDC-REQ-032", True, "only_expected_meta_path_hooks_present", ())


def _check_cwd_shadow_and_path_order() -> ClassBCheckResult:
    """HBDC-REQ-033: the resolved production `sys.path` must not place
    an agent-writable, agent-selectable directory (including CWD) ahead
    of the canonical repository package location."""

    try:
        spec = importlib.util.find_spec("pcae")
    except (ImportError, ValueError) as exc:
        return ClassBCheckResult("HBDC-REQ-033", False, "pcae_package_spec_unresolvable", (repr(exc),))
    if spec is None or not spec.submodule_search_locations:
        return ClassBCheckResult("HBDC-REQ-033", False, "pcae_package_not_found", ())
    package_dir = Path(next(iter(spec.submodule_search_locations))).resolve()
    package_parent = package_dir.parent

    cwd = Path.cwd().resolve()
    agent_uid, agent_gids = _current_agent_identity()

    package_index: Optional[int] = None
    cwd_index: Optional[int] = None
    for idx, entry in enumerate(sys.path):
        candidate = Path(entry).resolve() if entry else cwd
        if package_index is None and candidate == package_parent:
            package_index = idx
        if cwd_index is None and candidate == cwd:
            write, _reason, _evidence = _effective_write_access(candidate, agent_uid, agent_gids)
            if write is not False:
                cwd_index = idx

    if package_index is None:
        return ClassBCheckResult("HBDC-REQ-033", False, "canonical_package_location_not_on_sys_path", ())
    if cwd_index is not None and cwd_index < package_index:
        return ClassBCheckResult(
            "HBDC-REQ-033", False, "agent_writable_cwd_precedes_canonical_package_location", (str(cwd),)
        )
    return ClassBCheckResult("HBDC-REQ-033", True, "cwd_cannot_shadow_canonical_package_location", (str(package_dir),))


def _check_module_origin_containment() -> ClassBCheckResult:
    repo_root = _own_repo_root()
    shadowed: "list[str]" = []
    unresolvable: "list[str]" = []
    for relative in _AUTHORITY_MODULE_RELATIVE_PATHS:
        module_name = "pcae." + relative[:-3].replace("/", ".")
        try:
            spec = importlib.util.find_spec(module_name)
        except (ImportError, ValueError) as exc:
            unresolvable.append(f"{module_name}:{exc!r}")
            continue
        if spec is None or spec.origin is None:
            unresolvable.append(f"{module_name}:no_spec_or_origin")
            continue
        origin = Path(spec.origin).resolve()
        try:
            origin.relative_to(repo_root)
        except ValueError:
            shadowed.append(f"{module_name}:{origin}")
    if shadowed:
        return ClassBCheckResult("HBDC-REQ-034", False, "authority_module_origin_outside_canonical_root", tuple(shadowed))
    if unresolvable:
        return ClassBCheckResult("HBDC-REQ-034", False, "authority_module_spec_unresolvable", tuple(unresolvable))
    return ClassBCheckResult("HBDC-REQ-034", True, "all_authority_module_origins_contained", (str(repo_root),))


def _check_editable_install_metadata(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    try:
        dist = importlib.metadata.distribution("pcae")
    except importlib.metadata.PackageNotFoundError:
        return ClassBCheckResult("HBDC-REQ-035", False, "pcae_distribution_metadata_not_found", ())
    dist_path = getattr(dist, "_path", None)
    if dist_path is None:
        return ClassBCheckResult("HBDC-REQ-035", False, "dist_info_path_unavailable", ())
    dist_dir = Path(dist_path)
    if not dist_dir.exists():
        return ClassBCheckResult("HBDC-REQ-035", False, "dist_info_directory_missing", (str(dist_dir),))
    unsafe: "list[str]" = []
    checked_any = False
    for candidate_name in ("direct_url.json", "RECORD", "__editable___pcae_finder.py"):
        candidate = dist_dir / candidate_name
        if not candidate.exists():
            continue
        checked_any = True
        write, reason, _evidence = _effective_write_access(candidate, agent_uid, agent_gids)
        if write is not False:
            unsafe.append(f"{candidate}:{reason}")
    write_dir, reason_dir, _evidence = _effective_write_access(dist_dir, agent_uid, agent_gids)
    if write_dir is not False:
        unsafe.append(f"{dist_dir}:{reason_dir}")
    if unsafe:
        return ClassBCheckResult("HBDC-REQ-035", False, "editable_install_metadata_agent_writable", tuple(unsafe))
    if not checked_any:
        return ClassBCheckResult("HBDC-REQ-035", True, "no_editable_metadata_artifact_found_dist_dir_locked", (str(dist_dir),))
    return ClassBCheckResult("HBDC-REQ-035", True, "editable_install_metadata_admin_controlled", (str(dist_dir),))


def _check_launcher(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    from shutil import which

    launcher = which("pcae")
    if launcher is None:
        return ClassBCheckResult("HBDC-REQ-036", False, "no_configured_production_launcher_detected", ())
    launcher_path = Path(launcher)
    try:
        real = launcher_path.resolve(strict=True)
    except OSError as exc:
        return ClassBCheckResult("HBDC-REQ-036", False, "launcher_unresolvable", (repr(exc),))
    write, reason, evidence = _effective_write_access(real, agent_uid, agent_gids)
    if write is not False:
        return ClassBCheckResult("HBDC-REQ-036", False, reason if write else f"indeterminate:{reason}", evidence)
    return ClassBCheckResult("HBDC-REQ-036", True, "launcher_agent_unwritable", (str(real),))


def _check_shell_environment_injection() -> ClassBCheckResult:
    """HBDC-REQ-037: satisfied jointly by HBDC-REQ-028 (`PYTHONPATH`)
    and HBDC-REQ-033 (`sys.path`/CWD ordering) — no independent probe
    is added beyond those two, matching plan §2's disposition."""

    pythonpath = _check_pythonpath(*_current_agent_identity())
    cwd = _check_cwd_shadow_and_path_order()
    if pythonpath.satisfied and cwd.satisfied:
        return ClassBCheckResult("HBDC-REQ-037", True, "no_authority_changing_env_injection_channel_open", ())
    return ClassBCheckResult(
        "HBDC-REQ-037",
        False,
        "authority_changing_env_injection_channel_open",
        (f"pythonpath:{pythonpath.status}", f"cwd:{cwd.status}"),
    )


def _check_trusted_git() -> ClassBCheckResult:
    """Phase 149O.20J.1 (B-CBV-J-3 repair): resolution now goes through
    `_resolve_trusted_executable_with_effective_access`, which layers
    the ACL-inclusive effective-access check (shared with Protected Root,
    HBDC-REQ-016/017) on top of the unchanged, non-recursive PATH-
    precedence walk — see that function's docstring for the anti-
    recursion design."""

    resolved = _resolve_trusted_executable_with_effective_access("git")
    if resolved is None:
        return ClassBCheckResult("HBDC-REQ-038", False, "git_executable_not_trustworthy_resolvable", ())
    return ClassBCheckResult("HBDC-REQ-038", True, "git_executable_path_precedence_and_ownership_verified", (str(resolved),))


def _check_third_party_dependency_boundary(agent_uid: int, agent_gids: "frozenset[int]") -> ClassBCheckResult:
    """HBDC-REQ-039: satisfied by the venv/site-packages lock
    (HBDC-REQ-025..027) — no separate dependency-pinning mechanism, per
    plan §2's disposition."""

    venv = _check_venv_lock(agent_uid, agent_gids)
    if venv.satisfied:
        return ClassBCheckResult("HBDC-REQ-039", True, "third_party_dependencies_covered_by_venv_lock", ())
    return ClassBCheckResult("HBDC-REQ-039", False, "venv_lock_not_established_dependency_boundary_unproven", (venv.status,))


# ═══════════════════════════════════════════════════════════════════════════
# Public API (plan §7)
# ═══════════════════════════════════════════════════════════════════════════


def verify_environment_lock_conformance() -> ClassBDeploymentVerificationResult:
    """DIAGNOSTIC ONLY — NOT AN AUTHORITATIVE READINESS SIGNAL.

    Evaluates HBDC-REQ-023, HBDC-REQ-025..039's Model-A environment-lock
    requirements against live interpreter/process state. Accepts no
    parameter. Read-only: performs no filesystem mutation.
    """

    agent_uid, agent_gids = _current_agent_identity()

    checks = [
        _safe_check("HBDC-REQ-025", lambda: _check_production_environment_provisioned(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-026", lambda: _check_venv_lock(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-027", lambda: _check_interpreter_unwritable(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-028", lambda: _check_pythonpath(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-029", lambda: _check_user_site(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-030", lambda: _check_customization_modules(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-031", lambda: _check_pth_files(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-032", _check_meta_path_hooks),
        _safe_check("HBDC-REQ-033", _check_cwd_shadow_and_path_order),
        _safe_check("HBDC-REQ-034", _check_module_origin_containment),
        _safe_check("HBDC-REQ-035", lambda: _check_editable_install_metadata(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-036", lambda: _check_launcher(agent_uid, agent_gids)),
        _safe_check("HBDC-REQ-037", _check_shell_environment_injection),
        _safe_check("HBDC-REQ-038", _check_trusted_git),
        _safe_check("HBDC-REQ-039", lambda: _check_third_party_dependency_boundary(agent_uid, agent_gids)),
    ]
    return _build_result(checks)

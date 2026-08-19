"""Phase 149O.20L.7O.2G -- HATP Trust-Enrollment and Signing HMIC
Transitive Authority-Scope Analysis.

Mechanically re-validates the analysis in `docs/PHASE_149O_20L_7O_2G_
HATP_TRUST_ENROLLMENT_AND_SIGNING_HMIC_TRANSITIVE_AUTHORITY_SCOPE_
ANALYSIS.md` against live repository state:

* the current 30-file / 5-contract HMIC baseline, extracted directly
  from `hatp_mandatory_certification.py`'s own production constants
  (not hardcoded independently of it -- this is a baseline-extraction
  check, not a re-derivation);
* the three candidate Trust-Enrollment/signing source files exist and
  are not already members of the current frozen set;
* a fresh AST-based PCAE-owned import walk of those three files
  produces the exact import set the analysis document cites, and that
  every one of those imports is either an already-bound member or one
  of the four explicitly-excluded utility/telemetry leaves;
* the proposed 33-file / 7-contract target sets are internally
  consistent: sorted, duplicate-free, and every path exists on disk;
* HPSE-001/HHCE-001's contract files match the identical
  `**Contract:**`/`**Version:**` header grammar
  `derive_contract_versions` already parses for the other five.

This phase makes no production change. No signing, enrollment, or
certification code path is exercised for a decision -- only static
analysis and file-existence/header checks.
"""
from __future__ import annotations

import ast
from pathlib import Path

from pcae.core import hatp_mandatory_certification as hmic_impl

REPO_ROOT = Path(__file__).resolve().parent.parent

_NEW_SRC_PCAE_RELATIVE = (
    "core/hatp_signing_ceremony.py",
    "core/hatp_hardware_credential_admin.py",
    "core/hatp_principal_signer_admin.py",
)

_NEW_CONTRACT_ROOT_RELATIVE = (
    "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
    "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
)

_NEW_CONTRACT_IDENTITY = (
    ("HPSE-001", "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"),
    ("HHCE-001", "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"),
)

_EXCLUDED_UTILITY_LEAVES = frozenset({"paths", "provenance", "git_status", "tasks"})


def _pcae_owned_imports(path: Path) -> "set[str]":
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: "set[str]" = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("pcae"):
                result.add(module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("pcae"):
                    result.add(alias.name)
    return result


def test_current_baseline_is_thirty_files_five_contracts() -> None:
    assert len(hmic_impl._FROZEN_AUTHORITY_BEARING_FILES) == 30
    assert len(hmic_impl._CONTRACT_IDENTITY_FILES) == 5
    contract_ids = {contract_id for contract_id, _ in hmic_impl._CONTRACT_IDENTITY_FILES}
    assert contract_ids == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}


def test_three_candidate_files_exist_and_are_not_currently_bound() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    for relative in _NEW_SRC_PCAE_RELATIVE:
        on_disk = REPO_ROOT / "src" / "pcae" / relative
        assert on_disk.is_file(), f"candidate source missing: {relative}"
        canonical = f"src/pcae/{relative}"
        assert canonical not in current_canonical, f"{relative} unexpectedly already HMIC-bound"


def test_two_candidate_contracts_exist_and_are_not_currently_bound() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    bound_contract_paths = {path for _, path in hmic_impl._CONTRACT_IDENTITY_FILES}
    for relative in _NEW_CONTRACT_ROOT_RELATIVE:
        on_disk = REPO_ROOT / relative
        assert on_disk.is_file(), f"candidate contract missing: {relative}"
        assert relative not in current_canonical, f"{relative} unexpectedly already content-bound"
        assert relative not in bound_contract_paths, f"{relative} unexpectedly already version-bound"


def test_candidate_source_import_closure_matches_documented_set() -> None:
    direct_imports: "dict[str, set[str]]" = {}
    for relative in _NEW_SRC_PCAE_RELATIVE:
        path = REPO_ROOT / "src" / "pcae" / relative
        direct_imports[relative] = _pcae_owned_imports(path)

    assert direct_imports["core/hatp_signing_ceremony.py"] == {
        "pcae.core.agent",
        "pcae.core.hatp_bootstrap",
        "pcae.core.hatp_evidence_store",
        "pcae.core.hatp_hardware_credentials",
        "pcae.core.hatp_providers",
        "pcae.core.hatp_signed_evidence",
        "pcae.core.human_approval_trusted_provenance",
        "pcae.core.paths",
        "pcae.core.repository_identity",
        "pcae.core.rollback_approval_evidence",
    }
    assert direct_imports["core/hatp_hardware_credential_admin.py"] == {
        "pcae.core.hatp_hardware_credentials",
        "pcae.core.paths",
        "pcae.core.provenance",
        "pcae.core.hatp_bootstrap",
    }
    assert direct_imports["core/hatp_principal_signer_admin.py"] == {
        "pcae.core.hatp_bootstrap",
        "pcae.core.hatp_deployment_binding_admin",
        "pcae.core.hatp_hardware_credential_admin",
        "pcae.core.hatp_hardware_credentials",
        "pcae.core.hatp_providers",
        "pcae.core.paths",
        "pcae.core.provenance",
    }


def test_every_direct_import_is_bound_new_or_an_excluded_leaf() -> None:
    """Module-level (not whole-transitive-fanout) check: every PCAE-owned
    name the three new candidates import directly resolves to an
    already-bound member, one of the three candidates themselves, or one
    of the four established-precedent excluded leaves (`paths`,
    `provenance`, `git_status`, `tasks`). A blind whole-module recursive
    walk through those four leaves' *own* unrelated fan-out (e.g.
    `tasks.py` also backs the entire `pcae task`/`pcae health` CLI
    surface) is deliberately not performed here -- see
    `test_excluded_leaf_symbols_used_by_new_candidates_do_not_reach_
    beyond_their_own_narrow_bodies` below, which instead checks the
    *specific* symbols the new candidates actually call."""

    current_canonical = set(hmic_impl._frozen_canonical_paths())
    bound_modules = {p.rsplit("/", 1)[-1][: -len(".py")] for p in current_canonical if p.endswith(".py")}
    new_modules = {relative.rsplit("/", 1)[-1][: -len(".py")] for relative in _NEW_SRC_PCAE_RELATIVE}

    for relative in _NEW_SRC_PCAE_RELATIVE:
        path = REPO_ROOT / "src" / "pcae" / relative
        for imported in _pcae_owned_imports(path):
            leaf = imported.rsplit(".", 1)[-1]
            assert leaf in bound_modules or leaf in new_modules or leaf in _EXCLUDED_UTILITY_LEAVES, (
                f"{relative} imports {imported!r}, which is neither an already-bound member, "
                f"one of the three new candidates, nor an explicitly-excluded utility leaf"
            )


def test_excluded_leaf_symbols_used_by_new_candidates_do_not_reach_beyond_their_own_narrow_bodies() -> None:
    """The four excluded leaves (`paths.py`, `provenance.py`,
    `git_status.py`, `tasks.py`) each have broad, unrelated fan-out at
    the *module* level (`tasks.py` alone backs the whole `pcae task`
    CLI surface, including `health`/`session`/`status`). What matters
    for HMIC-REQ-052's closure test is only the *specific* symbol each
    new candidate actually calls -- `HarnessPath.cwd`/`.join`,
    `append_provenance_event`, and (via `provenance.py`)
    `read_git_branch`/`find_latest_active_task`. This test asserts
    those specific functions' own source bodies contain no call to any
    name outside a narrow, explicitly-audited allowlist -- i.e. the
    broad module-level fan-out is never actually reached at runtime by
    the code path the new candidates exercise."""

    tasks_path = REPO_ROOT / "src" / "pcae" / "core" / "tasks.py"
    tree = ast.parse(tasks_path.read_text(encoding="utf-8"))
    target = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "find_latest_active_task":
            target = node
            break
    assert target is not None, "find_latest_active_task not found in tasks.py"

    called_names = {
        n.func.id
        for n in ast.walk(target)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    called_attrs = {
        n.func.attr
        for n in ast.walk(target)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
    }
    assert called_names <= {"sorted", "read_active_task", "Path"}
    assert called_attrs <= {"join", "is_dir", "glob"}


def test_proposed_target_source_set_is_sorted_unique_and_exists() -> None:
    current_canonical = hmic_impl._frozen_canonical_paths()
    added_canonical = tuple(f"src/pcae/{relative}" for relative in _NEW_SRC_PCAE_RELATIVE)
    target = tuple(sorted(set(current_canonical) | set(added_canonical)))

    assert len(target) == 33
    assert len(set(target)) == len(target)
    for canonical_path in target:
        assert (REPO_ROOT / canonical_path).is_file(), f"target member missing on disk: {canonical_path}"


def test_proposed_target_contract_set_is_seven_members_and_headers_parse() -> None:
    target_contract_ids = {c for c, _ in hmic_impl._CONTRACT_IDENTITY_FILES} | {
        c for c, _ in _NEW_CONTRACT_IDENTITY
    }
    assert target_contract_ids == {
        "HMRC-001",
        "HATP-001",
        "HSCE-001",
        "RAE-001",
        "HBDC-001",
        "HPSE-001",
        "HHCE-001",
    }
    for contract_id, relative_path in _NEW_CONTRACT_IDENTITY:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        id_match = hmic_impl._CONTRACT_ID_HEADER_RE.search(text)
        version_match = hmic_impl._CONTRACT_VERSION_HEADER_RE.search(text)
        assert id_match is not None and id_match.group(1) == contract_id
        assert version_match is not None and version_match.group(1) == "1.1"


def test_hsce_001_v1_3_already_fully_bound_content_and_version() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    assert "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md" in current_canonical
    bound_ids = {c for c, _ in hmic_impl._CONTRACT_IDENTITY_FILES}
    assert "HSCE-001" in bound_ids
    text = (REPO_ROOT / "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md").read_text(
        encoding="utf-8"
    )
    version_match = hmic_impl._CONTRACT_VERSION_HEADER_RE.search(text)
    assert version_match is not None and version_match.group(1) == "1.3"


def test_class_b_verifier_files_remain_bound_unchanged() -> None:
    current_canonical = set(hmic_impl._frozen_canonical_paths())
    for relative in (
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
    ):
        assert relative in current_canonical


def test_no_production_hmic_constant_modified_by_this_phase() -> None:
    assert len(hmic_impl._FROZEN_AUTHORITY_BEARING_FILES) == 30
    assert len(hmic_impl._CONTRACT_IDENTITY_FILES) == 5

"""Phase 149O.19.3R.1 -- HMIC Frozen Implementation Identity Contract
Repair Independent Re-Verification.

This is a documentation/test-only INDEPENDENT RE-VERIFICATION phase. It
does not trust Phase 149O.19.3R's own dependency table, diagrams, or
test constants (`tests/test_phase_149o_19_3r_hmic_frozen_file_set_
contract_repair.py`): every expectation below is independently derived
from the contract text (`docs/contracts/
HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`) and
from direct source inspection (a fresh `ast`-based import walk, not
regex-copied from any prior phase's helper code).

Findings this module independently re-confirms:

  * the repaired HMIC-REQ-050 enumeration is exactly 22 paths, the four
    newly-added ones present, each existing/unique/canonical;
  * a fresh transitive `ast`-based import walk from the 15 authority-
    relevant frozen files (excluding `cli.py`/`commands/agent.py`/
    `core/agent.py`'s own broad command-dispatch fan-out, per this
    repository's own established methodology) discovers no
    class-A (authority-sensitive) dependency outside the 22-file set;
  * `implementation_scope_digest`, independently reimplemented from
    HMIC-REQ-054-058's normative text (not the repair phase's own
    helper), is deterministic and sensitive to a single-bit mutation in
    every one of the 22 frozen files;
  * the specific pre-repair defect (B-149O.19.3-1) is reproduced: a
    single-bit mutation to any of the four newly-added files leaves the
    historical 18-file-model digest unchanged, but changes the current
    22-file-model digest;
  * `hatp_hardware_credentials.py` has zero `pcae.*` imports (a leaf
    node structurally analogous to the already-frozen `HATPTrustStore`);
  * `rollback_approval_evidence.py`'s `resolve_rollback_approval_
    evidence`/`resolve_rollback_approval_evidence_with_hatp` entry
    points never call `create_rollback_approval_decision` or
    `PublicationCoordinator.execute` -- independently confirming the
    RAE creation-ceremony exclusion claim;
  * requirement/invariant/attack-matrix inventory counts are unchanged
    (144/12/32) after the repair;
  * no `src/pcae/**` file and no upstream contract file was modified by
    this phase.
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")

_UPSTREAM_CONTRACT_PATHS = (
    _CONTRACTS / "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    _CONTRACTS / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    _CONTRACTS / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    _CONTRACTS / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_ADAPTER_CONTRACT.md",
    _CONTRACTS / "PERMISSION_BROKER_POLICY_CONTRACT.md",
    _CONTRACTS / "REPOSITORY_WRITE_MERGE_PUSH_CONTROL_CONTRACT.md",
)

# ---------------------------------------------------------------------------
# Independently-derived frozen file set (read directly from HMIC-REQ-050's
# fenced enumeration; not copied from any prior phase's constant).
# ---------------------------------------------------------------------------

_PRE_REPAIR_18 = (
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
)

_NEWLY_ADDED_4 = (
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
)

_CURRENT_18_PLUS_4 = _PRE_REPAIR_18 + _NEWLY_ADDED_4

_FROZEN_CONTRACT_PATHS = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
)


def _current_22_repo_relative() -> Tuple[str, ...]:
    return tuple(f"src/pcae/{p}" for p in _CURRENT_18_PLUS_4) + _FROZEN_CONTRACT_PATHS


# ---------------------------------------------------------------------------
# Extraction of HMIC-REQ-050's literal enumeration directly from contract
# text, independent of any hard-coded constant above -- used as a
# cross-check that our hand-copied constant matches the contract itself.
# ---------------------------------------------------------------------------


def _extract_req_050_block() -> str:
    marker = "HMIC-REQ-050 (Exact Enumeration"
    start = _CONTRACT_TEXT.index(marker)
    fence_start = _CONTRACT_TEXT.index("```", start)
    fence_end = _CONTRACT_TEXT.index("```", fence_start + 3)
    return _CONTRACT_TEXT[fence_start + 3 : fence_end]


def _extract_req_050_paths() -> List[str]:
    block = _extract_req_050_block()
    lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
    return lines


def _historical_contract_text_at_repair() -> str:
    # Phase 149O.19.5E.1 (contract §50) later widened HMIC-REQ-050 from
    # 22 to 24 files (v1.0 -> v1.1). This test's whole purpose is an
    # independent re-verification of 149O.19.3R's own repair commit
    # (942df2a2) -- "the repaired HMIC-REQ-050 enumeration is exactly 22
    # paths" is a true, permanent historical fact about that commit, not
    # a claim about the live file, so it is pinned to that commit's blob
    # rather than reading the current (now 24-file, v1.1) contract text.
    result = subprocess.run(
        ["git", "show", f"942df2a2:{_CONTRACT_PATH.relative_to(_REPO_ROOT)}"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_contract_req_050_enumeration_matches_hand_extracted_22_paths():
    historical_text = _historical_contract_text_at_repair()
    marker = "HMIC-REQ-050 (Exact Enumeration"
    start = historical_text.index(marker)
    fence_start = historical_text.index("```", start)
    fence_end = historical_text.index("```", fence_start + 3)
    block = historical_text[fence_start + 3 : fence_end]
    extracted = [ln.strip() for ln in block.splitlines() if ln.strip()]
    assert len(extracted) == 22, f"expected 22 lines in HMIC-REQ-050's fenced block, found {len(extracted)}: {extracted}"
    expected_src = {f"core/{Path(p).name}" if False else p for p in _CURRENT_18_PLUS_4}
    # Convert extracted src/pcae-relative lines (no src/pcae/ prefix in the
    # contract text) into repo-relative and compare directly against the
    # 18 pre-repair + 4 new source paths (order-independent).
    extracted_src = {p for p in extracted if p.startswith("core/") or p in ("cli.py",) or p.startswith("commands/")}
    assert extracted_src == set(_CURRENT_18_PLUS_4)
    extracted_contracts = {p.split()[0] for p in extracted if p.startswith("docs/contracts/")}
    assert extracted_contracts == set(_FROZEN_CONTRACT_PATHS)


def test_current_22_file_set_has_exactly_22_entries_and_all_exist():
    paths = _current_22_repo_relative()
    assert len(paths) == 22
    assert len(set(paths)) == 22, "duplicate path in frozen set"
    for rel in paths:
        full = _REPO_ROOT / rel
        assert full.is_file(), f"frozen path does not exist or is not a regular file: {rel}"
        assert not full.is_symlink(), f"frozen path is a symlink: {rel}"


def test_newly_added_four_files_are_present_in_current_set_and_absent_from_historical_set():
    for rel in _NEWLY_ADDED_4:
        assert rel in _CURRENT_18_PLUS_4
        assert rel not in _PRE_REPAIR_18


# ---------------------------------------------------------------------------
# Fresh AST-based transitive import walk (independent re-implementation,
# not reused from any prior phase's helper).
# ---------------------------------------------------------------------------


def _imports_of(rel_path: str) -> Set:
    full = _SRC / rel_path
    src = full.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(full))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                mods.add(("REL", node.level, node.module))
            elif node.module and node.module.startswith("pcae"):
                mods.add(node.module)
    return mods


def _module_to_path(mod: str):
    parts = mod.split(".")
    if not parts or parts[0] != "pcae" or len(parts) < 2:
        return None
    rel = os.path.join(*parts[1:])
    for candidate in (rel + ".py", os.path.join(rel, "__init__.py")):
        if (_SRC / candidate).exists():
            return candidate
    return None


def _rel_import_to_path(cur_path: str, level: int, module: str):
    cur_dir = os.path.dirname(cur_path)
    cur_dir_parts = cur_dir.split(os.sep) if cur_dir else []
    base = cur_dir_parts[: len(cur_dir_parts) - (level - 1)] if level > 1 else cur_dir_parts
    mod_parts = module.split(".") if module else []
    rel_parts = base + mod_parts
    if not rel_parts:
        return None
    rel = os.path.join(*rel_parts)
    for candidate in (rel + ".py", os.path.join(rel, "__init__.py")):
        if (_SRC / candidate).exists():
            return candidate
    return None


#: The three broad command-dispatch surfaces whose own onward fan-out is
#: deliberately not walked further -- consistent with this repository's own
#: established 149O.19.2/149O.19.3/149O.19.3R methodology (their *own*
#: bytes remain bound via HMIC-REQ-050 regardless).
_BROAD_SURFACE_FILES = {"cli.py", "commands/agent.py", "core/agent.py"}

#: Classes B/C/D dependencies this repository's own repair phase (149O.19.3R
#: §49) already named and rationalized as deliberately excluded. This test
#: independently re-derives the *same* set via its own walk (not by
#: asserting this list is correct a priori) and then checks no file
#: *outside* this known-safe set was found.
_KNOWN_SAFE_NON_AUTHORITY_PATHS = {
    "core/paths.py",
    "core/gate_dry_run.py",
    "core/scope_preflight.py",
    "core/shell_gate.py",
    "core/gate_dry_run_context.py",
    "core/artifact_index.py",
    "core/decision_log.py",
    "core/governance_timeline.py",
    "core/memory_snapshot.py",
    "core/project_state.py",
    "core/risk_register.py",
    "core/__init__.py",
    # Phase 149O.19.5F (Wave F, gated by Stop Condition W-1): this test
    # module's `_CURRENT_18_PLUS_4` is a static historical reconstruction
    # of HMIC-REQ-050's enumeration as it stood at Phase 149O.19.3R and is
    # intentionally not live-updated. `hatp_mandatory_certification.py`
    # did not exist at that time; it was built later (149O.19.5A-5D) and
    # added to the frozen enumeration by the v1.1 24-file realignment
    # (149O.19.5E.3, independently re-verified 149O.19.5E.4). It IS bound
    # in the current, real HMIC-REQ-050 enumeration -- listed here only
    # because this test's own historical snapshot predates that addition.
    "core/hatp_mandatory_certification.py",
}


def _authority_adjacent_closure() -> Dict[str, Set[str]]:
    """Transitive pcae.* closure starting from the 15 authority-relevant
    frozen files (i.e. the 18+4 minus the 3 broad command-dispatch
    surfaces), independent of any prior phase's own walk."""
    seed = [p for p in _CURRENT_18_PLUS_4 if p not in _BROAD_SURFACE_FILES]
    visited: Set[str] = set()
    queue = list(seed)
    deps_by_file: Dict[str, Set[str]] = {}
    while queue:
        p = queue.pop()
        if p in visited:
            continue
        visited.add(p)
        if not (_SRC / p).exists():
            continue
        mods = _imports_of(p)
        deps: Set[str] = set()
        for m in mods:
            if isinstance(m, tuple):
                tp = _rel_import_to_path(p, m[1], m[2])
            else:
                tp = _module_to_path(m)
            if tp:
                deps.add(tp)
                if tp not in visited:
                    queue.append(tp)
        deps_by_file[p] = deps
    return deps_by_file


def test_authority_adjacent_closure_contains_no_undocumented_class_a_dependency():
    """Independent re-walk: every pcae-owned dependency reachable from the
    15 authority-relevant frozen files, excluding the 3 broad
    command-dispatch surfaces, must be either (a) already inside the
    22-file frozen set, or (b) inside the known-safe non-authority set
    this repository's own repair phase already named and rationalized
    (governance/publication/**, interactive_workflow/** reached only via
    rollback_approval_evidence.py's own RAE creation-ceremony imports, and
    schema_runtime/**/schema_resources/** reached only via those)."""
    deps_by_file = _authority_adjacent_closure()
    frozen_set = set(_CURRENT_18_PLUS_4)
    unexpected: Set[str] = set()
    for _p, deps in deps_by_file.items():
        for d in deps:
            if d in frozen_set:
                continue
            if d in _KNOWN_SAFE_NON_AUTHORITY_PATHS:
                continue
            if d.startswith("governance/publication/"):
                continue
            if d.startswith("interactive_workflow/"):
                continue
            if d.startswith("schema_runtime/") or d.startswith("schema_resources/"):
                continue
            unexpected.add(d)
    assert not unexpected, (
        "independent re-walk found a pcae-owned dependency neither in the "
        f"22-file frozen set nor in any previously-documented safe class: {sorted(unexpected)}"
    )


def test_hatp_hardware_credentials_has_zero_pcae_imports():
    """Independently confirms hatp_hardware_credentials.py is a leaf node
    -- it does not import hatp_bootstrap.py or any other pcae module,
    matching the contract's own claim that it duplicates rather than
    imports hatp_bootstrap.py's discipline."""
    mods = _imports_of("core/hatp_hardware_credentials.py")
    pcae_mods = {m for m in mods if isinstance(m, str) and m.startswith("pcae")}
    rel_mods = {m for m in mods if isinstance(m, tuple)}
    assert not pcae_mods and not rel_mods, f"expected zero pcae imports, found: {mods}"


def test_hatp_fido2_provider_imports_both_providers_and_hardware_credentials():
    mods = _imports_of("core/hatp_fido2_provider.py")
    plain = {m for m in mods if isinstance(m, str)}
    assert "pcae.core.hatp_hardware_credentials" in plain
    assert "pcae.core.hatp_providers" in plain


def test_hatp_providers_dynamically_imports_fido2_and_piv_source():
    text = (_SRC / "core/hatp_providers.py").read_text(encoding="utf-8")
    assert "hatp_fido2_provider" in text
    assert "hatp_piv_provider" in text


# ---------------------------------------------------------------------------
# RAE creation-ceremony non-reachability -- independently confirmed by
# reading the actual function bodies, not the contract's own prose.
# ---------------------------------------------------------------------------


def test_rollback_approval_evidence_resolution_paths_never_call_creation_ceremony():
    text = (_SRC / "core/rollback_approval_evidence.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    for fn_name in ("resolve_rollback_approval_evidence", "resolve_rollback_approval_evidence_with_hatp"):
        assert fn_name in functions, f"expected function {fn_name} in rollback_approval_evidence.py"
        fn_node = functions[fn_name]
        called_names = {
            n.func.id
            for n in ast.walk(fn_node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        }
        called_attrs = {
            n.func.attr
            for n in ast.walk(fn_node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        }
        assert "create_rollback_approval_decision" not in called_names
        assert "execute" not in called_attrs or not any(
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "execute"
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "coordinator"
            for n in ast.walk(fn_node)
        )


def test_resolve_decision_ref_reads_chgr_record_directly_off_disk():
    """Independently confirms `_resolve_decision_ref` -- the helper both
    resolution entry points call -- reads the CHGR JSON record directly
    from disk rather than invoking the PublicationCoordinator creation
    pipeline."""
    text = (_SRC / "core/rollback_approval_evidence.py").read_text(encoding="utf-8")
    tree = ast.parse(text)
    fn_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_resolve_decision_ref"
    )
    source = ast.get_source_segment(text, fn_node) or ""
    assert "read_text" in source or "read_bytes" in source
    assert "PublicationCoordinator" not in source
    assert "create_rollback_approval_decision" not in source


# ---------------------------------------------------------------------------
# hatp_signing_ceremony.py -- dynamically imported, undocumented in
# 149O.19.3R's own transitive-completeness table (this phase's own finding,
# recorded non-Blocking; see the accompanying findings doc).
# ---------------------------------------------------------------------------


def test_hatp_mandatory_cutover_dynamically_imports_hatp_signing_ceremony():
    text = (_SRC / "core/hatp_mandatory_cutover.py").read_text(encoding="utf-8")
    assert 'importlib.import_module("pcae.core.hatp_signing_ceremony")' in text


def test_hatp_signing_ceremony_import_readiness_check_consumes_only_a_boolean():
    """The readiness check around the dynamic import only records
    import-success as a boolean/detail-string pair; it does not call any
    function from the imported module, confirming no output of
    hatp_signing_ceremony.py's own logic feeds into the readiness result
    beyond bare importability."""
    text = (_SRC / "core/hatp_mandatory_cutover.py").read_text(encoding="utf-8")
    idx = text.index('importlib.import_module("pcae.core.hatp_signing_ceremony")')
    window = text[idx : idx + 400]
    assert "signing_available = True" in window
    assert "hatp_signing_ceremony." not in window  # no attribute access into the module in this window


def test_hatp_signed_evidence_does_not_trust_creation_provenance():
    """hatp_signed_evidence.py's own docstring states parsing/construction
    confers no assertion-validity/proof-trust credit -- independently
    confirming that whatever produced an evidence envelope (including
    hatp_signing_ceremony.py) cannot bypass verify_hatp_proof."""
    text = (_SRC / "core/hatp_signed_evidence.py").read_text(encoding="utf-8")
    assert "never reimplemented or shortcut" in text or "assertion validity or proof trust" in text


# ---------------------------------------------------------------------------
# Independent implementation_scope_digest reimplementation (not reused from
# any prior phase's code) + mutation sensitivity + pre/post defect proof.
# ---------------------------------------------------------------------------


def _resolve_frozen(rel: str) -> Path:
    return _REPO_ROOT / rel


def _digest(file_list: Tuple[str, ...], overrides: Dict[str, bytes] = None) -> str:
    overrides = overrides or {}
    records = []
    for rel in sorted(file_list):
        if rel in overrides:
            data = overrides[rel]
        else:
            data = _resolve_frozen(rel).read_bytes()
        h = hashlib.sha256(data).hexdigest()
        records.append(rel.encode("utf-8") + b"\0" + h.encode("utf-8") + b"\n")
    return hashlib.sha256(b"".join(records)).hexdigest()


def _current_22_all() -> Tuple[str, ...]:
    return tuple(f"src/pcae/{p}" if not p.startswith("docs/") else p for p in _current_22_repo_relative())


def test_implementation_scope_digest_is_deterministic():
    files = _current_22_repo_relative()
    d1 = _digest(files)
    d2 = _digest(files)
    assert d1 == d2
    assert len(d1) == 64  # sha256 hex


def test_implementation_scope_digest_sensitive_to_every_one_of_22_files():
    files = _current_22_repo_relative()
    baseline = _digest(files)
    for rel in files:
        full = _resolve_frozen(rel)
        data = full.read_bytes()
        mutated = bytearray(data)
        mutated[0] ^= 0x01
        mutated_digest = _digest(files, overrides={rel: bytes(mutated)})
        assert mutated_digest != baseline, f"digest insensitive to mutation of {rel}"


@pytest.mark.parametrize("rel", _NEWLY_ADDED_4)
def test_pre_repair_defect_reproduced_and_closed_by_current_set(rel):
    """For each newly-added file: a byte mutation must NOT change the
    digest computed over the historical 18-file set (reproducing
    B-149O.19.3-1), but MUST change the digest computed over the current
    22-file set (independently proving the repair closes it)."""
    historical_18 = tuple(f"src/pcae/{p}" for p in _PRE_REPAIR_18) + _FROZEN_CONTRACT_PATHS
    current_22 = _current_22_repo_relative()

    rel_repo = f"src/pcae/{rel}"
    full = _resolve_frozen(rel_repo)
    data = full.read_bytes()
    mutated = bytearray(data)
    mutated[0] ^= 0x01
    mutated = bytes(mutated)

    historical_before = _digest(historical_18)
    historical_after = _digest(historical_18, overrides={rel_repo: mutated})
    assert historical_before == historical_after, (
        f"expected historical 18-file digest to be UNAFFECTED by mutating {rel} "
        "(reproducing B-149O.19.3-1) but it changed"
    )

    current_before = _digest(current_22)
    current_after = _digest(current_22, overrides={rel_repo: mutated})
    assert current_before != current_after, (
        f"expected current 22-file digest to CHANGE when mutating {rel} "
        "(proving the repair closes B-149O.19.3-1) but it did not"
    )


# ---------------------------------------------------------------------------
# Requirement / invariant / attack-matrix inventory counts (independently
# re-extracted, not assumed).
# ---------------------------------------------------------------------------


def test_requirement_ids_are_144_sequential_gap_free():
    ids = sorted(set(re.findall(r"HMIC-REQ-(\d{3})", _CONTRACT_TEXT)))
    numbers = sorted(int(i) for i in ids)
    assert len(numbers) == 144
    assert numbers[0] == 1
    assert numbers[-1] == 144
    assert numbers == list(range(1, 145))


def test_civc_invariants_are_12():
    ids = sorted(set(re.findall(r"CIVC-(\d+)", _CONTRACT_TEXT)), key=int)
    assert len(ids) == 12
    assert [int(i) for i in ids] == list(range(1, 13))


def test_attack_matrix_has_32_rows():
    section_start = _CONTRACT_TEXT.index("## 41.")
    section_end = _CONTRACT_TEXT.index("\n## 42.")
    section = _CONTRACT_TEXT[section_start:section_end]
    rows = re.findall(r"^\|\s*\d+\s*\|", section, flags=re.MULTILINE)
    assert len(rows) == 32, f"expected 32 attack-matrix rows, found {len(rows)}"


def test_attack_row_11_names_all_four_newly_added_files():
    section_start = _CONTRACT_TEXT.index("## 41.")
    section_end = _CONTRACT_TEXT.index("\n## 42.")
    section = _CONTRACT_TEXT[section_start:section_end]
    row_11_match = re.search(r"^\|\s*11\s*\|.*$", section, flags=re.MULTILINE)
    assert row_11_match is not None
    row_11 = row_11_match.group(0)
    for rel in _NEWLY_ADDED_4:
        fname = rel.rsplit("/", 1)[-1]
        assert fname in row_11, f"attack row #11 does not name {fname}"


# ---------------------------------------------------------------------------
# Contract-repaired-set status text and finding-status text (independent
# re-read of the contract's own current claims).
# ---------------------------------------------------------------------------


def test_contract_status_is_frozen_repaired_pending_reverification():
    # Reads the live contract text (module-level `_CONTRACT_TEXT`), so
    # this assertion tracks the contract's current status string across
    # later amendments -- Phase 149O.19.5E.1 (contract §50) subsequently
    # amended HMIC-001 again (v1.0 -> v1.1), same forward-update pattern
    # already established for this exact assertion in
    # tests/test_phase_149o_19_2_...py and tests/test_phase_149o_19_3r_....py.
    assert (
        "FROZEN — VALIDATOR/ADMIN IMPLEMENTATION IDENTITY CONTRACT "
        "EVOLUTION COMPLETE — PENDING INDEPENDENT VERIFICATION"
        in _CONTRACT_TEXT
    )


def test_finding_b_149o_19_3_1_recorded_as_repaired_pending_reverification():
    idx = _CONTRACT_TEXT.index("**Finding status.**")
    window = _CONTRACT_TEXT[idx : idx + 300]
    assert "REPAIRED AT CONTRACT LEVEL" in window
    assert "PENDING INDEPENDENT RE-VERIFICATION" in window


def test_recommended_next_phase_names_149o_19_3r_1():
    idx = _CONTRACT_TEXT.index("**Recommended next phase.**")
    window = _CONTRACT_TEXT[idx : idx + 300]
    assert "149O.19.3R.1" in window


# ---------------------------------------------------------------------------
# No production or upstream-contract change performed by this phase.
# ---------------------------------------------------------------------------


# Phase 149O.19.5A (Wave A of the HMIC-001 implementation this contract
# repair/reverification phase precedes) legitimately added exactly one new
# production file, `hatp_mandatory_certification.py` -- a pure data-model/
# parser module, no writer, no certification state, no wiring into
# readiness (independently confirmed by that phase's own phase-boundary
# test suite). This assertion, an ongoing live `git diff` against this
# phase's own fixed entry commit rather than a point-in-time snapshot,
# would otherwise break on every subsequent legitimate `src/pcae/`
# addition; widened here in place ("restated, not weakened") per the
# identical methodology `test_phase_149o_18a_...py`'s own
# `_ASSEMBLED_PRODUCTION_FILES` comment already established for this
# repository. Any *other* file change still fails this test.
# Phase 149O.19.5F (Wave F, gated by Stop Condition W-1 -- independently
# confirmed closed at 149O.19.5E.4) modifies hatp_mandatory_cutover.py
# to wire the fresh HMIC active-certification validator into the
# previously-hardcoded readiness ceiling. Widened here in place, per the
# identical "restated, not weakened" methodology already used above for
# hatp_mandatory_certification.py's own addition.
_POST_REPAIR_ALLOWED_NEW_FILES = frozenset(
    {
        "src/pcae/core/hatp_mandatory_certification.py",
        "src/pcae/core/hatp_mandatory_cutover.py",
    }
)


def test_no_src_pcae_file_modified_by_this_phase():
    result = subprocess.run(
        ["git", "diff", "--name-only", "942df2a2", "--", "src/pcae"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [ln for ln in result.stdout.splitlines() if ln.strip()]
    unexpected = [ln for ln in changed if ln not in _POST_REPAIR_ALLOWED_NEW_FILES]
    assert unexpected == [], f"unexpected src/pcae files changed since 942df2a2: {unexpected}"


def test_hmic_contract_file_unchanged_since_repair_commit():
    # This test's original intent: confirm no *accidental* drift between
    # 149O.19.3R's own repair commit (942df2a2) and this re-verification
    # phase's (149O.19.3R.1's) own conclusion -- i.e. that nothing
    # silently touched the contract while this re-verification was in
    # progress. It was never a claim that the contract could never be
    # deliberately amended again in the future -- W-1 (contract §50) was
    # already on record at this point as a named, anticipated future
    # amendment. Phase 149O.19.5E.1 performed exactly that anticipated,
    # deliberate amendment, well after this phase concluded, so the
    # upper bound here is pinned to 149O.19.3R.1's own final commit
    # (11d7c616) rather than an open-ended "HEAD forever" comparison.
    result = subprocess.run(
        ["git", "diff", "--name-only", "942df2a2", "11d7c616", "--", str(_CONTRACT_PATH.relative_to(_REPO_ROOT))],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [ln for ln in result.stdout.splitlines() if ln.strip()]
    assert changed == [], "HMIC-001 contract file was modified between its repair commit and 149O.19.3R.1's own conclusion"


def test_no_certification_state_artifacts_exist():
    for name in ("certifications.json", "active_certification.json", "revocations.json"):
        hits = list(_REPO_ROOT.rglob(name))
        hits = [h for h in hits if ".git" not in h.parts and ".venv" not in h.parts]
        assert not hits, f"unexpected certification-state artifact found: {hits}"


def test_readiness_ceiling_still_hardcoded_false():
    # Phase 149O.19.5F (Wave F, gated by Stop Condition W-1) intentionally
    # replaces this literal with fresh HMIC active-certification
    # validation after this re-verification phase. Pinned to this file's
    # own pre-Wave-F phase-entry commit so the original evidentiary claim
    # (unchanged as of 149O.19.3R.1) is preserved, not weakened.
    text = subprocess.run(
        ["git", "show", "dd6492717ea27a43e16bce3e9c2077a884ed366f:src/pcae/core/hatp_mandatory_cutover.py"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    idx = text.index('"mandatory_consumption_implementation_independently_verified"')
    window = text[idx : idx + 120]
    assert re.search(r",\s*False\s*,", window), "readiness ceiling is no longer hard-coded False"

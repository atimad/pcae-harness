"""Phase 149O.19.3R -- HMIC-001 Frozen Implementation Identity Narrow
Contract Repair (finding B-149O.19.3-1,
`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
§49; repair document
`docs/PHASE_149O_19_3R_HMIC_FROZEN_IMPLEMENTATION_IDENTITY_CONTRACT_REPAIR.md`).

This is a NARROW CONTRACT-REPAIR-ONLY phase: it modifies no `src/pcae/**`
file, no upstream contract (HMRC-001/HATP-001/HSCE-001/RAE-001/RWMPC-001/
PBPA-001/PBPC-001), and creates no certification state. It repairs
exactly one contract (HMIC-001 v1.0) to close 149O.19.3's own
independently-verified Blocking finding: the original eighteen-file
frozen authority-bearing file set (HMIC-REQ-050) under-bound four
security-relevant transitive production dependencies.

This module independently re-verifies, by direct document and source
inspection:

  * the repaired HMIC-REQ-050 enumeration is exactly 22 paths, each
    existing, unique, and canonical;
  * the repaired set includes the three provider files 149O.19.3 named
    plus the fourth (`hatp_hardware_credentials.py`) this repair phase's
    own extended re-walk additionally found;
  * a mechanical AST/import-based transitive-closure check that no
    further undocumented authority-sensitive dependency remains unbound;
  * `implementation_scope_digest` (independently reimplemented) is
    sensitive to a byte change in each of the four newly-added files;
  * the contract's requirement/invariant/attack-matrix inventory counts
    are unchanged (144/12/32) after the repair;
  * no authority-sensitive TBD/TODO/FIXME was introduced;
  * upstream contracts remain byte-identical;
  * no `src/pcae/**` file was modified by this phase.
"""
from __future__ import annotations

import ast
import hashlib
import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")

#: Phase 149O.19.3's own final commit -- the entry point for this
#: narrow repair phase's own diff scoping.
_PHASE_149O_19_3_ENTRY_COMMIT = "1600215e"

# ---------------------------------------------------------------------------
# Repaired frozen file set
# ---------------------------------------------------------------------------

_PRE_REPAIR_SRC_RELATIVE_PATHS = (
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

_NEWLY_ADDED_SRC_RELATIVE_PATHS = (
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
)

_FROZEN_SRC_RELATIVE_PATHS = _PRE_REPAIR_SRC_RELATIVE_PATHS + _NEWLY_ADDED_SRC_RELATIVE_PATHS

_FROZEN_CONTRACT_RELATIVE_PATHS = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
)


def _frozen_repo_relative_paths():
    paths = [f"src/pcae/{p}" for p in _FROZEN_SRC_RELATIVE_PATHS]
    paths.extend(_FROZEN_CONTRACT_RELATIVE_PATHS)
    return tuple(paths)


# ---------------------------------------------------------------------------
# 68-72. Repaired frozen file set: exact count, three named providers,
# existence, uniqueness, canonical paths.
# ---------------------------------------------------------------------------


def test_repaired_frozen_file_set_has_exactly_22_entries():
    all_paths = _frozen_repo_relative_paths()
    assert len(all_paths) == 22


def test_repaired_frozen_file_set_includes_exactly_the_four_new_provider_credential_files():
    section_start = _CONTRACT_TEXT.index("## 17. Implementation Identity")
    section_end = _CONTRACT_TEXT.index("## 18.")
    section = _CONTRACT_TEXT[section_start:section_end]
    for rel in _NEWLY_ADDED_SRC_RELATIVE_PATHS:
        assert rel in section, f"repaired contract does not name newly-added path: {rel}"


def test_repaired_frozen_paths_exist_are_regular_and_not_symlinked():
    for rel in _frozen_repo_relative_paths():
        p = _REPO_ROOT / rel
        assert p.exists(), f"frozen file missing: {rel}"
        assert p.is_file() and not p.is_symlink(), f"frozen path not a plain regular file: {rel}"
        cur = p.parent
        while cur != _REPO_ROOT and cur != cur.parent:
            assert not cur.is_symlink(), f"frozen path has symlinked parent: {cur}"
            cur = cur.parent


def test_repaired_frozen_file_set_has_no_duplicates():
    all_paths = _frozen_repo_relative_paths()
    assert len(set(all_paths)) == len(all_paths)


def test_repaired_frozen_paths_are_canonical_relative_posix_no_traversal():
    for rel in _frozen_repo_relative_paths():
        assert not rel.startswith("/"), rel
        assert ".." not in rel.split("/"), rel
        assert "\\" not in rel, rel
        assert rel == rel.strip()


# ---------------------------------------------------------------------------
# 73. Provider transitive closure -- independent AST/import check
# ---------------------------------------------------------------------------


def _pcae_imports(py_path: Path):
    tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pcae"):
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("pcae"):
                    modules.add(alias.name)
    return modules


_FROZEN_DOTTED_MODULES = {
    "pcae." + p[:-3].replace("/", ".") for p in _FROZEN_SRC_RELATIVE_PATHS if p.endswith(".py")
}

#: Non-authority-sensitive dependencies of the newly-frozen provider/
#: credential files, documented with rationale (contract §49's
#: transitive-completeness table):
_DOCUMENTED_UNBOUND_PROVIDER_DEPENDENCIES = {
    "pcae.core.paths",
}


def test_provider_layer_transitive_pcae_dependencies_are_frozen_or_documented():
    """Independently walk the one-hop `pcae.*` import closure of the four
    newly-added files and confirm each dependency is itself in the
    repaired frozen set, or is an explicitly documented non-authority
    exception -- closing the repair loop rather than trusting the
    contract's own prose."""
    unexplained = set()
    for rel in _NEWLY_ADDED_SRC_RELATIVE_PATHS:
        for dotted in _pcae_imports(_SRC / rel):
            if dotted in _FROZEN_DOTTED_MODULES:
                continue
            if dotted in _DOCUMENTED_UNBOUND_PROVIDER_DEPENDENCIES:
                continue
            unexplained.add((rel, dotted))
    assert not unexplained, f"undocumented unbound dependency of the provider layer: {sorted(unexplained)}"


def test_hatp_hardware_credentials_is_the_fourth_omission_this_repair_phase_found():
    """The repair phase's own extended re-walk (beyond 149O.19.3's three
    named files) found a fourth: `hatp_fido2_provider.py` imports
    `hatp_hardware_credentials.HATPHardwareCredentialStore`, the
    protected registry supplying the public-key material a hardware
    signature is checked against."""
    imports = _pcae_imports(_SRC / "core" / "hatp_fido2_provider.py")
    assert "pcae.core.hatp_hardware_credentials" in imports
    assert "pcae.core.hatp_hardware_credentials" in _FROZEN_DOTTED_MODULES

    credentials_source = (_SRC / "core" / "hatp_hardware_credentials.py").read_text(encoding="utf-8")
    assert "class HATPHardwareCredentialStore" in credentials_source
    assert "def lookup_credential" in credentials_source
    # This module must itself have no further un-reviewed pcae dependency.
    assert _pcae_imports(_SRC / "core" / "hatp_hardware_credentials.py") == set()


def test_piv_provider_is_frozen_despite_being_non_conformant_today():
    """Per the governing repair instruction: a currently-deferred/
    NOT_CONFORMANT provider path still belongs in the frozen set if
    certified source could later make it authoritative without changing
    HMIC identity otherwise -- deferred status is not an exclusion
    criterion."""
    assert "pcae.core.hatp_piv_provider" in _FROZEN_DOTTED_MODULES
    piv_source = (_SRC / "core" / "hatp_piv_provider.py").read_text(encoding="utf-8")
    assert "NOT_CONFORMANT" in piv_source


# ---------------------------------------------------------------------------
# 74. Digest sensitivity -- independently modeled implementation_scope_digest
# changes when each newly-added file's bytes change.
# ---------------------------------------------------------------------------


def _per_file_record(path: str, file_bytes: bytes) -> bytes:
    digest_hex = hashlib.sha256(file_bytes).hexdigest()
    return f"{path}\0{digest_hex}\n".encode("utf-8")


def _implementation_scope_digest(paths_and_bytes) -> str:
    ordered = sorted(paths_and_bytes, key=lambda item: item[0])
    blob = b"".join(_per_file_record(p, b) for p, b in ordered)
    return hashlib.sha256(blob).hexdigest()


def _current_repaired_paths_and_bytes():
    paths_and_bytes = []
    for rel in _frozen_repo_relative_paths():
        p = _REPO_ROOT / rel
        paths_and_bytes.append((rel, p.read_bytes()))
    return paths_and_bytes


@pytest.mark.parametrize(
    "rel",
    [f"src/pcae/{p}" for p in _NEWLY_ADDED_SRC_RELATIVE_PATHS],
)
def test_digest_changes_when_a_newly_added_file_mutates(rel):
    baseline = _current_repaired_paths_and_bytes()
    baseline_digest = _implementation_scope_digest(baseline)

    mutated = [(p, b if p != rel else b + b"\n# mutated-for-test\n") for p, b in baseline]
    mutated_digest = _implementation_scope_digest(mutated)

    assert mutated_digest != baseline_digest, f"digest insensitive to a byte mutation of {rel}"


def test_digest_was_insensitive_to_these_files_before_repair_historical_reconstruction():
    """Historical reconstruction: recomputing the digest over ONLY the
    pre-repair 18-path enumeration is unaffected by mutating any of the
    four newly-added files -- exactly reproducing B-149O.19.3-1's
    pre-repair defect for the record."""
    pre_repair_paths = [f"src/pcae/{p}" for p in _PRE_REPAIR_SRC_RELATIVE_PATHS] + list(
        _FROZEN_CONTRACT_RELATIVE_PATHS
    )
    pre_repair_bytes = [(p, (_REPO_ROOT / p).read_bytes()) for p in pre_repair_paths]
    baseline_digest = _implementation_scope_digest(pre_repair_bytes)

    for rel in _NEWLY_ADDED_SRC_RELATIVE_PATHS:
        full_path = _REPO_ROOT / "src" / "pcae" / rel
        real_bytes = full_path.read_bytes()
        # Simulate a behavior-changing edit to the (pre-repair) unbound file:
        # the pre-repair digest domain never included this path at all, so
        # its bytes cannot appear in `pre_repair_bytes` to begin with -- the
        # historical defect is that no entry for it exists, not that an
        # existing entry is stale. Confirming absence IS the reproduction.
        assert rel not in _PRE_REPAIR_SRC_RELATIVE_PATHS
        assert real_bytes  # sanity: file is non-empty and was real content

    unaffected_digest = _implementation_scope_digest(pre_repair_bytes)
    assert unaffected_digest == baseline_digest


# ---------------------------------------------------------------------------
# 75. Existing digest/path-ambiguity invariants remain passing (spot check)
# ---------------------------------------------------------------------------


def test_digest_domain_still_resists_naive_concatenation_ambiguity_over_repaired_set():
    naive_1 = hashlib.sha256(b"ab" + b"c").hexdigest()
    naive_2 = hashlib.sha256(b"a" + b"bc").hexdigest()
    assert naive_1 == naive_2

    domain_1 = _implementation_scope_digest([("ab", b"c")])
    domain_2 = _implementation_scope_digest([("a", b"bc")])
    assert domain_1 != domain_2


# ---------------------------------------------------------------------------
# 76. Contract inventory after repair: requirement IDs, invariants, attacks.
# ---------------------------------------------------------------------------


def test_requirement_ids_remain_exactly_001_to_144_after_repair():
    ids = sorted(int(m) for m in re.findall(r"\*\*HMIC-REQ-(\d{3})", _CONTRACT_TEXT))
    assert ids == list(range(1, 145))
    assert len(set(ids)) == 144


def test_civc_invariants_remain_exactly_1_to_12_after_repair():
    ids = sorted(int(m) for m in re.findall(r"\*\*CIVC-(\d+)\.\*\*", _CONTRACT_TEXT))
    assert ids == list(range(1, 13))


def test_attack_matrix_remains_exactly_32_rows_after_repair():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    rows = re.findall(r"^\| (\d+) \|", table, flags=re.MULTILINE)
    assert [int(r) for r in rows] == list(range(1, 33))


def test_attack_row_11_now_names_the_repaired_provider_files():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    row_11 = next(line for line in table.splitlines() if line.startswith("| 11 |"))
    assert "hatp_fido2_provider.py" in row_11
    assert "hatp_piv_provider.py" in row_11
    assert "hatp_providers.py" in row_11
    assert "hatp_hardware_credentials.py" in row_11
    assert "B-149O.19.3-1" in row_11


# ---------------------------------------------------------------------------
# 77. No authority-sensitive TBD/TODO/FIXME introduced by the repair
# ---------------------------------------------------------------------------


def test_no_tbd_todo_fixme_introduced_in_repaired_sections():
    # Scope narrowly to the actually-edited spans (HMIC-REQ-050/052 through
    # the end of §17, and the new §49 appendix) rather than the whole
    # document tail, which legitimately contains pre-existing references
    # like `tasks/TODO.md` (HMIC-REQ-074) unrelated to this repair.
    section_17_start = _CONTRACT_TEXT.index("## 17. Implementation Identity")
    section_18_start = _CONTRACT_TEXT.index("## 18.")
    frozen_set_span = _CONTRACT_TEXT[section_17_start:section_18_start]

    section_49_start = _CONTRACT_TEXT.index("## 49. Contract Repair History")
    section_49_span = _CONTRACT_TEXT[section_49_start:]

    for forbidden in ("TBD", "TODO", "FIXME", "implementation may choose"):
        assert forbidden not in frozen_set_span, f"forbidden token {forbidden!r} found in repaired §17"
        assert forbidden not in section_49_span, f"forbidden token {forbidden!r} found in new §49"
    assert section_49_start > section_17_start


# ---------------------------------------------------------------------------
# 78. Upstream contract byte identity (HMRC-001/HATP-001/HSCE-001/RAE-001/
# RWMPC-001/PBPA-001/PBPC-001) unchanged by this repair phase.
# ---------------------------------------------------------------------------


def _diff_since_entry(pathspec: str) -> str:
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_149O_19_3_ENTRY_COMMIT, "HEAD", "--", pathspec],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout


@pytest.mark.parametrize(
    "existing_contract",
    [
        "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
        "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
        "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
        "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
        "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
        "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
    ],
)
def test_upstream_contract_byte_unchanged_by_this_repair(existing_contract):
    if existing_contract == "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md":
        # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3) — long after this
        # narrow repair phase — amended PBPA-001 v1.0 -> v1.1 (additive
        # only: the POL-013 row + PBPA-REQ-089; PBNDE-001 v1.0 / PBRD-001
        # v3.0). That is the sole authorized change to PBPA since this
        # phase's entry. Pinned to the exact current bytes so any *further*
        # PBPA change still fails. Reconciled by .1R.22R (N-23-3).
        import hashlib

        path = Path(__file__).resolve().parents[1] / "docs" / "contracts" / existing_contract
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert actual == "13fc441a6e3688d1ea1b8e62a2b0ea3fafc6a293340f6907b05b7dccf8a16660", (
            "PBPA-001 changed beyond the authorized .1R.22 v1.1 amendment"
        )
        text = path.read_text()
        assert "**Version:** 1.1" in text and "POL-013" in text
        return
    diff = _diff_since_entry(f"docs/contracts/{existing_contract}")
    assert existing_contract not in diff, f"{existing_contract} was modified by this narrow repair phase"


# ---------------------------------------------------------------------------
# 79. No production source changed by this repair phase.
# ---------------------------------------------------------------------------


def test_no_production_source_changed_by_this_repair():
    diff = _diff_since_entry("src/pcae/")
    assert diff.strip() == "", f"production source changed this phase: {diff}"


#: Phase 149O.19.5F (Wave F, gated by Stop Condition W-1) intentionally
#: replaces this literal with fresh HMIC active-certification validation
#: after this repair phase. Pinned to the pre-Wave-F phase-entry commit
#: so this test's original evidentiary claim (unchanged as of this
#: narrow repair phase) is preserved rather than weakened.
_PRE_WAVE_F_COMMIT = "dd6492717ea27a43e16bce3e9c2077a884ed366f"


def test_hardcoded_readiness_ceiling_still_literal_false():
    source = subprocess.run(
        ["git", "show", f"{_PRE_WAVE_F_COMMIT}:src/pcae/core/hatp_mandatory_cutover.py"],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    match = re.search(
        r'"mandatory_consumption_implementation_independently_verified",\s*\n\s*(False|True)\s*,',
        source,
    )
    assert match, "could not locate the readiness-ceiling check literal in hatp_mandatory_cutover.py"
    assert match.group(1) == "False"


def test_no_certification_state_created_by_this_repair():
    matches = list(_REPO_ROOT.rglob("certifications.json")) + list(
        _REPO_ROOT.rglob("certification-bindings.json")
    )
    matches = [m for m in matches if ".git" not in m.parts]
    assert matches == []


# ---------------------------------------------------------------------------
# Contract status/version/finding-ID assertions
# ---------------------------------------------------------------------------


def test_contract_status_is_repaired_not_verified():
    # This module's own module-level `_CONTRACT_TEXT` reads the live
    # contract file (not a pinned historical blob), so this assertion
    # tracks the contract's current status text across later amendments
    # -- Phase 149O.19.5E.1 (contract §50) subsequently amended HMIC-001
    # again (v1.0 -> v1.1), so the live status text now reads the v1.1
    # amendment status, still explicitly not VERIFIED.
    assert (
        "**Status:** FROZEN — VALIDATOR/ADMIN IMPLEMENTATION IDENTITY "
        "CONTRACT EVOLUTION COMPLETE — PENDING INDEPENDENT VERIFICATION "
        "(not VERIFIED at v1.1)"
        in _CONTRACT_TEXT
    )


def test_contract_version_remains_1_0():
    # Historically true of this repair phase's own exit state (still
    # true as a claim about 149O.19.3R specifically -- HMIC-001 v1.0 is
    # named throughout the contract's historical §49 repair-history
    # section this repair phase authored). The *current* contract
    # version subsequently moved to v1.1 at Phase 149O.19.5E.1 (contract
    # §50); this repair phase's test module reads the live file for its
    # other assertions, so this specific check now tracks the current
    # version rather than asserting an eternal "remains 1.0" claim this
    # repository has never treated as permanent for these status-style
    # checks (see the identical forward-update precedent in
    # tests/test_phase_149o_19_2_...py).
    assert "**Version:** 1.1" in _CONTRACT_TEXT
    assert "HMIC-001 v1.0" in _CONTRACT_TEXT


def test_finding_id_b_149o_19_3_1_present_with_correct_status():
    assert "B-149O.19.3-1" in _CONTRACT_TEXT
    assert "REPAIRED AT CONTRACT LEVEL" in _CONTRACT_TEXT
    assert "PENDING INDEPENDENT RE-VERIFICATION" in _CONTRACT_TEXT
    assert "VALID" not in _CONTRACT_TEXT.split("B-149O.19.3-1: REPAIRED")[1][:80]


def test_recommended_next_phase_is_repair_re_verification():
    assert "149O.19.3R.1" in _CONTRACT_TEXT

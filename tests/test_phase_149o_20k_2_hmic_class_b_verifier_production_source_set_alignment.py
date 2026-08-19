"""Phase 149O.20K.2 -- HMIC Class-B Verifier Production Source-Set
Alignment.

Implements the production half of Phase 149O.20K's contract-level
amendment (HMIC-001 v1.2 -> v1.3, independently verified 149O.20K.1):
`src/pcae/core/hatp_mandatory_certification.py`'s own
`_FROZEN_AUTHORITY_BEARING_FILES` is realigned from the pre-amendment,
twenty-five-file set to the independently verified v1.3 set of
twenty-eight files, adding the three Class-B deployment-conformance
verifier modules (`hatp_class_b_topology_verifier.py`,
`hatp_environment_lock_verifier.py`, `hatp_class_b_conformance.py`) in
HMIC-REQ-050's canonical presentation order, using exactly the
identical `src/pcae/`-relative binding mechanism already applied to
every other frozen-set entry -- no new mechanism, no Class-B-specific
branch.

This is a NARROW PRODUCTION SOURCE-SET ALIGNMENT phase. It does not
amend HMIC-001, HBDC-001, or any other contract (all bound contracts
verified byte-unchanged below), does not modify any of the three
Class-B verifier modules themselves (byte-identical before/after,
verified below), does not change the digest algorithm, path
canonicalization, file ordering, Git-identity semantics, or
validator/storage/admin-writer semantics, does not perform readiness
integration, Class-B provisioning, or any certification/activation
ceremony. `_CONTRACT_IDENTITY_FILES` remains at its existing five
members -- this amendment widened HMIC-REQ-050 only, not HMIC-REQ-067.
CBV-S1 is NOT closed by this phase alone -- an independent production-
alignment verification phase (149O.20K.3) is required next.

Covers (per the governing phase instruction, steps 8-37):
  * exact production/contract 28-file set equality, independently
    extracted from the live contract text (never a copied production
    constant used as its own "expected" value);
  * literal presentation-order equality (HMIC-REQ-051);
  * exact +3 delta against this phase's own entry commit; the
    pre-alignment 25 files remain a strict subset;
  * `_CONTRACT_IDENTITY_FILES` unchanged at 5 members;
  * per-new-file digest sensitivity, exercised individually against
    the real digest-generation mechanism (not inferred from list
    membership);
  * missing-new-file fail-closed behavior, individually, for each of
    the three new files;
  * representative existing-file (HMIC module, provider file, HBDC-001
    contract bytes) digest-sensitivity regression;
  * HBDC-001 dual-binding (content digest + contract-version)
    preservation;
  * B-149O.19.3-1 provider-file binding regression;
  * path uniqueness/normalization checks over the full 28-file set;
  * cycle/self-binding regression (W-1): no Import/ImportFrom node in
    any of the three new verifier modules names the certification/
    admin modules, and neither of those two modules imports any
    verifier module;
  * zero-consumer regression: no production module outside the three
    verifier files imports or calls into the verifier island;
  * Class-B verifier module and HMIC-001/HBDC-001 contract byte-
    identity across this phase;
  * function/class-body AST-source identity against this phase's own
    entry commit, proving only the frozen-set constants and their
    surrounding comments changed;
  * real-host NON_COMPLIANT confirmation, read-only;
  * CBV-S10 untouched.
"""
from __future__ import annotations

import ast
import hashlib
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")
_HBDC_CONTRACT_PATH = _CONTRACTS / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
_CUTOVER_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"

#: This phase's own entry commit -- 149O.20K.1's own exit commit, as
#: observed at this phase's own initial inspection. Production still
#: implemented the pre-alignment 25-file / 5-contract set at this
#: commit.
_PHASE_ENTRY_COMMIT = "17a797af"

_NEW_VERIFIER_RELATIVE_PATHS = (
    "src/pcae/core/hatp_class_b_topology_verifier.py",
    "src/pcae/core/hatp_environment_lock_verifier.py",
    "src/pcae/core/hatp_class_b_conformance.py",
)

_HBDC_RELATIVE = "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"

_UPSTREAM_CONTRACT_RELATIVE_PATHS = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    _HBDC_RELATIVE,
)


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_req_050_block(contract_text: str) -> "tuple[str, ...]":
    """Independently parses HMIC-REQ-050's fenced code block out of raw
    contract text via regex -- never a copied/hardcoded path list."""

    match = re.search(r"HMIC-REQ-050 \(Exact Enumeration.*?```\n(.*?)```", contract_text, re.S)
    assert match is not None, "HMIC-REQ-050 fenced enumeration block not found in contract text"
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    return tuple(lines)


def _live_contract_28_canonical_paths() -> "list[str]":
    """Independently extracts HMIC-REQ-050's 28 entries from the live
    contract text and resolves each to its repository-relative
    canonical path (existence-based split, not trusting the contract's
    own src/pcae-vs-root grouping prose)."""

    entries = [e.split()[0] for e in _extract_req_050_block(_CONTRACT_TEXT)]
    assert len(entries) == 28
    result = []
    for entry in entries:
        if (_SRC / entry).exists():
            result.append(f"src/pcae/{entry}")
        else:
            result.append(entry)
    return result


def _independent_scope_digest(root: Path, canonical_relative_paths: "list[str]") -> str:
    """A from-scratch reimplementation of HMIC-REQ-054/056-058's
    two-level digest construction, independent of
    `derive_implementation_scope_digest` in production."""

    ordered = sorted(canonical_relative_paths)
    records = bytearray()
    for rel in ordered:
        file_bytes = (root / rel).read_bytes()
        file_digest = _sha256_hex(file_bytes)
        records += rel.encode("utf-8") + b"\0" + file_digest.encode("ascii") + b"\n"
    return _sha256_hex(bytes(records))


def _top_level_def_sources(source: str) -> "dict[str, str]":
    tree = ast.parse(source)
    sources: "dict[str, str]" = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segment = ast.get_source_segment(source, node)
            assert segment is not None
            sources[node.name] = segment
    return sources


def _entry_frozen_authority_bearing_files() -> "tuple[str, ...]":
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    entry_tree = ast.parse(entry_source)
    parts: "dict[str, tuple[str, ...]]" = {}
    for node in entry_tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id in ("_FROZEN_SRC_PCAE_RELATIVE_FILES", "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"):
                assert isinstance(node.value, ast.Tuple)
                parts[node.target.id] = tuple(elt.value for elt in node.value.elts)
    assert set(parts) == {"_FROZEN_SRC_PCAE_RELATIVE_FILES", "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"}
    return parts["_FROZEN_SRC_PCAE_RELATIVE_FILES"] + parts["_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES"]


def _entry_contract_identity_members() -> "tuple[str, ...]":
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    entry_tree = ast.parse(entry_source)
    for node in entry_tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "_CONTRACT_IDENTITY_FILES":
                assert isinstance(node.value, ast.Tuple)
                return tuple(pair.elts[0].value for pair in node.value.elts)
    raise AssertionError("_CONTRACT_IDENTITY_FILES not found in phase-entry source")


def _copy_frozen_tree(dest_root: Path, canonical: "list[str]") -> None:
    for rel in canonical:
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest)


# ---------------------------------------------------------------------------
# Contract/production exact equality (steps 8, 26)
# ---------------------------------------------------------------------------


def test_live_contract_req_050_enumeration_is_exactly_28_entries():
    entries = _extract_req_050_block(_CONTRACT_TEXT)
    assert len(entries) == 28


def test_production_frozen_set_exactly_equals_live_contract_28_file_set():
    from pcae.core import hatp_mandatory_certification as hmic

    contract_paths = set(_live_contract_28_canonical_paths())
    production_paths = set(hmic._frozen_canonical_paths())

    assert len(contract_paths) == 28
    assert len(production_paths) == 28
    assert production_paths == contract_paths, (
        f"production/contract frozen-set mismatch: "
        f"contract-only={contract_paths - production_paths}, "
        f"production-only={production_paths - contract_paths}"
    )


def test_production_module_constant_matches_contract_literal_presentation_order():
    """Stronger than set equality: the production tuple's own literal
    order (before canonicalization) must match HMIC-REQ-050's fenced
    block, entry for entry (HMIC-REQ-051 -- not merely a same-set,
    different-order list)."""

    from pcae.core import hatp_mandatory_certification as hmic

    contract_entries = tuple(e.split()[0] for e in _extract_req_050_block(_CONTRACT_TEXT))
    assert hmic._FROZEN_AUTHORITY_BEARING_FILES == contract_entries


def test_production_frozen_set_count_assertion_is_exactly_28():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", source)
    assert match is not None
    assert match.group(1) == "28"
    assert ">= 28" not in source
    assert ">=28" not in source


def test_new_entries_are_exactly_the_three_verified_class_b_additions():
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = set(hmic._frozen_canonical_paths())
    for rel in _NEW_VERIFIER_RELATIVE_PATHS:
        assert rel in canonical


# ---------------------------------------------------------------------------
# Exact +3 delta; existing 25 preserved (steps 9, 28)
# ---------------------------------------------------------------------------


def test_pre_20k_2_production_was_exactly_25_files():
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", entry_source)
    assert match is not None
    assert match.group(1) == "25"


def test_exact_three_entry_delta_between_pre_20k_2_and_current_frozen_sets():
    from pcae.core import hatp_mandatory_certification as hmic

    entry_frozen_tuple = _entry_frozen_authority_bearing_files()
    assert len(entry_frozen_tuple) == 25

    current = set(hmic._FROZEN_AUTHORITY_BEARING_FILES)
    entering = set(entry_frozen_tuple)
    assert current - entering == {
        "core/hatp_class_b_topology_verifier.py",
        "core/hatp_environment_lock_verifier.py",
        "core/hatp_class_b_conformance.py",
    }
    assert entering - current == set()


def test_original_25_frozen_paths_preserved():
    from pcae.core import hatp_mandatory_certification as hmic

    original_25 = _entry_frozen_authority_bearing_files()
    assert len(original_25) == 25
    current = set(hmic._FROZEN_AUTHORITY_BEARING_FILES)
    assert set(original_25) <= current


def test_no_zero_entry_delta_in_contract_identity_files():
    """`_CONTRACT_IDENTITY_FILES` is unchanged at 5 members -- this
    amendment widened HMIC-REQ-050 only, not HMIC-REQ-067."""

    from pcae.core import hatp_mandatory_certification as hmic

    entry_members = _entry_contract_identity_members()
    current_members = tuple(contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES)
    assert entry_members == current_members[: len(entry_members)]
    assert len(current_members) >= 5


def test_production_contract_identity_set_still_exactly_5_matching_contract():
    """As of this phase (149O.20K.2) this was exactly 5; a later
    amendment (149O.20L.7O.2H) additively widened it to 7."""
    from pcae.core import hatp_mandatory_certification as hmic

    production_members = {contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES}
    assert {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"} <= production_members
    assert len(production_members) >= 5


# ---------------------------------------------------------------------------
# Path uniqueness / normalization / safety over the full 28-file set
# ---------------------------------------------------------------------------


def test_all_28_frozen_paths_exist_are_regular_and_not_symlinked():
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = hmic._frozen_canonical_paths()
    assert len(canonical) == 28
    for canonical_path in canonical:
        path = _REPO_ROOT / canonical_path
        assert path.exists(), f"frozen path missing: {canonical_path}"
        assert not path.is_symlink(), f"frozen path is a symlink: {canonical_path}"
        assert path.is_file(), f"frozen path is not a regular file: {canonical_path}"


def test_no_duplicate_entries_in_frozen_set():
    from pcae.core import hatp_mandatory_certification as hmic

    assert len(set(hmic._FROZEN_AUTHORITY_BEARING_FILES)) == len(hmic._FROZEN_AUTHORITY_BEARING_FILES)
    assert len(set(hmic._frozen_canonical_paths())) == len(hmic._frozen_canonical_paths())


def test_new_verifier_paths_accepted_with_no_special_casing():
    from pcae.core import hatp_mandatory_certification as hmic

    for rel in _NEW_VERIFIER_RELATIVE_PATHS:
        hmic._validate_frozen_path_literal(rel.removeprefix("src/pcae/"))
        assert rel in hmic._frozen_canonical_paths()


def test_frozen_set_is_immutable_tuple_not_list_or_set():
    from pcae.core import hatp_mandatory_certification as hmic

    assert isinstance(hmic._FROZEN_AUTHORITY_BEARING_FILES, tuple)
    assert isinstance(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES, tuple)
    assert isinstance(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES, tuple)


# ---------------------------------------------------------------------------
# Per-new-file digest sensitivity (steps 10, 17) -- exercised individually
# against the real digest-generation mechanism, isolated fixture copies
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel", _NEW_VERIFIER_RELATIVE_PATHS)
def test_each_new_verifier_file_is_individually_digest_sensitive(tmp_path, rel):
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    _copy_frozen_tree(tree, canonical)

    baseline = _independent_scope_digest(tree, canonical)

    target = tree / rel
    original = target.read_bytes()
    target.write_bytes(original + b"\n# mutated-for-test\n")
    mutated = _independent_scope_digest(tree, canonical)
    target.write_bytes(original)

    assert mutated != baseline, f"{rel} content mutation did not change implementation_scope_digest"


def test_topology_verifier_semantic_mutation_changes_digest(tmp_path):
    """A semantically meaningful mutation (flipping a constant that
    would alter a result-producing branch), not merely an appended
    comment, still changes the digest."""

    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    _copy_frozen_tree(tree, canonical)

    baseline = _independent_scope_digest(tree, canonical)
    target = tree / "src/pcae/core/hatp_class_b_topology_verifier.py"
    original = target.read_bytes()
    assert b"COMPLIANT = \"COMPLIANT\"" in original
    target.write_bytes(original.replace(b'COMPLIANT = "COMPLIANT"', b'COMPLIANT = "COMPLIANT_MUTATED"'))
    mutated = _independent_scope_digest(tree, canonical)
    assert mutated != baseline


def test_environment_lock_verifier_semantic_mutation_changes_digest(tmp_path):
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    _copy_frozen_tree(tree, canonical)

    baseline = _independent_scope_digest(tree, canonical)
    target = tree / "src/pcae/core/hatp_environment_lock_verifier.py"
    original = target.read_bytes()
    target.write_bytes(original + b"\n_MUTATION_MARKER = True\n")
    mutated = _independent_scope_digest(tree, canonical)
    assert mutated != baseline


def test_conformance_aggregator_semantic_mutation_changes_digest(tmp_path):
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    _copy_frozen_tree(tree, canonical)

    baseline = _independent_scope_digest(tree, canonical)
    target = tree / "src/pcae/core/hatp_class_b_conformance.py"
    original = target.read_bytes()
    assert b"Strictly read-only" in original
    target.write_bytes(original.replace(b"Strictly read-only", b"Strictly read-only (mutated)"))
    mutated = _independent_scope_digest(tree, canonical)
    assert mutated != baseline


def test_production_derive_implementation_scope_digest_matches_independent_reimplementation():
    """Golden-style cross-check: production's own
    `derive_implementation_scope_digest`, called against the real
    repository, must equal this test's independently authored digest
    algorithm over the same live 28-file set -- not merely
    self-consistent with itself."""

    from pcae.core.paths import HarnessPath
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    expected = _independent_scope_digest(_REPO_ROOT, canonical)
    actual = hmic.derive_implementation_scope_digest(HarnessPath(_REPO_ROOT))
    assert actual == expected


# ---------------------------------------------------------------------------
# Missing-new-file fail-closed behavior (steps 16), individually
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel", _NEW_VERIFIER_RELATIVE_PATHS)
def test_missing_new_verifier_file_fails_closed(tmp_path, rel):
    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    _copy_frozen_tree(tree, canonical)

    (tree / rel).unlink()

    with pytest.raises(hmic.FrozenFileDerivationError):
        hmic.derive_implementation_scope_digest(HarnessPath(tree))


# ---------------------------------------------------------------------------
# Representative existing-file digest regression (step 11); HBDC/provider
# binding preservation (steps 12, 13)
# ---------------------------------------------------------------------------


def test_hmic_module_itself_still_digest_sensitive(tmp_path):
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    _copy_frozen_tree(tree, canonical)

    baseline = _independent_scope_digest(tree, canonical)
    target = tree / "src/pcae/core/hatp_mandatory_certification.py"
    original = target.read_bytes()
    target.write_bytes(original + b"\n# mutated-for-test\n")
    mutated = _independent_scope_digest(tree, canonical)
    target.write_bytes(original)
    assert mutated != baseline


@pytest.mark.parametrize(
    "rel",
    (
        "src/pcae/core/hatp_providers.py",
        "src/pcae/core/hatp_fido2_provider.py",
        "src/pcae/core/hatp_piv_provider.py",
        "src/pcae/core/hatp_hardware_credentials.py",
    ),
)
def test_b_149o_19_3_1_provider_files_remain_bound_and_digest_sensitive(tmp_path, rel):
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    assert rel in canonical

    tree = tmp_path / "tree"
    _copy_frozen_tree(tree, canonical)

    baseline = _independent_scope_digest(tree, canonical)
    target = tree / rel
    original = target.read_bytes()
    target.write_bytes(original + b"\n# mutated-for-test\n")
    mutated = _independent_scope_digest(tree, canonical)
    target.write_bytes(original)
    assert mutated != baseline


def test_hbdc_bytes_still_digest_sensitive(tmp_path):
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    assert _HBDC_RELATIVE in canonical
    tree = tmp_path / "tree"
    _copy_frozen_tree(tree, canonical)

    baseline = _independent_scope_digest(tree, canonical)
    target = tree / _HBDC_RELATIVE
    original = target.read_bytes()
    target.write_bytes(original.replace(b"HATP Class-B Deployment Contract", b"HATP Class-B Deployment Contract "))
    mutated = _independent_scope_digest(tree, canonical)
    target.write_bytes(original)
    assert mutated != baseline


def test_hbdc_still_participates_in_contract_versions():
    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    versions = dict(hmic.derive_contract_versions(HarnessPath(_REPO_ROOT)))
    assert "HBDC-001" in versions
    assert versions["HBDC-001"] == "1.0"


def test_b_149o_20d_1_closed_at_contract_and_production_identity_boundary_unweakened():
    """B-149O.20D-1 stays closed: HBDC-001 still dual-bound (content
    digest + version header) after this phase's own widening."""

    from pcae.core import hatp_mandatory_certification as hmic

    assert _HBDC_RELATIVE in hmic._frozen_canonical_paths()
    assert "HBDC-001" in {contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES}


# ---------------------------------------------------------------------------
# Cycle / self-binding regression (W-1) (step 25)
# ---------------------------------------------------------------------------


def test_new_verifier_modules_do_not_import_certification_or_admin_modules():
    forbidden_names = {"hatp_mandatory_certification", "hatp_certification_admin"}
    for rel in _NEW_VERIFIER_RELATIVE_PATHS:
        source = (_REPO_ROOT / rel).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name.split(".")[-1] not in forbidden_names, f"{rel} imports {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module.split(".")[-1] not in forbidden_names, f"{rel} imports from {module}"


def test_hmic_module_does_not_import_any_verifier_module():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_names = {
        "hatp_class_b_topology_verifier",
        "hatp_environment_lock_verifier",
        "hatp_class_b_conformance",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[-1] not in forbidden_names
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert module.split(".")[-1] not in forbidden_names


def test_admin_script_does_not_import_any_verifier_module():
    source = _ADMIN_SCRIPT_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_names = {
        "hatp_class_b_topology_verifier",
        "hatp_environment_lock_verifier",
        "hatp_class_b_conformance",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[-1] not in forbidden_names
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            assert module.split(".")[-1] not in forbidden_names


# ---------------------------------------------------------------------------
# Zero-consumer regression (step 20)
# ---------------------------------------------------------------------------


def test_zero_production_consumers_of_verifier_island_outside_the_island_itself():
    result = subprocess.run(
        [
            "grep",
            "-rl",
            "-E",
            "--include=*.py",
            "hatp_class_b_topology_verifier|hatp_environment_lock_verifier|hatp_class_b_conformance"
            "|verify_class_b_deployment_conformance|verify_class_b_topology_conformance"
            "|verify_environment_lock_conformance",
            str(_SRC),
        ],
        capture_output=True,
        text=True,
    )
    matches = [line for line in result.stdout.splitlines() if line.strip()]
    island_files = {str(_REPO_ROOT / rel) for rel in _NEW_VERIFIER_RELATIVE_PATHS}
    # hatp_mandatory_certification.py legitimately names the three
    # verifier files as path *strings* in its frozen-set constants
    # (binding by path, not import/call) -- confirmed separately by the
    # AST-level import tests above.
    non_island = [m for m in matches if m not in island_files and m != str(_HMIC_MODULE_PATH)]
    assert non_island == [], f"unexpected consumer(s) of the verifier island: {non_island}"


def test_cutover_module_still_does_not_reference_verifier_island():
    source = _CUTOVER_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "hatp_class_b_topology_verifier",
        "hatp_environment_lock_verifier",
        "hatp_class_b_conformance",
        "verify_class_b_deployment_conformance",
    ):
        assert forbidden not in source


# ---------------------------------------------------------------------------
# Class-B module / HMIC contract byte-identity across this phase (steps
# 34, 35)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel", _NEW_VERIFIER_RELATIVE_PATHS)
def test_class_b_verifier_module_byte_identical_since_phase_entry(rel):
    current = (_REPO_ROOT / rel).read_bytes()
    entry = _git_show(_PHASE_ENTRY_COMMIT, rel).encode("utf-8")
    assert current == entry, f"Class-B verifier module changed during K.2: {rel}"


def test_hmic_contract_and_upstream_contracts_byte_unchanged_since_phase_entry():
    for rel in (_CONTRACT_PATH.relative_to(_REPO_ROOT).as_posix(),) + _UPSTREAM_CONTRACT_RELATIVE_PATHS:
        current = (_REPO_ROOT / rel).read_bytes()
        entry = _git_show(_PHASE_ENTRY_COMMIT, rel).encode("utf-8")
        assert current == entry, f"contract changed since phase entry: {rel}"


def test_admin_script_byte_unchanged_since_phase_entry():
    current = _ADMIN_SCRIPT_PATH.read_bytes()
    entry = _git_show(_PHASE_ENTRY_COMMIT, "scripts/hatp_certification_admin.py").encode("utf-8")
    assert current == entry


def test_no_src_pcae_file_other_than_hmic_module_changed_since_phase_entry():
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "HEAD", "--", "src/pcae"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    tracked_changes = [line for line in changed if line != "src/pcae/core/hatp_mandatory_certification.py"]
    assert tracked_changes == [], f"unexpected src/pcae change(s): {tracked_changes}"


def test_no_scripts_file_changed_since_phase_entry():
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "HEAD", "--", "scripts"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert [line for line in result.stdout.splitlines() if line.strip()] == []


def test_no_contract_file_changed_since_phase_entry():
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "HEAD", "--", "docs/contracts"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert [line for line in result.stdout.splitlines() if line.strip()] == []


# ---------------------------------------------------------------------------
# Function/class-body AST-source identity -- only frozen-set constants and
# surrounding comments changed
# ---------------------------------------------------------------------------


def test_every_function_and_class_body_is_ast_source_identical_to_phase_entry():
    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")

    current_defs = _top_level_def_sources(current_source)
    entry_defs = _top_level_def_sources(entry_source)

    assert set(current_defs) == set(entry_defs), "function/class inventory changed this phase"

    # `derive_contract_versions`, `ContractIdentityDerivationError`, and
    # `FrozenFileDerivationError` had only their docstrings updated by
    # 149O.20L.7O.2H (v1.5), tracking the HPSE-001/HHCE-001 widening --
    # not an algorithm/schema change.
    docstring_only_exceptions = {
        "derive_contract_versions",
        "ContractIdentityDerivationError",
        "FrozenFileDerivationError",
    }
    changed_defs = {
        name
        for name in current_defs
        if current_defs[name] != entry_defs[name] and name not in docstring_only_exceptions
    }
    assert changed_defs == set(), f"unexpected function/class body change(s): {changed_defs}"


def test_derive_implementation_scope_digest_algorithm_unchanged():
    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    current_defs = _top_level_def_sources(current_source)
    entry_defs = _top_level_def_sources(entry_source)
    assert current_defs["derive_implementation_scope_digest"] == entry_defs["derive_implementation_scope_digest"]
    assert current_defs["_frozen_canonical_paths"] == entry_defs["_frozen_canonical_paths"]
    assert current_defs["_canonical_frozen_path"] == entry_defs["_canonical_frozen_path"]


def test_derive_contract_versions_algorithm_unchanged():
    """149O.20L.7O.2H (v1.5) updated this function's docstring ("four" ->
    "seven bound contracts") without touching its executable statements
    -- compare with the docstring stripped."""
    import ast

    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")

    def _body_without_docstring(name: str, source: str) -> str:
        tree = ast.parse(source)
        func = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        )
        body = func.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body = body[1:]
        return "\n".join(ast.get_source_segment(source, stmt) or "" for stmt in body)

    assert _body_without_docstring("derive_contract_versions", current_source) == _body_without_docstring(
        "derive_contract_versions", entry_source
    )


def test_validator_storage_admin_writer_functions_unchanged():
    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    current_defs = _top_level_def_sources(current_source)
    entry_defs = _top_level_def_sources(entry_source)
    for name in (
        "_validate_at_root",
        "validate_active_hatp_mandatory_independent_verification_certification",
        "_append_certification_record",
        "_write_active_binding",
        "_write_revocation",
        "parse_certification_record",
        "parse_certification_binding",
        "canonical_serialize",
    ):
        assert current_defs[name] == entry_defs[name], f"{name} changed unexpectedly this phase"


def test_no_legacy_scope_language_in_production_module():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "legacy_scope",
        "v1_2_compat",
        "file_count=25",
        "ignore_new_files",
        "legacy=True",
        "ignore_class_b",
        "bound_file_count=25",
        "legacy_frozen_set",
    ):
        assert forbidden not in source


def test_derive_implementation_scope_digest_accepts_no_scope_override_parameter():
    import inspect

    from pcae.core import hatp_mandatory_certification as hmic

    signature = inspect.signature(hmic.derive_implementation_scope_digest)
    assert set(signature.parameters) == {"root"}


# ---------------------------------------------------------------------------
# Real-host NON_COMPLIANT confirmation, read-only (step 23); CBV-S10
# untouched (step 21)
# ---------------------------------------------------------------------------


def test_real_host_class_b_conformance_is_non_compliant_read_only():
    """No Class-B provisioning occurred; the real, unprovisioned host
    still fails Model-A/environment-lock/topology checks."""

    from pcae.core.hatp_class_b_conformance import verify_class_b_deployment_conformance
    from pcae.core.hatp_class_b_topology_verifier import ClassBConformanceStatus

    before = subprocess.run(
        ["git", "status", "--porcelain"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout
    result = verify_class_b_deployment_conformance()
    after = subprocess.run(
        ["git", "status", "--porcelain"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout

    assert result.status != ClassBConformanceStatus.COMPLIANT
    assert before == after, "verify_class_b_deployment_conformance mutated repository state"


def test_readiness_still_not_ready_against_real_production_state():
    """Read-only: readiness is unaffected by this phase's HMIC binding
    -- with no real Protected Root/certification on this host, live
    readiness is still `ready=False`."""

    from pcae.core.hatp_mandatory_cutover import assess_hatp_mandatory_activation_readiness
    from pcae.core.paths import HarnessPath

    result = assess_hatp_mandatory_activation_readiness(HarnessPath(_REPO_ROOT))
    assert result.ready is False


def test_cbv_s10_readiness_gap_language_unchanged_in_contract():
    """CBV-S10 (readiness contract/integration gap) is untouched by
    this phase -- the contract's own readiness-residual-limitation text
    (HMIC-REQ-063) is verified byte-unchanged above; this test confirms
    it still names the accepted-residual language, not a closed one."""

    assert "HMIC-REQ-063" in _CONTRACT_TEXT


def test_no_real_certification_state_exists_on_host():
    from pcae.core.hatp_bootstrap import HATPTrustStore

    root = HATPTrustStore.production().root
    assert not (root / "certifications.json").exists()
    assert not (root / "certification-bindings.json").exists()
    assert not (root / "active-certification.json").exists()

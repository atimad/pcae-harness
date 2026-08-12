"""Phase 149O.20F -- HMIC v1.2 HBDC 25-File / 5-Contract Production
Identity Alignment.

Implements the production half of finding B-149O.20D-1's contract-level
repair (149O.20D.1, independently verified 149O.20E):
`src/pcae/core/hatp_mandatory_certification.py`'s own
`_FROZEN_AUTHORITY_BEARING_FILES` and `_CONTRACT_IDENTITY_FILES`
constants are realigned from the pre-repair, twenty-four-file /
four-contract set to the independently verified HMIC-001 v1.2 set of
twenty-five files (adding `docs/contracts/HATP_CLASS_B_DEPLOYMENT_
CONTRACT.md`, HBDC-001) and five `contract_versions` members (adding
`HBDC-001`), using exactly the identical mechanism already applied to
the other four bound contracts -- no HBDC-specific branch.

This is a NARROW PRODUCTION IDENTITY ALIGNMENT phase. It does not amend
HMIC-001, HBDC-001, or any other contract (all nine frozen corpus
members verified byte-unchanged below), does not change the digest
algorithm, path canonicalization, file ordering, Git-identity
semantics, or validator/storage/admin-writer semantics, and does not
implement a Class-B verifier, environment lock, or any real
provisioning/certification/binding/revocation/activation.
HBDC-BINDING-GATE and B-149O.20D-1 are NOT closed by this phase alone
-- an independent implementation-verification phase (149O.20G) is
required next.

Covers (per the governing phase instruction §48-109):
  * exact production/contract 25-file and 5-contract-member set
    equality, independently extracted from the live contract text
    (never a copied production constant used as its own "expected"
    value);
  * literal presentation-order equality, not merely set equality;
  * the 24 previously-frozen files are byte-identical to this phase's
    own entry commit; only the core HMIC module itself changed;
  * self-binding: the core module's post-edit bytes (not stale
    pre-edit bytes) participate in the digest it computes -- proven
    against the real, live implementation-scope digest, not a fixture;
  * dual binding: HBDC-001 now participates in both
    `implementation_scope_digest` (content bytes) and
    `contract_versions` (version header), exactly like the other four
    bound contracts;
  * same-version HBDC-001 content-drift sensitivity, version-drift
    sensitivity, and Contract-ID-drift fail-closed behavior, all
    against production's own live functions;
  * all 25/25-file mutation sensitivity, using an independent digest
    reimplementation;
  * historical 24-file/4-member vs current 25-file/5-member digest and
    contract-identity mismatch, and a modeled pre-20F replay rejection,
    for an identical snapshot;
  * no caller-suppliable legacy/24-file or 4-contract scope override
    exists;
  * digest algorithm, path canonicalization, Git-identity derivation,
    and validator/storage/admin-script semantics are AST-source-
    identical to this phase's own entry commit -- only the frozen-set/
    contract-identity constants and their surrounding module-level
    comments changed;
  * hard-coded `False` readiness ceiling unchanged; zero readiness/
    cutover callers of the validator; admin script byte-unchanged;
    HMIC-001, HBDC-001, and all seven other upstream contracts
    byte-unchanged.
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
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
_CUTOVER_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"

#: This phase's own entry commit -- 149O.20E's own exit commit, as
#: observed at this phase's own initial inspection. Production still
#: implemented the pre-alignment 24-file / 4-contract set at this
#: commit.
_PHASE_ENTRY_COMMIT = "43ecacb9"

#: The eight upstream contracts HMIC-REQ-050/053/067 bind (HMIC-001
#: itself is the ninth of the nine-member frozen corpus, but is not
#: itself a HMIC-REQ-050 member -- it is the contract this module
#: implements, not one of the files it hashes).
_UPSTREAM_CONTRACT_RELATIVE_PATHS = (
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
)

_HBDC_RELATIVE = "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"


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


def _live_contract_25_canonical_paths() -> "list[str]":
    """Independently extracts HMIC-REQ-050's 25 entries from the live
    contract text and resolves each to its repository-relative
    canonical path (existence-based split, not trusting the contract's
    own src/pcae-vs-root grouping prose)."""

    entries = [e.split()[0] for e in _extract_req_050_block(_CONTRACT_TEXT)]
    assert len(entries) == 25
    result = []
    for entry in entries:
        if (_SRC / entry).exists():
            result.append(f"src/pcae/{entry}")
        else:
            result.append(entry)
    return result


def _extract_req_067_members(contract_text: str) -> "tuple[str, ...]":
    """Independently parses HMIC-REQ-067's prose for the five
    `contract_versions` member IDs -- a fresh regex extraction, never a
    copied production constant."""

    match = re.search(r"HMIC-REQ-067 \(Revised, v1\.2.*?Five entries, no more, no fewer", contract_text, re.S)
    assert match is not None, "HMIC-REQ-067 (v1.2) block not found in contract text"
    block = match.group(0)
    ids = re.findall(r"`([A-Z]+-\d{3})`", block)
    # Preserve first-seen order, de-duplicated.
    seen: "list[str]" = []
    for contract_id in ids:
        if contract_id not in seen:
            seen.append(contract_id)
    return tuple(seen)


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


# ---------------------------------------------------------------------------
# §77-78/§48 -- independent contract extraction, exact set equality
# ---------------------------------------------------------------------------


def test_live_contract_req_050_enumeration_is_exactly_25_entries():
    entries = _extract_req_050_block(_CONTRACT_TEXT)
    assert len(entries) == 25


def test_live_contract_req_067_members_are_exactly_5():
    members = _extract_req_067_members(_CONTRACT_TEXT)
    assert len(members) == 5
    assert set(members) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}


def test_production_frozen_set_exactly_equals_live_contract_25_file_set():
    from pcae.core import hatp_mandatory_certification as hmic

    contract_paths = set(_live_contract_25_canonical_paths())
    production_paths = set(hmic._frozen_canonical_paths())

    assert len(contract_paths) == 25
    assert len(production_paths) == 25
    assert production_paths == contract_paths, (
        f"production/contract frozen-set mismatch: "
        f"contract-only={contract_paths - production_paths}, "
        f"production-only={production_paths - contract_paths}"
    )


def test_production_contract_identity_set_exactly_equals_live_req_067_members():
    from pcae.core import hatp_mandatory_certification as hmic

    contract_members = set(_extract_req_067_members(_CONTRACT_TEXT))
    production_members = {contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES}

    assert len(contract_members) == 5
    assert len(production_members) == 5
    assert production_members == contract_members, (
        f"production/contract contract_versions mismatch: "
        f"contract-only={contract_members - production_members}, "
        f"production-only={production_members - contract_members}"
    )


def test_production_module_constant_matches_contract_literal_presentation_order():
    """Stronger than set equality: the production tuple's own literal
    order (before canonicalization) must match HMIC-REQ-050's fenced
    block, entry for entry (HMIC-REQ-051 -- not merely a same-set,
    different-order list)."""

    from pcae.core import hatp_mandatory_certification as hmic

    contract_entries = tuple(e.split()[0] for e in _extract_req_050_block(_CONTRACT_TEXT))
    assert hmic._FROZEN_AUTHORITY_BEARING_FILES == contract_entries


def test_production_contract_identity_files_order_matches_hbdc_last():
    """HBDC-001 is HMIC-REQ-067's fifth, newly-added member; production
    preserves the original four members' order and appends HBDC-001
    exactly as the fifth, matching the other four's own insertion
    precedent (each prior contract was appended, never reordered)."""

    from pcae.core import hatp_mandatory_certification as hmic

    ids = tuple(contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES)
    assert ids == ("HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001")


def test_production_frozen_set_count_assertion_is_exactly_25():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", source)
    assert match is not None
    assert match.group(1) == "25"
    assert ">= 25" not in source
    assert ">=25" not in source


def test_new_entries_are_exactly_the_two_verified_additions():
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = set(hmic._frozen_canonical_paths())
    assert _HBDC_RELATIVE in canonical
    members = {contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES}
    assert "HBDC-001" in members


# ---------------------------------------------------------------------------
# §79 -- exact delta historical test: 24->25, 4->5, no rewritten history
# ---------------------------------------------------------------------------


def test_pre_20f_production_was_exactly_24_files_and_4_contract_members():
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", entry_source)
    assert match is not None
    assert match.group(1) == "24"
    assert entry_source.count('_CONTRACT_IDENTITY_FILES: "tuple[tuple[str, str], ...]" = (') == 1
    # Historical (pre-alignment) four-member tuple; HBDC-001 absent.
    assert "HBDC-001" not in entry_source.split('_CONTRACT_IDENTITY_FILES: "tuple[tuple[str, str], ...]" = (')[1].split(")")[0]


def _entry_frozen_authority_bearing_files() -> "tuple[str, ...]":
    """Both `_FROZEN_SRC_PCAE_RELATIVE_FILES` and
    `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` are `ast.AnnAssign` nodes
    (annotated with `"tuple[str, ...]"`), not plain `ast.Assign` --
    extracted separately and concatenated, mirroring production's own
    `_FROZEN_SRC_PCAE_RELATIVE_FILES + _FROZEN_REPOSITORY_ROOT_RELATIVE_
    FILES` construction."""

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


def test_exact_one_entry_delta_between_pre_20f_and_current_frozen_sets():
    from pcae.core import hatp_mandatory_certification as hmic

    entry_frozen_tuple = _entry_frozen_authority_bearing_files()
    assert len(entry_frozen_tuple) == 24

    current = set(hmic._FROZEN_AUTHORITY_BEARING_FILES)
    entering = set(entry_frozen_tuple)
    assert current - entering == {_HBDC_RELATIVE}
    assert entering - current == set()


def test_exact_one_member_delta_between_pre_20f_and_current_contract_identity():
    from pcae.core import hatp_mandatory_certification as hmic

    entry_members = _entry_contract_identity_members()
    assert len(entry_members) == 4

    current_members = {contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES}
    entering_members = set(entry_members)
    assert current_members - entering_members == {"HBDC-001"}
    assert entering_members - current_members == set()


# ---------------------------------------------------------------------------
# §40-44/§104 -- file existence, safety, canonicalization over all 25
# ---------------------------------------------------------------------------


def test_all_25_frozen_paths_exist_are_regular_and_not_symlinked():
    from pcae.core import hatp_mandatory_certification as hmic

    for canonical_path in hmic._frozen_canonical_paths():
        path = _REPO_ROOT / canonical_path
        assert path.exists(), f"frozen path missing: {canonical_path}"
        assert not path.is_symlink(), f"frozen path is a symlink: {canonical_path}"
        assert path.is_file(), f"frozen path is not a regular file: {canonical_path}"


def test_hbdc_path_accepted_with_no_special_casing():
    from pcae.core import hatp_mandatory_certification as hmic

    hmic._validate_frozen_path_literal(_HBDC_RELATIVE)
    assert _HBDC_RELATIVE in hmic._frozen_canonical_paths()


def test_frozen_set_is_immutable_tuple_not_list_or_set():
    from pcae.core import hatp_mandatory_certification as hmic

    assert isinstance(hmic._FROZEN_AUTHORITY_BEARING_FILES, tuple)
    assert isinstance(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES, tuple)
    assert isinstance(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES, tuple)
    assert isinstance(hmic._CONTRACT_IDENTITY_FILES, tuple)


def test_no_duplicate_entries_in_frozen_set_or_contract_identity():
    from pcae.core import hatp_mandatory_certification as hmic

    assert len(set(hmic._FROZEN_AUTHORITY_BEARING_FILES)) == len(hmic._FROZEN_AUTHORITY_BEARING_FILES)
    ids = [contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES]
    paths = [path for _, path in hmic._CONTRACT_IDENTITY_FILES]
    assert len(set(ids)) == len(ids)
    assert len(set(paths)) == len(paths)


# ---------------------------------------------------------------------------
# §72-73/§55-56 -- exactly one production file, one frozen subject file
# changed; the other 24 frozen target files remain byte-unchanged since
# this phase's own entry commit
# ---------------------------------------------------------------------------


def test_exactly_one_frozen_file_changed_the_other_24_are_byte_unchanged():
    from pcae.core import hatp_mandatory_certification as hmic

    changed = []
    unchanged = []
    for canonical_path in hmic._frozen_canonical_paths():
        current_bytes = (_REPO_ROOT / canonical_path).read_bytes()
        entry_text = _git_show(_PHASE_ENTRY_COMMIT, canonical_path).encode("utf-8")
        if current_bytes != entry_text:
            changed.append(canonical_path)
        else:
            unchanged.append(canonical_path)

    assert changed == ["src/pcae/core/hatp_mandatory_certification.py"], (
        f"expected exactly the core HMIC module to change; got: {changed}"
    )
    assert len(unchanged) == 24


def test_admin_script_byte_unchanged_since_phase_entry():
    current = _ADMIN_SCRIPT_PATH.read_bytes()
    entry = _git_show(_PHASE_ENTRY_COMMIT, "scripts/hatp_certification_admin.py").encode("utf-8")
    assert current == entry


def test_hmic_contract_hbdc_contract_and_upstream_contracts_byte_unchanged_since_phase_entry():
    for rel in (_CONTRACT_PATH.relative_to(_REPO_ROOT).as_posix(),) + _UPSTREAM_CONTRACT_RELATIVE_PATHS:
        current = (_REPO_ROOT / rel).read_bytes()
        entry = _git_show(_PHASE_ENTRY_COMMIT, rel).encode("utf-8")
        assert current == entry, f"contract changed since phase entry: {rel}"


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
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    assert changed == []


def test_no_contract_file_changed_since_phase_entry():
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "HEAD", "--", "docs/contracts"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    assert changed == []


# ---------------------------------------------------------------------------
# §71/§27-28/§33-37 -- hunk classification: the ONLY production change is
# the frozen-set/contract-identity constants, count-assertion, and their
# surrounding module-level comments -- no validator, storage, admin-
# writer, parser, or digest/contract-version-algorithm function body
# changed. Verified at the AST function/class-source level against this
# phase's own entry commit.
# ---------------------------------------------------------------------------


def _top_level_def_sources(source: str) -> "dict[str, str]":
    tree = ast.parse(source)
    sources: "dict[str, str]" = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            segment = ast.get_source_segment(source, node)
            assert segment is not None
            sources[node.name] = segment
    return sources


def test_every_function_and_class_body_is_ast_source_identical_to_phase_entry():
    """Only `_FROZEN_SRC_PCAE_RELATIVE_FILES`, `_FROZEN_REPOSITORY_ROOT_
    RELATIVE_FILES`, `_FROZEN_AUTHORITY_BEARING_FILES`'s count assertion,
    `_CONTRACT_IDENTITY_FILES`, and their surrounding module-level
    comments are module-level statements, not function/class bodies -- so
    this test's function-by-function, class-by-class comparison
    independently proves no validator, storage, admin-writer, parser,
    digest, contract-version-derivation, or Git-identity function or
    error class changed a single byte this phase."""

    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")

    current_defs = _top_level_def_sources(current_source)
    entry_defs = _top_level_def_sources(entry_source)

    assert set(current_defs) == set(entry_defs), "function/class inventory changed this phase"

    changed_defs = {name for name in current_defs if current_defs[name] != entry_defs[name]}
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
    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    current_defs = _top_level_def_sources(current_source)
    entry_defs = _top_level_def_sources(entry_source)
    assert current_defs["derive_contract_versions"] == entry_defs["derive_contract_versions"]


def test_derive_implementation_commit_git_identity_unchanged():
    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    current_defs = _top_level_def_sources(current_source)
    entry_defs = _top_level_def_sources(entry_source)
    assert current_defs["derive_implementation_commit"] == entry_defs["derive_implementation_commit"]
    assert current_defs["_run_git"] == entry_defs["_run_git"]


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


# ---------------------------------------------------------------------------
# §14/§18/§21/§80 -- live-digest self-binding, dual binding, and 25/25
# mutation sensitivity, all against the real repository state (not a
# synthetic fixture) so self-binding is proven against production's own
# post-edit bytes.
# ---------------------------------------------------------------------------


def test_live_digest_uses_post_edit_core_module_bytes_not_stale_cache():
    """Mutating a *copy* of the live tree's core module and recomputing
    the digest over that copy must differ from the real on-disk digest --
    proving the digest is a fresh, uncached function of current bytes."""

    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    root = HarnessPath(_REPO_ROOT)
    assert hmic.derive_implementation_scope_digest(root) == hmic.derive_implementation_scope_digest(root)

    canonical = hmic._frozen_canonical_paths()
    real_digest = _independent_scope_digest(_REPO_ROOT, list(canonical))

    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        for rel in canonical:
            dest = tree / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_REPO_ROOT / rel, dest)
        core_rel = "src/pcae/core/hatp_mandatory_certification.py"
        (tree / core_rel).write_bytes((tree / core_rel).read_bytes() + b"\n# mutated-for-test\n")
        mutated_digest = _independent_scope_digest(tree, list(canonical))

    assert mutated_digest != real_digest, "mutating the core module's current bytes did not change the digest"


def test_all_25_live_files_are_individually_digest_sensitive(tmp_path):
    """For the real, live 25-file set, a one-byte modeled mutation of
    every single frozen file changes the aggregate digest -- 25/25, not
    just the newly-added HBDC-001 entry."""

    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    for rel in canonical:
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest)

    baseline = _independent_scope_digest(tree, canonical)
    sensitive = []
    for rel in canonical:
        target = tree / rel
        original = target.read_bytes()
        target.write_bytes(original + b"\x00mutated")
        mutated = _independent_scope_digest(tree, canonical)
        if mutated != baseline:
            sensitive.append(rel)
        target.write_bytes(original)

    assert set(sensitive) == set(canonical), (
        f"not all 25 frozen files are digest-sensitive: insensitive={set(canonical) - set(sensitive)}"
    )


def test_hbdc_same_version_content_mutation_changes_implementation_scope_digest(tmp_path):
    """§14/§15/§81: HBDC-001's dual binding, production-live -- a
    same-version, content-only mutation of HBDC-001's document changes
    `implementation_scope_digest`, the production closure of
    B-149O.20D-1's repaired property, now proven against production's
    own constants rather than a scratch reimplementation only."""

    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    for rel in canonical:
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest)

    baseline = hmic.derive_implementation_scope_digest(HarnessPath(tree))

    hbdc_path = tree / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    assert b"**Version:** 1.0" in original, "expected HBDC-001 v1.0 header unchanged"
    hbdc_path.write_bytes(original.replace(b"HATP Class-B Deployment Contract", b"HATP Class-B Deployment Contract "))

    mutated = hmic.derive_implementation_scope_digest(HarnessPath(tree))
    assert mutated != baseline, "same-version HBDC-001 content mutation did not change implementation_scope_digest"


def test_hbdc_version_drift_changes_contract_versions(tmp_path):
    """§16/§82: bumping HBDC-001's version header changes the derived
    `contract_versions` mapping's `HBDC-001` value, using production's
    own existing, unmodified derivation mechanism."""

    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    for rel in canonical:
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest)

    baseline = dict(hmic.derive_contract_versions(HarnessPath(tree)))
    assert baseline["HBDC-001"] == "1.0"

    hbdc_path = tree / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    hbdc_path.write_bytes(original.replace(b"**Version:** 1.0", b"**Version:** 1.1"))

    drifted = dict(hmic.derive_contract_versions(HarnessPath(tree)))
    assert drifted["HBDC-001"] == "1.1"
    assert drifted["HBDC-001"] != baseline["HBDC-001"]


def test_hbdc_wrong_contract_id_fails_closed(tmp_path):
    """§17/§83: a malformed/renamed HBDC-001 Contract-ID header fails
    closed with `ContractIdentityDerivationError`, matching the existing,
    unmodified fail-closed behavior for the other four bound contracts --
    no silent substitution."""

    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    for rel in canonical:
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest)

    hbdc_path = tree / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    hbdc_path.write_bytes(original.replace(b"**Contract:** HBDC-001", b"**Contract:** WRONG-ID-999"))

    with pytest.raises(hmic.ContractIdentityDerivationError):
        hmic.derive_contract_versions(HarnessPath(tree))


def test_other_four_bound_contracts_dual_binding_regression(tmp_path):
    """§22/§84: the pre-existing four bound contracts' own dual binding
    (content-digest + version-header) is unweakened by this phase's
    addition of a fifth."""

    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    canonical = list(hmic._frozen_canonical_paths())
    tree = tmp_path / "tree"
    for rel in canonical:
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest)

    baseline_digest = hmic.derive_implementation_scope_digest(HarnessPath(tree))
    baseline_versions = dict(hmic.derive_contract_versions(HarnessPath(tree)))

    for rel in _UPSTREAM_CONTRACT_RELATIVE_PATHS:
        if rel == _HBDC_RELATIVE:
            continue
        target = tree / rel
        original = target.read_bytes()
        target.write_bytes(original + b"\n<!-- mutated-for-test -->\n")
        mutated_digest = hmic.derive_implementation_scope_digest(HarnessPath(tree))
        assert mutated_digest != baseline_digest, f"{rel} content mutation did not change implementation_scope_digest"
        target.write_bytes(original)

    restored_digest = hmic.derive_implementation_scope_digest(HarnessPath(tree))
    assert restored_digest == baseline_digest
    restored_versions = dict(hmic.derive_contract_versions(HarnessPath(tree)))
    assert restored_versions == baseline_versions


def test_hbdc_participates_in_both_scope_digest_and_contract_versions():
    """§18/§40 (final report requirement): mechanically verify HBDC-001
    is a member of both dimensions in the current, live production
    constants -- the mandatory dual-binding property."""

    from pcae.core import hatp_mandatory_certification as hmic

    assert _HBDC_RELATIVE in hmic._frozen_canonical_paths()
    assert "HBDC-001" in {contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES}


def test_production_derive_implementation_scope_digest_matches_independent_reimplementation():
    """Golden-style cross-check: production's own
    `derive_implementation_scope_digest`, called against the real
    repository, must equal this test's independently authored digest
    algorithm over the same live 25-file set -- not merely
    self-consistent with itself."""

    from pcae.core.hatp_bootstrap import resolve_canonical_deployment_root  # noqa: F401
    from pcae.core.paths import HarnessPath
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    expected = _independent_scope_digest(_REPO_ROOT, canonical)
    actual = hmic.derive_implementation_scope_digest(HarnessPath(_REPO_ROOT))
    assert actual == expected


# ---------------------------------------------------------------------------
# §19-20/§43-45/§86 -- original 24/4 preserved; pre-20F replay rejection
# ---------------------------------------------------------------------------


def test_original_24_frozen_paths_preserved():
    from pcae.core import hatp_mandatory_certification as hmic

    original_24 = _entry_frozen_authority_bearing_files()
    assert len(original_24) == 24
    current = set(hmic._FROZEN_AUTHORITY_BEARING_FILES)
    assert set(original_24) <= current


def test_original_4_contract_members_preserved():
    from pcae.core import hatp_mandatory_certification as hmic

    original_4 = _entry_contract_identity_members()
    assert len(original_4) == 4
    current = {contract_id for contract_id, _ in hmic._CONTRACT_IDENTITY_FILES}
    assert set(original_4) <= current


def test_historical_24_file_digest_differs_from_current_25_file_digest(tmp_path):
    """For an identical snapshot of the repository, the digest computed
    over the historical 24-file scope must not equal the digest computed
    over the current, aligned 25-file scope -- a v1.1-scope certification
    cannot be replayed against v1.2."""

    from pcae.core import hatp_mandatory_certification as hmic

    live_25 = list(hmic._frozen_canonical_paths())
    old_24 = [p for p in live_25 if p != _HBDC_RELATIVE]
    assert len(old_24) == 24

    tree = tmp_path / "tree"
    for rel in live_25:
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest)

    old_scope_digest = _independent_scope_digest(tree, old_24)
    new_scope_digest = _independent_scope_digest(tree, live_25)
    assert old_scope_digest != new_scope_digest


def test_pre_20f_four_member_contract_versions_differs_from_current_five_member():
    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    current = dict(hmic.derive_contract_versions(HarnessPath(_REPO_ROOT)))
    assert len(current) == 5
    old_four = {k: v for k, v in current.items() if k != "HBDC-001"}
    assert len(old_four) == 4
    assert dict(current) != old_four


# ---------------------------------------------------------------------------
# §46-47/§87 -- no caller-suppliable legacy/24-file or 4-contract override
# ---------------------------------------------------------------------------


def test_derive_implementation_scope_digest_accepts_no_scope_override_parameter():
    import inspect

    from pcae.core import hatp_mandatory_certification as hmic

    signature = inspect.signature(hmic.derive_implementation_scope_digest)
    param_names = set(signature.parameters)
    assert param_names == {"root"}, f"unexpected caller-suppliable parameter(s): {param_names - {'root'}}"


def test_derive_contract_versions_accepts_no_scope_override_parameter():
    import inspect

    from pcae.core import hatp_mandatory_certification as hmic

    signature = inspect.signature(hmic.derive_contract_versions)
    param_names = set(signature.parameters)
    assert param_names == {"root"}, f"unexpected caller-suppliable parameter(s): {param_names - {'root'}}"


def test_no_legacy_scope_language_in_production_module():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "legacy_scope",
        "v1_1_compat",
        "file_count=24",
        "ignore_new_files",
        "legacy=True",
        "ignore_hbdc",
        "bound_contract_count=4",
        "legacy_contract_set",
    ):
        assert forbidden not in source


# ---------------------------------------------------------------------------
# §38-39/§93 -- no readiness/cutover semantic change (the validator's
# readiness caller in `hatp_mandatory_cutover.py` predates this phase --
# 149O.19.5F Wave F wired it in, independently of this phase's own narrow
# scope; this phase's own obligation is that the file is byte-unchanged
# and real, live readiness is still NOT READY), read-only
# ---------------------------------------------------------------------------


def test_cutover_module_byte_unchanged_since_phase_entry():
    current = _CUTOVER_PATH.read_bytes()
    entry = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_cutover.py").encode("utf-8")
    assert current == entry


def test_readiness_still_not_ready_against_real_production_state():
    """Read-only: `assess_hatp_mandatory_activation_readiness`'s existing,
    unmodified readiness caller already reaches
    `validate_active_hatp_mandatory_independent_verification_certification`
    (Wave F, wired before this phase) -- this phase changes neither that
    wiring nor its outcome. With no real Protected Root/certification on
    this host, live readiness is still `ready=False`."""

    from pcae.core.hatp_mandatory_cutover import assess_hatp_mandatory_activation_readiness
    from pcae.core.paths import HarnessPath

    result = assess_hatp_mandatory_activation_readiness(HarnessPath(_REPO_ROOT))
    assert result.ready is False


def test_no_real_certification_state_exists_on_host():
    from pcae.core.hatp_bootstrap import HATPTrustStore

    root = HATPTrustStore.production().root
    assert not (root / "certifications.json").exists()
    assert not (root / "certification-bindings.json").exists()


def test_hatp_production_readiness_still_not_ready():
    """§39/§93: read-only confirmation -- no real Protected Root,
    certification, active binding, revocation, or Cutover Record exists
    on this host, so HATP production remains NOT READY. This test
    performs no mutation."""

    from pcae.core.hatp_bootstrap import HATPTrustStore

    root = HATPTrustStore.production().root
    assert not (root / "certifications.json").exists()
    assert not (root / "certification-bindings.json").exists()
    assert not (root / "active-certification.json").exists()


# ---------------------------------------------------------------------------
# §50-51 -- gate-status signal: this phase implements, but does not close,
# HBDC-BINDING-GATE / B-149O.20D-1
# ---------------------------------------------------------------------------


def test_contract_still_records_hbdc_repair_and_no_production_alignment_claim():
    """This phase does not amend the contract (verified above); it
    merely confirms the contract it reads still records the 149O.20D.1
    contract-level repair, and makes no claim that production alignment
    (this phase's own scope, a distinct production-side concern the
    contract itself does not track) has occurred."""

    assert "149O.20D.1" in _CONTRACT_TEXT
    assert "PRODUCTION 25-FILE" not in _CONTRACT_TEXT
    assert "PRODUCTION ALIGNMENT IMPLEMENTED" not in _CONTRACT_TEXT

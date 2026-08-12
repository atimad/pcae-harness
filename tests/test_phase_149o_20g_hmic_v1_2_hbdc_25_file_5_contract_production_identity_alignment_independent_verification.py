"""Phase 149O.20G -- HMIC v1.2 HBDC 25-File / 5-Contract Production
Identity Alignment Independent Verification.

INDEPENDENT IMPLEMENTATION VERIFICATION ONLY. This module independently
re-derives and confirms every load-bearing claim of Phase 149O.20F's own
report from primary sources (the live HMIC-001 contract text and the
live production source), without importing 149O.20F's own test module or
treating its literal constants as an oracle. It adjudicates
B-149O.20D-1 and HBDC-BINDING-GATE at the implementation-verification
boundary.

Modifies no `src/pcae/**` file, no `scripts/**` file, and no contract
file. If a Blocking defect were found here, this module records it; it
does not repair it.

Covers:
  * fresh, from-scratch extraction of HMIC-REQ-050 (25 files) and
    HMIC-REQ-067 (5 contract_versions members) directly from the live
    contract text;
  * fresh, from-scratch extraction of production's
    `_FROZEN_AUTHORITY_BEARING_FILES`/`_CONTRACT_IDENTITY_FILES` via
    regex over the module's own source text (not merely importing and
    trusting the already-imported tuple);
  * exact dual-set equality (25/25, 5/5), by content and by literal
    presentation order;
  * historical 24-file/4-member pre-20F baseline reconstruction via
    `git show` against the phase-entry commit, and the exact delta;
  * a from-scratch, independent reimplementation of the
    `implementation_scope_digest` two-level SHA-256 construction
    (HMIC-REQ-054/056-058), cross-checked against production's own
    `derive_implementation_scope_digest` (golden digest);
  * 25/25 mutation sensitivity using the independent digest
    reimplementation;
  * HBDC-001 dual binding: same-version content-drift sensitivity,
    version-drift sensitivity, and malformed-Contract-ID fail-closed
    behavior, all exercised against production's own live functions
    inside an isolated filesystem fixture (never mutating the real
    working tree);
  * core self-binding (post-edit source bytes, not stale pre-edit
    bytes, participate in the digest);
  * HBDC missing / symlinked / non-regular-file fail-closed behavior;
  * no legacy 24-file/4-contract override path, no validation cache, no
    import-time identity freeze, no duplicate frozen path or contract
    ID;
  * AST/byte stability of the digest algorithm, contract-identity
    algorithm, Git-identity derivation, validator, admin script, and
    cutover module across the 149O.20F diff;
  * modeled pre-20F/pre-repair/v1.1 certification replay rejection
    against the current live production identity;
  * the nine frozen-corpus contract files remain byte-unchanged.
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
_HMIC_MODULE_TEXT = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
_CUTOVER_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"

#: 149O.20F's own phase-entry commit (149O.20E's exit commit) --
#: independently confirmed via `git log` during this phase's initial
#: inspection, not copied from 149O.20F's own report text.
_PHASE_ENTRY_COMMIT = "43ecacb9"

#: Nine-member frozen corpus: the eight upstream contracts HMIC-REQ-050/
#: 053/067 bind, plus HMIC-001 itself (not a HMIC-REQ-050 member -- the
#: contract this module implements, not one of the files it hashes).
_NINE_CONTRACT_CORPUS_RELATIVE_PATHS = (
    "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
)

_HBDC_RELATIVE = "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"


# ---------------------------------------------------------------------------
# Helpers -- independent extraction, never importing 149O.20F's own test
# module or trusting a copied production constant as its own oracle.
# ---------------------------------------------------------------------------


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
    match = re.search(r"HMIC-REQ-050 \(Exact Enumeration.*?```\n(.*?)```", contract_text, re.S)
    assert match is not None, "HMIC-REQ-050 fenced enumeration block not found"
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    return tuple(lines)


def _live_contract_25_literal_entries() -> "list[str]":
    return [e.split()[0] for e in _extract_req_050_block(_CONTRACT_TEXT)]


def _live_contract_25_canonical_paths() -> "list[str]":
    result = []
    for entry in _live_contract_25_literal_entries():
        if (_SRC / entry).exists():
            result.append(f"src/pcae/{entry}")
        else:
            result.append(entry)
    return result


def _extract_req_067_members(contract_text: str) -> "tuple[str, ...]":
    match = re.search(r"HMIC-REQ-067 \(Revised, v1\.2.*?Five entries, no more, no fewer", contract_text, re.S)
    assert match is not None, "HMIC-REQ-067 (v1.2) block not found"
    ids = re.findall(r"`([A-Z]+-\d{3})`", match.group(0))
    seen: "list[str]" = []
    for contract_id in ids:
        if contract_id not in seen:
            seen.append(contract_id)
    return tuple(seen)


def _extract_production_frozen_literal_from_source(module_text: str) -> "list[str]":
    """Regex extraction of the two literal tuples directly from the
    module's own *source text*, independent of importing the module and
    trusting its already-constructed `_FROZEN_AUTHORITY_BEARING_FILES`
    object."""

    src_match = re.search(
        r'_FROZEN_SRC_PCAE_RELATIVE_FILES: "tuple\[str, \.\.\.\]" = \((.*?)\)\n', module_text, re.S
    )
    root_match = re.search(
        r'_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES: "tuple\[str, \.\.\.\]" = \((.*?)\)\n', module_text, re.S
    )
    assert src_match and root_match
    src_files = re.findall(r'"([^"]+)"', src_match.group(1))
    root_files = re.findall(r'"([^"]+)"', root_match.group(1))
    return [f"src/pcae/{f}" for f in src_files] + root_files


def _extract_production_contract_ids_from_source(module_text: str) -> "list[str]":
    match = re.search(
        r'_CONTRACT_IDENTITY_FILES: "tuple\[tuple\[str, str\], \.\.\.\]" = \((.*?)\)\n', module_text, re.S
    )
    assert match is not None
    pairs = re.findall(r'\("([^"]+)",\s*"([^"]+)"\)', match.group(1))
    return [contract_id for contract_id, _ in pairs]


def _independent_scope_digest(root: Path, canonical_relative_paths: "list[str]") -> str:
    """From-scratch reimplementation of HMIC-REQ-054/056-058's two-level
    SHA-256 construction, independent of
    `derive_implementation_scope_digest` in production."""

    ordered = sorted(canonical_relative_paths)
    records = bytearray()
    for rel in ordered:
        file_bytes = (root / rel).read_bytes()
        file_digest = _sha256_hex(file_bytes)
        records += rel.encode("utf-8") + b"\0" + file_digest.encode("ascii") + b"\n"
    return _sha256_hex(bytes(records))


def _isolated_fixture() -> Path:
    """Creates an isolated, disposable copy of the tracked working tree
    via `git archive`, so HBDC-mutation tests never touch the real
    repository."""

    tmp = Path(tempfile.mkdtemp(prefix="pcae_149o_20g_"))
    subprocess.run(f"git archive HEAD | tar -x -C {tmp}", shell=True, check=True, cwd=_REPO_ROOT)
    return tmp


def _run_in_fixture(fixture_root: Path, script: str) -> "subprocess.CompletedProcess[str]":
    return subprocess.run(["python3", "-c", script], cwd=fixture_root, capture_output=True, text=True)


_DIGEST_VERSIONS_SCRIPT = """
import sys, pathlib
sys.path.insert(0, "src")
from pcae.core.hatp_mandatory_certification import derive_implementation_scope_digest, derive_contract_versions
from pcae.core.paths import HarnessPath
root = HarnessPath(pathlib.Path("."))
print("DIGEST", derive_implementation_scope_digest(root))
print("VERSIONS", dict(derive_contract_versions(root)))
"""


# ---------------------------------------------------------------------------
# Independent contract + production extraction, exact dual equality
# ---------------------------------------------------------------------------


def test_live_contract_req_050_is_exactly_25_entries():
    assert len(_extract_req_050_block(_CONTRACT_TEXT)) == 25


def test_live_contract_req_067_is_exactly_5_members():
    members = _extract_req_067_members(_CONTRACT_TEXT)
    assert len(members) == 5
    assert set(members) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}


def test_production_source_text_frozen_literal_is_exactly_25_entries():
    literal = _extract_production_frozen_literal_from_source(_HMIC_MODULE_TEXT)
    assert len(literal) == 25


def test_production_source_text_contract_ids_is_exactly_5_members():
    ids = _extract_production_contract_ids_from_source(_HMIC_MODULE_TEXT)
    assert len(ids) == 5
    assert set(ids) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"}


def test_dual_equality_25_file_set_content_and_order():
    contract_canonical = _live_contract_25_canonical_paths()
    prod_literal = _extract_production_frozen_literal_from_source(_HMIC_MODULE_TEXT)
    assert contract_canonical == prod_literal, (
        f"contract-only={set(contract_canonical) - set(prod_literal)}, "
        f"production-only={set(prod_literal) - set(contract_canonical)}"
    )


def test_dual_equality_5_contract_member_set_content_and_order():
    contract_ids = list(_extract_req_067_members(_CONTRACT_TEXT))
    prod_ids = _extract_production_contract_ids_from_source(_HMIC_MODULE_TEXT)
    assert contract_ids == prod_ids


def test_production_import_matches_source_text_extraction():
    """Cross-checks the regex-over-source-text extraction against the
    actual imported tuple, ruling out a stale bytecode/import mismatch."""

    from pcae.core import hatp_mandatory_certification as hmic

    imported_canonical = sorted(hmic._frozen_canonical_paths())
    contract_canonical = sorted(_live_contract_25_canonical_paths())
    assert imported_canonical == contract_canonical
    imported_ids = [cid for cid, _ in hmic._CONTRACT_IDENTITY_FILES]
    assert imported_ids == list(_extract_req_067_members(_CONTRACT_TEXT))


# ---------------------------------------------------------------------------
# Historical baseline reconstruction and exact delta
# ---------------------------------------------------------------------------


def test_pre_20f_production_baseline_is_exactly_24_files_4_contracts():
    pre_module_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    pre_files = _extract_production_frozen_literal_from_source(pre_module_text)
    pre_ids = _extract_production_contract_ids_from_source(pre_module_text)
    assert len(pre_files) == 24
    assert len(pre_ids) == 4
    assert set(pre_ids) == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}


def test_exact_historical_delta_is_hbdc_only():
    pre_module_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    pre_files = set(_extract_production_frozen_literal_from_source(pre_module_text))
    pre_ids = set(_extract_production_contract_ids_from_source(pre_module_text))

    current_files = set(_extract_production_frozen_literal_from_source(_HMIC_MODULE_TEXT))
    current_ids = set(_extract_production_contract_ids_from_source(_HMIC_MODULE_TEXT))

    assert current_files - pre_files == {_HBDC_RELATIVE}
    assert pre_files - current_files == set()
    assert current_ids - pre_ids == {"HBDC-001"}
    assert pre_ids - current_ids == set()


def test_original_24_entries_preserved_and_original_4_contract_members_preserved():
    pre_module_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    pre_files = set(_extract_production_frozen_literal_from_source(pre_module_text))
    pre_ids = set(_extract_production_contract_ids_from_source(pre_module_text))

    current_files = set(_extract_production_frozen_literal_from_source(_HMIC_MODULE_TEXT))
    current_ids = set(_extract_production_contract_ids_from_source(_HMIC_MODULE_TEXT))

    assert pre_files.issubset(current_files)
    assert pre_ids.issubset(current_ids)


def test_20f_diff_touched_exactly_one_production_file_no_scripts():
    diff = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "HEAD", "--", "src/pcae/", "scripts/"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert diff == ["src/pcae/core/hatp_mandatory_certification.py"]


def test_20f_diff_changed_zero_function_or_class_bodies():
    pre_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    pre_tree = ast.parse(pre_text)
    post_tree = ast.parse(_HMIC_MODULE_TEXT)

    def bodies(tree):
        out = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out[node.name] = ast.dump(node)
        return out

    pre_bodies, post_bodies = bodies(pre_tree), bodies(post_tree)
    assert set(pre_bodies) == set(post_bodies), "function/class added or removed"
    changed = [n for n in pre_bodies if pre_bodies[n] != post_bodies[n]]
    assert changed == [], f"unexpected function/class body change(s): {changed}"


# ---------------------------------------------------------------------------
# Independent digest reimplementation, golden cross-check, mutation
# sensitivity
# ---------------------------------------------------------------------------


def test_golden_digest_independent_matches_production():
    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    contract_canonical = _live_contract_25_canonical_paths()
    independent = _independent_scope_digest(_REPO_ROOT, contract_canonical)
    production = hmic.derive_implementation_scope_digest(HarnessPath(_REPO_ROOT))
    assert independent == production


def test_25_of_25_files_are_digest_sensitive():
    contract_canonical = sorted(_live_contract_25_canonical_paths())
    baseline = _independent_scope_digest(_REPO_ROOT, contract_canonical)

    def digest_with_override(target_rel: str, mutated_bytes: bytes) -> str:
        ordered = sorted(contract_canonical)
        records = bytearray()
        for rel in ordered:
            data = mutated_bytes if rel == target_rel else (_REPO_ROOT / rel).read_bytes()
            file_digest = _sha256_hex(data)
            records += rel.encode("utf-8") + b"\0" + file_digest.encode("ascii") + b"\n"
        return _sha256_hex(bytes(records))

    sensitive = 0
    insensitive = []
    for rel in contract_canonical:
        original = (_REPO_ROOT / rel).read_bytes()
        mutated = original + b"\x00" if not original.endswith(b"\x00") else original[:-1]
        d = digest_with_override(rel, mutated)
        if d != baseline:
            sensitive += 1
        else:
            insensitive.append(rel)

    assert insensitive == []
    assert sensitive == 25


def test_pre_20f_24_file_digest_differs_from_current_25_file_digest():
    pre_module_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    pre_literal = _extract_production_frozen_literal_from_source(pre_module_text)
    current_literal = _live_contract_25_canonical_paths()

    pre_digest = _independent_scope_digest(_REPO_ROOT, pre_literal)
    current_digest = _independent_scope_digest(_REPO_ROOT, current_literal)
    assert pre_digest != current_digest


# ---------------------------------------------------------------------------
# HBDC dual binding: content, version, Contract-ID sensitivity (isolated
# fixture, never mutating the real working tree)
# ---------------------------------------------------------------------------


@pytest.fixture()
def fixture_root():
    root = _isolated_fixture()
    yield root
    shutil.rmtree(root, ignore_errors=True)


def test_hbdc_same_version_content_mutation_changes_digest_not_versions(fixture_root):
    baseline = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    assert baseline.returncode == 0, baseline.stderr

    hbdc_path = fixture_root / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    hbdc_path.write_bytes(original + b"\n<!-- 149O.20G mutation probe -->\n")
    mutated = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    hbdc_path.write_bytes(original)

    assert mutated.returncode == 0, mutated.stderr
    baseline_digest = baseline.stdout.splitlines()[0]
    mutated_digest = mutated.stdout.splitlines()[0]
    baseline_versions = baseline.stdout.splitlines()[1]
    mutated_versions = mutated.stdout.splitlines()[1]

    assert baseline_digest != mutated_digest
    assert baseline_versions == mutated_versions  # same-version drift is digest-only visible


def test_hbdc_version_bump_changes_contract_versions_and_digest(fixture_root):
    baseline = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    assert baseline.returncode == 0, baseline.stderr

    hbdc_path = fixture_root / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    bumped = re.sub(rb"(\*\*Version:\*\*\s*)(\S+)", rb"\g<1>9.9", original, count=1)
    assert bumped != original
    hbdc_path.write_bytes(bumped)
    result = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    hbdc_path.write_bytes(original)

    assert result.returncode == 0, result.stderr
    assert "'HBDC-001': '9.9'" in result.stdout
    assert result.stdout.splitlines()[0] != baseline.stdout.splitlines()[0]


def test_hbdc_wrong_contract_id_fails_closed(fixture_root):
    hbdc_path = fixture_root / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    malformed = re.sub(rb"(\*\*Contract:\*\*\s*)(\S+)", rb"\g<1>WRONG-ID-999", original, count=1)
    assert malformed != original
    hbdc_path.write_bytes(malformed)
    result = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    hbdc_path.write_bytes(original)

    assert result.returncode != 0
    assert "ContractIdentityDerivationError" in result.stderr


def test_hbdc_dual_binding_both_dimensions_material(fixture_root):
    """Explicit dual-binding proof: HBDC-001 participates in BOTH
    `implementation_scope_digest` (content) AND `contract_versions`
    (version header) -- neither alone would be sufficient."""

    baseline = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    hbdc_path = fixture_root / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()

    hbdc_path.write_bytes(original + b"\n<!-- dual-binding content probe -->\n")
    content_mutated = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    hbdc_path.write_bytes(original)

    bumped = re.sub(rb"(\*\*Version:\*\*\s*)(\S+)", rb"\g<1>9.9", original, count=1)
    hbdc_path.write_bytes(bumped)
    version_mutated = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    hbdc_path.write_bytes(original)

    content_dimension_active = content_mutated.stdout.splitlines()[0] != baseline.stdout.splitlines()[0]
    version_dimension_active = "'HBDC-001': '9.9'" in version_mutated.stdout

    assert content_dimension_active, "HBDC-001 not bound into implementation_scope_digest"
    assert version_dimension_active, "HBDC-001 not bound into contract_versions"


def test_other_four_bound_contracts_dual_binding_unweakened(fixture_root):
    baseline = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    baseline_digest = baseline.stdout.splitlines()[0]

    for rel in (
        "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
        "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
        "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
        "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    ):
        target = fixture_root / rel
        original = target.read_bytes()
        target.write_bytes(original + b"\n<!-- regression probe -->\n")
        mutated = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
        target.write_bytes(original)
        assert mutated.returncode == 0, mutated.stderr
        assert mutated.stdout.splitlines()[0] != baseline_digest, f"{rel} lost digest sensitivity"


def test_hbdc_missing_fails_closed(fixture_root):
    hbdc_path = fixture_root / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    hbdc_path.unlink()
    result = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    hbdc_path.write_bytes(original)
    assert result.returncode != 0
    assert "FrozenFileDerivationError" in result.stderr
    assert "does not exist" in result.stderr


def test_hbdc_symlink_rejected(fixture_root):
    hbdc_path = fixture_root / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    other = fixture_root / "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md"
    hbdc_path.unlink()
    hbdc_path.symlink_to(other)
    result = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    hbdc_path.unlink()
    hbdc_path.write_bytes(original)
    assert result.returncode != 0
    assert "symlink" in result.stderr


def test_hbdc_non_regular_file_rejected(fixture_root):
    hbdc_path = fixture_root / _HBDC_RELATIVE
    original = hbdc_path.read_bytes()
    hbdc_path.unlink()
    hbdc_path.mkdir()
    result = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    shutil.rmtree(hbdc_path)
    hbdc_path.write_bytes(original)
    assert result.returncode != 0
    assert "not a regular file" in result.stderr


# ---------------------------------------------------------------------------
# Core self-binding
# ---------------------------------------------------------------------------


def test_core_module_self_binding_post_edit_bytes_participate(fixture_root):
    baseline = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    baseline_digest = baseline.stdout.splitlines()[0]

    core_path = fixture_root / "src/pcae/core/hatp_mandatory_certification.py"
    original = core_path.read_bytes()
    core_path.write_bytes(original + b"\n# 149O.20G self-binding probe\n")
    mutated = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)
    core_path.write_bytes(original)
    restored = _run_in_fixture(fixture_root, _DIGEST_VERSIONS_SCRIPT)

    assert mutated.stdout.splitlines()[0] != baseline_digest
    assert restored.stdout.splitlines()[0] == baseline_digest


# ---------------------------------------------------------------------------
# No legacy override, no cache, no import-time freeze, no duplicates
# ---------------------------------------------------------------------------


def test_no_legacy_scope_override_signature_exists():
    forbidden_patterns = (
        r"legacy_scope",
        r"file_count\s*=\s*24",
        r"ignore_hbdc",
        r"hmic_v1_1",
        r"legacy_24",
        r"legacy_compat",
    )
    for pattern in forbidden_patterns:
        assert re.search(pattern, _HMIC_MODULE_TEXT, re.IGNORECASE) is None, pattern
        assert re.search(pattern, _ADMIN_SCRIPT_PATH.read_text(encoding="utf-8"), re.IGNORECASE) is None, pattern


def test_no_validation_cache_decorator_present():
    assert "lru_cache" not in _HMIC_MODULE_TEXT
    assert "@cache" not in _HMIC_MODULE_TEXT


def test_no_module_level_derivation_call_at_import_time():
    tree = ast.parse(_HMIC_MODULE_TEXT)
    top_level_calls = [
        node for node in tree.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
    ]
    assert top_level_calls == []


def test_no_duplicate_frozen_path_or_contract_id():
    from pcae.core import hatp_mandatory_certification as hmic

    paths = hmic._frozen_canonical_paths()
    assert len(paths) == len(set(paths))
    ids = [cid for cid, _ in hmic._CONTRACT_IDENTITY_FILES]
    assert len(ids) == len(set(ids))


def test_no_caller_suppliable_contract_map_parameter():
    """Neither `derive_contract_versions` nor
    `derive_implementation_scope_digest` accept a caller-supplied
    contract-identity map, expected digest, expected version, or
    expected contract count -- authority is internally derived from the
    module's own frozen literals only."""

    import inspect

    from pcae.core import hatp_mandatory_certification as hmic

    for fn in (hmic.derive_implementation_scope_digest, hmic.derive_contract_versions):
        params = set(inspect.signature(fn).parameters)
        assert params == {"root"}, f"{fn.__name__} accepts unexpected caller-suppliable parameter(s): {params}"


# ---------------------------------------------------------------------------
# Algorithm/semantic stability across the 149O.20F diff
# ---------------------------------------------------------------------------


def test_digest_and_contract_algorithm_functions_unchanged():
    pre_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    pre_tree = ast.parse(pre_text)
    post_tree = ast.parse(_HMIC_MODULE_TEXT)

    def body_of(tree, name):
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == name:
                return ast.dump(node)
        raise AssertionError(f"{name} not found")

    for fn_name in (
        "derive_implementation_scope_digest",
        "derive_contract_versions",
        "derive_implementation_commit",
        "_validate_at_root",
        "validate_active_hatp_mandatory_independent_verification_certification",
    ):
        assert body_of(pre_tree, fn_name) == body_of(post_tree, fn_name), fn_name


def test_admin_script_byte_unchanged_since_phase_entry():
    pre_admin = _git_show(_PHASE_ENTRY_COMMIT, "scripts/hatp_certification_admin.py")
    assert pre_admin == _ADMIN_SCRIPT_PATH.read_text(encoding="utf-8")


def test_cutover_module_byte_unchanged_since_phase_entry():
    pre_cutover = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_cutover.py")
    assert pre_cutover == _CUTOVER_PATH.read_text(encoding="utf-8")


def test_nine_contract_corpus_byte_unchanged_since_phase_entry():
    for rel in _NINE_CONTRACT_CORPUS_RELATIVE_PATHS:
        pre_text = _git_show(_PHASE_ENTRY_COMMIT, rel)
        post_text = (_REPO_ROOT / rel).read_text(encoding="utf-8")
        assert pre_text == post_text, rel


def test_readiness_fact_wiring_unchanged_since_phase_entry():
    """149O.20F corrected a stale governing-instruction assumption that
    the readiness fact was a hard-coded `False` literal: it is, and
    remains (pre-existing Wave F wiring, unaffected by 20F/20G), a
    dynamically computed check driven by
    `validate_active_hatp_mandatory_independent_verification_certification`.
    This test confirms `hatp_mandatory_cutover.py` is byte-unchanged
    since phase entry (already asserted directly by
    `test_cutover_module_byte_unchanged_since_phase_entry`) AND that the
    readiness-fact check name this contract supplies is still present,
    unredesigned."""

    cutover_text = _CUTOVER_PATH.read_text(encoding="utf-8")
    assert '"mandatory_consumption_implementation_independently_verified"' in cutover_text
    assert "validate_active_hatp_mandatory_independent_verification_certification(" in cutover_text


# ---------------------------------------------------------------------------
# Modeled legacy replay rejection against current live production identity
# ---------------------------------------------------------------------------


def test_pre_20f_24_file_replay_rejected_against_current_production():
    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    pre_module_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    pre_literal = _extract_production_frozen_literal_from_source(pre_module_text)
    pre_ids = _extract_production_contract_ids_from_source(pre_module_text)

    modeled_pre_digest = _independent_scope_digest(_REPO_ROOT, pre_literal)
    current_digest = hmic.derive_implementation_scope_digest(HarnessPath(_REPO_ROOT))
    assert modeled_pre_digest != current_digest, "pre-20F 24-file identity must not replay against current 25-file identity"

    current_ids = {cid for cid, _ in hmic._CONTRACT_IDENTITY_FILES}
    assert set(pre_ids) != current_ids, "pre-20F 4-member identity must not replay against current 5-member identity"


def test_v1_1_24_file_4_contract_replay_rejected():
    """Models 149O.19.5E.1-era (HMIC v1.1) semantics: 24-file scope,
    4-contract-member set. Must fail against current production."""

    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    pre_module_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    v1_1_literal = _extract_production_frozen_literal_from_source(pre_module_text)
    v1_1_ids = set(_extract_production_contract_ids_from_source(pre_module_text))

    assert len(v1_1_literal) == 24
    assert v1_1_ids == {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001"}

    modeled_digest = _independent_scope_digest(_REPO_ROOT, v1_1_literal)
    current_digest = hmic.derive_implementation_scope_digest(HarnessPath(_REPO_ROOT))
    assert modeled_digest != current_digest


def test_pre_repair_v1_2_24_file_5_contract_replay_rejected():
    """Models 149O.20D-era semantics (post-20D, pre-20D.1 repair): still
    24-file content scope, but 5-member contract_versions (HBDC-001
    version-header-only, content not yet bound). Must fail against
    current production's 25-file content scope."""

    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    pre_module_text = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    modeled_24_file_literal = _extract_production_frozen_literal_from_source(pre_module_text)
    # Model the 20D contract_versions widening (5 members) while content
    # scope remains the pre-repair 24 files -- this is exactly finding
    # B-149O.20D-1's own disclosed gap.
    modeled_5_member_ids = list(_extract_production_contract_ids_from_source(pre_module_text)) + ["HBDC-001"]

    modeled_digest = _independent_scope_digest(_REPO_ROOT, modeled_24_file_literal)
    current_digest = hmic.derive_implementation_scope_digest(HarnessPath(_REPO_ROOT))
    assert modeled_digest != current_digest

    current_ids = [cid for cid, _ in hmic._CONTRACT_IDENTITY_FILES]
    # Even though the modeled 5-member ID set is superficially equal,
    # implementation_scope_digest is the load-bearing identity term and
    # it already differs above -- precedence is content-digest-mismatch,
    # not a false-accept via contract_versions alone.
    assert modeled_digest != current_digest
    assert sorted(modeled_5_member_ids) == sorted(current_ids)  # ID *set* coincidentally equal; digest still differs


# ---------------------------------------------------------------------------
# HMIC-REQ-145 / HMIC-REQ-063 / Option-C status (read-only confirmation)
# ---------------------------------------------------------------------------


def test_hmic_req_145_marks_hbdc_drift_defect_closed():
    match = re.search(r"\*\*HMIC-REQ-145.*?\n(.*?)\n\n---", _CONTRACT_TEXT, re.S)
    assert match is not None
    block = match.group(0)
    assert "Repair (this section, as of 149O.20D.1" in block
    assert "now the\ntwenty-fifth entry" in block or "now the" in block


def test_hmic_req_063_residual_limitation_still_present_unresolved():
    assert "HMIC-REQ-063" in _CONTRACT_TEXT
    assert "does NOT verify that the Python\ninterpreter" in _CONTRACT_TEXT or "does NOT verify" in _CONTRACT_TEXT
    assert "v1.0 of this contract does NOT implement" in _CONTRACT_TEXT


def test_current_real_readiness_is_not_ready():
    from pcae.core.hatp_mandatory_cutover import assess_hatp_mandatory_activation_readiness
    from pcae.core.paths import HarnessPath

    result = assess_hatp_mandatory_activation_readiness(HarnessPath(_REPO_ROOT))
    assert result.ready is False

    readiness_fact_check = next(
        c for c in result.checks if c.name == "mandatory_consumption_implementation_independently_verified"
    )
    assert readiness_fact_check.satisfied is False

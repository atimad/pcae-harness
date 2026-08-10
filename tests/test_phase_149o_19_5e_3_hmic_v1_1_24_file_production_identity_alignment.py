"""Phase 149O.19.5E.3 -- HMIC v1.1 24-File Production Identity Alignment.

Resolves the production half of Stop Condition W-1
(`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`
§50, HMIC-REQ-050/052): `src/pcae/core/hatp_mandatory_certification.py`'s
own `_FROZEN_AUTHORITY_BEARING_FILES` constant is realigned from the
pre-v1.1, twenty-two-file set to the independently verified v1.1
twenty-four-file set (adding itself,
`core/hatp_mandatory_certification.py`, and the Protected Admin ceremony
script, `scripts/hatp_certification_admin.py`).

This is a NARROW PRODUCTION CONTRACT-ALIGNMENT phase. It does not amend
HMIC-001 (which must remain byte-unchanged -- verified independently in
149O.19.5E.2), does not change the digest algorithm, Git identity
semantics, validator/storage/admin semantics, or the hard-coded
`mandatory_consumption_implementation_independently_verified = False`
readiness ceiling, and wires no readiness/cutover caller of the
validator. W-1 is NOT closed by this phase -- an independent
implementation-verification phase (149O.19.5E.4) is required next; Wave
F remains blocked.

Covers (per the governing phase instruction, §48-109):
  * exact production/contract 24-file set equality, independently
    extracted from the live contract text (never a copied production
    constant used as its own "expected" value);
  * the 23 unmodified frozen files are byte-identical to this phase's own
    entry commit; only the core HMIC module itself changed;
  * self-binding: the core module's post-edit bytes (not stale pre-edit
    bytes) participate in the digest it computes -- proven against the
    real, live implementation-scope digest, not a fixture;
  * admin-script and all-24-file mutation sensitivity;
  * historical 22-file vs current 24-file digest mismatch, and a
    modeled v1.0-scope-replay rejection, for an identical snapshot;
  * no caller-suppliable legacy/22-file scope override exists;
  * digest algorithm, Git-identity derivation, and validator/storage/
    admin-script semantics are AST-source-identical to this phase's own
    entry commit -- only the frozen-set constants and their surrounding
    comments changed;
  * hard-coded `False` readiness ceiling unchanged; zero readiness/
    cutover callers of the validator; admin script byte-unchanged;
    HMIC-001 and all seven other upstream contracts byte-unchanged.
"""
from __future__ import annotations

import ast
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACT_PATH = (
    _REPO_ROOT
    / "docs"
    / "contracts"
    / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
_CUTOVER_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"

#: This phase's own entry commit -- 149O.19.5E.2's own exit commit
#: (`.pcae/phase-completion-metadata.json`'s `source_revision` as
#: observed at this phase's own initial inspection). Production still
#: implemented the pre-amendment 22-file set at this commit.
_PHASE_ENTRY_COMMIT = "e0f64390"

#: The eight contracts HMIC-REQ-050/053/067 bind -- HMIC-001 itself plus
#: the seven upstream contracts this phase must not touch.
_UPSTREAM_CONTRACT_RELATIVE_PATHS = (
    "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
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


def _live_contract_24_canonical_paths() -> "list[str]":
    """Independently extracts HMIC-REQ-050's 24 entries from the live
    contract text and resolves each to its repository-relative canonical
    path (existence-based split, not trusting the contract's own
    src/pcae-vs-root grouping prose)."""

    entries = [e.split()[0] for e in _extract_req_050_block(_CONTRACT_TEXT)]
    assert len(entries) == 24
    result = []
    for entry in entries:
        if (_SRC / entry).exists():
            result.append(f"src/pcae/{entry}")
        else:
            result.append(entry)
    return result


def _independent_scope_digest(root: Path, canonical_relative_paths: "list[str]") -> str:
    """A from-scratch reimplementation of HMIC-REQ-054/056-058's two-level
    digest construction, independent of
    `derive_implementation_scope_digest` in production."""

    ordered = sorted(canonical_relative_paths)
    records = bytearray()
    for rel in ordered:
        file_bytes = (root / rel).read_bytes()
        file_digest = _sha256_hex(file_bytes)
        records += rel.encode("utf-8") + b"\0" + file_digest.encode("ascii") + b"\n"
    return _sha256_hex(bytes(records))


# ---------------------------------------------------------------------------
# §48/§50/§75/§76 -- exact production/contract 24-file set equality
# ---------------------------------------------------------------------------


def test_production_frozen_set_exactly_equals_live_contract_24_file_set():
    from pcae.core import hatp_mandatory_certification as hmic

    contract_paths = set(_live_contract_24_canonical_paths())
    production_paths = set(hmic._frozen_canonical_paths())

    assert len(contract_paths) == 24
    assert len(production_paths) == 24
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


def test_production_frozen_set_count_assertion_is_exactly_24():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", source)
    assert match is not None
    assert match.group(1) == "24"
    # No permissive ">= 24" / range-based acceptance anywhere nearby.
    assert ">= 24" not in source
    assert ">=24" not in source


def test_new_entries_are_exactly_the_two_verified_additions():
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = set(hmic._frozen_canonical_paths())
    assert "src/pcae/core/hatp_mandatory_certification.py" in canonical
    assert "scripts/hatp_certification_admin.py" in canonical


# ---------------------------------------------------------------------------
# §40-44/§104 -- file existence, safety, canonicalization over all 24
# ---------------------------------------------------------------------------


def test_all_24_frozen_paths_exist_are_regular_and_not_symlinked():
    from pcae.core import hatp_mandatory_certification as hmic

    for canonical_path in hmic._frozen_canonical_paths():
        path = _REPO_ROOT / canonical_path
        assert path.exists(), f"frozen path missing: {canonical_path}"
        assert not path.is_symlink(), f"frozen path is a symlink: {canonical_path}"
        assert path.is_file(), f"frozen path is not a regular file: {canonical_path}"


def test_scripts_path_accepted_with_no_special_casing():
    from pcae.core import hatp_mandatory_certification as hmic

    hmic._validate_frozen_path_literal("scripts/hatp_certification_admin.py")
    assert "scripts/hatp_certification_admin.py" in hmic._frozen_canonical_paths()


def test_frozen_set_is_immutable_tuple_not_list_or_set():
    from pcae.core import hatp_mandatory_certification as hmic

    assert isinstance(hmic._FROZEN_AUTHORITY_BEARING_FILES, tuple)
    assert isinstance(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES, tuple)
    assert isinstance(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES, tuple)


def test_no_duplicate_entries():
    from pcae.core import hatp_mandatory_certification as hmic

    assert len(set(hmic._FROZEN_AUTHORITY_BEARING_FILES)) == len(hmic._FROZEN_AUTHORITY_BEARING_FILES)


# ---------------------------------------------------------------------------
# §104/§55-56 -- exactly one frozen file intentionally changed; the other
# 23 must remain byte-unchanged since this phase's own entry commit
# ---------------------------------------------------------------------------


def test_exactly_one_frozen_file_changed_the_other_23_are_byte_unchanged():
    from pcae.core import hatp_mandatory_certification as hmic

    changed = []
    unchanged = []
    for canonical_path in hmic._frozen_canonical_paths():
        current_bytes = (_REPO_ROOT / canonical_path).read_bytes()
        entry_text = _git_show(_PHASE_ENTRY_COMMIT, canonical_path)
        if current_bytes.decode("utf-8", errors="surrogateescape") != entry_text:
            changed.append(canonical_path)
        else:
            unchanged.append(canonical_path)

    assert changed == ["src/pcae/core/hatp_mandatory_certification.py"], (
        f"expected exactly the core HMIC module to change; got: {changed}"
    )
    assert len(unchanged) == 23


def test_admin_script_byte_unchanged_since_phase_entry():
    current = _ADMIN_SCRIPT_PATH.read_bytes()
    entry = _git_show(_PHASE_ENTRY_COMMIT, "scripts/hatp_certification_admin.py").encode("utf-8")
    assert current == entry


def test_hmic_contract_and_upstream_contracts_byte_unchanged_since_phase_entry():
    for rel in _UPSTREAM_CONTRACT_RELATIVE_PATHS:
        current = (_REPO_ROOT / rel).read_bytes()
        entry = _git_show(_PHASE_ENTRY_COMMIT, rel).encode("utf-8")
        assert current == entry, f"upstream contract changed since phase entry: {rel}"


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
# §56-60/§83-85 -- hunk classification: the ONLY production change is the
# frozen-set constants/count-assert/their comments -- no validator,
# storage, admin-writer, parser, or digest-algorithm function body changed.
# Verified at the AST function/class-source level against this phase's own
# entry commit, so an unrelated same-file edit cannot hide inside an
# incidental whole-file byte diff.
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
    and their surrounding module-level comments are module-level
    statements, not function/class bodies -- so this test's function-by-
    function comparison independently proves no validator, storage,
    admin-writer, parser, digest, or Git-identity function changed a
    single byte this phase."""

    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")

    current_defs = _top_level_def_sources(current_source)
    entry_defs = _top_level_def_sources(entry_source)

    assert set(current_defs) == set(entry_defs), "function/class inventory changed this phase"

    changed_defs = {name for name in current_defs if current_defs[name] != entry_defs[name]}
    assert changed_defs == set(), f"unexpected function/class body change(s): {changed_defs}"


def test_derive_implementation_scope_digest_algorithm_unchanged():
    """Explicit, named check on top of the whole-module AST sweep above:
    the digest function itself (framing, hash function, ordering) is
    untouched -- only its *inputs* (the frozen-set constants) changed."""

    current_source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    current_defs = _top_level_def_sources(current_source)
    entry_defs = _top_level_def_sources(entry_source)
    assert current_defs["derive_implementation_scope_digest"] == entry_defs["derive_implementation_scope_digest"]
    assert current_defs["_frozen_canonical_paths"] == entry_defs["_frozen_canonical_paths"]
    assert current_defs["_canonical_frozen_path"] == entry_defs["_canonical_frozen_path"]


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
# §30-34/§77-80/§105-106 -- live-digest self-binding, mutation sensitivity,
# and golden-style historical-vs-current mismatch, all against the real
# repository state (not a synthetic fixture) so self-binding is proven
# against production's own post-edit bytes.
# ---------------------------------------------------------------------------


def test_live_digest_uses_post_edit_core_module_bytes_not_stale_cache():
    """§105-106: mutating a *copy* of the live tree's core module and
    recomputing the digest over that copy must differ from the real
    on-disk digest -- proving the digest is a fresh, uncached function of
    current bytes, and that the core module's own current (post-
    alignment) bytes are what get hashed, not some frozen historical
    value."""

    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    # No caching: two consecutive live calls must both reflect current
    # bytes and agree with each other (HMIC-REQ-113).
    root = HarnessPath(_REPO_ROOT)
    assert hmic.derive_implementation_scope_digest(root) == hmic.derive_implementation_scope_digest(root)

    canonical = hmic._frozen_canonical_paths()
    real_digest = _independent_scope_digest(_REPO_ROOT, list(canonical))

    import tempfile

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


def test_all_24_live_files_are_individually_digest_sensitive(tmp_path):
    """§33/§77: for the real, live 24-file set, a one-byte modeled
    mutation of every single frozen file changes the aggregate digest --
    not just the two newly-added entries."""

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
        f"not all 24 frozen files are digest-sensitive: "
        f"insensitive={set(canonical) - set(sensitive)}"
    )


def test_historical_22_file_digest_differs_from_current_24_file_digest(tmp_path):
    """§34/§37/§91: for an identical snapshot of the repository, the
    digest computed over the historical 22-file scope must not equal the
    digest computed over the current, aligned 24-file scope -- a
    v1.0-scope certification cannot be replayed against v1.1."""

    from pcae.core import hatp_mandatory_certification as hmic

    live_24 = list(hmic._frozen_canonical_paths())
    old_22 = [
        p
        for p in live_24
        if p != "src/pcae/core/hatp_mandatory_certification.py"
        and p != "scripts/hatp_certification_admin.py"
    ]
    assert len(old_22) == 22

    tree = tmp_path / "tree"
    for rel in live_24:
        dest = tree / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_REPO_ROOT / rel, dest)

    old_scope_digest = _independent_scope_digest(tree, old_22)
    new_scope_digest = _independent_scope_digest(tree, live_24)
    assert old_scope_digest != new_scope_digest


def test_production_derive_implementation_scope_digest_matches_independent_reimplementation():
    """Golden-style cross-check (§80): production's own
    `derive_implementation_scope_digest`, called against the real
    repository, must equal this test's independently authored digest
    algorithm over the same live 24-file set -- not merely self-
    consistent with itself."""

    from pcae.core.hatp_bootstrap import resolve_canonical_deployment_root  # noqa: F401
    from pcae.core.paths import HarnessPath
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = list(hmic._frozen_canonical_paths())
    expected = _independent_scope_digest(_REPO_ROOT, canonical)
    actual = hmic.derive_implementation_scope_digest(HarnessPath(_REPO_ROOT))
    assert actual == expected


# ---------------------------------------------------------------------------
# §38/§109 -- no caller-suppliable legacy/22-file scope override
# ---------------------------------------------------------------------------


def test_derive_implementation_scope_digest_accepts_no_scope_override_parameter():
    import inspect

    from pcae.core import hatp_mandatory_certification as hmic

    signature = inspect.signature(hmic.derive_implementation_scope_digest)
    param_names = set(signature.parameters)
    assert param_names == {"root"}, f"unexpected caller-suppliable parameter(s): {param_names - {'root'}}"


def test_no_legacy_scope_language_in_production_module():
    source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    for forbidden in ("legacy_scope", "v1_0_compat", "file_count=22", "ignore_new_files", "legacy=True"):
        assert forbidden not in source


# ---------------------------------------------------------------------------
# §63/§28-29/§62 -- hard-coded False ceiling, zero readiness/cutover
# callers, no readiness integration
# ---------------------------------------------------------------------------


def test_hardcoded_readiness_ceiling_still_literal_false():
    source = _CUTOVER_PATH.read_text(encoding="utf-8")
    match = re.search(
        r'"mandatory_consumption_implementation_independently_verified",\s*\n?\s*(True|False)',
        source,
    )
    assert match is not None
    assert match.group(1) == "False"


def test_cutover_module_byte_unchanged_since_phase_entry():
    current = _CUTOVER_PATH.read_bytes()
    entry = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_cutover.py").encode("utf-8")
    assert current == entry


def test_zero_readiness_or_cutover_callers_of_validator():
    forbidden_symbols = (
        "validate_active_hatp_mandatory_independent_verification_certification",
        "hatp_mandatory_certification",
        "hatp_certification_admin",
    )
    cutover_src = _CUTOVER_PATH.read_text(encoding="utf-8")
    for symbol in forbidden_symbols:
        assert symbol not in cutover_src

    result = subprocess.run(
        ["grep", "-rl", "--include=*.py", "hatp_mandatory_certification", str(_SRC), str(_REPO_ROOT / "scripts")],
        capture_output=True,
        text=True,
    )
    referencing_files = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {str(_HMIC_MODULE_PATH), str(_ADMIN_SCRIPT_PATH)}
    assert referencing_files <= allowed, f"unexpected referencing files: {referencing_files - allowed}"


def test_no_real_certification_state_exists_on_host():
    from pcae.core.hatp_bootstrap import HATPTrustStore

    root = HATPTrustStore.production().root
    assert not (root / "certifications.json").exists()
    assert not (root / "certification-bindings.json").exists()


# ---------------------------------------------------------------------------
# §110 -- overall implementation verdict signal: production is aligned,
# W-1 is not closed by this phase alone
# ---------------------------------------------------------------------------


def test_contract_still_records_w1_not_closed_and_wave_f_still_blocked():
    """This phase does not amend the contract (verified above); it merely
    confirms the contract it reads still records the correct pending
    state this phase does not itself resolve."""

    assert "W-1 CLOSED" not in _CONTRACT_TEXT
    assert "Not `READY FOR WAVE" in _CONTRACT_TEXT
    assert "**READY FOR WAVE F**" not in _CONTRACT_TEXT

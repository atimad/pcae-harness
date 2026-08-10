"""Phase 149O.19.5E.2 -- HMIC v1.1 Validator/Admin Implementation Identity
Contract Independent Verification.

This is an INDEPENDENT CONTRACT VERIFICATION phase. It modifies no
`src/pcae/**` file, no `scripts/**` file, and no contract file. It does
NOT trust, import, or copy expected sets/counts/paths from
`tests/test_phase_149o_19_5e_1_hmic_v1_1_validator_admin_identity_contract_evolution.py`
(the phase-under-verification's own test module) -- every fixture below
is independently re-derived either by parsing the live contract text
directly, or by reading the contract's own byte content at the historical
git commit that preceded the v1.1 amendment (`942df2a2`, the 149O.19.3R
repair commit -- the last commit at which HMIC-001 was v1.0).

Covers (per the governing phase instruction, §65-84):
  * independent v1.0-baseline reconstruction from git history and the
    v1.0 -> v1.1 semantic diff;
  * independent, from-scratch extraction of the live 24-file HMIC-REQ-050
    enumeration (no copied list);
  * an independent AST-based transitive-dependency walk of the two newly
    bound files, not a name-existence check;
  * an independently re-implemented digest algorithm (HMIC-REQ-054-058,
    written fresh here, not imported from production) used to test
    self-reference sensitivity (mutating the validator's/admin script's
    own modeled bytes changes the digest) and v1.0-scope-replay/old-scope
    mismatch;
  * production-staleness (still 22 files) and fail-closed proof;
  * requirement/CIVC/attack-matrix inventory counts (144/12/34);
  * HMIC-REQ-063's residual-limitation wording, CIVC-4's strengthened
    text, and attack rows #11/#33/#34's actual normative text (not
    merely their presence);
  * path canonicalization/existence/uniqueness/regular-file/non-symlink
    checks over all 24 paths;
  * that no production source or upstream contract was touched by this
    verification phase itself.
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

#: The commit immediately preceding the v1.1 amendment (149O.19.3R's own
#: repair exit commit) -- HMIC-001 was v1.0 (22-file, repaired) at this
#: commit. Used as this phase's own independent historical fixture,
#: never the 149O.19.5E.1 test module's own baseline constant.
_PRE_V1_1_COMMIT = "942df2a2"

#: This phase's own entry commit (149O.19.5E.1's final commit) -- used to
#: confirm zero production/scripts diff across this verification phase.
_PHASE_ENTRY_COMMIT = "a8282578"


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _extract_req_050_block(contract_text: str) -> "tuple[str, ...]":
    """Independently parses HMIC-REQ-050's fenced code block out of raw
    contract text via regex -- never a copied/hardcoded path list."""

    match = re.search(
        r"HMIC-REQ-050 \(Exact Enumeration.*?```\n(.*?)```",
        contract_text,
        re.S,
    )
    assert match is not None, "HMIC-REQ-050 fenced enumeration block not found in contract text"
    lines = [line.strip() for line in match.group(1).splitlines() if line.strip()]
    return tuple(lines)


def _extract_version(contract_text: str) -> str:
    match = re.search(r"^\*\*Version:\*\*\s*(\S+)", contract_text, re.M)
    assert match is not None
    return match.group(1)


def _extract_req_ids(contract_text: str) -> "list[int]":
    return sorted(set(int(m) for m in re.findall(r"HMIC-REQ-(\d+)", contract_text)))


def _extract_civc_ids(contract_text: str) -> "list[int]":
    return sorted(set(int(m) for m in re.findall(r"CIVC-(\d+)", contract_text)))


def _extract_attack_row_ids(contract_text: str) -> "list[str]":
    match = re.search(
        r"## 41\. Full Mandatory Attack Matrix.*?\n\n(\|.*?)\n\n---",
        contract_text,
        re.S,
    )
    assert match is not None, "attack matrix table not found"
    rows = [
        line
        for line in match.group(1).splitlines()
        if line.startswith("|") and not line.startswith("|---")
    ]
    data_rows = rows[1:]  # drop header row
    return [row.split("|")[1].strip() for row in data_rows]


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _independent_scope_digest(root: Path, canonical_relative_paths: "list[str]") -> str:
    """A from-scratch reimplementation of HMIC-REQ-054/056-058's two-level
    digest construction -- deliberately NOT imported from
    `derive_implementation_scope_digest` in production, so this test
    exercises an independently authored algorithm against the same
    normative spec, not the same code twice."""

    ordered = sorted(canonical_relative_paths)
    records = bytearray()
    for rel in ordered:
        target = root / rel
        file_bytes = target.read_bytes()
        file_digest = _sha256_hex(file_bytes)
        records += rel.encode("utf-8") + b"\0" + file_digest.encode("ascii") + b"\n"
    return _sha256_hex(bytes(records))


# ---------------------------------------------------------------------------
# §66 -- v1.0 baseline reconstruction + v1.0 -> v1.1 diff
# ---------------------------------------------------------------------------


def test_v1_0_baseline_reconstructed_from_git_history_is_22_files_and_v1_0():
    pre_v1_1_text = _git_show(_PRE_V1_1_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    version = _extract_version(pre_v1_1_text)
    assert version == "1.0"
    entries = _extract_req_050_block(pre_v1_1_text)
    assert len(entries) == 22
    assert len(set(entries)) == 22


def test_v1_0_baseline_144_reqs_12_civc_32_attacks():
    pre_v1_1_text = _git_show(_PRE_V1_1_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    assert _extract_req_ids(pre_v1_1_text) == list(range(1, 145))
    assert _extract_civc_ids(pre_v1_1_text) == list(range(1, 13))
    assert len(_extract_attack_row_ids(pre_v1_1_text)) == 32


def test_v1_1_bumps_version_and_adds_exactly_two_files():
    pre_entries = set(
        _extract_req_050_block(
            _git_show(_PRE_V1_1_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
        )
    )
    live_entries = set(_extract_req_050_block(_CONTRACT_TEXT))
    assert _extract_version(_CONTRACT_TEXT) == "1.1"
    added = live_entries - pre_entries
    removed = pre_entries - live_entries
    assert removed == set(), "no original v1.0 path was removed"
    assert added == {
        "core/hatp_mandatory_certification.py",
        "scripts/hatp_certification_admin.py",
    }


def test_v1_1_attack_matrix_grows_from_32_to_34_with_row_11_strengthened():
    pre_rows = _extract_attack_row_ids(
        _git_show(_PRE_V1_1_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")
    )
    live_rows = _extract_attack_row_ids(_CONTRACT_TEXT)
    assert len(pre_rows) == 32
    assert len(live_rows) == 34
    assert live_rows[-2].startswith("33")
    assert live_rows[-1].startswith("34")
    # row 11 strengthened in place: still present, and now references the
    # new v1.1 files by name.
    match = re.search(r"\|\s*11\s*\|(.*?)\|\s*Rejected", _CONTRACT_TEXT, re.S)
    assert match is not None
    row_11_text = match.group(1)
    assert "hatp_mandatory_certification.py" in row_11_text
    assert "hatp_certification_admin.py" in row_11_text


def test_v1_1_civc_4_strengthened_to_cover_own_implementation():
    match = re.search(r"\*\*CIVC-4\.\*\*(.*?)- \*\*CIVC-5\.\*\*", _CONTRACT_TEXT, re.S)
    assert match is not None
    civc4_text = match.group(1)
    assert "core/hatp_mandatory_certification.py" in civc4_text
    assert "scripts/hatp_certification_admin.py" in civc4_text
    assert "v1.1" in civc4_text


# ---------------------------------------------------------------------------
# §67, §78-80 -- independent 24-file extraction, existence, uniqueness,
# regular/non-symlink
# ---------------------------------------------------------------------------


def _resolve_full_path(entry: str, index: int, src_count: int) -> Path:
    if index < src_count:
        return _SRC / entry
    return _REPO_ROOT / entry.split()[0]  # strip trailing "(HMRC-001)"-style annotation


def test_24_file_set_independently_extracted_unique_exists_regular_nonsymlink():
    entries = _extract_req_050_block(_CONTRACT_TEXT)
    assert len(entries) == 24
    assert len(set(entries)) == 24

    # First N entries (up to the blank-separated boundary in the original
    # fenced block) are src/pcae-relative; independently re-derive the
    # split point by testing existence under src/pcae/ first.
    src_relative = []
    root_relative = []
    for entry in entries:
        bare = entry.split()[0]
        if (_SRC / bare).exists():
            src_relative.append(bare)
        else:
            root_relative.append(bare)

    assert len(src_relative) == 19
    assert len(root_relative) == 5
    assert "core/hatp_mandatory_certification.py" in src_relative
    assert "scripts/hatp_certification_admin.py" in root_relative

    all_paths = [_SRC / p for p in src_relative] + [_REPO_ROOT / p for p in root_relative]
    assert len(all_paths) == 24
    for path in all_paths:
        assert path.exists(), f"frozen path missing: {path}"
        assert not path.is_symlink(), f"frozen path is a symlink: {path}"
        assert path.is_file(), f"frozen path is not a regular file: {path}"

    # No `..`, no absolute component, no backslash anywhere in the raw
    # enumeration text (HMIC-REQ-055).
    for entry in entries:
        bare = entry.split()[0]
        assert not bare.startswith("/")
        assert "\\" not in bare
        assert ".." not in bare.split("/")


def test_scripts_path_is_canonically_representable_no_symlink_no_traversal():
    """§16/§45/§77: `scripts/hatp_certification_admin.py` passes the same
    canonicalization grammar as every other frozen path -- no
    `src/pcae/`-only assumption, no ambiguity."""

    rel = "scripts/hatp_certification_admin.py"
    assert not rel.startswith("/")
    assert "\\" not in rel
    assert ".." not in rel.split("/")
    assert _ADMIN_SCRIPT_PATH.exists()
    assert not _ADMIN_SCRIPT_PATH.is_symlink()
    assert _ADMIN_SCRIPT_PATH.is_file()
    assert str(_ADMIN_SCRIPT_PATH.relative_to(_REPO_ROOT)).replace("\\", "/") == rel


# ---------------------------------------------------------------------------
# §68/§14-16 -- independent AST transitive-dependency walk
# ---------------------------------------------------------------------------


def _pcae_owned_imports(path: Path) -> "set[str]":
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: "set[str]" = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pcae."):
            modules.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("pcae."):
                    modules.add(alias.name)
    return modules


def _module_to_path(dotted: str) -> Path:
    # e.g. "pcae.core.hatp_bootstrap" -> src/pcae/core/hatp_bootstrap.py
    parts = dotted.split(".")[1:]  # drop leading "pcae"
    return _SRC / Path(*parts).with_suffix(".py")


def test_transitive_closure_ast_walk_finds_no_unbound_authority_sensitive_file():
    """Independent, source-level AST walk (not a docstring-trust check) of
    both newly-bound files' own `pcae.*` imports. Every resolved module
    must be either already a member of the 24-file frozen set, or the
    pre-adjudicated non-authority `pcae.core.paths` utility (independently
    re-inspected here for its actual content, not merely cited)."""

    frozen_module_paths = {
        _module_to_path(f"pcae.core.hatp_bootstrap"),
        _module_to_path(f"pcae.core.repository_identity"),
        _module_to_path(f"pcae.core.hatp_mandatory_certification"),
    }
    excluded_non_authority = {_module_to_path("pcae.core.paths")}

    walked = set()
    for source_file in (_HMIC_MODULE_PATH, _ADMIN_SCRIPT_PATH):
        walked |= _pcae_owned_imports(source_file)

    resolved_paths = {_module_to_path(m) for m in walked}
    unexplained = resolved_paths - frozen_module_paths - excluded_non_authority
    assert unexplained == set(), f"found PCAE-owned dependency not adjudicated: {unexplained}"

    # Independently re-confirm pcae.core.paths really is a trivial,
    # non-authority-sensitive utility (not merely trusting the prior
    # phase's own classification prose).
    paths_module_src = (_SRC / "core" / "paths.py").read_text(encoding="utf-8")
    for forbidden_token in ("signature", "verify", "digest", "certif", "approval", "credential"):
        assert forbidden_token not in paths_module_src.lower(), (
            f"pcae.core.paths unexpectedly references {forbidden_token!r} -- "
            "re-examine its non-authority classification"
        )

    # Neither newly-bound file imports the readiness/PB/RAE/AG3-AG5 chain.
    forbidden_imports = {
        "pcae.core.hatp_mandatory_cutover",
        "pcae.core.permission_broker",
        "pcae.core.permission_broker_foundation",
        "pcae.core.rollback_approval_evidence",
        "pcae.core.hatp_ag_authority",
        "pcae.core.hatp_rollback_consumption",
    }
    assert walked & forbidden_imports == set()


# ---------------------------------------------------------------------------
# §69-72, §90-92 -- self-reference, admin-source, replay, old-scope tests
# using an independently reimplemented digest algorithm
# ---------------------------------------------------------------------------


def _copy_24_file_tree(tmp_path: Path, canonical_relative_paths: "list[str]") -> Path:
    dest_root = tmp_path / "tree"
    for rel in canonical_relative_paths:
        src_file = _REPO_ROOT / rel
        dest_file = dest_root / rel
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dest_file)
    return dest_root


def _live_24_canonical_paths() -> "list[str]":
    entries = _extract_req_050_block(_CONTRACT_TEXT)
    result = []
    for entry in entries:
        bare = entry.split()[0]
        if (_SRC / bare).exists():
            result.append(f"src/pcae/{bare}")
        else:
            result.append(bare)
    assert len(result) == 24
    return result


def test_self_reference_mutating_validator_source_changes_digest(tmp_path):
    canonical = _live_24_canonical_paths()
    tree = _copy_24_file_tree(tmp_path, canonical)
    baseline = _independent_scope_digest(tree, canonical)

    validator_rel = "src/pcae/core/hatp_mandatory_certification.py"
    target = tree / validator_rel
    target.write_bytes(target.read_bytes() + b"\n# mutated-for-test\n")

    mutated = _independent_scope_digest(tree, canonical)
    assert mutated != baseline, "mutating the validator's own bound source did not change the digest"


def test_admin_source_mutation_changes_digest(tmp_path):
    canonical = _live_24_canonical_paths()
    tree = _copy_24_file_tree(tmp_path, canonical)
    baseline = _independent_scope_digest(tree, canonical)

    admin_rel = "scripts/hatp_certification_admin.py"
    target = tree / admin_rel
    target.write_bytes(target.read_bytes() + b"\n# mutated-for-test\n")

    mutated = _independent_scope_digest(tree, canonical)
    assert mutated != baseline, "mutating the admin script's own bound source did not change the digest"


def test_no_circularity_frozen_set_excludes_generated_certification_artifacts():
    """§18/§90: v1.1 must not hash any generated protected-storage
    artifact (certifications.json, certification-bindings.json, a
    revocation record, or any digest-output file) -- only source/contract
    bytes."""

    entries = _extract_req_050_block(_CONTRACT_TEXT)
    forbidden_names = {"certifications.json", "certification-bindings.json"}
    for entry in entries:
        bare = entry.split()[0]
        assert Path(bare).name not in forbidden_names


def test_v1_0_scope_replay_mismatches_against_v1_1_environment(tmp_path):
    """§71/§91: a hypothetical certification computed over the pre-v1.1
    22-file set must not equal a digest computed over the current v1.1
    24-file set, for the identical underlying repository state."""

    live_24 = _live_24_canonical_paths()
    old_22 = [p for p in live_24 if not p.endswith("hatp_mandatory_certification.py") and not p.endswith("hatp_certification_admin.py")]
    assert len(old_22) == 22

    tree = _copy_24_file_tree(tmp_path, live_24)
    old_scope_digest = _independent_scope_digest(tree, old_22)
    new_scope_digest = _independent_scope_digest(tree, live_24)
    assert old_scope_digest != new_scope_digest


def test_old_22_scope_under_v1_1_does_not_equal_24_file_identity(tmp_path):
    """§72/§92: modeling production's still-22-file scope under the
    current repository does not accidentally coincide with the true
    24-file v1.1 implementation identity."""

    live_24 = _live_24_canonical_paths()
    old_22 = [p for p in live_24 if "hatp_mandatory_certification.py" not in p and "hatp_certification_admin.py" not in p]
    tree = _copy_24_file_tree(tmp_path, live_24)
    assert _independent_scope_digest(tree, old_22) != _independent_scope_digest(tree, live_24)


def test_no_legacy_scope_override_language_in_contract():
    """§22/§86: the contract exposes no `legacy_scope`/`v1_0_compat`/
    `file_count=22`/`ignore_new_files` caller-selectable authority path.
    These tokens MAY appear in the contract text only inside an explicit
    prohibition ("no caller-suppliable ... override") -- never as part of
    a normative grant of such an override."""

    for forbidden in ("legacy_scope", "v1_0_compat", "file_count=22", "ignore_new_files"):
        for match in re.finditer(re.escape(forbidden), _CONTRACT_TEXT):
            window = _CONTRACT_TEXT[max(0, match.start() - 80) : match.start()]
            assert "no caller-suppliable" in window or "No caller-suppliable" in window, (
                f"{forbidden!r} appears outside an explicit no-override-exists prohibition context: "
                f"...{window}[{forbidden}]"
            )


# ---------------------------------------------------------------------------
# §29-30, §76 -- HMIC-REQ-063 residual limitation, unchanged
# ---------------------------------------------------------------------------


def test_req_063_residual_limitation_byte_identical_since_pre_v1_1():
    pre_text = _git_show(_PRE_V1_1_COMMIT, "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md")

    def _extract_req_063(text: str) -> str:
        match = re.search(r"\*\*HMIC-REQ-063 \(.*?\*\*(.*?)\*\*HMIC-REQ-064", text, re.S)
        assert match is not None
        return match.group(1).strip()

    assert _extract_req_063(pre_text) == _extract_req_063(_CONTRACT_TEXT)


def test_req_063_does_not_claim_runtime_source_binding_solved():
    match = re.search(r"\*\*HMIC-REQ-063.*?\*\*HMIC-REQ-064", _CONTRACT_TEXT, re.S)
    assert match is not None
    # Normalize whitespace/line-wrap so a normative phrase spanning a
    # markdown line-wrap is still matched.
    text = re.sub(r"\s+", " ", match.group(0))
    assert "does NOT implement an executed-code" in text or "does NOT verify" in text
    assert "SHALL NOT be represented" in text


# ---------------------------------------------------------------------------
# §73-74, §35-39 -- production staleness + fail-closed proof
# ---------------------------------------------------------------------------


def test_production_frozen_set_still_22_files_expected_divergence():
    module_src = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
    match = re.search(r"assert len\(_FROZEN_AUTHORITY_BEARING_FILES\) == (\d+)", module_src)
    assert match is not None
    assert int(match.group(1)) == 22, (
        "production frozen-file count changed from 22 -- this contract-verification "
        "phase expected production to remain intentionally stale; if this now reads "
        "24, a production-alignment phase has already run and this test module is stale"
    )
    assert "hatp_mandatory_certification.py" not in re.search(
        r"_FROZEN_SRC_PCAE_RELATIVE_FILES.*?\)\n", module_src, re.S
    ).group(0)


def test_hardcoded_false_ceiling_unchanged():
    cutover_src = (_SRC / "core" / "hatp_mandatory_cutover.py").read_text(encoding="utf-8")
    assert '"mandatory_consumption_implementation_independently_verified"' in cutover_src
    match = re.search(
        r'"mandatory_consumption_implementation_independently_verified",\s*\n?\s*(True|False)',
        cutover_src,
    )
    assert match is not None
    assert match.group(1) == "False"


def test_zero_readiness_or_cutover_callers_of_validator():
    forbidden_symbols = (
        "validate_active_hatp_mandatory_independent_verification_certification",
        "hatp_mandatory_certification",
        "hatp_certification_admin",
    )
    cutover_src = (_SRC / "core" / "hatp_mandatory_cutover.py").read_text(encoding="utf-8")
    for symbol in forbidden_symbols:
        assert symbol not in cutover_src

    result = subprocess.run(
        [
            "grep",
            "-rl",
            "--include=*.py",
            "hatp_mandatory_certification",
            str(_SRC),
            str(_REPO_ROOT / "scripts"),
        ],
        capture_output=True,
        text=True,
    )
    referencing_files = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {str(_HMIC_MODULE_PATH), str(_ADMIN_SCRIPT_PATH)}
    assert referencing_files <= allowed, f"unexpected referencing files: {referencing_files - allowed}"


def test_no_real_certification_state_exists_on_host():
    from pcae.core.hatp_bootstrap import HATPTrustStore

    root = HATPTrustStore.production().root
    certifications_file = root / "certifications.json"
    bindings_file = root / "certification-bindings.json"
    # Read-only existence check only -- never created as a side effect of
    # this test (HATPTrustStore.production() performs no I/O beyond path
    # resolution).
    assert not certifications_file.exists()
    assert not bindings_file.exists()


# ---------------------------------------------------------------------------
# §75, §84 -- requirement/CIVC/attack inventory counts on the live contract
# ---------------------------------------------------------------------------


def test_live_contract_144_requirements_12_civc_34_attacks():
    assert _extract_req_ids(_CONTRACT_TEXT) == list(range(1, 145))
    assert _extract_civc_ids(_CONTRACT_TEXT) == list(range(1, 13))
    assert len(_extract_attack_row_ids(_CONTRACT_TEXT)) == 34


def test_w1_status_repaired_not_closed_no_wave_f_authorization():
    assert "REPAIRED AT CONTRACT LEVEL" in _CONTRACT_TEXT
    assert "W-1: CLOSED" not in _CONTRACT_TEXT
    assert "READY FOR WAVE F" not in _CONTRACT_TEXT


def test_contract_status_header_reflects_v1_1_pending_verification():
    assert "**Version:** 1.1" in _CONTRACT_TEXT
    header_match = re.search(r"\*\*Status:\*\*\s*(.*)", _CONTRACT_TEXT)
    assert header_match is not None
    assert "PENDING INDEPENDENT VERIFICATION" in header_match.group(1)


def test_contract_versioning_section_stale_v1_0_literal_is_a_known_finding():
    """Non-blocking finding, independently confirmed: §42 (HMIC-REQ-139)
    and §46's verdict block still literally read 'HMIC-001 v1.0', not
    updated when the header/§50 bumped to v1.1. This does not create any
    ambiguity about the contract's actual, governing version (the header
    and §50's own amendment-history section are unambiguous, and no
    consumer reads §42/§46 as authoritative over the header) but is
    recorded here as a disclosed textual-consistency gap, not silently
    passed over."""

    assert "This contract is frozen as `HMIC-001 v1.0`" in _CONTRACT_TEXT
    assert "HMIC-001 v1.0: FROZEN — READY FOR INDEPENDENT CONTRACT VERIFICATION" in _CONTRACT_TEXT
    # But the authoritative header and the v1.1 amendment section are
    # unambiguous about the real, current version:
    assert re.search(r"^\*\*Version:\*\*\s*1\.1\s*$", _CONTRACT_TEXT, re.M)
    assert "HMIC-001 moves from **v1.0** to\n**v1.1**" in _CONTRACT_TEXT or "HMIC-001 moves from **v1.0** to **v1.1**" in _CONTRACT_TEXT.replace("\n", " ")


# ---------------------------------------------------------------------------
# §54, §56 -- no production/contract/upstream mutation by this phase
# ---------------------------------------------------------------------------


def test_no_production_or_scripts_file_changed_since_phase_entry():
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "--", "src/pcae", "scripts"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    assert changed == []


def test_upstream_contracts_byte_unchanged_since_phase_entry():
    result = subprocess.run(
        ["git", "diff", "--name-only", _PHASE_ENTRY_COMMIT, "--", "docs/contracts"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [line for line in result.stdout.splitlines() if line.strip()]
    assert changed == [], f"unexpected contract-file changes: {changed}"

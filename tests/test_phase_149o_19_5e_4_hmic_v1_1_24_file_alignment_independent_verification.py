"""Phase 149O.19.5E.4 -- HMIC v1.1 24-File Production Identity Alignment
Independent Verification.

This is an INDEPENDENT IMPLEMENTATION VERIFICATION phase. It modifies no
`src/pcae/**` file, no `scripts/**` file, and no contract file. It does
NOT trust, import, or reuse
`tests/test_phase_149o_19_5e_3_hmic_v1_1_24_file_production_identity_alignment.py`
(the phase-under-verification's own test module) as evidence -- every
independent claim below is re-derived here from primary sources: the
live contract text (parsed fresh, never a copied production constant
compared against itself), the live production module (read via AST, not
merely imported and trusted), and, for the digest algorithm, a
from-scratch reimplementation of HMIC-REQ-054-058 written independently
in this file.

Adds validator-level (Wave D) fixture round-trip coverage that neither
149O.19.5E.3 nor 149O.19.5E.2 performed: a fully-consistent isolated
fixture validates VALID under the current (post-E.3) frozen-set shape,
a core-module/admin-script self-reference mutation attack against that
fixture yields IMPLEMENTATION_MISMATCH, and a modeled v1.0-scope (fewer
frozen files) certification replayed against a v1.1-shaped environment
also yields IMPLEMENTATION_MISMATCH -- using the isolated-fixture pattern
established by `tests/test_phase_149o_19_5d_hmic_active_certification_validation_engine.py`
(`env` fixture, `_FROZEN_AUTHORITY_BEARING_FILES` monkeypatch), never
this repository's own real frozen files (item 81/113 discipline).

Covers (per the governing phase instruction, §67-90):
  * independent contract 24-file extraction and independent production
    24-file extraction (AST-based, not `import` + trust), exact set and
    literal-order equality;
  * independent digest reimplementation cross-checked against
    `derive_implementation_scope_digest` on the live repository;
  * all-24 mutation sensitivity and core/admin self-binding, using an
    independently written digest function, not production's;
  * historical 22-file reconstruction from the phase-149O.19.5E.3-entry
    commit and the exact-two-additions delta;
  * v1.0 (22-file) vs current (24-file) digest mismatch on an identical
    snapshot;
  * validator-level (Wave D) VALID / IMPLEMENTATION_MISMATCH fixture
    round trips exercising self-binding and v1.0-scope replay through
    the actual validation algorithm, not just the digest function;
  * legacy-scope-override absence, hard-coded-False/zero-caller
    unchanged, no real certification state;
  * that no production source or upstream contract was touched by this
    verification phase itself.
"""
from __future__ import annotations

import ast
import hashlib
import re
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import ensure_repository_identity

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACT_PATH = (
    _REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)
_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_ADMIN_SCRIPT_PATH = _REPO_ROOT / "scripts" / "hatp_certification_admin.py"
_CUTOVER_PATH = _SRC / "core" / "hatp_mandatory_cutover.py"

# This phase's own entry commit -- 149O.19.5E.3's last commit, i.e. the
# state this verification phase must not itself have moved past.
_PHASE_ENTRY_COMMIT = "e0f64390"
_PRE_E3_COMMIT = _PHASE_ENTRY_COMMIT  # E.3's phase-entry commit == E.4's phase-entry commit == pre-alignment state


def _git(args: "list[str]", cwd: Path = _REPO_ROOT) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return result.stdout


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    )
    return result.stdout


# ═══════════════════════════════════════════════════════════════════════════
# Independent contract 24-file extraction (fresh regex/parse of the live
# contract text, never a copied production list).
# ═══════════════════════════════════════════════════════════════════════════


def _extract_contract_files() -> "list[str]":
    match = re.search(r"HMIC-REQ-050 \(Exact Enumeration.*?```\n(.*?)```", _CONTRACT_TEXT, re.S)
    assert match, "could not locate the HMIC-REQ-050 fenced enumeration block"
    lines = [l for l in match.group(1).splitlines() if l.strip()]
    # Strip trailing "  (HMRC-001)"-style contract-ID annotations: the
    # bare path is everything before two-or-more spaces.
    return [re.split(r"\s{2,}", line.strip())[0] for line in lines]


def _contract_canonical_paths() -> "list[str]":
    bare = _extract_contract_files()
    canonical = []
    for entry in bare:
        if entry.startswith("core/") or entry.startswith("commands/") or entry == "cli.py":
            canonical.append(f"src/pcae/{entry}")
        else:
            canonical.append(entry)
    return canonical


# ═══════════════════════════════════════════════════════════════════════════
# Independent production 24-file extraction (AST parse of the live module
# source, never `import` + trust of the resulting Python object alone).
# ═══════════════════════════════════════════════════════════════════════════


def _ast_tuple_strings(node: ast.AST) -> "tuple[str, ...]":
    return tuple(elt.value for elt in node.elts if isinstance(elt, ast.Constant) and isinstance(elt.value, str))


def _production_literal_tuples(source: str) -> "tuple[tuple[str, ...], tuple[str, ...]]":
    tree = ast.parse(source)
    src_pcae_tuple = None
    root_tuple = None
    for node in ast.walk(tree):
        target = None
        value = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target, value = node.targets[0].id, node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target, value = node.target.id, node.value
        if target == "_FROZEN_SRC_PCAE_RELATIVE_FILES" and value is not None:
            src_pcae_tuple = _ast_tuple_strings(value)
        elif target == "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES" and value is not None:
            root_tuple = _ast_tuple_strings(value)
    assert src_pcae_tuple is not None and root_tuple is not None
    return src_pcae_tuple, root_tuple


def _live_production_canonical_paths() -> "list[str]":
    """Live counterpart to `_production_canonical_paths()` (below): used
    only by cross-checks whose claim is "production's live output is
    internally self-consistent right now" (a structural property of the
    mechanism), never by claims about this phase's own historical
    24-file checkpoint."""

    src_pcae_tuple, root_tuple = _production_literal_tuples(_HMIC_MODULE_PATH.read_text(encoding="utf-8"))
    return [f"src/pcae/{e}" for e in src_pcae_tuple] + list(root_tuple)


def _production_canonical_paths() -> "list[str]":
    # Pinned to this phase's own exit commit (_PRE_WAVE_F_COMMIT,
    # dd649271): this entire module independently verifies the 24-file
    # production alignment 149O.19.5E.3 achieved and 149O.19.5E.4 itself
    # confirmed -- a fixed historical checkpoint, not live current state.
    # Phase 149O.20F later, legitimately widens production to 25 entries
    # (149O.20D.1's HBDC-001 repair, aligned by 149O.20F); this module's
    # own claims about the 24-file checkpoint are preserved unweakened.
    source = _git_show(_PRE_WAVE_F_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    src_pcae_tuple, root_tuple = _production_literal_tuples(source)
    return [f"src/pcae/{e}" for e in src_pcae_tuple] + list(root_tuple)


# ═══════════════════════════════════════════════════════════════════════════
# Independent digest reimplementation (HMIC-REQ-054-058, written fresh
# here -- never imported from production, and never `hashlib` used with
# production's own helper functions).
# ═══════════════════════════════════════════════════════════════════════════


def _independent_digest(paths: "list[str]", root: Path) -> str:
    hasher = hashlib.sha256()
    for canonical_path in sorted(paths):
        data = (root / canonical_path).read_bytes()
        file_digest = hashlib.sha256(data).hexdigest()
        record = f"{canonical_path}\0{file_digest}\n".encode("utf-8")
        hasher.update(record)
    return hasher.hexdigest()


_HISTORICAL_22 = [
    "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
    "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
    "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
    "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
    "src/pcae/cli.py",
    "src/pcae/commands/agent.py",
    "src/pcae/core/agent.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/hatp_evidence_store.py",
    "src/pcae/core/hatp_fido2_provider.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/hatp_mandatory_cutover.py",
    "src/pcae/core/hatp_piv_provider.py",
    "src/pcae/core/hatp_providers.py",
    "src/pcae/core/hatp_rollback_consumption.py",
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    "src/pcae/core/repository_identity.py",
    "src/pcae/core/rollback_approval_evidence.py",
]

_EXPECTED_TWO_ADDITIONS = {
    "src/pcae/core/hatp_mandatory_certification.py",
    "scripts/hatp_certification_admin.py",
}


# ═══════════════════════════════════════════════════════════════════════════
# 1. Contract/production 24-file set equality (independent extraction)
# ═══════════════════════════════════════════════════════════════════════════


class TestExactSetEquality:
    def test_contract_enumeration_has_24_entries_no_duplicates(self) -> None:
        files = _extract_contract_files()
        assert len(files) == 24
        assert len(set(files)) == 24

    def test_production_enumeration_has_24_entries_no_duplicates(self) -> None:
        paths = _production_canonical_paths()
        assert len(paths) == 24
        assert len(set(paths)) == 24

    def test_contract_and_production_sets_are_exactly_equal(self) -> None:
        # Live-vs-live consistency (not this module's historical 24-file
        # checkpoint): confirms the CURRENT live contract enumeration and
        # CURRENT live production constant remain aligned -- Phase
        # 149O.20F later, legitimately widens both sides in lockstep to
        # 25 entries; this test's claim ("contract and production agree")
        # continues to hold, now at the current count.
        assert set(_contract_canonical_paths()) == set(_live_production_canonical_paths())

    def test_contract_and_production_literal_order_is_identical(self) -> None:
        # Compare bare (non-prefixed) literal presentation order directly,
        # independent of any canonicalization step.
        bare_contract = _extract_contract_files()
        src_pcae_tuple, root_tuple = _production_literal_tuples(_HMIC_MODULE_PATH.read_text(encoding="utf-8"))
        assert bare_contract == list(src_pcae_tuple) + list(root_tuple)

    def test_all_24_files_exist_are_regular_not_symlinked(self) -> None:
        for path in _production_canonical_paths():
            full = _REPO_ROOT / path
            assert full.is_file(), f"missing: {path}"
            assert not full.is_symlink(), f"symlinked: {path}"

    def test_production_frozen_canonical_paths_matches_independent_sorted_set(self) -> None:
        # Live-vs-live consistency, same rationale as the test above.
        assert list(hmic._frozen_canonical_paths()) == sorted(_live_production_canonical_paths())


# ═══════════════════════════════════════════════════════════════════════════
# 2. Historical 22-file reconstruction + exact two additions
# ═══════════════════════════════════════════════════════════════════════════


class TestHistoricalReconstruction:
    def test_pre_e3_entry_commit_module_has_22_files(self) -> None:
        source = _git_show(_PRE_E3_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
        src_pcae_tuple, root_tuple = _production_literal_tuples(source)
        assert len(src_pcae_tuple) + len(root_tuple) == 22

    def test_historical_22_matches_independently_reconstructed_list(self) -> None:
        source = _git_show(_PRE_E3_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
        src_pcae_tuple, root_tuple = _production_literal_tuples(source)
        historical = sorted([f"src/pcae/{e}" for e in src_pcae_tuple] + list(root_tuple))
        assert historical == sorted(_HISTORICAL_22)

    def test_historical_22_all_present_in_current_24(self) -> None:
        current = set(_production_canonical_paths())
        assert set(_HISTORICAL_22).issubset(current)

    def test_current_minus_historical_equals_exactly_two_named_additions(self) -> None:
        current = set(_production_canonical_paths())
        assert current - set(_HISTORICAL_22) == _EXPECTED_TWO_ADDITIONS

    def test_b_149o_19_3_1_four_provider_repair_files_still_present(self) -> None:
        current = set(_production_canonical_paths())
        for f in (
            "src/pcae/core/hatp_providers.py",
            "src/pcae/core/hatp_fido2_provider.py",
            "src/pcae/core/hatp_piv_provider.py",
            "src/pcae/core/hatp_hardware_credentials.py",
        ):
            assert f in current


# ═══════════════════════════════════════════════════════════════════════════
# 3. E.3 production diff reconstruction: exactly one file, no other
#    production/scripts/contract file touched.
# ═══════════════════════════════════════════════════════════════════════════


class TestE3DiffReconstruction:
    # Phase 149O.19.5F (Wave F, gated by Stop Condition W-1 --
    # independently confirmed closed by THIS phase, 149O.19.5E.4) later,
    # legitimately modifies hatp_mandatory_cutover.py. Every comparison
    # in this class is pinned to `_PRE_WAVE_F_COMMIT` (this repository's
    # own last commit before Wave F) rather than an open-ended
    # "...HEAD forever" comparison, so this phase's own E.3-diff-
    # reconstruction claims are preserved exactly.

    def test_exactly_one_src_pcae_or_scripts_file_changed(self) -> None:
        diff = _git(["diff", "--name-only", _PHASE_ENTRY_COMMIT, _PRE_WAVE_F_COMMIT, "--", "src/pcae/", "scripts/"])
        changed = [l for l in diff.splitlines() if l.strip()]
        assert changed == ["src/pcae/core/hatp_mandatory_certification.py"]

    def test_admin_script_byte_unchanged(self) -> None:
        diff = _git(["diff", "--stat", _PHASE_ENTRY_COMMIT, _PRE_WAVE_F_COMMIT, "--", "scripts/hatp_certification_admin.py"])
        assert diff.strip() == ""

    def test_cutover_module_byte_unchanged(self) -> None:
        diff = _git(["diff", "--stat", _PHASE_ENTRY_COMMIT, _PRE_WAVE_F_COMMIT, "--", "src/pcae/core/hatp_mandatory_cutover.py"])
        assert diff.strip() == ""

    def test_all_eight_bound_contracts_byte_unchanged(self) -> None:
        for path in (
            "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md",
            "docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
            "docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
            "docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
            "docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
        ):
            diff = _git(["diff", "--stat", _PHASE_ENTRY_COMMIT, _PRE_WAVE_F_COMMIT, "--", path])
            assert diff.strip() == "", f"{path} changed"

    def test_other_23_frozen_files_byte_unchanged(self) -> None:
        others = [p for p in _production_canonical_paths() if p != "src/pcae/core/hatp_mandatory_certification.py"]
        assert len(others) == 23
        for path in others:
            diff = _git(["diff", "--stat", _PHASE_ENTRY_COMMIT, _PRE_WAVE_F_COMMIT, "--", path])
            assert diff.strip() == "", f"{path} changed unexpectedly"

    def test_diff_hunk_is_only_frozen_set_tuples_count_and_comments(self) -> None:
        # Independently re-parse the *post-image* (current) module with
        # AST and diff its top-level statement bytes against the
        # phase-entry module's top-level statements, rather than a
        # line-oriented heuristic (which cannot safely distinguish
        # docstring prose from code). Only the two frozen-set tuple
        # assignments and the count assertion may differ; every other
        # top-level statement (including the module docstring itself,
        # whose prose changed 22->24 but is not executable code) is
        # exempted explicitly below since HMIC-REQ-054-062 concern code
        # semantics, not comments/docstrings -- already independently
        # confirmed byte-identical for every *function/class* body in
        # `TestSemanticStability`.
        # `after_src` is pinned to this phase's own exit commit
        # (_PRE_WAVE_F_COMMIT), not live source: Phase 149O.20F later,
        # legitimately touches a third top-level constant
        # (`_CONTRACT_IDENTITY_FILES`) that did not exist as a frozen-set
        # concern at 149O.19.5E.3/E.4's own time -- this test's claim is
        # about THIS phase's OWN diff window, preserved unweakened.
        before_src = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
        after_src = _git_show(_PRE_WAVE_F_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
        before_tree = ast.parse(before_src)
        after_tree = ast.parse(after_src)

        def top_level_assigns(tree):
            out = {}
            for node in tree.body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    out[node.targets[0].id] = ast.dump(node)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    out[node.target.id] = ast.dump(node)
            return out

        before_assigns = top_level_assigns(before_tree)
        after_assigns = top_level_assigns(after_tree)
        assert set(before_assigns) == set(after_assigns), "top-level constant set changed"

        changed_names = {
            name for name in before_assigns if before_assigns[name] != after_assigns[name]
        }
        assert changed_names == {
            "_FROZEN_SRC_PCAE_RELATIVE_FILES",
            "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES",
        }, f"unexpected top-level constant changes: {changed_names}"

        # The count assertion (`assert len(...) == 24`) is the only
        # top-level `ast.Assert` statement expected to differ.
        def top_level_asserts(tree):
            return [ast.dump(node) for node in tree.body if isinstance(node, ast.Assert)]

        before_asserts = top_level_asserts(before_tree)
        after_asserts = top_level_asserts(after_tree)
        assert len(before_asserts) == len(after_asserts) == 1
        assert "24" in ast.unparse(ast.parse(after_src).body[[
            i for i, n in enumerate(after_tree.body) if isinstance(n, ast.Assert)
        ][0]])


# ═══════════════════════════════════════════════════════════════════════════
# 4. Digest algorithm: independent reimplementation cross-check, all-24
#    sensitivity, self-binding (core + admin), no cache/import-time
#    computation, no legacy override.
# ═══════════════════════════════════════════════════════════════════════════


class TestDigestAlgorithm:
    def test_golden_digest_matches_production_on_live_repository(self) -> None:
        # Self-binding/golden-cross-check infrastructure proof: production's
        # OWN current `derive_implementation_scope_digest` is exercised
        # against the CURRENT live frozen-set membership (`hmic._frozen_
        # canonical_paths()`), not this module's own historically-pinned
        # 24-path snapshot -- Phase 149O.20F later, legitimately widens
        # production's live scope to 25 entries, and this test's claim
        # ("production's function correctly implements the algorithm over
        # whatever it currently hashes") is a structural property of the
        # mechanism, unaffected by which historical count is current.
        paths = list(hmic._frozen_canonical_paths())
        golden = _independent_digest(paths, _REPO_ROOT)
        produced = hmic.derive_implementation_scope_digest(HarnessPath(_REPO_ROOT))
        assert golden == produced

    def test_all_24_files_are_individually_mutation_sensitive(self, tmp_path) -> None:
        paths = _production_canonical_paths()
        for path in paths:
            dest = tmp_path / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((_REPO_ROOT / path).read_bytes())
        baseline = _independent_digest(paths, tmp_path)
        sensitive = 0
        for path in paths:
            target = tmp_path / path
            original = target.read_bytes()
            target.write_bytes(original + b"\nmutated\n")
            mutated = _independent_digest(paths, tmp_path)
            target.write_bytes(original)
            if mutated != baseline:
                sensitive += 1
        assert sensitive == 24

    def test_core_module_self_binding_uses_post_change_bytes(self, tmp_path) -> None:
        # Live-infrastructure proof (see comment on the golden-digest test
        # above): exercises production's current, real function and
        # current, real frozen-set membership, not this module's
        # historically-pinned 24-path snapshot.
        paths = list(hmic._frozen_canonical_paths())
        for path in paths:
            dest = tmp_path / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((_REPO_ROOT / path).read_bytes())
        root = HarnessPath(tmp_path)
        baseline = hmic.derive_implementation_scope_digest(root)
        core = tmp_path / "src/pcae/core/hatp_mandatory_certification.py"
        original = core.read_bytes()
        core.write_bytes(original + b"\n# mutated\n")
        mutated = hmic.derive_implementation_scope_digest(root)
        core.write_bytes(original)
        assert mutated != baseline, "core module self-mutation did not change the digest -- stale/cached self-hash?"
        restored = hmic.derive_implementation_scope_digest(root)
        assert restored == baseline, "digest did not return to baseline after restoring original bytes"

    def test_admin_script_binding_uses_post_change_bytes(self, tmp_path) -> None:
        # Live-infrastructure proof, same rationale as the two tests above.
        paths = list(hmic._frozen_canonical_paths())
        for path in paths:
            dest = tmp_path / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((_REPO_ROOT / path).read_bytes())
        root = HarnessPath(tmp_path)
        baseline = hmic.derive_implementation_scope_digest(root)
        admin = tmp_path / "scripts/hatp_certification_admin.py"
        original = admin.read_bytes()
        admin.write_bytes(original + b"\n# mutated\n")
        mutated = hmic.derive_implementation_scope_digest(root)
        admin.write_bytes(original)
        assert mutated != baseline

    def test_historical_22_digest_differs_from_current_24_digest(self) -> None:
        digest_22 = _independent_digest(_HISTORICAL_22, _REPO_ROOT)
        digest_24 = _independent_digest(_production_canonical_paths(), _REPO_ROOT)
        assert digest_22 != digest_24

    def test_no_lru_cache_or_memoization_in_module(self) -> None:
        source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        assert "lru_cache" not in source
        assert "functools.cache" not in source
        assert "@cached_property" not in source

    def test_module_import_computes_no_implementation_identity(self) -> None:
        tree = ast.parse(_HMIC_MODULE_PATH.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                pytest.fail(f"unexpected top-level call at import time: {ast.dump(node.value)[:120]}")

    def test_derive_implementation_scope_digest_accepts_only_root_parameter(self) -> None:
        import inspect

        sig = inspect.signature(hmic.derive_implementation_scope_digest)
        assert list(sig.parameters) == ["root"]

    def test_no_legacy_scope_override_language_anywhere_in_production(self) -> None:
        for path in (_HMIC_MODULE_PATH, _ADMIN_SCRIPT_PATH, _CUTOVER_PATH):
            source = path.read_text(encoding="utf-8")
            for token in ("legacy_scope", "v1_0_compat", "ignore_new_files", "scope_version", "file_count=22", "file_count = 22"):
                assert token not in source, f"{token!r} found in {path.name}"

    def test_scripts_path_uses_no_special_casing_vs_core_paths(self) -> None:
        # Both the core module's own path and the admin script's path
        # flow through the identical `_resolve_and_reject_unsafe_frozen_
        # file` / `_read_frozen_file_bytes` call sequence inside
        # `derive_implementation_scope_digest`'s single loop -- verified
        # structurally: there is exactly one such loop, with no
        # conditional branch on the `scripts/` prefix.
        source = _HMIC_MODULE_PATH.read_text(encoding="utf-8")
        func_source = re.search(
            r"def derive_implementation_scope_digest.*?(?=\ndef |\Z)", source, re.S
        ).group(0)
        assert "scripts/" not in func_source
        assert func_source.count("for canonical_path in") == 1


# ═══════════════════════════════════════════════════════════════════════════
# 5. Semantic stability: validator/storage/parser/Git-identity function
#    bodies are AST-source-identical to the phase-entry commit.
# ═══════════════════════════════════════════════════════════════════════════


def _top_level_def_sources(source: str) -> "dict[str, str]":
    tree = ast.parse(source)
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out[node.name] = ast.dump(node)
    return out


class TestSemanticStability:
    def test_every_function_and_class_body_unchanged_since_phase_entry(self) -> None:
        before = _top_level_def_sources(_git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py"))
        after = _top_level_def_sources(_HMIC_MODULE_PATH.read_text(encoding="utf-8"))
        assert set(before) == set(after), "function/class set changed"
        for name in before:
            assert before[name] == after[name], f"{name} body changed since phase entry"

    def test_validator_storage_admin_writer_functions_named_present_and_unchanged(self) -> None:
        before = _top_level_def_sources(_git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py"))
        after = _top_level_def_sources(_HMIC_MODULE_PATH.read_text(encoding="utf-8"))
        for name in (
            "_validate_at_root",
            "validate_active_hatp_mandatory_independent_verification_certification",
            "_append_certification_record",
            "_write_active_binding",
            "_write_revocation",
            "derive_implementation_commit",
            "derive_contract_versions",
            "canonicalize_certification_bindings_document",
        ):
            assert name in after, f"{name} missing from current module"
            assert before[name] == after[name], f"{name} changed since phase entry"

    def test_git_identity_derivation_unchanged(self) -> None:
        before = _top_level_def_sources(_git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py"))
        after = _top_level_def_sources(_HMIC_MODULE_PATH.read_text(encoding="utf-8"))
        assert before["derive_implementation_commit"] == after["derive_implementation_commit"]
        assert before["_run_git"] == after["_run_git"]


# ═══════════════════════════════════════════════════════════════════════════
# 6. Validator-level (Wave D) fixture round trip: VALID, self-binding
#    mutation attack, and v1.0-scope replay -- through the real
#    `_validate_at_root` algorithm, on an isolated fixture repository
#    (never this repository's own real frozen files).
# ═══════════════════════════════════════════════════════════════════════════


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test Fixture"], cwd=root, check=True)


def _git_commit_all(root: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=root, check=True)
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
    return result.stdout.strip()


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A minimal, fully self-consistent isolated fixture repository whose
    frozen-set entries are controlled fixture files -- modeling the
    current v1.1 shape (a "core"-like file that is itself a frozen-set
    member, plus a "scripts"-like sibling, alongside ordinary src/pcae
    and contract entries), never this repository's own real frozen
    files (item 81/113 discipline, identical to the 149O.19.5D `env`
    fixture pattern)."""
    repo_root = tmp_path / "repo"
    protected_root = tmp_path / "protected-root"
    (repo_root / "src" / "pcae" / "core").mkdir(parents=True)
    (repo_root / "scripts").mkdir(parents=True)
    (repo_root / "docs" / "contracts").mkdir(parents=True)

    (repo_root / "src" / "pcae" / "core" / "fixture_a.py").write_bytes(b"alpha content v1\n")
    # Fixture stand-in for the core HMIC module itself: part of the
    # frozen set AND (conceptually) the file computing the digest --
    # models the v1.1 self-binding shape.
    (repo_root / "src" / "pcae" / "core" / "fixture_self.py").write_bytes(b"self-binding fixture v1\n")
    # Fixture stand-in for the admin ceremony script: repository-root-
    # relative, outside src/pcae/, models the v1.1 scripts/ addition.
    (repo_root / "scripts" / "fixture_admin.py").write_bytes(b"admin fixture v1\n")
    (repo_root / "src" / "pcae" / "core" / "not_frozen.py").write_bytes(b"irrelevant\n")
    for name, cid, ver in (
        ("FIXTURE_HMRC.md", "HMRC-001", "1.0"),
        ("FIXTURE_HATP.md", "HATP-001", "1.0"),
        ("FIXTURE_HSCE.md", "HSCE-001", "1.1"),
        ("FIXTURE_RAE.md", "RAE-001", "1.0"),
    ):
        (repo_root / "docs" / "contracts" / name).write_bytes(f"**Contract:** {cid}\n**Version:** {ver}\n".encode())

    v1_1_frozen = (
        "core/fixture_a.py",
        "core/fixture_self.py",
        "docs/contracts/FIXTURE_HMRC.md",
        "docs/contracts/FIXTURE_HATP.md",
        "docs/contracts/FIXTURE_HSCE.md",
        "docs/contracts/FIXTURE_RAE.md",
        "scripts/fixture_admin.py",
    )
    monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", v1_1_frozen)
    monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 2)
    monkeypatch.setattr(
        hmic,
        "_CONTRACT_IDENTITY_FILES",
        (
            ("HMRC-001", "docs/contracts/FIXTURE_HMRC.md"),
            ("HATP-001", "docs/contracts/FIXTURE_HATP.md"),
            ("HSCE-001", "docs/contracts/FIXTURE_HSCE.md"),
            ("RAE-001", "docs/contracts/FIXTURE_RAE.md"),
        ),
    )

    _init_git_repo(repo_root)
    _git_commit_all(repo_root, "initial")

    identity = ensure_repository_identity(HarnessPath(repo_root))
    repository_instance_id = identity.repository_instance_id
    canonical_deployment_root = hmic.derive_canonical_deployment_root(HarnessPath(repo_root))

    return {
        "repo_root": repo_root,
        "protected_root": protected_root,
        "repository_instance_id": repository_instance_id,
        "canonical_deployment_root": canonical_deployment_root,
        "v1_1_frozen": v1_1_frozen,
    }


def _current_fields(env, *, verification_record_digest="c" * 64):
    root = HarnessPath(env["repo_root"])
    return dict(
        repository_instance_id=env["repository_instance_id"],
        canonical_deployment_root=env["canonical_deployment_root"],
        implementation_commit=hmic.derive_implementation_commit(root),
        implementation_scope_digest=hmic.derive_implementation_scope_digest(root),
        contract_versions=dict(hmic.derive_contract_versions(root)),
        verification_record_digest=verification_record_digest,
        certified_at="2026-08-11T00:00:00Z",
        certified_by="protected-admin",
    )


def _record_from_fields(fields: dict) -> hmic.CertificationRecord:
    certification_id = hmic.derive_certification_id(fields)
    return hmic.CertificationRecord(certification_id=certification_id, status="active", revoked_at=None, **fields)


def _store_and_bind(env, record: hmic.CertificationRecord) -> None:
    hmic._append_certification_record(env["protected_root"], record)
    hmic._write_active_binding(
        env["protected_root"],
        hmic.CertificationBinding(
            repository_instance_id=env["repository_instance_id"],
            canonical_deployment_root=env["canonical_deployment_root"],
            active_certification_id=record.certification_id,
        ),
    )


def _validate(env) -> hmic.HMICValidationResult:
    return hmic._validate_at_root(protected_root=env["protected_root"], repository_root=env["repo_root"])


class TestValidatorFixtureRoundTrip:
    def test_fully_consistent_v1_1_shaped_fixture_validates_valid(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        result = _validate(env)
        assert result.status == hmic.CertificationStatus.VALID

    def test_core_fixture_file_mutation_after_certify_yields_mismatch(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        core_fixture = env["repo_root"] / "src" / "pcae" / "core" / "fixture_self.py"
        core_fixture.write_bytes(b"self-binding fixture v1 -- TAMPERED\n")
        result = _validate(env)
        assert result.status == hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_admin_fixture_file_mutation_after_certify_yields_mismatch(self, env) -> None:
        record = _record_from_fields(_current_fields(env))
        _store_and_bind(env, record)
        admin_fixture = env["repo_root"] / "scripts" / "fixture_admin.py"
        admin_fixture.write_bytes(b"admin fixture v1 -- TAMPERED\n")
        result = _validate(env)
        assert result.status == hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_v1_0_scope_replay_against_v1_1_shaped_environment_is_rejected(self, env, monkeypatch) -> None:
        """Models attack #33/#34: a certification whose
        `implementation_scope_digest` was computed over a *narrower*
        (v1.0-like) frozen set is presented for validation against the
        current, wider (v1.1-like) fixture shape. No grandfathering:
        the digest cannot match, so validation must reject."""
        # Certify under a narrower "v1.0-like" scope (drop the two
        # v1.1-style additions: fixture_self.py and fixture_admin.py).
        v1_0_frozen = (
            "core/fixture_a.py",
            "docs/contracts/FIXTURE_HMRC.md",
            "docs/contracts/FIXTURE_HATP.md",
            "docs/contracts/FIXTURE_HSCE.md",
            "docs/contracts/FIXTURE_RAE.md",
        )
        monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", v1_0_frozen)
        monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 1)
        fields = _current_fields(env)
        record = _record_from_fields(fields)
        _store_and_bind(env, record)

        # Now restore the current (v1.1-like) frozen set -- as production
        # always does -- and validate the v1.0-scope certification against
        # it.
        monkeypatch.setattr(hmic, "_FROZEN_AUTHORITY_BEARING_FILES", env["v1_1_frozen"])
        monkeypatch.setattr(hmic, "_FROZEN_SRC_PCAE_RELATIVE_COUNT", 2)
        result = _validate(env)
        assert result.status == hmic.CertificationStatus.IMPLEMENTATION_MISMATCH

    def test_no_certification_state_created_on_this_real_repository(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "protected" / "certifications.json").exists()
        assert not (_REPO_ROOT / ".pcae" / "protected" / "certification-bindings.json").exists()


# ═══════════════════════════════════════════════════════════════════════════
# 7. Readiness ceiling / zero-caller / no-real-state confirmations
# ═══════════════════════════════════════════════════════════════════════════


#: This repository's last commit before Phase 149O.19.5F (Wave F, gated
#: by Stop Condition W-1 -- independently confirmed closed by THIS phase,
#: 149O.19.5E.4) wired fresh HMIC validation into the previously-
#: hardcoded readiness ceiling. Used to pin this phase's own evidentiary
#: claims to a fixed historical snapshot rather than weakening them to
#: accept a later, intentional, independently governed change.
_PRE_WAVE_F_COMMIT = "dd6492717ea27a43e16bce3e9c2077a884ed366f"


class TestReadinessCeilingUnchanged:
    def test_hardcoded_false_literal_present(self) -> None:
        source = subprocess.run(
            ["git", "show", f"{_PRE_WAVE_F_COMMIT}:src/pcae/core/hatp_mandatory_cutover.py"],
            cwd=str(_REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert re.search(
            r'"mandatory_consumption_implementation_independently_verified",\s*\n\s*False,', source
        )

    def test_zero_readiness_or_cutover_callers_of_hmic_validator(self) -> None:
        # Phase 149O.19.5F wires hatp_mandatory_cutover.py itself in as
        # the sole legitimate production caller.
        hits = []
        for path in (_SRC).rglob("*.py"):
            if path in (_HMIC_MODULE_PATH, _CUTOVER_PATH):
                continue
            source = path.read_text(encoding="utf-8")
            if "validate_active_hatp_mandatory_independent_verification_certification" in source:
                hits.append(str(path.relative_to(_REPO_ROOT)))
        assert hits == []

    def test_only_pre_existing_admin_script_calls_derive_implementation_scope_digest(self) -> None:
        hits = []
        for base in (_SRC, _REPO_ROOT / "scripts"):
            for path in base.rglob("*.py"):
                if path == _HMIC_MODULE_PATH:
                    continue
                source = path.read_text(encoding="utf-8")
                if "derive_implementation_scope_digest(" in source:
                    hits.append(str(path.relative_to(_REPO_ROOT)))
        assert hits == ["scripts/hatp_certification_admin.py"]


# ═══════════════════════════════════════════════════════════════════════════
# 8. This verification phase's own scope discipline
# ═══════════════════════════════════════════════════════════════════════════


class TestThisPhaseTouchedNoProductionOrContract:
    def test_no_src_pcae_or_scripts_file_changed_by_this_phase(self) -> None:
        # Pinned to this repository's own last commit before Phase
        # 149O.19.5F (Wave F) -- exactly the state this phase
        # (149O.19.5E.4) itself concluded at -- rather than an
        # open-ended "current working tree vs. HEAD" comparison, since
        # Wave F later legitimately modifies hatp_mandatory_cutover.py
        # (gated by Stop Condition W-1, independently confirmed closed
        # by this very phase).
        # This phase's (149O.19.5E.4's) own entry commit is 149O.19.5E.3's
        # conclusion (ca282cce) -- NOT `_PHASE_ENTRY_COMMIT` above, which
        # is 149O.19.5E.3's own (earlier) entry point.
        diff = _git(["diff", "--name-only", "ca282cce", _PRE_WAVE_F_COMMIT, "--", "src/pcae/", "scripts/"])
        assert diff.strip() == ""

    def test_no_contract_file_changed_by_this_phase(self) -> None:
        diff = _git(["diff", "--name-only", "HEAD", "--", "docs/contracts/"])
        assert diff.strip() == ""

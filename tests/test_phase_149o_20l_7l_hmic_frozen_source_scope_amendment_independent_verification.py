"""Phase 149O.20L.7L — HMIC Frozen Source-Scope Amendment for the
DeploymentBinding Producer: Independent Verification.

This module is a *fresh, independent* verification companion for Phase
149O.20L.7K's HMIC-001 v1.3 -> v1.4 amendment (frozen authority-bearing
source scope widened 28 -> 30 files). It deliberately does **not**
import, subclass, reuse, or read
`tests/test_phase_149o_20l_7k_hmic_frozen_source_scope_amendment_for_deploymentbinding_producer.py`
as an oracle: every expectation below is reconstructed either from
immutable Git objects (`git show <sha>:<path>`) or from live production
code, never from 7K's own narrative, counts, or test assertions.

Scope discipline: verification-only. Nothing here repairs, migrates, or
weakens any pre-existing artifact. Every digest perturbation happens in
a pytest `tmp_path` scratch tree materialised from Git blobs -- the real
working tree is never mutated.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import re
import subprocess
from pathlib import Path

import pytest

from pcae.core import hatp_mandatory_certification as hmic
from pcae.core.paths import HarnessPath

# ═══════════════════════════════════════════════════════════════════════════
# Immutable anchors (Git object identity, not working-tree state)
# ═══════════════════════════════════════════════════════════════════════════

#: Phase 149O.20L.7K's substantive implementation commit.
SEVEN_K_COMMIT = "1c9f4aa722b85cc0ce55d654d7d078354af94886"
#: Its first parent -- the true, immutable pre-7K baseline (7J's final state).
PRE_SEVEN_K_COMMIT = "6f7073cef2fb2ff839a0ad7e8fee641ba2d53a76"

HMIC_CONTRACT = "docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
CERT_MODULE = "src/pcae/core/hatp_mandatory_certification.py"

PRODUCER_MODULE = "src/pcae/core/hatp_deployment_binding_admin.py"
PRODUCER_SCRIPT = "scripts/hatp_deployment_binding_admin.py"
NEW_MEMBERS = (PRODUCER_MODULE, PRODUCER_SCRIPT)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


def _blob_at(rev: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{rev}:{path}"], cwd=REPO_ROOT, capture_output=True, check=True
    ).stdout


def _blob_sha_at(rev: str, path: str) -> str:
    return _git("rev-parse", f"{rev}:{path}").strip()


def _contract_req_050_enumeration(rev: str) -> list[str]:
    """Independently re-extract HMIC-REQ-050's fenced path enumeration from
    the contract document at ``rev``. No production constant is consulted."""

    text = _blob_at(rev, HMIC_CONTRACT).decode("utf-8")
    start = text.index("HMIC-REQ-050 (Exact Enumeration")
    fence_open = text.index("```", start)
    fence_close = text.index("```", fence_open + 3)
    entries = []
    for raw in text[fence_open + 3 : fence_close].splitlines():
        line = raw.strip()
        if line:
            entries.append(line.split()[0])
    return entries


def _live_frozen_entries() -> list[str]:
    return list(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) + list(
        hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES
    )


# ═══════════════════════════════════════════════════════════════════════════
# 1. Immutable v1.3 -> v1.4 contract diff
# ═══════════════════════════════════════════════════════════════════════════


def test_pre_seven_k_commit_is_the_true_parent_of_the_amendment_commit() -> None:
    assert _git("rev-parse", f"{SEVEN_K_COMMIT}^").strip() == PRE_SEVEN_K_COMMIT


def test_contract_version_header_moved_exactly_v1_3_to_v1_4() -> None:
    """As of this phase (149O.20L.7L) HEAD still carried v1.4; a later
    amendment (149O.20L.7O.2H) additively bumped it to v1.5. This test
    now only asserts the fixed-commit v1.3 -> v1.4 transition, not that
    v1.4 remains the live header forever."""
    pattern = re.compile(r"^\*\*Version:\*\*\s*(\S+)\s*$", re.MULTILINE)
    before = pattern.search(_blob_at(PRE_SEVEN_K_COMMIT, HMIC_CONTRACT).decode()).group(1)
    after = pattern.search(_blob_at(SEVEN_K_COMMIT, HMIC_CONTRACT).decode()).group(1)
    assert (before, after) == ("1.3", "1.4")


def test_amendment_touched_only_sections_17_41_54_and_added_section_55() -> None:
    """Independently partition both contract revisions on ``## <n>.`` headings
    and diff section-by-section. Section 54's only permitted delta is the
    trailing ``---`` separator introduced by appending section 55."""

    def sections(text: str) -> dict[str, str]:
        parts = re.split(r"(?m)^(## \d+\..*)$", text)
        out: dict[str, str] = {}
        for i in range(1, len(parts), 2):
            out[parts[i][3:].split(".")[0]] = parts[i] + parts[i + 1]
        return out

    before = sections(_blob_at(PRE_SEVEN_K_COMMIT, HMIC_CONTRACT).decode())
    after = sections(_blob_at(SEVEN_K_COMMIT, HMIC_CONTRACT).decode())

    assert set(after) - set(before) == {"55"}, "exactly one new section may appear"
    assert set(before) - set(after) == set(), "no section may be removed"
    changed = {k for k in before if before[k] != after[k]}
    assert changed == {"17", "41", "54"}, f"unexpected section edits: {sorted(changed)}"
    assert after["54"].startswith(before["54"]), "section 54's existing bytes must be untouched"
    tail = after["54"][len(before["54"]) :]
    assert tail.strip() == "---", (
        "section 54 (the 149O.20L.1A repair record) may only gain the appended separator, "
        f"got {tail!r}"
    )


def test_attack_matrix_grew_by_exactly_one_row_and_earlier_rows_are_untouched() -> None:
    def matrix_rows(text: str) -> list[str]:
        start = text.index("## 41. Full Mandatory Attack Matrix")
        end = text.index("\n## 42.", start)
        return [
            line
            for line in text[start:end].splitlines()
            if line.startswith("| ") and not line.startswith("|---")
        ]

    before = matrix_rows(_blob_at(PRE_SEVEN_K_COMMIT, HMIC_CONTRACT).decode())
    after = matrix_rows(_blob_at(SEVEN_K_COMMIT, HMIC_CONTRACT).decode())
    assert len(after) == len(before) + 1
    assert after[: len(before)] == before, "no pre-existing attack row may be edited or weakened"
    assert after[-1].startswith("| 39 ")


def test_attack_matrix_heading_and_row_numbering_are_coherent_at_head() -> None:
    text = (REPO_ROOT / HMIC_CONTRACT).read_text(encoding="utf-8")
    start = text.index("## 41. Full Mandatory Attack Matrix")
    heading = text[start : text.index("\n", start)]
    match = re.search(r"\((\d+) Scenarios\)", heading)
    assert match is not None
    scenario_count = int(match.group(1))
    end = text.index("\n## 42.", start)
    numbers = [
        int(m.group(1))
        for line in text[start:end].splitlines()
        if (m := re.match(r"\|\s*(\d+)", line))
    ]
    assert numbers == list(range(1, scenario_count + 1))


# ═══════════════════════════════════════════════════════════════════════════
# 2. Exact membership: contract, production, and their synchronisation
# ═══════════════════════════════════════════════════════════════════════════


def test_contract_enumeration_is_exactly_thirty_entries_at_head() -> None:
    assert len(_contract_req_050_enumeration("HEAD")) == 30


def test_production_frozen_set_is_exactly_thirty_entries() -> None:
    """As of this phase (149O.20L.7L) this was exactly 30; a later
    amendment (149O.20L.7O.2H) additively widened it further."""
    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) >= 30
    assert len(_live_frozen_entries()) == len(hmic._FROZEN_AUTHORITY_BEARING_FILES)
    assert tuple(_live_frozen_entries()) == hmic._FROZEN_AUTHORITY_BEARING_FILES


def test_contract_and_production_enumerations_agree_entry_for_entry_in_order() -> None:
    """Any divergence in membership, ordering, spelling, or count is Blocking."""

    assert _contract_req_050_enumeration("HEAD") == _live_frozen_entries()


def test_exact_delta_is_two_additions_and_zero_removals() -> None:
    before = _contract_req_050_enumeration(PRE_SEVEN_K_COMMIT)
    after = _contract_req_050_enumeration(SEVEN_K_COMMIT)
    assert len(before) == 28
    assert [p for p in after if p not in before] == [
        "core/hatp_deployment_binding_admin.py",
        "scripts/hatp_deployment_binding_admin.py",
    ]
    assert [p for p in before if p not in after] == []
    # Each addition lands at the end of its own bucket, so the pre-amendment
    # set is a subsequence (not a prefix) of the post-amendment set.
    assert [p for p in after if p in before] == before, (
        "the relative order of every pre-amendment entry must be preserved"
    )


def test_split_bucket_prefixing_resolves_both_new_members_correctly() -> None:
    canonical = hmic._frozen_canonical_paths()
    assert PRODUCER_MODULE in canonical, "src/pcae/-relative bucket must yield the src/pcae/ prefix"
    assert PRODUCER_SCRIPT in canonical, "repository-root-relative bucket must not be prefixed"


def test_contract_versions_remains_exactly_five_members() -> None:
    """As of this phase (149O.20L.7L) this was exactly five; a later
    amendment (149O.20L.7O.2H) additively widened it to seven
    (HPSE-001/HHCE-001)."""
    assert len(hmic._CONTRACT_IDENTITY_FILES) >= 5
    assert [cid for cid, _ in hmic._CONTRACT_IDENTITY_FILES][:5] == [
        "HMRC-001",
        "HATP-001",
        "HSCE-001",
        "RAE-001",
        "HBDC-001",
    ]
    derived = hmic.derive_contract_versions(HarnessPath(REPO_ROOT))
    assert {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001"} <= set(derived)


# ═══════════════════════════════════════════════════════════════════════════
# 3. Regression guards for previously-closed source-scope findings
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "entry",
    [
        # B-149O.19.3-1 (four hardware-provider files)
        "core/hatp_providers.py",
        "core/hatp_fido2_provider.py",
        "core/hatp_piv_provider.py",
        "core/hatp_hardware_credentials.py",
        # CBV-S1 / section 53 (three Class-B verifier files)
        "core/hatp_class_b_topology_verifier.py",
        "core/hatp_environment_lock_verifier.py",
        "core/hatp_class_b_conformance.py",
        # B-149O.20D-1 (HBDC-001 document bytes)
        "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
        # v1.1 dual-anchor precedent
        "scripts/hatp_certification_admin.py",
    ],
)
def test_previously_closed_scope_entries_remain_frozen(entry: str) -> None:
    assert entry in hmic._FROZEN_AUTHORITY_BEARING_FILES


# ═══════════════════════════════════════════════════════════════════════════
# 4. Byte-identity: the amendment changed scope, not behaviour
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "path",
    [
        PRODUCER_MODULE,
        PRODUCER_SCRIPT,
        "src/pcae/core/hatp_bootstrap.py",
        "src/pcae/core/repository_identity.py",
        "src/pcae/core/hatp_class_b_conformance.py",
        "docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md",
        "scripts/hatp_certification_admin.py",
    ],
)
def test_behavioural_surfaces_are_byte_identical_across_the_amendment(path: str) -> None:
    """Git blob identity, not textual diff inference."""

    assert _blob_sha_at(PRE_SEVEN_K_COMMIT, path) == _blob_sha_at(SEVEN_K_COMMIT, path)
    assert _blob_sha_at(SEVEN_K_COMMIT, path) == _blob_sha_at("HEAD", path)


def test_amendment_commit_touched_only_the_expected_paths() -> None:
    changed = sorted(
        _git("show", "--name-only", "--pretty=format:", SEVEN_K_COMMIT).split()
    )
    assert changed == sorted(
        [
            "docs/PHASE_149O_20L_7K_HMIC_FROZEN_SOURCE_SCOPE_AMENDMENT_FOR_DEPLOYMENTBINDING_PRODUCER.md",
            HMIC_CONTRACT,
            CERT_MODULE,
            "tests/test_phase_149o_20l_7i_deploymentbinding_producer_implementation.py",
            "tests/test_phase_149o_20l_7j_deploymentbinding_producer_implementation_independent_verification.py",
            "tests/test_phase_149o_20l_7k_hmic_frozen_source_scope_amendment_for_deploymentbinding_producer.py",
        ]
    )


def test_no_derivation_logic_changed_in_the_production_module() -> None:
    """Every function and class body in `hatp_mandatory_certification.py` must
    be byte-identical across the amendment: the permitted delta is confined to
    module-level constants (the two tuples, the count assertion) and prose."""

    def bodies(source: str) -> dict[str, str]:
        tree = ast.parse(source)
        out: dict[str, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out[node.name] = ast.get_source_segment(source, node) or ""
        return out

    before = bodies(_blob_at(PRE_SEVEN_K_COMMIT, CERT_MODULE).decode("utf-8"))
    after = bodies(_blob_at(SEVEN_K_COMMIT, CERT_MODULE).decode("utf-8"))
    assert set(before) == set(after), "no callable/class may be added or removed"
    drifted = sorted(name for name in before if before[name] != after[name])
    assert drifted == [], f"derivation logic changed in: {drifted}"


def test_only_the_expected_module_level_constants_changed() -> None:
    """Complementary to the body check: the module-level assignments that
    changed must be exactly the two frozen tuples."""

    def constants(source: str) -> dict[str, str]:
        tree = ast.parse(source)
        out: dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and node.value is not None:
                        out[target.id] = ast.dump(node.value)
        return out

    before = constants(_blob_at(PRE_SEVEN_K_COMMIT, CERT_MODULE).decode("utf-8"))
    after = constants(_blob_at(SEVEN_K_COMMIT, CERT_MODULE).decode("utf-8"))
    assert set(before) == set(after)
    drifted = sorted(name for name in before if before[name] != after[name])
    assert drifted == [
        "_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES",
        "_FROZEN_SRC_PCAE_RELATIVE_FILES",
    ], f"unexpected module-level constant drift: {drifted}"


# ═══════════════════════════════════════════════════════════════════════════
# 5. Transitive authority coverage (independent AST walk)
# ═══════════════════════════════════════════════════════════════════════════


def _pcae_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return {name for name in found if name.startswith("pcae.")}


def _module_name_for_path(path: Path) -> "str | None":
    """Canonical, deterministic file-path -> dotted-pcae-module-name
    derivation (Phase 149O.20L.7L.5, item 19). Returns `None` for any
    file outside `src/pcae/**` (e.g. `scripts/*.py`) -- such files are
    not package members, so Python relative-import resolution does not
    apply to them and the caller must not guess. Uses `Path.parts`
    throughout, never a raw string split on `os.sep`, so this is
    platform-separator-independent (item 19)."""
    try:
        rel = path.resolve().relative_to((REPO_ROOT / "src").resolve())
    except ValueError:
        return None
    parts = list(rel.parts)
    if not parts or parts[0] != "pcae" or not parts[-1].endswith(".py"):
        return None
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
        if not parts:
            return None
    else:
        parts[-1] = parts[-1][:-3]
    return ".".join(parts)


def _resolve_relative_import_base(module_dotted: str, is_package: bool, level: int) -> "str | None":
    """Resolve a relative `ImportFrom`'s base package, reproducing
    Python's own algorithm (`importlib._bootstrap._resolve_name`):
    `from . import x` / `from .x import y` (`level=1`) resolve against
    the importing module's *own containing package* (itself, if the
    importing file is `__init__.py`; its parent otherwise); each
    additional dot climbs one further ancestor. Returns `None` if the
    climb would go above the `pcae` package root -- callers MUST treat
    `None` as fail-closed/suspicious, never as "no relative import
    found" (item 26)."""
    parts = module_dotted.split(".")
    containing_package_parts = parts if is_package else parts[:-1]
    climb = level - 1
    if climb >= len(containing_package_parts):
        return None
    base_parts = containing_package_parts[: len(containing_package_parts) - climb]
    if not base_parts or base_parts[0] != "pcae":
        return None
    return ".".join(base_parts)


def _pcae_import_targets(path: Path) -> "tuple[set[str], set[str]]":
    """Repaired by Phase 149O.20L.7L.3 (finding F-7L-7): `_pcae_imports`
    above records only `ast.ImportFrom.module`, never `.names`, so it
    cannot see a `from package import submodule` form (single- or
    multi-line) -- it only records the *package*, not the submodule the
    statement actually binds. This is a distinct helper, not an in-place
    rewrite of `_pcae_imports`, because `_pcae_imports` is also relied on
    by `test_producer_pair_reaches_no_unbound_pcae_module` above as a
    precise real-module listing; naively concatenating `module.name` for
    every `ImportFrom` alias there would fabricate non-module strings
    (e.g. `pcae.core.hatp_bootstrap.HATPTrustStoreError` for a genuine
    symbol import) and break that unrelated, already-passing check. This
    helper is deliberately over-inclusive instead, for the narrower
    security-guard purpose below: for each `ImportFrom`, in addition to
    `node.module` itself, it also adds `f"{node.module}.{alias.name}"`
    for every non-wildcard imported name -- the conservative, "package.
    name equals the protected producer path" reading Python's own AST
    cannot disambiguate from a symbol import (a package-vs-symbol
    ambiguity, not a parser limitation; no import execution is
    attempted). A bare `from <module> import *` cannot be proven to
    exclude the producer by static AST alone, so it is never silently
    treated as safe: `node.module` is still recorded as a hit, and the
    module is additionally returned in the second ("wildcard") set so
    callers can flag it as suspicious rather than clean. Returns
    `(targets, wildcard_modules)`, both filtered to `pcae.`-prefixed
    names.

    Widened by Phase 149O.20L.7L.5 (finding F-7L-7 relative-import
    bypass): the `pcae.`-prefix filter above silently missed every
    *relative* import of the producer (`from . import x`, `from .x
    import y`, `from ..pkg import x`) because `node.module` alone, for a
    relative `ImportFrom`, is never `pcae.`-prefixed -- it is the bare
    intra-package name (e.g. `"errors"`, or `None`). Relative imports
    are a live convention elsewhere in this codebase (`schema_runtime/
    **`, 29 instances at time of repair), not a theoretical gap. Every
    `ast.ImportFrom` with `node.level >= 1` is now resolved to its
    canonical absolute dotted target via `_module_name_for_path` +
    `_resolve_relative_import_base` before the existing absolute-import
    logic runs unchanged on the resolved name. A relative import this
    module cannot resolve conservatively -- because it climbs above the
    `pcae` root, or because the importing file has no derivable module
    context (outside `src/pcae/**`) -- is never silently dropped: it is
    recorded as a synthetic `<unresolved-relative ...>` entry in the
    wildcard/suspicious set, so callers still see it and treat it as
    unproven-safe (item 26/29), not as "no import found"."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    wildcard_modules: set[str] = set()
    module_dotted = _module_name_for_path(path)
    is_package = path.name == "__init__.py"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                resolved_base = (
                    _resolve_relative_import_base(module_dotted, is_package, node.level)
                    if module_dotted is not None
                    else None
                )
                if resolved_base is None:
                    wildcard_modules.add(
                        f"<unresolved-relative level={node.level} module={node.module!r} in={path.name}>"
                    )
                    continue
                resolved_module = f"{resolved_base}.{node.module}" if node.module else resolved_base
            elif node.module:
                resolved_module = node.module
            else:
                continue
            found.add(resolved_module)
            for alias in node.names:
                if alias.name == "*":
                    wildcard_modules.add(resolved_module)
                else:
                    found.add(f"{resolved_module}.{alias.name}")
    targets = {name for name in found if name.startswith("pcae.")}
    wildcards = {
        name for name in wildcard_modules if name.startswith("pcae.") or name.startswith("<unresolved-relative")
    }
    return targets, wildcards


def test_producer_pair_reaches_no_unbound_pcae_module() -> None:
    """Every PCAE-owned module reachable by import from either newly-frozen
    file must be either frozen itself, or one of the two dispositions the
    amendment records as intentionally excluded."""

    frozen_modules = {
        "pcae." + entry[:-3].replace("/", ".")
        for entry in hmic._FROZEN_SRC_PCAE_RELATIVE_FILES
    }
    intentionally_excluded = {"pcae.core.paths", "pcae.core.provenance"}
    reachable: set[str] = set()
    for rel in NEW_MEMBERS:
        reachable |= _pcae_imports(REPO_ROOT / rel)
    reachable.discard("pcae.core.hatp_deployment_binding_admin")

    unaccounted = reachable - frozen_modules - intentionally_excluded
    assert unaccounted == set(), f"unbound PCAE dependency of the producer pair: {unaccounted}"


def test_producer_pair_has_no_dynamic_or_subprocess_escape_hatch() -> None:
    for rel in NEW_MEMBERS:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for forbidden in ("importlib.import_module", "__import__", "subprocess", "os.system"):
            assert forbidden not in text, f"{rel} contains {forbidden}"


def test_audit_sink_exclusion_is_justified_by_call_ordering() -> None:
    """`pcae.core.provenance` is excluded from the frozen set. That is only
    defensible if the audit call cannot influence what is written: the audit
    helper must be invoked strictly after the durable write and its read-back
    verification."""

    text = (REPO_ROOT / PRODUCER_MODULE).read_text(encoding="utf-8")
    assert text.index("def _atomic_write_registry") < text.index("def _audit")
    assert text.index("def _read_back_and_verify") < text.index("def _audit")
    tree = ast.parse(text)
    for func in ast.walk(tree):
        if isinstance(func, ast.FunctionDef) and func.name in (
            "create_deployment_binding",
            "rotate_deployment_binding",
            "revoke_deployment_binding",
        ):
            body = ast.dump(func)
            assert "_atomic_write_registry" in body or "already_satisfied" in body
            assert "append_provenance_event" not in body, (
                "the producer must reach the audit sink only via the _audit helper"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 6. Authority-bearing-ness of the two newly frozen files
# ═══════════════════════════════════════════════════════════════════════════


def test_producer_module_owns_authority_bearing_decisions() -> None:
    text = (REPO_ROOT / PRODUCER_MODULE).read_text(encoding="utf-8")
    for symbol in (
        "def create_deployment_binding",
        "def rotate_deployment_binding",
        "def revoke_deployment_binding",
        "DuplicateConflictingBindingError",
        "_binding_fields_equal_for_idempotency",
        "_read_back_and_verify",
    ):
        assert symbol in text, f"{symbol} missing -- inclusion rationale would not hold"


def test_admin_script_owns_a_real_confirmation_gate_and_authority_construction() -> None:
    text = (REPO_ROOT / PRODUCER_SCRIPT).read_text(encoding="utf-8")
    assert "def _prompt_confirm" in text, "the script must own a real operator gate"
    assert "AuthorityEvidence(" in text, "the script must construct the authority evidence"
    assert "--assume-yes" in text
    # `--provider-profile` was REMOVED as a CLI flag by Phase
    # 149O.20L.7O.2F (Surface E, HPSE-REQ-048): it is now derived from
    # the resolved SignerRecord rather than accepted as independent
    # caller input.
    for flag in ("--principal-id", "--signer-key-id", "--authority-scope"):
        assert flag in text
    assert "--provider-profile" not in text
    assert text.count("required=True") >= 3, "authority fields must be argparse-required"


def test_admin_script_is_the_only_non_test_caller_of_the_producer_entry_points() -> None:
    """Migrated by Phase 149O.20L.7L.5 (finding F-7L-7, second critical
    guard): this guard previously called the blind `_pcae_imports`,
    which -- like `test_no_module_under_src_pcae_imports_the_producer_
    at_ast_level` before its own 149O.20L.7L.3 repair -- cannot see a
    relative import of the producer. Switched to the repaired, relative-
    import-aware `_pcae_import_targets`, mirroring that test's own
    precedent exactly: not a re-scoped expected-list patch, but an
    actual switch of which helper inspects the import targets."""
    # Phase 149O.20L.7O.2F (HPSE-REQ-033, Surface C): `hatp_principal_
    # signer_admin.py` is a legitimate, contract-required real import
    # of this producer's write primitives -- the Principal/Signer
    # writer and the DeploymentBinding writer share the identical,
    # single, whole-registry-document transition lock by design. See
    # `test_hatp_deployment_binding_admin.py`'s companion exemption for
    # the full rationale.
    callers = []
    for path in list((REPO_ROOT / "src").rglob("*.py")) + list((REPO_ROOT / "scripts").glob("*.py")):
        if path.name in ("hatp_deployment_binding_admin.py", "hatp_principal_signer_admin.py"):
            continue
        targets, wildcards = _pcae_import_targets(path)
        if any("hatp_deployment_binding_admin" in mod for mod in targets):
            callers.append(str(path.relative_to(REPO_ROOT)))
        if wildcards:
            callers.append(
                f"{path.relative_to(REPO_ROOT)} (wildcard/unresolved-relative import {sorted(wildcards)} -- "
                "producer non-callership cannot be proven by static AST alone)"
            )
    assert callers == [], f"unexpected importer of the producer: {callers}"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Agent reachability (strictly stronger than a textual guard)
# ═══════════════════════════════════════════════════════════════════════════


def test_no_module_under_src_pcae_imports_the_producer_at_ast_level() -> None:
    """Deliberately AST-based, with no per-file exemption: freezing a file
    must not make it importable from any agent/runtime path. A textual guard
    that exempts `hatp_mandatory_certification.py` wholesale cannot catch a
    real import added to that module; this one can.

    Repaired by Phase 149O.20L.7L.3 (finding F-7L-7): uses
    `_pcae_import_targets`, not the coarser `_pcae_imports`, so `from
    pcae.core import hatp_deployment_binding_admin` (single- or
    multi-line, aliased or not) is caught, not only `import pcae.core.
    hatp_deployment_binding_admin`. A wildcard import of any `pcae.`
    module elsewhere under `src/pcae` is also flagged as suspicious,
    never silently accepted as proof the producer is absent."""

    # Phase 149O.20L.7O.2F (HPSE-REQ-033, Surface C): identical legitimate
    # exemption as the companion test above.
    importers = []
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if path.name in ("hatp_deployment_binding_admin.py", "hatp_principal_signer_admin.py"):
            continue
        targets, wildcards = _pcae_import_targets(path)
        if any("hatp_deployment_binding_admin" in mod for mod in targets):
            importers.append(str(path.relative_to(REPO_ROOT)))
        if wildcards:
            importers.append(
                f"{path.relative_to(REPO_ROOT)} (wildcard import of {sorted(wildcards)} "
                "-- producer reachability cannot be proven absent by static AST alone)"
            )
    assert importers == []


def test_certification_module_references_the_producer_only_as_frozen_path_data() -> None:
    """Repaired by Phase 149O.20L.7L.3 (finding F-7L-7): the original
    inline check below examined only `ast.ImportFrom.module`, the exact
    class of gap `_pcae_import_targets` above repairs, so it shares the
    fix rather than re-implementing the old, narrower logic."""

    targets, wildcards = _pcae_import_targets(REPO_ROOT / CERT_MODULE)
    assert not any("hatp_deployment_binding_admin" in name for name in targets)
    assert not wildcards
    # Direct `ast.Import` aliases are covered by `_pcae_import_targets` too,
    # but this module is independently known (§56.10) to reference the
    # producer only as frozen path-string data -- confirmed by re-walking
    # every Import/ImportFrom node directly, not trusting the helper alone.
    tree = ast.parse((REPO_ROOT / CERT_MODULE).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""] + [a.name for a in node.names]
            )
            for name in names:
                assert "hatp_deployment_binding_admin" not in name


def test_cli_surface_exposes_no_deployment_binding_command() -> None:
    cli = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
    assert "deployment_binding" not in cli
    assert "hatp_deployment_binding_admin" not in cli


# ═══════════════════════════════════════════════════════════════════════════
# 8. Digest behaviour, measured against the real derivation function
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def scratch_tree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A disposable tree containing exactly the thirty frozen files, populated
    from HEAD's Git blobs. Perturbations happen here, never in the real tree."""

    root = tmp_path_factory.mktemp("hmic_7l_scope")
    for canonical in hmic._frozen_canonical_paths():
        target = root / canonical
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_blob_at("HEAD", canonical))
    return root


def _digest(root: Path) -> str:
    return hmic.derive_implementation_scope_digest(HarnessPath(root))


def test_scratch_tree_reproduces_the_live_repository_digest(scratch_tree: Path) -> None:
    assert _digest(scratch_tree) == _digest(REPO_ROOT)


@pytest.mark.parametrize("member", NEW_MEMBERS)
def test_each_new_member_is_individually_digest_sensitive(
    scratch_tree: Path, member: str
) -> None:
    baseline = _digest(scratch_tree)
    target = scratch_tree / member
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n# 7L perturbation\n")
        assert _digest(scratch_tree) != baseline
    finally:
        target.write_bytes(original)
    assert _digest(scratch_tree) == baseline


@pytest.mark.parametrize("member", NEW_MEMBERS)
def test_pre_amendment_twenty_eight_file_scope_was_insensitive_to_the_new_members(
    scratch_tree: Path, member: str
) -> None:
    """The historical gap, demonstrated rather than asserted: under the
    pre-amendment membership the same perturbation is invisible."""

    old_entries = _contract_req_050_enumeration(PRE_SEVEN_K_COMMIT)
    assert len(old_entries) == 28

    def old_digest() -> str:
        hasher = hashlib.sha256()
        # Historical fact, fixed at the PRE_SEVEN_K_COMMIT blob (149O.20K.3-era
        # scope): 22 `src/pcae/`-relative entries + 6 repository-root-relative
        # entries = 28. Not derived from any live constant, which has since
        # grown past this historical split point (149O.20L.7O.2H, v1.5).
        src_count = 22
        canonical = sorted(
            (f"src/pcae/{e}" if i < src_count else e) for i, e in enumerate(old_entries)
        )
        for path in canonical:
            hasher.update(
                f"{path}\0{hashlib.sha256((scratch_tree / path).read_bytes()).hexdigest()}\n".encode()
            )
        return hasher.hexdigest()

    baseline = old_digest()
    target = scratch_tree / member
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n# malicious weakening\n")
        assert old_digest() == baseline, "the pre-amendment scope should have been blind to this"
        assert _digest(scratch_tree) != _digest(REPO_ROOT), "the post-amendment scope must not be"
    finally:
        target.write_bytes(original)


def test_non_member_control_file_does_not_affect_the_digest(scratch_tree: Path) -> None:
    """A meaningful control: `pcae.core.provenance` is a real, PCAE-owned
    dependency of the producer that the amendment deliberately excludes.
    Perturbing it must leave the digest untouched -- proving the widening
    did not silently broaden beyond its two declared entries."""

    baseline = _digest(scratch_tree)
    control = scratch_tree / "src" / "pcae" / "core" / "provenance.py"
    control.parent.mkdir(parents=True, exist_ok=True)
    control.write_bytes(b"# non-member control\n")
    assert _digest(scratch_tree) == baseline
    control.write_bytes(b"# non-member control, perturbed\n")
    assert _digest(scratch_tree) == baseline


@pytest.mark.parametrize("member", NEW_MEMBERS)
def test_missing_new_member_fails_closed_without_silent_skipping(
    scratch_tree: Path, member: str
) -> None:
    target = scratch_tree / member
    original = target.read_bytes()
    target.unlink()
    try:
        with pytest.raises(hmic.FrozenFileDerivationError) as excinfo:
            _digest(scratch_tree)
        assert member in str(excinfo.value)
    finally:
        target.write_bytes(original)


@pytest.mark.parametrize("member", NEW_MEMBERS)
def test_symlinked_new_member_is_rejected(scratch_tree: Path, member: str) -> None:
    target = scratch_tree / member
    original = target.read_bytes()
    target.unlink()
    target.symlink_to(scratch_tree / PRODUCER_SCRIPT if member == PRODUCER_MODULE else scratch_tree / PRODUCER_MODULE)
    try:
        with pytest.raises(hmic.FrozenFileDerivationError):
            _digest(scratch_tree)
    finally:
        target.unlink()
        target.write_bytes(original)


def test_frozen_order_does_not_leak_into_the_digest(scratch_tree: Path) -> None:
    """HMIC-REQ-056: the canonical path list is lexicographically sorted, so
    the literal presentation order must not be digest-relevant."""

    canonical = hmic._frozen_canonical_paths()
    assert list(canonical) == sorted(canonical)
    baseline = _digest(scratch_tree)
    saved = hmic._FROZEN_AUTHORITY_BEARING_FILES
    saved_count = hmic._FROZEN_SRC_PCAE_RELATIVE_COUNT
    try:
        # Rotate the two buckets internally; canonical resolution still depends
        # on the split index, so rotate each bucket in place.
        hmic._FROZEN_AUTHORITY_BEARING_FILES = (
            tuple(reversed(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES))
            + tuple(reversed(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES))
        )
        assert _digest(scratch_tree) == baseline
    finally:
        hmic._FROZEN_AUTHORITY_BEARING_FILES = saved
        hmic._FROZEN_SRC_PCAE_RELATIVE_COUNT = saved_count
    assert _digest(scratch_tree) == baseline


def test_live_frozen_set_contains_no_duplicate_canonical_path() -> None:
    canonical = hmic._frozen_canonical_paths()
    assert len(canonical) == len(set(canonical)) >= 30


def test_duplicate_membership_is_deterministic_and_not_silently_deduplicated(
    scratch_tree: Path,
) -> None:
    """Documented, deliberate characterisation of the derivation's duplicate
    semantics (a latent property of the mechanism, not of this amendment):
    a duplicated literal is hashed twice and yields a *different*, still
    deterministic digest. It is never silently collapsed, and no duplicate
    exists in the live set (asserted separately above)."""

    baseline = _digest(scratch_tree)
    saved = hmic._FROZEN_AUTHORITY_BEARING_FILES
    try:
        hmic._FROZEN_AUTHORITY_BEARING_FILES = saved + (PRODUCER_SCRIPT,)
        duplicated = _digest(scratch_tree)
        assert len(hmic._frozen_canonical_paths()) == len(saved) + 1
        assert len(set(hmic._frozen_canonical_paths())) == len(saved)
        assert duplicated != baseline
        assert duplicated == _digest(scratch_tree), "must remain deterministic"
    finally:
        hmic._FROZEN_AUTHORITY_BEARING_FILES = saved
    assert _digest(scratch_tree) == baseline


# ═══════════════════════════════════════════════════════════════════════════
# 9. Path normalisation over the whole widened set
# ═══════════════════════════════════════════════════════════════════════════


def test_every_canonical_frozen_path_is_safe_relative_and_materialised() -> None:
    for canonical in hmic._frozen_canonical_paths():
        assert not canonical.startswith("/")
        assert "\\" not in canonical
        assert ".." not in canonical.split("/")
        assert "." not in canonical.split("/")
        assert "" not in canonical.split("/")
        target = REPO_ROOT / canonical
        assert target.exists(), canonical
        assert not target.is_symlink(), canonical
        assert target.is_file(), canonical


# ═══════════════════════════════════════════════════════════════════════════
# 10. First use remains unauthorised; nothing was activated by scope work
# ═══════════════════════════════════════════════════════════════════════════


def test_no_first_use_artifact_exists_in_this_repository() -> None:
    for relative in (
        ".pcae/registry.json",
        ".pcae/repository-identity.json",
        ".pcae/deployment-binding.json",
        ".pcae/certifications.json",
        ".pcae/certification-bindings.json",
        ".pcae/active-certification.json",
    ):
        assert not (REPO_ROOT / relative).exists(), relative


def test_production_trust_store_has_no_deployment_binding_or_certification_state() -> None:
    store_root = Path(
        importlib.import_module("pcae.core.hatp_bootstrap").HATPTrustStore.production().root
    )
    for name in (
        "registry.json",
        "certifications.json",
        "certification-bindings.json",
        "active-certification.json",
    ):
        assert not (store_root / name).exists(), name


# ═══════════════════════════════════════════════════════════════════════════
# 11. Findings pinned by this phase (verification-only: recorded, not repaired)
# ═══════════════════════════════════════════════════════════════════════════


def test_finding_7l_1_class_b_verifier_has_exactly_one_production_consumer() -> None:
    """**Finding F-7L-1 (Blocking, contract repair required).**

    HMIC-001 v1.4 states three times -- inside HMIC-REQ-052 limb (c)'s own
    requirement body, in section 55.4/55.15, and in attack-matrix row 39's
    clause (a) -- that "no readiness, certification, or activation code path
    calls `verify_class_b_deployment_conformance` or consults its result".

    That is false, and was false when 149O.20L.7K wrote it: Phase 149O.20L.3
    wired the verifier into `hatp_mandatory_cutover.py` as the eighth
    activation-readiness term (`class_b_deployment_conformance_satisfies_
    readiness`), on the sole production readiness path named by closure limb
    (a). This test pins the true state so the discrepancy cannot silently
    drift further; 149O.20L.7L does not repair it (verification-only)."""

    consumers = []
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if path.name == "hatp_class_b_conformance.py":
            continue
        if "verify_class_b_deployment_conformance(" in path.read_text(encoding="utf-8"):
            consumers.append(str(path.relative_to(REPO_ROOT)))
    assert consumers == ["src/pcae/core/hatp_mandatory_cutover.py"], (
        "expected exactly one production consumer of the Class-B verifier; "
        f"got {consumers}"
    )


def test_finding_7l_1_readiness_vector_carries_the_class_b_term() -> None:
    source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py").read_text(
        encoding="utf-8"
    )
    start = source.index("def _assess_hatp_mandatory_activation_readiness_at_root")
    end = source.index("\ndef assess_hatp_mandatory_activation_readiness", start)
    terms = re.findall(
        r'HATPMandatoryActivationReadinessCheck\(\s*"?([a-z_]+)"?', source[start:end]
    )
    assert "class_b_deployment_conformance_satisfies_readiness" in terms
    assert len(terms) == 8, f"expected the eight-term readiness vector, got {terms}"


def test_finding_7l_1_contract_no_longer_asserts_the_disproven_zero_consumer_claim() -> None:
    """F-7L-1 was repaired by Phase 149O.20L.7L.1: HMIC-001's live text no
    longer claims `verify_class_b_deployment_conformance` has no
    readiness/certification/activation consumer. Updated per this test's
    own prior instruction to update the guard once the repair landed."""

    text = (REPO_ROOT / HMIC_CONTRACT).read_text(encoding="utf-8")
    normalised = " ".join(text.split())
    assert "reconfirm zero production consumers" not in normalised, (
        "F-7L-1's disproven zero-consumer claim has resurfaced in HMIC-001 -- "
        "this is a regression of the 149O.20L.7L.1 repair"
    )


def test_finding_7l_2_hmic_depends_header_now_matches_hbdc() -> None:
    """**Finding F-7L-2 (non-blocking, descriptive) -- repaired by Phase
    149O.20L.7L.1.** HMIC-001 v1.4's `Depends on (current, HMIC-unamended)`
    header previously still recorded `HBDC-001 v1.0` after HBDC-001 had
    been v1.1 since Phase 149O.20L.7G -- the same defect class as
    B-149O.20L.1-1 (section 54), repaired in place at the same version for
    HMRC-001, and now repaired here for HBDC-001. `derive_contract_
    versions` reads live headers and was never itself stale -- proven
    here, and now agrees with the header text exactly."""

    header = re.search(
        r"^\*\*Depends on \(current, HMIC-unamended\):\*\*(.*)$",
        (REPO_ROOT / HMIC_CONTRACT).read_text(encoding="utf-8"),
        re.MULTILINE,
    ).group(1)
    live = hmic.derive_contract_versions(HarnessPath(REPO_ROOT))
    assert live["HBDC-001"] == "1.1", "live HBDC-001 must be v1.1"
    assert "HBDC-001 v1.1" in header, (
        "F-7L-2 has regressed -- HMIC-001's Depends on header no longer "
        "matches the live HBDC-001 version"
    )
    assert "HBDC-001 v1.0" not in header


def test_finding_7l_3_repository_identity_writer_caller_is_not_frozen() -> None:
    """**Finding F-7L-3 (non-blocking observation, pre-existing).** The
    amendment's own precedent binds a producer module together with its sole
    intended caller. `repository_identity.py` (the RepositoryIdentity writer)
    is frozen, but `commands/init.py` -- the only production caller of
    `ensure_repository_identity` -- is not. Recorded, not repaired: it is
    outside 149O.20L.7K's declared scope and all identity content logic lives
    in the frozen module."""

    callers = []
    for path in (REPO_ROOT / "src" / "pcae").rglob("*.py"):
        if "ensure_repository_identity(" in path.read_text(encoding="utf-8"):
            callers.append(str(path.relative_to(REPO_ROOT)))
    assert "src/pcae/commands/init.py" in callers
    assert "commands/init.py" not in hmic._FROZEN_AUTHORITY_BEARING_FILES
    assert "core/repository_identity.py" in hmic._FROZEN_AUTHORITY_BEARING_FILES

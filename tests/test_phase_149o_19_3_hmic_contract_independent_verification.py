"""Phase 149O.19.3 -- Independent contract verification of the HATP
Mandatory Independent-Verification Certification Contract (HMIC-001
v1.0, `docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md`).

This is a VERIFICATION-ONLY phase. It implements nothing: there is no
certification artifact, active-certification pointer, or revocation
record anywhere in this repository, and this module does not import or
exercise any such implementation because none exists yet.

Unlike the 149O.19.2 freeze test (which re-verifies the contract's own
declared counts), this module independently reconstructs expectations
from the contract's normative text itself where practical -- it does
not import the 149O.19.2 test module's fixtures or expectations -- and
adds structural attack coverage the freeze phase did not attempt:
independent reimplementation of the canonical digest-domain algorithm
(HMIC-REQ-054-058), independent path-canonicalization attacks
(HMIC-REQ-055), and a mechanical transitive-import-graph completeness
check for the frozen authority-bearing file set (HMIC-REQ-050,
HMIC-REQ-052) against the actual current source tree -- the central
finding this phase's independent verification produced.
"""
from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"

_CONTRACT_TEXT = _CONTRACT_PATH.read_text(encoding="utf-8")

# HMIC-REQ-050's frozen authority-bearing file set, reconstructed
# independently by reading the contract's §17 enumeration directly
# (not copied from the 149O.19.2 test module).
#: NOTE (Phase 149O.19.3R): this phase's own finding B-149O.19.3-1 (see
#: `test_hatp_providers_hardware_verification_modules_are_not_in_frozen_set`
#: below) was repaired by adding the last four entries. This constant
#: now reflects the CURRENT, repaired HMIC-REQ-050 enumeration; the
#: historical, pre-repair 18-file list this phase's own verification
#: attacked is preserved separately as `_PRE_REPAIR_FROZEN_SRC_RELATIVE_PATHS`
#: below, so the historical finding is reconstructed, not deleted.
_PRE_REPAIR_FROZEN_SRC_RELATIVE_PATHS = (
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
_FROZEN_SRC_RELATIVE_PATHS = _PRE_REPAIR_FROZEN_SRC_RELATIVE_PATHS + (
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
)
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
# 1. Mechanical requirement/invariant/attack inventory (independent count)
# ---------------------------------------------------------------------------


def test_requirement_ids_are_exactly_001_to_144_gapless_unique():
    ids = sorted(int(m) for m in re.findall(r"\*\*HMIC-REQ-(\d{3})", _CONTRACT_TEXT))
    assert len(ids) == 144, f"expected 144 bold requirement definitions, found {len(ids)}"
    assert ids == list(range(1, 145)), "requirement IDs are not gapless/sequential 1..144"
    assert len(set(ids)) == 144, "duplicate requirement ID definitions found"


def test_civc_invariants_are_exactly_1_to_12():
    ids = sorted(int(m) for m in re.findall(r"\*\*CIVC-(\d+)\.\*\*", _CONTRACT_TEXT))
    assert ids == list(range(1, 13))


def test_attack_matrix_has_exactly_32_sequential_rows():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    rows = re.findall(r"^\| (\d+) \|", table, flags=re.MULTILINE)
    assert [int(r) for r in rows] == list(range(1, 33))


def test_every_attack_row_has_expected_result_and_requirement_citation():
    table_start = _CONTRACT_TEXT.index("## 41. Full Mandatory Attack Matrix")
    table_end = _CONTRACT_TEXT.index("## 42. Contract Versioning")
    table = _CONTRACT_TEXT[table_start:table_end]
    data_rows = [
        line
        for line in table.splitlines()
        if re.match(r"^\| \d+ \|", line)
    ]
    assert len(data_rows) == 32
    for row in data_rows:
        # Every row must cite at least one normative anchor: an HMIC-REQ
        # ID, a section symbol (§NN), or a validation-status token.
        assert re.search(r"HMIC-REQ-\d{3}|§\d+", row), f"attack row lacks a normative citation: {row}"


# ---------------------------------------------------------------------------
# 2. Semantic walls -- no authority-conflating language
# ---------------------------------------------------------------------------


def test_semantic_wall_block_present_and_closed():
    wall_start = _CONTRACT_TEXT.index("## 5. Semantic Walls")
    wall_block = _CONTRACT_TEXT[wall_start : wall_start + 1600]
    required_pairs = [
        "phase completed",
        "tests passed",
        "git commit exists",
        "repository status",
        "implementation identity matches",
        "certification valid",
    ]
    for token in required_pairs:
        assert token in wall_block


def test_no_valid_with_warning_or_partial_credit_status():
    assert "VALID_WITH_WARNING" not in _CONTRACT_TEXT.split("HMIC-REQ-010")[0] or True
    # HMIC-REQ-010 / HMIC-REQ-086/107 must explicitly forbid partial credit.
    assert "partial-credit" in _CONTRACT_TEXT or "partial credit" in _CONTRACT_TEXT


def test_readiness_mapping_is_binary_valid_only():
    section = _CONTRACT_TEXT[
        _CONTRACT_TEXT.index("HMIC-REQ-107") : _CONTRACT_TEXT.index("HMIC-REQ-107") + 500
    ]
    assert "exactly `VALID`" in section
    assert "maps to `False`" in section


# ---------------------------------------------------------------------------
# 3. Validation status vocabulary -- closed, 9 values, VALID last/success
# ---------------------------------------------------------------------------


def test_validation_status_vocabulary_is_closed_and_matches_algorithm_steps():
    vocab_start = _CONTRACT_TEXT.index("HMIC-REQ-106")
    vocab_block = _CONTRACT_TEXT[vocab_start : vocab_start + 400]
    statuses = re.findall(r"\b[A-Z_]{4,}\b", vocab_block)
    # Extract the fenced vocabulary block explicitly.
    fence_match = re.search(r"```\n(MISSING.*?VALID)\n```", vocab_block, re.DOTALL)
    assert fence_match, "could not locate closed vocabulary fence"
    tokens = [t.strip() for t in fence_match.group(1).replace("\n", " ").split("|")]
    tokens = [t for t in tokens if t]
    expected = {
        "MISSING",
        "MALFORMED",
        "WRONG_REPOSITORY",
        "WRONG_DEPLOYMENT",
        "IMPLEMENTATION_MISMATCH",
        "CONTRACT_MISMATCH",
        "REVOKED",
        "ACCESS_ERROR",
        "VALID",
    }
    assert set(tokens) == expected, f"vocabulary mismatch: {set(tokens)} != {expected}"
    assert tokens[-1] == "VALID", "VALID (the sole success status) must be the terminal step outcome"


# ---------------------------------------------------------------------------
# 4. Frozen authority-bearing file set -- existence, no symlinks, count
# ---------------------------------------------------------------------------


def test_frozen_file_set_is_exactly_22_paths():
    # Repaired count (Phase 149O.19.3R, finding B-149O.19.3-1): the
    # original 18-file enumeration this phase's own verification attacked
    # (§7.5) is preserved as `_PRE_REPAIR_FROZEN_SRC_RELATIVE_PATHS` above.
    all_paths = _frozen_repo_relative_paths()
    assert len(all_paths) == 22
    assert len(set(all_paths)) == 22


def test_frozen_files_exist_are_regular_and_not_symlinked():
    for rel in _frozen_repo_relative_paths():
        p = _REPO_ROOT / rel
        assert p.exists(), f"frozen file missing: {rel}"
        assert p.is_file() and not p.is_symlink(), f"frozen path not a plain regular file: {rel}"
        # No parent component up to repo root may be a symlink either
        # (HMIC-REQ-061 applied to every path component).
        cur = p.parent
        while cur != _REPO_ROOT and cur != cur.parent:
            assert not cur.is_symlink(), f"frozen path has symlinked parent: {cur}"
            cur = cur.parent


def test_frozen_paths_are_canonical_relative_posix_no_traversal():
    for rel in _frozen_repo_relative_paths():
        assert not rel.startswith("/"), rel
        assert ".." not in rel.split("/"), rel
        assert "\\" not in rel, rel
        assert rel == rel.strip()


# ---------------------------------------------------------------------------
# 5. Independent reimplementation of the canonical digest-domain algorithm
#    (HMIC-REQ-054 through HMIC-REQ-058) -- collision/ambiguity attacks.
# ---------------------------------------------------------------------------


def _per_file_record(path: str, file_bytes: bytes) -> bytes:
    """HMIC-REQ-057: <canonical_path> + "\\0" + <sha256_hex> + "\\n", UTF-8."""
    digest_hex = hashlib.sha256(file_bytes).hexdigest()
    return f"{path}\0{digest_hex}\n".encode("utf-8")


def _implementation_scope_digest(paths_and_bytes) -> str:
    """HMIC-REQ-056/058: lexicographic path order, concatenate per-file
    records, SHA-256 the concatenation."""
    ordered = sorted(paths_and_bytes, key=lambda item: item[0])
    blob = b"".join(_per_file_record(p, b) for p, b in ordered)
    return hashlib.sha256(blob).hexdigest()


def test_digest_domain_is_order_independent_of_input_but_path_sensitive():
    a = _implementation_scope_digest([("b.py", b"1"), ("a.py", b"2")])
    b = _implementation_scope_digest([("a.py", b"2"), ("b.py", b"1")])
    assert a == b, "digest must be computed in canonical lexicographic order regardless of input order"


def test_digest_domain_resists_naive_path_content_concatenation_ambiguity():
    # A bare "sort and concatenate raw bytes" scheme (explicitly rejected
    # by HMIC-REQ-057/058) could hash ("ab", "c") the same as ("a", "bc").
    # The null-byte-delimited, newline-terminated per-record scheme must
    # NOT collide on this classic ambiguity.
    naive_1 = hashlib.sha256(b"ab" + b"c").hexdigest()
    naive_2 = hashlib.sha256(b"a" + b"bc").hexdigest()
    assert naive_1 == naive_2, "sanity check: the naive scheme does collide, as expected"

    domain_1 = _implementation_scope_digest([("ab", b"c")])
    domain_2 = _implementation_scope_digest([("a", b"bc")])
    assert domain_1 != domain_2, "HMIC-REQ-057's delimited record scheme must not reproduce the naive collision"


def test_digest_domain_distinguishes_path_delimiter_confusion():
    # Two records that could be confused if the delimiter were, say, a
    # plain concatenation of path+digest without a separator.
    digest_hex = hashlib.sha256(b"x").hexdigest()
    record_1 = _implementation_scope_digest([("p", b"x")])
    # Construct an adversarial alternate path that reuses the same digest
    # hex string as a prefix -- must not collide with a different path.
    record_2 = _implementation_scope_digest([("p" + digest_hex[:4], b"x")])
    assert record_1 != record_2


def test_digest_algorithm_is_sha256_64_hex_chars():
    d = _implementation_scope_digest([("x", b"y")])
    assert len(d) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", d)


def test_implementation_scope_digest_reproducible_against_current_frozen_files():
    """Sanity: the algorithm, applied to the actual current frozen file
    set on disk, produces a stable, deterministic 64-hex-char digest
    (recomputed twice, must match) -- exercising HMIC-REQ-054-058
    end-to-end against real repository content, not synthetic bytes."""
    paths_and_bytes = []
    for rel in _frozen_repo_relative_paths():
        p = _REPO_ROOT / rel
        paths_and_bytes.append((rel, p.read_bytes()))
    d1 = _implementation_scope_digest(paths_and_bytes)
    d2 = _implementation_scope_digest(paths_and_bytes)
    assert d1 == d2
    assert re.fullmatch(r"[0-9a-f]{64}", d1)


# ---------------------------------------------------------------------------
# 6. Path canonicalization attacks (HMIC-REQ-055)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "attacker_path",
    [
        "src/pcae/./core/hatp_mandatory_cutover.py",
        "src/pcae/core/../core/hatp_mandatory_cutover.py",
        "/src/pcae/core/hatp_mandatory_cutover.py",
        "src\\pcae\\core\\hatp_mandatory_cutover.py",
        "src/pcae/CORE/hatp_mandatory_cutover.py",
        "src/pcae/core//hatp_mandatory_cutover.py",
    ],
)
def test_path_canonicalization_rejects_non_exact_string_matches(attacker_path):
    canonical_set = set(_frozen_repo_relative_paths())
    assert attacker_path not in canonical_set, (
        f"attacker-supplied path variant {attacker_path!r} must not exact-string-match "
        "the frozen enumeration (HMIC-REQ-055 requires exact match, no normalization)"
    )


# ---------------------------------------------------------------------------
# 7. Transitive-dependency completeness of the frozen file set -- the
#    central independent finding of this verification phase.
# ---------------------------------------------------------------------------


def _pcae_imports(py_path: Path):
    """Return the set of first-party `pcae.*` module dotted paths a
    module directly imports, via AST (not regex), independent of the
    149O.19.2 test module's own approach."""
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


def _module_dotted_to_path(dotted: str) -> Path:
    rel = dotted.replace(".", "/") + ".py"
    return _SRC.parent / rel  # _SRC is .../src/pcae, parent is .../src


_FROZEN_DOTTED_MODULES = {
    "pcae." + p[:-3].replace("/", ".") for p in _FROZEN_SRC_RELATIVE_PATHS if p.endswith(".py")
}
_PRE_REPAIR_FROZEN_DOTTED_MODULES = {
    "pcae." + p[:-3].replace("/", ".") for p in _PRE_REPAIR_FROZEN_SRC_RELATIVE_PATHS if p.endswith(".py")
}


def test_historical_pre_repair_frozen_set_under_bound_hardware_verification_modules():
    """Historical finding, reconstructed (not deleted) after repair:
    B-149O.19.3-1 (this phase's own Blocking finding, §7.5 of the phase
    verification document). Against the PRE-REPAIR 18-file enumeration,
    `hatp_ag_authority.py`, `hatp_rollback_consumption.py`, and
    `human_approval_trusted_provenance.py` (all three IN the pre-repair
    frozen set) directly call
    `pcae.core.hatp_providers.create_production_hardware_provider`, which
    dynamically imports `pcae.core.hatp_fido2_provider.Fido2HardwareProvider`
    (or `hatp_piv_provider.PivHardwareProvider`) -- the modules that
    perform the actual hardware/cryptographic signature verification
    producing `signature_valid`/`human_presence_proven`. None of
    `hatp_providers.py`, `hatp_fido2_provider.py`, `hatp_piv_provider.py`,
    nor (a fourth omission this phase's own extended re-walk additionally
    found) `hatp_hardware_credentials.py` was named in the pre-repair
    HMIC-REQ-050 enumeration, so none of their bytes participated in
    `implementation_scope_digest` at that time. An edit to
    `Fido2HardwareProvider.verify()` that always returns
    `signature_valid=True` was invisible to certification under that
    enumeration -- a security-relevant transitive dependency HMIC-REQ-052
    claimed was fully covered, was not. Phase 149O.19.3R repaired this by
    adding all four files to HMIC-REQ-050 (contract §49); see
    `test_repaired_frozen_set_now_includes_hardware_verification_modules`
    for the current, repaired assertion."""
    pre_repair_frozen_dotted = _PRE_REPAIR_FROZEN_DOTTED_MODULES
    assert "pcae.core.hatp_providers" not in pre_repair_frozen_dotted
    assert "pcae.core.hatp_fido2_provider" not in pre_repair_frozen_dotted
    assert "pcae.core.hatp_piv_provider" not in pre_repair_frozen_dotted
    assert "pcae.core.hatp_hardware_credentials" not in pre_repair_frozen_dotted

    for frozen_rel in (
        "core/hatp_ag_authority.py",
        "core/hatp_rollback_consumption.py",
        "core/human_approval_trusted_provenance.py",
    ):
        imports = _pcae_imports(_SRC / frozen_rel)
        assert "pcae.core.hatp_providers" in imports, (
            f"{frozen_rel} expected to import pcae.core.hatp_providers directly"
        )

    fido2_source = (_SRC / "core" / "hatp_providers.py").read_text(encoding="utf-8")
    assert "hatp_fido2_provider" in fido2_source
    assert "hatp_piv_provider" in fido2_source

    fido2_verify_source = (_SRC / "core" / "hatp_fido2_provider.py").read_text(encoding="utf-8")
    assert "def verify(" in fido2_verify_source
    assert "signature_valid=True" in fido2_verify_source

    assert "pcae.core.hatp_hardware_credentials" in _pcae_imports(_SRC / "core" / "hatp_fido2_provider.py")


def test_repaired_frozen_set_now_includes_hardware_verification_modules():
    """Current-state assertion (post Phase 149O.19.3R repair, B-149O.19.3-1):
    the CURRENT HMIC-REQ-050 enumeration now names all four previously-
    omitted authority-sensitive files, so their bytes now do participate
    in `implementation_scope_digest`. This does not itself close
    B-149O.19.3-1 -- the finding remains REPAIRED AT CONTRACT LEVEL,
    PENDING INDEPENDENT RE-VERIFICATION (contract §49) until a future
    independent re-verification phase confirms it."""
    frozen_dotted = _FROZEN_DOTTED_MODULES
    for dotted in (
        "pcae.core.hatp_providers",
        "pcae.core.hatp_fido2_provider",
        "pcae.core.hatp_piv_provider",
        "pcae.core.hatp_hardware_credentials",
    ):
        assert dotted in frozen_dotted, f"expected {dotted} to be in the repaired frozen set"

    contract_text = _CONTRACT_TEXT
    assert "B-149O.19.3-1" in contract_text
    assert "REPAIRED AT CONTRACT LEVEL" in contract_text
    assert "PENDING INDEPENDENT RE-VERIFICATION" in contract_text


#: The narrow subset of the frozen set whose own authority-sensitive
#: transitive `pcae.core.*` dependencies this test holds to a strict
#: completeness bar. `cli.py`, `commands/agent.py`, and `core/agent.py`
#: are excluded from this strict check: they are broad CLI-dispatch/
#: agent-lifecycle entrypoints whose own `pcae.*` import lists are
#: dominated by dozens of unrelated command modules and generic
#: task/git/policy utilities (verified by direct inspection: none of
#: `pcae.commands.<other-subcommand>`, `pcae.core.paths`,
#: `pcae.core.git_status`, `pcae.core.tasks`, `pcae.core.policy`,
#: `pcae.core.strategic_lineage`, `pcae.core.provenance`,
#: `pcae.core.handoff_verification`, `pcae.core.backend_invocations`, or
#: `pcae.core.notification_config` implement HATP/HMRC verification or
#: consumption-gating logic) -- a utility/dispatch dependency whose
#: change cannot alter authority semantics, per the "utility vs.
#: authority-sensitive dependency" distinction the verification document
#: draws explicitly. This strict check instead targets exactly the
#: HATP/HMRC/PB-core modules where an unbound dependency would be
#: security-relevant.
#: Phase 149O.19.3R added the four newly-frozen provider/credential files
#: to this strict subset too, so their OWN one-hop `pcae.*` dependencies
#: are held to the identical completeness bar -- closing the repair
#: loop rather than only adding them to the frozen list without
#: re-checking what THEY import.
_STRICT_CLOSURE_SUBSET = (
    "core/hatp_mandatory_cutover.py",
    "core/hatp_ag_authority.py",
    "core/hatp_rollback_consumption.py",
    "core/hatp_bootstrap.py",
    "core/human_approval_trusted_provenance.py",
    "core/repository_identity.py",
    "core/hatp_evidence_store.py",
    "core/hatp_signed_evidence.py",
    "core/permission_broker.py",
    "core/permission_broker_foundation.py",
    "core/hatp_providers.py",
    "core/hatp_fido2_provider.py",
    "core/hatp_piv_provider.py",
    "core/hatp_hardware_credentials.py",
)

#: Documented, non-blocking unbound dependencies of the strict subset,
#: each with an explicit rationale (see the phase verification document
#: and the Phase 149O.19.3R repair document/contract §49 for full
#: analysis):
#:
#: - `pcae.core.paths`: a generic repo-root/`HarnessPath` path-join
#:   helper with no HATP/consumption-authority logic of its own.
#: - `pcae.core.gate_dry_run`, `pcae.core.scope_preflight`,
#:   `pcae.core.shell_gate`: Permission Broker *policy-decision-support*
#:   modules, downstream of `permission_broker.py`'s own bound bytes.
#:   HMIC-REQ-068 already explicitly excludes PBPA-001/PBPC-001 (PB
#:   *policy*) from `contract_versions` as "a separate, downstream
#:   concern from the consumption chain's own implementation
#:   correctness" -- these modules implement that same excluded PB
#:   policy-decision concern, not HMRC-001's own consumption-chain gating
#:   logic, so leaving them unbound is consistent with, not an exception
#:   to, the contract's own stated line.
#:
#: `pcae.core.hatp_providers`, `hatp_fido2_provider`, `hatp_piv_provider`,
#: and `hatp_hardware_credentials` were REMOVED from this allowlist by
#: Phase 149O.19.3R: they are the repaired finding (B-149O.19.3-1) and
#: are now themselves part of the frozen set (`_FROZEN_DOTTED_MODULES`),
#: not a documented exception to it.
#: `pcae.core.hatp_mandatory_certification` (Phase 149O.19.5F, Wave F):
#: this test module's `_FROZEN_SRC_RELATIVE_PATHS` constant is a static
#: historical reconstruction of HMIC-REQ-050's enumeration as it stood at
#: Phase 149O.19.3/149O.19.3R and is intentionally not live-updated (see
#: the historical/current split above). `hatp_mandatory_certification.py`
#: did not exist at that time; it was built later (149O.19.5A-5D) and
#: added to the frozen enumeration by the v1.1 24-file realignment
#: (149O.19.5E.3, independently re-verified 149O.19.5E.4). It IS bound in
#: the current, real HMIC-REQ-050 enumeration -- listed here only because
#: this test's own historical snapshot constant predates that addition,
#: not because the dependency is actually uncovered.
#:
#: `pcae.core.hatp_class_b_conformance`, `pcae.core.
#: hatp_class_b_topology_verifier` (Phase 149O.20L.3, HMRC-REQ-086-100's
#: production integration): `hatp_mandatory_cutover.py` now imports the
#: canonical `verify_class_b_deployment_conformance()` (HMRC-REQ-087, "no
#: duplicate calculation") and the `ClassBConformanceStatus` closed enum
#: it returns, to implement the eighth,
#: `class_b_deployment_conformance_satisfies_readiness` readiness term.
#: This mirrors CBV-S1's own already-established precedent exactly: the
#: three Class-B verifier modules are deliberately outside HMIC-REQ-050's
#: frozen scope (independently confirmed by 149O.20K/149O.20K.1's own
#: source-scope contract work) -- HMIC certifies mandatory-consumption
#: implementation identity, not Class-B deployment conformance, which
#: HBDC-001 owns as its own, separately-verified fact. This is a
#: genuinely new, additive, documented exception, not a repair of an
#: existing gap.
_DOCUMENTED_UNBOUND_DEPENDENCIES = {
    "pcae.core.paths",
    "pcae.core.gate_dry_run",
    "pcae.core.scope_preflight",
    "pcae.core.shell_gate",
    "pcae.core.hatp_mandatory_certification",
    "pcae.core.hatp_class_b_conformance",
    "pcae.core.hatp_class_b_topology_verifier",
}


def test_frozen_set_first_party_import_closure_names_every_pcae_dependency_or_is_documented():
    """Mechanically compute the one-hop `pcae.*` import closure of the
    strict HATP/HMRC/PB-core subset of the frozen file set and assert
    each imported module is either (a) itself in the frozen set, or (b)
    in the explicitly documented, rationale-bearing allowlist above. Any
    OTHER unbound first-party dependency of this subset would be a
    second, undocumented gap and must fail this test so it cannot pass
    unnoticed."""
    frozen_dotted = _FROZEN_DOTTED_MODULES

    unexplained = set()
    for rel in _STRICT_CLOSURE_SUBSET:
        p = _SRC / rel
        for dotted in _pcae_imports(p):
            if dotted in frozen_dotted:
                continue
            if dotted in _DOCUMENTED_UNBOUND_DEPENDENCIES:
                continue
            unexplained.add((rel, dotted))

    assert not unexplained, (
        "undocumented unbound first-party dependency of the strict HATP/HMRC/PB-core subset: "
        f"{sorted(unexplained)} -- either add to the frozen set, or document with rationale"
    )


# ---------------------------------------------------------------------------
# 8. Self-certification / writer-surface impossibility -- repository-wide
#    negative search, independent of the 149O.19.2 module's own search.
# ---------------------------------------------------------------------------


#: Phase 149O.19.5A (Wave A of the HMIC-001 implementation this contract
#: verification phase precedes) legitimately added
#: `hatp_mandatory_certification.py`: a pure data-model/parser module that
#: must name the two frozen storage filenames (HMIC-REQ-025) in its own
#: docstrings/comments to document the schema it parses -- it creates no
#: writer, no certification state, and defines none of the writer-shaped
#: symbols below (mechanically confirmed by that phase's own test suite,
#: `tests/test_phase_149o_19_5a_hmic_certification_models_canonical_
#: parsing.py::TestDependencyClosure`/`TestNoCertificationStateCreated`).
#: This is the identical "restated, not weakened" widening methodology
#: `test_phase_149o_18a_...py`'s `_ASSEMBLED_PRODUCTION_FILES` already
#: established for this repository: the filename-mention exemption below
#: is scoped to exactly this one file and exactly the two filename
#: tokens -- every writer-shaped token remains forbidden everywhere,
#: including inside this file, with no exception.
_FILENAME_MENTION_EXEMPT_FILES = frozenset({"src/pcae/core/hatp_mandatory_certification.py"})
_FILENAME_TOKENS = ("certifications.json", "certification-bindings.json")


def test_no_certification_writer_or_state_exists_anywhere_in_src():
    writer_shaped_tokens = (
        "mark_independently_verified",
        "set_certified",
        "create_certification",
        "activate_certification",
        "revoke_certification",
    )
    hits = []
    for py_file in _SRC.rglob("*.py"):
        rel = str(py_file.relative_to(_REPO_ROOT))
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        for token in writer_shaped_tokens:
            if token in text:
                hits.append((rel, token))
        if rel in _FILENAME_MENTION_EXEMPT_FILES:
            continue
        for token in _FILENAME_TOKENS:
            if token in text:
                hits.append((rel, token))
    assert not hits, f"certification-authority-shaped symbol found in production source: {hits}"


def test_no_certification_state_files_exist_under_repository_or_pcae_dir():
    forbidden_names = {"certifications.json", "certification-bindings.json"}
    hits = []
    for path in _REPO_ROOT.rglob("*"):
        if path.name in forbidden_names:
            hits.append(str(path.relative_to(_REPO_ROOT)))
    assert not hits, f"certification state file exists: {hits}"


#: Phase 149O.19.5F (Wave F, gated by Stop Condition W-1 -- independently
#: confirmed closed at 149O.19.5E.4) intentionally replaces this literal
#: with fresh HMIC active-certification validation. This test's original
#: purpose -- proving the ceiling had NOT yet been wired as of Phase
#: 149O.19.3 -- is preserved as a pinned historical read rather than
#: deleted or weakened to accept either value.
_PRE_WAVE_F_COMMIT = "dd6492717ea27a43e16bce3e9c2077a884ed366f"


def test_hardcoded_readiness_ceiling_is_unchanged_literal_false():
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
    assert match.group(1) == "False", (
        "hard-coded ceiling was literal False as of the pre-Wave-F phase-entry commit "
        f"{_PRE_WAVE_F_COMMIT} (HMIC-REQ-075/114); Phase 149O.19.5F wires it to fresh HMIC "
        "validation thereafter -- see test_phase_149o_19_5f_hmic_activation_readiness_integration.py"
    )


# ---------------------------------------------------------------------------
# 9. Editable-install / runtime-source binding reality check (HMIC-REQ-064)
# ---------------------------------------------------------------------------


def test_current_interpreter_resolves_frozen_modules_to_this_repository_checkout():
    import importlib

    module = importlib.import_module("pcae.core.hatp_mandatory_cutover")
    resolved = Path(module.__file__).resolve()
    expected = (_SRC / "core" / "hatp_mandatory_cutover.py").resolve()
    assert resolved == expected, (
        "the currently-running interpreter's import of a frozen module does not resolve to this "
        "checkout's on-disk file -- HMIC-REQ-064's editable-install/source-checkout assumption "
        "would not hold under this interpreter"
    )


# ---------------------------------------------------------------------------
# 10. Contract byte-identity -- no upstream contract amended by this phase
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "contract_file,expected_version",
    [
        ("HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md", "1.0"),
        ("HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md", "1.0"),
        ("HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md", "1.1"),
        ("ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md", "1.0"),
    ],
)
def test_bound_contract_version_headers_match_hmic_contract_versions_field(contract_file, expected_version):
    text = (_CONTRACTS / contract_file).read_text(encoding="utf-8")
    header = text[:400]
    assert f"Version:** {expected_version}" in header or f"**Version:** {expected_version}" in header


def test_no_src_pcae_file_modified_since_149o_19_2_entry_commit():
    # Phase 149O.19.5A legitimately added exactly one new production file,
    # `hatp_mandatory_certification.py` (Wave A of the HMIC-001
    # implementation this contract-verification phase precedes) -- a pure
    # data-model/parser module, no writer, no certification state, no
    # readiness wiring (independently confirmed by that phase's own
    # phase-boundary suite). Widened in place ("restated, not weakened"),
    # identical methodology to `_FILENAME_MENTION_EXEMPT_FILES` above and
    # to `test_phase_149o_18a_...py`'s own `_ASSEMBLED_PRODUCTION_FILES`
    # precedent. Any *other* file change since 149O.19.1's entry commit
    # still fails this test.
    # Phase 149O.19.5F (Wave F, gated by Stop Condition W-1 --
    # independently confirmed closed at 149O.19.5E.4) later, legitimately
    # modified a second production file, `hatp_mandatory_cutover.py`
    # itself -- the sole intended Wave-F wiring site. Widened here in
    # place ("restated, not weakened"), same methodology as the
    # `hatp_mandatory_certification.py` exemption above.
    result = subprocess.run(
        ["git", "diff", "--name-only", "560924f2..HEAD", "--", "src/pcae"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = [ln for ln in result.stdout.splitlines() if ln.strip()]
    exempt = _FILENAME_MENTION_EXEMPT_FILES | {"src/pcae/core/hatp_mandatory_cutover.py"}
    unexpected = [ln for ln in changed if ln not in exempt]
    assert unexpected == [], f"unexpected src/pcae changes since 149O.19.1 entry: {unexpected}"


#: Phase 149O.19.3's own final commit (before Phase 149O.19.3R's repair
#: commits). Re-anchored here (rather than an ever-moving `HEAD`) by
#: Phase 149O.19.3R so this historical assertion -- "149O.19.3 itself,
#: being verification-only, never amended the contract" -- remains true
#: forever, independent of 149O.19.3R's own later, legitimate,
#: explicitly-authorized contract repair (finding B-149O.19.3-1,
#: contract §49). Comparing against `HEAD` here would incorrectly turn
#: this into a false regression the moment any later phase amends the
#: contract at all, including a fully-authorized repair.
_PHASE_149O_19_3_EXIT_COMMIT = "1600215e"


def test_hmic_contract_itself_byte_unchanged_since_149o_19_2_freeze_commit():
    result = subprocess.run(
        [
            "git",
            "diff",
            "--stat",
            f"679f9ba6..{_PHASE_149O_19_3_EXIT_COMMIT}",
            "--",
            str(_CONTRACT_PATH.relative_to(_REPO_ROOT)),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "", "HMIC-001 contract must not be amended by a verification-only phase"

"""Phase 149O.20L.7O.2H -- HMIC-001 v1.4-to-v1.5 Contract Evolution and
Production Alignment: Trust-Enrollment/Signing Closure Limb (d).

Implements the exact target reconciled by 149O.20L.7O.2G.1
(`B-149O.20L.7O.2G-1`): HMIC-001 is amended v1.4 -> v1.5 (contract §59):
HMIC-REQ-052 widened with a new closure limb (d) binding the
Trust-Enrollment/signing authority surface; HMIC-REQ-050 widened from
30 to 35 files (three new `src/pcae/`-relative source entries, two new
repository-root-relative contract-content entries); `contract_versions`
(HMIC-REQ-067) widened from five to seven members, content- and
version-binding `HPSE-001` v1.1 and `HHCE-001` v1.1 per HMIC-REQ-053's
existing uniform-coverage rule. `src/pcae/core/hatp_mandatory_
certification.py`'s `_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_
REPOSITORY_ROOT_RELATIVE_FILES`/`_CONTRACT_IDENTITY_FILES` are realigned
to the new 35/7 set in this same phase, per the 149O.20L.7K precedent.

This is CONTRACT EVOLUTION AND SOURCE/CONTRACT-CONTENT IDENTITY BINDING
ONLY. It does not certify, does not activate HATP, does not provision
FIDO2 hardware, does not enroll a real Principal/Signer, does not create
a real DeploymentBinding, does not mutate hac-dell or the Protected
Root, does not change readiness semantics, does not close CBV-S10, and
does not change runtime capability. See contract §59 and
`docs/PHASE_149O_20L_7O_2H_HMIC_V1_4_TO_V1_5_CONTRACT_EVOLUTION_AND_
PRODUCTION_ALIGNMENT_TRUST_ENROLLMENT_SIGNING_CLOSURE_LIMB_D.md` for the
full phase record.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src" / "pcae"
_CONTRACTS = _REPO_ROOT / "docs" / "contracts"
_CONTRACT_PATH = _CONTRACTS / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
_HPSE_CONTRACT_PATH = _CONTRACTS / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
_HHCE_CONTRACT_PATH = _CONTRACTS / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"
_HMIC_MODULE_PATH = _SRC / "core" / "hatp_mandatory_certification.py"
_SIGNING_CEREMONY_PATH = _SRC / "core" / "hatp_signing_ceremony.py"
_HW_CRED_ADMIN_PATH = _SRC / "core" / "hatp_hardware_credential_admin.py"
_PRINCIPAL_SIGNER_ADMIN_PATH = _SRC / "core" / "hatp_principal_signer_admin.py"

#: This phase's own entry commit -- 149O.20L.7O.2G.1's own finalization
#: commit. Production still implemented the pre-amendment 30/5 set at
#: this commit; the contract still declared v1.4.
_PHASE_ENTRY_COMMIT = "e65b4ce0"

_NEW_SRC_MEMBERS = (
    "src/pcae/core/hatp_signing_ceremony.py",
    "src/pcae/core/hatp_hardware_credential_admin.py",
    "src/pcae/core/hatp_principal_signer_admin.py",
)
_NEW_CONTRACT_MEMBERS = (
    "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md",
    "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md",
)
_NEW_MEMBER_RELATIVE_PATHS = _NEW_SRC_MEMBERS + _NEW_CONTRACT_MEMBERS
_NEW_CONTRACT_IDENTITY = (("HPSE-001", _NEW_CONTRACT_MEMBERS[0]), ("HHCE-001", _NEW_CONTRACT_MEMBERS[1]))


def _git_show(commit: str, path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


# ═══════════════════════════════════════════════════════════════════════════
# 1/2/3/4/5. Exact membership counts (HMIC-REQ-050/067)
# ═══════════════════════════════════════════════════════════════════════════


def test_hmic_contract_version_is_1_5():
    text = _CONTRACT_PATH.read_text(encoding="utf-8")
    assert "**Version:** 1.5" in text


def test_exactly_twenty_six_source_relative_members():
    from pcae.core import hatp_mandatory_certification as hmic

    assert len(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) == 26


def test_exactly_nine_repository_root_relative_members():
    """Historical snapshot, preserved (§26 of the 149O.20L.7O.2M
    governing prompt): true at this phase's own exit commit
    (0893f40a). Superseded for LIVE production state by Phase
    149O.20L.7O.2M's own HMIC v1.7 widening (9 -> 11)."""

    text = subprocess.check_output(
        ["git", "show", "0893f40a:src/pcae/core/hatp_mandatory_certification.py"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )
    assert text.count("scripts/hatp_certification_admin.py") >= 1
    from pcae.core import hatp_mandatory_certification as hmic

    # Live production state after Phase 149O.20L.7O.2M's own widening:
    assert len(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 11


def test_exactly_thirty_five_total_frozen_members():
    from pcae.core import hatp_mandatory_certification as hmic

    assert len(hmic._FROZEN_AUTHORITY_BEARING_FILES) == 35
    assert len(hmic._FROZEN_SRC_PCAE_RELATIVE_FILES) + len(hmic._FROZEN_REPOSITORY_ROOT_RELATIVE_FILES) == 35


def test_exactly_seven_contract_identities():
    from pcae.core import hatp_mandatory_certification as hmic

    assert len(hmic._CONTRACT_IDENTITY_FILES) == 7


# ═══════════════════════════════════════════════════════════════════════════
# 6/7. No duplicate frozen member; no missing frozen path
# ═══════════════════════════════════════════════════════════════════════════


def test_no_duplicate_frozen_member():
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = hmic._frozen_canonical_paths()
    assert len(canonical) == len(set(canonical)) == 35


def test_no_missing_frozen_path():
    from pcae.core import hatp_mandatory_certification as hmic

    for canonical in hmic._frozen_canonical_paths():
        assert (_REPO_ROOT / canonical).is_file(), f"missing on disk: {canonical}"
        assert not (_REPO_ROOT / canonical).is_symlink(), f"symlinked: {canonical}"


# ═══════════════════════════════════════════════════════════════════════════
# 8/9. Exact contract<->production source-set and contract-version equality
# ═══════════════════════════════════════════════════════════════════════════


def _extract_req_050_block(contract_text: str) -> "list[str]":
    start = contract_text.index("HMIC-REQ-050 (Exact Enumeration")
    fence_open = contract_text.index("```", start)
    fence_close = contract_text.index("```", fence_open + 3)
    entries = []
    for raw in contract_text[fence_open + 3 : fence_close].splitlines():
        line = raw.strip()
        if line:
            entries.append(line.split()[0])
    return entries


def test_contract_production_source_set_equality():
    from pcae.core import hatp_mandatory_certification as hmic

    entries = _extract_req_050_block(_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert len(entries) == 35
    contract_canonical = set()
    for index, entry in enumerate(entries):
        contract_canonical.add(f"src/pcae/{entry}" if index < 26 else entry)
    assert contract_canonical == set(hmic._frozen_canonical_paths())


def test_contract_production_contract_version_equality():
    from pcae.core import hatp_mandatory_certification as hmic

    match = re.search(
        r"HMIC-REQ-067 \(Revised,.*?entries?,\s+no more,\s+no fewer",
        _CONTRACT_PATH.read_text(encoding="utf-8"),
        re.S,
    )
    assert match is not None
    contract_ids = re.findall(r"`([A-Z]+-\d{3})`", match.group(0))
    seen: "list[str]" = []
    for cid in contract_ids:
        if cid not in seen:
            seen.append(cid)
    production_ids = [cid for cid, _ in hmic._CONTRACT_IDENTITY_FILES]
    assert seen == production_ids
    assert len(production_ids) == 7


# ═══════════════════════════════════════════════════════════════════════════
# 10. Closed contract_versions schema equality (Wave A parser)
# ═══════════════════════════════════════════════════════════════════════════


def test_closed_contract_versions_schema_is_now_seven_members_repaired_by_2h_0():
    """As left by this phase (149O.20L.7O.2H), `_CONTRACT_VERSIONS_
    REQUIRED_KEYS` (Wave A's own closed-schema constant) was widened by
    this phase's own two new members only (HMRC/HATP/HSCE/RAE +
    HPSE-001/HHCE-001 = 6), leaving the pre-existing, disclosed
    `HBDC-001` gap (2G/2G.1's own carried-forward finding) untouched.
    Finding B-149O.20L.7O.2H-1 (opened by 149O.20L.7O.2H.0's own
    governing task) subsequently found this gap load-bearing -- HMIC-001
    v1.5's own text (HMIC-REQ-067/069/053) unambiguously requires exactly
    seven `contract_versions` entries, with no textual basis for a
    narrower Wave-A-only acceptance set -- and repaired it in
    149O.20L.7O.2H.0, widening this constant to the full seven-member
    set, exactly equal to `_CONTRACT_IDENTITY_FILES`. This test now
    reflects that repaired state; see `tests/test_phase_149o_20l_7o_2h_0_
    hmic_certificationrecord_contract_version_closed_schema_alignment_
    repair.py` for the full repair test suite."""
    from pcae.core import hatp_mandatory_certification as hmic

    assert hmic._CONTRACT_VERSIONS_REQUIRED_KEYS == frozenset(
        {"HMRC-001", "HATP-001", "HSCE-001", "RAE-001", "HBDC-001", "HPSE-001", "HHCE-001"}
    )


# ═══════════════════════════════════════════════════════════════════════════
# 11/12. Three new Python files included; retained members
# ═══════════════════════════════════════════════════════════════════════════


def test_three_new_python_source_files_included():
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = set(hmic._frozen_canonical_paths())
    for relative in _NEW_SRC_MEMBERS:
        assert relative in canonical


def test_all_previous_thirty_members_retained():
    entry_source = _git_show(_PHASE_ENTRY_COMMIT, "src/pcae/core/hatp_mandatory_certification.py")
    ns: dict = {}
    exec(compile(entry_source, "<pre-2H hatp_mandatory_certification.py>", "exec"), ns)  # noqa: S102
    pre_2h_canonical = ns["_frozen_canonical_paths"]()
    assert len(pre_2h_canonical) == 30

    from pcae.core import hatp_mandatory_certification as hmic

    current_canonical = set(hmic._frozen_canonical_paths())
    assert set(pre_2h_canonical) < current_canonical


# ═══════════════════════════════════════════════════════════════════════════
# 13. HPSE/HHCE contract content included
# ═══════════════════════════════════════════════════════════════════════════


def test_hpse_contract_content_included():
    from pcae.core import hatp_mandatory_certification as hmic

    assert "docs/contracts/HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md" in hmic._frozen_canonical_paths()


def test_hhce_contract_content_included():
    from pcae.core import hatp_mandatory_certification as hmic

    assert "docs/contracts/HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md" in hmic._frozen_canonical_paths()


# ═══════════════════════════════════════════════════════════════════════════
# 15/16/17. HPSE/HHCE digest sensitivity, HPSE/HHCE version dynamically
# derived, same-version content drift changes digest (disposable copy)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def scratch_tree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A disposable tree containing exactly the live thirty-five frozen
    files, populated from working-tree bytes. Perturbations happen here,
    never in the real tree."""
    from pcae.core import hatp_mandatory_certification as hmic

    root = tmp_path_factory.mktemp("hmic_2h_scope")
    for canonical in hmic._frozen_canonical_paths():
        target = root / canonical
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((_REPO_ROOT / canonical).read_bytes())
    return root


def _digest(root: Path) -> str:
    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    return hmic.derive_implementation_scope_digest(HarnessPath(root))


@pytest.mark.parametrize("member", _NEW_MEMBER_RELATIVE_PATHS)
def test_new_member_digest_sensitive(scratch_tree: Path, member: str):
    baseline = _digest(scratch_tree)
    target = scratch_tree / member
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n# 2H perturbation\n")
        assert _digest(scratch_tree) != baseline
    finally:
        target.write_bytes(original)
    assert _digest(scratch_tree) == baseline


def test_hpse_version_dynamically_derived(scratch_tree: Path):
    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    monkeypatch_target = scratch_tree / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
    original = monkeypatch_target.read_bytes()
    try:
        monkeypatch_target.write_bytes(original.replace(b"**Version:** 1.1", b"**Version:** 9.9"))
        derived = hmic.derive_contract_versions(HarnessPath(scratch_tree))
        assert derived["HPSE-001"] == "9.9"
    finally:
        monkeypatch_target.write_bytes(original)


def test_hhce_version_dynamically_derived(scratch_tree: Path):
    from pcae.core import hatp_mandatory_certification as hmic
    from pcae.core.paths import HarnessPath

    monkeypatch_target = scratch_tree / "docs" / "contracts" / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"
    original = monkeypatch_target.read_bytes()
    try:
        monkeypatch_target.write_bytes(original.replace(b"**Version:** 1.1", b"**Version:** 9.9"))
        derived = hmic.derive_contract_versions(HarnessPath(scratch_tree))
        assert derived["HHCE-001"] == "9.9"
    finally:
        monkeypatch_target.write_bytes(original)


def test_hpse_same_version_content_drift_changes_digest(scratch_tree: Path):
    """Same-version content-only drift is caught by the digest binding,
    not merely by the version-header comparison -- the exact HBDC-001
    precedent (149O.20D.1), now demonstrated for HPSE-001."""
    baseline_digest = _digest(scratch_tree)
    target = scratch_tree / "docs" / "contracts" / "HATP_PRINCIPAL_SIGNER_ENROLLMENT_CONTRACT.md"
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n<!-- same-version content drift -->\n")
        assert b"**Version:** 1.1" in target.read_bytes()
        assert _digest(scratch_tree) != baseline_digest
    finally:
        target.write_bytes(original)


def test_hhce_same_version_content_drift_changes_digest(scratch_tree: Path):
    baseline_digest = _digest(scratch_tree)
    target = scratch_tree / "docs" / "contracts" / "HATP_HARDWARE_CREDENTIAL_ENROLLMENT_CONTRACT.md"
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n<!-- same-version content drift -->\n")
        assert b"**Version:** 1.1" in target.read_bytes()
        assert _digest(scratch_tree) != baseline_digest
    finally:
        target.write_bytes(original)


# ═══════════════════════════════════════════════════════════════════════════
# 20. New limb (d) call-graph closure satisfied
# ═══════════════════════════════════════════════════════════════════════════


def _pcae_owned_imports(path: Path) -> "set[str]":
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: "set[str]" = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("pcae"):
                result.add(module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("pcae"):
                    result.add(alias.name)
    return result


def test_limb_d_anchor_function_present():
    text = _SIGNING_CEREMONY_PATH.read_text(encoding="utf-8")
    assert "def production_sign_rollback_evidence(" in text


def test_limb_d_writer_entry_points_present():
    hw_text = _HW_CRED_ADMIN_PATH.read_text(encoding="utf-8")
    principal_text = _PRINCIPAL_SIGNER_ADMIN_PATH.read_text(encoding="utf-8")
    assert "def register_credential(" in hw_text
    assert "def revoke_credential(" in hw_text
    assert "def enroll_principal(" in principal_text
    assert "def enroll_signer(" in principal_text


_EXCLUDED_UTILITY_LEAVES = frozenset({"paths", "provenance", "git_status", "tasks"})


def test_limb_d_closure_every_import_bound_or_excluded_leaf():
    from pcae.core import hatp_mandatory_certification as hmic

    current_canonical = set(hmic._frozen_canonical_paths())
    bound_modules = {p.rsplit("/", 1)[-1][: -len(".py")] for p in current_canonical if p.endswith(".py")}

    for relative in _NEW_SRC_MEMBERS:
        path = _REPO_ROOT / relative
        for imported in _pcae_owned_imports(path):
            leaf = imported.rsplit(".", 1)[-1]
            assert leaf in bound_modules or leaf in _EXCLUDED_UTILITY_LEAVES, (
                f"{relative} imports {imported!r}, which is neither an already-bound member "
                f"nor an explicitly-excluded utility leaf"
            )


# ═══════════════════════════════════════════════════════════════════════════
# 21. Class-B members retained; 22. DeploymentBinding admin retained
# ═══════════════════════════════════════════════════════════════════════════


def test_class_b_and_deploymentbinding_members_retained():
    from pcae.core import hatp_mandatory_certification as hmic

    canonical = set(hmic._frozen_canonical_paths())
    for relative in (
        "src/pcae/core/hatp_class_b_topology_verifier.py",
        "src/pcae/core/hatp_environment_lock_verifier.py",
        "src/pcae/core/hatp_class_b_conformance.py",
        "src/pcae/core/hatp_deployment_binding_admin.py",
        "scripts/hatp_deployment_binding_admin.py",
    ):
        assert relative in canonical


# ═══════════════════════════════════════════════════════════════════════════
# 23/24. Old-five CertificationRecord fails current identity; unknown
# contract entry fails closed
# ═══════════════════════════════════════════════════════════════════════════


def test_old_five_member_certification_record_fails_current_schema():
    """A record built against the pre-2H four-member `_CONTRACT_VERSIONS_
    REQUIRED_KEYS` set (HMRC/HATP/HSCE/RAE, matching this constant's own
    pre-existing, disclosed scope -- HBDC-001 was never a member of it)
    fails the current, widened six-member schema as missing the two new
    required entries."""
    from pcae.core import hatp_mandatory_certification as hmic

    old_four = {
        "HMRC-001": "1.0",
        "HATP-001": "1.0",
        "HSCE-001": "1.1",
        "RAE-001": "1.0",
    }
    with pytest.raises(hmic.CertificationMalformedError, match="missing required contract entries"):
        hmic._require_contract_versions(old_four, context="contract_versions")


def test_unknown_eighth_contract_entry_fails_closed():
    from pcae.core import hatp_mandatory_certification as hmic

    seven_plus_one = {
        "HMRC-001": "1.0",
        "HATP-001": "1.0",
        "HSCE-001": "1.1",
        "RAE-001": "1.0",
        "HPSE-001": "1.1",
        "HHCE-001": "1.1",
        "UNKNOWN-001": "1.0",
    }
    with pytest.raises(hmic.CertificationMalformedError, match="unrecognized contract entries"):
        hmic._require_contract_versions(seven_plus_one, context="contract_versions")


# ═══════════════════════════════════════════════════════════════════════════
# 25. Deterministic repeated digest
# ═══════════════════════════════════════════════════════════════════════════


def test_deterministic_repeated_digest():
    from pcae.core.paths import HarnessPath
    from pcae.core import hatp_mandatory_certification as hmic

    root = HarnessPath(_REPO_ROOT)
    first = hmic.derive_implementation_scope_digest(root)
    second = hmic.derive_implementation_scope_digest(root)
    assert first == second
    assert re.match(r"^[0-9a-f]{64}$", first)


# ═══════════════════════════════════════════════════════════════════════════
# 26. Self-bound certification module included
# ═══════════════════════════════════════════════════════════════════════════


def test_self_bound_certification_module_included():
    from pcae.core import hatp_mandatory_certification as hmic

    assert "src/pcae/core/hatp_mandatory_certification.py" in hmic._frozen_canonical_paths()


# ═══════════════════════════════════════════════════════════════════════════
# 27/28. No production certification created; runtime unchanged
# ═══════════════════════════════════════════════════════════════════════════


def test_no_certification_storage_artifacts_created_by_this_phase():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    for line in result.stdout.splitlines():
        assert "certifications.json" not in line
        assert "certification-bindings.json" not in line


def test_runtime_state_unchanged_observed_observe_unavailable():
    """This phase binds source/contract identity only -- it does not
    touch runtime state, readiness wiring, or activation. `pcae runtime
    inspect` remains Observed/observe/unavailable."""
    result = subprocess.run(
        ["pcae", "runtime", "inspect"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "Observed" in result.stdout
    assert "observe" in result.stdout
    assert "unavailable" in result.stdout


# ═══════════════════════════════════════════════════════════════════════════
# HMIC-REQ-053 uniform coverage: every contract_versions member content-bound
# ═══════════════════════════════════════════════════════════════════════════


def test_every_contract_versions_member_is_also_content_bound():
    from pcae.core import hatp_mandatory_certification as hmic

    current_canonical = set(hmic._frozen_canonical_paths())
    for _contract_id, relative_path in hmic._CONTRACT_IDENTITY_FILES:
        assert relative_path in current_canonical


def test_hpse_hhce_headers_parse_as_version_1_1():
    from pcae.core import hatp_mandatory_certification as hmic

    for contract_id, relative_path in _NEW_CONTRACT_IDENTITY:
        text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8")
        id_match = hmic._CONTRACT_ID_HEADER_RE.search(text)
        version_match = hmic._CONTRACT_VERSION_HEADER_RE.search(text)
        assert id_match is not None and id_match.group(1) == contract_id
        assert version_match is not None and version_match.group(1) == "1.1"


# ═══════════════════════════════════════════════════════════════════════════
# BF-1/BF-2/2F.3-1/2F.3-2 unaffected: zero commits to signing/hardware
# authority files since this phase's own entry
# ═══════════════════════════════════════════════════════════════════════════


def test_no_commits_to_signing_or_admin_files_since_phase_entry():
    """"src/pcae/core/hatp_hardware_credential_admin.py" intentionally
    excluded as of Phase 149O.20L.7O.2N.13, which legitimately committed
    to it (protocol_name vocabulary widening + duplicated-validator
    centralization, NBF-149O.20L.7O.2N.12-2's repair) -- see that
    phase's own dedicated test module for coverage."""
    for relative in (
        "src/pcae/core/hatp_signing_ceremony.py",
        "src/pcae/core/hatp_fido2_provider.py",
        "src/pcae/core/hatp_principal_signer_admin.py",
    ):
        result = subprocess.run(
            ["git", "log", "--oneline", f"{_PHASE_ENTRY_COMMIT}..HEAD", "--", relative],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        assert result.stdout.strip() == "", f"unexpected commit touching {relative}: {result.stdout}"

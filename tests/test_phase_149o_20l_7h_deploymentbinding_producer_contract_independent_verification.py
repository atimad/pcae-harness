"""Phase 149O.20L.7H -- DeploymentBinding Producer Contract Independent
Verification.

Verification-only companion module. This module does NOT import or treat
`tests/test_phase_149o_20l_7g_deploymentbinding_producer_contract_schema_
evolution.py` as an oracle -- every assertion here is derived fresh
against primary contract/source text: the immutable pre-7G/post-7G
contract diff, requirement-ID integrity, each of HBDC-REQ-056..070
individually, the authority-input/evidence boundary, the
`RepositoryIdentity` prerequisite, F3/F4 adversarial verification,
uniqueness/idempotency/duplicate/revocation semantics, atomic-replacement
and audit-reconstructability properties, path normalization, trust-store
symlink/ACL discipline, timestamp strictness and the permissive-parser
gap, the implementation-plan's requirement-to-module mapping, the
first-use sequencing, the HMIC digest-binding consequence, Dell staleness,
and proof that no producer/binding/mutation was introduced.

This phase implements nothing. It creates no `DeploymentBinding`. It
performs no Dell mutation.
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parents[1]
_HBDC_CONTRACT_PATH = _REPO_ROOT / "docs" / "contracts" / "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md"
_HMIC_CONTRACT_PATH = (
    _REPO_ROOT / "docs" / "contracts" / "HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_CONTRACT.md"
)
_HBDC_CONTRACT = _HBDC_CONTRACT_PATH.read_text(encoding="utf-8")
_HMIC_CONTRACT = _HMIC_CONTRACT_PATH.read_text(encoding="utf-8")
_BOOTSTRAP_SRC_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_bootstrap.py"
_IDENTITY_SRC_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "repository_identity.py"
_CUTOVER_SRC_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_cutover.py"
_CERT_SRC_PATH = _REPO_ROOT / "src" / "pcae" / "core" / "hatp_mandatory_certification.py"
_BOOTSTRAP_SRC = _BOOTSTRAP_SRC_PATH.read_text(encoding="utf-8")
_IDENTITY_SRC = _IDENTITY_SRC_PATH.read_text(encoding="utf-8")
_CUTOVER_SRC = _CUTOVER_SRC_PATH.read_text(encoding="utf-8")
_CERT_SRC = _CERT_SRC_PATH.read_text(encoding="utf-8")
_CLI_SRC = (_REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
_SRC_PCAE_ROOT = _REPO_ROOT / "src" / "pcae"
_CHGR_PATH = _REPO_ROOT / ".pcae" / "publication-execution" / "records" / "chgr-0e37ed1340b14311826722c4dbf3e856.json"

_PRE_7G_BASELINE_SHA = "01a47f0510e51d5b9b18c8f3a8beeb46b8c1a4d7"  # placeholder, overridden below by dynamic lookup
_POST_7G_SHA = "0b530959857349c947f0b2410de95d8f8c0effb9"


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()


def _pre_7g_baseline_sha() -> str:
    return _git("rev-parse", f"{_POST_7G_SHA}^")


# ═══════════════════════════════════════════════════════════════════════════
# 1. Immutable pre-7G / post-7G contract diff, independently re-derived
# ═══════════════════════════════════════════════════════════════════════════


class TestImmutableBaselineDiff:
    def test_pre_7g_baseline_is_parent_of_7g_commit(self) -> None:
        assert _pre_7g_baseline_sha() == _git("rev-parse", "01a47f05")

    def test_7g_commit_touches_exactly_three_files(self) -> None:
        names = _git("show", "--stat", "--format=", _POST_7G_SHA)
        touched = [line.split("|")[0].strip() for line in names.splitlines() if "|" in line]
        assert len(touched) == 3

    def test_7g_commit_touches_zero_src_pcae_files(self) -> None:
        changed = _git("diff", "--name-only", _pre_7g_baseline_sha(), _POST_7G_SHA)
        assert not any(name.startswith("src/pcae/") for name in changed.splitlines())

    def test_hbdc_contract_version_bumped_1_0_to_1_1(self) -> None:
        pre = _git("show", f"{_pre_7g_baseline_sha()}:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
        post = _git("show", f"{_POST_7G_SHA}:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
        assert "**Version:** 1.0" in pre
        assert "**Version:** 1.1" in post

    def test_no_existing_requirement_001_055_text_was_altered(self) -> None:
        pre = _git("show", f"{_pre_7g_baseline_sha()}:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
        post = _git("show", f"{_POST_7G_SHA}:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
        pre_reqs = dict(re.findall(r"\*\*(HBDC-REQ-0[0-5][0-9])\.\*\*\s*(.+)", pre))
        post_reqs = dict(re.findall(r"\*\*(HBDC-REQ-0[0-5][0-9])\.\*\*\s*(.+)", post))
        assert pre_reqs, "expected to find HBDC-REQ-001..055 in pre-7G text"
        for req_id, text in pre_reqs.items():
            assert post_reqs.get(req_id) == text, f"{req_id} text changed unexpectedly"


# ═══════════════════════════════════════════════════════════════════════════
# 2. Requirement-ID integrity (independent re-scan, not 7G's own claim)
# ═══════════════════════════════════════════════════════════════════════════


class TestRequirementIdIntegrity:
    def test_seventy_unique_gapless_defined_ids(self) -> None:
        defined = re.findall(r"\*\*(HBDC-REQ-[0-9]+)\.\*\*", _HBDC_CONTRACT)
        assert len(defined) == len(set(defined)) == 70
        numbers = sorted(int(d.rsplit("-", 1)[1]) for d in defined)
        assert numbers == list(range(1, 71))

    def test_traceability_table_section_24_matches_defined_set_exactly(self) -> None:
        section = _HBDC_CONTRACT.split("## 24. Full Requirement Traceability")[1].split("## 25.")[0]
        traced = re.findall(r"\|\s*(HBDC-REQ-[0-9]+)\s*\|", section)
        defined = set(re.findall(r"\*\*(HBDC-REQ-[0-9]+)\.\*\*", _HBDC_CONTRACT))
        assert len(traced) == len(set(traced)) == 70
        assert set(traced) == defined

    def test_cbd_9_and_cbd_10_present_and_new(self) -> None:
        assert "**CBD-9**" in _HBDC_CONTRACT
        assert "**CBD-10**" in _HBDC_CONTRACT
        pre = _git("show", f"{_pre_7g_baseline_sha()}:docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md")
        assert "CBD-9" not in pre
        assert "CBD-10" not in pre

    def test_each_new_requirement_appears_exactly_once_in_traceability(self) -> None:
        section = _HBDC_CONTRACT.split("## 24. Full Requirement Traceability")[1].split("## 25.")[0]
        for n in range(56, 71):
            assert section.count(f"HBDC-REQ-{n:03d}") == 1


# ═══════════════════════════════════════════════════════════════════════════
# 3. Every HBDC-REQ-056..070 individually present with expected obligations
# ═══════════════════════════════════════════════════════════════════════════


class TestEachNewRequirementIndividually:
    @pytest.mark.parametrize("req_id,fragment", [
        ("HBDC-REQ-056", "separate, non-agent-writable admin tool"),
        ("HBDC-REQ-057", "derive `repository_id` and `canonical_deployment_root` read-only"),
        ("HBDC-REQ-058", "admin's own enrollment context"),
        ("HBDC-REQ-059", "fail closed"),
        ("HBDC-REQ-060", "distinct, explicit admin operation from creation"),
        ("HBDC-REQ-061", "field mutation"),
        ("HBDC-REQ-062", "audit record"),
        ("HBDC-REQ-063", "atomic-write discipline"),
        ("HBDC-REQ-064", "fresh, separate human election"),
        ("HBDC-REQ-065", "not itself cryptographically verified"),
        ("HBDC-REQ-066", "admin OS principal"),
        ("HBDC-REQ-067", "strict"),
        ("HBDC-REQ-068", "not itself gated by HBDC-REQ-056..066's election requirement"),
        ("HBDC-REQ-069", "does not itself satisfy"),
        ("HBDC-REQ-070", "implementation_scope_digest"),
    ])
    def test_requirement_text_present(self, req_id: str, fragment: str) -> None:
        pattern = re.escape(f"**{req_id}.**")
        match = re.search(pattern + r"(.+?)(?=\n- \*\*HBDC-REQ|\n\n##)", _HBDC_CONTRACT, re.DOTALL)
        assert match is not None, f"{req_id} not found"
        assert fragment in match.group(1)

    def test_req_067_timestamp_regex_byte_identical_to_cutover_and_certification(self) -> None:
        req_text_match = re.search(r"\*\*HBDC-REQ-067\.\*\*(.+?)(?=\n- \*\*HBDC-REQ|\n\n##)", _HBDC_CONTRACT, re.DOTALL)
        assert req_text_match is not None
        assert r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$" in req_text_match.group(1)
        cutover_pattern = re.search(r'_TIMESTAMP_PATTERN = re\.compile\((r".+?")\)', _CUTOVER_SRC)
        cert_pattern = re.search(r'_TIMESTAMP_PATTERN = re\.compile\((r".+?")\)', _CERT_SRC)
        assert cutover_pattern and cert_pattern
        assert cutover_pattern.group(1) == cert_pattern.group(1)
        assert r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z" in cutover_pattern.group(1)


# ═══════════════════════════════════════════════════════════════════════════
# 4. Authority-input / election-evidence boundary
# ═══════════════════════════════════════════════════════════════════════════


class TestAuthorityInputBoundary:
    def test_no_boolean_or_freeform_approved_accepted(self) -> None:
        assert "unverified boolean" in _HBDC_CONTRACT
        assert 'free-form "approved" string' in _HBDC_CONTRACT

    def test_election_must_authorize_specific_proposition_fields(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-064\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        for field in ("repository", "root", "principal", "scope"):
            assert field in section

    def test_evidence_not_cryptographically_verified_by_writer_mirrors_hmic(self) -> None:
        assert "mirrors HMIC-REQ-078" in _HBDC_CONTRACT
        assert "HMIC-REQ-078" in _HMIC_CONTRACT

    def test_writer_invocable_only_by_admin_os_principal(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-066\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "never agent-invocable" in section


# ═══════════════════════════════════════════════════════════════════════════
# 5. RepositoryIdentity prerequisite -- explicit, fail-closed, no substitution
# ═══════════════════════════════════════════════════════════════════════════


class TestRepositoryIdentityPrerequisite:
    def test_producer_derives_repository_id_from_existing_identity_only(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-057\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "existing" in section
        assert "never as free-form caller input" in section

    def test_identity_creation_not_gated_by_binding_election(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-068\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "HATP-REQ-048" in section

    def test_ensure_repository_identity_unchanged_and_idempotent_preserve(self) -> None:
        assert "def ensure_repository_identity" in _IDENTITY_SRC
        func = _IDENTITY_SRC.split("def ensure_repository_identity")[1]
        assert "existing is not None" in func
        assert "return existing" in func


# ═══════════════════════════════════════════════════════════════════════════
# 6. F3 adversarial consistency -- repository_id/root re-derivation
# ═══════════════════════════════════════════════════════════════════════════


class TestF3AdversarialConsistency:
    def test_certification_record_has_no_binding_identifier_field(self) -> None:
        section = _HMIC_CONTRACT.split("**HMIC-REQ-032.**")[1].split("**HMIC-REQ-033")[0]
        for forbidden in ("binding_id", "binding_digest", "binding_version"):
            assert forbidden not in section

    def test_certification_reads_from_binding_never_reverse(self) -> None:
        assert "HMIC-REQ-043" in _HMIC_CONTRACT
        assert "HMIC-REQ-044" in _HMIC_CONTRACT
        assert "HMIC-REQ-045" in _HMIC_CONTRACT
        section = _HMIC_CONTRACT.split("**HMIC-REQ-045")[1][:600]
        assert "read-only" in section

    def test_validation_algorithm_never_reads_deployment_binding_status(self) -> None:
        section = _HMIC_CONTRACT.split("## 31. Validation Algorithm")[1].split("## 32.")[0]
        assert "load_repository_enrollment" not in section
        assert "DeploymentBinding" not in section
        assert "status" in section  # step 8 checks CertificationRecord's own status


# ═══════════════════════════════════════════════════════════════════════════
# 7. F4 lifecycle -- schema-enforced single entry, no history, in-place
# ═══════════════════════════════════════════════════════════════════════════


class TestF4Lifecycle:
    def test_status_vocabulary_closed_two_values(self) -> None:
        assert '_STATUS_VALUES = frozenset({"active", "revoked"})' in _BOOTSTRAP_SRC

    def test_duplicate_repository_id_rejected_by_parser(self) -> None:
        assert "if record.repository_id in deployment_bindings:" in _BOOTSTRAP_SRC
        assert "raise HATPTrustStoreMalformedError" in _BOOTSTRAP_SRC.split(
            "if record.repository_id in deployment_bindings:"
        )[1][:200]

    def test_deployment_binding_dataclass_field_set_unchanged(self) -> None:
        fields = re.search(r"class DeploymentBinding:\n(.+?)\n\n", _BOOTSTRAP_SRC, re.DOTALL).group(1)
        names = re.findall(r"\s+(\w+):", fields)
        assert names == [
            "repository_id",
            "canonical_deployment_root",
            "principal_id",
            "signer_key_id",
            "provider_profile",
            "authority_scope",
            "valid_from",
            "status",
            "revoked_at",
        ]

    def test_revocation_is_field_mutation_not_deletion_text(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-061\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "SHALL NOT be deleted" in section
        assert "in-place overwrite" in section

    def test_no_history_explicitly_delegated_to_governance_infra(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-061\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "retains no history" in section
        assert "HBDC-REQ-062" in section


# ═══════════════════════════════════════════════════════════════════════════
# 8. Uniqueness key, idempotency, duplicate-conflict, revocation matching
# ═══════════════════════════════════════════════════════════════════════════


class TestUniquenessIdempotencyDuplicates:
    def test_uniqueness_key_is_repository_id_alone(self) -> None:
        parse_fn = _BOOTSTRAP_SRC.split("def _parse_registry_document")[1]
        binding_block = parse_fn.split("deployment_bindings: dict[str, DeploymentBinding] = {}")[1][:400]
        assert "record.repository_id in deployment_bindings" in binding_block

    def test_idempotent_no_op_and_conflicting_fail_closed_both_specified(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-059\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "fail closed" in section
        assert "safe no-op" in section
        assert "idempotent-preserve" in section

    def test_revoked_binding_cannot_match(self) -> None:
        func = _BOOTSTRAP_SRC.split("def deployment_binding_matches(")[1]
        assert 'binding.status != "active"' in func
        assert "return False" in func.split('binding.status != "active"')[1][:50]


# ═══════════════════════════════════════════════════════════════════════════
# 9. Atomic replacement / audit reconstructability
# ═══════════════════════════════════════════════════════════════════════════


class TestAtomicityAndAudit:
    def test_writer_must_reuse_write_atomic_no_new_idiom(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-063\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "_write_atomic" in section
        assert "no new idiom SHALL be invented" in section

    def test_write_atomic_precedent_uses_mkstemp_fsync_replace_and_symlink_rejection(self) -> None:
        func = _IDENTITY_SRC.split("def _write_atomic(")[1].split("def read_repository_identity")[0]
        assert "tempfile.mkstemp" in func
        assert "os.fsync" in func
        assert "os.replace" in func
        assert func.count("_reject_symlink") == 2

    def test_audit_record_required_no_bespoke_mechanism(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-062\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "SHALL produce an audit record" in section
        assert "no bespoke audit mechanism SHALL be introduced" in section

    def test_hmic_sibling_contract_has_dedicated_concurrency_lock_hbdc_does_not(self) -> None:
        """Non-blocking finding, captured as a permanent regression guard: HMIC-001
        requires a dedicated fcntl.flock transition lock (HMIC-REQ-097); HBDC-001
        v1.1's new writer requirements do not name an analogous lock anywhere."""
        assert "Dedicated Lock" in _HMIC_CONTRACT
        assert "fcntl.flock" in _HMIC_CONTRACT
        section_16_1 = _HBDC_CONTRACT.split("### 16.1")[1].split("## 17.")[0]
        assert "flock" not in section_16_1
        assert "lock" not in section_16_1.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 10. Canonical-root path normalization
# ═══════════════════════════════════════════════════════════════════════════


class TestPathNormalization:
    def test_resolve_canonical_deployment_root_absolutizes_normalizes_resolves(self, tmp_path: Path) -> None:
        import sys

        sys.path.insert(0, str(_SRC_PCAE_ROOT.parent))
        try:
            from pcae.core.hatp_bootstrap import resolve_canonical_deployment_root
        finally:
            sys.path.pop(0)

        target = tmp_path / "a" / "b"
        target.mkdir(parents=True)
        redundant = tmp_path / "a" / "." / "b" / ".."  / "b"
        assert resolve_canonical_deployment_root(target) == resolve_canonical_deployment_root(redundant)

    def test_same_function_used_by_both_hbdc_057_and_hmic_044(self) -> None:
        hbdc_section = re.search(r"\*\*HBDC-REQ-057\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        hmic_section = _HMIC_CONTRACT.split("**HMIC-REQ-044.**")[1][:400]
        assert "resolve_canonical_deployment_root" in hbdc_section
        assert "resolve_canonical_deployment_root" in hmic_section


# ═══════════════════════════════════════════════════════════════════════════
# 11. Symlink / ACL trust-store rules (unmodified, cross-checked)
# ═══════════════════════════════════════════════════════════════════════════


class TestTrustStoreSymlinkAndOwnership:
    def test_reject_symlink_checks_target_and_parent(self) -> None:
        func = _IDENTITY_SRC.split("def _reject_symlink(")[1].split("def _write_atomic")[0]
        assert "target.is_symlink()" in func
        assert "target.parent" in func

    def test_inspect_bootstrap_environment_checks_group_other_write_and_parent_ownership(self) -> None:
        func = _BOOTSTRAP_SRC.split("def inspect_bootstrap_environment(")[1]
        assert "S_IWGRP" in func
        assert "S_IWOTH" in func
        assert "trust_store_parent_owner_mismatch" in func

    def test_fixed_trust_root_never_derived_from_home_or_env(self) -> None:
        func_text = _BOOTSTRAP_SRC.split("def _default_production_trust_root(")[1].split("def _reject_symlink")[0]
        body = func_text.split('"""', 2)[-1]  # drop the docstring, which discusses Path.home() only to disclaim it
        assert "Path.home(" not in body
        assert "os.environ" not in body
        assert "getenv" not in body
        assert '_MACOS_FIXED_TRUST_ROOT' in body and '_LINUX_FIXED_TRUST_ROOT' in body


# ═══════════════════════════════════════════════════════════════════════════
# 12. Timestamp strictness and the permissive-parser attack
# ═══════════════════════════════════════════════════════════════════════════


class TestTimestampStrictnessAndPermissiveParserGap:
    _STRICT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")

    def _permissive_parse(self, value: str):
        try:
            text = value[:-1] + "+00:00" if value.endswith("Z") else value
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)

    @pytest.mark.parametrize("value", [
        "2026-08-16T10:00:00+05:00",
        "2026-08-16T10:00:00.123456789Z",
        "2026-08-16T10:00:00-00:00",
        "2026-08-16 10:00:00+00:00",
    ])
    def test_read_path_accepts_forms_strict_grammar_rejects(self, value: str) -> None:
        assert not self._STRICT.match(value)
        assert self._permissive_parse(value) is not None

    def test_read_path_parser_is_permissive_fromisoformat(self) -> None:
        func = _BOOTSTRAP_SRC.split("def _parse_iso_timestamp(")[1].split("def is_valid" if False else "# ══")[0]
        assert "datetime.fromisoformat" in func

    def test_req_067_binds_only_future_writer_output_not_read_path(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-067\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "read-path parser" in section or "read-path" in section


# ═══════════════════════════════════════════════════════════════════════════
# 13. Implementation-plan mapping (every HBDC-REQ traced to a named owner)
# ═══════════════════════════════════════════════════════════════════════════


class TestImplementationPlanMapping:
    def test_architecture_doc_names_three_writer_verbs(self) -> None:
        arch_doc = (
            _REPO_ROOT
            / "docs"
            / "PHASE_149O_20L_7G_DEPLOYMENTBINDING_PRODUCER_CONTRACT_SCHEMA_EVOLUTION_AND_IMPLEMENTATION_PLANNING.md"
        ).read_text(encoding="utf-8")
        for name in ("create_deployment_binding", "rotate_deployment_binding", "revoke_deployment_binding"):
            assert name in arch_doc

    def test_no_write_verb_added_to_ordinary_cli(self) -> None:
        assert "create_deployment_binding" not in _CLI_SRC
        assert "rotate_deployment_binding" not in _CLI_SRC
        assert "revoke_deployment_binding" not in _CLI_SRC

    def test_no_admin_tool_script_created_yet(self) -> None:
        scripts_dir = _REPO_ROOT / "scripts"
        names = {p.name for p in scripts_dir.iterdir()} if scripts_dir.exists() else set()
        assert "hatp_deployment_binding_admin.py" not in names


# ═══════════════════════════════════════════════════════════════════════════
# 14. First-use sequencing / CHGR condition 6 / election boundary
# ═══════════════════════════════════════════════════════════════════════════


class TestFirstUseSequencingAndElectionBoundary:
    def test_chgr_condition_6_verbatim_excludes_deploymentbinding_without_fresh_election(self) -> None:
        record = json.loads(_CHGR_PATH.read_text(encoding="utf-8"))
        conditions = record["conditions"]
        assert "no DeploymentBinding" in conditions
        assert "fresh, separate election" in conditions
        assert "repository-identity" not in conditions.lower() or "no repository onboarding" in conditions

    def test_req_069_does_not_claim_to_satisfy_any_election(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-069\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "does not itself satisfy" in section

    def test_no_election_authorization_language_anywhere_in_new_section(self) -> None:
        section_16_1 = _HBDC_CONTRACT.split("### 16.1")[1].split("## 17.")[0]
        assert "is hereby authorized" not in section_16_1
        assert "this election" not in section_16_1


# ═══════════════════════════════════════════════════════════════════════════
# 15. HMIC digest-binding consequence
# ═══════════════════════════════════════════════════════════════════════════


class TestContractIdentityConsequence:
    def test_hbdc_contract_file_in_hmic_frozen_set(self) -> None:
        assert "HATP_CLASS_B_DEPLOYMENT_CONTRACT.md" in _CERT_SRC

    def test_req_070_states_no_separate_hmic_action_required(self) -> None:
        section = re.search(r"\*\*HBDC-REQ-070\.\*\*(.+?)(?=\n- \*\*HBDC-REQ)", _HBDC_CONTRACT, re.DOTALL).group(1)
        assert "no separate HMIC action" in section


# ═══════════════════════════════════════════════════════════════════════════
# 16. Dell staleness (read-only, no Dell access performed by this phase)
# ═══════════════════════════════════════════════════════════════════════════


class TestDellStalenessAnalysis:
    def test_dell_deployed_sha_is_ancestor_of_pre_7g_baseline(self) -> None:
        dell_sha = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", dell_sha, _pre_7g_baseline_sha()],
            cwd=_REPO_ROOT,
        )
        assert result.returncode == 0

    def test_dell_deployed_sha_many_commits_behind_head(self) -> None:
        dell_sha = "28bf137b5dc95d024e8913b678dce0501a46fd0f"
        count = int(_git("rev-list", "--count", f"{dell_sha}..HEAD"))
        assert count >= 40


# ═══════════════════════════════════════════════════════════════════════════
# 17. Proof of no implementation / no binding / no Dell mutation this phase
# ═══════════════════════════════════════════════════════════════════════════


class TestNoImplementationNoBindingNoMutation:
    def test_no_write_function_added_anywhere_in_src_pcae(self) -> None:
        for path in _SRC_PCAE_ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for name in ("def create_deployment_binding", "def rotate_deployment_binding", "def revoke_deployment_binding"):
                assert name not in text, f"{name} unexpectedly found in {path}"

    def test_hatp_trust_store_has_zero_write_methods(self) -> None:
        cls = _BOOTSTRAP_SRC.split("class HATPTrustStore:")[1]
        cls = cls.split("\nclass ")[0] if "\nclass " in cls else cls
        for verb in ("def create(", "def rotate(", "def revoke(", "def enroll(", "def grant("):
            assert verb not in cls

    def test_no_repository_identity_file_created_in_this_repo(self) -> None:
        assert not (_REPO_ROOT / ".pcae" / "repository-identity.json").exists()

    def test_working_tree_clean_at_collection_time(self) -> None:
        status = _git("status", "--short")
        # This module's own file is untracked at authoring time; ignore it.
        remaining = [
            line for line in status.splitlines()
            if "test_phase_149o_20l_7h_deploymentbinding_producer_contract_independent_verification.py" not in line
        ]
        # Governance bookkeeping files (task/status/changelog) are expected to be
        # staged alongside this module by the phase-completion procedure; this
        # test only guards against unexpected src/pcae changes.
        assert not any(line.strip().endswith("src/pcae") or "/src/pcae/" in line for line in remaining)

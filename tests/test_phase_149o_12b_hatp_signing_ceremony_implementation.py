"""Phase 149O.12B — HATP Signing Ceremony Resolver + Orchestrator
Implementation.

BOUNDED PRODUCTION IMPLEMENTATION (per HSCE-001 v1.1, 149O.11's
implementation plan Waves C + D). This phase-specific suite verifies the
implementation's own scope boundaries and cross-cutting invariants --
field-level/attack-level unit coverage lives in `test_hatp_signing_
ceremony.py`.

Authorized production scope this phase: `src/pcae/core/
hatp_signing_ceremony.py` only (AG3/AG5 proof-context resolution +
signing-ceremony orchestration). NOT authorized: CLI (`commands/hatp.py`,
`cli.py` registration -- 149O.12C's exclusive scope), AG3/AG5 consumption
wiring, rollback dispatch changes, Permission Broker changes, Class-B
provisioning, production HATP activation, and no modification of
149O.12A's two modules (`hatp_signed_evidence.py`, `hatp_evidence_
store.py`).

**Updated by Phase 149O.12C** (149O.5-F-3 precedent: an existing test
asserting a since-superseded "zero HATP CLI consumers" snapshot is
updated to reflect the next, separately-authorized phase's own intended
addition, never deleted). This file's own baseline-diff design measures
the *cumulative* `src/pcae/` diff since the fixed 149O.12A commit
(`_149O_12A_BASELINE_COMMIT`), not "149O.12B's own diff in isolation" --
so once 149O.12C's later, planned commits land on top, `commands/
hatp.py` and `cli.py`'s registration hunk are *expected* additions, not
scope creep. `TestProductionFileAllowlist`/`TestNoScopeCreep` below are
updated accordingly (`_EXPECTED_PRODUCTION_FILES` now includes both
149O.12C files; the "CLI must not exist yet" assertions are inverted to
"CLI now exists, exactly as 149O.12C's own governing prompt planned").
Every other invariant this file protects -- 149O.12A's two modules
remaining byte-unchanged, HSCE-001/HATP-001/RAE-001 remaining
byte-unchanged, no Permission Broker import, no AG3/AG5 authority
wiring -- is unchanged and still independently enforced below.

**Updated again by Phase 149O.16.1** (same 149O.5-F-3 precedent):
149O.16.1's own governing prompt authorized exactly one narrow,
independent production repair -- normalizing a terminal 'Z' UTC
designator in `pcae.governance.publication.coordinator._parse_
timestamp` (149O.12B-Obs-PY39-1, a pre-existing, unrelated Python
3.9/3.10 compatibility defect this module's own docstring and
`test_hatp_signing_ceremony.py`'s workaround fixture already documented
as out of 149O.12B's scope). `_EXPECTED_PRODUCTION_FILES` now includes
`coordinator.py`; no other invariant this file protects changed.
"""
from __future__ import annotations

import dataclasses
import inspect
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HSCE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
HATP_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
RAE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"

#: Last commit entering Phase 149O.12B (this phase's baseline) -- pinned
#: per this repository's own repair/re-verification-chain convention.
_149O_12A_BASELINE_COMMIT = "53bf12ca"

#: Cumulative allowlist since the 149O.12A baseline commit. 149O.12B
#: contributed exactly `hatp_signing_ceremony.py`; 149O.12C (a later,
#: separately-authorized phase) legitimately added the two files below
#: (`commands/hatp.py` NEW, `cli.py` registration-only MODIFY) per its
#: own governing prompt's Production Diff Allowlist -- see this module's
#: docstring.
_EXPECTED_PRODUCTION_FILES = frozenset(
    {
        "src/pcae/core/hatp_signing_ceremony.py",
        "src/pcae/commands/hatp.py",
        "src/pcae/cli.py",
        "src/pcae/governance/publication/coordinator.py",
    }
)

_149O_12A_MODULES = (
    "src/pcae/core/hatp_signed_evidence.py",
    "src/pcae/core/hatp_evidence_store.py",
)

_EXISTING_HATP_MODULES_NOT_TOUCHED = (
    "src/pcae/core/human_approval_trusted_provenance.py",
    "src/pcae/core/hatp_providers.py",
    "src/pcae/core/hatp_fido2_provider.py",
    "src/pcae/core/hatp_bootstrap.py",
    "src/pcae/core/hatp_hardware_credentials.py",
    "src/pcae/core/hatp_ag_authority.py",
    "src/pcae/core/repository_identity.py",
    "src/pcae/core/rollback_approval_evidence.py",
    "src/pcae/core/agent.py",
    "src/pcae/commands/agent.py",
    "src/pcae/core/permission_broker.py",
    "src/pcae/core/permission_broker_foundation.py",
    # `src/pcae/cli.py` intentionally excluded here as of Phase 149O.12C
    # (its own separately-authorized CLI_REGISTRATION scope) -- see
    # `test_cli_py_change_is_confined_to_hatp_registration_block` below,
    # which independently confirms the CLI-registration-only expectation
    # this list's exclusion previously enforced by omission.
)

_FORBIDDEN_AUTHORITY_FIELD_NAMES = (
    "approved",
    "verified",
    "valid",
    "permission",
    "allow",
    "operational",
    "executed",
    "human_present",
)


def _run_git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def _production_diff_files() -> set:
    diff = _run_git("diff", "--name-only", _149O_12A_BASELINE_COMMIT, "--", "src/pcae/")
    untracked = _run_git("ls-files", "--others", "--exclude-standard", "--", "src/pcae/")
    if diff.returncode != 0 or untracked.returncode != 0:
        pytest.skip("git unavailable")
    return {line for line in (diff.stdout.split() + untracked.stdout.split()) if line}


class TestProductionFileAllowlist:
    def test_production_diff_is_exactly_the_one_planned_module(self):
        files = _production_diff_files()
        assert files == set(_EXPECTED_PRODUCTION_FILES), f"expected exactly {_EXPECTED_PRODUCTION_FILES}, got {files}"

    def test_no_other_src_pcae_file_touched(self):
        files = _production_diff_files()
        unrelated = files - _EXPECTED_PRODUCTION_FILES
        assert unrelated == set(), f"unrelated production hunks: {unrelated}"

    def test_cli_py_change_is_confined_to_hatp_registration_block(self):
        """Updated by Phase 149O.12C (see module docstring): `cli.py` is
        no longer expected to be byte-unchanged since the 149O.12A
        baseline -- 149O.12C's own governing prompt authorizes exactly a
        registration-only addition. This confirms the diff is a pure
        addition (no line removed/rewritten elsewhere in the file) and
        that the added text is the expected `hatp` registration block."""

        result = _run_git("diff", "--numstat", _149O_12A_BASELINE_COMMIT, "--", "src/pcae/cli.py")
        if result.returncode != 0:
            pytest.skip("git unavailable")
        line = result.stdout.strip()
        assert line, "expected a non-empty cli.py diff since the 149O.12A baseline (149O.12C's registration)"
        added, removed, _path = line.split(maxsplit=2)
        assert int(removed) == 0, "cli.py's diff must be a pure addition, never a rewrite of existing lines"

        cli_source = (REPO_ROOT / "src" / "pcae" / "cli.py").read_text(encoding="utf-8")
        assert 'from pcae.commands.hatp import run_hatp_sign_rollback' in cli_source
        assert 'subparsers.add_parser(\n        "hatp"' in cli_source or '"hatp",' in cli_source

    def test_commands_hatp_module_exists_as_of_149o_12c(self):
        """Inverted by Phase 149O.12C (see module docstring): the CLI
        handler module now exists, exactly as 149O.12B's own report
        recommended as the next phase's exclusive scope."""

        assert (REPO_ROOT / "src" / "pcae" / "commands" / "hatp.py").exists()

    def test_no_permission_broker_module_modified(self):
        for relative in (
            "src/pcae/core/permission_broker.py",
            "src/pcae/core/permission_broker_foundation.py",
        ):
            result = _run_git("diff", "--stat", _149O_12A_BASELINE_COMMIT, "--", relative)
            if result.returncode != 0:
                pytest.skip("git unavailable")
            assert result.stdout.strip() == ""

    def test_149o_12a_modules_byte_unchanged(self):
        for relative in _149O_12A_MODULES:
            result = _run_git("diff", "--stat", _149O_12A_BASELINE_COMMIT, "--", relative)
            if result.returncode != 0:
                pytest.skip("git unavailable")
            assert result.stdout.strip() == "", f"{relative} (149O.12A) was unexpectedly touched this phase"

    def test_no_existing_hatp_or_agent_module_modified(self):
        for relative in _EXISTING_HATP_MODULES_NOT_TOUCHED:
            result = _run_git("diff", "--stat", _149O_12A_BASELINE_COMMIT, "--", relative)
            if result.returncode != 0:
                pytest.skip("git unavailable")
            assert result.stdout.strip() == "", f"{relative} was unexpectedly touched this phase"


class TestContractByteIdentity:
    def test_hsce_001_unmodified(self):
        result = _run_git("diff", "--stat", _149O_12A_BASELINE_COMMIT, "--", str(HSCE_CONTRACT.relative_to(REPO_ROOT)))
        if result.returncode != 0:
            pytest.skip("git unavailable")
        assert result.stdout.strip() == "", "this is an implementation phase; HSCE-001 v1.1 text must not change"

    def test_hatp_001_unmodified(self):
        result = _run_git("diff", "--stat", _149O_12A_BASELINE_COMMIT, "--", str(HATP_CONTRACT.relative_to(REPO_ROOT)))
        if result.returncode != 0:
            pytest.skip("git unavailable")
        assert result.stdout.strip() == ""

    def test_rae_001_unmodified(self):
        result = _run_git("diff", "--stat", _149O_12A_BASELINE_COMMIT, "--", str(RAE_CONTRACT.relative_to(REPO_ROOT)))
        if result.returncode != 0:
            pytest.skip("git unavailable")
        assert result.stdout.strip() == ""


class TestNoScopeCreep:
    def test_no_hatp_evidence_directory_created_in_repository(self):
        assert not (REPO_ROOT / ".pcae" / "hatp-evidence").exists()

    def test_hatp_sign_cli_surface_exists_as_of_149o_12c(self):
        """Inverted by Phase 149O.12C (see module docstring): the
        `pcae hatp sign rollback` CLI surface now exists, exactly as
        149O.12B's own report recommended as the next phase's exclusive
        scope. `--hatp-evidence` (AG3/AG5 *consumption* wiring) remains
        absent -- that is still out of scope, deferred to 149O.14+."""

        result = subprocess.run(
            ["grep", "-rEn", "hatp sign|add_parser\\(.hatp.", "src/pcae/cli.py", "src/pcae/commands/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout != ""

        consumption_result = subprocess.run(
            ["grep", "-rn", "--hatp-evidence", "src/pcae/cli.py", "src/pcae/commands/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert consumption_result.stdout == "", "--hatp-evidence consumption wiring remains out of scope"

    def test_commands_hatp_module_exists(self):
        assert (REPO_ROOT / "src" / "pcae" / "commands" / "hatp.py").exists()

    def test_no_ag3_ag5_authority_wiring_introduced(self):
        """`hatp_ag_authority.py` must not reference this phase's new
        module -- AG3/AG5 consumption wiring remains out of scope."""

        result = subprocess.run(
            ["grep", "-l", "hatp_signing_ceremony", "src/pcae/core/hatp_ag_authority.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout == ""

    def test_no_permission_broker_import(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "import permission_broker" not in source
        assert "pcae.core.permission_broker" not in source

    def test_no_cryptographic_verification_call(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "verify_hatp_proof(" not in source
        assert "verify_hatp_proof," not in source
        assert " verify_hatp_proof\n" not in source

    def test_no_legacy_approval_state_mutation(self):
        """Never calls `approve_rollback`, never assigns
        `rollback_approval_state`, never writes job/PER status fields."""

        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "approve_rollback" not in source
        assert "rollback_approval_state" not in source
        assert "mark_promotion_execution_interrupted" not in source
        assert "_write_job(" not in source

    def test_no_rollback_dispatch_call(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "execute_rollback(" not in source
        assert "build_rollback_execution(" not in source
        assert "run_rollback(" not in source

    def test_no_approval_present_derivation(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "approval_present =" not in source
        assert "approval_present:" not in source


class TestNoAuthorityBearingFields:
    def test_preview_has_no_authority_bearing_field(self):
        from pcae.core.hatp_signing_ceremony import HATPSigningPreview

        field_names = {f.name for f in dataclasses.fields(HATPSigningPreview)}
        for forbidden in _FORBIDDEN_AUTHORITY_FIELD_NAMES:
            assert forbidden not in field_names

    def test_result_has_no_authority_bearing_field(self):
        from pcae.core.hatp_signing_ceremony import HATPSigningResult

        field_names = {f.name for f in dataclasses.fields(HATPSigningResult)}
        assert field_names == {"evidence_id", "path", "idempotent"}
        for forbidden in _FORBIDDEN_AUTHORITY_FIELD_NAMES:
            assert forbidden not in field_names

    def test_context_has_no_authority_bearing_field(self):
        from pcae.core.hatp_signing_ceremony import HATPRollbackSigningContext

        field_names = {f.name for f in dataclasses.fields(HATPRollbackSigningContext)}
        for forbidden in _FORBIDDEN_AUTHORITY_FIELD_NAMES:
            assert forbidden not in field_names


class TestProductionWrapperZeroOverride:
    """F-2 non-regression (mirrors `hatp_ag_authority.py`'s own
    zero-override production-adapter discipline): the production entry
    point must have zero overridable authority-bearing dependencies."""

    def test_production_wrapper_signature_has_no_override_parameters(self):
        from pcae.core.hatp_signing_ceremony import production_sign_rollback_evidence

        signature = inspect.signature(production_sign_rollback_evidence)
        forbidden_param_names = {
            "provider",
            "provider_factory",
            "trust_store",
            "trust_store_factory",
            "clock",
            "confirm",
            "store",
            "store_factory",
        }
        assert forbidden_param_names.isdisjoint(signature.parameters.keys())
        assert set(signature.parameters.keys()) == {"root", "site", "job_id", "per_id"}

    def test_production_wrapper_calls_core_function_with_no_overrides(self):
        """Static-source check: `production_sign_rollback_evidence`'s body
        never passes `provider_factory=`/`trust_store_factory=`/`clock=`/
        `confirm=` to `sign_rollback_evidence` -- it always relies on the
        core function's own production defaults."""

        from pcae.core.hatp_signing_ceremony import production_sign_rollback_evidence

        source = inspect.getsource(production_sign_rollback_evidence)
        body = source.split('"""', 2)[-1]
        for forbidden in ("provider_factory=", "trust_store_factory=", "clock=", "confirm=", "provider=", "trust_store="):
            assert forbidden not in body, f"production wrapper must not pass override {forbidden!r}"

    def test_core_function_default_factories_resolve_production_dependencies_only(self):
        """The core, test-injectable `sign_rollback_evidence`'s own
        *default* values must resolve exclusively through the Wave-5/
        Wave-2 production factories -- never a test/software provider."""

        import pcae.core.hatp_signing_ceremony as ceremony

        signature = inspect.signature(ceremony.sign_rollback_evidence)
        assert signature.parameters["provider_factory"].default is ceremony._default_provider_factory
        assert signature.parameters["trust_store_factory"].default is ceremony._default_trust_store_factory

        provider_factory_source = inspect.getsource(ceremony._default_provider_factory)
        assert "create_production_hardware_provider" in provider_factory_source
        assert "TestHATPProofVerifierProvider" not in provider_factory_source

        trust_store_factory_source = inspect.getsource(ceremony._default_trust_store_factory)
        assert "HATPTrustStore.production()" in trust_store_factory_source

    def test_no_test_provider_class_imported_or_referenced(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "TestHATPProofVerifierProvider" not in source


class TestPreviewBeforeTouchAndToctouOrdering:
    """Static structural checks complementing the dynamic ordering tests
    in `test_hatp_signing_ceremony.py::
    test_preview_shown_before_provider_touch_and_provider_called_exactly_once`
    and the TOCTOU discard tests."""

    def test_confirm_called_before_request_signature_in_source(self):
        import pcae.core.hatp_signing_ceremony as ceremony

        source = inspect.getsource(ceremony.sign_rollback_evidence)
        body = source.split('"""', 2)[-1]
        confirm_index = body.index("confirm(preview)")
        request_signature_index = body.index("provider.request_signature(")
        assert confirm_index < request_signature_index

    def test_toctou_recheck_occurs_after_request_signature_and_before_publish(self):
        import pcae.core.hatp_signing_ceremony as ceremony

        source = inspect.getsource(ceremony.sign_rollback_evidence)
        body = source.split('"""', 2)[-1]
        request_signature_index = body.index("provider.request_signature(")
        context_b_index = body.index("context_b = resolve_signing_context(")
        envelope_index = body.index("build_hatp_signed_evidence_envelope(")
        publish_index = body.index("store.publish(")
        assert request_signature_index < context_b_index < envelope_index < publish_index

    def test_resolve_signing_context_called_exactly_twice_in_source(self):
        import pcae.core.hatp_signing_ceremony as ceremony

        source = inspect.getsource(ceremony.sign_rollback_evidence)
        assert source.count("resolve_signing_context(") == 2

    def test_request_signature_called_exactly_once_in_source(self):
        import pcae.core.hatp_signing_ceremony as ceremony

        source = inspect.getsource(ceremony.sign_rollback_evidence)
        assert source.count("provider.request_signature(") == 1


class TestClosedErrorVocabulary:
    def test_every_exception_error_type_is_in_the_hsce_closed_vocabulary(self):
        import pcae.core.hatp_signing_ceremony as ceremony

        closed_vocabulary = {
            "repository_identity_unavailable",
            "operation_not_found",
            "decision_unavailable",
            "binding_unavailable",
            "no_authorized_signer",
            "provider_unavailable",
            "hardware_device_fault",
            "human_signing_cancelled",
            "provider_signature_failure",
            "evidence_serialization_failure",
            "evidence_conflict",
            "evidence_persistence_failure",
            "generic_signing_failure",  # base-class default, never raised bare
        }
        error_classes = [
            obj
            for _name, obj in vars(ceremony).items()
            if isinstance(obj, type)
            and issubclass(obj, ceremony.HATPSigningCeremonyError)
            and obj.__module__ == ceremony.__name__
        ]
        assert error_classes, "expected at least one HATPSigningCeremonyError subclass"
        for cls in error_classes:
            assert cls.error_type in closed_vocabulary, f"{cls.__name__}.error_type={cls.error_type!r} not in closed vocabulary"

    def test_no_hatp_verification_status_vocabulary_used(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "HATPVerificationStatus" not in source


class TestLazyImportDiscipline:
    def test_module_does_not_import_fido2_provider_at_top_level(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "import hatp_fido2_provider" not in source
        assert "pcae.core.hatp_fido2_provider" not in source

    def test_no_optional_hardware_dependency_named_at_top_level(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "import fido2" not in source
        assert "cryptography" not in source


class TestRequiredAttackSubsetCovered:
    """Confirms the 149O.11-plan-mandated resolver/orchestrator attack
    subset (16,17,18,19,20,21) is exercised somewhere in `test_hatp_
    signing_ceremony.py` -- a coarse presence check, not a
    re-implementation of those tests."""

    @pytest.mark.parametrize(
        "expected_marker",
        [
            "test_human_cancels_touch_no_evidence_persisted",  # 16
            "test_provider_unavailable_at_factory_time",  # 17
            "test_toctou_real_supersession_between_preview_and_touch",  # 18
            "test_no_matching_binding_is_binding_unavailable",  # 19
            "test_ag5_resolver_unresolvable_ecp_id_is_operation_not_found",  # 20
            "test_ag3_resolver_unresolvable_original_commit_sha_is_operation_not_found",  # 21
        ],
    )
    def test_marker_present(self, expected_marker):
        source = (REPO_ROOT / "tests" / "test_hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert f"def {expected_marker}" in source


class TestPython39Compatibility:
    def test_module_imports_without_syntax_error_on_this_interpreter(self):
        import pcae.core.hatp_signing_ceremony  # noqa: F401

    def test_no_optional_hardware_dependency_required_to_import(self):
        source = (REPO_ROOT / "src" / "pcae" / "core" / "hatp_signing_ceremony.py").read_text(encoding="utf-8")
        assert "import fido2" not in source

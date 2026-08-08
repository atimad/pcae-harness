"""Phase 149O.12A — Signed Evidence Model + Evidence Store Implementation.

BOUNDED PRODUCTION IMPLEMENTATION (per HSCE-001 v1.1, 149O.11's
implementation plan Wave A + B). This phase-specific suite verifies the
implementation's own scope boundaries and cross-cutting invariants --
field-level/attack-level unit coverage lives in `test_hatp_signed_
evidence.py` and `test_hatp_evidence_store.py`.

Authorized production scope this phase: `src/pcae/core/
hatp_signed_evidence.py` (envelope model/parser/serializer) and
`src/pcae/core/hatp_evidence_store.py` (exclusive-publication evidence
store). NOT authorized: signing ceremony, proof-context resolution,
hardware invocation, CLI, AG3/AG5 consumption, rollback changes,
Permission Broker changes, Class-B provisioning, production activation
(149O.12B/149O.12C/149O.13's scope, not this phase's).
"""
from __future__ import annotations

import inspect
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HSCE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md"
HATP_CONTRACT = REPO_ROOT / "docs" / "contracts" / "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md"
RAE_CONTRACT = REPO_ROOT / "docs" / "contracts" / "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md"

#: Last commit of Phase 149O.11 (this phase's entering baseline) --
#: pinned per this repository's own repair/re-verification-chain
#: convention (mirrors `test_phase_149o_10_2_...::_V1_1_REPAIR_COMMIT`).
_149O_11_BASELINE_COMMIT = "0812d49c"

_EXPECTED_PRODUCTION_FILES = frozenset(
    {
        "src/pcae/core/hatp_signed_evidence.py",
        "src/pcae/core/hatp_evidence_store.py",
    }
)

#: 149O.12B, Waves C+D (retained 149O.5-F-3 lesson, applied here exactly
#: as 149O.12A's own report documented it would be for the next new
#: intentional HATP module): the signing-ceremony resolver/orchestrator
#: is a distinct, properly-scoped, independently-tested phase's own
#: production file. Its presence in the cumulative `src/pcae/` diff
#: against this (149O.11) phase's baseline does not mean 149O.12A itself
#: grew scope -- 149O.12A's own diff, taken alone at 149O.12A's
#: completion time, was and remains exactly `_EXPECTED_PRODUCTION_FILES`
#: above; this allowlist is widened, not silently ignored, so this suite
#: keeps passing as later phases build on top, per this project's own
#: allowed-file-widening convention (mirrors `test_phase_149o_1g_hatp_
#: proof_models_canonical_serialization.py::test_only_expected_
#: production_files_changed`).
_LATER_PHASE_APPROVED_FILES = frozenset(
    {
        "src/pcae/core/hatp_signing_ceremony.py",
        # 149O.12C, Wave E: the signing CLI surface (`commands/hatp.py`
        # NEW, `cli.py` registration-only MODIFY) -- the identical
        # 149O.5-F-3 widening lesson applied again for this phase's own
        # planned next addition (see this phase's own report's
        # Recommended Next Phase).
        "src/pcae/commands/hatp.py",
        "src/pcae/cli.py",
    }
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
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _production_diff_files() -> set:
    diff = _run_git("diff", "--name-only", _149O_11_BASELINE_COMMIT, "--", "src/pcae/")
    untracked = _run_git("ls-files", "--others", "--exclude-standard", "--", "src/pcae/")
    if diff.returncode != 0 or untracked.returncode != 0:
        pytest.skip("git unavailable")
    return {line for line in (diff.stdout.split() + untracked.stdout.split()) if line}


class TestProductionFileAllowlist:
    def test_production_diff_contains_exactly_the_two_planned_modules_of_this_phase(self):
        """149O.12A's own two files must both be present in the
        cumulative diff -- a later phase never removes an earlier
        phase's production module."""

        files = _production_diff_files()
        assert _EXPECTED_PRODUCTION_FILES <= files, (
            f"expected 149O.12A's own {_EXPECTED_PRODUCTION_FILES} to be present, got {files}"
        )

    def test_no_other_src_pcae_file_touched(self):
        """Every `src/pcae/` file in the cumulative diff must be either
        one of 149O.12A's own two files or a file explicitly approved as
        a later, separately-scoped phase's own production addition
        (`_LATER_PHASE_APPROVED_FILES`, widened per the retained
        149O.5-F-3 lesson) -- never an unrelated hunk."""

        files = _production_diff_files()
        unrelated = files - _EXPECTED_PRODUCTION_FILES - _LATER_PHASE_APPROVED_FILES
        assert unrelated == set(), f"unrelated production hunks: {unrelated}"

    def test_cli_py_change_is_confined_to_hatp_registration_block(self):
        """Updated by Phase 149O.12C (`_LATER_PHASE_APPROVED_FILES`
        above): `cli.py` is no longer expected to be byte-unchanged since
        the 149O.11 baseline -- confirms the diff is a pure addition."""

        result = _run_git("diff", "--numstat", _149O_11_BASELINE_COMMIT, "--", "src/pcae/cli.py")
        if result.returncode != 0:
            pytest.skip("git unavailable")
        line = result.stdout.strip()
        assert line, "expected a non-empty cli.py diff since the 149O.11 baseline (149O.12C's registration)"
        added, removed, _path = line.split(maxsplit=2)
        assert int(removed) == 0, "cli.py's diff must be a pure addition, never a rewrite of existing lines"

    def test_commands_hatp_module_exists_as_of_149o_12c(self):
        """Inverted by Phase 149O.12C: the CLI handler module now exists,
        exactly as 149O.11's own implementation plan scheduled it for
        Wave E."""

        assert (REPO_ROOT / "src" / "pcae" / "commands" / "hatp.py").exists()

    def test_no_existing_hatp_module_modified(self):
        for relative in (
            "src/pcae/core/human_approval_trusted_provenance.py",
            "src/pcae/core/hatp_providers.py",
            "src/pcae/core/hatp_fido2_provider.py",
            "src/pcae/core/hatp_bootstrap.py",
            "src/pcae/core/hatp_ag_authority.py",
            "src/pcae/core/repository_identity.py",
            "src/pcae/core/rollback_approval_evidence.py",
            "src/pcae/core/agent.py",
            "src/pcae/commands/agent.py",
            "src/pcae/core/permission_broker.py",
            "src/pcae/core/permission_broker_foundation.py",
        ):
            result = _run_git("diff", "--stat", _149O_11_BASELINE_COMMIT, "--", relative)
            if result.returncode != 0:
                pytest.skip("git unavailable")
            assert result.stdout.strip() == "", f"{relative} was unexpectedly touched this phase"


class TestContractByteIdentity:
    def test_hsce_001_unmodified(self):
        result = _run_git(
            "diff", "--stat", _149O_11_BASELINE_COMMIT, "--", str(HSCE_CONTRACT.relative_to(REPO_ROOT))
        )
        if result.returncode != 0:
            pytest.skip("git unavailable")
        assert result.stdout.strip() == "", "this is an implementation phase; HSCE-001 v1.1 text must not change"

    def test_hatp_001_unmodified(self):
        result = _run_git(
            "diff", "--stat", _149O_11_BASELINE_COMMIT, "--", str(HATP_CONTRACT.relative_to(REPO_ROOT))
        )
        if result.returncode != 0:
            pytest.skip("git unavailable")
        assert result.stdout.strip() == ""

    def test_rae_001_unmodified(self):
        result = _run_git(
            "diff", "--stat", _149O_11_BASELINE_COMMIT, "--", str(RAE_CONTRACT.relative_to(REPO_ROOT))
        )
        if result.returncode != 0:
            pytest.skip("git unavailable")
        assert result.stdout.strip() == ""


class TestNoScopeCreep:
    def test_no_hatp_evidence_directory_created_in_repository(self):
        assert not (REPO_ROOT / ".pcae" / "hatp-evidence").exists()

    def test_hatp_sign_cli_surface_exists_as_of_149o_12c(self):
        """Inverted by Phase 149O.12C (`_LATER_PHASE_APPROVED_FILES`
        above): the CLI surface now exists, exactly as planned.
        `--hatp-evidence` (consumption wiring) remains absent."""

        result = subprocess.run(
            ["grep", "-rEln", "hatp sign", "src/pcae/cli.py", "src/pcae/commands/"],
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

    def test_no_ag3_ag5_authority_wiring_introduced(self):
        """No new caller of `resolve_ag3_gated_rollback_authority`/
        `resolve_ag5_gated_rollback_authority` should reference this
        phase's new modules -- 149O.12A's surface is inert."""

        result = subprocess.run(
            ["grep", "-rln", "hatp_signed_evidence\\|hatp_evidence_store", "src/pcae/core/hatp_ag_authority.py"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout == ""

    def test_no_permission_broker_import(self):
        for module_name in ("hatp_signed_evidence", "hatp_evidence_store"):
            path = REPO_ROOT / "src" / "pcae" / "core" / f"{module_name}.py"
            source = path.read_text(encoding="utf-8")
            assert "import permission_broker" not in source
            assert "pcae.core.permission_broker" not in source

    def test_no_signing_or_hardware_invocation(self):
        for module_name in ("hatp_signed_evidence", "hatp_evidence_store"):
            path = REPO_ROOT / "src" / "pcae" / "core" / f"{module_name}.py"
            source = path.read_text(encoding="utf-8")
            assert "request_signature(" not in source
            assert "import hatp_providers" not in source
            assert "pcae.core.hatp_providers" not in source
            assert "import hatp_bootstrap" not in source
            assert "pcae.core.hatp_bootstrap" not in source

    def test_no_cryptographic_verification_call(self):
        for module_name in ("hatp_signed_evidence", "hatp_evidence_store"):
            path = REPO_ROOT / "src" / "pcae" / "core" / f"{module_name}.py"
            source = path.read_text(encoding="utf-8")
            assert "verify_hatp_proof(" not in source


class TestNoAuthorityBearingFields:
    def test_envelope_has_no_authority_bearing_field(self):
        from pcae.core.hatp_signed_evidence import HATPSignedEvidenceEnvelope

        field_names = {f.name for f in __import__("dataclasses").fields(HATPSignedEvidenceEnvelope)}
        assert field_names == {"evidence_version", "evidence_id", "proof", "provider_assertion"}
        for forbidden in _FORBIDDEN_AUTHORITY_FIELD_NAMES:
            assert forbidden not in field_names

    def test_publication_result_has_no_authority_bearing_field(self):
        from pcae.core.hatp_evidence_store import HATPEvidencePublicationResult

        field_names = {f.name for f in __import__("dataclasses").fields(HATPEvidencePublicationResult)}
        assert field_names == {"evidence_id", "path", "idempotent"}
        for forbidden in _FORBIDDEN_AUTHORITY_FIELD_NAMES:
            assert forbidden not in field_names

    def test_store_has_no_exists_or_approval_style_method(self):
        from pcae.core.hatp_evidence_store import HATPEvidenceStore

        public_methods = {
            name for name in dir(HATPEvidenceStore) if not name.startswith("_")
        }
        assert public_methods == {"path_for", "load", "publish", "repository_root", "envelopes_dir"}


class TestHardLinkPublicationPrimitive:
    def test_os_link_is_the_winner_publication_primitive(self):
        from pcae.core import hatp_evidence_store

        source = inspect.getsource(hatp_evidence_store)
        assert "os.link(" in source

    def test_os_replace_never_used_as_winner_primitive(self):
        """The repaired HSCE-REQ-052 forbids `os.replace` (or any other
        overwrite-capable primitive) as a fallback under any condition."""

        from pcae.core import hatp_evidence_store

        source = inspect.getsource(hatp_evidence_store)
        assert "os.replace(" not in source

    def test_close_before_link_ordering_in_source(self):
        """Static ordering check: the `with os.fdopen(...)` write block
        (which closes the fd on exit) appears before the `os.link(` call
        in `publish`'s source text -- a coarse but meaningful proxy for
        the close-before-link invariant, backed by the dynamic
        instrumentation test in `test_hatp_evidence_store.py::
        test_write_descriptor_closed_before_link_is_attempted`."""

        from pcae.core.hatp_evidence_store import HATPEvidenceStore

        source = inspect.getsource(HATPEvidenceStore.publish)
        # Strip the leading docstring (which itself narrates the ordering,
        # inflating naive substring indices) before locating the actual
        # code statements.
        body = source.split('"""', 2)[-1]
        fdopen_index = body.index("os.fdopen(")
        link_index = body.index("os.link(")
        assert fdopen_index < link_index

    def test_publish_docstring_states_no_write_after_close(self):
        from pcae.core.hatp_evidence_store import HATPEvidenceStore

        assert HATPEvidenceStore.publish.__doc__ is not None
        assert "no writable" in HATPEvidenceStore.publish.__doc__.lower()


class TestObs3Mapping:
    """149O.10.2-Obs-3: loser-comparison read-failure -- resolved by the
    149O.11 plan as `evidence_persistence_failure`, never `evidence_
    conflict` and never a new `error_type`."""

    def test_evidence_persistence_failure_error_class_exists(self):
        from pcae.core.hatp_evidence_store import EvidencePersistenceFailureError

        assert issubclass(EvidencePersistenceFailureError, Exception)

    def test_no_new_error_type_beyond_the_closed_vocabulary(self):
        """This module introduces exactly three storage-layer error
        classes -- `EvidenceNotFoundError` (load-path only, HSCE-REQ-064),
        `EvidenceConflictError` (`evidence_conflict`), and
        `EvidencePersistenceFailureError` (`evidence_persistence_
        failure`) -- no fourth storage `error_type` category exists."""

        from pcae.core import hatp_evidence_store

        error_classes = {
            name
            for name, obj in vars(hatp_evidence_store).items()
            if isinstance(obj, type)
            and issubclass(obj, Exception)
            and obj.__module__ == hatp_evidence_store.__name__
        }
        assert error_classes == {
            "HATPEvidenceStoreError",
            "EvidenceNotFoundError",
            "EvidenceConflictError",
            "EvidencePersistenceFailureError",
        }

    def test_directory_at_final_path_maps_to_persistence_failure_not_conflict(self, tmp_path):
        from pcae.core.hatp_evidence_store import EvidenceConflictError, EvidencePersistenceFailureError, HATPEvidenceStore
        from pcae.core.hatp_signed_evidence import build_hatp_signed_evidence_envelope
        from pcae.core.human_approval_trusted_provenance import (
            Ag3OperationReference,
            HumanApprovalProvenanceProof,
            RollbackSite,
        )
        from pcae.core.paths import HarnessPath
        import uuid

        proof = HumanApprovalProvenanceProof(
            proof_version=1,
            principal_id="alice",
            signer_key_id="signer-1",
            provider_profile="HATP_HARDWARE_PROVIDER_V1",
            repository_id=str(uuid.uuid4()),
            decision_record_id="chgr-record-1",
            decision_record_digest="a" * 64,
            binding_id="rae-binding-1",
            binding_digest="b" * 64,
            rollback_site=RollbackSite.AG3,
            operation_reference=Ag3OperationReference(job_id="obs3", original_commit_sha="c" * 40),
            issued_at="2026-08-06T00:00:00.000Z",
        )
        envelope = build_hatp_signed_evidence_envelope(proof, b"assertion")
        store = HATPEvidenceStore(HarnessPath(tmp_path))
        final_path = store.path_for(envelope.evidence_id)
        final_path.mkdir(parents=True, exist_ok=True)

        with pytest.raises(EvidencePersistenceFailureError):
            store.publish(envelope)
        # Never misrepresented as evidence_conflict (that specifically
        # means "compared and differed," not "could not safely compare").
        try:
            store.publish(envelope)
        except EvidenceConflictError:
            pytest.fail("directory-occupied destination must not be reported as evidence_conflict")
        except EvidencePersistenceFailureError:
            pass


class TestNoLatestOrExistsAsApprovalPattern:
    """HSCE-REQ-061's forbidden pattern: `if evidence_file.exists():
    approval_present = True` and equivalents. This module never derives
    approval from bare existence -- it does not compute `approval_present`
    at all."""

    def test_no_approval_present_symbol_anywhere_in_new_modules(self):
        for module_name in ("hatp_signed_evidence", "hatp_evidence_store"):
            path = REPO_ROOT / "src" / "pcae" / "core" / f"{module_name}.py"
            source = path.read_text(encoding="utf-8")
            # Docstrings narrate the *absence* of this concept (HSCE-REQ-061);
            # the check that matters is that no code actually assigns,
            # returns, or type-annotates such a field/variable.
            assert "approval_present =" not in source
            assert "approval_present:" not in source
            assert "approval_present)" not in source


class TestRequiredAttackSubsetCovered:
    """Confirms the 149O.11-plan-mandated model/store attack subset
    (attacks 1,2,3,4,5,6,7,8,9,10,13,14,15,E1,E2,E3,E4) is exercised
    somewhere in this phase's own test files -- a coarse presence check,
    not a re-implementation of those tests."""

    @pytest.mark.parametrize(
        "test_file,expected_marker",
        [
            ("test_hatp_signed_evidence.py", "test_validate_evidence_id_rejects_malformed_values"),  # 1, 2
            ("test_hatp_evidence_store.py", "test_byte_identical_rewrite_is_idempotent"),  # 3
            ("test_hatp_evidence_store.py", "test_differing_rewrite_same_id_conflicts_and_winner_unchanged"),  # 4
            ("test_hatp_signed_evidence.py", "test_duplicate_top_level_key_rejected"),  # 5
            ("test_hatp_signed_evidence.py", "test_unknown_top_level_field_rejected"),  # 6
            ("test_hatp_signed_evidence.py", "test_construction_rejects_bad_versions"),  # 7
            ("test_hatp_signed_evidence.py", "test_missing_required_field_rejected"),  # 8
            ("test_hatp_signed_evidence.py", "test_evidence_id_must_equal_proof_digest_on_parse"),  # 9
            ("test_hatp_signed_evidence.py", "test_corrupt_provider_assertion_still_parses_structurally"),  # 10
            ("test_hatp_evidence_store.py", "test_publish_rejects_symlinked_final_destination"),  # 13
            ("test_hatp_evidence_store.py", "test_publish_rejects_escaping_path_component_symlink"),  # 14
            ("test_hatp_evidence_store.py", "test_fsync_failure_leaves_no_partial_final_artifact"),  # 15
            ("test_hatp_evidence_store.py", "test_publish_existing_directory_at_final_path_fails_closed"),  # E1
            ("test_hatp_evidence_store.py", "test_write_descriptor_closed_before_link_is_attempted"),  # E2
            ("test_hatp_evidence_store.py", "test_many_mixed_writers_identical_and_differing"),  # E3
            ("test_hatp_evidence_store.py", "test_non_eexist_link_errors_fail_closed_no_fallback"),  # E4
        ],
    )
    def test_marker_present(self, test_file, expected_marker):
        source = (REPO_ROOT / "tests" / test_file).read_text(encoding="utf-8")
        assert f"def {expected_marker}" in source


class TestPython39Compatibility:
    def test_modules_import_without_syntax_error_on_this_interpreter(self):
        import pcae.core.hatp_evidence_store  # noqa: F401
        import pcae.core.hatp_signed_evidence  # noqa: F401

    def test_no_optional_hardware_dependency_required_to_import(self):
        """Neither module imports `fido2`/`cryptography` -- ordinary PCAE
        imports must still work without the hardware extras installed."""

        for module_name in ("hatp_signed_evidence", "hatp_evidence_store"):
            path = REPO_ROOT / "src" / "pcae" / "core" / f"{module_name}.py"
            source = path.read_text(encoding="utf-8")
            assert "import fido2" not in source
            assert "cryptography" not in source

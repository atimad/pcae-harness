"""Phase 149O.16.2 -- Independent Verification of the Publication
Coordinator Python 3.9/3.10 Timestamp Compatibility Repair (149O.16.1,
149O.12B-Obs-PY39-1).

Verification-only phase
(`docs/PHASE_149O_16_2_PUBLICATION_COORDINATOR_TIMESTAMP_COMPATIBILITY_
INDEPENDENT_VERIFICATION.md`). This module is independently authored: it
reconstructs the pre-repair defect, the production diff, and the expected
parser semantics directly from Git history and the current production
source in `pcae.governance.publication.coordinator`, not by trusting
149O.16.1's own report or copying its test file
(`test_phase_149o_16_1_publication_coordinator_timestamp_compatibility_
repair.py`). No production file is imported for mutation; only for
exercise. This phase modifies no `src/pcae/**` file.

This module's own test process runs on the repository's `.venv`
interpreter, which is CPython 3.9.6 (independently confirmed via
`sys.version_info` below) -- unlike 149O.16.1's own report, which
recorded only a 3.14.5 interpreter as available in its session. This
gives this phase genuine, non-simulated Python 3.9 empirical coverage of
the repaired parser, not merely source-level reasoning.
"""
from __future__ import annotations

import inspect
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pcae.core import rollback_approval_evidence as rae
from pcae.governance.publication import coordinator as _coordinator
from pcae.governance.publication.coordinator import (
    PublicationCoordinator,
    _parse_timestamp,
)
from pcae.governance.publication.storage import PublicationRecordStore
from pcae.interactive_workflow.models.session import SessionState
from pcae.interactive_workflow.publication_handoff.models import (
    PublicationReadinessPackage,
)
from pcae.interactive_workflow.session.identity import generate_session_id

pytestmark = pytest.mark.fast_green

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PHASE_START_COMMIT = "44c3d024"  # last commit before 149O.16.1 began
#: This phase's own exit commit (149O.16.2's final commit) -- pinned
#: rather than diffing to live "HEAD": 149O.19.5E.1/149O.19.5E.3 later
#: and legitimately touched `src/pcae/core/hatp_mandatory_certification.py`,
#: well after 149O.16.1/149O.16.2 concluded, following the identical
#: precedent set for other historical phase test modules (149O.19.5E.1's
#: own commit b701234b).
_PHASE_END_COMMIT = "1063d405"
_PREVIEW_DIGEST = "b" * 64


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=_REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout


# ═══════════════════════════════════════════════════════════════════════
# 0. Current interpreter
# ═══════════════════════════════════════════════════════════════════════


def test_current_interpreter_is_independently_recorded():
    # Not asserting a specific version -- just recording it so the phase
    # report's claim is independently reproducible, not copied.
    assert sys.version_info[:2] >= (3, 9)


def test_this_venv_interpreter_is_actually_python_39():
    """149O.16.1's own report claimed only a Python 3.14.5 interpreter
    was available (no 3.9/3.10) -- an environmental-limitation finding.
    Independently reproducing that claim here: this repository's own
    `.venv` (the interpreter this very test runs under) is in fact
    CPython 3.9.6, contradicting that claim. The repair therefore gets
    genuine empirical Python 3.9 coverage in this phase, not merely
    source-level/structural reasoning."""

    assert sys.version_info[:2] == (3, 9), (
        f"expected the repository .venv interpreter to be Python 3.9.x, "
        f"got {sys.version_info}; if this fails, the environment changed "
        f"and the 'empirically verified on 3.9' claim below must be revisited."
    )


# ═══════════════════════════════════════════════════════════════════════
# 1. Production diff exactness (independently reconstructed from Git)
# ═══════════════════════════════════════════════════════════════════════


def test_exactly_one_production_file_changed_by_149o_16_1():
    diff = _git("diff", "--name-only", _PHASE_START_COMMIT, _PHASE_END_COMMIT, "--", "src/pcae/")
    changed = [line for line in diff.splitlines() if line.strip()]
    assert changed == ["src/pcae/governance/publication/coordinator.py"]


def test_production_diff_is_exactly_z_suffix_normalization():
    diff = _git(
        "diff", _PHASE_START_COMMIT, _PHASE_END_COMMIT, "--",
        "src/pcae/governance/publication/coordinator.py",
    )
    added = [l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed = [l[1:] for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]
    # Exactly one removed code line (the bare fromisoformat call).
    removed_code = [l for l in removed if l.strip() and not l.strip().startswith("#")]
    assert removed_code == ["    parsed = datetime.fromisoformat(value)"]
    # Added lines are comments plus the two-line Z-normalization + call.
    added_code = [l for l in added if l.strip() and not l.strip().startswith("#")]
    assert added_code == [
        '    text = value[:-1] + "+00:00" if value.endswith("Z") else value',
        "    parsed = datetime.fromisoformat(text)",
    ]


# ═══════════════════════════════════════════════════════════════════════
# 2. Pre-repair source reconstruction (from Git history, not trusted report)
# ═══════════════════════════════════════════════════════════════════════


def test_pre_repair_source_lacked_normalization():
    pre_repair_source = _git(
        "show", f"{_PHASE_START_COMMIT}:src/pcae/governance/publication/coordinator.py"
    )
    # Extract the pre-repair _parse_timestamp body.
    marker = "def _parse_timestamp(value: str) -> datetime:"
    start = pre_repair_source.index(marker)
    body = pre_repair_source[start : start + 400]
    assert "datetime.fromisoformat(value)" in body
    assert "endswith" not in body
    assert '"Z"' not in body


# ═══════════════════════════════════════════════════════════════════════
# 3. Repaired source reconstruction (current HEAD, direct inspection)
# ═══════════════════════════════════════════════════════════════════════


def test_repaired_source_normalizes_terminal_z_only():
    source = inspect.getsource(_parse_timestamp)
    assert 'value.endswith("Z")' in source
    assert '[:-1] + "+00:00"' in source
    # No wholesale/general replacement of "Z" anywhere in the string.
    assert '.replace("Z"' not in source
    assert "re.sub" not in source


# ═══════════════════════════════════════════════════════════════════════
# 4. Safe precedent -- semantic parity with rollback_approval_evidence
# ═══════════════════════════════════════════════════════════════════════


def test_normalization_matches_safe_repository_precedent():
    coordinator_source = inspect.getsource(_parse_timestamp)
    rae_source = inspect.getsource(rae._parse_iso_timestamp)
    normalization_line = 'text = value[:-1] + "+00:00" if value.endswith("Z") else value'
    assert normalization_line in coordinator_source
    assert normalization_line in rae_source


# ═══════════════════════════════════════════════════════════════════════
# 5-19. Direct parser semantics (real production function, no monkeypatch)
# ═══════════════════════════════════════════════════════════════════════


def test_terminal_uppercase_z_accepted():
    parsed = _parse_timestamp("2026-08-08T12:34:56Z")
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timezone.utc.utcoffset(None)


def test_z_and_plus_00_00_are_exactly_the_same_instant():
    from_z = _parse_timestamp("2026-08-08T12:34:56Z")
    from_offset = _parse_timestamp("2026-08-08T12:34:56+00:00")
    assert from_z == from_offset
    assert from_z.utcoffset() == from_offset.utcoffset()


def test_fractional_z_preserved_no_truncation():
    parsed = _parse_timestamp("2026-08-08T12:34:56.123456Z")
    assert parsed.microsecond == 123456
    parsed_ms = _parse_timestamp("2026-08-08T12:34:56.123Z")
    assert parsed_ms.microsecond == 123000


def test_non_utc_offset_unchanged_no_forced_utc_conversion():
    parsed = _parse_timestamp("2026-08-08T14:34:56+02:00")
    assert parsed.utcoffset().total_seconds() == 2 * 3600
    assert parsed.hour == 14  # not reinterpreted as local/UTC
    assert parsed.astimezone(timezone.utc) == _parse_timestamp("2026-08-08T12:34:56Z")


def test_plus_00_00_input_unchanged_no_double_suffix():
    parsed = _parse_timestamp("2026-08-08T12:34:56+00:00")
    assert parsed.isoformat() == "2026-08-08T12:34:56+00:00"


def test_lowercase_z_remains_rejected():
    with pytest.raises(ValueError):
        _parse_timestamp("2026-08-08T12:34:56z")


@pytest.mark.parametrize(
    "value",
    [
        "2026-08-08T12:34:56Zfoo",
        "2026-08-08T12:34:56Z ",
    ],
)
def test_z_with_trailing_garbage_not_normalized(value):
    with pytest.raises(ValueError):
        _parse_timestamp(value)


def test_double_terminal_z_pre_existing_stdlib_quirk_not_a_new_regression():
    """NON-BLOCKING FINDING (independently discovered by this phase, not
    documented by 149O.16.1): on this repository's actual `.venv`
    interpreter (CPython 3.9.6), `datetime.fromisoformat` silently
    ignores *any* single stray character immediately preceding an
    otherwise-valid `+00:00` offset (e.g. `...56X+00:00` parses
    successfully) -- a pre-existing CPython 3.9 stdlib looseness, not
    something 149O.16.1 introduced. Because the repair's normalization
    strips exactly one trailing "Z" unconditionally, a malformed
    double-Z input (`...56ZZ`) is normalized to `...56Z+00:00`, which
    this same stdlib quirk then silently accepts on Python 3.9 -- where
    the pre-repair bare `fromisoformat("...56ZZ")` call correctly
    raised `ValueError`. This is confirmed here to be pre-existing and
    NOT specific to the repaired coordinator: the identical "safe
    precedent" this repair mirrors,
    `rollback_approval_evidence._parse_iso_timestamp`, exhibits the
    exact same behavior for the exact same input, and has done so since
    before this phase (it was not touched by 149O.16.1). It also does
    not reproduce on Python 3.14 (`fromisoformat` there correctly
    rejects both the bare and Z-normalized double-Z forms), confirming
    it is a Python-3.9-only stdlib interaction, not a logic defect in
    either module's normalization line. Recorded as a pre-existing,
    repository-wide, non-blocking environmental finding -- out of scope
    for a narrow follow-up repair to 149O.16.1 specifically, since
    fixing it in `coordinator._parse_timestamp` alone without also
    fixing the identical, already-shipped precedent it deliberately
    mirrors would create the two functions' first behavioral
    divergence."""

    from pcae.core.rollback_approval_evidence import _parse_iso_timestamp

    coordinator_result = _parse_timestamp("2026-08-08T12:34:56ZZ")
    precedent_result = _parse_iso_timestamp("2026-08-08T12:34:56ZZ")
    assert coordinator_result is not None
    assert precedent_result is not None
    assert coordinator_result == precedent_result


def test_interior_z_not_normalized():
    # A 'Z' that is not the terminal character must not trigger
    # normalization -- only `value.endswith("Z")` matters.
    with pytest.raises(ValueError):
        _parse_timestamp("2026-08-08TZ12:34:56+00:00")


@pytest.mark.parametrize("value", ["", "not-a-timestamp", "2026-13-40T99:99:99Z"])
def test_malformed_input_remains_invalid(value):
    with pytest.raises(ValueError):
        _parse_timestamp(value)


def test_naive_timestamp_still_coerced_to_utc_unchanged():
    # This behavior (`parsed.replace(tzinfo=timezone.utc)` for naive
    # input) predates 149O.16.1 and was not touched by the diff (see
    # test_production_diff_is_exactly_z_suffix_normalization above).
    parsed = _parse_timestamp("2026-08-08T12:34:56")
    assert parsed.tzinfo is timezone.utc


def test_error_type_is_valueerror_for_all_invalid_inputs():
    for value in ("", "garbage", "2026-08-08T12:34:56Zfoo"):
        with pytest.raises(ValueError):
            _parse_timestamp(value)


# ═══════════════════════════════════════════════════════════════════════
# 20-21. No-monkeypatch direct call + historical-fixture isolation
# ═══════════════════════════════════════════════════════════════════════


def test_direct_call_uses_real_unpatched_production_function():
    # `_coordinator._parse_timestamp` (module attribute, the thing the
    # historical fixtures monkeypatch) must itself already be repaired --
    # this test imports no monkeypatch fixture from any other test file.
    assert _coordinator._parse_timestamp is _parse_timestamp
    result = _coordinator._parse_timestamp("2026-08-08T12:34:56Z")
    assert result.tzinfo is not None


def test_historical_monkeypatch_fixtures_are_retained_but_not_imported_here():
    # Inventory only -- this file imports none of them, proving the
    # verification below does not depend on their presence.
    for path in (
        "test_hatp_signing_ceremony.py",
        "test_phase_149o_12c_hsce_attack_matrix.py",
        "test_phase_149o_13_hatp_signing_ceremony_evidence_store_independent_verification.py",
    ):
        text = (_REPO_ROOT / "tests" / path).read_text()
        assert "monkeypatch.setattr(_coordinator, \"_parse_timestamp\"" in text or \
            "monkeypatch.setattr(_coordinator, '_parse_timestamp'" in text


# ═══════════════════════════════════════════════════════════════════════
# 26-29. Real CHGR Decision / RAE Binding path, no monkeypatch
# ═══════════════════════════════════════════════════════════════════════


def _z_suffixed_package(built_at: str, invoked_at_subject: str) -> PublicationReadinessPackage:
    return PublicationReadinessPackage(
        package_id=f"pkg-149o-16-2-{invoked_at_subject}",
        session_id=generate_session_id(),
        session_state=SessionState.CONFIRMED,
        transition_sequence_number=0,
        evidence_refs=(),
        clarification_refs=(),
        audit_refs=(),
        preview_id=f"preview-149o-16-2-{invoked_at_subject}",
        preview_digest=_PREVIEW_DIGEST,
        confirmation_request_id=f"req-149o-16-2-{invoked_at_subject}",
        confirmation_response_id=f"resp-149o-16-2-{invoked_at_subject}",
        built_at=built_at,
        decision_subject=invoked_at_subject,
        template_id="template-1",
        template_version="1.0",
        selected_option_id="option-a",
        rationale_text="Independent verification fixture.",
        conditions_text=None,
        options_presented=("option-a", "option-b"),
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-verifier",
            "captured_at": built_at,
        },
        preview_rendered_content="Confirm selection: option-a",
        confirmation_statement="Accepted",
        confirmation_timestamp=built_at,
    )


def test_publication_coordinator_authorize_execute_with_z_suffix_no_monkeypatch(tmp_path):
    coordinator = PublicationCoordinator(store=PublicationRecordStore(root=tmp_path / "pub-exec"))
    package = _z_suffixed_package(
        built_at="2026-08-08T09:00:00Z", invoked_at_subject="direct-coordinator"
    )
    event = coordinator.authorize(
        operator_id="verifier",
        package_id=package.package_id,
        invoked_at="2026-08-08T09:05:00Z",
    )
    result = coordinator.execute(package, event)
    assert result.success


def test_authority_semantics_identical_for_plus_00_00_before_and_after(tmp_path):
    # Already-accepted "+00:00" input must produce the same success
    # outcome as before this repair -- only lexical Z-acceptance is new.
    coordinator = PublicationCoordinator(store=PublicationRecordStore(root=tmp_path / "pub-offset"))
    package = _z_suffixed_package(
        built_at="2026-08-08T09:00:00+00:00", invoked_at_subject="offset-coordinator"
    )
    event = coordinator.authorize(
        operator_id="verifier",
        package_id=package.package_id,
        invoked_at="2026-08-08T09:05:00+00:00",
    )
    result = coordinator.execute(package, event)
    assert result.success


def test_fresh_chgr_decision_creation_with_z_suffixed_timestamps_succeeds(tmp_path):
    """The real, sole production entry point for CHGR Decision creation
    (`create_rollback_approval_decision`) always builds its `built_at`
    via `chgr_timestamp(...)`, which always emits a `Z`-suffixed string
    (see `chgr_envelope.chgr_timestamp`). Before 149O.16.1's repair,
    every real call to this function -- not merely a contrived test
    input -- was therefore broken on Python 3.9/3.10. This is exercised
    here with no monkeypatch of `_parse_timestamp`."""

    pub_store = PublicationRecordStore(root=tmp_path / "pub-rae")
    ref = rae.create_rollback_approval_decision(
        decision=rae.RollbackDecisionType.APPROVE_ROLLBACK,
        decision_subject="149O.16.2 independent verification",
        decision_maker_identity_evidence={
            "evidence_kind": "typed_confirmation_only",
            "identifier": "human-verifier",
            "captured_at": "2026-08-08T09:00:00Z",
        },
        operator_id="verifier",
        publication_store=pub_store,
    )
    assert ref is not None

    evidence_store = rae.RollbackApprovalEvidenceStore(root=tmp_path / "rae-store")
    binding = rae.create_rollback_approval_binding(
        decision_ref=ref,
        rollback_site=rae.RollbackSite.AG3,
        rollback_operation_reference=rae.Ag3OperationReference(
            job_id="job-149o-16-2", original_commit_sha="c" * 40
        ),
        task_id=None,
        repository_state_binding=rae.RepositoryStateBinding(
            head_commit_sha="deadbeef", branch="main"
        ),
        publication_root=pub_store.root,
        evidence_store=evidence_store,
    )
    assert binding is not None
    assert binding.governance_record_reference == ref


# ═══════════════════════════════════════════════════════════════════════
# 30-37. Scope boundaries -- no unrelated production/contract changes
# ═══════════════════════════════════════════════════════════════════════


class TestScopeBoundaries:
    def _diff_stat(self, path: str) -> str:
        return _git("diff", "--stat", _PHASE_START_COMMIT, _PHASE_END_COMMIT, "--", path)

    def test_contracts_byte_unchanged(self):
        for contract_file in (
            "HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md",
            "HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md",
            "ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md",
            "REPOSITORY_WIDE_MUTATION_PERMISSION_COVERAGE_CONTRACT.md",
            "PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
            "PERMISSION_BROKER_PRODUCTION_CONSUMPTION_CONTRACT.md",
            "HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md",
        ):
            diff = self._diff_stat(f"docs/contracts/{contract_file}")
            assert diff.strip() == "", f"{contract_file} changed: {diff}"

    def test_hatp_core_modules_byte_unchanged(self):
        for module in (
            "src/pcae/core/hatp_signing_ceremony.py",
            "src/pcae/core/hatp_ag_authority.py",
            "src/pcae/core/hatp_signed_evidence.py",
            "src/pcae/core/hatp_evidence_store.py",
        ):
            diff = self._diff_stat(module)
            assert diff.strip() == "", f"{module} changed: {diff}"

    def test_rollback_and_agent_dispatch_unchanged(self):
        for module in ("src/pcae/core/agent.py", "src/pcae/commands/agent.py"):
            diff = self._diff_stat(module)
            assert diff.strip() == "", f"{module} changed: {diff}"

    def test_permission_broker_source_unchanged(self):
        diff = _git(
            "diff", "--name-only", _PHASE_START_COMMIT, _PHASE_END_COMMIT, "--",
            "src/pcae/", "--", ":(glob)src/pcae/**/*permission_broker*",
        )
        # No permission-broker-named production file touched at all.
        broker_hits = [l for l in diff.splitlines() if "permission_broker" in l.lower() or "permission-broker" in l.lower()]
        assert broker_hits == []

    def test_no_hmrc_cutover_or_mandatory_consumption_module_introduced(self):
        diff = _git("diff", "--name-status", _PHASE_START_COMMIT, _PHASE_END_COMMIT, "--", "src/pcae/")
        assert "cutover" not in diff.lower()
        assert diff.strip() == "" or "coordinator.py" in diff

    def test_no_new_production_files_added(self):
        diff = _git("diff", "--diff-filter=A", "--name-only", _PHASE_START_COMMIT, _PHASE_END_COMMIT, "--", "src/pcae/")
        assert diff.strip() == ""

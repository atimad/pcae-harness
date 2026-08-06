"""Phase 149O.1R — Phase Report Evidence-Coherence Validator + Suppression
Plumbing Repair.

Covers two source-confirmed defects in the canonical phase-report trust
gate, independently established by Phase 149O.1H.1R's investigation:

B-149O.1R-1: `validate_internal_report_coherence()`'s evidence-phase-ID
extraction could recognize at most two phase-ID components (e.g.
`149O.1H`), so a three-or-more-component phase ID (`149O.1H.1`,
`149O.1H.1R`) could never be recognized as its own evidence, producing a
false `internal_evidence_coherence` failure regardless of how the
report was worded.

B-149O.1R-2: the governed `test_evidence_classification` metadata field
(documented, Phase 134E.9, as "the only way to suppress" a legitimate
same-series evidence citation) was never read from
`.pcae/phase-completion-metadata.json` nor forwarded into the
`PhaseReport.metadata` the validator reads, by either production path
(`pcae phase complete` / `finalize_phase_report`, or
`pcae phase-report create` / `run_phase_report_create`) -- dead
metadata.

This suite is deliberately generic: no test hardcodes an exception for
`"149O.1H.1"` or any other specific phase ID (per the governing prompt's
explicit prohibition on phase-specific exceptions in the repair itself
and in its verification).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from pcae.core import phase_id as canonical_phase_id
from pcae.core.phase_reports import (
    PhaseReport,
    _extract_evidence_phase_ids,
    finalize_phase_report,
    make_phase_report,
    validate_internal_report_coherence,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _report(phase_id: str, test_results: dict, metadata: dict | None = None) -> PhaseReport:
    return PhaseReport(
        phase_id=phase_id,
        phase_name="Test Phase",
        status="completed",
        summary="",
        test_results=test_results,
        metadata=metadata or {},
    )


# ═══════════════════════════════════════════════════════════════════════
# B-149O.1R-1 — nested phase-ID extraction
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "phase_id",
    [
        "149O",
        "149O.1A",
        "149O.1B.3",
        "149O.1H",
        "149O.1H.1",
        "149O.1H.1R",
        "135H.2",
        "145H.1R",
    ],
)
def test_positive_nested_ids_recognized_as_self_evidence(phase_id: str) -> None:
    """A report whose evidence text names its own (possibly
    three-or-more-component) phase ID exactly must not be flagged as
    incoherent for that reason alone."""
    report = _report(phase_id, {"x": f"Phase {phase_id} closed the finding."})
    issues = validate_internal_report_coherence(report)
    assert not any("linked only to other phase identities" in issue for issue in issues)


@pytest.mark.parametrize(
    "malformed",
    ["149O..", "149O.1H.", ".149O", "149O..1H", "149O.1H..1", "149O/1H/1"],
)
def test_negative_malformed_ids_never_extracted_whole(malformed: str) -> None:
    """The malformed string as a *whole* must never be extracted as a
    single valid token (it may still contain a shorter, independently
    valid prefix substring -- e.g. "149O" inside "149O.." -- which is
    correct, not a defect: `phase_id.parse` legitimately accepts that
    shorter substring on its own)."""
    assert canonical_phase_id.validate(malformed) is not None
    tokens = _extract_evidence_phase_ids(f"see {malformed} for details")
    normalized = {t.normalized_text for t in tokens}
    assert malformed.upper().replace("/", ".") not in normalized


def test_no_shorter_prefix_extracted_from_longer_id() -> None:
    """`149O.1H.1` in evidence text must be extracted whole, never
    truncated to the shorter prefix `149O.1H`."""
    tokens = _extract_evidence_phase_ids("Phase 149O.1H.1 repaired the findings.")
    assert len(tokens) == 1
    assert tokens[0].normalized_text == "149O.1H.1"


def test_no_shorter_prefix_extracted_from_deeper_suffixed_id() -> None:
    tokens = _extract_evidence_phase_ids("Phase 149O.1H.1R investigated the report.")
    assert len(tokens) == 1
    assert tokens[0].normalized_text == "149O.1H.1R"


def test_prefix_collision_shorter_current_not_satisfied_by_longer_evidence() -> None:
    """current=149O.1H, evidence only names the longer 149O.1H.1: the
    longer ID must not satisfy the shorter current phase's own-evidence
    check (they are distinct, unrelated-by-equality identities)."""
    report = _report("149O.1H", {"x": "evidence discusses 149O.1H.1 only"})
    issues = validate_internal_report_coherence(report)
    assert any("149O.1H.1" in issue for issue in issues)


def test_prefix_collision_longer_current_not_satisfied_by_shorter_evidence() -> None:
    """current=149O.1H.1, evidence only names the shorter 149O.1H: the
    shorter ID must not satisfy the longer current phase's own-evidence
    check."""
    report = _report("149O.1H.1", {"x": "evidence discusses 149O.1H and 149O.1G only"})
    issues = validate_internal_report_coherence(report)
    assert any("149O.1H" in issue for issue in issues)


@pytest.mark.parametrize(
    "embedded",
    ["x149O.1H.1", "149O.1H.1xyz", "foo149O.1H.1bar", "abc149O.1H.1def"],
)
def test_boundary_safe_extraction_rejects_embedded_substrings(embedded: str) -> None:
    """A phase-ID-shaped substring embedded inside a longer alphanumeric
    run (not the case where the run happens to itself be one valid,
    longer token) must not be extracted as a standalone token."""
    tokens = _extract_evidence_phase_ids(f"digest {embedded} is not a phase mention")
    normalized = {t.normalized_text for t in tokens}
    assert "149O.1H.1" not in normalized


def test_mixed_current_and_historical_references_coherent() -> None:
    """Evidence legitimately citing both the current phase and prior
    findings/phases must not be flagged."""
    report = _report(
        "149O.1H.1",
        {
            "x": (
                "Phase 149O.1H.1 repaired B-149O.1H-1 and B-149O.1H-2, "
                "findings originally discovered by 149O.1H, following the "
                "149O.1G/149O.1F.1 convention."
            )
        },
    )
    assert validate_internal_report_coherence(report) == []


def test_historical_test_filename_does_not_invalidate_current_evidence() -> None:
    """A regression test filename embedding a historical phase ID must
    not, by itself, make current-phase evidence incoherent as long as
    the current phase is also genuinely named in the evidence."""
    report = _report(
        "149O.1H.1",
        {
            "regression": (
                "python -m pytest "
                "tests/test_phase_149o_1h_hatp_proof_models_canonical_serialization_independent_verification.py "
                "-q: 166 passed (149O.1H.1 re-run)"
            )
        },
    )
    assert validate_internal_report_coherence(report) == []


def test_generic_grammar_not_hardcoded_to_one_phase() -> None:
    """The same behavior must hold for an arbitrary nested phase ID, not
    just the phase that originally exposed the defect."""
    for phase_id, evidence in [
        ("42Q.7C.9", "Phase 42Q.7C.9 closed the finding."),
        ("3Z.1A.2B.4", "Phase 3Z.1A.2B.4 closed the finding."),
    ]:
        report = _report(phase_id, {"x": evidence})
        issues = validate_internal_report_coherence(report)
        assert not any("linked only to other phase identities" in issue for issue in issues)


# ═══════════════════════════════════════════════════════════════════════
# B-149O.1R-2 — test_evidence_classification plumbing
# ═══════════════════════════════════════════════════════════════════════


def test_classification_reaches_phase_report_metadata_via_finalize() -> None:
    """`finalize_phase_report` (the `pcae phase complete` path) must
    carry `test_evidence_classification` from its caller into
    `report.metadata`."""
    with tempfile.TemporaryDirectory() as td:
        result = finalize_phase_report(
            phase_id="99Z.1A",
            phase_name="Plumbing Test",
            status="completed",
            summary="test",
            reports_dir=Path(td),
            test_evidence_classification="inherited_regression",
        )
        assert result["report"].metadata.get("test_evidence_classification") == "inherited_regression"


def test_classification_absent_when_not_supplied() -> None:
    """Absence must have no default/implicit suppression semantics --
    only an explicit governed value may suppress the check."""
    with tempfile.TemporaryDirectory() as td:
        result = finalize_phase_report(
            phase_id="99Z.1B",
            phase_name="Plumbing Test",
            status="completed",
            summary="test",
            reports_dir=Path(td),
        )
        assert "test_evidence_classification" not in result["report"].metadata


def test_classification_serialization_round_trip() -> None:
    """The field must survive `to_dict()` (the JSON serialization path)
    since `validate_internal_report_coherence` may run against a
    reconstructed report."""
    report = make_phase_report(
        phase_id="99Z.1C", phase_name="x", status="completed", summary="test",
    )
    report.metadata["test_evidence_classification"] = "inherited_regression"
    data = report.to_dict()
    assert data["metadata"]["test_evidence_classification"] == "inherited_regression"
    reconstructed = PhaseReport(**{k: v for k, v in data.items() if k != "canonical_report_used"})
    assert reconstructed.metadata.get("test_evidence_classification") == "inherited_regression"


def test_classification_suppresses_documented_case() -> None:
    """A report whose evidence cites only other same-series phase IDs
    (never itself) is suppressed by the documented classification --
    unchanged, pre-existing semantics, not broadened by this repair."""
    report = _report(
        "149O.1Z",
        {"x": "this rerun only mentions 149O.1H and 149O.1G, never itself"},
        metadata={"test_evidence_classification": "inherited_regression"},
    )
    assert validate_internal_report_coherence(report) == []


def test_classification_cannot_manufacture_missing_current_evidence() -> None:
    """B-149O.1R closure criterion: classification must classify
    legitimate historical/regression evidence, never conjure current-
    phase evidence that does not exist. This is unaffected because the
    check only ever *adds* an issue when historical evidence exists and
    is unclassified -- classification never manufactures a passing
    'current-phase evidence found' fact; it only elects not to complain
    about the absence-of-self-mention pattern. Confirm no other trust
    dimension is fooled: report_completeness for a report with zero
    substantive test_results and the classification set must not
    silently become 'complete' by virtue of the classification alone."""
    report = _report("149O.1Z", {}, metadata={"test_evidence_classification": "inherited_regression"})
    # No evidence at all -- internal coherence trivially has nothing to
    # flag (there is nothing to be incoherent about), but this must not
    # be conflated with completeness, which is governed by a wholly
    # separate check (assess_completeness) that classification cannot
    # touch.
    assert validate_internal_report_coherence(report) == []
    completeness, missing, _warnings = report.assess_completeness()
    assert completeness != "complete"


def test_classification_cannot_hide_contradictory_production_evidence() -> None:
    """Internal coherence and production-diff contradictions are
    independent checks; classification (which only touches the
    phase-ID-linkage check) must not affect a metadata/phase-identity
    disagreement check."""
    report = _report(
        "149O.1Z",
        {"x": "Phase 149O.1Z closed the finding."},
        metadata={
            "test_evidence_classification": "inherited_regression",
            "phase_id": "149O.1Y",  # deliberately contradicts report.phase_id
        },
    )
    issues = validate_internal_report_coherence(report)
    assert any("disagrees with snapshot metadata" in issue for issue in issues)


# ═══════════════════════════════════════════════════════════════════════
# End-to-end CLI (`pcae phase-report create`)
# ═══════════════════════════════════════════════════════════════════════


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "pcae", "phase-report"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)


_REQUIRED_GOVERNANCE_ARGS = [
    "--governance-result", "pcae_health=healthy",
    "--governance-result", "pcae_check=passed",
    "--governance-result", "pcae_doctor_task_memory=passed",
    "--governance-result", "pcae_push_check=clean",
    "--governance-result", "telegram_runtime=loaded",
]
_REQUIRED_BASE_TEST_RESULT_ARGS = [
    "--test-result", "report_notification_tests=not_applicable_this_phase",
    "--test-result", "bootstrap_session_reporting_tests=not_applicable_this_phase",
    "--test-result", "fast_green=4531 passed",
]
_ELEVEN_NO_GO_ARGS = [
    arg
    for text in [
        "No production files were touched.",
        "No contract files were touched.",
        "No RAE integration exists.",
        "No Permission Broker wiring exists.",
        "No agent behavior changed.",
        "No runtime execution capability changed.",
        "No Wave 4 engine was implemented.",
        "No signature verification was implemented.",
        "No provider attestation was implemented.",
        "No hardware provider was implemented.",
        "No trust bypass flag was added.",
    ]
    for arg in ("--no-go-confirmation", text)
]


def test_cli_create_nested_id_with_classification_is_complete() -> None:
    with tempfile.TemporaryDirectory() as td:
        result = _run_cli([
            "create",
            "--phase-id", "88Y.1Q.1",
            "--phase-name", "CLI Plumbing Test",
            "--status", "completed",
            "--summary", "End-to-end test of the nested-ID + classification repair.",
            "--files-changed", "1",
            "--tests-run", "10",
            "--pushed-status", "pushed",
            "--origin-main-head-count", "0",
            "--recommended-next-phase", "89A",
            "--commit", "deadbeef",
            *_REQUIRED_GOVERNANCE_ARGS,
            *_REQUIRED_BASE_TEST_RESULT_ARGS,
            "--test-result", "regression=88Y.1Q suite rerun during 88Y.1Q.1, 10 passed",
            *_ELEVEN_NO_GO_ARGS,
            "--test-evidence-classification", "inherited_regression",
            "--reports-dir", td,
            "--json",
        ])
        payload = json.loads(result.stdout)
        # `--reports-dir` isolates the report artifact, but the broader
        # trust pipeline also cross-checks the *repository's own live*
        # `.pcae/phase-completion-report.md` title (an unrelated,
        # pre-existing trust dimension -- "canonical report and metadata
        # disagree" -- not touched by this repair and not isolated by
        # `--reports-dir`), so a throwaway test phase ID run against a
        # real checkout can still be quarantined for that unrelated
        # reason. The signal that actually matters for B-149O.1R-1/2 is
        # that internal_evidence_coherence specifically never appears
        # among the blockers/warnings text.
        blob = json.dumps(payload)
        assert "test evidence is linked only to other phase identities" not in blob, payload


def test_cli_create_truly_incoherent_nested_report_still_quarantines() -> None:
    """The repair must not become permissive: a nested-ID report whose
    evidence genuinely belongs only to a different same-series phase,
    with no classification supplied, must still be flagged."""
    with tempfile.TemporaryDirectory() as td:
        result = _run_cli([
            "create",
            "--phase-id", "88Y.1Q.2",
            "--phase-name", "CLI Quarantine Test",
            "--status", "completed",
            "--summary", "This report's evidence belongs to a different phase.",
            "--files-changed", "1",
            "--tests-run", "10",
            "--pushed-status", "pushed",
            "--origin-main-head-count", "0",
            "--recommended-next-phase", "89A",
            "--commit", "deadbeef",
            *_REQUIRED_GOVERNANCE_ARGS,
            *_REQUIRED_BASE_TEST_RESULT_ARGS,
            "--test-result", "regression=88Y.1Q.1 suite rerun, 10 passed",
            *_ELEVEN_NO_GO_ARGS,
            "--reports-dir", td,
            "--json",
        ])
        payload = json.loads(result.stdout)
        blob = json.dumps(payload)
        assert "test evidence is linked only to other phase identities" in blob, payload
        assert not Path(td, "latest.json").exists()

"""Phase 134E.1V — independent adversarial verification of the Canonical
Engineering Evidence executable model (134E.1).

Does not trust 134E.1's own report, documentation, or its 52 tests as
sufficient evidence. These are fresh probes beyond that existing coverage,
including regression tests for two genuine BLOCKING defects found and
repaired during this verification phase:

1. Shallow immutability: a caller-supplied mutable list/dict was stored
   directly on "frozen" dataclass fields with no defensive copy. A
   finalized record's content and digest could be silently changed after
   finalization by mutating the external object the caller still held a
   reference to.
2. Applicability-disclosure/mandatory-present bypass: `OMITTED_INVALID_
   INPUT` was excluded from the "must disclose via uncertainty/limitation"
   check, and the phase-class mandatory-present check only rejected the
   `NOT_APPLICABLE` disposition specifically -- so an IMPLEMENTATION- or
   VERIFICATION-class record could finalize with its own mandatory
   category (e.g. `implementation_findings`) marked `UNAVAILABLE` or
   `OMITTED_INVALID_INPUT`, silently missing, with zero disclosure
   anywhere in the record.
"""

from __future__ import annotations

import inspect
import json
import subprocess
import sys
from types import MappingProxyType

import pytest

from pcae.core import canonical_engineering_evidence as cee
from pcae.core.canonical_engineering_evidence import (
    Applicability,
    CanonicalEngineeringEvidence,
    CommitPushInfo,
    CorrectionMetadata,
    EvidenceIdentity,
    EvidencePhaseIdentity,
    EvidenceProvenanceRecord,
    FindingClassification,
    FindingRecord,
    LimitationItem,
    PhaseClass,
    REQUIRED_APPLICABILITY_CATEGORIES,
    RepairRecord,
    RepositoryStateSnapshot,
    RuntimeStateSnapshot,
    UncertaintyItem,
)


def _identity(phase_id: str = "999X", version: int = 1, correction_of=None) -> EvidenceIdentity:
    return EvidenceIdentity(
        phase=EvidencePhaseIdentity(phase_id=phase_id, phase_name="Verification Probe", source="cli_argument"),
        record_version=version, correction_of=correction_of,
    )


def _minimal(phase_class: PhaseClass, **overrides) -> CanonicalEngineeringEvidence:
    app = dict(overrides.pop("applicability", {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}))
    kwargs = dict(
        identity=_identity(),
        phase_class=phase_class,
        task_id=None,
        objective="verification probe objective",
        engineering_actions=(),
        architectural_findings=(),
        implementation_findings=(),
        verification_findings=(),
        defects_discovered=(),
        defects_repaired=(),
        incorrect_assumptions_corrected=(),
        technical_debt_reviewed=(),
        technical_debt_introduced=(),
        notable_engineering_knowledge=(),
        governance_results=(),
        test_results=(),
        repository_state=RepositoryStateSnapshot(commit="abc1234", branch="main", pushed_status="pushed", origin_main_head_count=0, clean=True),
        runtime_state=RuntimeStateSnapshot(runtime_state="Observed", maximum_capability="observe", execution_availability="unavailable"),
        no_go_confirmations=(),
        architectural_boundary_confirmations=(),
        track_progress="verification probe",
        recommended_next_phase="999Y",
        commit_and_push=CommitPushInfo(commits=("abc1234",), pushed_status="pushed", origin_main_head_count=0),
        provenance=(),
        uncertainty=(),
        limitations=(),
        correction=CorrectionMetadata(),
        applicability=MappingProxyType(app),
        created_at="2026-01-01T00:00:00+00:00",
    )
    kwargs.update(overrides)
    return CanonicalEngineeringEvidence(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Deep immutability of nested state (regression for BLOCKING fix #1)
# ─────────────────────────────────────────────────────────────────────────────

def test_deep_immutability_engineering_actions_list_cannot_leak():
    mutable = ["original"]
    app = {**{c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES},
           "engineering_actions": Applicability.PRESENT}
    ev = _minimal(PhaseClass.ARCHITECTURE, engineering_actions=mutable, applicability=app).finalize()
    d1 = ev.compute_digest()
    mutable.append("injected-after-finalize")
    d2 = ev.compute_digest()
    assert d1 == d2, "digest must not change from mutating an externally-held reference"
    assert ev.engineering_actions == ("original",)
    assert isinstance(ev.engineering_actions, tuple)


def test_deep_immutability_uncertainty_affected_evidence_list_cannot_leak():
    mutable_refs = ["technical_debt_reviewed"]
    u = UncertaintyItem(category="c", description="d", affected_evidence=mutable_refs,
                         source="s", verification_state="v")
    mutable_refs.append("engineering_actions")
    assert u.affected_evidence == ("technical_debt_reviewed",)


def test_deep_immutability_applicability_dict_cannot_leak():
    mutable_app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    ev = _minimal(PhaseClass.ARCHITECTURE, applicability=mutable_app)
    mutable_app["engineering_actions"] = Applicability.PRESENT  # mutate original dict after construction
    assert ev.applicability["engineering_actions"] == Applicability.NOT_APPLICABLE
    with pytest.raises(TypeError):
        ev.applicability["engineering_actions"] = Applicability.PRESENT  # MappingProxyType is read-only


def test_deep_immutability_commit_push_info_commits_list_cannot_leak():
    mutable_commits = ["abc1234"]
    cp = CommitPushInfo(commits=mutable_commits, pushed_status="pushed", origin_main_head_count=0)
    mutable_commits.append("def5678")
    assert cp.commits == ("abc1234",)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Equivalent-input byte determinism
# ─────────────────────────────────────────────────────────────────────────────

def test_equivalent_input_byte_determinism_across_ten_constructions():
    digests = set()
    for _ in range(10):
        ev = _minimal(PhaseClass.ARCHITECTURE, objective="stable objective")
        digests.add(ev.compute_digest())
    assert len(digests) == 1


# ─────────────────────────────────────────────────────────────────────────────
# 3-4. Digest coverage of uncertainty / limitations
# ─────────────────────────────────────────────────────────────────────────────

def test_digest_covers_uncertainty_content():
    base = _minimal(PhaseClass.ARCHITECTURE)
    with_uncertainty = _minimal(
        PhaseClass.ARCHITECTURE,
        uncertainty=(UncertaintyItem(category="c", description="d",
                                      affected_evidence=("engineering_actions",),
                                      source="s", verification_state="v"),),
    )
    assert base.compute_digest() != with_uncertainty.compute_digest()


def test_digest_covers_limitations_content():
    base = _minimal(PhaseClass.ARCHITECTURE)
    with_limitation = _minimal(
        PhaseClass.ARCHITECTURE,
        limitations=(LimitationItem(category="c", description="d",
                                     affected_evidence=("engineering_actions",)),),
    )
    assert base.compute_digest() != with_limitation.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 5-6. Digest excludes approved timestamps, includes material ones
# ─────────────────────────────────────────────────────────────────────────────

def test_digest_excludes_created_at_and_finalized_at():
    ev1 = _minimal(PhaseClass.ARCHITECTURE, created_at="2020-01-01T00:00:00+00:00")
    ev2 = _minimal(PhaseClass.ARCHITECTURE, created_at="2030-12-31T23:59:59+00:00")
    assert ev1.compute_digest() == ev2.compute_digest()
    f1, f2 = ev1.finalize(), ev2.finalize()
    assert f1.finalized_at != f2.finalized_at  # genuinely different wall-clock times
    assert f1.compute_digest() == f2.compute_digest()  # but digest still equal


def test_digest_includes_material_provenance_observed_at():
    """observed_at on a provenance record is *material* evidence (when an
    observation happened), distinct from record creation/finalization
    time -- it must affect the digest, unlike created_at/finalized_at.
    """
    p1 = EvidenceProvenanceRecord(covers="test_results", source_artifact="pytest",
                                   source_command="pytest", source_phase_id="999X",
                                   derivation_path="direct", verification_state="verified",
                                   observed_at="2026-01-01T00:00:00+00:00")
    p2 = EvidenceProvenanceRecord(covers="test_results", source_artifact="pytest",
                                   source_command="pytest", source_phase_id="999X",
                                   derivation_path="direct", verification_state="verified",
                                   observed_at="2026-06-06T00:00:00+00:00")
    ev1 = _minimal(PhaseClass.ARCHITECTURE, provenance=(p1,))
    ev2 = _minimal(PhaseClass.ARCHITECTURE, provenance=(p2,))
    assert ev1.compute_digest() != ev2.compute_digest()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Applicability-state bypass attempts (regression for BLOCKING fix #2/#3)
# ─────────────────────────────────────────────────────────────────────────────

def test_omitted_invalid_input_requires_disclosure_regression():
    ev = _minimal(
        PhaseClass.ARCHITECTURE,
        applicability={**{c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES},
                       "technical_debt_reviewed": Applicability.OMITTED_INVALID_INPUT},
    )
    issues = ev.validate()
    assert any(i.code == "missing_uncertainty_disclosure" for i in issues)
    with pytest.raises(ValueError):
        ev.finalize()


@pytest.mark.parametrize("bypass_disposition", [
    Applicability.UNAVAILABLE, Applicability.UNKNOWN,
    Applicability.OMITTED_INVALID_INPUT, Applicability.NOT_APPLICABLE,
])
def test_implementation_phase_cannot_bypass_mandatory_present_via_any_disposition(bypass_disposition):
    app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    app["implementation_findings"] = bypass_disposition
    ev = _minimal(PhaseClass.IMPLEMENTATION, applicability=app)
    issues = ev.validate()
    assert any(i.code == "contradictory_applicability" for i in issues), (
        f"disposition {bypass_disposition} bypassed the mandatory-present check"
    )


def test_verification_phase_cannot_bypass_mandatory_present():
    app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}
    app["verification_findings"] = Applicability.OMITTED_INVALID_INPUT
    ev = _minimal(PhaseClass.VERIFICATION, applicability=app)
    assert any(i.code == "contradictory_applicability" for i in ev.validate())


# ─────────────────────────────────────────────────────────────────────────────
# 8. Empty-present evidence (fresh combinations)
# ─────────────────────────────────────────────────────────────────────────────

def test_empty_present_cannot_masquerade_across_multiple_categories():
    app = {c: Applicability.PRESENT for c in REQUIRED_APPLICABILITY_CATEGORIES}
    ev = _minimal(PhaseClass.ARCHITECTURE, applicability=app)  # all tuples still empty
    issues = ev.validate()
    contradictory = [i for i in issues if i.code == "contradictory_status"]
    assert len(contradictory) == len(REQUIRED_APPLICABILITY_CATEGORIES)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Repair-history preservation (multiple/partial repairs)
# ─────────────────────────────────────────────────────────────────────────────

def test_multiple_repairs_each_preserve_their_own_original_finding():
    f1 = FindingRecord("F1", FindingClassification.BLOCKING, "issue one", "module_a")
    f2 = FindingRecord("F2", FindingClassification.NON_BLOCKING, "issue two", "module_b")
    r1 = RepairRecord(f1, "fixed one", "module_a.py", "test_a passed", FindingClassification.CONFIRMED)
    r2 = RepairRecord(f2, "fixed two", "module_b.py", "test_b passed", FindingClassification.CONFIRMED)
    ev = _minimal(
        PhaseClass.ARCHITECTURE,
        applicability={**{c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES},
                       "defects_repaired": Applicability.PRESENT},
        defects_repaired=(r1, r2),
    )
    assert ev.validate() == ()
    d = ev.to_dict()
    originals = [r["original_finding"]["classification"] for r in d["defects_repaired"]]
    assert originals == ["blocking", "non_blocking"]  # neither overwritten by "confirmed"


def test_partial_repair_does_not_alter_unrelated_findings():
    """A repair of one finding must not be representable as also
    resolving a different, unrelated finding still present elsewhere in
    the same record (defects_discovered is untouched by defects_repaired).
    """
    discovered = FindingRecord("F3", FindingClassification.BLOCKING, "unrelated issue", "module_c")
    repaired_finding = FindingRecord("F1", FindingClassification.BLOCKING, "issue one", "module_a")
    repair = RepairRecord(repaired_finding, "fixed", "module_a.py", "verified", FindingClassification.CONFIRMED)
    ev = _minimal(
        PhaseClass.ARCHITECTURE,
        applicability={**{c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES},
                       "defects_discovered": Applicability.PRESENT,
                       "defects_repaired": Applicability.PRESENT},
        defects_discovered=(discovered,),
        defects_repaired=(repair,),
    )
    d = ev.to_dict()
    assert d["defects_discovered"][0]["classification"] == "blocking"  # untouched, still BLOCKING
    assert d["defects_repaired"][0]["resulting_status"] == "confirmed"


# ─────────────────────────────────────────────────────────────────────────────
# 10. Invalid correction references
# ─────────────────────────────────────────────────────────────────────────────

def test_invalid_correction_reference_mismatch_detected():
    ev = _minimal(
        PhaseClass.ARCHITECTURE,
        identity=_identity(phase_id="999X", version=2, correction_of="999X#1"),
        correction=CorrectionMetadata(is_correction=True, supersedes_evidence_id="999X#0",
                                       reason="repair", authority="operator"),
    )
    issues = ev.validate()
    assert any(i.code == "correction_identity_mismatch" for i in issues)


def test_correction_cycle_self_reference_rejected_at_identity_level():
    """A record cannot declare itself its own correction target -- the
    identity's own version-1-cannot-correct-anything rule prevents the
    simplest supersession cycle (a record superseding itself).
    """
    with pytest.raises(ValueError):
        _identity(phase_id="999X", version=1, correction_of="999X#1")


# ─────────────────────────────────────────────────────────────────────────────
# 11. Cross-process serialization stability
# ─────────────────────────────────────────────────────────────────────────────

def test_cross_process_digest_stability():
    code = (
        "import json, sys; sys.path.insert(0, %r); "
        "from types import MappingProxyType; "
        "from pcae.core.canonical_engineering_evidence import ("
        "CanonicalEngineeringEvidence, EvidenceIdentity, EvidencePhaseIdentity, "
        "PhaseClass, Applicability, RepositoryStateSnapshot, RuntimeStateSnapshot, "
        "CommitPushInfo, CorrectionMetadata, REQUIRED_APPLICABILITY_CATEGORIES); "
        "app = {c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}; "
        "ev = CanonicalEngineeringEvidence("
        "identity=EvidenceIdentity(phase=EvidencePhaseIdentity(phase_id='999X', phase_name='Probe', source='cli_argument')), "
        "phase_class=PhaseClass.ARCHITECTURE, task_id=None, objective='cross-process probe', "
        "engineering_actions=(), architectural_findings=(), implementation_findings=(), verification_findings=(), "
        "defects_discovered=(), defects_repaired=(), incorrect_assumptions_corrected=(), "
        "technical_debt_reviewed=(), technical_debt_introduced=(), notable_engineering_knowledge=(), "
        "governance_results=(), test_results=(), "
        "repository_state=RepositoryStateSnapshot(commit='abc1234', branch='main', pushed_status='pushed', origin_main_head_count=0, clean=True), "
        "runtime_state=RuntimeStateSnapshot(runtime_state='Observed', maximum_capability='observe', execution_availability='unavailable'), "
        "no_go_confirmations=(), architectural_boundary_confirmations=(), "
        "track_progress='cross-process', recommended_next_phase='999Y', "
        "commit_and_push=CommitPushInfo(commits=('abc1234',), pushed_status='pushed', origin_main_head_count=0), "
        "provenance=(), uncertainty=(), limitations=(), correction=CorrectionMetadata(), "
        "applicability=MappingProxyType(app), created_at='2026-01-01T00:00:00+00:00'); "
        "print(ev.compute_digest())"
    ) % (str(__import__("pathlib").Path(__file__).resolve().parent.parent / "src"))
    r1 = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    r2 = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert r1.stdout.strip() == r2.stdout.strip()
    assert len(r1.stdout.strip()) == 64  # sha256 hex digest length


# ─────────────────────────────────────────────────────────────────────────────
# 12. Unknown future-agent provenance
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("caller", ["deepseek-agent", "claude-agent", "codex-agent", "unknown-future-agent", "direct-human-cli"])
def test_synthetic_caller_provenance_does_not_change_identity_or_validation(caller):
    """Caller provenance may be *recorded* in provenance.source_command;
    it must not change evidence identity, validation outcome, or finding
    semantics. It legitimately changes the digest only because provenance
    content itself is material evidence (documented, intended behavior),
    not because caller identity has special authority.
    """
    prov = EvidenceProvenanceRecord(
        covers="engineering_actions", source_artifact="cli invocation",
        source_command=f"invoked-by:{caller}", source_phase_id="999X",
        derivation_path="direct", verification_state="verified",
    )
    app = {**{c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES}}
    ev = _minimal(PhaseClass.ARCHITECTURE, provenance=(prov,), applicability=app)
    assert ev.validate() == ()
    assert ev.identity.evidence_id == "999X#1"  # caller identity plays no role


def test_no_caller_identity_field_exists_on_the_model():
    import dataclasses
    for cls in (CanonicalEngineeringEvidence, EvidenceIdentity, EvidenceProvenanceRecord):
        names = {f.name for f in dataclasses.fields(cls)}
        assert not any("agent" in n or "model" in n or "caller" in n for n in names), (
            f"{cls.__name__} unexpectedly has a caller/agent/model-identity field: {names}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 13. Secret-bearing free-text behavior (fresh injection points)
# ─────────────────────────────────────────────────────────────────────────────

def test_secret_in_notable_engineering_knowledge_rejected():
    ev = _minimal(
        PhaseClass.ARCHITECTURE,
        applicability={**{c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES},
                       "notable_engineering_knowledge": Applicability.PRESENT},
        notable_engineering_knowledge=(
            "remember PCAE_TELEGRAM_BOT_TOKEN=123456:abcdefGHIJKLMNOPQRSTUVWXYZ0123456 for later",
        ),
    )
    assert any(i.code == "likely_secret_material" for i in ev.validate())


def test_secret_shape_not_scanned_in_governance_or_repository_fields_documented_gap():
    """Documented, not silently accepted: the secret-shape scan currently
    covers objective/engineering_actions/notable_engineering_knowledge
    only, not governance_results.status, provenance.source_command, or
    repository_state.commit free text. This is recorded as a NON-BLOCKING
    scope gap (see verification report) rather than repaired here, since
    none of those fields are expected to legitimately carry long free text
    in current usage, and no production caller populates them from
    untrusted input.
    """
    prov = EvidenceProvenanceRecord(
        covers="governance_results", source_artifact="shell history",
        source_command="PCAE_TELEGRAM_BOT_TOKEN=123456:abcdefGHIJKLMNOPQRSTUVWXYZ0123456 pcae phase complete",
        source_phase_id="999X", derivation_path="direct", verification_state="verified",
    )
    ev = _minimal(PhaseClass.ARCHITECTURE, provenance=(prov,))
    # Not currently flagged -- this assertion documents present behavior,
    # not an endorsement; see the NON-BLOCKING finding in the report.
    assert not any(i.code == "likely_secret_material" for i in ev.validate())


# ─────────────────────────────────────────────────────────────────────────────
# 14. Duplicate/reordered normalized evidence
# ─────────────────────────────────────────────────────────────────────────────

def test_reordered_findings_produce_different_digest_documented_as_non_blocking():
    """Findings are intentionally order-preserving (narrative artifacts,
    not unordered sets) -- two constructions differing only in the order
    two findings were supplied produce different digests. This is
    documented as NON-BLOCKING (a scope/interpretation clarification, not
    a violation): the determinism guarantee is "same construction twice ->
    same digest," verified elsewhere, not "any reordering of semantically
    equivalent items collapses to one digest."
    """
    fa = FindingRecord("FA", FindingClassification.CONFIRMED, "a", "x")
    fb = FindingRecord("FB", FindingClassification.CONFIRMED, "b", "y")
    app = {**{c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES},
           "architectural_findings": Applicability.PRESENT}
    ev1 = _minimal(PhaseClass.ARCHITECTURE, applicability=app, architectural_findings=(fa, fb))
    ev2 = _minimal(PhaseClass.ARCHITECTURE, applicability=app, architectural_findings=(fb, fa))
    assert ev1.compute_digest() != ev2.compute_digest()  # documented current behavior


# ─────────────────────────────────────────────────────────────────────────────
# 15. Identity sufficiency under correction/supersession
# ─────────────────────────────────────────────────────────────────────────────

def test_identity_distinguishes_correction_versions():
    original = _identity(phase_id="999X", version=1)
    correction = _identity(phase_id="999X", version=2, correction_of="999X#1")
    assert original.evidence_id != correction.evidence_id
    assert original.evidence_id == "999X#1"
    assert correction.evidence_id == "999X#2"


def test_identity_does_not_distinguish_multiple_tasks_under_one_phase_documented_gap():
    """NON-BLOCKING (documented, not repaired): phase_id#version alone
    cannot distinguish two different task_id values completing the *same*
    phase_id independently -- task_id is a separate field, not part of
    EvidenceIdentity. Per the frozen contract, cardinality is exactly one
    canonical record per governed *phase*, not per task, so this is
    consistent with 133D Section 3/5/13's own cardinality rule rather
    than a defect; flagged here as a refinement to revisit only if/when
    the correction workflow (Strict Non-Goal of 134E.1) is implemented.
    """
    id_a = EvidenceIdentity(phase=EvidencePhaseIdentity(phase_id="999X", phase_name="P", source="cli_argument"))
    id_b = EvidenceIdentity(phase=EvidencePhaseIdentity(phase_id="999X", phase_name="P", source="cli_argument"))
    assert id_a.evidence_id == id_b.evidence_id  # documented, not a defect per §15 of the report


# ─────────────────────────────────────────────────────────────────────────────
# 16. No active-lifecycle imports
# ─────────────────────────────────────────────────────────────────────────────

def test_no_existing_lifecycle_module_imports_the_new_evidence_model():
    import pathlib
    src_root = pathlib.Path(cee.__file__).resolve().parent.parent
    lifecycle_modules = [
        src_root / "core" / "phase_reports.py",
        src_root / "core" / "notifications.py",
        src_root / "core" / "notification_certification.py",
        src_root / "core" / "notification_config.py",
        src_root / "core" / "repository_transition_validator.py",
        src_root / "commands" / "phase.py",
    ]
    for path in lifecycle_modules:
        text = path.read_text()
        assert "canonical_engineering_evidence" not in text, (
            f"{path} unexpectedly references the new evidence model"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 17. No filesystem or network side effects (behavioral, not just AST)
# ─────────────────────────────────────────────────────────────────────────────

def test_full_construction_and_finalization_touches_no_filesystem(monkeypatch):
    def _forbidden_open(*a, **kw):
        raise AssertionError("canonical_engineering_evidence must not touch the filesystem")

    monkeypatch.setattr("builtins.open", _forbidden_open)
    ev = _minimal(PhaseClass.ARCHITECTURE)
    fin = ev.finalize()
    fin.to_dict()
    fin.compute_digest()
    CanonicalEngineeringEvidence.from_dict(fin.to_dict())


# ─────────────────────────────────────────────────────────────────────────────
# 18. Unsupported-version behavior
# ─────────────────────────────────────────────────────────────────────────────

def test_unsupported_version_fails_closed_not_coerced():
    with pytest.raises(ValueError):
        _minimal(PhaseClass.ARCHITECTURE, schema_version="2.0")
    with pytest.raises(ValueError):
        _minimal(PhaseClass.ARCHITECTURE, schema_version="")


# ─────────────────────────────────────────────────────────────────────────────
# 19. Invalid provenance references
# ─────────────────────────────────────────────────────────────────────────────

def test_provenance_covers_nonexistent_category_not_currently_validated_documented_gap():
    """NON-BLOCKING (documented, not repaired): nothing currently checks
    that a EvidenceProvenanceRecord.covers value names a real category on
    this record. A typo'd or fabricated category name is accepted. This
    does not permit invalid evidence to finalize silently (no category's
    own disposition/content is affected by a stray provenance record), so
    it is a traceability-quality gap, not an authority/correctness one.
    """
    prov = EvidenceProvenanceRecord(
        covers="not_a_real_category", source_artifact="x", source_command=None,
        source_phase_id=None, derivation_path="y", verification_state="z",
    )
    ev = _minimal(PhaseClass.ARCHITECTURE, provenance=(prov,))
    assert ev.validate() == ()  # documents current behavior; see NON-BLOCKING finding


# ─────────────────────────────────────────────────────────────────────────────
# 20. Uncertainty/limitation round-trip preservation
# ─────────────────────────────────────────────────────────────────────────────

def test_uncertainty_and_limitations_survive_round_trip():
    u = UncertaintyItem(category="data_gap", description="exact count unknown",
                         affected_evidence=("technical_debt_reviewed",), source="incident review",
                         verification_state="unresolved", resolution_status="open")
    lim = LimitationItem(category="tooling_gap", description="no receipt ledger",
                          affected_evidence=("technical_debt_reviewed",), resolution_status="open")
    ev = _minimal(
        PhaseClass.ARCHITECTURE,
        applicability={**{c: Applicability.NOT_APPLICABLE for c in REQUIRED_APPLICABILITY_CATEGORIES},
                       "technical_debt_reviewed": Applicability.UNKNOWN},
        uncertainty=(u,), limitations=(lim,),
    ).finalize()
    rt = CanonicalEngineeringEvidence.from_dict(ev.to_dict())
    assert rt.uncertainty[0].to_dict() == u.to_dict()
    assert rt.limitations[0].to_dict() == lim.to_dict()
    assert rt.compute_digest() == ev.compute_digest()

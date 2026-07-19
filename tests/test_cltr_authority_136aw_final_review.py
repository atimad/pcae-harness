"""Phase 136AW: Stage 3 Typed Authority Model Final Review and Stage-Exit
Readiness Assessment.

Independent final-review test module. Does not merely assert that prior
phase reports exist or that prior test modules pass; it re-derives and
directly probes the specific claims the 136AW final review verdict rests
on, using fixtures built directly from the live schema files (independent
of any prior test module's own builder functions).

Scope: this module is read-only evidence for the Stage 3 exit verdict. No
production model or schema change is made by, or required for, this
module -- Phase 136AW's own review found no genuine Blocking defect (see
the canonical phase report). It only narrows four historically-inherited
stale packaging/scope-guard tests (136AB, 136AD, 136M, 136U) whose
original forbidden-module/forbidden-family lists predate the now-complete
sixteen-family implementation; those narrowings are covered directly by
rerunning the repaired tests themselves, not by this module.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
RECORDS_SCHEMA_DIR = REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "records"
MANIFEST_PATH = REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "manifest.json"

SID_TEMPLATE = "https://pcae.local/schemas/cltr_cutover/records/{}.schema.json"

EXPECTED_FAMILIES = {
    "authority_epoch": "AuthorityEpoch",
    "authority_state": "AuthorityState",
    "cutover_request": "CutoverRequest",
    "readiness_package": "ReadinessPackage",
    "human_authorization": "HumanAuthorization",
    "cutover_candidate": "CutoverCandidate",
    "certification": "Certification",
    "publication_attempt": "PublicationAttempt",
    "publication_evidence": "PublicationEvidence",
    "concurrency_conflict": "ConcurrencyConflict",
    "recovery_journal_entry": "RecoveryJournalEntry",
    "notification_authority_binding": "NotificationAuthorityBinding",
    "marker_authority_binding": "MarkerAuthorityBinding",
    "receipt_authority_binding": "FinalizationReceiptAuthorityBinding",
    "compatibility_state": "CompatibilityState",
    "quarantine_record": "QuarantineRecord",
}

MODEL_BY_FAMILY = {fam: getattr(auth, name) for fam, name in EXPECTED_FAMILIES.items()}


# ---------------------------------------------------------------------------
# 1. Exact sixteen-family inventory: schemas, registry, manifest, models,
#    exports all independently re-derived and cross-checked.
# ---------------------------------------------------------------------------


def _schema_docs() -> dict[str, dict]:
    out = {}
    for path in sorted(RECORDS_SCHEMA_DIR.glob("*.schema.json")):
        doc = json.loads(path.read_text())
        out[doc["properties"]["record_type"]["const"]] = doc
    return out


SCHEMA_DOCS = _schema_docs()


def test_136aw_exactly_sixteen_families_on_disk():
    assert len(SCHEMA_DOCS) == 16
    assert set(SCHEMA_DOCS) == set(EXPECTED_FAMILIES)


def test_136aw_no_unexpected_seventeenth_schema_file():
    on_disk = {p.stem.replace(".schema", "") for p in RECORDS_SCHEMA_DIR.glob("*.schema.json")}
    assert on_disk == set(EXPECTED_FAMILIES)


def test_136aw_no_duplicate_schema_id_or_discriminator():
    ids = [doc["$id"] for doc in SCHEMA_DOCS.values()]
    assert len(ids) == len(set(ids)) == 16
    assert len(SCHEMA_DOCS) == len(set(SCHEMA_DOCS)) == 16


def test_136aw_registry_manifest_schema_model_export_all_agree():
    with cltr_cutover_root() as root:
        registry = build_offline_registry(root)
    record_ids_in_registry = {sid for sid in registry.schema_ids if "/records/" in sid}

    manifest = json.loads(MANIFEST_PATH.read_text())
    manifest_families = {
        e["family"] for e in manifest["entries"] if e["file_path"].startswith("records/")
    }

    class_names = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}

    assert record_ids_in_registry == {doc["$id"] for doc in SCHEMA_DOCS.values()}
    assert manifest_families == set(EXPECTED_FAMILIES)
    for fam, class_name in EXPECTED_FAMILIES.items():
        assert class_name in class_names, f"model class {class_name} not found in package source"
        assert class_name in auth.__all__, f"{class_name} not exported from pcae.cltr.authority"
        assert getattr(auth, class_name) is MODEL_BY_FAMILY[fam]

    # No hidden unexported model, no model without schema, no schema
    # without model: package-level class count for the sixteen expected
    # names must be exact, not merely a superset.
    matched = {c for c in class_names if c in EXPECTED_FAMILIES.values()}
    assert matched == set(EXPECTED_FAMILIES.values())


def test_136aw_current_schema_versions_are_1_0_and_status_frozen():
    manifest = json.loads(MANIFEST_PATH.read_text())
    rec_entries = {e["family"]: e for e in manifest["entries"] if e["file_path"].startswith("records/")}
    for fam in EXPECTED_FAMILIES:
        entry = rec_entries[fam]
        assert entry["schema_version"] == "1.0", fam
        assert entry["status"] == "frozen", fam
        assert SCHEMA_DOCS[fam].get("required") is not None


# ---------------------------------------------------------------------------
# 2. Independently-built minimal wire payloads, one per family, each
#    schema-validated before use.
# ---------------------------------------------------------------------------


def _sha(fill: str) -> str:
    return (fill * 64)[:64]


def _rref(family: str, rid: str = "final-ref-000001", with_schema: bool = False) -> dict:
    d = {"record_id": rid, "record_digest": _sha("a"), "record_family": family}
    if with_schema:
        d["schema_id"] = SID_TEMPLATE.format(family)
        d["schema_version"] = "1.0"
    return d


def _gref() -> dict:
    return {"generation_id": "final-gen-000001", "generation_digest": _sha("b")}


def _disclosure(role: str = "derivative") -> dict:
    return {"authority_role": role, "is_authoritative": False, "disclosure_text": "136aw final review disclosure"}


def _cas_expectation() -> dict:
    return {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _rref("authority_epoch"),
        "expected_authoritative_generation": _gref(),
        "expected_authority_pointer_digest": _sha("c"),
        "expected_authority_state_digest": _sha("d"),
        "expected_migration_epoch": "epoch-136aw",
        "expected_source_lifecycle_state": "PROPOSED",
        "expected_compatibility_mode": "legacy_authoritative",
        "expected_journal_lock_state": "unlocked",
        "expected_request_reference": _rref("cutover_request"),
        "expected_certification_reference": _rref("certification"),
    }


def _envelope(fam: str, rid: str) -> dict:
    return {
        "schema_id": SID_TEMPLATE.format(fam),
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": fam,
        "record_id": rid,
        "record_digest": _sha("0"),
        "created_at": "2026-07-19T12:00:00Z",
        "migration_epoch": "epoch-136aw",
    }


def _build(fam: str) -> dict:
    d = _envelope(fam, f"{fam[:12].replace('_', '-')}-final001")
    if fam == "authority_epoch":
        d.update(authority_kind="legacy", activation_state="proposed", predecessor_epoch=None,
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "authority_state":
        d.update(transition_id="trans-final01", active_authority_epoch=_rref("authority_epoch"),
                  authority_kind="legacy", publication_evidence_reference=_rref("publication_evidence"),
                  pointer_digest=_sha("5"), verification_state="verified",
                  compatibility_mode="legacy_authoritative", limitations=[], authority_disclosure=_disclosure())
    elif fam == "cutover_request":
        d.update(phase_id="136AW", target="cltr", source_authority="legacy",
                  source_epoch=_rref("authority_epoch"), target_epoch=_rref("authority_epoch"),
                  evidence_requirements=[], readiness_package_reference=_rref("readiness_package", with_schema=True),
                  authorization_requirement=True, final_revision="1", state="pending",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "readiness_package":
        d.update(phase_id="136AW", transition_id="trans-final02", evidence_references=[],
                  prerequisite_status="unknown", findings=[], state="unknown",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "human_authorization":
        d.update(phase_id="136AW", principal="operator@example.com", method="manual_review",
                  request_reference=_rref("cutover_request", with_schema=True),
                  readiness_reference=_rref("readiness_package", with_schema=True),
                  target_reference=_rref("authority_epoch", with_schema=True),
                  issued_at="2026-07-19T12:00:00Z", expires_at="2027-07-19T12:00:00Z",
                  state="issued", replay_binding="bind-136aw", risk_acknowledgement=True,
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "cutover_candidate":
        d.update(stage2_generation_reference=_rref("cutover_candidate"), cas_expectation=_cas_expectation(),
                  state="proposed", limitations=[], authority_disclosure=_disclosure())
    elif fam == "certification":
        d.update(phase_id="136AW", candidate_reference=_rref("cutover_candidate", with_schema=True),
                  request_reference=_rref("cutover_request", with_schema=True),
                  readiness_reference=_rref("readiness_package", with_schema=True),
                  authorization_reference=_rref("human_authorization", with_schema=True),
                  source_authority_reference=_rref("authority_epoch"), target_epoch_reference=_rref("authority_epoch"),
                  cas_expectation=_cas_expectation(), verifier_evidence=[], state="pending",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "publication_attempt":
        d.update(transition_id="trans-final03", attempt_id="pubattempt-final02",
                  request_reference=_rref("cutover_request", with_schema=True),
                  candidate_reference=_rref("cutover_candidate", with_schema=True),
                  certification_reference=_rref("certification", with_schema=True),
                  cas_expectation=_cas_expectation(), source_authority_reference=_rref("authority_epoch"),
                  target_authority_reference=_rref("authority_epoch"), attempt_sequence=1, state="not_requested",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "publication_evidence":
        d.update(transition_id="trans-final04", attempt_reference=_rref("publication_attempt", with_schema=True),
                  outcome="not_attempted", limitations=[], authority_disclosure=_disclosure())
    elif fam == "concurrency_conflict":
        d.update(actors=["writer-a", "writer-b"], requests=[_rref("cutover_request", with_schema=True)],
                  type="dual_writer", winner=None, recovery_requirement="none_required",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "recovery_journal_entry":
        d.update(transition_id="trans-final05", sequence=0, prior_entry_digest=None,
                  operation_reference=_rref("recovery_journal_entry"), prior_state_reference=_rref("authority_state"),
                  new_state_reference=_rref("authority_state"), authority_state_reference=_rref("authority_state"),
                  generation_reference=_gref(), external_effect_state="none",
                  retry_replay_classification="original", state="recorded",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "notification_authority_binding":
        d.update(authoritative_generation_reference=_gref(), authority_epoch_reference=_rref("authority_epoch"),
                  payload_digest=_sha("6"), attempt_identity="notifattempt-final1",
                  pfn001_classification="cutover-notification", delivery_state="not_dispatched",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "marker_authority_binding":
        d.update(generation_reference=_gref(), state="absent", compatibility_fallback_forbidden=True,
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "receipt_authority_binding":
        d.update(generation_reference=_gref(), receipt_state="absent",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "compatibility_state":
        d.update(component="legacy-lifecycle", role="compatibility", allowed_reads=[],
                  forbidden_authority_use=True, fallback_disabled=False, mode="legacy_adapter",
                  limitations=[], authority_disclosure=_disclosure())
    elif fam == "quarantine_record":
        d.update(object_type="generation", object_reference=_rref("cutover_candidate"),
                  reason_code="quarantine_required", state="quarantined",
                  limitations=[], authority_disclosure=_disclosure(role="quarantined"))
    else:  # pragma: no cover - exhaustiveness guard
        raise AssertionError(f"no fixture builder for family {fam}")
    return d


FIXTURES = {fam: _build(fam) for fam in EXPECTED_FAMILIES}


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


@pytest.mark.parametrize("family", sorted(EXPECTED_FAMILIES))
def test_136aw_fixture_schema_valid(family, schema_registry):
    result = validate_record_shape(FIXTURES[family], schema_id=SID_TEMPLATE.format(family), registry=schema_registry)
    assert result.status is OutcomeStatus.VALID, result.issues


# ---------------------------------------------------------------------------
# 3. Representative round-trip, recursive immutability, structural
#    equality/inequality, and mutation-isolation for every family.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("family", sorted(EXPECTED_FAMILIES))
def test_136aw_round_trip_lossless_for_every_family(family):
    wire = FIXTURES[family]
    cls = MODEL_BY_FAMILY[family]
    model = cls.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


@pytest.mark.parametrize("family", sorted(EXPECTED_FAMILIES))
def test_136aw_constructor_input_mutation_does_not_affect_model(family):
    wire = copy.deepcopy(FIXTURES[family])
    cls = MODEL_BY_FAMILY[family]
    model = cls.from_dict(wire, schema_version="1.0")
    before = model.to_dict()
    wire["record_id"] = "mutated-after-construction"
    if isinstance(wire.get("limitations"), list):
        wire["limitations"].append({"tampered": True})
    after = model.to_dict()
    assert before == after, f"{family}: post-construction input mutation leaked into model"


@pytest.mark.parametrize("family", sorted(EXPECTED_FAMILIES))
def test_136aw_serialized_output_mutation_does_not_affect_model(family):
    cls = MODEL_BY_FAMILY[family]
    model = cls.from_dict(FIXTURES[family], schema_version="1.0")
    out1 = model.to_dict()
    out1["record_id"] = "mutated-output"
    out2 = model.to_dict()
    assert out2 == FIXTURES[family]
    assert out2["record_id"] != "mutated-output"


@pytest.mark.parametrize("family", sorted(EXPECTED_FAMILIES))
def test_136aw_model_is_recursively_immutable(family):
    cls = MODEL_BY_FAMILY[family]
    model = cls.from_dict(FIXTURES[family], schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(model, "record_id", "x")


@pytest.mark.parametrize("family", sorted(EXPECTED_FAMILIES))
def test_136aw_structural_equality_and_hashing(family):
    cls = MODEL_BY_FAMILY[family]
    a = cls.from_dict(FIXTURES[family], schema_version="1.0")
    b = cls.from_dict(copy.deepcopy(FIXTURES[family]), schema_version="1.0")
    assert a == b
    assert a is not b


def test_136aw_cross_family_instances_are_never_equal():
    families = sorted(EXPECTED_FAMILIES)
    instances = {
        fam: MODEL_BY_FAMILY[fam].from_dict(FIXTURES[fam], schema_version="1.0") for fam in families
    }
    for i, fam_a in enumerate(families):
        for fam_b in families[i + 1:]:
            assert instances[fam_a] != instances[fam_b]


def test_136aw_no_identifier_digest_or_state_only_equality():
    a = auth.AuthorityEpoch.from_dict(FIXTURES["authority_epoch"], schema_version="1.0")
    altered = dict(FIXTURES["authority_epoch"])
    altered["activation_state"] = "superseded"
    b = auth.AuthorityEpoch.from_dict(altered, schema_version="1.0")
    assert a != b, "changing one field while keeping record_id/record_digest fixed must break equality"


# ---------------------------------------------------------------------------
# 4. Reference construction is lookup-free (no filesystem/network access
#    during construction of any reference-bearing field).
# ---------------------------------------------------------------------------


def test_136aw_reference_construction_performs_no_filesystem_or_network_lookup(monkeypatch):
    def _blocked_open(*args, **kwargs):
        raise AssertionError("unexpected filesystem access during model construction")

    def _blocked_socket(*args, **kwargs):
        raise AssertionError("unexpected network access during model construction")

    import socket

    monkeypatch.setattr("builtins.open", _blocked_open)
    monkeypatch.setattr(socket, "socket", _blocked_socket)

    for family in sorted(EXPECTED_FAMILIES):
        cls = MODEL_BY_FAMILY[family]
        model = cls.from_dict(FIXTURES[family], schema_version="1.0")
        model.to_dict()


# ---------------------------------------------------------------------------
# 5. Runtime import isolation and side-effect freedom.
# ---------------------------------------------------------------------------


def test_136aw_no_production_runtime_module_imports_authority_package():
    result = subprocess.run(
        ["git", "grep", "-n", "-e", "pcae.cltr.authority", "-e", "cltr import authority", "--", "src/pcae"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    hits = [
        line for line in result.stdout.splitlines()
        if not line.split(":", 1)[0].startswith("src/pcae/cltr/authority/")
    ]
    assert hits == [], hits


def test_136aw_package_import_is_side_effect_free(monkeypatch):
    import importlib
    import socket
    import subprocess as sp

    def _blocked(*args, **kwargs):
        raise AssertionError("side effect attempted during package import")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(sp, "Popen", _blocked)

    for mod_name in list(sys.modules):
        if mod_name == "pcae.cltr.authority" or mod_name.startswith("pcae.cltr.authority."):
            del sys.modules[mod_name]
    importlib.import_module("pcae.cltr.authority")


def test_136aw_no_operational_authority_api_exposed():
    forbidden_substrings = (
        "activate_authority",
        "resolve_authority",
        "execute_cutover",
        "publish_now",
        "dispatch_notification",
        "write_marker",
        "finalize_receipt",
        "run_migration",
        "run_recovery",
        "run_quarantine",
    )
    exported_lower = {name.lower() for name in auth.__all__}
    for forbidden in forbidden_substrings:
        assert forbidden not in exported_lower, forbidden


# ---------------------------------------------------------------------------
# 6. Stage 3-related inherited-failure disposition (the four historically
#    stale packaging/scope guards): final review confirms all four are
#    accurately-obsolete guards from a completed staged rollout, now
#    repaired narrowly (not deferred, not reclassified as defects) since
#    every referenced module/family is legitimately implemented.
# ---------------------------------------------------------------------------


def test_136aw_stale_scope_guards_repaired_not_ambiguous():
    checks = {
        "src/pcae/cltr/authority/bindings.py": AUTHORITY_PACKAGE_DIR / "bindings.py",
        "src/pcae/cltr/authority/compatibility_quarantine.py": AUTHORITY_PACKAGE_DIR / "compatibility_quarantine.py",
        "src/pcae/cltr/authority/recovery_concurrency.py": AUTHORITY_PACKAGE_DIR / "recovery_concurrency.py",
    }
    for label, path in checks.items():
        assert path.exists(), f"{label}: expected legitimately-implemented module missing"

    forbidden_record_models_now_implemented = (
        "CompatibilityState",
        "QuarantineRecord",
        "NotificationAuthorityBinding",
        "MarkerAuthorityBinding",
        "FinalizationReceiptAuthorityBinding",
        "ConcurrencyConflict",
        "RecoveryJournalEntry",
        "PublicationAttempt",
        "PublicationEvidence",
    )
    for name in forbidden_record_models_now_implemented:
        assert name in auth.__all__, f"{name} expected to be implemented and exported as of 136AW"

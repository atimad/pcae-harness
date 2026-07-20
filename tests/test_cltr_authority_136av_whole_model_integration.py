"""Phase 136AV: Stage 3 Typed Authority Model Whole-Model Integration
Verification.

Independent whole-model verification of the complete, now-sixteen-family
Stage 3 Typed Authority Model (``src/pcae/cltr/authority``), re-derived
directly from the live executable schema registry
(``src/pcae/schema_resources/cltr_cutover``: 16 ``records/*.schema.json``
files, the shared ``$defs`` files they compose, and ``manifest.json``) --
not from ``pcae.cltr.authority.__all__``, prior per-family implementation
or independent-verification test modules (``test_cltr_authority_136a[a-u]*``),
prior phase reports, or documentation summaries.

This module does not re-derive each family's own field-by-field contract
(each of the sixteen families already has its own independent-verification
module doing exactly that: 136AC/AE/AG/AI/AK/AM/AO/AQ/AS/AU). It instead
checks properties that only exist at the level of the *whole* model:
whole-model inventory completeness, schema-registry consistency, package
export completeness, module assignment, cross-family discriminator/
schema_id collision resistance (a full 16x15x2 = 480-substitution matrix),
and production-runtime isolation.

Every fixture below (one minimal valid wire payload per family) was built
directly from the sixteen live schema files and their shared ``$defs``,
then confirmed schema-valid via ``pcae.schema_runtime.validate_record_shape``
against the real offline registry before being used in any model-layer
assertion -- not copied from any 136a* test module's own fixtures.

Scope: whole-model integration only. No production implementation change
is made unless a genuine Blocking integration defect is independently
demonstrated (none is, per the findings recorded in the canonical phase
report).
"""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority.errors import TypedModelConstructionError
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
RECORDS_SCHEMA_DIR = REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "records"
MANIFEST_PATH = REPO_ROOT / "src" / "pcae" / "schema_resources" / "cltr_cutover" / "manifest.json"

SID_TEMPLATE = "https://pcae.local/schemas/cltr_cutover/records/{}.schema.json"


# ---------------------------------------------------------------------------
# Independently re-derived whole-model inventory (from the live schema files
# directly, via a filesystem sweep -- not from any Python symbol).
# ---------------------------------------------------------------------------


def _record_type_consts() -> dict[str, dict]:
    """Every records/*.schema.json file's own record_type const and $id,
    independently re-derived from the schema JSON itself."""
    out: dict[str, dict] = {}
    for path in sorted(RECORDS_SCHEMA_DIR.glob("*.schema.json")):
        doc = json.loads(path.read_text())
        fam = doc["properties"]["record_type"]["const"]
        out[fam] = {
            "schema_id": doc["$id"],
            "file": path.name,
            "required": tuple(doc["required"]),
        }
    return out


RECORD_SCHEMAS = _record_type_consts()

MODEL_BY_FAMILY: dict[str, type] = {
    "authority_epoch": auth.AuthorityEpoch,
    "authority_state": auth.AuthorityState,
    "cutover_request": auth.CutoverRequest,
    "readiness_package": auth.ReadinessPackage,
    "human_authorization": auth.HumanAuthorization,
    "cutover_candidate": auth.CutoverCandidate,
    "certification": auth.Certification,
    "publication_attempt": auth.PublicationAttempt,
    "publication_evidence": auth.PublicationEvidence,
    "concurrency_conflict": auth.ConcurrencyConflict,
    "recovery_journal_entry": auth.RecoveryJournalEntry,
    "notification_authority_binding": auth.NotificationAuthorityBinding,
    "marker_authority_binding": auth.MarkerAuthorityBinding,
    "receipt_authority_binding": auth.FinalizationReceiptAuthorityBinding,
    "compatibility_state": auth.CompatibilityState,
    "quarantine_record": auth.QuarantineRecord,
}


# ---------------------------------------------------------------------------
# 1. Whole-model inventory
# ---------------------------------------------------------------------------


def test_136av_exactly_sixteen_record_schemas_on_disk():
    assert len(RECORD_SCHEMAS) == 16


def test_136av_no_duplicate_discriminator_or_schema_id_on_disk():
    discriminators = list(RECORD_SCHEMAS.keys())
    schema_ids = [v["schema_id"] for v in RECORD_SCHEMAS.values()]
    assert len(discriminators) == len(set(discriminators)) == 16
    assert len(schema_ids) == len(set(schema_ids)) == 16


def test_136av_schema_id_matches_owning_filename():
    for fam, info in RECORD_SCHEMAS.items():
        assert info["schema_id"] == SID_TEMPLATE.format(fam)
        assert info["file"] == f"{fam}.schema.json"


def test_136av_exactly_sixteen_models_in_package_and_match_schema_inventory():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for expected in MODEL_BY_FAMILY.values():
        assert expected.__name__ in class_names
    assert set(MODEL_BY_FAMILY) == set(RECORD_SCHEMAS)


def test_136av_every_model_exported_and_no_duplicate_class_names():
    names = [cls.__name__ for cls in MODEL_BY_FAMILY.values()]
    assert len(names) == len(set(names)) == 16
    for name in names:
        assert name in auth.__all__
        assert getattr(auth, name) is MODEL_BY_FAMILY[[f for f in MODEL_BY_FAMILY if MODEL_BY_FAMILY[f].__name__ == name][0]]


def test_136av_every_model_is_frozen_dataclass():
    import dataclasses

    for fam, cls in MODEL_BY_FAMILY.items():
        assert dataclasses.is_dataclass(cls), fam
        assert cls.__dataclass_params__.frozen, fam


# ---------------------------------------------------------------------------
# 2. Schema registry verification
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def test_136av_registry_contains_all_sixteen_record_schemas_exactly_once(schema_registry):
    record_ids = [sid for sid in schema_registry.schema_ids if "/records/" in sid]
    assert len(record_ids) == 16
    assert len(set(record_ids)) == 16
    assert set(record_ids) == {info["schema_id"] for info in RECORD_SCHEMAS.values()}


def test_136av_registry_resolution_deterministic_across_rebuild():
    with cltr_cutover_root() as root:
        reg_a = build_offline_registry(root)
    with cltr_cutover_root() as root:
        reg_b = build_offline_registry(root)
    assert reg_a.schema_ids == reg_b.schema_ids
    for sid in reg_a.schema_ids:
        assert reg_a.document(sid) == reg_b.document(sid)


def test_136av_manifest_lists_all_sixteen_record_families_with_matching_schema_id():
    manifest = json.loads(MANIFEST_PATH.read_text())
    rec_entries = [e for e in manifest["entries"] if e["file_path"].startswith("records/")]
    assert len(rec_entries) == 16
    families = {e["family"] for e in rec_entries}
    assert families == set(RECORD_SCHEMAS)
    for e in rec_entries:
        assert e["schema_id"] == SID_TEMPLATE.format(e["family"])
        assert e["status"] == "frozen"


# ---------------------------------------------------------------------------
# 3. Independently-built, schema-validated minimal wire payloads (one per
#    family; each confirmed valid against the live registry before use).
# ---------------------------------------------------------------------------


def _sha(fill: str) -> str:
    return (fill * 64)[:64]


def _rref(family: str, rid: str = "ref-0000001", with_schema: bool = False) -> dict:
    d = {"record_id": rid, "record_digest": _sha("1"), "record_family": family}
    if with_schema:
        d["schema_id"] = SID_TEMPLATE.format(family)
        d["schema_version"] = "1.0"
    return d


def _gref() -> dict:
    return {"generation_id": "gen-0000001", "generation_digest": _sha("2")}


def _disclosure(role: str = "derivative") -> dict:
    return {"authority_role": role, "is_authoritative": False, "disclosure_text": "test disclosure"}


def _cas_expectation() -> dict:
    return {
        "expected_authority_kind": "legacy",
        "expected_authority_epoch": _rref("authority_epoch"),
        "expected_authoritative_generation": _gref(),
        "expected_authority_pointer_digest": _sha("3"),
        "expected_authority_state_digest": _sha("4"),
        "expected_migration_epoch": "epoch-001",
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
        "migration_epoch": "epoch-001",
    }


def _build_authority_epoch():
    d = _envelope("authority_epoch", "authepoch-0000001")
    d.update(authority_kind="legacy", activation_state="proposed", predecessor_epoch=None,
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_authority_state():
    d = _envelope("authority_state", "authstate-0000001")
    d.update(transition_id="trans-0000001", active_authority_epoch=_rref("authority_epoch"),
              authority_kind="legacy", publication_evidence_reference=_rref("publication_evidence"),
              pointer_digest=_sha("5"), verification_state="verified",
              compatibility_mode="legacy_authoritative", limitations=[], authority_disclosure=_disclosure())
    return d


def _build_cutover_request():
    d = _envelope("cutover_request", "cutreq-00000001")
    d.update(phase_id="136AV", target="cltr", source_authority="legacy",
              source_epoch=_rref("authority_epoch"), target_epoch=_rref("authority_epoch"),
              evidence_requirements=[], readiness_package_reference=_rref("readiness_package", with_schema=True),
              authorization_requirement=True, final_revision="1", state="pending",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_readiness_package():
    d = _envelope("readiness_package", "readypkg-0000001")
    d.update(phase_id="136AV", transition_id="trans-0000002", evidence_references=[],
              prerequisite_status="unknown", findings=[], state="unknown",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_human_authorization():
    d = _envelope("human_authorization", "humanauth-0000001")
    d.update(phase_id="136AV", principal="operator@example.com", method="manual_review",
              request_reference=_rref("cutover_request", with_schema=True),
              readiness_reference=_rref("readiness_package", with_schema=True),
              target_reference=_rref("authority_epoch", with_schema=True),
              issued_at="2026-07-19T12:00:00Z", expires_at="2027-07-19T12:00:00Z",
              state="issued", replay_binding="bind-1", risk_acknowledgement=True,
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_cutover_candidate():
    d = _envelope("cutover_candidate", "cutcand-00000001")
    d.update(stage2_generation_reference=_rref("cutover_candidate"), cas_expectation=_cas_expectation(),
              state="proposed", limitations=[], authority_disclosure=_disclosure())
    return d


def _build_certification():
    d = _envelope("certification", "certif-00000001")
    d.update(phase_id="136AV", candidate_reference=_rref("cutover_candidate", with_schema=True),
              request_reference=_rref("cutover_request", with_schema=True),
              readiness_reference=_rref("readiness_package", with_schema=True),
              authorization_reference=_rref("human_authorization", with_schema=True),
              source_authority_reference=_rref("authority_epoch"), target_epoch_reference=_rref("authority_epoch"),
              cas_expectation=_cas_expectation(), verifier_evidence=[], state="pending",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_publication_attempt():
    d = _envelope("publication_attempt", "pubattempt-0000001")
    d.update(transition_id="trans-0000003", attempt_id="pubattempt-0000002",
              request_reference=_rref("cutover_request", with_schema=True),
              candidate_reference=_rref("cutover_candidate", with_schema=True),
              certification_reference=_rref("certification", with_schema=True),
              cas_expectation=_cas_expectation(), source_authority_reference=_rref("authority_epoch"),
              target_authority_reference=_rref("authority_epoch"), attempt_sequence=1, state="not_requested",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_publication_evidence():
    d = _envelope("publication_evidence", "pubevid-00000001")
    d.update(transition_id="trans-0000004", attempt_reference=_rref("publication_attempt", with_schema=True),
              outcome="not_attempted", limitations=[], authority_disclosure=_disclosure())
    return d


def _build_concurrency_conflict():
    d = _envelope("concurrency_conflict", "concconf-0000001")
    d.update(actors=["writer-a", "writer-b"], requests=[_rref("cutover_request", with_schema=True)],
              type="dual_writer", winner=None, recovery_requirement="none_required",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_recovery_journal_entry():
    d = _envelope("recovery_journal_entry", "recjournal-0000001")
    d.update(transition_id="trans-0000005", sequence=0, prior_entry_digest=None,
              operation_reference=_rref("recovery_journal_entry"), prior_state_reference=_rref("authority_state"),
              new_state_reference=_rref("authority_state"), authority_state_reference=_rref("authority_state"),
              generation_reference=_gref(), external_effect_state="none",
              retry_replay_classification="original", state="recorded",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_notification_authority_binding():
    d = _envelope("notification_authority_binding", "notifbind-0000001")
    d.update(authoritative_generation_reference=_gref(), authority_epoch_reference=_rref("authority_epoch"),
              payload_digest=_sha("6"), attempt_identity="notifattempt-0000001",
              pfn001_classification="cutover-notification", delivery_state="not_dispatched",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_marker_authority_binding():
    d = _envelope("marker_authority_binding", "markerbind-0000001")
    d.update(generation_reference=_gref(), state="absent", compatibility_fallback_forbidden=True,
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_receipt_authority_binding():
    d = _envelope("receipt_authority_binding", "receiptbind-0000001")
    d.update(generation_reference=_gref(), receipt_state="absent",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_compatibility_state():
    d = _envelope("compatibility_state", "compatst-0000001")
    d.update(component="legacy-lifecycle", role="compatibility", allowed_reads=[],
              forbidden_authority_use=True, fallback_disabled=False, mode="legacy_adapter",
              limitations=[], authority_disclosure=_disclosure())
    return d


def _build_quarantine_record():
    d = _envelope("quarantine_record", "quarrec-0000001")
    d.update(object_type="generation", object_reference=_rref("cutover_candidate"),
              reason_code="quarantine_required", state="quarantined",
              limitations=[], authority_disclosure=_disclosure(role="quarantined"))
    return d


WIRE_BUILDERS = {
    "authority_epoch": _build_authority_epoch,
    "authority_state": _build_authority_state,
    "cutover_request": _build_cutover_request,
    "readiness_package": _build_readiness_package,
    "human_authorization": _build_human_authorization,
    "cutover_candidate": _build_cutover_candidate,
    "certification": _build_certification,
    "publication_attempt": _build_publication_attempt,
    "publication_evidence": _build_publication_evidence,
    "concurrency_conflict": _build_concurrency_conflict,
    "recovery_journal_entry": _build_recovery_journal_entry,
    "notification_authority_binding": _build_notification_authority_binding,
    "marker_authority_binding": _build_marker_authority_binding,
    "receipt_authority_binding": _build_receipt_authority_binding,
    "compatibility_state": _build_compatibility_state,
    "quarantine_record": _build_quarantine_record,
}


def test_136av_wire_builders_cover_all_sixteen_families():
    assert set(WIRE_BUILDERS) == set(MODEL_BY_FAMILY) == set(RECORD_SCHEMAS)


@pytest.mark.parametrize("family", sorted(WIRE_BUILDERS))
def test_136av_fixture_is_schema_valid(family, schema_registry):
    wire = WIRE_BUILDERS[family]()
    result = validate_record_shape(wire, schema_id=SID_TEMPLATE.format(family), registry=schema_registry)
    assert result.status is OutcomeStatus.VALID, result.issues


@pytest.mark.parametrize("family", sorted(WIRE_BUILDERS))
def test_136av_fixture_constructs_and_round_trips(family):
    wire = WIRE_BUILDERS[family]()
    cls = MODEL_BY_FAMILY[family]
    model = cls.from_dict(wire, schema_version="1.0")
    assert model.to_dict() == wire


# ---------------------------------------------------------------------------
# 4. Cross-family schema identity verification: full 16x15x2 = 480
#    substitution matrix (every family's payload gets every OTHER family's
#    record_type and, separately, every other family's schema_id spliced
#    in; every substitution must be rejected at construction).
# ---------------------------------------------------------------------------


def test_136av_cross_family_collision_matrix_all_480_substitutions_rejected():
    failures = []
    checked = 0
    for fam_b, cls_b in MODEL_BY_FAMILY.items():
        base_wire = WIRE_BUILDERS[fam_b]()
        for fam_a in MODEL_BY_FAMILY:
            if fam_a == fam_b:
                continue
            mutated_type = copy.deepcopy(base_wire)
            mutated_type["record_type"] = fam_a
            checked += 1
            try:
                cls_b.from_dict(mutated_type, schema_version="1.0")
                failures.append((fam_a, fam_b, "record_type"))
            except TypedModelConstructionError:
                pass

            mutated_sid = copy.deepcopy(base_wire)
            mutated_sid["schema_id"] = SID_TEMPLATE.format(fam_a)
            checked += 1
            try:
                cls_b.from_dict(mutated_sid, schema_version="1.0")
                failures.append((fam_a, fam_b, "schema_id"))
            except TypedModelConstructionError:
                pass
    assert checked == 16 * 15 * 2
    assert failures == []


def test_136av_no_routing_depends_on_import_or_enumeration_order():
    """There is no central dispatcher/factory keyed by record_type anywhere
    in the package: UnknownModelFamilyError is declared in the taxonomy but
    never raised by production code, and every family is constructed
    directly via its own ``Model.from_dict``. Order-independence therefore
    follows structurally (nothing iterates a collection to pick a model),
    which this test re-confirms by checking the error class is unused."""
    import re

    raise_sites = 0
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        text = path.read_text()
        raise_sites += len(re.findall(r"raise\s+UnknownModelFamilyError", text))
    assert raise_sites == 0
    # Constructing every family in reverse-sorted order changes nothing.
    for family in sorted(WIRE_BUILDERS, reverse=True):
        wire = WIRE_BUILDERS[family]()
        MODEL_BY_FAMILY[family].from_dict(wire, schema_version="1.0")


# ---------------------------------------------------------------------------
# 5. Package export / module-assignment consistency
# ---------------------------------------------------------------------------


def test_136av_wildcard_import_matches_all():
    namespace: dict = {}
    exec("from pcae.cltr.authority import *", namespace)
    exported = {name for name in namespace if not name.startswith("_")}
    assert exported == set(auth.__all__)


def test_136av_no_two_families_share_a_production_module_incorrectly():
    # Every model's module must itself live under pcae.cltr.authority, and
    # module co-location (multiple families sharing one .py file) must not
    # cause any class-name or discriminator collision (already checked
    # above); this just re-confirms the module prefix.
    for fam, cls in MODEL_BY_FAMILY.items():
        assert cls.__module__.startswith("pcae.cltr.authority."), fam


# ---------------------------------------------------------------------------
# 6. Runtime isolation / no unauthorized operational integration
# ---------------------------------------------------------------------------


def test_136av_no_production_runtime_module_imports_authority_package():
    src_root = REPO_ROOT / "src" / "pcae"
    offenders = []
    for path in src_root.rglob("*.py"):
        if AUTHORITY_PACKAGE_DIR in path.parents or path.parent == AUTHORITY_PACKAGE_DIR:
            continue
        # Phase 137K: the sole authorized production Typed Authority Model
        # consumer is permitted to import pcae.cltr.authority (TAMPC-001
        # v1.0, docs/contracts/TYPED_AUTHORITY_MODEL_PRODUCTION_CONSUMPTION_CONTRACT.md).
        if path.name in {"authority_inspection.py", "authority_inspect.py"}:
            continue
        text = path.read_text()
        if "pcae.cltr.authority" in text or "cltr import authority" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    # The test suite itself references the package; only src/pcae is scanned.
    assert offenders == [], offenders


def test_136av_opaque_json_round_trip_helper_present_and_pure():
    assert callable(auth.verify_round_trip)
    assert callable(auth.OpaqueJsonValue)

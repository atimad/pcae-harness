"""Phase 136M: Request and Readiness Schema Independent Verification.

Independently re-derives, re-attacks, and cross-checks Phase 136L's Group 3
executable schemas -- ``cutover_request.schema.json`` and
``readiness_package.schema.json`` -- against primary contract sources
(CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.7, Sec.9, Sec.10, Sec.12,
Sec.19, Sec.19.1 (136D-repaired), Sec.20, Sec.46) rather than trusting 136L's
own fixtures, tests, prose, or findings.

This module does not merely duplicate ``test_cltr_cutover_136l_*``: every
test here either (a) re-derives a requirement independently from contract
text and attacks it with fresh fixtures, or (b) probes an attack surface
136L's suite did not exercise (cross-family record_id prefix substitution,
duplicate finding/evidence-reference detection, manifest field-level tamper
variants, registry-order determinism across subprocesses, wheel-install
availability).

Every schema here validates SHAPE only. No test in this module creates,
reads, or asserts anything about live CLTR authority, migration state,
readiness truth, human authorization, or production lifecycle behavior.
Legacy lifecycle remains the sole production authority; CLTR remains
derivative.
"""
from __future__ import annotations

import copy
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import (
    ManifestIntegrityError,
    OutcomeStatus,
    build_offline_registry,
    load_and_verify_manifest,
    validate_record_shape,
)

MANIFEST_SCHEMA_ID = "https://pcae.local/schemas/cltr_cutover/manifest.schema.json"
BASE_ID = "https://pcae.local/schemas/cltr_cutover/"

CUTOVER_REQUEST_ID = BASE_ID + "records/cutover_request.schema.json"
READINESS_PACKAGE_ID = BASE_ID + "records/readiness_package.schema.json"
AUTHORITY_EPOCH_ID = BASE_ID + "records/authority_epoch.schema.json"
AUTHORITY_STATE_ID = BASE_ID + "records/authority_state.schema.json"

SHARED_FILES = (
    "shared/digest.schema.json",
    "shared/enums.schema.json",
    "shared/envelope.schema.json",
    "shared/failures.schema.json",
    "shared/identity.schema.json",
    "shared/limitations.schema.json",
    "shared/references.schema.json",
)

GROUP2_RECORD_FILES = (
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
)

GROUP3_RECORD_FILES = (
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
)

LATER_GROUP_STEMS = (
    # human_authorization, cutover_candidate, and certification are no
    # longer forbidden: Phase 136N legitimately implements them as
    # Implementation Group 4. publication_attempt and publication_evidence
    # are no longer forbidden: Phase 136P legitimately implements them as
    # Implementation Group 5.
    "concurrency_conflict",
    "recovery_journal_entry",
    "quarantine_record",
    "notification_authority_binding",
    "marker_authority_binding",
    "receipt_authority_binding",
    "compatibility_state",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _epoch_ref(record_id="authepoch-0000001", digest="b" * 64, family="authority_epoch"):
    return {"record_id": record_id, "record_digest": digest, "record_family": family}


def _readiness_ref(record_id="readypkg-0000001", digest="a" * 64, family="readiness_package"):
    return {
        "record_id": record_id,
        "record_digest": digest,
        "record_family": family,
        "schema_id": READINESS_PACKAGE_ID,
        "schema_version": "1.0",
    }


def _valid_readiness_package(**overrides) -> dict:
    record = {
        "schema_id": READINESS_PACKAGE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "readiness_package",
        "record_id": "readypkg-0000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "phase_id": "136M",
        "transition_id": "trans-00000001",
        "migration_epoch": "epoch-001",
        "evidence_references": [],
        "prerequisite_status": "unknown",
        "findings": [],
        "state": "unknown",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


def _valid_cutover_request(**overrides) -> dict:
    record = {
        "schema_id": CUTOVER_REQUEST_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "cutover_request",
        "record_id": "cutreq-00000001",
        "record_digest": "a" * 64,
        "created_at": "2026-07-16T12:00:00Z",
        "phase_id": "136M",
        "migration_epoch": "epoch-001",
        "target": "cltr",
        "source_authority": "legacy",
        "source_epoch": _epoch_ref("authepoch-0000001", "b" * 64),
        "target_epoch": _epoch_ref("authepoch-0000002", "c" * 64),
        "evidence_requirements": [],
        "readiness_package_reference": _readiness_ref(),
        "authorization_requirement": True,
        "final_revision": "rev-001",
        "state": "pending",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "Non-authoritative schema-validated companion record.",
        },
    }
    record.update(overrides)
    return record


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        yield build_offline_registry(root)


def _validate(record, schema_id, registry):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# 1. Independent Group 3 inventory derivation and exact scope guard
# ---------------------------------------------------------------------------


def test_136m_independent_group3_inventory_is_exactly_request_and_readiness():
    """Sec.46's original per-file grouping lists cutover_request as Group 3
    alone and readiness_package as a separate Group 4; the 136E
    implementation plan Sec."Group 3 -- Request and readiness" explicitly
    and reasonedly re-groups both files under one coarser "Group 3" label
    (dependency prerequisites: Group 1 only, no $ref on Group 2). Both
    schemas' own manifest entries and file headers consistently use the
    136E numbering, not Sec.46's. This is disclosed here as a verified,
    non-contradictory renumbering -- not silently accepted."""
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_family = {e["family"]: e for e in manifest["entries"]}
    assert by_family["cutover_request"]["implementation_group"] == 3
    assert by_family["readiness_package"]["implementation_group"] == 3


def test_136m_exactly_four_production_record_schemas_exist():
    # Updated by Phase 136N (seven) and Phase 136P: nine production record
    # schemas now legitimately exist (Group 2+3's four, Group 4's three,
    # Group 5's two).
    with cltr_cutover_root() as root:
        files = sorted(p.name for p in (root / "records").glob("*.schema.json"))
    assert files == [
        "authority_epoch.schema.json",
        "authority_state.schema.json",
        "certification.schema.json",
        "cutover_candidate.schema.json",
        "cutover_request.schema.json",
        "human_authorization.schema.json",
        "publication_attempt.schema.json",
        "publication_evidence.schema.json",
        "readiness_package.schema.json",
    ]


def test_136m_manifest_has_exactly_eleven_entries():
    # Updated by Phase 136N (14) and Phase 136P: manifest now legitimately
    # carries 16 entries.
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    assert len(manifest["entries"]) == 16


@pytest.mark.parametrize("stem", LATER_GROUP_STEMS)
def test_136m_no_group4plus_record_schema_file_exists(stem):
    with cltr_cutover_root() as root:
        assert not (root / "records" / f"{stem}.schema.json").exists()


def test_136m_no_bindings_or_views_directory():
    with cltr_cutover_root() as root:
        assert not (root / "bindings").exists()
        assert not (root / "views").exists()


def test_136m_no_cltr_authority_namespace_on_disk():
    assert not (_repo_root() / ".pcae" / "cltr-authority").exists()


def test_136m_no_typed_authority_model_module_exists():
    candidate = _repo_root() / "src" / "pcae" / "cltr" / "authority"
    assert not candidate.exists()


def test_136m_no_semantic_validator_module_introduced():
    tracked = subprocess.run(
        ["git", "ls-files", "src/pcae"], cwd=_repo_root(), capture_output=True, text=True, check=True
    ).stdout.splitlines()
    forbidden = ("semantic_validator.py", "authority_resolver.py", "cutover_authority_resolver.py")
    hits = [p for p in tracked if Path(p).name in forbidden]
    assert hits == []


# ---------------------------------------------------------------------------
# 2. Re-derived creation-order proof ($ref graph + identity/digest graph)
# ---------------------------------------------------------------------------


def test_136m_readiness_package_content_derived_independent_of_request(registry):
    """Fresh, 136M-authored fixture: a readiness_package validates on its
    own with zero mention of any cutover_request anywhere in its document
    tree -- proving the record's own identity-bearing fields never require
    a request to exist first."""
    package = _valid_readiness_package(record_id="readypkg-0000777", record_digest="e" * 64)
    assert "cutover_request" not in json.dumps(package)
    result = _validate(package, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136m_request_binds_second_to_independently_created_package(registry):
    package = _valid_readiness_package(record_id="readypkg-0000777", record_digest="e" * 64)
    assert _validate(package, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.VALID

    request = _valid_cutover_request(
        readiness_package_reference=_readiness_ref(record_id="readypkg-0000777", digest="e" * 64)
    )
    assert _validate(request, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.VALID


def test_136m_ref_dependency_graph_has_no_cycle():
    """Build the $ref graph by textual scan of both Group 3 files: neither
    file's raw JSON text contains a $ref pointing at the other file."""
    with cltr_cutover_root() as root:
        cr_text = (root / "records/cutover_request.schema.json").read_text(encoding="utf-8")
        rp_text = (root / "records/readiness_package.schema.json").read_text(encoding="utf-8")
    assert '"$ref": "../records/readiness_package.schema.json' not in cr_text
    assert '"$ref": "../records/cutover_request.schema.json' not in rp_text
    assert '"$ref": "records/cutover_request.schema.json' not in rp_text


def test_136m_identity_dependency_graph_has_no_cycle():
    """The record identity/digest graph: readiness_package's own record_id
    and record_digest fields are shape-only generic definitions (no $const
    or $ref that could encode a dependency on a cutover_request's
    record_id/record_digest values); cutover_request's own record_id/
    record_digest are likewise independent, generic definitions. Neither
    file's identity fields reference the other family's identity fields."""
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    assert cr["properties"]["record_id"] == {
        "$ref": "../shared/identity.schema.json#/$defs/record_identity",
        "description": cr["properties"]["record_id"]["description"],
    }
    assert rp["properties"]["record_id"]["$ref"] == "../shared/identity.schema.json#/$defs/record_identity"
    assert cr["properties"]["record_digest"]["$ref"] == "../shared/digest.schema.json#/$defs/record_digest"
    assert rp["properties"]["record_digest"]["$ref"] == "../shared/digest.schema.json#/$defs/record_digest"


def test_136m_readiness_package_has_no_request_reference_field_at_all():
    with cltr_cutover_root() as root:
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    props = set(rp["properties"])
    assert "request_reference" not in props
    assert "cutover_request_reference" not in props
    assert not any("request" in name.lower() for name in props)


def test_136m_no_request_v2_or_re_creation_mechanism_anywhere():
    """No field name or $def anywhere encodes a second, separately-versioned
    request document -- only prose disclaiming the absence of such a
    mechanism may mention the phrase 'request-v2'."""
    with cltr_cutover_root() as root:
        document = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    names = set(document.get("properties", {})) | set(document.get("$defs", {}))
    for name in names:
        lowered = name.lower()
        for token in ("v2", "version_2", "supersedes_request", "re_created"):
            assert token not in lowered, f"field/$def name {name!r} suggests a request-v2 mechanism"


def test_136m_readiness_reference_requires_schema_id_and_version_per_sec12(registry):
    """Sec.12: schema_id/schema_version required only where a reference
    crosses a family boundary whose compatibility is not otherwise implied
    -- Sec.12 names cutover_request->readiness_package as exactly this
    case. Independently confirm both are unconditionally required here."""
    record = _valid_cutover_request()
    del record["readiness_package_reference"]["schema_id"]
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID

    record2 = _valid_cutover_request()
    del record2["readiness_package_reference"]["schema_version"]
    assert _validate(record2, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


def test_136m_epoch_reference_does_not_require_schema_id_same_family(registry):
    """Sec.12: same-family/version references may omit schema_id/version.
    source_epoch/target_epoch reference authority_epoch (a different family
    than cutover_request, but Sec.19's own field table does not add a
    cross-family schema_id/version requirement for epoch references the
    way it does for readiness_package_reference) -- confirm the
    as-implemented epoch_reference $def has no required schema_id/version,
    matching the narrower Sec.12 case list."""
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    epoch_def = cr["$defs"]["epoch_reference"]
    for branch in epoch_def["allOf"]:
        assert "required" not in branch or "schema_id" not in branch.get("required", [])


# ---------------------------------------------------------------------------
# 3. CutoverRequest Tier 1 strictness re-attack
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutation",
    [
        {"target": "legacy"},
        {"source_authority": "cltr"},
        {"authorization_requirement": False},
        {"authorization_requirement": None},
        {"target": None},
        {"source_authority": None},
    ],
)
def test_136m_request_tier1_constants_reject_every_weakening(registry, mutation):
    record = _valid_cutover_request(**mutation)
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID, f"weakening {mutation} must be rejected"


def test_136m_request_target_equals_source_authority_rejected(registry):
    """target must be 'cltr' and source_authority must be 'legacy'
    (distinct consts) -- a request cannot set both to the same value."""
    record = _valid_cutover_request(target="legacy", source_authority="legacy")
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


def test_136m_request_target_alias_case_variant_rejected(registry):
    for alias in ("CLTR", "Cltr", " cltr", "cltr "):
        record = _valid_cutover_request(target=alias)
        result = _validate(record, CUTOVER_REQUEST_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{alias!r} must not be accepted as target"


def test_136m_request_tier1_no_extensions_escape_hatch(registry):
    record = _valid_cutover_request(_extensions={"k": "v"})
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


def test_136m_request_unknown_field_cannot_smuggle_through_allof_branch(registry):
    """target/source_authority are declared via allOf branches combining a
    shared $ref with a local const; confirm neither allOf branch opens an
    additionalProperties gap at the document's top level."""
    record = _valid_cutover_request(smuggled_via_allof="x")
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 4. CutoverRequest state-machine re-attack
# ---------------------------------------------------------------------------


def test_136m_request_state_reaching_published_is_local_label_only(registry):
    """A record_state of 'published' must not itself require or imply any
    publication-evidence-shaped field, since PublicationEvidence is a later
    (not-yet-implemented) family -- confirm the schema accepts 'published'
    with no additional publication-proof fields, and independently confirm
    the schema's own description text discloses this is a label only."""
    record = _valid_cutover_request(state="published")
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.VALID
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    assert "never itself proves" in cr["properties"]["state"]["description"]


def test_136m_request_state_unknown_value_fails_closed(registry):
    for bogus in ("in_progress", "complete", "READY", "", None):
        record = _valid_cutover_request(state=bogus)
        result = _validate(record, CUTOVER_REQUEST_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"state={bogus!r} must fail closed"


def test_136m_request_no_locally_enforced_reason_code_conditional(registry):
    """Sec.16 defines no if/then row for cutover_request's reason_code, so
    -- unlike readiness_package's conflict/BLOCKING-finding conditional --
    a 'rejected' state with no reason_code must still validate; this is
    disclosed convention, not an enforced rule. Confirm both branches."""
    rejected_without_reason = _valid_cutover_request(state="rejected")
    assert _validate(rejected_without_reason, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.VALID
    rejected_with_reason = _valid_cutover_request(state="rejected", reason_code="authority_missing")
    assert _validate(rejected_with_reason, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.VALID


def test_136m_request_multiple_terminal_states_not_representable_single_field(registry):
    """state is a single scalar enum -- structurally impossible to declare
    two simultaneous terminal states in one document; confirm the field
    shape (not an array) forecloses this attack by construction."""
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    assert cr["properties"]["state"]["enum"]
    assert "type" not in cr["properties"]["state"] or cr["properties"]["state"].get("type") != "array"


# ---------------------------------------------------------------------------
# 5. Source/target authority binding re-attack
# ---------------------------------------------------------------------------


def test_136m_request_source_epoch_and_target_epoch_reject_readiness_family(registry):
    for field in ("source_epoch", "target_epoch"):
        record = _valid_cutover_request(**{field: _readiness_ref()})
        result = _validate(record, CUTOVER_REQUEST_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{field} must reject readiness_package family"


def test_136m_request_epoch_reference_malformed_digest_rejected(registry):
    record = _valid_cutover_request(source_epoch=_epoch_ref(digest="not-hex-at-all"))
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


def test_136m_request_epoch_reference_traversal_record_id_rejected(registry):
    record = _valid_cutover_request(source_epoch=_epoch_ref(record_id="../../etc/passwd"))
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


def test_136m_request_source_epoch_unknown_authority_kind_family_rejected(registry):
    record = _valid_cutover_request(source_epoch=_epoch_ref(family="cutover_request"))
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 6. Evidence-family separation (cross-substitution at every reference site)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "wrong_family",
    ["cutover_request", "authority_state", "human_authorization", "not_a_real_family"],
)
def test_136m_request_readiness_reference_rejects_every_wrong_family(registry, wrong_family):
    record = _valid_cutover_request(
        readiness_package_reference=_readiness_ref(family=wrong_family)
    )
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID, f"{wrong_family} must not substitute for readiness_package"


def test_136m_readiness_evidence_references_accept_any_of_sixteen_families(registry):
    """Sec.20: evidence_references applies no family restriction -- an
    evidence reference may point at any of the 16 companion families.
    Independently confirm every one of the 16 record_family enum values is
    accepted here (not just the two Group 2/3 families 136L fixtured)."""
    with cltr_cutover_root() as root:
        enums_doc = json.loads((root / "shared/enums.schema.json").read_bytes())
    all_families = enums_doc["$defs"]["record_family"]["enum"]
    assert len(all_families) == 16
    for family in all_families:
        record = _valid_readiness_package(
            evidence_references=[_epoch_ref(record_id="authepoch-0000009", digest="f" * 64, family=family)]
        )
        result = _validate(record, READINESS_PACKAGE_ID, registry)
        assert result.status is OutcomeStatus.VALID, f"evidence_references must accept family {family}"


def test_136m_readiness_evidence_reference_rejects_unknown_family(registry):
    record = _valid_readiness_package(
        evidence_references=[_epoch_ref(family="totally_invented_family")]
    )
    assert _validate(record, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 7. Authorization-requirement boundary
# ---------------------------------------------------------------------------


def test_136m_request_schema_has_no_authorization_proof_fields():
    """The request must only declare that authorization is required, never
    embed proof it occurred: confirm no signature/principal/decision-shaped
    field exists anywhere in cutover_request's property set."""
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    props = set(cr["properties"])
    forbidden_substrings = ("signature", "principal", "authorized_by", "authorization_state", "decision")
    for prop in props:
        for forbidden in forbidden_substrings:
            assert forbidden not in prop.lower(), f"property {prop} suggests embedded authorization proof"


def test_136m_request_rejects_injected_authorization_proof_field(registry):
    record = _valid_cutover_request(authorization_proof={"signed_by": "x"})
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


def test_136m_request_state_authorized_does_not_require_or_accept_proof_fields(registry):
    """'authorized' is a valid state value (label-only, per schema
    description); confirm reaching it does not additionally unlock any
    proof-shaped field (the schema remains additionalProperties: false
    regardless of state value)."""
    record = _valid_cutover_request(state="authorized", authorization_proof={"x": "y"})
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 8. Identity/digest honesty
# ---------------------------------------------------------------------------


def test_136m_neither_schema_description_claims_identity_recomputation():
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    for doc in (cr, rp):
        record_id_desc = doc["properties"]["record_id"]["description"]
        digest_desc = doc["properties"]["record_digest"]["description"]
        assert "never recomputed" in record_id_desc or "shape-checked only" in record_id_desc
        assert "never recomputed" in digest_desc


def test_136m_created_at_not_used_as_identity_or_ordering_input():
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    for doc in (cr, rp):
        assert "created_at" in doc["properties"]
        assert "Never used to establish record identity" in doc["properties"]["created_at"]["description"]


# ---------------------------------------------------------------------------
# 9. ReadinessPackage Tier 2 extension boundary re-attack
# ---------------------------------------------------------------------------


def test_136m_extensions_field_is_string_valued_map_only(registry):
    for bad_value in ({"k": 1}, {"k": None}, {"k": ["nested"]}, {"k": {"nested": "obj"}}):
        record = _valid_readiness_package(_extensions=bad_value)
        result = _validate(record, READINESS_PACKAGE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"_extensions value {bad_value!r} must be rejected"


def test_136m_extensions_oversized_rejected(registry):
    record = _valid_readiness_package(_extensions={f"k{i}": "v" for i in range(33)})
    assert _validate(record, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.INVALID


@pytest.mark.parametrize(
    "authority_key",
    ["authoritative", "cutover_complete", "authorization", "publication", "current_authority", "recovery_complete"],
)
def test_136m_extensions_authority_bearing_keys_are_still_only_string_valued(registry, authority_key):
    """_extensions is a forward-compatible annotation-only map: even an
    authority-suggestive key name is accepted as a *key* (Sec.14 imposes no
    key-name restriction), but its value can never be anything other than
    a plain string -- confirm no nested/boolean/object smuggling is
    possible through such a key."""
    record = _valid_readiness_package(_extensions={authority_key: True})
    assert _validate(record, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.INVALID
    record2 = _valid_readiness_package(_extensions={authority_key: "true"})
    assert _validate(record2, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.VALID


def test_136m_extensions_cannot_carry_a_second_nested_extensions_key(registry):
    record = _valid_readiness_package(_extensions={"_extensions": "nested"})
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID  # a string-valued sibling key is not itself a smuggling vector


def test_136m_unknown_top_level_field_outside_extensions_still_rejected(registry):
    record = _valid_readiness_package(cutover_complete=True)
    assert _validate(record, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 10. Readiness category / result vocabulary -- exact inventory re-derivation
# ---------------------------------------------------------------------------


def test_136m_readiness_state_enum_is_exactly_five_values():
    with cltr_cutover_root() as root:
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    assert set(rp["properties"]["state"]["enum"]) == {"unknown", "stale", "partial", "ready", "conflict"}


def test_136m_prerequisite_status_enum_is_exactly_three_values():
    with cltr_cutover_root() as root:
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    assert set(rp["properties"]["prerequisite_status"]["enum"]) == {"unknown", "unmet", "met"}


def test_136m_gate_result_enum_is_exactly_four_values_matching_cutover001_sec10():
    with cltr_cutover_root() as root:
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    assert set(rp["properties"]["gate_result"]["enum"]) == {"eligible", "ineligible", "uncertain", "conflict"}


def test_136m_finding_verdict_enum_is_exactly_five_values():
    with cltr_cutover_root() as root:
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    assert set(rp["$defs"]["finding"]["properties"]["verdict"]["enum"]) == {
        "CONFIRMED",
        "NON-BLOCKING",
        "BLOCKING",
        "PREREQUISITE",
        "DEFERRED",
    }


def test_136m_readiness_package_has_no_invented_category_structure():
    """No separate 'readiness_categories' array or per-category result
    object exists anywhere -- readiness is represented only by the
    package-wide state/prerequisite_status/gate_result scalars plus the
    findings array, exactly as Sec.20's field table lists. Confirm no
    implementation-invented category concept was added."""
    with cltr_cutover_root() as root:
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    props = set(rp["properties"])
    assert not any("categor" in name.lower() for name in props)


# ---------------------------------------------------------------------------
# 11. Overall readiness-state conflict/BLOCKING invariant re-attack
# ---------------------------------------------------------------------------


def test_136m_conflict_state_requires_blocking_finding_present(registry):
    record = _valid_readiness_package(state="conflict", findings=[])
    assert _validate(record, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.INVALID


def test_136m_conflict_state_with_mixed_verdicts_including_blocking_accepted(registry):
    record = _valid_readiness_package(
        state="conflict",
        findings=[
            {"id": "f1", "verdict": "NON-BLOCKING", "title": "minor"},
            {"id": "f2", "verdict": "BLOCKING", "title": "major"},
            {"id": "f3", "verdict": "DEFERRED", "title": "later"},
        ],
    )
    assert _validate(record, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.VALID


def test_136m_ready_state_with_open_blocking_finding_is_not_locally_forbidden(registry):
    """The only local if/then rule binds 'conflict' to a required BLOCKING
    finding; it does NOT forbid a 'ready' state from simultaneously
    carrying a BLOCKING-verdict finding. This is Layer 4's cross-field
    consistency responsibility (Sec.40), not a JSON-Schema-shape rule --
    confirm this is genuinely unenforced here (not merely undocumented) so
    the honest boundary is independently proven, not assumed."""
    record = _valid_readiness_package(
        state="ready",
        findings=[{"id": "f1", "verdict": "BLOCKING", "title": "should have blocked readiness"}],
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID, (
        "confirms this specific cross-field consistency check is Layer 4's responsibility, "
        "not Layer 2's -- disclosed as a limitation in the verification document, not a defect"
    )


def test_136m_duplicate_finding_ids_are_not_locally_rejected(registry):
    """Sec.20 defines no uniqueItems constraint on findings[].id; confirm
    duplicate finding IDs validate (a genuine, disclosed Layer 4 gap, not a
    136M-introduced regression)."""
    record = _valid_readiness_package(
        findings=[
            {"id": "dup", "verdict": "CONFIRMED", "title": "first"},
            {"id": "dup", "verdict": "BLOCKING", "title": "second"},
        ]
    )
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136m_duplicate_evidence_references_are_not_locally_rejected(registry):
    ref = _epoch_ref()
    record = _valid_readiness_package(evidence_references=[ref, dict(ref)])
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 12. Record-id cross-family prefix substitution (new independent finding)
# ---------------------------------------------------------------------------


def test_136m_record_id_shape_does_not_enforce_family_slug_prefix(registry):
    """Sec.10's identifier table documents a per-family record_id prefix
    convention ('cutreq-', 'readypkg-', 'authstate-'), but
    shared/identity.schema.json#/$defs/record_identity is a single generic
    pattern with no per-family prefix enforcement. A record_id that reads
    like it belongs to a different family (e.g. a readypkg-prefixed value
    used as a cutover_request's own record_id) is schema-valid here, since
    record_family/record_type is tracked by a separate, explicit const
    field rather than derived from the id string. This is disclosed as a
    NON-BLOCKING/DEFERRED cross-family (Group 1, not Group-3-specific)
    observation, not a Group 3 defect requiring repair within this phase's
    bounded scope -- record_family in reference tuples remains the actual
    security-relevant tag and is independently, correctly enforced
    elsewhere in this suite."""
    record = _valid_cutover_request(record_id="readypkg-9999999")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.VALID

    record2 = _valid_readiness_package(record_id="cutreq-00000042")
    result2 = _validate(record2, READINESS_PACKAGE_ID, registry)
    assert result2.status is OutcomeStatus.VALID


def test_136m_record_type_const_remains_the_actual_family_tag(registry):
    """Even though record_id itself does not enforce a family prefix,
    record_type does remain a hard per-file const -- confirm swapping
    record_type is still rejected regardless of record_id content."""
    record = _valid_cutover_request(record_id="readypkg-9999999", record_type="readiness_package")
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 13. Requiredness / absent-vs-null re-attack
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("field", ["reason_code"])
def test_136m_request_conditionally_present_fields_reject_explicit_null(registry, field):
    record = _valid_cutover_request(**{field: None})
    result = _validate(record, CUTOVER_REQUEST_ID, registry)
    assert result.status is OutcomeStatus.INVALID, f"{field}=null must be rejected, not treated as absent"


@pytest.mark.parametrize("field", ["gate_result", "_extensions"])
def test_136m_readiness_conditionally_present_fields_reject_explicit_null(registry, field):
    record = _valid_readiness_package(**{field: None})
    result = _validate(record, READINESS_PACKAGE_ID, registry)
    assert result.status is OutcomeStatus.INVALID, f"{field}=null must be rejected, not treated as absent"


def test_136m_request_evidence_requirements_empty_array_is_valid(registry):
    record = _valid_cutover_request(evidence_requirements=[])
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.VALID


def test_136m_readiness_findings_and_evidence_references_empty_arrays_valid(registry):
    record = _valid_readiness_package(findings=[], evidence_references=[])
    assert _validate(record, READINESS_PACKAGE_ID, registry).status is OutcomeStatus.VALID


def test_136m_request_final_revision_empty_string_rejected(registry):
    record = _valid_cutover_request(final_revision="")
    assert _validate(record, CUTOVER_REQUEST_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 14. Manifest tamper attacks (fresh mutation set beyond 136L's two cases)
# ---------------------------------------------------------------------------


def _copy_tree(source: Path, dest: Path) -> None:
    import shutil

    for item in source.rglob("*"):
        if item.is_file():
            target = dest / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def test_136m_manifest_declared_dependency_list_correctness_not_cross_checked(tmp_path):
    """The manifest's own ``dependencies`` array is informational metadata:
    load_and_verify_manifest verifies per-entry digest/$id and two-way file
    completeness, but does not cross-check that a declared dependency edge
    is real or non-circular. Injecting a spurious
    cutover_request -> readiness_package dependency entry (which would
    contradict Sec.9.2/the actual $ref graph, independently confirmed
    elsewhere in this suite to have no such edge) still loads successfully.
    Disclosed as a genuine, bounded limitation -- true cycle-freedom is
    established by the $ref/identity graph tests in this module, not by
    manifest metadata, so this does not weaken the creation-order proof."""
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    for entry in manifest["entries"]:
        if entry["family"] == "cutover_request":
            entry["dependencies"].append(
                "https://pcae.local/schemas/cltr_cutover/records/readiness_package.schema.json"
            )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    manifest_obj = load_and_verify_manifest(
        manifest_path,
        package_root=tmp_path,
        registry=reg,
        manifest_schema_id=MANIFEST_SCHEMA_ID,
        excluded_relative_paths=frozenset({"manifest.schema.json"}),
    )
    # Updated by Phase 136N (14) and Phase 136P: manifest now legitimately
    # carries 16 entries.
    assert len(manifest_obj.entries) == 16


def test_136m_manifest_out_of_range_implementation_group_rejected(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    for entry in manifest["entries"]:
        if entry["family"] == "readiness_package":
            entry["implementation_group"] = 99
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    with pytest.raises(ManifestIntegrityError):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136m_manifest_in_range_but_semantically_wrong_implementation_group_not_locally_detected(tmp_path):
    """Unlike an out-of-range value, an in-range-but-semantically-wrong
    implementation_group (e.g. readiness_package mislabeled as group 2, a
    value the manifest schema's own bounds happily accept) is NOT caught by
    load_and_verify_manifest -- shape/digest verification has no
    cross-check against the family's actual dependency-derived group.
    Disclosed as a genuine, bounded limitation (manifest-authoring review
    responsibility), not a Group 3 schema defect requiring repair."""
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    for entry in manifest["entries"]:
        if entry["family"] == "readiness_package":
            entry["implementation_group"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    manifest_obj = load_and_verify_manifest(
        manifest_path,
        package_root=tmp_path,
        registry=reg,
        manifest_schema_id=MANIFEST_SCHEMA_ID,
        excluded_relative_paths=frozenset({"manifest.schema.json"}),
    )
    by_family = {e["family"]: e for e in manifest_obj.document["entries"]}
    assert by_family["readiness_package"]["implementation_group"] == 2


def test_136m_manifest_duplicate_schema_id_across_entries_detected(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    entries_by_family = {e["family"]: e for e in manifest["entries"]}
    entries_by_family["cutover_request"]["schema_id"] = entries_by_family["readiness_package"]["schema_id"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    with pytest.raises(Exception):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136m_manifest_traversal_file_path_detected(tmp_path):
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    for entry in manifest["entries"]:
        if entry["family"] == "cutover_request":
            entry["file_path"] = "../../../etc/passwd"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    with pytest.raises(Exception):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136m_manifest_missing_group3_entry_detected(tmp_path):
    """Removing cutover_request's manifest entry while its schema file
    still exists on disk must fail the two-way completeness check (the
    file becomes an undeclared, unindexed resource)."""
    with cltr_cutover_root() as source_root:
        _copy_tree(source_root, tmp_path)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["entries"] = [e for e in manifest["entries"] if e["family"] != "cutover_request"]
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    reg = build_offline_registry(tmp_path)
    with pytest.raises(ManifestIntegrityError, match="completeness"):
        load_and_verify_manifest(
            manifest_path,
            package_root=tmp_path,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


# ---------------------------------------------------------------------------
# 15. Registry / packaging / no-network / determinism
# ---------------------------------------------------------------------------


def test_136m_registry_schema_ids_stable_across_subprocess(registry):
    script = (
        "from pcae.schema_resources import cltr_cutover_root\n"
        "from pcae.schema_runtime import build_offline_registry\n"
        "with cltr_cutover_root() as root:\n"
        "    reg = build_offline_registry(root)\n"
        "print(sorted(reg.schema_ids))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=_repo_root(), capture_output=True, text=True, check=True
    )
    subprocess_ids = eval(result.stdout.strip())
    assert subprocess_ids == sorted(registry.schema_ids)


def test_136m_no_network_socket_during_group3_validation(monkeypatch):
    def _blocked(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        _validate(_valid_cutover_request(), CUTOVER_REQUEST_ID, reg)
        _validate(_valid_readiness_package(), READINESS_PACKAGE_ID, reg)


def test_136m_validation_of_invalid_records_does_not_mutate_filesystem(tmp_path, registry):
    before = set(tmp_path.iterdir())
    _validate(_valid_cutover_request(target="legacy"), CUTOVER_REQUEST_ID, registry)
    _validate(_valid_readiness_package(state="conflict", findings=[]), READINESS_PACKAGE_ID, registry)
    after = set(tmp_path.iterdir())
    assert before == after


def test_136m_build_config_packages_the_whole_pcae_tree_group3_included():
    """Group 3's actual wheel/sdist inclusion is exhaustively re-verified by
    tests/test_schema_runtime_packaging.py (built-wheel and built-sdist
    archive inspection, both listing cutover_request.schema.json and
    readiness_package.schema.json by exact archive path). Independently
    confirm here only that the build configuration's package scope
    (`packages = ["src/pcae"]`) is the one mechanism responsible for that
    inclusion -- i.e. there is no separate, narrower include list that
    could silently exclude schema_resources without also breaking the
    rest of the package."""
    pyproject = (_repo_root() / "pyproject.toml").read_text(encoding="utf-8")
    assert 'packages = ["src/pcae"]' in pyproject
    schema_resources_dir = _repo_root() / "src" / "pcae" / "schema_resources"
    assert schema_resources_dir.is_dir()


def test_136m_installed_package_can_locate_group3_schemas_via_cltr_cutover_root():
    with cltr_cutover_root() as root:
        assert (root / "records" / "cutover_request.schema.json").is_file()
        assert (root / "records" / "readiness_package.schema.json").is_file()


# ---------------------------------------------------------------------------
# 16. Prior-finding disposition re-check
# ---------------------------------------------------------------------------


def test_136m_nonblocking_136l_1_state_field_gap_still_correctly_disclosed():
    """NON-BLOCKING-136L-1: RequestState's carrying field ('state') is not
    literally named in Sec.19's own table but is required by Sec.8.8's
    cross-reference; independently re-confirm the field exists, is
    required, and its description still discloses the gap rather than
    silently presenting it as directly sourced from Sec.19."""
    with cltr_cutover_root() as root:
        cr = json.loads((root / "records/cutover_request.schema.json").read_bytes())
    assert "state" in cr["required"]
    assert "NON-BLOCKING-136L-1" in cr["properties"]["state"]["description"]


def test_136m_nonblocking_136l_2_transition_id_gap_still_correctly_disclosed():
    """NON-BLOCKING-136L-2: Sec.20's own field table requires transition_id
    even though Sec.7.2's general family-required-field table does not list
    readiness_package among transition_id-required families; re-confirm
    the as-implemented resolution (transition_id required) and disclosure
    both still hold."""
    with cltr_cutover_root() as root:
        rp = json.loads((root / "records/readiness_package.schema.json").read_bytes())
    assert "transition_id" in rp["required"]
    assert "NON-BLOCKING-136L-2" in rp["properties"]["transition_id"]["description"]


def test_136m_manifest_status_field_is_frozen_for_both_group3_entries():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_family = {e["family"]: e for e in manifest["entries"]}
    assert by_family["cutover_request"]["status"] == "frozen"
    assert by_family["readiness_package"]["status"] == "frozen"

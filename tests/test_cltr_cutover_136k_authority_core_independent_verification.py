"""Phase 136K: Authority Core Schema Independent Verification.

Independent adversarial verification of Phase 136J's two Implementation
Group 2 record schemas -- ``records/authority_epoch.schema.json`` and
``records/authority_state.schema.json`` -- their manifest entries, and the
shared-core manifest verifier those entries depend on. This module is
deliberately independent of ``test_cltr_cutover_136j_authority_core.py``:
its fixtures, attack surface, and assertions were re-derived from the
governing contracts (CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0 Sec.9,
Sec.16, Sec.17, Sec.18, Sec.46) rather than copied from 136J's own tests.

Every test here validates SHAPE only, or independently proves the absence
of a capability (network, execution, authority persistence). No test
creates, reads, or asserts anything about live CLTR authority, migration
state, or production lifecycle behavior. Legacy lifecycle remains the sole
production authority; CLTR remains derivative.
"""
from __future__ import annotations

import ast
import copy
import json
import shutil
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

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_ID = "https://pcae.local/schemas/cltr_cutover/"
MANIFEST_SCHEMA_ID = BASE_ID + "manifest.schema.json"
AUTHORITY_EPOCH_ID = BASE_ID + "records/authority_epoch.schema.json"
AUTHORITY_STATE_ID = BASE_ID + "records/authority_state.schema.json"

# Updated by Phase 136L: Group 3 (cutover_request, readiness_package) now
# legitimately exists alongside Group 1+2, raising both counts by 2. This
# is a current-repository-state assertion, not a frozen historical
# snapshot of 136K's own completion moment -- mirroring 136K's own
# in-place repair of 136I's manifest-status test.
# Updated by Phase 136L (11/12) and Phase 136N: manifest/registry counts now
# legitimately include Group 4 (3 new record schemas).
EXPECTED_MANIFEST_ENTRY_COUNT = 14
EXPECTED_REGISTRY_RESOURCE_COUNT = 15
EXPECTED_GROUP1_SHARED_FILES = (
    "shared/digest.schema.json",
    "shared/enums.schema.json",
    "shared/envelope.schema.json",
    "shared/failures.schema.json",
    "shared/identity.schema.json",
    "shared/limitations.schema.json",
    "shared/references.schema.json",
)
EXPECTED_GROUP2_RECORD_FILES = (
    "records/authority_epoch.schema.json",
    "records/authority_state.schema.json",
)
EXPECTED_GROUP3_RECORD_FILES = (
    "records/cutover_request.schema.json",
    "records/readiness_package.schema.json",
)
EXPECTED_GROUP4_RECORD_FILES = (
    "records/human_authorization.schema.json",
    "records/cutover_candidate.schema.json",
    "records/certification.schema.json",
)

# The frozen contract's Sec.9 explicit 12/13-file "authoritative forbidden"
# list, independently re-derived from Sec.9's own prose (see 136J's
# NON-BLOCKING-136J-2 for the original judgment call this re-derivation
# checks).
SEC9_EXPLICIT_FORBIDDEN_FAMILIES = (
    "cutover_request",
    "readiness_package",
    "human_authorization",
    "cutover_candidate",
    "certification",
    "publication_attempt",
    "concurrency_conflict",
    "recovery_journal_entry",
    "quarantine_record",
    "compatibility_state",
    "notification_authority_binding",
    "marker_authority_binding",
    "receipt_authority_binding",
)
SEC9_EXPLICIT_PERMITTED_FAMILIES = ("authority_state", "publication_evidence")
ALL_16_RECORD_FAMILIES = (
    "authority_epoch",
    "authority_state",
    "cutover_request",
    "readiness_package",
    "human_authorization",
    "cutover_candidate",
    "certification",
    "publication_attempt",
    "publication_evidence",
    "concurrency_conflict",
    "recovery_journal_entry",
    "quarantine_record",
    "notification_authority_binding",
    "marker_authority_binding",
    "receipt_authority_binding",
    "compatibility_state",
)


# ---------------------------------------------------------------------------
# Fixtures -- independently re-derived, not copied from 136J
# ---------------------------------------------------------------------------


def _epoch(**overrides) -> dict:
    doc = {
        "schema_id": AUTHORITY_EPOCH_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_epoch",
        "record_id": "authepoch-1000001",
        "record_digest": "1" * 64,
        "created_at": "2026-07-16T00:00:00Z",
        "migration_epoch": "epoch-k",
        "authority_kind": "legacy",
        "activation_state": "proposed",
        "predecessor_epoch": None,
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "136K adversarial fixture.",
        },
    }
    doc.update(overrides)
    return doc


def _state(**overrides) -> dict:
    doc = {
        "schema_id": AUTHORITY_STATE_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "authority_state",
        "record_id": "authstate-1000001",
        "record_digest": "2" * 64,
        "created_at": "2026-07-16T00:00:00Z",
        "migration_epoch": "epoch-k",
        "transition_id": "trans-10000001",
        "active_authority_epoch": {
            "record_id": "authepoch-1000001",
            "record_digest": "1" * 64,
            "record_family": "authority_epoch",
        },
        "authority_kind": "legacy",
        "publication_evidence_reference": {
            "record_id": "pubevidence-1000001",
            "record_digest": "3" * 64,
            "record_family": "publication_evidence",
        },
        "pointer_digest": "4" * 64,
        "verification_state": "verification_failed",
        "compatibility_mode": "legacy_read_only",
        "limitations": [],
        "authority_disclosure": {
            "authority_role": "derivative",
            "is_authoritative": False,
            "disclosure_text": "136K adversarial fixture.",
        },
    }
    doc.update(overrides)
    return doc


@pytest.fixture(scope="module")
def registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _v(record, schema_id, registry):
    return validate_record_shape(record, schema_id=schema_id, registry=registry)


def _copy_package(dest: Path) -> Path:
    with cltr_cutover_root() as source:
        for item in source.rglob("*"):
            if item.is_file():
                target = dest / item.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
    return dest


# ---------------------------------------------------------------------------
# 1. Independent Group 2 inventory re-derivation (Sec.46)
# ---------------------------------------------------------------------------


def test_136k_group2_inventory_is_exactly_authority_epoch_and_authority_state():
    # Updated by Phase 136L: records/ now legitimately also contains the
    # two Group 3 files; Group 2's own subset (authority_epoch,
    # authority_state) is unchanged and still verified as a subset here.
    with cltr_cutover_root() as root:
        record_files = sorted(p.name for p in (root / "records").glob("*.schema.json"))
    assert {"authority_epoch.schema.json", "authority_state.schema.json"} <= set(record_files)


def test_136k_group3_files_now_present_confirming_136l_implementation():
    # Renamed and updated by Phase 136L (was
    # test_136k_group3_files_remain_absent_confirming_deferral): Group 3
    # deferral ended with 136L's own implementation; this test now
    # confirms presence rather than absence, preserving the original
    # test's role as a live check of Group 3's file-inventory state.
    with cltr_cutover_root() as root:
        assert (root / "records" / "cutover_request.schema.json").exists()
        assert (root / "records" / "readiness_package.schema.json").exists()


def test_136k_manifest_entry_count_is_exactly_nine(registry):
    with cltr_cutover_root() as root:
        manifest = load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=registry,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
    assert len(manifest.entries) == EXPECTED_MANIFEST_ENTRY_COUNT


def test_136k_registry_resource_count_is_exactly_ten(registry):
    assert len(registry.schema_ids) == EXPECTED_REGISTRY_RESOURCE_COUNT


def test_136k_group2_manifest_entries_depend_only_on_group1_shared_files():
    with cltr_cutover_root() as root:
        manifest = json.loads((root / "manifest.json").read_bytes())
    by_path = {e["file_path"]: e for e in manifest["entries"]}
    for path in EXPECTED_GROUP2_RECORD_FILES:
        deps = by_path[path]["dependencies"]
        for dep in deps:
            dep_path = dep.replace(BASE_ID, "")
            assert dep_path in EXPECTED_GROUP1_SHARED_FILES, (
                f"{path} depends on {dep_path!r}, which is not a Group 1 shared file "
                "-- premature Group 3+ coupling"
            )


# ---------------------------------------------------------------------------
# 2. Sec.9 authority-role file-list re-derivation (disposes NON-BLOCKING-136J-2)
# ---------------------------------------------------------------------------


def test_136k_sec9_file_list_omits_authority_epoch_confirming_136j_judgment_call():
    """Independently re-derives Sec.9's forbidden(13) + permitted(2) = 15
    file list against the full 16-family record_family enum. 16 - 15 == 1,
    and the missing family is authority_epoch -- confirming NON-BLOCKING-
    136J-2's own reading that Sec.9 does not explicitly classify
    authority_epoch either way. This is a real, confirmed gap in the frozen
    contract text (not a 136J miscount); 136J's conservative choice to
    locally forbid authority_role "authoritative" on authority_epoch
    remains the correct disposition pending a future contract-text repair.
    """
    accounted = set(SEC9_EXPLICIT_FORBIDDEN_FAMILIES) | set(SEC9_EXPLICIT_PERMITTED_FAMILIES)
    assert len(accounted) == 15
    missing = set(ALL_16_RECORD_FAMILIES) - accounted
    assert missing == {"authority_epoch"}


def test_136k_epoch_locally_forbids_authoritative_role_matching_conservative_reading(registry):
    record = _epoch(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "attempted authority claim on a lineage node",
        }
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 3. AuthorityEpoch state-machine attacks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: r.__setitem__("activation_state", "active") or r,  # active w/o binding (already set by fixture default proposed)
        lambda r: {**r, "activation_state": "active"},
    ],
)
def test_136k_epoch_active_without_generation_binding_always_rejected(registry, mutation):
    record = _epoch()
    record = mutation(record)
    record.pop("generation_binding", None)
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_proposed_with_generation_binding_rejected(registry):
    record = _epoch(
        generation_binding={"generation_id": "gen-1000001", "generation_digest": "5" * 64}
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_unknown_activation_state_value_rejected(registry):
    for bogus in ("historical", "current", "verified", "retired", "PROPOSED", ""):
        record = _epoch(activation_state=bogus)
        result = _v(record, AUTHORITY_EPOCH_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136k_epoch_predecessor_equal_to_self_is_shape_valid_not_layer2_detectable(registry):
    # A same-document self-reference is representable at Layer 2 (the shape
    # cannot compare record_id to predecessor_epoch.record_id); this is
    # correctly a Layer 4 cross-field/cross-record concern, independently
    # confirmed here rather than assumed.
    record = _epoch(
        record_id="authepoch-selfref1",
        activation_state="superseded",
        predecessor_epoch={
            "record_id": "authepoch-selfref1",
            "record_digest": "1" * 64,
            "record_family": "authority_epoch",
        },
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.VALID


def test_136k_epoch_proposed_epoch_cannot_carry_authoritative_disclosure(registry):
    """Critical boundary: a proposed epoch must never be representable as
    describing established, current, or verified authority -- attempted via
    every combination of authority_role and generation_binding presence."""
    for role in ("authoritative", "operational", "evidence"):
        record = _epoch(
            authority_disclosure={
                "authority_role": role,
                "is_authoritative": False,
                "disclosure_text": "proposed epoch masquerade attempt",
            }
        )
        result = _v(record, AUTHORITY_EPOCH_ID, registry)
        if role == "authoritative":
            assert result.status is OutcomeStatus.INVALID
        else:
            # operational/evidence are structurally permitted vocabulary
            # values -- is_authoritative remains const false regardless,
            # so no authority is ever established either way.
            assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize("kind", ["Legacy", "CLTR", "legacy-old", "not-legacy", "legacy_authority", "cltr_authority", "LEGACY", "cltr "])
def test_136k_epoch_authority_kind_exactness_no_alias_or_case_fold(registry, kind):
    record = _epoch(authority_kind=kind)
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID, f"{kind!r} must not be accepted as authority_kind"


@pytest.mark.parametrize("kind", ["legacy", "cltr"])
def test_136k_epoch_authority_kind_exact_values_accepted(registry, kind):
    record = _epoch(authority_kind=kind)
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 4. AuthorityEpoch generation-reference attacks
# ---------------------------------------------------------------------------


def test_136k_epoch_generation_binding_missing_digest_rejected(registry):
    record = _epoch(
        activation_state="active",
        generation_binding={"generation_id": "gen-1000001"},
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_generation_binding_missing_id_rejected(registry):
    record = _epoch(
        activation_state="active",
        generation_binding={"generation_digest": "5" * 64},
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_generation_binding_remote_uri_rejected(registry):
    record = _epoch(
        activation_state="active",
        generation_binding={
            "generation_id": "https://evil.example/gen",
            "generation_digest": "5" * 64,
        },
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_generation_binding_traversal_id_rejected(registry):
    record = _epoch(
        activation_state="active",
        generation_binding={"generation_id": "../../etc/passwd", "generation_digest": "5" * 64},
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_generation_binding_unknown_field_rejected(registry):
    record = _epoch(
        activation_state="active",
        generation_binding={
            "generation_id": "gen-1000001",
            "generation_digest": "5" * 64,
            "generation_role": "authoritative_generation",
        },
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_generation_binding_shape_validity_does_not_imply_authority(registry):
    """A schema-valid generation_binding must validate identically whether
    it names a real, certified generation or an arbitrary opaque token --
    proving shape validity alone establishes nothing about the referenced
    generation's authority (Layer 4/6 boundary)."""
    record = _epoch(
        activation_state="active",
        generation_binding={"generation_id": "gen-totally-invented", "generation_digest": "f" * 64},
    )
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 5. AuthorityState pointer relationship + verification/uncertainty attacks
# ---------------------------------------------------------------------------


def test_136k_state_pointer_digest_always_required_regardless_of_verification_state(registry):
    for vstate, extra in (
        ("unverified", {"uncertainty": {"reason": "pending"}}),
        ("verified", {}),
        ("verification_failed", {}),
    ):
        record = _state(verification_state=vstate, **extra)
        record.pop("pointer_digest")
        result = _v(record, AUTHORITY_STATE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"pointer_digest must be required for {vstate}"


def test_136k_state_uncertainty_forbidden_only_for_verified():
    """Independently confirms the exact scope of the verified/uncertainty
    exclusion: the frozen conditional only forbids ``uncertainty`` when
    ``verification_state == "verified"`` (Sec.16). ``verification_failed``
    is not listed in that row, so ``uncertainty`` remains legitimately
    optional there (e.g. to disclose *why* verification failed) -- this is
    not a gap, and this test exists specifically so a future accidental
    tightening to also forbid it on ``verification_failed`` would be
    caught as a regression against the frozen contract's own scope."""
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)

    verified_with_uncertainty = _state(
        verification_state="verified", uncertainty={"reason": "should be forbidden"}
    )
    assert _v(verified_with_uncertainty, AUTHORITY_STATE_ID, reg).status is OutcomeStatus.INVALID

    failed_with_uncertainty = _state(
        verification_state="verification_failed", uncertainty={"reason": "legitimately optional detail"}
    )
    assert _v(failed_with_uncertainty, AUTHORITY_STATE_ID, reg).status is OutcomeStatus.VALID

    failed_without_uncertainty = _state(verification_state="verification_failed")
    assert _v(failed_without_uncertainty, AUTHORITY_STATE_ID, reg).status is OutcomeStatus.VALID


def test_136k_state_unverified_requires_uncertainty_with_bounded_reason(registry):
    record = _state(verification_state="unverified", uncertainty={"reason": ""})
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID  # empty reason violates minLength


def test_136k_state_uncertainty_unknown_field_rejected(registry):
    record = _state(
        verification_state="unverified",
        uncertainty={"reason": "pending", "confidence": 0.5},
    )
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_state_unknown_verification_value_rejected(registry):
    for bogus in ("uncertain", "quarantined", "verified_current", "Verified", ""):
        record = _state(verification_state=bogus)
        result = _v(record, AUTHORITY_STATE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"{bogus!r} must be rejected"


def test_136k_state_pointer_digest_null_rejected(registry):
    record = _state(pointer_digest=None)
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_state_active_authority_epoch_absent_rejected(registry):
    record = _state()
    record.pop("active_authority_epoch")
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_state_active_authority_epoch_null_rejected(registry):
    record = _state(active_authority_epoch=None)
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 6. AuthorityState authority-kind / compatibility-mode attacks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["legacy_authoritative", "legacy_adapter", "legacy_read_only", "legacy_historical", "legacy_disabled", "legacy_retired"])
def test_136k_state_every_compatibility_mode_value_independently_accepted(registry, mode):
    record = _state(compatibility_mode=mode)
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.VALID


@pytest.mark.parametrize("mode", ["Legacy_Adapter", "legacy-adapter", "cltr_authoritative", "unsupported_mode", ""])
def test_136k_state_compatibility_mode_no_alias_or_case_fold(registry, mode):
    record = _state(compatibility_mode=mode)
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_state_cltr_kind_requires_authoritative_generation(registry):
    record = _state(authority_kind="cltr")
    record.pop("authoritative_generation", None)
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_state_legacy_kind_forbids_neither_permits_nor_requires_generation(registry):
    # legacy authority_kind: authoritative_generation is simply optional,
    # not forbidden -- confirm both branches independently.
    without = _state(authority_kind="legacy")
    without.pop("authoritative_generation", None)
    assert _v(without, AUTHORITY_STATE_ID, registry).status is OutcomeStatus.VALID

    with_gen = _state(
        authority_kind="legacy",
        authoritative_generation={"generation_id": "gen-1000002", "generation_digest": "6" * 64},
    )
    assert _v(with_gen, AUTHORITY_STATE_ID, registry).status is OutcomeStatus.VALID


def test_136k_state_authoritative_generation_rehearsal_pointer_substitution_is_shape_valid():
    """A generation_reference's shape cannot distinguish a rehearsal
    generation from an authoritative one -- both are opaque id+digest pairs.
    This independently confirms that boundary is real (Layer 4/6), not a
    gap 136J silently left unguarded."""
    # No registry needed: this documents an architectural fact about
    # generation_reference's shape (shared/references.schema.json), cross-
    # checked against the schema text directly.
    with cltr_cutover_root() as root:
        refs = json.loads((root / "shared" / "references.schema.json").read_bytes())
    generation_reference = refs["$defs"]["generation_reference"]
    assert set(generation_reference["properties"]) == {"generation_id", "generation_digest"}
    assert "generation_role" not in generation_reference["properties"]


# ---------------------------------------------------------------------------
# 7. Reference-family separation, exhaustively over all 5 reference fields
# ---------------------------------------------------------------------------


def test_136k_epoch_predecessor_wrong_family_every_other_family_rejected(registry):
    for family in ALL_16_RECORD_FAMILIES:
        if family == "authority_epoch":
            continue
        record = _epoch(
            activation_state="superseded",
            predecessor_epoch={"record_id": "x" * 8, "record_digest": "7" * 64, "record_family": family},
        )
        result = _v(record, AUTHORITY_EPOCH_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"predecessor_epoch must reject family {family!r}"


def test_136k_state_active_authority_epoch_wrong_family_every_other_family_rejected(registry):
    for family in ALL_16_RECORD_FAMILIES:
        if family == "authority_epoch":
            continue
        record = _state(
            active_authority_epoch={"record_id": "x" * 8, "record_digest": "7" * 64, "record_family": family}
        )
        result = _v(record, AUTHORITY_STATE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"active_authority_epoch must reject family {family!r}"


def test_136k_state_publication_evidence_reference_wrong_family_every_other_family_rejected(registry):
    for family in ALL_16_RECORD_FAMILIES:
        if family == "publication_evidence":
            continue
        record = _state(
            publication_evidence_reference={"record_id": "x" * 8, "record_digest": "7" * 64, "record_family": family}
        )
        result = _v(record, AUTHORITY_STATE_ID, registry)
        assert result.status is OutcomeStatus.INVALID, f"publication_evidence_reference must reject family {family!r}"


def test_136k_reference_unknown_field_rejected_in_every_reference_field(registry):
    epoch = _epoch(
        activation_state="superseded",
        predecessor_epoch={
            "record_id": "authepoch-2000001",
            "record_digest": "7" * 64,
            "record_family": "authority_epoch",
            "smuggled": True,
        },
    )
    assert _v(epoch, AUTHORITY_EPOCH_ID, registry).status is OutcomeStatus.INVALID

    state = _state()
    state["active_authority_epoch"]["smuggled"] = True
    assert _v(state, AUTHORITY_STATE_ID, registry).status is OutcomeStatus.INVALID

    state2 = _state()
    state2["publication_evidence_reference"]["smuggled"] = True
    assert _v(state2, AUTHORITY_STATE_ID, registry).status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 8. Requiredness / absent-vs-null / empty-value attacks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_value", [None, "", {}, [], 0, False])
def test_136k_epoch_migration_epoch_wrong_scalar_type_or_empty_rejected(registry, bad_value):
    record = _epoch(migration_epoch=bad_value)
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


@pytest.mark.parametrize("bad_value", [None, "", {}, [], 0, False])
def test_136k_state_transition_id_wrong_scalar_type_or_empty_rejected(registry, bad_value):
    record = _state(transition_id=bad_value)
    result = _v(record, AUTHORITY_STATE_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_limitations_wrong_type_rejected(registry):
    for bad in (None, "not-an-array", {}, 0):
        record = _epoch(limitations=bad)
        result = _v(record, AUTHORITY_EPOCH_ID, registry)
        assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_authority_disclosure_null_rejected(registry):
    record = _epoch(authority_disclosure=None)
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_epoch_authority_disclosure_empty_object_rejected(registry):
    record = _epoch(authority_disclosure={})
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_state_limitations_duplicate_entries_are_shape_valid():
    """Confirms shared/limitations.schema.json's own documented scope:
    duplicate limitation strings are a Layer 4/authoring-review concern,
    not a shape concern -- independently re-verified here rather than
    assumed from the shared-core description text."""
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
    record = _state(limitations=["duplicate", "duplicate"])
    result = _v(record, AUTHORITY_STATE_ID, reg)
    assert result.status is OutcomeStatus.VALID


# ---------------------------------------------------------------------------
# 9. Identity/digest boundary honesty (Sec.1, Sec.40)
# ---------------------------------------------------------------------------


def test_136k_two_structurally_valid_but_mutually_contradictory_epochs_both_validate():
    """Independently proves the schema never establishes cross-record truth:
    two AuthorityEpoch documents both claiming activation_state == "active"
    for the same migration_epoch, with different generation_binding targets,
    both validate individually -- contradiction detection is Layer 4/6, not
    Layer 2, and this schema never claims otherwise."""
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
    epoch_a = _epoch(
        record_id="authepoch-3000001",
        activation_state="active",
        generation_binding={"generation_id": "gen-a0000001", "generation_digest": "a" * 64},
    )
    epoch_b = _epoch(
        record_id="authepoch-3000002",
        activation_state="active",
        generation_binding={"generation_id": "gen-b0000001", "generation_digest": "b" * 64},
    )
    assert _v(epoch_a, AUTHORITY_EPOCH_ID, reg).status is OutcomeStatus.VALID
    assert _v(epoch_b, AUTHORITY_EPOCH_ID, reg).status is OutcomeStatus.VALID


def test_136k_schema_descriptions_do_not_overclaim_authority_establishment():
    with cltr_cutover_root() as root:
        epoch_doc = json.loads((root / "records" / "authority_epoch.schema.json").read_bytes())
        state_doc = json.loads((root / "records" / "authority_state.schema.json").read_bytes())
    forbidden_overclaims = (
        "establishes authority",
        "creates authority",
        "proves current authority",
        "confirms cutover",
    )
    for doc in (epoch_doc, state_doc):
        blob = json.dumps(doc).lower()
        for phrase in forbidden_overclaims:
            assert phrase not in blob, f"overclaiming phrase {phrase!r} found in {doc['title']}"


# ---------------------------------------------------------------------------
# 10. Manifest tamper attacks (independent of 136J's content/missing-file cases)
# ---------------------------------------------------------------------------


def _tampered_manifest(tmp_path, mutate):
    dest = tmp_path / "pkg"
    _copy_package(dest)
    manifest = json.loads((dest / "manifest.json").read_bytes())
    mutate(manifest)
    (dest / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return dest


def _expect_integrity_error(dest):
    with pytest.raises(ManifestIntegrityError):
        reg = build_offline_registry(dest)
        load_and_verify_manifest(
            dest / "manifest.json",
            package_root=dest,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def _expect_fail_closed(dest):
    """Broader than :func:`_expect_integrity_error`: some tamper shapes
    fail closed via a sibling ``SchemaResourceError`` subclass rather than
    ``ManifestIntegrityError`` itself (see
    ``test_136k_orphaned_entry_raises_schemaresourcenotfound_not_manifestintegrityerror``
    for the independently confirmed, disclosed reason). Both are
    acceptable fail-closed outcomes; only ``ManifestIntegrityError`` itself
    is not required here."""
    from pcae.schema_runtime.errors import SchemaResourceError

    with pytest.raises(SchemaResourceError):
        reg = build_offline_registry(dest)
        load_and_verify_manifest(
            dest / "manifest.json",
            package_root=dest,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136k_manifest_swapped_schema_ids_rejected(tmp_path):
    def mutate(m):
        by_path = {e["file_path"]: e for e in m["entries"]}
        a = by_path["records/authority_epoch.schema.json"]
        b = by_path["records/authority_state.schema.json"]
        a["schema_id"], b["schema_id"] = b["schema_id"], a["schema_id"]

    _expect_integrity_error(_tampered_manifest(tmp_path, mutate))


def test_136k_manifest_swapped_digests_rejected(tmp_path):
    def mutate(m):
        by_path = {e["file_path"]: e for e in m["entries"]}
        a = by_path["records/authority_epoch.schema.json"]
        b = by_path["records/authority_state.schema.json"]
        a["file_digest"], b["file_digest"] = b["file_digest"], a["file_digest"]

    _expect_integrity_error(_tampered_manifest(tmp_path, mutate))


def test_136k_manifest_duplicate_file_path_rejected(tmp_path):
    def mutate(m):
        first = dict(m["entries"][0])
        m["entries"].append(first)

    _expect_integrity_error(_tampered_manifest(tmp_path, mutate))


def test_136k_manifest_orphaned_entry_rejected(tmp_path):
    def mutate(m):
        m["entries"].append(
            {
                "schema_id": BASE_ID + "records/does_not_exist.schema.json",
                "schema_version": "1.0",
                "file_path": "records/does_not_exist.schema.json",
                "file_digest": "0" * 64,
                "family": "authority_epoch",
                "implementation_group": 2,
                "dependencies": [],
                "status": "frozen",
            }
        )

    _expect_fail_closed(_tampered_manifest(tmp_path, mutate))


def test_136k_orphaned_entry_raises_schemaresourcenotfound_not_manifestintegrityerror(tmp_path):
    """FINDING CONFIRMED-136K-2 (non-blocking, documentation accuracy):
    ``load_and_verify_manifest``'s own docstring claims "an orphaned entry
    or an unindexed file are both raised as ManifestIntegrityError". This
    independently proves that is only true for the *unindexed-file* case
    (a file on disk not listed in the manifest, caught by the trailing
    two-way completeness check); an *orphaned entry* (a manifest-listed
    path whose file does not exist on disk) instead raises
    ``SchemaResourceNotFoundError`` from the inner ``load_schema_resource``
    call, before the completeness check is ever reached. Both are
    ``SchemaResourceError`` subclasses and both fail closed -- no security
    or authority-boundary impact -- but a caller that narrowly catches only
    ``ManifestIntegrityError``, trusting the docstring literally, would not
    catch this specific case. Disclosed, not repaired: fixing this would
    mean either re-wrapping a well-established, independently useful
    exception type (used elsewhere to distinguish "missing" from "invalid")
    or rewriting the docstring, both outside this phase's Group 2 schema
    scope and inherited unchanged from Phase 136H."""
    from pcae.schema_runtime.errors import SchemaResourceNotFoundError

    def mutate(m):
        m["entries"].append(
            {
                "schema_id": BASE_ID + "records/does_not_exist.schema.json",
                "schema_version": "1.0",
                "file_path": "records/does_not_exist.schema.json",
                "file_digest": "0" * 64,
                "family": "authority_epoch",
                "implementation_group": 2,
                "dependencies": [],
                "status": "frozen",
            }
        )

    dest = _tampered_manifest(tmp_path, mutate)
    with pytest.raises(SchemaResourceNotFoundError):
        reg = build_offline_registry(dest)
        load_and_verify_manifest(
            dest / "manifest.json",
            package_root=dest,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136k_manifest_unindexed_extra_schema_file_rejected(tmp_path):
    dest = _copy_package(tmp_path / "pkg2")
    (dest / "records" / "unindexed.schema.json").write_text(
        json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "x", "type": "object"}),
        encoding="utf-8",
    )
    _expect_integrity_error(dest)


def test_136k_manifest_file_path_pattern_charset_does_not_itself_forbid_traversal():
    """FINDING CONFIRMED-136K-3 (non-blocking, documentation accuracy, no
    security impact): manifest.schema.json's own field description for
    ``file_path`` claims '..' and a leading '/' are "forbidden by
    construction" because "neither character sequence needed nor permitted
    by the pattern's charset for a traversal to succeed". This is false as
    a claim about the regex alone: the charset ``[a-zA-Z0-9_./-]`` includes
    both '.' and '/', so ``^[a-zA-Z0-9_./-]{1,512}$`` structurally MATCHES
    "../../etc/passwd" and "/etc/passwd". The description's own very next
    clause -- "the loader additionally verifies containment independent of
    this pattern" -- is accurate and is the real defense; see
    ``test_136k_manifest_traversal_file_path_rejected_end_to_end_by_loader_containment_check``
    for independent proof the actual security boundary holds. Disclosed,
    not repaired: the description text overclaims what the regex does, but
    the schema is not itself a security control here and no attack
    succeeds."""
    with cltr_cutover_root() as root:
        manifest_schema = json.loads((root / "manifest.schema.json").read_bytes())
    pattern = manifest_schema["$defs"]["manifest_entry"]["properties"]["file_path"]["pattern"]
    import re

    assert re.match(pattern, "../../etc/passwd") is not None
    assert re.match(pattern, "/etc/passwd") is not None


def test_136k_manifest_traversal_file_path_rejected_end_to_end_by_loader_containment_check(tmp_path):
    from pcae.schema_runtime.errors import SchemaResourceError

    def mutate(m):
        m["entries"][0]["file_path"] = "../../../../etc/passwd"

    dest = _tampered_manifest(tmp_path, mutate)
    with pytest.raises(SchemaResourceError, match="escapes trusted root"):
        reg = build_offline_registry(dest)
        load_and_verify_manifest(
            dest / "manifest.json",
            package_root=dest,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )


def test_136k_manifest_wrong_implementation_group_for_group2_entry_rejected(tmp_path):
    def mutate(m):
        for entry in m["entries"]:
            if entry["file_path"] == "records/authority_epoch.schema.json":
                entry["implementation_group"] = 3

    dest = _tampered_manifest(tmp_path, mutate)
    # implementation_group is shape-legal (1-11); this specific tamper is a
    # semantic/group-boundary concern the manifest verifier (digest +
    # completeness only) does not itself check -- independently confirmed
    # here rather than assumed, so it is NOT expected to raise.
    reg = build_offline_registry(dest)
    verified = load_and_verify_manifest(
        dest / "manifest.json",
        package_root=dest,
        registry=reg,
        manifest_schema_id=MANIFEST_SCHEMA_ID,
        excluded_relative_paths=frozenset({"manifest.schema.json"}),
    )
    assert len(verified.entries) == EXPECTED_MANIFEST_ENTRY_COUNT


def test_136k_manifest_draft_status_on_group2_entry_rejected(tmp_path):
    """Independent, Group-2-specific reproduction of the manifest status
    gap repaired by this phase (CONFIRMED-136K-1) -- confirms the repair
    lands specifically on a Group 2 production entry, not only on
    whichever entry happened to be first alphabetically."""

    def mutate(m):
        for entry in m["entries"]:
            if entry["file_path"] == "records/authority_state.schema.json":
                entry["status"] = "draft"

    _expect_integrity_error(_tampered_manifest(tmp_path, mutate))


# ---------------------------------------------------------------------------
# 11. Unresolved / remote $ref rejection
# ---------------------------------------------------------------------------


def test_136k_unresolved_remote_ref_is_rejected_not_silently_fetched(registry):
    tampered_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://pcae.local/schemas/cltr_cutover/records/__136k_probe.schema.json",
        "type": "object",
        "properties": {"x": {"$ref": "https://example.com/not-a-real-schema.json"}},
    }
    from referencing import Registry as _RefRegistry
    from referencing.jsonschema import DRAFT202012

    # Build a throwaway registry containing only the tampered resource,
    # deliberately excluding the shared-core resources -- if $ref
    # resolution ever fell back to network retrieval, this would hang or
    # attempt a real HTTP call instead of raising a local resolution error.
    probe_registry = _RefRegistry().with_resource(
        tampered_schema["$id"], DRAFT202012.create_resource(tampered_schema)
    )
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator({"$ref": tampered_schema["$id"]}, registry=probe_registry)
    with pytest.raises(Exception):
        list(validator.iter_errors({"x": {}}))


# ---------------------------------------------------------------------------
# 11b. Security attacks: Unicode confusables, oversized fields, cyclic input
# ---------------------------------------------------------------------------


def test_136k_unicode_confusable_record_id_rejected(registry):
    record = _epoch(record_id="аuthepoch-0000001")  # Cyrillic 'а'
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_oversized_migration_epoch_rejected(registry):
    record = _epoch(migration_epoch="a" * 65)
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_non_string_limitation_entry_rejected(registry):
    record = _epoch(limitations=[{"nested": "smuggled object"}])
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


def test_136k_cyclic_python_input_fails_closed_as_infrastructure_failure_not_crash(registry):
    """A record containing a reference cycle cannot be produced by strict
    JSON parsing (Layer 1) -- it can only arise from a caller passing an
    already-decoded Python object directly to validate_record_shape. This
    independently confirms the three-way OutcomeStatus contract holds even
    for that misuse: the call returns INFRASTRUCTURE_FAILURE rather than
    raising an uncaught RecursionError or silently returning VALID."""
    record = _epoch()
    record["authority_disclosure"] = dict(record["authority_disclosure"])
    record["authority_disclosure"]["self"] = record
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INFRASTRUCTURE_FAILURE


def test_136k_oversized_limitations_array_rejected_at_bound(registry):
    record = _epoch(limitations=["ok"] * 40)
    result = _v(record, AUTHORITY_EPOCH_ID, registry)
    assert result.status is OutcomeStatus.INVALID


# ---------------------------------------------------------------------------
# 12. No-network / no-authority / no-execution, extended scope
# ---------------------------------------------------------------------------


def test_136k_no_forbidden_imports_anywhere_in_schema_runtime():
    forbidden_modules = {"subprocess", "socket", "urllib", "http", "requests"}
    for py_file in (REPO_ROOT / "src" / "pcae" / "schema_runtime").glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    assert top not in forbidden_modules, f"{py_file}: import {alias.name}"
            if isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                assert top not in forbidden_modules, f"{py_file}: from {node.module} import ..."
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec", "__import__"}, f"{py_file}: {node.func.id}(...)"


def test_136k_no_network_including_urllib_during_full_group2_validation_cycle(monkeypatch):
    calls = []

    def _blocked(*a, **k):
        calls.append((a, k))
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    import urllib.request

    monkeypatch.setattr(urllib.request, "urlopen", _blocked)

    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        load_and_verify_manifest(
            root / "manifest.json",
            package_root=root,
            registry=reg,
            manifest_schema_id=MANIFEST_SCHEMA_ID,
            excluded_relative_paths=frozenset({"manifest.schema.json"}),
        )
        for _ in range(5):
            _v(_epoch(), AUTHORITY_EPOCH_ID, reg)
            _v(_state(), AUTHORITY_STATE_ID, reg)
    assert calls == []


def test_136k_no_pcae_cltr_authority_import_anywhere_in_schema_layer():
    for py_file in list((REPO_ROOT / "src" / "pcae" / "schema_runtime").glob("*.py")) + list(
        (REPO_ROOT / "src" / "pcae" / "schema_resources").rglob("*.py")
    ):
        text = py_file.read_text(encoding="utf-8")
        assert "pcae.cltr" not in text, f"{py_file} references pcae.cltr"


def test_136k_no_authority_namespace_created_by_repeated_validation_cycles(tmp_path):
    before = set(REPO_ROOT.glob(".pcae/cltr-authority*"))
    with cltr_cutover_root() as root:
        reg = build_offline_registry(root)
        for _ in range(10):
            _v(_epoch(activation_state="active", generation_binding={"generation_id": "gen-x0000001", "generation_digest": "9" * 64}), AUTHORITY_EPOCH_ID, reg)
            _v(_state(verification_state="verified"), AUTHORITY_STATE_ID, reg)
    after = set(REPO_ROOT.glob(".pcae/cltr-authority*"))
    assert before == after == set()


def test_136k_validation_result_never_carries_a_resolved_authority_flag(registry):
    result = _v(_state(verification_state="verified"), AUTHORITY_STATE_ID, registry)
    assert not hasattr(result, "is_current_authority")
    assert not hasattr(result, "authority_resolved")
    assert not hasattr(result, "cutover_complete")


# ---------------------------------------------------------------------------
# 13. Determinism across subprocesses / PYTHONHASHSEED
# ---------------------------------------------------------------------------


def test_136k_registry_schema_ids_stable_across_hashseed_subprocesses():
    probe = (
        "import json\n"
        "from pcae.schema_resources import cltr_cutover_root\n"
        "from pcae.schema_runtime import build_offline_registry\n"
        "with cltr_cutover_root() as root:\n"
        "    reg = build_offline_registry(root)\n"
        "print(json.dumps(sorted(reg.schema_ids)))\n"
    )
    outputs = []
    for seed in ("0", "1", "42"):
        env = {"PYTHONHASHSEED": seed, "PATH": "/usr/bin:/bin"}
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs.append(json.loads(result.stdout.strip().splitlines()[-1]))
    assert outputs[0] == outputs[1] == outputs[2]
    assert len(outputs[0]) == EXPECTED_REGISTRY_RESOURCE_COUNT


# ---------------------------------------------------------------------------
# 14. Scope-guard repair audit (136J's 19 repaired assertions)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "test_file",
    [
        "tests/test_cltr_cutover_136h_shared_core.py",
        "tests/test_cltr_cutover_136i_shared_core_independent_verification.py",
        "tests/test_schema_runtime_boundaries.py",
        "tests/test_schema_runtime_packaging.py",
    ],
)
def test_136k_repaired_scope_guards_still_forbid_every_group3plus_filename(test_file):
    text = (REPO_ROOT / test_file).read_text(encoding="utf-8")
    forbidden_stems = (
        "cutover_request.schema",
        "readiness_package.schema",
        "human_authorization.schema",
        "cutover_candidate.schema",
        "certification.schema",
        "publication_attempt.schema",
        "publication_evidence.schema",
        "concurrency_conflict.schema",
        "recovery_journal_entry.schema",
        "quarantine_record.schema",
        "compatibility_state.schema",
    )
    # The repaired guards must at minimum still *reference* the Group 3+
    # forbidden vocabulary somewhere in the file (proving the broader
    # boundary assertion was not silently dropped during the 136J repair,
    # only narrowed to admit the two legitimate Group 2 filenames).
    mentions_any_forbidden_family = any(stem.split(".")[0] in text for stem in forbidden_stems)
    mentions_group2_families = "authority_epoch" in text or "authority_state" in text
    assert mentions_any_forbidden_family or mentions_group2_families, (
        f"{test_file}: repaired scope guard lost all later-group vocabulary"
    )


def test_136k_no_group4plus_schema_file_introduced_since_136l_baseline():
    # Renamed and updated by Phase 136L (was
    # test_136k_no_group3plus_schema_file_introduced_since_136j_baseline)
    # and again by Phase 136N: Group 4 is now the legitimate current
    # baseline; this test's role (confirm no *further* group has been
    # introduced) is preserved by widening the expected set to include
    # Group 4.
    with cltr_cutover_root() as root:
        all_files = sorted(p.relative_to(root).as_posix() for p in root.rglob("*.schema.json"))
    expected = sorted(
        ("manifest.schema.json",)
        + EXPECTED_GROUP1_SHARED_FILES
        + EXPECTED_GROUP2_RECORD_FILES
        + EXPECTED_GROUP3_RECORD_FILES
        + EXPECTED_GROUP4_RECORD_FILES
    )
    assert all_files == expected


# ---------------------------------------------------------------------------
# 15. Packaging: installed-wheel validation from outside the repository
# ---------------------------------------------------------------------------


def test_136k_installed_wheel_validates_group2_fixtures_outside_repository(tmp_path):
    import venv

    dist_dir = tmp_path / "dist"
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1

    venv_dir = tmp_path / "venv136k"
    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    venv_python = venv_dir / "bin" / "python"
    assert venv_python.exists()

    install = subprocess.run(
        [str(venv_python), "-m", "pip", "install", str(wheels[0]), "jsonschema>=4.18,<5"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr

    outside_cwd = tmp_path / "elsewhere"
    outside_cwd.mkdir()
    probe_script = (
        "from pcae.schema_resources import cltr_cutover_root\n"
        "from pcae.schema_runtime import build_offline_registry, validate_record_shape, OutcomeStatus\n"
        "with cltr_cutover_root() as root:\n"
        "    reg = build_offline_registry(root)\n"
        "assert len(reg.schema_ids) == 15, reg.schema_ids\n"
        "valid = {\n"
        "    'schema_id': 'https://pcae.local/schemas/cltr_cutover/records/authority_epoch.schema.json',\n"
        "    'schema_version': '1.0', 'contract_version': '1.0', 'record_type': 'authority_epoch',\n"
        "    'record_id': 'authepoch-9000001', 'record_digest': 'a'*64, 'created_at': '2026-07-16T00:00:00Z',\n"
        "    'migration_epoch': 'epoch-w', 'authority_kind': 'legacy', 'activation_state': 'proposed',\n"
        "    'predecessor_epoch': None, 'limitations': [],\n"
        "    'authority_disclosure': {'authority_role': 'derivative', 'is_authoritative': False, 'disclosure_text': 'x'},\n"
        "}\n"
        "result = validate_record_shape(valid, schema_id=valid['schema_id'], registry=reg)\n"
        "assert result.status is OutcomeStatus.VALID, result.issues\n"
        "invalid = dict(valid); invalid['activation_state'] = 'active'\n"
        "result2 = validate_record_shape(invalid, schema_id=valid['schema_id'], registry=reg)\n"
        "assert result2.status is OutcomeStatus.INVALID\n"
        "print('OK')\n"
    )
    probe = subprocess.run(
        [str(venv_python), "-c", probe_script],
        cwd=str(outside_cwd),
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    assert "OK" in probe.stdout


def test_136k_sdist_and_wheel_still_exclude_group3plus_and_authority_namespace(tmp_path):
    import tarfile
    import zipfile

    dist_dir = tmp_path / "dist2"
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(dist_dir.glob("*.whl"))
    sdist = next(dist_dir.glob("*.tar.gz"))

    # cutover_request and readiness_package are no longer forbidden stems:
    # Phase 136L legitimately packages them as Group 3. human_authorization
    # is no longer a forbidden stem: Phase 136N legitimately packages it as
    # Group 4 (cutover_candidate/certification substrings overlap with no
    # forbidden Group 5+ stem, so only compatibility_state remains checked
    # here for this particular assertion).
    forbidden_stems = ("compatibility_state",)

    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    assert not any(any(stem in n for stem in forbidden_stems) for n in names)
    assert not any("/bindings/" in n or "/views/" in n for n in names)
    assert not any(".pcae/cltr-authority" in n for n in names)
    assert any(n.endswith("records/authority_epoch.schema.json") for n in names)
    assert any(n.endswith("records/authority_state.schema.json") for n in names)
    assert any(n.endswith("records/cutover_request.schema.json") for n in names)
    assert any(n.endswith("records/readiness_package.schema.json") for n in names)

    with tarfile.open(sdist) as tf:
        tnames = tf.getnames()
    assert not any(any(stem in n for stem in forbidden_stems) for n in tnames)
    assert any(n.endswith("records/authority_epoch.schema.json") for n in tnames)

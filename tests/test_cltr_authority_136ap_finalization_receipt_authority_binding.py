"""Phase 136AP: Stage 3 Typed Authority Model Finalization Receipt Authority
Binding Implementation (Typed Model Implementation Group 9).

Focused tests for ``src/pcae/cltr/authority/bindings.py``: the
``FinalizationReceiptAuthorityBinding`` typed record model. Covers exact
field mapping, strict constructor behavior, family-restriction enforcement,
the ``receipt_state``/``publication_evidence_reference``/``marker_reference``
conditional, enum fidelity, schema conformance, no-later-group-model
inventory, no-receipt-management/no-lifecycle-finalization/no-authority-
activation semantics, no-side-effect, and runtime-isolation.

This module implements only Typed Model Implementation Group 9
(``FinalizationReceiptAuthorityBinding``). No other record-family model
(``CompatibilityState``, ``QuarantineRecord``) is implemented or exercised
here.

Independently fixtured: wire fixtures below are re-derived from the
authoritative schema (``records/receipt_authority_binding.schema.json``),
not copied from ``test_cltr_authority_136an_marker_authority_binding.py``'s
or ``test_cltr_authority_136ao_marker_authority_binding_independent.py``'s
own fixture helpers.
"""

from __future__ import annotations

import ast
import copy
import dataclasses
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from pcae.cltr import authority as auth
from pcae.cltr.authority import bindings
from pcae.schema_resources import cltr_cutover_root
from pcae.schema_runtime import OutcomeStatus, build_offline_registry, validate_record_shape

REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PACKAGE_DIR = REPO_ROOT / "src" / "pcae" / "cltr" / "authority"
BINDINGS_MODULE = AUTHORITY_PACKAGE_DIR / "bindings.py"

PRODUCTION_SCAN_ROOTS = (
    REPO_ROOT / "src" / "pcae" / "commands",
    REPO_ROOT / "src" / "pcae" / "core",
    REPO_ROOT / "src" / "pcae" / "cltr",
    REPO_ROOT / "src" / "pcae" / "runtime",
)

# Receipt boundary + lifecycle boundary + authority boundary no-go symbols,
# named as functions per the operator prompt's exhaustive receipt/lifecycle/
# authority forbidden-action list.
FORBIDDEN_SYMBOLS = (
    "create_receipt",
    "generate_receipt",
    "publish_receipt",
    "finalize_phase",
    "acknowledge_completion",
    "determine_successful_completion",
    "determine_failed_completion",
    "validate_receipt_authenticity",
    "validate_signatures",
    "verify_hashes",
    "compare_receipt_timestamps",
    "reconcile_receipt_history",
    "inspect_receipt_files",
    "discover_receipts",
    "enumerate_receipts",
    "locate_receipts",
    "archive_receipts",
    "promote_receipts",
    "retire_receipts",
    "finalize_lifecycle",
    "close_task",
    "promote_report",
    "update_metadata",
    "write_completion_marker",
    "write_project_status",
    "advance_lifecycle_state",
    "authorize_publication",
    "mutate_transition",
    "activate_authority",
    "resolve_authority",
    "determine_current_authority",
    "compare_authorities",
    "transfer_authority",
    "mutate_authority_pointer",
)

LATER_GROUP_MODEL_NAMES = (
    "CompatibilityState",
    "QuarantineRecord",
)

RECEIPT_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/receipt_authority_binding.schema.json"
)
MARKER_AUTHORITY_BINDING_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/marker_authority_binding.schema.json"
)
PUBLICATION_EVIDENCE_SCHEMA_ID = (
    "https://pcae.local/schemas/cltr_cutover/records/publication_evidence.schema.json"
)


def _sha256_hex(fill: str) -> str:
    assert len(fill) == 1
    return fill * 64


@pytest.fixture(scope="module")
def schema_registry():
    with cltr_cutover_root() as root:
        return build_offline_registry(root)


def _assert_schema_valid(record: dict, schema_id: str, registry) -> None:
    result = validate_record_shape(record, schema_id=schema_id, registry=registry)
    assert result.status is OutcomeStatus.VALID, result.issues


# ---------------------------------------------------------------------------
# Wire fixtures
# ---------------------------------------------------------------------------


def _disclosure(role: str = "derivative") -> dict:
    return {
        "authority_role": role,
        "is_authoritative": False,
        "disclosure_text": "Non-authoritative schema-validated companion record.",
    }


def _generation_ref(gen_id: str = "generatn-0000009", digest: str = "9") -> dict:
    return {"generation_id": gen_id, "generation_digest": _sha256_hex(digest)}


def _marker_ref(record_id: str = "markrbnd-0000001", digest: str = "b") -> dict:
    return {
        "record_id": record_id,
        "record_digest": _sha256_hex(digest),
        "record_family": "marker_authority_binding",
        "schema_id": MARKER_AUTHORITY_BINDING_SCHEMA_ID,
        "schema_version": "1.0",
    }


def _publication_evidence_ref(record_id: str = "pubevdnc-0000001", digest: str = "c") -> dict:
    return {
        "record_id": record_id,
        "record_digest": _sha256_hex(digest),
        "record_family": "publication_evidence",
        "schema_id": PUBLICATION_EVIDENCE_SCHEMA_ID,
        "schema_version": "1.0",
    }


def _valid_receipt_authority_binding_wire(**overrides) -> dict:
    record = {
        "schema_id": RECEIPT_AUTHORITY_BINDING_SCHEMA_ID,
        "schema_version": "1.0",
        "contract_version": "1.0",
        "record_type": "receipt_authority_binding",
        "record_id": "receiptb-0000001",
        "record_digest": _sha256_hex("0"),
        "created_at": "2026-07-18T12:00:00Z",
        "migration_epoch": "epoch-001",
        "generation_reference": _generation_ref(),
        "receipt_state": "absent",
        "limitations": [],
        "authority_disclosure": _disclosure(),
    }
    record.update(overrides)
    return record


def _finalized_wire(**overrides) -> dict:
    base = _valid_receipt_authority_binding_wire(
        receipt_state="finalized",
        publication_evidence_reference=_publication_evidence_ref(),
        marker_reference=_marker_ref(),
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Inventory
# ---------------------------------------------------------------------------


def test_136ap_exactly_fourteen_record_family_models_exist_in_package():
    class_names: set[str] = set()
    for path in AUTHORITY_PACKAGE_DIR.glob("*.py"):
        tree = ast.parse(path.read_text())
        class_names |= {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    for expected in (
        "AuthorityEpoch",
        "AuthorityState",
        "CutoverRequest",
        "ReadinessPackage",
        "HumanAuthorization",
        "CutoverCandidate",
        "Certification",
        "PublicationAttempt",
        "PublicationEvidence",
        "ConcurrencyConflict",
        "RecoveryJournalEntry",
        "NotificationAuthorityBinding",
        "MarkerAuthorityBinding",
        "FinalizationReceiptAuthorityBinding",
    ):
        assert expected in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136ap_no_later_group_model_class_exists_in_bindings_module():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    assert "NotificationAuthorityBinding" in class_names
    assert "MarkerAuthorityBinding" in class_names
    assert "FinalizationReceiptAuthorityBinding" in class_names
    for later_name in LATER_GROUP_MODEL_NAMES:
        assert later_name not in class_names


def test_136ap_expected_public_exports_present():
    for name in ("FinalizationReceiptAuthorityBinding", "ReceiptState"):
        assert hasattr(auth, name)
        assert name in auth.__all__


def test_136ap_public_exports_exact():
    assert set(bindings.__all__) == {
        "DeliveryState",
        "NotificationAuthorityBindingUncertainty",
        "NotificationAuthorityBinding",
        "MarkerState",
        "MarkerAuthorityBinding",
        "ReceiptState",
        "FinalizationReceiptAuthorityBinding",
    }


def test_136ap_wildcard_import_matches_all():
    namespace: dict = {}
    exec("from pcae.cltr.authority.bindings import *", namespace)
    exported = {k for k in namespace if not k.startswith("_")}
    assert exported == set(bindings.__all__)


def test_136ap_model_is_frozen_dataclass():
    assert dataclasses.is_dataclass(auth.FinalizationReceiptAuthorityBinding)
    assert auth.FinalizationReceiptAuthorityBinding.__dataclass_params__.frozen


# ---------------------------------------------------------------------------
# 2. FinalizationReceiptAuthorityBinding: construction / round trip
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", ["absent", "stale", "conflict"])
def test_136ap_minimal_valid_construction_non_finalized_states(schema_registry, state):
    wire = _valid_receipt_authority_binding_wire(receipt_state=state)
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.publication_evidence_reference is auth.ABSENT
    assert model.marker_reference is auth.ABSENT
    assert model.to_dict() == wire


def test_136ap_finalized_state_with_both_references(schema_registry):
    wire = _finalized_wire()
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.publication_evidence_reference.record_id.value == "pubevdnc-0000001"
    assert model.marker_reference.record_id.value == "markrbnd-0000001"
    assert model.to_dict() == wire


def test_136ap_maximal_valid_construction_with_extensions_and_staleness_check(schema_registry):
    wire = _finalized_wire(_extensions={"note": "annotation"}, staleness_check={})
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model._extensions["note"] == "annotation"
    assert model.staleness_check.to_json() == {}
    assert model.to_dict() == wire


def test_136ap_finalized_without_publication_evidence_reference_rejected():
    wire = _valid_receipt_authority_binding_wire(
        receipt_state="finalized", marker_reference=_marker_ref()
    )
    with pytest.raises(Exception):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_finalized_without_marker_reference_rejected():
    wire = _valid_receipt_authority_binding_wire(
        receipt_state="finalized", publication_evidence_reference=_publication_evidence_ref()
    )
    with pytest.raises(Exception):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_finalized_without_either_reference_rejected():
    wire = _valid_receipt_authority_binding_wire(receipt_state="finalized")
    with pytest.raises(Exception):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("state", ["absent", "stale", "conflict"])
def test_136ap_non_finalized_with_publication_evidence_reference_rejected(state):
    wire = _valid_receipt_authority_binding_wire(
        receipt_state=state, publication_evidence_reference=_publication_evidence_ref()
    )
    with pytest.raises(Exception):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


@pytest.mark.parametrize("state", ["absent", "stale", "conflict"])
def test_136ap_non_finalized_with_marker_reference_rejected(state):
    wire = _valid_receipt_authority_binding_wire(
        receipt_state=state, marker_reference=_marker_ref()
    )
    with pytest.raises(Exception):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_unknown_field_rejected():
    wire = _valid_receipt_authority_binding_wire(scope="global")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_unsupported_schema_version_rejected():
    wire = _valid_receipt_authority_binding_wire()
    with pytest.raises(auth.UnsupportedSchemaVersionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="2.0")


def test_136ap_wrong_schema_id_rejected():
    wire = _valid_receipt_authority_binding_wire(schema_id="https://pcae.local/wrong.json")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_wrong_record_type_rejected():
    wire = _valid_receipt_authority_binding_wire(record_type="marker_authority_binding")
    with pytest.raises(auth.TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_missing_required_field_rejected():
    wire = _valid_receipt_authority_binding_wire()
    del wire["generation_reference"]
    with pytest.raises(auth.TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_forbids_authoritative_role():
    wire = _valid_receipt_authority_binding_wire(
        authority_disclosure={
            "authority_role": "authoritative",
            "is_authoritative": False,
            "disclosure_text": "x",
        }
    )
    with pytest.raises(Exception):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_marker_reference_wrong_family_rejected():
    wire = _finalized_wire(
        marker_reference={
            "record_id": "notifbnd-0000001",
            "record_digest": _sha256_hex("c"),
            "record_family": "notification_authority_binding",
            "schema_id": (
                "https://pcae.local/schemas/cltr_cutover/records/"
                "notification_authority_binding.schema.json"
            ),
            "schema_version": "1.0",
        }
    )
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_publication_evidence_reference_wrong_family_rejected():
    wire = _finalized_wire(publication_evidence_reference=_marker_ref())
    with pytest.raises(auth.WrongFamilyReferenceError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_marker_reference_requires_schema_id_and_version():
    ref = _marker_ref()
    del ref["schema_id"]
    wire = _finalized_wire(marker_reference=ref)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_publication_evidence_reference_requires_schema_id_and_version():
    ref = _publication_evidence_ref()
    del ref["schema_version"]
    wire = _finalized_wire(publication_evidence_reference=ref)
    with pytest.raises(auth.TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_receipt_state_enum_members_match_schema():
    assert {m.value for m in bindings.ReceiptState} == {"absent", "finalized", "stale", "conflict"}


def test_136ap_receipt_state_enum_strictness():
    wire = _valid_receipt_authority_binding_wire(receipt_state="ABSENT")
    with pytest.raises(ValueError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_top_level_assignment_raises():
    wire = _valid_receipt_authority_binding_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.receipt_state = bindings.ReceiptState.STALE


def test_136ap_no_extensions_escape_hatch_is_tier_2_permitted(schema_registry):
    wire = _valid_receipt_authority_binding_wire(_extensions={})
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model._extensions.to_dict() == {}


def test_136ap_extensions_reject_reserved_key_collision():
    wire = _valid_receipt_authority_binding_wire(_extensions={"receipt_state": "x"})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_extensions_reject_non_string_value():
    wire = _valid_receipt_authority_binding_wire(_extensions={"note": 5})
    with pytest.raises(auth.TypedModelConstructionError):
        auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")


def test_136ap_staleness_check_absent_by_default():
    wire = _valid_receipt_authority_binding_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert model.staleness_check is auth.ABSENT
    assert "staleness_check" not in model.to_dict()


def test_136ap_staleness_check_round_trips_as_opaque_value(schema_registry):
    wire = _valid_receipt_authority_binding_wire(staleness_check={})
    _assert_schema_valid(wire, RECEIPT_AUTHORITY_BINDING_SCHEMA_ID, schema_registry)
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    assert isinstance(model.staleness_check, auth.OpaqueJsonValue)
    auth.verify_round_trip({}, model.staleness_check)
    assert model.to_dict() == wire


# ---------------------------------------------------------------------------
# 3. Schema field-set parity
# ---------------------------------------------------------------------------


def test_136ap_schema_field_set_matches_model_known_keys():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "receipt_authority_binding.schema.json").read_text())
    assert set(schema["properties"].keys()) == bindings._RECEIPT_AUTHORITY_BINDING_KNOWN_KEYS


def test_136ap_required_set_matches_schema():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "receipt_authority_binding.schema.json").read_text())
    wire = _valid_receipt_authority_binding_wire()
    assert set(schema["required"]) <= set(wire.keys())


def test_136ap_receipt_state_enum_matches_schema_defs():
    with cltr_cutover_root() as root:
        import json

        schema = json.loads((root / "records" / "receipt_authority_binding.schema.json").read_text())
    assert set(schema["$defs"]["receipt_state"]["enum"]) == {
        m.value for m in bindings.ReceiptState
    }


# ---------------------------------------------------------------------------
# 4. Equality / immutability
# ---------------------------------------------------------------------------


def test_136ap_structural_equality():
    wire = _valid_receipt_authority_binding_wire()
    a = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    b = auth.FinalizationReceiptAuthorityBinding.from_dict(copy.deepcopy(wire), schema_version="1.0")
    assert a == b


def test_136ap_field_difference_breaks_equality():
    a = auth.FinalizationReceiptAuthorityBinding.from_dict(
        _valid_receipt_authority_binding_wire(), schema_version="1.0"
    )
    b = auth.FinalizationReceiptAuthorityBinding.from_dict(
        _valid_receipt_authority_binding_wire(receipt_state="stale"), schema_version="1.0"
    )
    assert a != b


def test_136ap_construction_input_mutation_does_not_mutate_model():
    wire = _valid_receipt_authority_binding_wire(limitations=["a limitation"])
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    wire["limitations"].append("mutated after construction")
    assert list(model.limitations) == ["a limitation"]


# ---------------------------------------------------------------------------
# 5. No-receipt-management / no-lifecycle-finalization / no-authority-
#    activation / no-later-model
# ---------------------------------------------------------------------------


def test_136ap_no_forbidden_symbols_defined_in_source():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    defined_names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defined_names.add(node.name)
    for forbidden in FORBIDDEN_SYMBOLS:
        assert forbidden not in defined_names


def test_136ap_no_repository_or_persistence_symbols_in_source():
    source = BINDINGS_MODULE.read_text()
    for forbidden in ("Repository", "save(", "persist(", "def load(", "requests.", "urllib", "socket."):
        assert forbidden not in source


def test_136ap_no_production_module_imports_authority_package():
    for root_dir in PRODUCTION_SCAN_ROOTS:
        if not root_dir.exists():
            continue
        for path in root_dir.rglob("*.py"):
            if AUTHORITY_PACKAGE_DIR in path.parents or path.parent == AUTHORITY_PACKAGE_DIR:
                continue
            source = path.read_text()
            assert "from pcae.cltr.authority" not in source, path
            assert "import pcae.cltr.authority" not in source, path


def test_136ap_bindings_module_imports_no_production_lifecycle_module():
    source = BINDINGS_MODULE.read_text()
    for forbidden_import in (
        "pcae.core.finalization",
        "pcae.core.notification",
        "pcae.commands",
        "pcae.runtime",
    ):
        assert forbidden_import not in source


def test_136ap_bindings_module_does_not_import_production_lifecycle_modules_ast():
    forbidden_modules = (
        "pcae.cltr.lifecycle",
        "pcae.cltr.finalization",
        "pcae.cltr.notification",
        "pcae.cltr.marker",
        "pcae.cltr.receipt",
        "pcae.commands",
        "pcae.core",
        "pcae.runtime",
    )
    tree = ast.parse(BINDINGS_MODULE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forbidden in forbidden_modules:
                    assert not alias.name.startswith(forbidden), (BINDINGS_MODULE, alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for forbidden in forbidden_modules:
                assert not node.module.startswith(forbidden), (BINDINGS_MODULE, node.module)


def test_136ap_no_network_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket.socket, "connect", _raise)
    wire = _valid_receipt_authority_binding_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136ap_no_subprocess_during_construction_or_serialization(monkeypatch):
    def _raise(*args, **kwargs):
        raise AssertionError("subprocess spawn attempted")

    monkeypatch.setattr(subprocess, "run", _raise)
    monkeypatch.setattr(subprocess, "Popen", _raise)
    wire = _finalized_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    model.to_dict()


def test_136ap_no_filesystem_write_during_construction_or_serialization(monkeypatch, tmp_path):
    real_open = open

    def _guarded_open(file, mode="r", *args, **kwargs):
        if isinstance(mode, str) and any(flag in mode for flag in ("w", "a", "x", "+")):
            raise AssertionError(f"unexpected filesystem write attempted: {file!r} mode={mode!r}")
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", _guarded_open)
    wire = _valid_receipt_authority_binding_wire()
    model = auth.FinalizationReceiptAuthorityBinding.from_dict(wire, schema_version="1.0")
    model.to_dict()
    repr(model)
    _ = model == model


def test_136ap_package_import_is_side_effect_free(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("unexpected socket use during import")

    monkeypatch.setattr(socket, "socket", _boom)
    import importlib

    importlib.reload(bindings)


# ---------------------------------------------------------------------------
# 6. Scope-guard verification (narrowed by 136AP; must still forbid the
#    remaining two later record families and permit only this group's one
#    new family).
# ---------------------------------------------------------------------------


SCOPE_GUARDED_TEST_FILES = (
    REPO_ROOT / "tests" / "test_cltr_authority_136z_shared_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136aa_shared_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ab_authority_core.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ac_authority_core_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ad_request_readiness.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ae_request_readiness_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136af_authorization_candidate.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ag_authorization_candidate_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ah_publication.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ai_publication_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136aj_recovery_concurrency.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ak_recovery_concurrency_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136al_notification_authority_binding.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136am_notification_authority_binding_independent.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136an_marker_authority_binding.py",
    REPO_ROOT / "tests" / "test_cltr_authority_136ao_marker_authority_binding_independent.py",
)


def test_136ap_adjacent_scope_guard_test_files_still_forbid_remaining_later_models():
    still_forbidden_after_136ap = (
        "CompatibilityState",
        "QuarantineRecord",
    )
    for path in SCOPE_GUARDED_TEST_FILES:
        if not path.exists():
            continue
        text = path.read_text()
        if (
            "LATER_MODEL_CLASS_NAMES" not in text
            and "LATER_GROUP_MODEL_NAMES" not in text
            and "_LATER_GROUP_MODEL_NAMES" not in text
            and "FOUR_MUST_NOT_EXIST_RECORD_FAMILIES" not in text
            and "FIVE_MUST_NOT_EXIST_RECORD_FAMILIES" not in text
            and "THREE_MUST_NOT_EXIST_RECORD_FAMILIES" not in text
        ):
            continue
        for later in still_forbidden_after_136ap:
            assert later in text, f"{path} no longer names {later} as forbidden"


def test_136ap_own_module_scope_guard_matches_exactly_the_new_family_trio():
    tree = ast.parse(BINDINGS_MODULE.read_text())
    class_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    record_family_models = class_names & {
        "NotificationAuthorityBinding", "MarkerAuthorityBinding",
        "FinalizationReceiptAuthorityBinding", *LATER_GROUP_MODEL_NAMES,
        "AuthorityEpoch", "AuthorityState", "CutoverRequest", "ReadinessPackage",
        "HumanAuthorization", "CutoverCandidate", "Certification",
        "PublicationAttempt", "PublicationEvidence",
        "ConcurrencyConflict", "RecoveryJournalEntry",
    }
    assert record_family_models == {
        "NotificationAuthorityBinding", "MarkerAuthorityBinding", "FinalizationReceiptAuthorityBinding",
    }


# ---------------------------------------------------------------------------
# 7. Packaging verification
# ---------------------------------------------------------------------------


@pytest.mark.slow
def test_136ap_wheel_contains_bindings_module_no_later_family(tmp_path: Path):
    import subprocess as _subprocess

    dist_dir = tmp_path / "dist"
    _subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    wheels = list(dist_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    import zipfile

    with zipfile.ZipFile(wheels[0]) as archive:
        names = archive.namelist()

    assert "pcae/cltr/authority/bindings.py" in names
    for forbidden in ("compatibility_quarantine",):
        assert f"pcae/cltr/authority/{forbidden}.py" not in names


@pytest.mark.slow
def test_136ap_sdist_includes_bindings_module(tmp_path: Path):
    import subprocess as _subprocess

    dist_dir = tmp_path / "dist"
    _subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(dist_dir), str(REPO_ROOT)],
        check=True, capture_output=True, text=True,
    )
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(sdists) == 1, f"expected exactly one sdist, found {sdists}"

    import tarfile

    with tarfile.open(sdists[0]) as archive:
        names = archive.getnames()

    assert any(name.endswith("pcae/cltr/authority/bindings.py") for name in names)

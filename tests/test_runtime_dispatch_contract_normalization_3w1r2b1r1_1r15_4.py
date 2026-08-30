"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 — Runtime-Dispatch Contract
Normalization Implementation.

RE-DERIVE, DO NOT TRUST. Every assertion is derived from the normalized
contract text (RDGO-001 v3.1, PBRD-001 v2.1, HPAC-001 v2.1, RIASC-001 v3.0
errata, RE No-Go Registry schema 1.1) and current production source — not
from the `.1R.15.4` report or its helper names.

Coverage:
 * §28  contract-traceability — the normalized wording matches the verified
        architecture (V-2/V-3/V-4/V-13-3-1/V-13-3-2/V-13-5-1/V-15-1);
 * §29  durable HPAC-AUTHORITY-CONSUMPTION/2.1 schema — version, closed
        field set, malformed/missing/extra, digest integrity, /2.0 read
        tolerance + Gate-10 ineligibility;
 * §30  N-15-3-2 production authority-generation resolver completeness;
 * §31  durable write / restart / read-back / reconstruction;
 * §32  post-consumption drift — the durable record is inert history;
 * §33  the durable snapshot is data, not a bearer token;
 * §34  Gate9Result forward semantics unchanged.

The positive Gate-9 consumption path is production-unreachable; every
positive assertion runs through the same clearly-labelled test-only
provenance substitution + tmp_path store the `.1R.14` integration suite
uses. No real authority is manufactured.
"""

from __future__ import annotations

import copy
import inspect
import json
import pickle
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_gate9 as g9
from pcae.core import runtime_invocation_authority_consumption as ric

from test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14 import (  # noqa: E501
    NOW,
    REPO_ROOT,
    _count_consumption_json,
    _run,
    chain,  # noqa: F401  (pytest fixture re-export)
)

CONTRACTS = REPO_ROOT / "docs" / "contracts"
RDGO = (CONTRACTS / "RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md").read_text()
PBRD = (CONTRACTS / "PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md").read_text()
HPAC = (CONTRACTS / "HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md").read_text()
RIASC = (CONTRACTS / "RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md").read_text()
RIHAC = (CONTRACTS / "RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md").read_text()
RENOGO = (REPO_ROOT / "docs" / "RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md").read_text()

_GEN_SNAPSHOT_SCHEMA = "HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0"
_CONSUMPTION_2_1 = "HPAC-AUTHORITY-CONSUMPTION/2.1"
_CONSUMPTION_2_0 = "HPAC-AUTHORITY-CONSUMPTION/2.0"


def _flat(s: str) -> str:
    return " ".join(s.split())


# ═══════════════════════════════════════════════════════════════════════
# §5, §40  Version adjudication
# ═══════════════════════════════════════════════════════════════════════
def test_contract_headers_are_the_normalized_minor_versions():
    assert RDGO.startswith("# RDGO-001 v3.1")
    assert PBRD.startswith("# PBRD-001 v2.1")
    assert HPAC.startswith("# HPAC-001 v2.1")
    assert RIASC.startswith("# RIASC-001 v3.0")  # errata only, no bump
    assert "**Schema version**: 1.1" in RENOGO


def test_both_major_candidate_calls_are_adjudicated_minor():
    assert "**v3.1 is a MINOR clarification**" in _flat(RDGO)
    assert "**v2.1 is a MINOR clarification**" in _flat(PBRD)
    # RDGO explicitly disclaims the reorder/merge/first-effect-move MAJORs
    assert "does not reorder a gate" in _flat(RDGO)
    assert 'This is not a "closed shape" MAJOR.' in PBRD


# ═══════════════════════════════════════════════════════════════════════
# §6, §7  V-2 / V-3 — sequence-3 creation ownership
# ═══════════════════════════════════════════════════════════════════════
def test_v2_rdgo_says_verifier_creates_seq3_at_gate3_and_gate5_reconfirms():
    f = _flat(RDGO)
    assert "HPAC-REQ-054 step 10 (`bind_gate5_canonical`) creates HPAC lifecycle sequence 3" in f
    assert "at gate 3 (approval creation) time" in f
    assert "Gate 5 does **not** create this event" in RDGO
    assert "gate 5 freshly **re-confirms**" in RDGO
    # §6 aligned
    assert "re-confirms (read-only) the current HPAC lifecycle sequence 3" in RDGO
    # the stale "Gate 5, not gate 3, creates ... over the completed approval digest" is gone
    assert "Gate 5, not gate 3, creates the final `PROOF_VERIFIED_AND_BOUND`" not in RDGO


def test_v3_seq3_binds_subject_digest_not_record_digest():
    assert "binds the `HPAC-APPROVAL-SUBJECT/2.0` subject digest fixed at gate 3, **not**" in RDGO
    assert "the completed RIASC-001 v3.0 approval `record_digest`" in RDGO
    # RIASC errata cross-reference
    assert "Errata note (Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 — V-3" in RIASC
    assert "are **distinct commitments** and are not\ninterchangeable" in RIASC
    assert "HPAC lifecycle sequence 3 does **not** bind\n`record_digest`" in RIASC
    # HPAC-REQ-097 cross-reference note
    assert "Cross-reference (RDGO-001 v3.1 §4 — V-2)" in HPAC


# ═══════════════════════════════════════════════════════════════════════
# §8  V-4 — human_authority_binding representation equivalence
# ═══════════════════════════════════════════════════════════════════════
def test_v4_pbrd_representation_equivalence_clause():
    assert "### 4a. `human_authority_binding` representation equivalence (v2.1 — V-4)" in PBRD
    body = _flat(PBRD[PBRD.index("### 4a."):PBRD.index("## 4a. Attempt/idempotency")]).replace("> ", "")
    assert "3-tuple `(approval_id, approval_record_digest, validation_evidence_digest)`" in body
    for logical in ("approval_id", "approval_record_digest", "validation_evidence_digest"):
        assert logical in body
    assert "Two authority contexts that differ in any logical field MUST NOT collapse" in body
    assert "The logical seven-field security meaning is NOT weakened" in body
    # the 7 logical fields are retained in fact 14
    fact14 = PBRD[PBRD.index("| 14 | `human_authority_binding`"):PBRD.index("`lifecycle_context` and")]
    for f in ("approval_id", "approval_digest", "authority_projection_id",
              "authority_projection_digest", "authority_contract_version",
              "proof_validation_digest", "request_binding_digest"):
        assert f in fact14


# ═══════════════════════════════════════════════════════════════════════
# §9  V-13-3-1 — Gate 6 owns PB policy; Gate 7/9 do not re-run it
# ═══════════════════════════════════════════════════════════════════════
def test_v13_3_1_rdgo_gate6_owns_pb_policy():
    g7 = _flat(RDGO[RDGO.index("## 8. Gate 7"):RDGO.index("## 9. Gate 8")])
    assert "PB policy evaluation is owned exclusively by gate 6" in g7
    assert "Neither gate 7 nor gate 9 re-runs PB policy" in g7
    assert "resolved by **re-entering gate 6**" in g7
    assert "advisory reason only" in g7
    # phase-doc erratum
    doc = (REPO_ROOT / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_13_2_GATE_7_RUNTIME_ENFORCEMENT_COORDINATOR_INTEGRATION_IMPLEMENTATION.md").read_text()
    assert "Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (V-13-3-1)" in doc
    assert "**overstates**" in doc


# ═══════════════════════════════════════════════════════════════════════
# §10  V-13-3-2 — RE No-Go Registry schema 1.1 classification
# ═══════════════════════════════════════════════════════════════════════
def test_v13_3_2_re_registry_schema_1_1_classification():
    assert "**Schema version**: 1.1" in RENOGO
    assert "Enforcement class (1.1)" in RENOGO
    # per-decision subset
    for pid in ("RE-NOGO-001", "RE-NOGO-008", "RE-NOGO-010", "RE-NOGO-011"):
        row = [ln for ln in RENOGO.splitlines() if ln.startswith(f"| {pid} ")][0]
        assert "per-decision" in row
    for eid in ("RE-NOGO-009", "RE-NOGO-013", "RE-NOGO-015", "RE-NOGO-016", "RE-NOGO-017"):
        row = [ln for ln in RENOGO.splitlines() if ln.startswith(f"| {eid} ")][0]
        assert "environmental-readiness" in row
    for aid in ("RE-NOGO-012", "RE-NOGO-014"):
        row = [ln for ln in RENOGO.splitlines() if ln.startswith(f"| {aid} ")][0]
        assert "advisory" in row
    assert "projects\nonly the **per-decision** subset" in RENOGO
    assert "Gate-7 progression depends on the authoritative Gate-7\ndecision" in RENOGO
    assert 'the sole source *for the\nper-decision projection*' in RENOGO


# ═══════════════════════════════════════════════════════════════════════
# §11  V-13-5-1 — three-layer Gate-8 containment model
# ═══════════════════════════════════════════════════════════════════════
def test_v13_5_1_rdgo_three_layer_containment_model():
    g8 = RDGO[RDGO.index("## 9. Gate 8"):RDGO.index("## 10. Gate 9")]
    assert "Three-layer containment model (v3.1 normalization — V-13-5-1)" in g8
    assert "(a) *direct validation*" in g8
    assert "(b) *canonical commitment*" in g8
    assert "(c) *gate-9 recomputation*" in g8
    assert "there\nis therefore no separate caller-supplied cwd / environment / transport\n\"reference\" to diff against" in g8
    # .1R.13.1 erratum strikes the transport row, rewords cwd/env
    doc = (REPO_ROOT / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_13_1_GATE_7_RUNTIME_ENFORCEMENT_AND_GATE_8_SHELL_GATE_CONSUMPTION_INTEGRATION_PLANNING.md").read_text()
    assert "gate8_transport_drift`:\n>   **STRUCK.**" in doc
    assert "reworded." in doc


# ═══════════════════════════════════════════════════════════════════════
# §12, §13  V-15-1 — create-only linearization + zero-I/O token re-check
# ═══════════════════════════════════════════════════════════════════════
def test_v15_1_rdgo_normalized_linearization_model():
    g9s = RDGO[RDGO.index("## 10. Gate 9"):RDGO.index("## 11. Gate 10")]
    assert "Gate-9 linearization semantics (v3.1 normalization — V-15-1)" in g9s
    assert "**is** the linearization point and the single\ntransaction mechanism; there is no second global lock" in g9s
    assert "monotonic authority-generation snapshot `S1`" in g9s
    assert "re-reads it as `S2` with **zero intervening effectful I/O**" in g9s
    assert "any `S2 != S1`" in g9s
    assert "residual instruction-level\nmicro-window" in g9s
    # `.1R.9` §13.5 self-contradiction erratum
    doc9 = (REPO_ROOT / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_9_GATE_5_GATE_9_PRODUCTION_AUTHORITY_COORDINATOR_INTEGRATION_PLANNING.md").read_text()
    assert "Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (V-15-1\n> normalization)" in doc9
    assert "**internally contradicted**" in doc9
    assert "there is **no** held lock" in doc9
    # `.1R.13.1` §16.2 invariant-4 erratum
    doc131 = (REPO_ROOT / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_13_1_GATE_7_RUNTIME_ENFORCEMENT_AND_GATE_8_SHELL_GATE_CONSUMPTION_INTEGRATION_PLANNING.md").read_text()
    assert "Erratum — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 (V-15-1)" in doc131
    assert "there is\n   > **no held lock**" in doc131


def test_hpac_req_099_matches_the_repaired_code():
    assert "HPAC-REQ-099." in HPAC
    r99 = HPAC[HPAC.index("- **HPAC-REQ-099."):HPAC.index("- **HPAC-REQ-100.")]
    assert "captures the HPAC-REQ-098a authority-generation\n  snapshot `S1` and re-reads it as `S2` with **zero intervening effectful\n  I/O**" in r99
    assert "The per-`proof_id` create-only atomic primitive (HPAC-REQ-100) **is** the\n  serialization boundary and the sole transaction mechanism" in r99
    # the code's coordinator + HPAC-REQ-099 agree: battery -> S1 -> build -> S2 -> create
    coord = inspect.getsource(g9.run_gate9_atomic_authority_consumption)
    assert coord.index("# 14a. V-15-1 repair — capture the authority-generation snapshot S1") \
        < coord.index("# 15a. V-15-1 repair — re-read the authority-generation snapshot S2") \
        < coord.index("consumption_store.create(proof_id, consumption_record)")


# ═══════════════════════════════════════════════════════════════════════
# §14, §16, §22  Gate-10 forward read-back prerequisite (semantics only)
# ═══════════════════════════════════════════════════════════════════════
def test_gate10_forward_readback_prerequisite_is_stated_not_designed():
    g10 = _flat(RDGO[RDGO.index("## 11. Gate 10"):RDGO.index("## 12. Gate 11")])
    assert "`is_gate9_result(x) == True` is **insufficient**" in g10
    assert '`x.status == "consumed"`' in g10
    assert "`authority_generation_binding` present and valid" in g10
    assert "re-derivation of the current authority-generation vector and comparison against the durable `authority_generation_binding` snapshot" in g10
    assert "The durable authority-generation snapshot is data, not a bearer token" in g10
    # no gate-10 module invented
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()
    assert "DispatchReceipt" not in (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate9.py").read_text()


# ═══════════════════════════════════════════════════════════════════════
# §29  Durable HPAC-AUTHORITY-CONSUMPTION/2.1 schema
# ═══════════════════════════════════════════════════════════════════════
_AGB_KEYS = {
    "snapshot_schema_version", "principal_generation", "credential_generation",
    "approval_generation", "lifecycle_generation", "consumption_generation",
}


def _valid_agb(**over):
    b = {
        "snapshot_schema_version": _GEN_SNAPSHOT_SCHEMA,
        "principal_generation": "p" * 64,
        "credential_generation": "c" * 64,
        "approval_generation": "a" * 64,
        "lifecycle_generation": "l" * 64,
        "consumption_generation": "absent",
    }
    b.update(over)
    return b


def _record(**over):
    kw = dict(
        request_identity={"invocation_id": "inv-1", "attempt_id": "att-1", "idempotency_key": "idem-1"},
        repository_task_binding={
            "repository_identity": "repo-1", "head_commit": "a" * 40, "task_id": "t-1",
            "task_contract_digest": "b" * 64, "phase_id": "p-1", "session_id": None,
        },
        target_binding={
            "runtime_target_id": "rt-1", "adapter_id": "ad-1", "descriptor_version": "v1",
            "descriptor_digest": "c" * 64, "target_config_digest": "d" * 64,
            "executable_identity_digest": "e" * 64,
        },
        prompt_binding={"prompt_hash": "f" * 64, "prompt_hash_profile": "pcae.prompt-semantic.v1"},
        authority_binding={
            "approval_id": "ria-" + "1" * 32, "approval_digest": "g" * 64,
            "authority_projection_id": "proj-1", "authority_projection_digest": "h" * 64,
            "authority_contract_version": "RIHAC-001/2.0", "proof_id": "hap-" + "1" * 32,
            "proof_digest": "i" * 64, "proof_validation_digest": "j" * 64,
            "registry_state_digest": "k" * 64, "approval_subject_digest": "l" * 64,
            "trusted_presentation_ref": {"presentation_id": "hpe-" + "1" * 32, "presentation_digest": "m" * 64},
            "challenge_digest": "n" * 64,
        },
        authority_generation_binding=_valid_agb(),
        pb_binding={
            "request_digest": "o" * 64, "decision_digest": "p" * 64, "decision": "ALLOW",
            "policy_version": "v1", "causing_policy_ids": [], "matched_no_go_ids": [],
        },
        runtime_enforcement_binding={
            "decision_id": "d-1", "decision_digest": "q" * 64, "verdict": "ALLOW",
            "expires_at": "2026-08-28T00:10:00Z", "evaluated_input_digest": "r" * 64,
        },
        dispatch_binding={
            "containment_evidence_ref": {"digest": "s" * 64, "live_preflight_digest": "t" * 64},
            "state": "dispatch_attempted", "consumed_at": "2026-08-28T00:00:00Z",
        },
    )
    kw.update(over)
    return ric.new_inert_consumption_record(**kw)


def test_current_schema_version_is_2_1_and_snapshot_schema_is_1_0():
    assert ric.CONSUMPTION_SCHEMA_VERSION == _CONSUMPTION_2_1
    assert ric.CONSUMPTION_SCHEMA_VERSION_LEGACY_2_0 == _CONSUMPTION_2_0
    assert ric.AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION == _GEN_SNAPSHOT_SCHEMA


def test_record_has_nine_binding_objects_and_the_agb_closed_field_set():
    rec = _record()
    doc = rec.to_document(include_digest=True)
    assert doc["consumption_schema_version"] == _CONSUMPTION_2_1
    assert set(doc) == {
        "consumption_schema_version", "record_digest", "request_identity",
        "repository_task_binding", "target_binding", "prompt_binding",
        "authority_binding", "authority_generation_binding", "pb_binding",
        "runtime_enforcement_binding", "dispatch_binding",
    }
    assert set(rec.authority_generation_binding) == _AGB_KEYS
    # authority_binding is still the closed 12-field set (unchanged by v2.1)
    assert len(rec.authority_binding) == 12


def test_missing_agb_is_rejected_at_construction():
    # None -> not a dict -> HPACMalformedError
    with pytest.raises(ric.HPACMalformedError):
        _record(authority_generation_binding=None)
    # omitted entirely -> TypeError (required keyword)
    kw = dict(
        request_identity={}, repository_task_binding={}, target_binding={},
        prompt_binding={}, authority_binding={}, pb_binding={},
        runtime_enforcement_binding={}, dispatch_binding={},
    )
    with pytest.raises(TypeError):
        ric.new_inert_consumption_record(**kw)


@pytest.mark.parametrize("bad", [
    {"snapshot_schema_version": "HPAC-AUTHORITY-GENERATION-SNAPSHOT/9.9"},
    {"principal_generation": ""},
    {"credential_generation": "  x  "},
    {"approval_generation": "z" * 300},
    {"lifecycle_generation": 123},
])
def test_malformed_agb_values_are_rejected(bad):
    with pytest.raises(ric.HPACMalformedError):
        _record(authority_generation_binding=_valid_agb(**bad))


def test_extra_or_missing_agb_field_is_rejected():
    with pytest.raises(ric.HPACMalformedError):
        _record(authority_generation_binding={**_valid_agb(), "extra": "x"})
    short = _valid_agb()
    del short["lifecycle_generation"]
    with pytest.raises(ric.HPACMalformedError):
        _record(authority_generation_binding=short)


def test_record_digest_covers_the_agb(tmp_path):
    store = ric.RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    a = _record()
    b = _record(authority_generation_binding=_valid_agb(principal_generation="X" * 64))
    assert a.record_digest != b.record_digest
    store.create("hap-" + "1" * 32, a)
    back = store.resolve("hap-" + "1" * 32)
    assert back is not None and back.authority_generation_binding == a.authority_generation_binding


# ═══════════════════════════════════════════════════════════════════════
# §18  /2.0 backward compatibility
# ═══════════════════════════════════════════════════════════════════════
def test_legacy_2_0_record_is_readable_but_gate10_ineligible(tmp_path):
    proof_id = "hap-" + "2" * 32
    rec = _record()
    doc = rec.to_document(include_digest=False)
    doc.pop("authority_generation_binding")
    doc["consumption_schema_version"] = _CONSUMPTION_2_0
    body_wo_digest = doc
    doc = dict(doc)
    doc["record_digest"] = ric.canonical_digest(body_wo_digest)
    path = tmp_path / "proofs" / "v2" / proof_id / "consumption.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")))
    store = ric.RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    back = store.resolve(proof_id)
    assert back is not None
    assert back.consumption_schema_version == _CONSUMPTION_2_0
    assert back.authority_generation_binding is None  # -> gate-10-ineligible


def test_unknown_schema_version_is_durability_uncertain(tmp_path):
    proof_id = "hap-" + "3" * 32
    doc = _record().to_document(include_digest=False)
    doc["consumption_schema_version"] = "HPAC-AUTHORITY-CONSUMPTION/9.0"
    doc = dict(doc)
    doc["record_digest"] = ric.canonical_digest({k: v for k, v in doc.items()})
    path = tmp_path / "proofs" / "v2" / proof_id / "consumption.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(doc, sort_keys=True, separators=(",", ":")))
    store = ric.RuntimeInvocationAuthorityConsumptionStore(tmp_path)
    with pytest.raises(ric.RuntimeInvocationAuthorityConsumptionDurabilityUncertainError):
        store.resolve(proof_id)


# ═══════════════════════════════════════════════════════════════════════
# §30  N-15-3-2 — production authority-generation resolver completeness
# ═══════════════════════════════════════════════════════════════════════
class _FakeApproval:
    def __init__(self, approval_id, record_digest):
        self.approval_id = approval_id
        self.record_digest = record_digest


class _FakeApprovalStore:
    def __init__(self, approval):
        self._approval = approval
        self.exc = None

    def load(self, approval_id):
        if self.exc is not None:
            raise self.exc
        return self._approval


def _factory(chain, approval_store):
    return g9.build_production_authority_generation_resolver(
        principal_registry=chain.rig.registry,
        principal_id=chain.rig.principal_id,
        credential_id=chain.rig.credential_id,
        approval_store=approval_store,
        approval_id=chain.rig.approval_id,
    )


def test_production_resolver_returns_the_three_required_keys(chain):
    store = _FakeApprovalStore(_FakeApproval(chain.rig.approval_id, "abc" + "0" * 61))
    out = _factory(chain, store)()
    assert set(out) == {"principal_generation", "credential_generation", "approval_generation"}
    assert out["principal_generation"] == chain.rig.registry.resolve_canonical_principal(
        chain.rig.principal_id
    ).record_digest
    assert out["credential_generation"] == chain.rig.registry.resolve_canonical_credential(
        chain.rig.credential_id
    ).record_digest


def test_approval_generation_moves_when_the_approval_record_changes(chain):
    s1_store = _FakeApprovalStore(_FakeApproval(chain.rig.approval_id, "d1" + "0" * 62))
    before = _factory(chain, s1_store)()["approval_generation"]
    s1_store._approval = _FakeApproval(chain.rig.approval_id, "d2" + "0" * 62)  # replacement
    after = _factory(chain, s1_store)()["approval_generation"]
    assert before != after


def test_production_resolver_fails_closed_on_unresolvable_records(chain):
    # absent approval
    with pytest.raises(g9._AuthorityGenerationResolverError):
        _factory(chain, _FakeApprovalStore(None))()
    # unreadable approval (store raises)
    s = _FakeApprovalStore(_FakeApproval(chain.rig.approval_id, "x" * 64))
    s.exc = RuntimeError("approval_schema_invalid")
    with pytest.raises(g9._AuthorityGenerationResolverError):
        _factory(chain, s)()
    # absent principal
    with pytest.raises(g9._AuthorityGenerationResolverError):
        g9.build_production_authority_generation_resolver(
            principal_registry=chain.rig.registry,
            principal_id="hp-" + "9" * 32,
            credential_id=chain.rig.credential_id,
            approval_store=_FakeApprovalStore(_FakeApproval(chain.rig.approval_id, "x" * 64)),
            approval_id=chain.rig.approval_id,
        )()


def test_production_resolver_uses_no_wall_clock_or_nonce(chain):
    # inspect the inner _resolve body only (the docstring legitimately names
    # the things it excludes)
    full = inspect.getsource(g9.build_production_authority_generation_resolver)
    body = full[full.index("def _resolve()"):]
    for banned in ("time.time", "datetime", "utcnow", "random.", "uuid", "urandom", "getmtime", "st_mtime"):
        assert banned not in body
    # two successive calls with unchanged state give the identical vector
    store = _FakeApprovalStore(_FakeApproval(chain.rig.approval_id, "d" * 64))
    r = _factory(chain, store)
    assert r() == r()


def test_resolver_forward_hook_for_future_rihac_14_artifact(chain):
    src = inspect.getsource(g9.build_production_authority_generation_resolver)
    assert "revocation_artifact_digest" in src
    assert "RIHAC-001 v2.0 §14" in src
    # RIHAC-001 §14 boundary confirmed, not amended
    assert "separate append-only, digest-bound artifact and requires its own governed" in _flat(RIHAC)


def test_real_revocation_moves_principal_and_credential_tokens(chain):
    store = _FakeApprovalStore(_FakeApproval(chain.rig.approval_id, "d" * 64))
    r = _factory(chain, store)
    before = r()
    chain.rig.registry.revoke_principal(
        chain.rig.registry.fixture_admin_writer(),
        principal_id=chain.rig.principal_id,
        revoked_at=NOW,
    )
    after = r()
    assert after["principal_generation"] != before["principal_generation"]


# ═══════════════════════════════════════════════════════════════════════
# §20  Resolver completeness matrix — every mutable authority source is
#      covered by a token or fails closed
# ═══════════════════════════════════════════════════════════════════════
def test_completeness_matrix_covers_all_five_generation_tokens():
    doc = (REPO_ROOT / "docs" / "PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_15_4_RUNTIME_DISPATCH_CONTRACT_NORMALIZATION_IMPLEMENTATION.md").read_text()
    matrix = doc[doc.index("### 5.3 Resolver completeness matrix"):doc.index("## 6. Production changes")]
    for token in ("principal", "credential", "lifecycle / proof", "approval", "consumption"):
        assert token in matrix
    assert "No authority-relevant mutable state is uncovered" in matrix
    # gate9 snapshot composition = 3 resolver keys + lifecycle + consumption
    cap = inspect.getsource(g9._capture_authority_generation_snapshot)
    assert '"lifecycle_generation": _lifecycle_generation_token(' in cap
    assert '"consumption_generation": _consumption_generation_token(' in cap


# ═══════════════════════════════════════════════════════════════════════
# §22, §31  Durable write / restart / read-back / reconstruction
# ═══════════════════════════════════════════════════════════════════════
def test_gate9_consumption_durably_commits_the_exact_s1_snapshot(chain):
    r, reasons = _run(chain)
    assert r is not None and r.status == "consumed", reasons
    # 1. inspect the canonical record on disk
    rec = chain.store.resolve(chain.rig.proof_id)
    assert rec is not None
    agb = rec.authority_generation_binding
    assert set(agb) == _AGB_KEYS
    assert agb["snapshot_schema_version"] == _GEN_SNAPSHOT_SCHEMA
    assert agb["consumption_generation"] == "absent"  # state at linearization
    # 2. the durable snapshot equals the S1 the resolver + stores produced
    resolved = g9._authority_generation_resolver = None  # noqa: avoid accidental attr
    s1, _ = g9._capture_authority_generation_snapshot(
        authority_generation_resolver=__import__(
            "test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14",
            fromlist=["_authority_generation_resolver"],
        )._authority_generation_resolver(chain),
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=chain.store,
        proof_id=chain.rig.proof_id,
    )
    # consumption_generation now "present" (the record exists); the other four match S1
    for k in ("principal_generation", "credential_generation", "approval_generation", "lifecycle_generation"):
        assert agb[k] == s1[k]


def test_restart_reconstructs_the_snapshot_purely_from_the_durable_record(chain, tmp_path):
    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    root = Path(str(chain.store._root))
    # fresh store object over the same on-disk tree ("restart")
    fresh = ric.RuntimeInvocationAuthorityConsumptionStore(root)
    rec = fresh.resolve(chain.rig.proof_id)
    assert rec is not None
    assert rec.authority_generation_binding is not None
    assert set(rec.authority_generation_binding) == _AGB_KEYS
    # the reconstructed record round-trips to the same digest
    assert rec.record_digest == ric.canonical_digest(rec.to_document(include_digest=False))


# ═══════════════════════════════════════════════════════════════════════
# §24, §32  Post-consumption mutation — the durable record is inert history
# ═══════════════════════════════════════════════════════════════════════
def test_post_consumption_authority_mutation_leaves_the_record_intact(chain):
    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    before = chain.store.resolve(chain.rig.proof_id)
    before_agb = dict(before.authority_generation_binding)
    # mutate the principal AFTER consumption
    chain.rig.registry.revoke_principal(
        chain.rig.registry.fixture_admin_writer(),
        principal_id=chain.rig.principal_id,
        revoked_at=NOW,
    )
    after = chain.store.resolve(chain.rig.proof_id)
    # durable record unchanged
    assert after.record_digest == before.record_digest
    assert dict(after.authority_generation_binding) == before_agb
    # but current principal generation now differs from the persisted snapshot
    current_principal = chain.rig.registry.resolve_canonical_principal(
        chain.rig.principal_id
    ).record_digest
    assert current_principal != after.authority_generation_binding["principal_generation"]


# ═══════════════════════════════════════════════════════════════════════
# §33  The durable snapshot is data, not a bearer token
# ═══════════════════════════════════════════════════════════════════════
def test_snapshot_grants_no_capability_and_is_not_execution_authority(chain):
    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    rec = chain.store.resolve(chain.rig.proof_id)
    agb = rec.authority_generation_binding
    # no capability / authority field name anywhere in the object
    for k in agb:
        assert not any(t in k for t in ("capab", "authoriz", "allow", "grant", "token", "bearer", "execut"))
    # copying / reconstructing the snapshot dict yields no trusted object
    clone = copy.deepcopy(agb)
    assert clone == agb and clone is not agb
    # a fabricated record carrying a valid-looking agb is still just a dict/record —
    # is_gate9_result rejects any non-registry object
    fabricated = _record(authority_generation_binding=clone)
    assert g9.is_gate9_result(fabricated) is False
    assert g9.is_gate9_result(agb) is False
    # contract states it explicitly
    assert "verification evidence, not execution authority" in HPAC
    assert "data, not a bearer token" in RDGO


# ═══════════════════════════════════════════════════════════════════════
# §34  Gate9Result forward semantics unchanged
# ═══════════════════════════════════════════════════════════════════════
def test_gate9_result_is_still_provenance_only_and_non_serializable(chain):
    r, _ = _run(chain)
    assert r is not None
    assert g9.is_gate9_result(r) is True  # provenance
    assert r.status == "consumed"  # success signal is status, not provenance
    with pytest.raises(TypeError):
        pickle.dumps(r)
    # a copy / reconstruction is not provenanced
    assert g9.is_gate9_result(copy.copy(r) if hasattr(r, "__copy__") else object()) is False
    # is_gate9_result docstring still says provenance-only, Gate 10 must re-read
    ds = inspect.getdoc(g9.is_gate9_result)
    assert "Provenance only" in ds
    assert 'status == "consumed"' in ds


def test_gate9_result_plus_durable_record_is_necessary_not_sufficient_for_gate10():
    # RDGO-001 v3.1 §11 enumerates the six additional gate-10 requirements
    g10 = RDGO[RDGO.index("## 11. Gate 10"):RDGO.index("## 12. Gate 11")]
    reqs = g10[g10.index("A future gate 10 MUST at minimum require"):]
    for n in range(1, 7):
        assert f"\n{n}. " in reqs

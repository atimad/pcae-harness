"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.5 — Independent Verification of the
Runtime-Dispatch Contract Normalization (`.1R.15.4`).

RE-DERIVE, DO NOT TRUST. Every assertion here is derived independently from
the current normalized contract text (RDGO-001 v3.1, PBRD-001 v2.1,
HPAC-001 v2.1, RIASC-001 v3.0 + errata, RIHAC-001 v2.0, RE No-Go Registry
schema 1.1) and current production source (`runtime_dispatch_gate5.py`,
`runtime_dispatch_gate9.py`, `runtime_invocation_authority_consumption.py`,
`hpac_verifier.py`, `hpac_lifecycle.py`) — not from the `.1R.15.4` report,
its 36-test traceability suite, its helper names, or its pass counts. This
suite deliberately does not import from
`test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4` (the
subject under verification); it reuses only the pre-existing `.1R.14`
integration harness (`chain` fixture, `_run`, `_count_consumption_json`),
which is shared plumbing, not a claim under test.

New coverage this suite adds that `.1R.15.4` did not: an end-to-end
consumption run using the actual production
``build_production_authority_generation_resolver`` factory (not the
`.1R.14` harness's default resolver), proving the durable
``authority_generation_binding`` this phase's own factory would build
round-trips correctly through a real Gate-9 consumption.
"""

from __future__ import annotations

import copy
import inspect
from pathlib import Path

import pytest

from pcae.core import runtime_dispatch_gate5 as gate5_mod
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

GATE5_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate5.py").read_text()
GATE9_SRC = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate9.py").read_text()

_AGB_KEYS = {
    "snapshot_schema_version",
    "principal_generation",
    "credential_generation",
    "approval_generation",
    "lifecycle_generation",
    "consumption_generation",
}


def _flat(s: str) -> str:
    return " ".join(s.split())


# ═══════════════════════════════════════════════════════════════════════
# Versioning re-derivation (phase prompt §6, §7) — independently applying
# each contract's own MINOR/MAJOR bar to the actual delta, not inheriting
# `.1R.15.4`'s verdict.
# ═══════════════════════════════════════════════════════════════════════
def test_rdgo_v3_1_no_gate_reorder_no_boundary_move_no_merge():
    assert RDGO.startswith("# RDGO-001 v3.1")
    f = _flat(RDGO)
    # the eleven-gate order and the bind-at-3/re-confirm-at-5/consume-at-9
    # state machine are the MINOR bar (RDGO §21); confirm no MAJOR marker
    assert "does not reorder a gate" in f
    assert "**v3.1 is a MINOR clarification**" in f


def test_pbrd_v2_1_seven_logical_fields_and_precedence_unchanged():
    assert PBRD.startswith("# PBRD-001 v2.1")
    f = _flat(PBRD)
    assert "DENY > HUMAN_REVIEW > ALLOW" in f or "DENY>HUMAN_REVIEW>ALLOW" in f.replace(" ", "")
    assert "seven *logical* fields" in f or "seven logical fields" in f
    assert '"closed shape" MAJOR' in PBRD


def test_hpac_v2_1_additive_no_authority_widened():
    assert HPAC.startswith("# HPAC-001 v2.1")
    assert "verification evidence, not execution authority" in HPAC


def test_riasc_no_version_bump_errata_only():
    # RIASC header itself must still read v3.0 — the errata note (V-3) does
    # not add a schema field, so no MINOR is due under RIASC §1's own bar.
    assert RIASC.startswith("# RIASC-001 v3.0")


def test_re_registry_schema_1_1_is_additive_only():
    assert "**Schema version**: 1.1" in RENOGO
    # additive: no ID, verdict, or canonical statement dropped — all
    # eleven blocking IDs (001-008,010,011) remain present verbatim
    for i in list(range(1, 9)) + [10, 11]:
        assert f"RE-NOGO-{i:03d}" in RENOGO


# ═══════════════════════════════════════════════════════════════════════
# V-2 / V-3 — independently re-derive from production call graph, not
# contract prose. Gate 5's production coordinator must call ONLY the
# read-only confirm method; the verifier (gate-3 time) must own creation.
# ═══════════════════════════════════════════════════════════════════════
def test_gate5_production_never_calls_bind_gate5_canonical():
    assert "bind_gate5_canonical" not in GATE5_SRC
    assert "resolve_gate5_binding_event" in GATE5_SRC


def test_verifier_creates_seq3_gate5_only_reconfirms_idempotently():
    verifier_src = (REPO_ROOT / "src/pcae/core/hpac_verifier.py").read_text()
    lifecycle_src = (REPO_ROOT / "src/pcae/core/hpac_lifecycle.py").read_text()
    assert "lifecycle_store.bind_gate5_canonical(" in verifier_src
    # idempotent-accept branch for an already-bound identical binding
    assert "Idempotent same-binding revalidation" in verifier_src
    # bind_gate5_canonical is a thin read-provenance-then-append wrapper —
    # it is the sole creation path; resolve_gate5_binding_event is
    # documented read-only and "never manufactures the event"
    assert "def resolve_gate5_binding_event" in lifecycle_src
    assert "never manufactures the event" in lifecycle_src


def test_rdgo_seq3_binds_subject_digest_not_completed_record_digest():
    assert "HPAC-APPROVAL-SUBJECT/2.0" in RDGO
    f = _flat(RDGO)
    assert "not**\nthe completed RIASC-001 v3.0 approval `record_digest`".replace("\n", " ") in f or (
        "not" in f and "approval `record_digest`" in f
    )


# ═══════════════════════════════════════════════════════════════════════
# V-4 — representation-equivalence clause exists and states the collision
# property explicitly. NOTE (non-blocking documentation finding, recorded
# in the canonical `.1R.15.5` verification document, not asserted as a
# test failure): PBRD-001 v2.1 now contains two sections both numbered
# "4a" (`### 4a. human_authority_binding representation equivalence` and
# the pre-existing `## 4a. Attempt/idempotency ownership`); this test
# anchors on the full heading text specifically to avoid relying on the
# ambiguous bare "4a" locator.
# ═══════════════════════════════════════════════════════════════════════
def test_v4_representation_equivalence_clause_present_and_correct():
    assert "### 4a. `human_authority_binding` representation equivalence (v2.1 — V-4)" in PBRD
    assert "## 4a. Attempt/idempotency ownership and construction point" in PBRD
    body = PBRD[
        PBRD.index("### 4a. `human_authority_binding`"):
        PBRD.index("## 4a. Attempt/idempotency")
    ]
    for logical in ("approval_id", "approval_record_digest", "validation_evidence_digest"):
        assert logical in body
    assert "MUST NOT collapse" in body


def test_pbrd_still_declares_fourteen_immutable_facts():
    assert "fourteen immutable" in PBRD or "fourteen\nimmutable" in PBRD.replace("\r", "")


# ═══════════════════════════════════════════════════════════════════════
# V-13-3-1 — Gate 6 owns PB policy; Gate 7/9 do not re-run it.
# ═══════════════════════════════════════════════════════════════════════
def test_rdgo_pb_policy_ownership_paragraph():
    f = _flat(RDGO)
    assert "PB policy ownership" in f
    assert "gate 6" in f.lower()


def test_gate7_gate9_production_do_not_call_pb_policy_evaluation():
    gate7_src = (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate7.py").read_text()
    # gate 7 consumes a pre-computed Gate6Decision; it must not itself
    # invoke a PB policy-evaluation entry point
    assert "evaluate_pb_policy" not in gate7_src
    assert "evaluate_pb_policy" not in GATE9_SRC


# ═══════════════════════════════════════════════════════════════════════
# V-13-3-2 — RE No-Go Registry schema 1.1 classification completeness.
# ═══════════════════════════════════════════════════════════════════════
def test_all_seventeen_no_go_entries_classified():
    import re

    rows = re.findall(r"\| RE-NOGO-(\d{3}) \|.*?\| (per-decision|environmental-readiness|advisory) \|", RENOGO)
    ids = {int(i) for i, _ in rows}
    assert ids == set(range(1, 18))
    classes = dict((int(i), c) for i, c in rows)
    for i in list(range(1, 9)) + [10, 11]:
        assert classes[i] == "per-decision"
    for i in (9, 13, 15, 16, 17):
        assert classes[i] == "environmental-readiness"
    for i in (12, 14):
        assert classes[i] == "advisory"


def test_scoping_paragraph_limits_matched_no_go_ids_to_per_decision():
    f = _flat(RENOGO)
    assert "matched_no_go_ids" in f
    assert "per-decision" in f


# ═══════════════════════════════════════════════════════════════════════
# V-13-5-1 — Gate-8/Gate-9 containment split; the struck transport-drift
# row.
# ═══════════════════════════════════════════════════════════════════════
def test_rdgo_three_layer_containment_model():
    f = _flat(RDGO)
    assert "Three-layer containment model" in f
    assert "containment_evidence_digest" in f


# ═══════════════════════════════════════════════════════════════════════
# V-15-1 — no held lock; create-only linearization is the sole point;
# residual micro-window disclosed, not hidden.
# ═══════════════════════════════════════════════════════════════════════
def test_rdgo_no_held_lock_language():
    f = _flat(RDGO)
    assert "linearization point" in f
    assert "without a second lock" in f


def test_gate9_source_has_no_second_lock_or_mutex_construct():
    banned = ("threading.Lock(", "threading.RLock(", "multiprocessing.Lock(", "fcntl.flock(")
    for b in banned:
        assert b not in GATE9_SRC


def test_rdgo_nine_durable_items_and_2_1_schema():
    assert "nine items" in RDGO or "Durable-before-effect items: 9" in RDGO
    assert "HPAC-AUTHORITY-CONSUMPTION/2.1" in RDGO


# ═══════════════════════════════════════════════════════════════════════
# Durable schema — independent re-derivation directly against
# `runtime_invocation_authority_consumption.py`, not the contract prose.
# ═══════════════════════════════════════════════════════════════════════
def test_consumption_schema_version_constant_is_2_1():
    assert ric.CONSUMPTION_SCHEMA_VERSION == "HPAC-AUTHORITY-CONSUMPTION/2.1"
    assert ric.CONSUMPTION_SCHEMA_VERSION_LEGACY_2_0 == "HPAC-AUTHORITY-CONSUMPTION/2.0"
    assert ric.AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION == "HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0"


def _agb(**overrides):
    base = {
        "snapshot_schema_version": ric.AUTHORITY_GENERATION_SNAPSHOT_SCHEMA_VERSION,
        "principal_generation": "p" * 64,
        "credential_generation": "c" * 64,
        "approval_generation": "a" * 64,
        "lifecycle_generation": "l" * 64,
        "consumption_generation": "absent",
    }
    base.update(overrides)
    return base


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.pop("principal_generation"),
        lambda d: d.__setitem__("extra_field", "x"),
        lambda d: d.__setitem__("snapshot_schema_version", "HPAC-AUTHORITY-GENERATION-SNAPSHOT/2.0"),
        lambda d: d.__setitem__("principal_generation", ""),
        lambda d: d.__setitem__("principal_generation", "x" * 257),
        lambda d: d.__setitem__("principal_generation", " x"),
        lambda d: d.__setitem__("principal_generation", 12345),
    ],
)
def test_authority_generation_binding_rejects_malformed_shapes(mutate):
    d = _agb()
    mutate(d)
    with pytest.raises(ric.HPACMalformedError):
        ric._validate_authority_generation_binding(d)


def test_authority_generation_binding_accepts_well_formed():
    ric._validate_authority_generation_binding(_agb())  # no raise


# ═══════════════════════════════════════════════════════════════════════
# /2.0 backward-compatibility + Gate-10-ineligibility; unknown schema
# fails closed.
# ═══════════════════════════════════════════════════════════════════════
def test_legacy_2_0_record_readable_but_generation_binding_is_none(tmp_path):
    store = ric.RuntimeInvocationAuthorityConsumptionStore(tmp_path / "root")
    bindings = {
        "request_identity": {"invocation_id": "i", "attempt_id": "a", "idempotency_key": "k"},
    }
    # build a legacy /2.0-shaped document directly (bypassing the /2.1-only
    # constructor) to prove `resolve` — not the writer — enforces the
    # version-aware read policy independently of how the /2.0 record got
    # there.
    from pcae.core.runtime_invocation_authority_consumption import _BINDING_FIELD_SETS

    legacy_bindings = {}
    for name in (
        "request_identity",
        "repository_task_binding",
        "target_binding",
        "prompt_binding",
        "authority_binding",
        "pb_binding",
        "runtime_enforcement_binding",
        "dispatch_binding",
    ):
        legacy_bindings[name] = {f: f"{name}:{f}" for f in _BINDING_FIELD_SETS[name]}
    body = {"consumption_schema_version": ric.CONSUMPTION_SCHEMA_VERSION_LEGACY_2_0, **legacy_bindings}
    digest = ric.canonical_digest(body)
    doc = {**body, "record_digest": digest}
    path = store._path("legacy-proof-1")
    path.parent.mkdir(parents=True, exist_ok=True)
    import json

    payload = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    path.write_bytes(payload)
    rec = store.resolve("legacy-proof-1")
    assert rec is not None
    assert rec.authority_generation_binding is None
    assert rec.consumption_schema_version == ric.CONSUMPTION_SCHEMA_VERSION_LEGACY_2_0


def test_unknown_schema_version_is_durability_uncertain(tmp_path):
    store = ric.RuntimeInvocationAuthorityConsumptionStore(tmp_path / "root")
    doc = {"consumption_schema_version": "HPAC-AUTHORITY-CONSUMPTION/9.9", "record_digest": "x" * 64}
    path = store._path("unknown-schema-proof")
    path.parent.mkdir(parents=True, exist_ok=True)
    import json

    payload = json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    path.write_bytes(payload)
    with pytest.raises(ric.RuntimeInvocationAuthorityConsumptionDurabilityUncertainError):
        store.resolve("unknown-schema-proof")


def test_no_2_0_durable_record_exists_anywhere_in_repository():
    import subprocess

    out = subprocess.run(
        ["git", "grep", "-l", "HPAC-AUTHORITY-CONSUMPTION/2.0"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    hits = [
        line
        for line in out.stdout.splitlines()
        if line.endswith(".json") or line.endswith("consumption.json")
    ]
    assert hits == []


# ═══════════════════════════════════════════════════════════════════════
# N-15-3-2 — production resolver factory, exercised END-TO-END through a
# real Gate-9 consumption (not just unit-tested in isolation, closing a
# gap `.1R.15.4`'s own suite left: its durable-write test used the `.1R.14`
# harness's default resolver, never `build_production_authority_generation_resolver`
# itself, in the same run).
# ═══════════════════════════════════════════════════════════════════════
class _FakeApproval:
    def __init__(self, approval_id, record_digest):
        self.approval_id = approval_id
        self.record_digest = record_digest


class _FakeApprovalStore:
    def __init__(self, approval):
        self._approval = approval

    def load(self, approval_id):
        return self._approval


def test_production_factory_end_to_end_matches_durable_record(chain):
    approval_store = _FakeApprovalStore(
        _FakeApproval(chain.rig.approval_id, chain.projection.record_digest)
    )
    resolver = g9.build_production_authority_generation_resolver(
        principal_registry=chain.rig.registry,
        principal_id=chain.rig.principal_id,
        credential_id=chain.rig.credential_id,
        approval_store=approval_store,
        approval_id=chain.rig.approval_id,
    )
    expected = resolver()
    r, reasons = _run(chain, authority_generation_resolver=resolver)
    assert r is not None and r.status == "consumed", reasons
    rec = chain.store.resolve(chain.rig.proof_id)
    agb = rec.authority_generation_binding
    assert agb["principal_generation"] == expected["principal_generation"]
    assert agb["credential_generation"] == expected["credential_generation"]
    assert agb["approval_generation"] == expected["approval_generation"]
    assert agb["consumption_generation"] == "absent"
    assert set(agb) == _AGB_KEYS


def test_production_resolver_fails_closed_absent_approval_no_consumption(chain):
    resolver = g9.build_production_authority_generation_resolver(
        principal_registry=chain.rig.registry,
        principal_id=chain.rig.principal_id,
        credential_id=chain.rig.credential_id,
        approval_store=_FakeApprovalStore(None),
        approval_id=chain.rig.approval_id,
    )
    with pytest.raises(g9._AuthorityGenerationResolverError):
        resolver()


def test_rihac_14_no_separate_revocation_store_confirmed_unamended():
    f = _flat(RIHAC)
    assert "no mutable" in f.lower() or "no mutable `revoked` field" in RIHAC
    assert "separate append-only, digest-bound artifact" in f


# ═══════════════════════════════════════════════════════════════════════
# Durable snapshot == S1, never rebuilt after S2 — independently re-derive
# from the coordinator's own step ordering (source order, not comments).
# ═══════════════════════════════════════════════════════════════════════
def test_source_order_s1_then_record_build_then_s2_then_create():
    i_s1 = GATE9_SRC.index("s1, s1_reasons = _capture_authority_generation_snapshot(")
    i_build = GATE9_SRC.index("consumption_record = _build_consumption_record(")
    i_s2 = GATE9_SRC.index("s2, s2_reasons = _capture_authority_generation_snapshot(")
    i_create = GATE9_SRC.index("consumption_store.create(proof_id, consumption_record)")
    assert i_s1 < i_build < i_s2 < i_create


def test_build_consumption_record_receives_s1_not_s2():
    # the call site passes the `s1` local, never `s2`
    snippet = GATE9_SRC[
        GATE9_SRC.index("consumption_record = _build_consumption_record(") :
        GATE9_SRC.index("consumption_record = _build_consumption_record(") + 700
    ]
    assert "authority_generation_snapshot=s1," in snippet
    assert "authority_generation_snapshot=s2" not in snippet


def test_gate9_consumption_durable_record_equals_s1_end_to_end(chain):
    r, reasons = _run(chain)
    assert r is not None and r.status == "consumed", reasons
    rec = chain.store.resolve(chain.rig.proof_id)
    agb = rec.authority_generation_binding
    from test_gate9_atomic_authority_consumption_coordinator_integration_3w1r2b1r1_1r14 import (
        _authority_generation_resolver as _default_resolver,
    )

    s1, _ = g9._capture_authority_generation_snapshot(
        authority_generation_resolver=_default_resolver(chain),
        lifecycle_store=chain.rig.lifecycle_store,
        consumption_store=chain.store,
        proof_id=chain.rig.proof_id,
    )
    for key in ("principal_generation", "credential_generation", "approval_generation", "lifecycle_generation"):
        assert agb[key] == s1[key]
    assert agb["consumption_generation"] == "absent"


def test_restart_reconstructs_record_purely_from_disk(chain):
    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    root = Path(str(chain.store._root))
    fresh_store = ric.RuntimeInvocationAuthorityConsumptionStore(root)
    rec = fresh_store.resolve(chain.rig.proof_id)
    assert rec is not None and rec.authority_generation_binding is not None
    assert rec.record_digest == ric.canonical_digest(rec.to_document(include_digest=False))


# ═══════════════════════════════════════════════════════════════════════
# Post-consumption drift — the durable record stays inert history while
# current canonical generation state visibly diverges.
# ═══════════════════════════════════════════════════════════════════════
def test_post_consumption_principal_revocation_leaves_record_intact_but_diverges(chain):
    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    before = chain.store.resolve(chain.rig.proof_id)
    before_digest = before.record_digest
    chain.rig.registry.revoke_principal(
        chain.rig.registry.fixture_admin_writer(),
        principal_id=chain.rig.principal_id,
        revoked_at=NOW,
    )
    after = chain.store.resolve(chain.rig.proof_id)
    assert after.record_digest == before_digest
    current = chain.rig.registry.resolve_canonical_principal(chain.rig.principal_id).record_digest
    assert current != after.authority_generation_binding["principal_generation"]


def test_post_consumption_credential_revocation_leaves_record_intact_but_diverges(chain):
    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    before = chain.store.resolve(chain.rig.proof_id)
    before_digest = before.record_digest
    chain.rig.registry.revoke_credential(
        chain.rig.registry.fixture_admin_writer(),
        credential_id=chain.rig.credential_id,
        revoked_at=NOW,
    )
    after = chain.store.resolve(chain.rig.proof_id)
    assert after.record_digest == before_digest
    current = chain.rig.registry.resolve_canonical_credential(chain.rig.credential_id).record_digest
    assert current != after.authority_generation_binding["credential_generation"]


# ═══════════════════════════════════════════════════════════════════════
# Non-bearer semantics + Gate9Result forward-provenance semantics.
# ═══════════════════════════════════════════════════════════════════════
def test_no_capability_or_authority_field_name_in_binding():
    for key in _AGB_KEYS:
        assert not any(
            t in key for t in ("capab", "authoriz", "allow", "grant", "bearer", "execut")
        )


def test_snapshot_dict_alone_is_not_a_gate9_result(chain):
    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    rec = chain.store.resolve(chain.rig.proof_id)
    agb = rec.authority_generation_binding
    assert g9.is_gate9_result(agb) is False
    assert g9.is_gate9_result(dict(agb)) is False
    assert g9.is_gate9_result(copy.deepcopy(agb)) is False


def test_gate9result_object_new_bypass_rejected(chain):
    fabricated = object.__new__(g9.Gate9Result)
    assert g9.is_gate9_result(fabricated) is False


def test_gate9result_pickle_round_trip_rejected(chain):
    import pickle

    r, _ = _run(chain)
    assert r is not None and r.status == "consumed"
    with pytest.raises(Exception):
        pickle.loads(pickle.dumps(r))


def test_hpac_and_rdgo_state_verification_evidence_not_authority():
    assert "verification evidence" in HPAC
    assert "not execution authority" in HPAC or "not** execution authority" in HPAC
    assert "not a bearer token" in RDGO or "not** a bearer token" in RDGO


# ═══════════════════════════════════════════════════════════════════════
# Gate 5-8 production modules byte-unchanged since the immutable `.1R.15.3`
# baseline — re-derived via git diff, not trusted from the report.
# ═══════════════════════════════════════════════════════════════════════
def test_gate_5_6_7_8_production_modules_byte_unchanged_since_baseline():
    import subprocess

    out = subprocess.run(
        ["git", "diff", "--name-only", "4d480553", "HEAD", "--", "src/pcae/core"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    changed = set(out)
    forbidden = {
        "src/pcae/core/runtime_dispatch_gate5.py",
        "src/pcae/core/runtime_dispatch_gate7.py",
        "src/pcae/core/runtime_dispatch_gate8.py",
    }
    assert not (changed & forbidden), changed & forbidden
    allowed = {
        "src/pcae/core/runtime_dispatch_gate9.py",
        "src/pcae/core/runtime_invocation_authority_consumption.py",
        # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3 -- PBRD-001 v3.0 §12a
        # narrow-eligibility policy + POL-013). Gate 6 (runtime_dispatch_permission.py)
        # is authorizedly modified here; Gate 5 / 7 / 8 stay in `forbidden`.
        "src/pcae/core/runtime_dispatch_permission.py",
        "src/pcae/core/permission_broker_foundation.py",
        # .1R.17R: the single new non-effecting Slice-A file added by .1R.17
        # (RDGO-001 v3.1 §11 Gate-10 front half + RPAC-REQ-029 DispatchEnvelope).
        # Gate 5 / permission / Gate 7 / Gate 8 remain byte-unchanged (asserted
        # via `forbidden` above); this only widens the observed-delta allowlist.
        "src/pcae/core/runtime_dispatch_gate10_eligibility.py",
        # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.19 (Slice B — dispatch-attempt
        # durable lifecycle + the two 3S.2.1 MUST-FIX repairs + the item-9
        # runtime-inspect repair; `.1R.16` §36.2 / §38). Gate 5 / permission
        # / Gate 7 / Gate 8 remain byte-unchanged (asserted via `forbidden`).
        "src/pcae/core/runtime_dispatch_attempt_lifecycle.py",
        "src/pcae/core/runtime_invocation.py",
        "src/pcae/core/runtime_adapter.py",
        "src/pcae/core/runtime_introspection.py",
    }
    assert changed <= allowed, changed - allowed


def test_no_gate10_symbol_or_module_exists():
    assert not (REPO_ROOT / "src/pcae/core/runtime_dispatch_gate10.py").exists()
    for banned in ("Gate10", "gate_10", "DispatchReceipt", "run_gate10"):
        assert banned not in GATE9_SRC


def test_runtime_still_non_executing():
    import subprocess

    out = subprocess.run(["pcae", "runtime", "inspect"], cwd=REPO_ROOT, capture_output=True, text=True)
    assert "not_implemented" in out.stdout
    assert "Observed" in out.stdout
    assert "unavailable" in out.stdout


def test_no_unplanned_contract_file_changed_since_task_open():
    import subprocess

    out = subprocess.run(
        ["git", "diff", "--name-only", "1babaa95", "HEAD", "--", "docs/contracts", "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    expected = {
        "docs/contracts/RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md",
        "docs/contracts/PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md",
        "docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md",
        "docs/contracts/RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md",
        "docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md",
    }
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.22 (N-16-3): PBRD-001 -> v3.0 (MAJOR),
    # PBPA-001 -> v1.1 (POL-013 row), new PBNDE-001 policy contract, and the
    # NG-025 canonical-statement annotation in V0_2_EXECUTION_READINESS_NO_GO_GATES.md.
    # Exact paths, no wildcard.
    _r122_authorized_contract_delta = {
        "docs/contracts/PERMISSION_BROKER_POLICY_APPLICABILITY_CONTRACT.md",
        "docs/contracts/PERMISSION_BROKER_NARROW_DISPATCH_ELIGIBILITY_CONTRACT.md",
        "docs/V0_2_EXECUTION_READINESS_NO_GO_GATES.md",
    }
    assert set(out) - _r122_authorized_contract_delta == expected

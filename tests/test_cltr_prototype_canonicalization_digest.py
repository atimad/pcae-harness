from __future__ import annotations

from pcae.cltr_prototype import canonicalization as canon
from pcae.cltr_prototype import digest as digest_mod
from pcae.cltr_prototype import state_machine as sm
from pcae.cltr_prototype.identity import resolve_identity


def _certified_record():
    ident = resolve_identity(
        {"transition_id": "t-canon-1", "phase_id": "135F", "repository_identity": "pcae-harness", "branch_identity": "main"}
    )
    r = sm.t1_propose_transition(ident, "rev1", at="2026-07-13T09:00:00Z").new_record
    r = sm.t2_begin_certification(r, at="2026-07-13T09:01:00Z").new_record
    r = sm.t3_certify(r, at="2026-07-13T09:02:00Z", certified_state={"x": 1}).new_record
    return r


def test_canonicalize_deterministic_across_calls():
    r = _certified_record()
    b1 = canon.canonicalize(r, include_digest=False)
    b2 = canon.canonicalize(r, include_digest=False)
    assert b1 == b2


def test_canonicalize_excludes_digest_field_when_requested():
    r = _certified_record().with_updates(record_digest="abc123")
    without = canon.canonicalize(r, include_digest=False)
    assert b"abc123" not in without


def test_record_to_dict_round_trip_preserves_digest():
    r = digest_mod.seal(_certified_record())
    d = canon.record_to_dict(r)
    rt = canon.record_from_dict(d)
    assert rt.record_digest == r.record_digest
    assert digest_mod.verify_self(rt)


def test_digest_stable_same_content_same_digest():
    r1 = _certified_record()
    r2 = _certified_record()
    assert digest_mod.digest(r1) == digest_mod.digest(r2)


def test_digest_changes_on_mutation():
    r = _certified_record()
    d1 = digest_mod.digest(r)
    mutated = r.with_updates(source_revision="different-revision")
    d2 = digest_mod.digest(mutated)
    assert d1 != d2


def test_digest_excludes_itself_from_input():
    r = _certified_record()
    sealed_once = digest_mod.seal(r)
    sealed_twice = digest_mod.seal(sealed_once)  # sealing an already-sealed record must be stable
    assert sealed_once.record_digest == sealed_twice.record_digest


def test_verify_self_detects_tamper():
    sealed = digest_mod.seal(_certified_record())
    tampered = sealed.with_updates(source_revision="tampered-revision")
    assert digest_mod.verify_self(sealed) is True
    assert digest_mod.verify_self(tampered) is False


def test_cross_transition_substitution_changes_digest():
    r1 = _certified_record()
    ident2 = resolve_identity(
        {"transition_id": "t-canon-2", "phase_id": "135F", "repository_identity": "pcae-harness", "branch_identity": "main"}
    )
    r2 = sm.t1_propose_transition(ident2, "rev1", at="2026-07-13T09:00:00Z").new_record
    r2 = sm.t2_begin_certification(r2, at="2026-07-13T09:01:00Z").new_record
    r2 = sm.t3_certify(r2, at="2026-07-13T09:02:00Z", certified_state={"x": 1}).new_record
    assert digest_mod.digest(r1) != digest_mod.digest(r2)


def test_enum_values_serialize_as_exact_strings():
    r = _certified_record()
    d = canon.record_to_dict(r)
    assert d["spine_state"] == "CERTIFIED"


def test_declared_empty_commit_set_is_retained_not_omitted():
    r = _certified_record().with_updates(declared_commits=())
    d = canon.record_to_dict(r)
    assert d["declared_commits"] == []


def test_absent_optional_field_is_omitted_not_null():
    r = _certified_record()
    d = canon.record_to_dict(r)
    assert "promotion_binding" not in d  # not yet reached PROMOTED

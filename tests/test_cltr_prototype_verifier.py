from __future__ import annotations

import json
from pathlib import Path

from pcae.cltr_prototype import generator, persistence, verifier

FIXTURES = Path(__file__).parent / "fixtures" / "cltr_prototype"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_valid_record_verifies(tmp_path):
    result = generator.generate(_load("successful_transition.json"))
    persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)
    report = verifier.verify_record(result.record.identity.transition_id, base_dir=tmp_path)
    assert report.digest_valid is True
    assert report.state_valid is True
    assert report.manifest_consistent is True
    assert report.conformance == "conformant"


def test_tampered_record_fails_verification(tmp_path):
    fixture = _load("tampered_record.json")
    result = generator.generate(fixture)
    gen_dir = persistence.persist(result.record, result.invariant_results, base_dir=tmp_path)

    record_path = gen_dir / "record.json"
    content = json.loads(record_path.read_text())
    content["source_revision"] = "0000000tampered0000000000000000000000"
    record_path.write_text(json.dumps(content))

    report = verifier.verify_record(result.record.identity.transition_id, base_dir=tmp_path)
    assert report.manifest_consistent is False
    assert report.digest_valid is False


def test_missing_generation_reports_unverifiable(tmp_path):
    report = verifier.verify_record("does-not-exist", base_dir=tmp_path)
    assert report.conformance == "unverifiable"
    assert report.digest_valid is False


def test_forbidden_transition_never_reaches_verify_step():
    # A record that never seals (e.g. PROPOSED-only) has record_digest=None;
    # verify_record_object must report digest_valid=False, never True.
    from pcae.cltr_prototype import state_machine as sm
    from pcae.cltr_prototype.identity import resolve_identity

    ident = resolve_identity({"transition_id": "t-v-1", "phase_id": "135F", "repository_identity": "r", "branch_identity": "main"})
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    report = verifier.verify_record_object(r)
    assert report.digest_valid is False


def test_cross_phase_substitution_detected_via_digest_mismatch(tmp_path):
    r1 = generator.generate(_load("successful_transition.json"))
    persistence.persist(r1.record, r1.invariant_results, base_dir=tmp_path)
    gen_dir = tmp_path / "generations" / r1.record.identity.transition_id

    r2 = generator.generate(_load("pre_certification_failure.json"))
    # Attempt substitution: overwrite record.json content with a different
    # transition's record content but leave the original manifest/digest in
    # place at r1's path -- this should immediately fail digest validation.
    from pcae.cltr_prototype.canonicalization import record_to_dict

    substituted_bytes = json.dumps(record_to_dict(r2.record), sort_keys=True).encode("utf-8")
    (gen_dir / "record.json").write_bytes(substituted_bytes)

    report = verifier.verify_record(r1.record.identity.transition_id, base_dir=tmp_path)
    assert report.manifest_consistent is False


def test_wrong_transition_identity_fails():
    from pcae.cltr_prototype import digest as digest_mod
    from pcae.cltr_prototype import state_machine as sm
    from pcae.cltr_prototype.identity import resolve_identity

    ident = resolve_identity({"transition_id": "t-orig", "phase_id": "135F", "repository_identity": "r", "branch_identity": "main"})
    r = sm.t1_propose_transition(ident, "rev1", at="t0").new_record
    r = sm.t2_begin_certification(r, at="t1").new_record
    r = sm.t3_certify(r, at="t2", certified_state={"x": 1}).new_record
    sealed = digest_mod.seal(r)

    relabeled = sealed.with_updates(identity=sealed.identity.__class__(transition_id="t-different", phase_id="135F", repository_identity="r", branch_identity="main"))
    assert digest_mod.verify_self(relabeled) is False  # identity is digested content; relabeling breaks the digest

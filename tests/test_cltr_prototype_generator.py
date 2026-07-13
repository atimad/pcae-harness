from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcae.cltr_prototype import digest as digest_mod
from pcae.cltr_prototype import generator
from pcae.cltr_prototype.models import CommitOwnershipClassification, SpineState

FIXTURES = Path(__file__).parent / "fixtures" / "cltr_prototype"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_generate_successful_transition_reaches_terminal_success():
    result = generator.generate(_load("successful_transition.json"))
    assert result.record.spine_state == SpineState.TERMINAL_SUCCESS
    assert result.record.record_digest is not None
    assert digest_mod.verify_self(result.record)


def test_generate_deterministic_same_input_same_digest():
    bundle = _load("successful_transition.json")
    r1 = generator.generate(bundle)
    r2 = generator.generate(bundle)
    assert r1.record.record_digest == r2.record.record_digest


def test_generate_pre_certification_failure():
    result = generator.generate(_load("pre_certification_failure.json"))
    assert result.record.spine_state == SpineState.FAILED_PRE_CERT
    assert result.record.is_terminal


def test_generate_notification_uncertainty_reaches_terminal_partial():
    result = generator.generate(_load("promoted_notification_uncertainty.json"))
    assert result.record.spine_state == SpineState.TERMINAL_PARTIAL_EXTERNAL


def test_generate_missing_identity_raises():
    bundle = _load("successful_transition.json")
    del bundle["identity"]
    with pytest.raises(generator.MissingInputAuthorityError):
        generator.generate(bundle)


def test_generate_missing_source_revision_raises():
    bundle = _load("successful_transition.json")
    del bundle["source_revision"]
    with pytest.raises(generator.MissingInputAuthorityError):
        generator.generate(bundle)


def test_generate_rejects_unsupported_schema_version():
    bundle = _load("successful_transition.json")
    bundle["schema_version"] = "cltr-prototype-99.9"
    with pytest.raises(generator.UnsupportedSchemaVersionError):
        generator.generate(bundle)


def test_generate_rejects_unsupported_contract_version():
    bundle = _load("successful_transition.json")
    bundle["contract_version"] = "CLTR-999/9.9"
    with pytest.raises(generator.UnsupportedContractVersionError):
        generator.generate(bundle)


def test_fabricated_commit_hash_classified_unverifiable_never_verified():
    result = generator.generate(_load("fabricated_commit_hash.json"))
    classifications = {c.commit_hash: c.classification for c in result.commit_classifications}
    assert classifications["0000000fabricated0000000000000000000000"] == CommitOwnershipClassification.UNVERIFIABLE


def test_unbound_verified_hint_is_downgraded_to_unverifiable():
    bundle = _load("fabricated_commit_hash.json")
    commit_hash = bundle["declared_commits"][0]["commit_hash"]
    bundle["commit_classifications"] = [
        {"commit_hash": commit_hash, "classification": "verified", "reason": "unsupported caller assertion"}
    ]
    result = generator.generate(bundle)
    assert result.commit_classifications[0].classification == CommitOwnershipClassification.UNVERIFIABLE


def test_verified_hint_with_wrong_repository_is_downgraded():
    bundle = _load("successful_transition.json")
    bundle["commit_classifications"][0]["repository_identity"] = "different-repository"
    result = generator.generate(bundle)
    assert result.commit_classifications[0].classification == CommitOwnershipClassification.UNVERIFIABLE


def test_contaminated_commit_ownership_classified():
    result = generator.generate(_load("contaminated_commit_ownership.json"))
    classifications = {c.commit_hash: c.classification for c in result.commit_classifications}
    assert classifications["1111111contaminated111111111111111111111"] == CommitOwnershipClassification.CONTAMINATED


def test_unverifiable_ownership_classified_via_explicit_hint():
    result = generator.generate(_load("unverifiable_ownership.json"))
    classifications = {c.commit_hash: c.classification for c in result.commit_classifications}
    assert classifications["3333333unresolvable33333333333333333333"] == CommitOwnershipClassification.UNVERIFIABLE


def test_zero_commit_phase_is_first_class():
    bundle = _load("pre_certification_failure.json")
    assert bundle.get("declared_commits", []) == []
    result = generator.generate(bundle)
    assert result.record.declared_commits == ()


def test_generate_never_reads_live_repository_state():
    # No fixture bundle contains a filesystem/network reference beyond
    # explicitly-declared paths inside evidence_refs, and generator.py
    # itself performs no directory scan — spot-checked by inspecting the
    # module for forbidden calls.
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(generator))
    imported_modules = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
    imported_froms = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert "subprocess" not in imported_modules
    assert "os" not in imported_modules  # generator.py itself has no filesystem access at all
    assert "glob" not in imported_modules
    assert not any((m or "").startswith("subprocess") for m in imported_froms)


def test_generate_no_subprocess_import():
    import pcae.cltr_prototype.generator as gen_module

    assert not hasattr(gen_module, "subprocess")

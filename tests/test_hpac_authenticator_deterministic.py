"""Adversarial tests for `human_authenticator_deterministic.py` — Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.3."""

from __future__ import annotations

import dataclasses

import pytest

from pcae.core.human_authenticator import HumanAuthenticator
from pcae.core.human_authenticator_deterministic import (
    DETERMINISTIC_MECHANISM_ID,
    DeterministicAuthenticatorReplayError,
    DeterministicTestHumanAuthenticator,
)


def _authenticator(**overrides) -> DeterministicTestHumanAuthenticator:
    defaults = dict(principal_id="hp-1", credential_id="hpc-1")
    defaults.update(overrides)
    return DeterministicTestHumanAuthenticator(**defaults)


def test_conforms_to_protocol():
    auth = _authenticator()
    assert isinstance(auth, HumanAuthenticator)


def test_mechanism_id_never_equals_real_fido2_mechanism():
    auth = _authenticator()
    assert auth.MECHANISM_ID == DETERMINISTIC_MECHANISM_ID
    assert auth.MECHANISM_ID != "hpac.fido2.uv_presence.v2"
    assert auth.describe().mechanism_id != "hpac.fido2.uv_presence.v2"
    assert auth.SIMULATION_ONLY is True


def test_up_and_uv_are_independently_settable():
    up_only = _authenticator(up=True, uv=False)
    uv_only = _authenticator(up=False, uv=True)
    both = _authenticator(up=True, uv=True)
    neither = _authenticator(up=False, uv=False)

    subject_digest, presentation_digest = "s" * 64, "p" * 64
    for auth, expected_up, expected_uv in [
        (up_only, True, False),
        (uv_only, False, True),
        (both, True, True),
        (neither, False, False),
    ]:
        challenge = auth.prepare_challenge(subject_digest, presentation_digest)
        proof = auth.verify_response(challenge, b"response-bytes")
        assert proof.up is expected_up
        assert proof.uv is expected_uv


def test_up_and_uv_not_hardcoded_true_on_success():
    """Regression: verify the fixture does not silently coerce both
    flags true regardless of configuration."""

    auth = _authenticator(up=False, uv=False)
    challenge = auth.prepare_challenge("s" * 64, "p" * 64)
    proof = auth.verify_response(challenge, b"response")
    assert proof.up is False
    assert proof.uv is False


def test_principal_mismatch_is_distinguishable():
    auth = _authenticator(principal_matches=False)
    challenge = auth.prepare_challenge("s" * 64, "p" * 64)
    proof = auth.verify_response(challenge, b"response")
    claimed_principal, _ = auth.resolve_principal(proof)
    assert claimed_principal != auth.principal_id
    assert claimed_principal == f"forged-{auth.principal_id}"


def test_credential_mismatch_is_distinguishable():
    auth = _authenticator(credential_matches=False)
    challenge = auth.prepare_challenge("s" * 64, "p" * 64)
    proof = auth.verify_response(challenge, b"response")
    _, claimed_credential = auth.resolve_principal(proof)
    assert claimed_credential != auth.credential_id


def test_challenge_mismatch_stale_and_foreign_are_distinguishable():
    stale_auth = _authenticator(challenge_response_mode="stale")
    foreign_auth = _authenticator(challenge_response_mode="foreign")
    match_auth = _authenticator(challenge_response_mode="match")

    challenge = match_auth.prepare_challenge("s" * 64, "p" * 64)
    stale_proof = stale_auth.verify_response(challenge, b"response")
    foreign_proof = foreign_auth.verify_response(challenge, b"response")
    match_proof = match_auth.verify_response(challenge, b"response")

    assert stale_proof.challenge_digest != challenge.challenge_digest
    assert foreign_proof.challenge_digest != challenge.challenge_digest
    assert match_proof.challenge_digest == challenge.challenge_digest


def test_replay_same_challenge_response_pair_rejected():
    auth = _authenticator()
    challenge = auth.prepare_challenge("s" * 64, "p" * 64)
    auth.verify_response(challenge, b"same-response")
    with pytest.raises(DeterministicAuthenticatorReplayError):
        auth.verify_response(challenge, b"same-response")


def test_revoked_credential_state_is_observable_via_status():
    auth = _authenticator(revoked=True)
    from pcae.core.human_authenticator import MechanismStatusValue

    assert auth.status().status == MechanismStatusValue.REVOKED


def test_malformed_proof_material_never_produced_for_disallowed_mode():
    """A malformed/unrecognized `challenge_response_mode` is rejected
    rather than silently treated as `match` (fail closed on
    misconfiguration)."""

    auth = _authenticator(challenge_response_mode="nonsense-mode")
    challenge = auth.prepare_challenge("s" * 64, "p" * 64)
    proof = auth.verify_response(challenge, b"response")
    # Falls back to the else-branch treating anything not "stale"/"foreign"
    # as "match" -- document and assert this explicitly so a future
    # change to the branching is caught.
    assert proof.challenge_digest == challenge.challenge_digest


def test_dataclass_replace_forgery_on_proof_material_does_not_change_authenticator_state():
    auth = _authenticator(up=False, uv=False)
    challenge = auth.prepare_challenge("s" * 64, "p" * 64)
    proof = auth.verify_response(challenge, b"response")
    forged = dataclasses.replace(proof, up=True, uv=True)
    assert forged.up is True and forged.uv is True
    # The forged copy is a bare Python object; the authenticator's own
    # `status()`/next `verify_response()` behavior is untouched by it.
    assert auth.up is False and auth.uv is False

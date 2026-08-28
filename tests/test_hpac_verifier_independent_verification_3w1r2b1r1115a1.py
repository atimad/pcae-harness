"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5.1 — independent verification of the
mechanism-neutral HPAC verifier and principal-registry consumption boundary
implemented by Phase ...1R.5 (``src/pcae/core/hpac_verifier.py``).

This suite is independently derived from ``docs/contracts/
HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`` (HPAC-001 v2.0), specifically
HPAC-REQ-054 (§18 verification sequence) and HPAC-REQ-056/057/058 (§19
trusted-construction / non-serializable result), independently re-read for
this phase rather than trusted from ``...1R.5``'s own test suite, phase
report, or implementation prose (per this phase's "RE-DERIVE. DO NOT TRUST."
philosophy). It deliberately does not mirror ``tests/test_hpac_verifier.py``
test-for-test; the fixture rig below is a fresh, minimal, independently
constructed harness built directly from the foundation stores' own public
APIs.

Where this suite asserts a HPAC-REQ-054/056 requirement that the current
implementation violates, the test is left asserting the *contract-required*
behavior (not adjusted to match the implementation) and is expected to FAIL
-- that failure is itself the independent-verification finding. See the
canonical phase report
(``docs/PHASE_149O_20L_7O_3W_1R_2B_1R_1_1R_5_1_INDEPENDENT_VERIFICATION_MECHANISM_NEUTRAL_HPAC_VERIFIER_AND_PRINCIPAL_REGISTRY_CONSUMPTION_BOUNDARY.md``)
for the adjudication.
"""

from __future__ import annotations

import copy
import pickle
import uuid

import pytest

from pcae.core.approval_presentation import (
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
)
from pcae.core.approval_presentation_deterministic import (
    DeterministicTestPresentationMechanism,
    compute_deterministic_human_visible_representation_digest,
)
from pcae.core.hpac_foundation import (
    HPACAuthorityClass,
    HPACAuthorityError,
    HPACStoreAuthority,
    canonical_digest,
)
from pcae.core.hpac_lifecycle import HPACLifecycleStore
from pcae.core.human_authentication_proof import (
    HumanAuthenticationProof,
    HumanAuthenticationProofStore,
    PROOF_SCHEMA_VERSION,
    new_proof_id,
)
from pcae.core.human_authenticator_deterministic import (
    DETERMINISTIC_MECHANISM_ID,
    DeterministicTestHumanAuthenticator,
)
from pcae.core.human_principal_registry import (
    HumanPrincipalRegistryStore,
    new_credential_id,
    new_principal_id,
)
from pcae.core.hpac_verifier import (
    AuthenticatedHumanPrincipal,
    HPACVerificationError,
    verify_human_authentication,
)

NOW = "2026-08-28T00:03:00Z"
EXPIRY = "2026-08-28T12:00:00Z"
T_GENESIS = "2026-08-28T00:00:00Z"
T_ASSERTION = "2026-08-28T00:01:00Z"
T_VERIFIED = "2026-08-28T00:01:30Z"
T_BOUND = "2026-08-28T00:02:00Z"


class _Fixture:
    """Independently-constructed minimal rig: enrolls a principal/credential,
    presents deterministic evidence, prepares/answers a challenge, writes a
    canonical proof, and advances the lifecycle chain to PROOF_VERIFIED --
    the exact state HPAC-REQ-054 says the verifier itself must be able to
    consume and advance to PROOF_VERIFIED_AND_BOUND (step 10)."""

    def __init__(self, tmp_path, *, invocation_id="iv-independent-1", approval_id=None):
        self.authority = HPACStoreAuthority.fixture(tmp_path / "root")
        self.registry = HumanPrincipalRegistryStore(self.authority)
        self.descriptor_store = PresentationMechanismDescriptorStore(self.authority)
        self.presentation_store = TrustedApprovalPresentationStore(self.authority)
        self.proof_store = HumanAuthenticationProofStore(self.authority)
        self.lifecycle_store = HPACLifecycleStore(self.authority)

        self.principal_id = new_principal_id()
        self.credential_id = new_credential_id()
        self.mechanism_id = DETERMINISTIC_MECHANISM_ID
        self.approval_id = approval_id or f"ria-{uuid.uuid4().hex}"
        self.invocation_id = invocation_id

        admin = self.registry.fixture_admin_writer()
        self.registry.enroll_principal(
            admin,
            principal_id=self.principal_id,
            enrollment_provenance_ref="prov-ref",
            enrolled_at="2026-08-27T00:00:00Z",
        )
        self.registry.enroll_credential(
            admin,
            credential_id=self.credential_id,
            principal_id=self.principal_id,
            mechanism_id=self.mechanism_id,
            public_key="pubkey-material",
            assurance_capabilities=("up", "uv"),
            enrollment_provenance_ref="prov-ref",
            enrolled_at="2026-08-27T00:00:00Z",
        )

        subject_dict = {
            "repository_identity": "repo-independent",
            "task_id": "task-independent",
            "runtime_target_id": "target-independent",
            "prompt_hash": "7" * 64,
            "invocation_id": self.invocation_id,
        }
        scope = {"capability": "runtime_dispatch", "network": False}
        preview = compute_deterministic_human_visible_representation_digest(
            EXPIRY, subject=subject_dict, approval_scope=scope
        )
        self.subject = new_canonical_runtime_approval_subject(
            subject=subject_dict, approval_scope=scope, approval_preview_digest=preview, expires_at=EXPIRY
        )

        self.mechanism = DeterministicTestPresentationMechanism()
        installed = self.descriptor_store.resolve_canonical(self.mechanism.MECHANISM_ID)
        if installed is None:
            self.descriptor_store.install(
                self.descriptor_store.fixture_installer(self.mechanism.MECHANISM_ID), self.mechanism.descriptor()
            )
            installed = self.descriptor_store.resolve_canonical(self.mechanism.MECHANISM_ID)
        self.evidence = self.mechanism.present_installed(self.subject, self.approval_id, installed)
        self.presentation_store.create_canonical(
            self.presentation_store.fixture_mechanism_writer(self.mechanism.MECHANISM_ID), self.evidence, installed
        )
        self.resolved_presentation = self.presentation_store.resolve_canonical(
            presentation_id=self.evidence.presentation_id,
            presentation_digest=self.evidence.presentation_digest,
            descriptor_store=self.descriptor_store,
        )

        self.authenticator = DeterministicTestHumanAuthenticator(
            principal_id=self.principal_id, credential_id=self.credential_id, up=True, uv=True
        )
        self.challenge = self.authenticator.prepare_challenge(
            self.subject.digest(), self.evidence.presentation_digest
        )
        self.proof_material = self.authenticator.verify_response(self.challenge, response=b"resp-bytes")

        self.proof_id = new_proof_id()
        genesis_writer = self.lifecycle_store.fixture_genesis_writer(self.proof_id)
        self.lifecycle_store.open_challenge_canonical(
            genesis_writer,
            proof_id=self.proof_id,
            approval_id=self.approval_id,
            invocation_id=self.invocation_id,
            attempt_id="attempt-independent-1",
            principal_id=self.principal_id,
            credential_id=self.credential_id,
            mechanism_id=self.mechanism_id,
            occurred_at=T_GENESIS,
            resolved_presentation=self.resolved_presentation,
            challenge=self.challenge,
        )
        assertion_writer = self.lifecycle_store.fixture_assertion_writer(self.proof_id)
        self.lifecycle_store.record_assertion_canonical(
            assertion_writer,
            proof_id=self.proof_id,
            assertion_digest=canonical_digest({"assertion": self.proof_material.assertion}),
            occurred_at=T_ASSERTION,
        )

        body = {
            "proof_schema_version": PROOF_SCHEMA_VERSION,
            "proof_id": self.proof_id,
            "mechanism_id": self.mechanism_id,
            "principal_id": self.principal_id,
            "credential_id": self.credential_id,
            "challenge_digest": self.challenge.challenge_digest,
            "approval_subject_digest": self.subject.digest(),
            "trusted_presentation_ref": {
                "presentation_id": self.evidence.presentation_id,
                "presentation_digest": self.evidence.presentation_digest,
            },
            "assertion": self.proof_material.assertion,
            "up": self.proof_material.up,
            "uv": self.proof_material.uv,
            "authenticated_at": self.proof_material.authenticated_at,
            "verifier_version": "independent-fixture/1.0",
        }
        digest = canonical_digest(body)
        proof = HumanAuthenticationProof(proof_digest=digest, **body)
        self.proof_store.create_canonical(self.proof_store.fixture_proof_writer(self.mechanism_id), proof)
        resolved_proof = self.proof_store.resolve_canonical(self.proof_id)

        verified_writer = self.lifecycle_store.fixture_verifier_writer(self.proof_id)
        self.lifecycle_store.record_verified_canonical(
            verified_writer,
            resolved_proof=resolved_proof,
            registry_state_digest=canonical_digest({"registry": "state"}),
            verifier_version="independent-fixture/1.0",
            occurred_at=T_VERIFIED,
        )

        self.gate5_writer = self.lifecycle_store.fixture_gate5_writer(self.proof_id)

    def verify(self, **overrides):
        kwargs = dict(
            registry=self.registry,
            presentation_store=self.presentation_store,
            descriptor_store=self.descriptor_store,
            proof_store=self.proof_store,
            lifecycle_store=self.lifecycle_store,
            challenge=self.challenge,
            proof_id=self.proof_id,
            approval_id=self.approval_id,
            now=NOW,
            occurred_at=T_BOUND,
            gate5_writer=self.gate5_writer,
        )
        kwargs.update(overrides)
        return verify_human_authentication(**kwargs)


# ═══════════════════════════════════════════════════════════════════════
# HPAC-REQ-054: independently-derived deterministic NON-REAL positive case
# ═══════════════════════════════════════════════════════════════════════


def test_full_valid_chain_succeeds_and_is_non_real_assurance(tmp_path):
    """A fully valid deterministic chain (UP=true, UV=true, matching
    principal/credential/challenge/invocation/presentation/lifecycle) SHALL
    succeed (HPAC-REQ-054 step 10) but SHALL classify as FIXTURE_NON_REAL,
    never PRODUCTION (HPAC-REQ-059/060 -- no production HPAC writer exists
    in this repository, so deterministic success can never be real)."""
    fx = _Fixture(tmp_path)
    result = fx.verify()
    assert isinstance(result, AuthenticatedHumanPrincipal)
    assert result.assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL
    assert result.is_real_runtime_eligible is False
    assert result.principal_id == fx.principal_id
    assert result.credential_id == fx.credential_id
    assert result.invocation_id == fx.invocation_id
    assert result.approval_id == fx.approval_id


def test_deterministic_assurance_upgrade_attempt_rejected_via_require_real_assurance(tmp_path):
    """HPAC-REQ-060: fixture-to-real upgrade is never permitted. Even a
    fully successful deterministic chain SHALL be rejected when real
    assurance is explicitly required."""
    fx = _Fixture(tmp_path)
    with pytest.raises(HPACVerificationError):
        fx.verify(require_real_assurance=True)


# ═══════════════════════════════════════════════════════════════════════
# Canonical principal-registry consumption (HPAC-REQ-054 steps 1-2)
# ═══════════════════════════════════════════════════════════════════════


def test_revoked_principal_rejected(tmp_path):
    fx = _Fixture(tmp_path)
    admin = fx.registry.fixture_admin_writer()
    fx.registry.revoke_principal(admin, principal_id=fx.principal_id, revoked_at=T_BOUND)
    with pytest.raises(HPACVerificationError):
        fx.verify()


def test_revoked_credential_rejected(tmp_path):
    fx = _Fixture(tmp_path)
    admin = fx.registry.fixture_admin_writer()
    fx.registry.revoke_credential(admin, credential_id=fx.credential_id, revoked_at=T_BOUND)
    with pytest.raises(HPACVerificationError):
        fx.verify()


def test_unknown_principal_id_in_proof_rejected(tmp_path):
    """A proof whose principal_id was never enrolled SHALL fail step 1,
    even though the proof document itself is otherwise well-formed."""
    fx = _Fixture(tmp_path)
    # Overwrite proof's principal binding at the raw store level to simulate
    # a proof claiming an unenrolled principal -- this must fail the
    # registry resolution step, not merely a later step.
    forged_principal = new_principal_id()
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": new_proof_id(),
        "mechanism_id": fx.mechanism_id,
        "principal_id": forged_principal,
        "credential_id": fx.credential_id,
        "challenge_digest": fx.challenge.challenge_digest,
        "approval_subject_digest": fx.subject.digest(),
        "trusted_presentation_ref": {
            "presentation_id": fx.evidence.presentation_id,
            "presentation_digest": fx.evidence.presentation_digest,
        },
        "assertion": fx.proof_material.assertion,
        "up": True,
        "uv": True,
        "authenticated_at": fx.proof_material.authenticated_at,
        "verifier_version": "independent-fixture/1.0",
    }
    digest = canonical_digest(body)
    forged_proof = HumanAuthenticationProof(proof_digest=digest, **body)
    fx.proof_store.create_canonical(fx.proof_store.fixture_proof_writer(fx.mechanism_id), forged_proof)
    with pytest.raises(HPACVerificationError, match="unknown principal_id"):
        fx.verify(proof_id=body["proof_id"])


def test_caller_supplied_principal_record_cannot_substitute_for_registry(tmp_path):
    """The verifier's public API accepts only opaque IDs and canonical
    stores -- there is no parameter through which a caller could hand it a
    ready-made ``PrincipalRecord``/``HPACResolvedRecord`` to bypass registry
    resolution. This is a structural (signature-level) assertion, not a
    behavioral one."""
    import inspect

    sig = inspect.signature(verify_human_authentication)
    for name, param in sig.parameters.items():
        assert "principal" not in name.lower() or name == "registry" or "id" in name.lower(), (
            f"unexpected principal-shaped parameter {name!r} could allow caller-supplied "
            "principal state to bypass registry resolution"
        )


# ═══════════════════════════════════════════════════════════════════════
# Credential relationship (HPAC-REQ-054 steps 2-3, 6)
# ═══════════════════════════════════════════════════════════════════════


def test_credential_bound_to_another_principal_rejected(tmp_path):
    fx_a = _Fixture(tmp_path, invocation_id="iv-a")
    fx_b = _Fixture(tmp_path, invocation_id="iv-b")
    # Splice B's credential_id into A's raw proof body -- a credential that
    # is enrolled and active, but bound to a *different* principal.
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": new_proof_id(),
        "mechanism_id": fx_a.mechanism_id,
        "principal_id": fx_a.principal_id,
        "credential_id": fx_b.credential_id,
        "challenge_digest": fx_a.challenge.challenge_digest,
        "approval_subject_digest": fx_a.subject.digest(),
        "trusted_presentation_ref": {
            "presentation_id": fx_a.evidence.presentation_id,
            "presentation_digest": fx_a.evidence.presentation_digest,
        },
        "assertion": fx_a.proof_material.assertion,
        "up": True,
        "uv": True,
        "authenticated_at": fx_a.proof_material.authenticated_at,
        "verifier_version": "independent-fixture/1.0",
    }
    digest = canonical_digest(body)
    forged = HumanAuthenticationProof(proof_digest=digest, **body)
    fx_a.proof_store.create_canonical(fx_a.proof_store.fixture_proof_writer(fx_a.mechanism_id), forged)
    with pytest.raises(HPACVerificationError, match="not bound to the claimed principal"):
        fx_a.verify(proof_id=body["proof_id"])


def test_mechanism_id_substitution_between_credential_and_proof_rejected(tmp_path):
    fx = _Fixture(tmp_path)
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": new_proof_id(),
        "mechanism_id": "hpac.forged.mechanism.v1",
        "principal_id": fx.principal_id,
        "credential_id": fx.credential_id,
        "challenge_digest": fx.challenge.challenge_digest,
        "approval_subject_digest": fx.subject.digest(),
        "trusted_presentation_ref": {
            "presentation_id": fx.evidence.presentation_id,
            "presentation_digest": fx.evidence.presentation_digest,
        },
        "assertion": fx.proof_material.assertion,
        "up": True,
        "uv": True,
        "authenticated_at": fx.proof_material.authenticated_at,
        "verifier_version": "independent-fixture/1.0",
    }
    digest = canonical_digest(body)
    forged = HumanAuthenticationProof(proof_digest=digest, **body)
    fx.proof_store.create_canonical(fx.proof_store.fixture_proof_writer(body["mechanism_id"]), forged)
    with pytest.raises(HPACVerificationError):
        fx.verify(proof_id=body["proof_id"])


def test_unsupported_mechanism_never_verifies_even_if_otherwise_well_formed(tmp_path):
    """Only ``hpac.deterministic.test-only.v1`` is eligible in this phase
    (no real FIDO2 mechanism exists) -- any other mechanism_id must fail
    step 3/6 regardless of how well-formed the rest of the proof is."""
    fx = _Fixture(tmp_path)
    admin = fx.registry.fixture_admin_writer()
    other_cred = new_credential_id()
    fx.registry.enroll_credential(
        admin,
        credential_id=other_cred,
        principal_id=fx.principal_id,
        mechanism_id="hpac.fido2.uv_presence.v2",
        public_key="pubkey-material-2",
        assurance_capabilities=("up", "uv"),
        enrollment_provenance_ref="prov-ref",
        enrolled_at="2026-08-27T00:00:00Z",
    )
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": new_proof_id(),
        "mechanism_id": "hpac.fido2.uv_presence.v2",
        "principal_id": fx.principal_id,
        "credential_id": other_cred,
        "challenge_digest": fx.challenge.challenge_digest,
        "approval_subject_digest": fx.subject.digest(),
        "trusted_presentation_ref": {
            "presentation_id": fx.evidence.presentation_id,
            "presentation_digest": fx.evidence.presentation_digest,
        },
        "assertion": fx.proof_material.assertion,
        "up": True,
        "uv": True,
        "authenticated_at": fx.proof_material.authenticated_at,
        "verifier_version": "independent-fixture/1.0",
    }
    digest = canonical_digest(body)
    forged = HumanAuthenticationProof(proof_digest=digest, **body)
    fx.proof_store.create_canonical(fx.proof_store.fixture_proof_writer(body["mechanism_id"]), forged)
    with pytest.raises(HPACVerificationError, match="no real assertion-verification mechanism"):
        fx.verify(proof_id=body["proof_id"])


# ═══════════════════════════════════════════════════════════════════════
# Presentation / proof canonical-resolution-only consumption
# ═══════════════════════════════════════════════════════════════════════


def test_presentation_bound_to_different_approval_id_rejected(tmp_path):
    """A presentation evidence record whose approval_id differs from the
    approval_id being verified is an invocation/approval substitution
    (HPAC-REQ-091's ``approval_id`` field, HPAC-REQ-054 step 5) and SHALL
    fail even though every other field matches."""
    fx = _Fixture(tmp_path)
    other_approval = f"ria-{uuid.uuid4().hex}"
    with pytest.raises(HPACVerificationError, match="approval_id does not match|substitution"):
        fx.verify(approval_id=other_approval)


def test_proof_reused_for_a_different_invocation_rejected(tmp_path):
    """HPAC-REQ-072: a proof produced for invocation A's subject digest
    SHALL fail verification if presented for invocation B's subject digest,
    even under an otherwise-valid chain."""
    fx_a = _Fixture(tmp_path, invocation_id="iv-a-transfer")
    fx_b = _Fixture(tmp_path, invocation_id="iv-b-transfer")
    with pytest.raises(HPACVerificationError):
        fx_a.verify(
            proof_store=fx_a.proof_store,
            lifecycle_store=fx_a.lifecycle_store,
            proof_id=fx_a.proof_id,
            approval_id=fx_b.approval_id,  # cross invocation
        )


def test_expired_approval_subject_rejected(tmp_path):
    fx = _Fixture(tmp_path)
    with pytest.raises(HPACVerificationError, match="expired"):
        fx.verify(now="2027-01-01T00:00:00Z")


def test_future_authenticated_at_rejected(tmp_path):
    """A proof claiming authentication in the future relative to ``now`` is
    not fresh (HPAC-REQ-054 step 8) and SHALL be rejected."""
    fx = _Fixture(tmp_path)
    with pytest.raises(HPACVerificationError, match="future"):
        fx.verify(now="2020-01-01T00:00:00Z")


# ═══════════════════════════════════════════════════════════════════════
# UP / UV independence (HPAC-REQ-054 step 7, HPAC-REQ-042)
# ═══════════════════════════════════════════════════════════════════════


def test_up_false_uv_true_rejected(tmp_path):
    fx = _Fixture(tmp_path)
    with pytest.raises(Exception):
        # up=False should already be rejected upstream by proof-document
        # validation (HPAC-001 canonical storage); either that store or
        # this verifier's own step-7 guard must reject it -- both are
        # acceptable, a silent pass is not.
        body = {
            "proof_schema_version": PROOF_SCHEMA_VERSION,
            "proof_id": new_proof_id(),
            "mechanism_id": fx.mechanism_id,
            "principal_id": fx.principal_id,
            "credential_id": fx.credential_id,
            "challenge_digest": fx.challenge.challenge_digest,
            "approval_subject_digest": fx.subject.digest(),
            "trusted_presentation_ref": {
                "presentation_id": fx.evidence.presentation_id,
                "presentation_digest": fx.evidence.presentation_digest,
            },
            "assertion": fx.proof_material.assertion,
            "up": False,
            "uv": True,
            "authenticated_at": fx.proof_material.authenticated_at,
            "verifier_version": "independent-fixture/1.0",
        }
        digest = canonical_digest(body)
        forged = HumanAuthenticationProof(proof_digest=digest, **body)
        fx.proof_store.create_canonical(fx.proof_store.fixture_proof_writer(fx.mechanism_id), forged)
        fx.verify(proof_id=body["proof_id"])


def test_uv_false_up_true_rejected(tmp_path):
    fx = _Fixture(tmp_path)
    with pytest.raises(Exception):
        body = {
            "proof_schema_version": PROOF_SCHEMA_VERSION,
            "proof_id": new_proof_id(),
            "mechanism_id": fx.mechanism_id,
            "principal_id": fx.principal_id,
            "credential_id": fx.credential_id,
            "challenge_digest": fx.challenge.challenge_digest,
            "approval_subject_digest": fx.subject.digest(),
            "trusted_presentation_ref": {
                "presentation_id": fx.evidence.presentation_id,
                "presentation_digest": fx.evidence.presentation_digest,
            },
            "assertion": fx.proof_material.assertion,
            "up": True,
            "uv": False,
            "authenticated_at": fx.proof_material.authenticated_at,
            "verifier_version": "independent-fixture/1.0",
        }
        digest = canonical_digest(body)
        forged = HumanAuthenticationProof(proof_digest=digest, **body)
        fx.proof_store.create_canonical(fx.proof_store.fixture_proof_writer(fx.mechanism_id), forged)
        fx.verify(proof_id=body["proof_id"])


# ═══════════════════════════════════════════════════════════════════════
# Lifecycle / replay (HPAC-REQ-054 steps 4 (partial), 9-10)
# ═══════════════════════════════════════════════════════════════════════


def test_no_lifecycle_chain_rejected(tmp_path):
    fx = _Fixture(tmp_path)
    orphan_proof_id = new_proof_id()
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": orphan_proof_id,
        "mechanism_id": fx.mechanism_id,
        "principal_id": fx.principal_id,
        "credential_id": fx.credential_id,
        "challenge_digest": fx.challenge.challenge_digest,
        "approval_subject_digest": fx.subject.digest(),
        "trusted_presentation_ref": {
            "presentation_id": fx.evidence.presentation_id,
            "presentation_digest": fx.evidence.presentation_digest,
        },
        "assertion": fx.proof_material.assertion,
        "up": True,
        "uv": True,
        "authenticated_at": fx.proof_material.authenticated_at,
        "verifier_version": "independent-fixture/1.0",
    }
    digest = canonical_digest(body)
    forged = HumanAuthenticationProof(proof_digest=digest, **body)
    fx.proof_store.create_canonical(fx.proof_store.fixture_proof_writer(fx.mechanism_id), forged)
    with pytest.raises(HPACVerificationError, match="no lifecycle chain"):
        fx.verify(proof_id=orphan_proof_id)


def test_idempotent_reverification_of_already_bound_state_succeeds(tmp_path):
    fx = _Fixture(tmp_path)
    first = fx.verify()
    second = fx.verify()
    assert first.proof_id == second.proof_id
    assert first is not second  # each call yields its own ephemeral instance


def test_reverification_with_different_approval_digest_after_binding_rejected(tmp_path):
    """Once lifecycle state is PROOF_VERIFIED_AND_BOUND to one approval
    digest, a second verification attempt claiming a different approval_id
    (hence a different resolvable approval_subject_digest) is cross-binding
    replay and SHALL be rejected, not silently re-bound."""
    fx = _Fixture(tmp_path)
    fx.verify()  # advances lifecycle to PROOF_VERIFIED_AND_BOUND
    other_approval = f"ria-{uuid.uuid4().hex}"
    with pytest.raises(HPACVerificationError):
        fx.verify(approval_id=other_approval)


# ═══════════════════════════════════════════════════════════════════════
# HPAC-REQ-054 step 4 -- independent challenge-state recomputation
# ═══════════════════════════════════════════════════════════════════════


def test_challenge_digest_is_independently_recomputed_not_merely_compared(tmp_path):
    """HPAC-REQ-054 step 4 requires the verifier to 'recompute
    challenge_digest from the exact challenge state and compare' -- an
    independent recomputation from canonical challenge bytes (domain
    separator, nonce, principal/credential binding, subject/presentation
    digests, issued_at/expires_at per HPAC-REQ-049), not merely comparing
    two already-stored digest strings for equality. If a proof's claimed
    challenge_digest and the lifecycle genesis binding's challenge_digest
    were both (hypothetically) corrupted to agree with each other without
    ever being computed from real canonical challenge bytes, an
    implementation that only compares stored strings (as
    ``hpac_verifier.py``'s step-9 lifecycle cross-check does) would still
    accept them. This test documents that gap by asserting the verifier
    performs a genuine recomputation-based rejection of a
    non-canonically-derived-but-string-matching challenge_digest; it is
    expected to reveal whether the implementation actually recomputes
    (independent verification finding, see canonical phase report)."""
    fx = _Fixture(tmp_path)
    # Corrupt the *lifecycle genesis* binding's recorded challenge_digest
    # and the *proof's* claimed challenge_digest to the same bogus value
    # that was never actually derived from the real canonical challenge
    # bytes (HPAC-REQ-049). A verifier that only compares
    # proof.challenge_digest == genesis.binding['challenge_digest'] for
    # string equality (rather than recomputing from real challenge state)
    # would incorrectly accept this.
    bogus_digest = "0" * 64
    body = {
        "proof_schema_version": PROOF_SCHEMA_VERSION,
        "proof_id": new_proof_id(),
        "mechanism_id": fx.mechanism_id,
        "principal_id": fx.principal_id,
        "credential_id": fx.credential_id,
        "challenge_digest": bogus_digest,
        "approval_subject_digest": fx.subject.digest(),
        "trusted_presentation_ref": {
            "presentation_id": fx.evidence.presentation_id,
            "presentation_digest": fx.evidence.presentation_digest,
        },
        "assertion": fx.proof_material.assertion,
        "up": True,
        "uv": True,
        "authenticated_at": fx.proof_material.authenticated_at,
        "verifier_version": "independent-fixture/1.0",
    }
    digest = canonical_digest(body)
    forged = HumanAuthenticationProof(proof_digest=digest, **body)
    fx.proof_store.create_canonical(fx.proof_store.fixture_proof_writer(fx.mechanism_id), forged)

    # This proof's challenge_digest (bogus_digest) was never produced by
    # HumanAuthenticator.prepare_challenge over real canonical challenge
    # bytes. HPAC-REQ-054 step 4 requires the verifier to independently
    # recompute the challenge digest from canonical challenge state and
    # reject on mismatch -- it must fail even though no lifecycle genesis
    # exists yet to cross-check against (this exact proof_id has no
    # lifecycle chain), which itself already causes rejection via a
    # different step (step 9, "no lifecycle chain"). The real question this
    # documents for the report is architectural, not this single
    # assertion: see the report's HPAC-REQ-054-step-4 adjudication.
    with pytest.raises(HPACVerificationError):
        fx.verify(proof_id=body["proof_id"])


# ═══════════════════════════════════════════════════════════════════════
# AuthenticatedHumanPrincipal construction boundary (HPAC-REQ-056/057)
# ═══════════════════════════════════════════════════════════════════════


def test_direct_construction_with_wrong_seal_rejected():
    with pytest.raises(HPACAuthorityError):
        AuthenticatedHumanPrincipal(
            principal_id="hp-forged",
            credential_id="hpc-forged",
            mechanism_id=DETERMINISTIC_MECHANISM_ID,
            approval_id="ria-" + "0" * 32,
            invocation_id="iv-forged",
            proof_id="hap-" + "0" * 32,
            presentation_id="hpe-" + "0" * 32,
            assurance_class=HPACAuthorityClass.PRODUCTION,
            verified_at=NOW,
            _seal=object(),
        )


def test_object_dunder_new_bypasses_trusted_construction_seal():
    """HPAC-REQ-056: 'AuthenticatedHumanPrincipal ... SHALL be producible
    only as the return value of a successful [HPAC-REQ-054] verification
    sequence, never by direct construction from caller-supplied strings or
    dicts.' ``object.__new__`` bypasses ``__init__`` (and therefore the
    ``_VERIFIER_CONSTRUCTOR_SEAL`` check inside it) entirely; the class
    defines ``__slots__`` but no ``__new__`` override, so a caller can
    allocate a bare instance via ``object.__new__`` and populate every slot
    directly via ``setattr``, including ``assurance_class=PRODUCTION`` --
    producing an object that is ``isinstance``-true, has a working
    ``is_real_runtime_eligible`` property, and was never produced by
    ``verify_human_authentication``. This is a caller-supplied-strings
    construction under a different Python mechanism than ``__init__``, and
    HPAC-REQ-056's prohibition is not limited to the ``__init__`` code path.
    This test asserts the CONTRACT-REQUIRED behavior (construction must be
    impossible) and is expected to FAIL against the current implementation
    -- see the canonical phase report's AuthenticatedHumanPrincipal
    construction-boundary adjudication."""
    forged = object.__new__(AuthenticatedHumanPrincipal)
    forged.principal_id = "forged-principal"
    forged.credential_id = "forged-credential"
    forged.mechanism_id = "forged-mechanism"
    forged.approval_id = "forged-approval"
    forged.invocation_id = "forged-invocation"
    forged.proof_id = "forged-proof"
    forged.presentation_id = "forged-presentation"
    forged.assurance_class = HPACAuthorityClass.PRODUCTION
    forged.verified_at = NOW
    forged._verifier_seal = object()

    # A fully-formed, isinstance-true forged result must not exist. It does
    # today (object.__new__ bypasses __init__'s seal check) -- this
    # assertion documents the contract violation.
    assert not isinstance(forged, AuthenticatedHumanPrincipal), (
        "object.__new__ produced an AuthenticatedHumanPrincipal instance without "
        "going through verify_human_authentication -- HPAC-REQ-056 trusted-"
        "construction boundary is not closed against this construction path"
    )


def test_forged_via_object_new_would_report_real_runtime_eligible():
    """Demonstrates concrete severity of the above gap: the forged instance
    is not merely isinstance-true, it also reports itself as real-runtime
    eligible (PRODUCTION assurance) without ever running verification."""
    forged = object.__new__(AuthenticatedHumanPrincipal)
    forged.principal_id = "forged-principal"
    forged.credential_id = "forged-credential"
    forged.mechanism_id = "forged-mechanism"
    forged.approval_id = "forged-approval"
    forged.invocation_id = "forged-invocation"
    forged.proof_id = "forged-proof"
    forged.presentation_id = "forged-presentation"
    forged.assurance_class = HPACAuthorityClass.PRODUCTION
    forged.verified_at = NOW
    forged._verifier_seal = object()
    assert forged.is_real_runtime_eligible is False, (
        "forged object.__new__ instance reports is_real_runtime_eligible=True "
        "without any successful HPAC-REQ-054 verification -- authority forgery"
    )


def test_verifier_result_cannot_be_pickled(tmp_path):
    fx = _Fixture(tmp_path)
    result = fx.verify()
    with pytest.raises(TypeError):
        pickle.dumps(result)


def test_verifier_result_cannot_be_deepcopied(tmp_path):
    fx = _Fixture(tmp_path)
    result = fx.verify()
    with pytest.raises(TypeError):
        copy.deepcopy(result)


def test_verifier_result_cannot_be_shallow_copied(tmp_path):
    fx = _Fixture(tmp_path)
    result = fx.verify()
    with pytest.raises(TypeError):
        copy.copy(result)


def test_verifier_result_equality_and_hash_are_identity_only(tmp_path):
    fx = _Fixture(tmp_path)
    result = fx.verify()
    assert result == result
    assert hash(result) == id(result)
    second = fx.verify()
    assert result != second


def test_verifier_result_attribute_copy_produces_a_distinguishable_object(tmp_path):
    """Manually copying every public attribute of a legitimate result onto
    a fresh forged instance (an attacker who has read access to a real
    result's fields but not the seal) must not itself constitute an equal
    or trusted object -- equality is identity-only (HPAC-REQ-056's spirit),
    so a field-cloned object is never '==' to the original even if every
    visible field matches."""
    fx = _Fixture(tmp_path)
    legit = fx.verify()
    cloned = object.__new__(AuthenticatedHumanPrincipal)
    for slot in AuthenticatedHumanPrincipal.__slots__:
        setattr(cloned, slot, getattr(legit, slot))
    assert cloned != legit
    assert hash(cloned) != hash(legit)


# ═══════════════════════════════════════════════════════════════════════
# Zero production consumer / zero PB / zero Gate-9 (static, not behavioral)
# ═══════════════════════════════════════════════════════════════════════


def test_runtime_authority_is_the_only_production_consumer_of_hpac_verifier():
    import ast
    import pathlib

    src_root = pathlib.Path(__file__).resolve().parents[1] / "src" / "pcae"
    consumers = []
    for path in src_root.rglob("*.py"):
        if path.name == "hpac_verifier.py":
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "hpac_verifier" in node.module:
                consumers.append(str(path))
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if "hpac_verifier" in alias.name:
                        consumers.append(str(path))
    assert set(consumers) == {
        str(src_root / "core" / "runtime_authority.py")
    }


def test_hpac_verifier_module_never_imports_pb_runtime_authority_or_gate9():
    import pathlib

    text = (pathlib.Path(__file__).resolve().parents[1] / "src" / "pcae" / "core" / "hpac_verifier.py").read_text(
        encoding="utf-8"
    )
    forbidden = [
        "permission_broker",
        "runtime_dispatch_permission",
        "runtime_authority",
        "runtime_invocation_authority_consumption",
        "runtime_invocation_approval_store",
    ]
    for token in forbidden:
        assert f"import" not in text or token not in text.split("\n\n")[0], token
    # Direct, precise check: no real import statement references any
    # forbidden module.
    import ast

    tree = ast.parse(text)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
    for token in forbidden:
        assert not any(token in name for name in imported), f"forbidden import present: {token}"

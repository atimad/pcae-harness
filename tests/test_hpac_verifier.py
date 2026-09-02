"""Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.5 — mechanism-neutral HPAC verifier
and principal-registry consumption boundary tests.

Exercises HPAC-REQ-054's fail-closed verification sequence end to end
against the real (fixture-authority) foundation stores, plus the
``...1R.4`` planning document's §30 threat matrix and §31 test plan:
canonical-resolution-only inputs, anti-forgery/anti-transfer of the
verifier's own result type, invocation binding, assurance classification,
and zero production-consumer boundaries (PB, runtime authority, Gate 9).
"""

from __future__ import annotations

import pathlib
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
    HumanAuthenticationProofTrustError,
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

EXPIRY = "2026-08-28T12:00:00Z"
NOW = "2026-08-28T00:03:00Z"
OCCURRED_AT_GENESIS = "2026-08-28T00:00:00Z"
OCCURRED_AT_ASSERTION = "2026-08-28T00:01:00Z"
OCCURRED_AT_VERIFIED = "2026-08-28T00:01:30Z"
OCCURRED_AT_BOUND = "2026-08-28T00:02:00Z"


class _Rig:
    """Everything needed to call verify_human_authentication, positioned
    with the lifecycle chain already at PROOF_VERIFIED (the state a real
    upstream proof-verification pipeline would leave it in before Gate 5's
    verifier call)."""

    def __init__(self, tmp_path, **kw):
        self.tmp_path = tmp_path
        self.authority = HPACStoreAuthority.fixture(tmp_path / "root")
        self.registry = HumanPrincipalRegistryStore(self.authority)
        self.descriptor_store = PresentationMechanismDescriptorStore(self.authority)
        self.presentation_store = TrustedApprovalPresentationStore(self.authority)
        self.proof_store = HumanAuthenticationProofStore(self.authority)
        self.lifecycle_store = HPACLifecycleStore(self.authority)

        self.principal_id = kw.get("principal_id") or new_principal_id()
        self.credential_id = kw.get("credential_id") or new_credential_id()
        self.mechanism_id = kw.get("mechanism_id", DETERMINISTIC_MECHANISM_ID)
        self.approval_id = kw.get("approval_id") or f"ria-{uuid.uuid4().hex}"
        self.invocation_id = kw.get("invocation_id", "iv-1")

        admin = self.registry.fixture_admin_writer()
        self.registry.enroll_principal(
            admin,
            principal_id=self.principal_id,
            enrollment_provenance_ref="prov-ref",
            enrolled_at="2026-08-27T00:00:00Z",
        )
        if not kw.get("skip_credential_enroll", False):
            self.registry.enroll_credential(
                admin,
                credential_id=self.credential_id,
                principal_id=kw.get("credential_principal_id", self.principal_id),
                mechanism_id=kw.get("credential_mechanism_id", self.mechanism_id),
                public_key=kw.get("public_key", "pubkey-material"),
                assurance_capabilities=("up", "uv"),
                enrollment_provenance_ref="prov-ref",
                enrolled_at="2026-08-27T00:00:00Z",
            )

        subject_dict = {
            "repository_identity": "repo-1r5",
            "task_id": "task-1r5",
            "runtime_target_id": "target-1r5",
            "prompt_hash": "5" * 64,
            "invocation_id": self.invocation_id,
        }
        scope = {"capability": "runtime_dispatch", "network": False}
        expires_at = kw.get("expires_at", EXPIRY)
        preview = compute_deterministic_human_visible_representation_digest(
            expires_at, subject=subject_dict, approval_scope=scope
        )
        self.subject = new_canonical_runtime_approval_subject(
            subject=subject_dict, approval_scope=scope, approval_preview_digest=preview, expires_at=expires_at
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
            principal_id=self.principal_id,
            credential_id=self.credential_id,
            up=kw.get("up", True),
            uv=kw.get("uv", True),
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
            attempt_id="attempt-1",
            principal_id=self.principal_id,
            credential_id=self.credential_id,
            mechanism_id=self.mechanism_id,
            occurred_at=OCCURRED_AT_GENESIS,
            resolved_presentation=self.resolved_presentation,
            challenge=self.challenge,
        )
        assertion_writer = self.lifecycle_store.fixture_assertion_writer(self.proof_id)
        self.lifecycle_store.record_assertion_canonical(
            assertion_writer,
            proof_id=self.proof_id,
            assertion_digest=canonical_digest({"assertion": self.proof_material.assertion}),
            occurred_at=OCCURRED_AT_ASSERTION,
        )

        if not kw.get("skip_proof_creation", False):
            proof_mechanism_id = kw.get("proof_mechanism_id", self.mechanism_id)
            body = {
                "proof_schema_version": PROOF_SCHEMA_VERSION,
                "proof_id": self.proof_id,
                "mechanism_id": proof_mechanism_id,
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
                "verifier_version": "test-fixture/1.0",
            }
            digest = canonical_digest(body)
            proof = HumanAuthenticationProof(proof_digest=digest, **body)
            self.proof_store.create_canonical(
                self.proof_store.fixture_proof_writer(proof_mechanism_id), proof
            )
            resolved_proof = self.proof_store.resolve_canonical(self.proof_id)

            if not kw.get("skip_record_verified", False):
                verified_writer = self.lifecycle_store.fixture_verifier_writer(self.proof_id)
                self.lifecycle_store.record_verified_canonical(
                    verified_writer,
                    resolved_proof=resolved_proof,
                    registry_state_digest=canonical_digest({"registry": "state"}),
                    verifier_version="test-fixture/1.0",
                    occurred_at=OCCURRED_AT_VERIFIED,
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
            occurred_at=OCCURRED_AT_BOUND,
            gate5_writer=self.gate5_writer,
        )
        kwargs.update(overrides)
        return verify_human_authentication(**kwargs)


# ═══════════════════════════════════════════════════════════════════════
# Happy path / assurance classification
# ═══════════════════════════════════════════════════════════════════════


def test_canonical_valid_deterministic_verification_succeeds_at_non_real_assurance(tmp_path):
    rig = _Rig(tmp_path)
    result = rig.verify()
    assert isinstance(result, AuthenticatedHumanPrincipal)
    assert result.principal_id == rig.principal_id
    assert result.credential_id == rig.credential_id
    assert result.approval_id == rig.approval_id
    assert result.invocation_id == rig.invocation_id
    assert result.assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL
    assert result.is_real_runtime_eligible is False


def test_deterministic_success_remains_non_real_even_with_up_and_uv_true(tmp_path):
    rig = _Rig(tmp_path, up=True, uv=True)
    result = rig.verify()
    assert result.assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL


def test_idempotent_same_binding_reverification_succeeds(tmp_path):
    rig = _Rig(tmp_path)
    first = rig.verify()
    second = rig.verify()
    assert first is not second
    assert first.proof_id == second.proof_id
    assert second.assurance_class is HPACAuthorityClass.FIXTURE_NON_REAL


# ═══════════════════════════════════════════════════════════════════════
# Canonical-resolution-only inputs (§14/§9 of the planning doc)
# ═══════════════════════════════════════════════════════════════════════


def test_unknown_proof_id_rejected(tmp_path):
    rig = _Rig(tmp_path)
    with pytest.raises(HPACVerificationError, match="unknown proof_id"):
        rig.verify(proof_id="hap-" + "0" * 32)


def test_malformed_proof_id_rejected(tmp_path):
    rig = _Rig(tmp_path)
    with pytest.raises(HumanAuthenticationProofTrustError):
        rig.verify(proof_id="not-a-proof-id")


def test_revoked_principal_rejected(tmp_path):
    rig = _Rig(tmp_path)
    admin = rig.registry.fixture_admin_writer()
    rig.registry.revoke_principal(admin, principal_id=rig.principal_id, revoked_at="2026-08-28T00:02:30Z")
    with pytest.raises(HPACVerificationError, match="not active"):
        rig.verify()


def test_revoked_credential_rejected(tmp_path):
    rig = _Rig(tmp_path)
    admin = rig.registry.fixture_admin_writer()
    rig.registry.revoke_credential(admin, credential_id=rig.credential_id, revoked_at="2026-08-28T00:02:30Z")
    with pytest.raises(HPACVerificationError, match="not active"):
        rig.verify()


def test_credential_not_bound_to_claimed_principal_rejected(tmp_path):
    other_principal = new_principal_id()
    rig = _Rig(tmp_path)
    admin = rig.registry.fixture_admin_writer()
    rig.registry.enroll_principal(
        admin, principal_id=other_principal, enrollment_provenance_ref="prov-ref", enrolled_at="2026-08-27T00:00:00Z"
    )
    # Directly corrupt: resolve the credential and confirm the verifier's
    # own principal-binding check is what fires, not merely a KeyError --
    # simulate by asking the verifier to trust proof.principal_id against a
    # credential enrolled under a different principal.
    resolved = rig.registry.resolve_canonical_credential(rig.credential_id)
    assert resolved.record.principal_id == rig.principal_id
    # There is no public path to make a canonical credential silently
    # belong to a different principal than it was enrolled under; the
    # verifier's _resolve_credential check exists for exactly this
    # invariant. Exercise it directly against the resolved data shape.
    from pcae.core.hpac_verifier import _resolve_credential

    with pytest.raises(HPACVerificationError, match="not bound to the claimed principal"):
        _resolve_credential(rig.registry, rig.credential_id, expected_principal_id=other_principal)


def test_mechanism_substitution_rejected(tmp_path):
    """A credential enrolled for a different mechanism than the proof
    claims must be rejected before any assurance is granted."""

    rig = _Rig(tmp_path, credential_mechanism_id="hpac.other-mechanism.v1")
    with pytest.raises(HPACVerificationError, match="mechanism substitution|does not match proof mechanism_id"):
        rig.verify()


def test_unsupported_mechanism_id_rejected(tmp_path):
    rig = _Rig(
        tmp_path,
        mechanism_id="hpac.unsupported.v9",
        proof_mechanism_id="hpac.unsupported.v9",
    )
    with pytest.raises(HPACVerificationError, match="no real assertion-verification mechanism"):
        rig.verify()


# ═══════════════════════════════════════════════════════════════════════
# Presentation / invocation / approval binding
# ═══════════════════════════════════════════════════════════════════════


def test_approval_id_substitution_rejected(tmp_path):
    rig_a = _Rig(tmp_path, invocation_id="iv-a")
    rig_b = _Rig(tmp_path, invocation_id="iv-b")
    with pytest.raises(HPACVerificationError, match="approval_id does not match|invocation/approval substitution"):
        rig_a.verify(approval_id=rig_b.approval_id)


def test_valid_result_for_invocation_a_cannot_be_reused_for_invocation_b(tmp_path):
    rig_a = _Rig(tmp_path, invocation_id="iv-a2")
    rig_b = _Rig(tmp_path, invocation_id="iv-b2")
    result_a = rig_a.verify()
    assert result_a.invocation_id == "iv-a2"
    with pytest.raises(HPACVerificationError):
        rig_a.verify(proof_id=rig_b.proof_id)


def test_expired_approval_subject_rejected(tmp_path):
    rig = _Rig(tmp_path, expires_at="2026-08-28T00:00:30Z")
    with pytest.raises(HPACVerificationError, match="expired"):
        rig.verify(now="2026-08-28T00:05:00Z")


def test_missing_presentation_rejected(tmp_path):
    from pcae.core.approval_presentation import ApprovalPresentationTrustError

    rig = _Rig(tmp_path)
    other_authority = HPACStoreAuthority.fixture(tmp_path / "other-root")
    other_presentation_store = TrustedApprovalPresentationStore(other_authority)
    with pytest.raises((ApprovalPresentationTrustError, HPACAuthorityError)):
        rig.verify(presentation_store=other_presentation_store)


# ═══════════════════════════════════════════════════════════════════════
# UP/UV (defense in depth -- canonical storage already forecloses a
# False UP/UV proof from being resolved at all, so this exercises the
# verifier's own redundant internal check directly)
# ═══════════════════════════════════════════════════════════════════════


def test_up_false_rejected_internal_guard(tmp_path):
    from dataclasses import replace

    from pcae.core.hpac_verifier import _check_up_uv

    rig = _Rig(tmp_path)
    resolved = rig.proof_store.resolve_canonical(rig.proof_id)
    forged_up_false = replace(resolved.record, up=False)
    with pytest.raises(HPACVerificationError, match="up=False"):
        _check_up_uv(forged_up_false)


def test_uv_false_rejected_internal_guard(tmp_path):
    from dataclasses import replace

    from pcae.core.hpac_verifier import _check_up_uv

    rig = _Rig(tmp_path)
    resolved = rig.proof_store.resolve_canonical(rig.proof_id)
    forged_uv_false = replace(resolved.record, uv=False)
    with pytest.raises(HPACVerificationError, match="uv=False"):
        _check_up_uv(forged_uv_false)


# ═══════════════════════════════════════════════════════════════════════
# Lifecycle state / replay
# ═══════════════════════════════════════════════════════════════════════


def test_lifecycle_not_yet_verified_state_rejected(tmp_path):
    rig = _Rig(tmp_path, skip_record_verified=True)
    with pytest.raises(HPACVerificationError, match="not in a verifiable-and-bindable state"):
        rig.verify()


def test_no_canonical_proof_rejected(tmp_path):
    rig = _Rig(tmp_path, skip_proof_creation=True)
    with pytest.raises(HPACVerificationError, match="unknown proof_id"):
        # No canonical proof exists at all in this configuration.
        rig.verify()


def test_bind_gate5_is_actually_invoked_and_persists(tmp_path):
    rig = _Rig(tmp_path)
    from pcae.core.hpac_lifecycle import STATE_PROOF_VERIFIED_AND_BOUND

    before = rig.lifecycle_store.resolve_chain(rig.proof_id)
    assert before[-1].state != STATE_PROOF_VERIFIED_AND_BOUND
    rig.verify()
    after = rig.lifecycle_store.resolve_chain(rig.proof_id)
    assert after[-1].state == STATE_PROOF_VERIFIED_AND_BOUND


# ═══════════════════════════════════════════════════════════════════════
# require_real_assurance (fixture-to-real upgrade rejection)
# ═══════════════════════════════════════════════════════════════════════


def test_fixture_to_real_upgrade_rejected(tmp_path):
    rig = _Rig(tmp_path)
    with pytest.raises(HPACVerificationError, match="fixture-to-real upgrade"):
        rig.verify(require_real_assurance=True)


# ═══════════════════════════════════════════════════════════════════════
# Anti-forgery / anti-transfer of AuthenticatedHumanPrincipal
# ═══════════════════════════════════════════════════════════════════════


def test_caller_constructed_verifier_result_rejected():
    with pytest.raises(HPACAuthorityError):
        AuthenticatedHumanPrincipal(
            principal_id="hp-forged",
            credential_id="hpc-forged",
            mechanism_id=DETERMINISTIC_MECHANISM_ID,
            approval_id="ria-" + "0" * 32,
            invocation_id="iv-forged",
            proof_id="hap-" + "0" * 32,
            presentation_id="hpe-" + "0" * 32,
            assurance_class=HPACAuthorityClass.FIXTURE_NON_REAL,
            verified_at=NOW,
            _seal=object(),
        )


def test_verifier_result_cannot_be_pickled(tmp_path):
    rig = _Rig(tmp_path)
    result = rig.verify()
    with pytest.raises(TypeError):
        pickle.dumps(result)


def test_copied_verifier_result_is_not_equal_to_a_fresh_one(tmp_path):
    rig = _Rig(tmp_path)
    result = rig.verify()
    import copy

    with pytest.raises(TypeError):
        copy.deepcopy(result)


def test_verifier_result_equality_is_identity_only(tmp_path):
    rig = _Rig(tmp_path)
    result = rig.verify()
    assert result == result
    # A second call produces a structurally-similar but distinct instance;
    # equality must not be shape-based, only identity-based.
    result2 = rig.verify()
    assert result != result2


# ═══════════════════════════════════════════════════════════════════════
# Zero external effect / zero production consumers (§31/§32)
# ═══════════════════════════════════════════════════════════════════════

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src" / "pcae"


def _all_python_sources():
    return [p for p in _SRC_ROOT.rglob("*.py") if "__pycache__" not in p.parts]


def _imported_module_names(path: pathlib.Path) -> set[str]:
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_hpac_verifier_module_does_not_import_pb_or_runtime_authority_modules():
    imports = _imported_module_names(_SRC_ROOT / "core" / "hpac_verifier.py")
    forbidden_suffixes = (
        "runtime_dispatch_permission",
        "permission_broker",
        "runtime_authority",
        "runtime_invocation_authority_consumption",
    )
    for module_name in imports:
        for suffix in forbidden_suffixes:
            assert not module_name.endswith(suffix), f"hpac_verifier.py must not import {module_name}"


def test_runtime_authority_is_the_only_production_consumer_of_hpac_verifier_module():
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 reconciliation: this guard
    # is about production *consumers* (modules that `import` hpac_verifier),
    # not about any file that merely mentions the name in prose. The merged
    # RHAMP `.1R.30` bundle adds `hpac_rhamp_assertion_verify.py` and
    # `human_authenticator_fido2.py`, both of which name `hpac_verifier` only
    # in their module docstrings (the real dependency runs the other way:
    # hpac_verifier lazily imports `verify_real_fido2_assertion`). The scan
    # is tightened from a substring match to a real-import match so those
    # docstring mentions do not register as consumers; the authorized
    # consumer set is unchanged. No `def test_` renamed/removed.
    consumers = []
    for path in _all_python_sources():
        if path.name == "hpac_verifier.py":
            continue
        imports = _imported_module_names(path)
        if any(name.endswith("hpac_verifier") or name == "pcae.core.hpac_verifier" for name in imports):
            consumers.append(str(path.relative_to(_REPO_ROOT)))
    # Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.10 added the authorized Gate-5
    # approval-validation coordinator, the "future Gate 5" this module was
    # designed to serve (.1R.9 §16.1). It consumes only the public
    # provenance predicate `is_verifier_authenticated_principal`.
    assert sorted(consumers) == [
        "src/pcae/core/runtime_authority.py",
        "src/pcae/core/runtime_dispatch_gate5.py",
    ]


def test_gate9_consumption_store_is_never_referenced_by_the_verifier():
    verifier_source = (_SRC_ROOT / "core" / "hpac_verifier.py").read_text(encoding="utf-8")
    assert "RuntimeInvocationAuthorityConsumption" not in verifier_source

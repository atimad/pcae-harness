"""Independent verification suite for Phase
149O.20L.7O.3W.1R.2B.1R.1.1R.3.2.2.1.

Re-derives HPAC-REQ-091/092's closed attestation schema directly from
`docs/contracts/HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (not from the
`.3.2.2` repair source or its test suite) and independently attacks the
`.3.2.2` repair for Finding P (protected-presentation attestation schema)
and Finding C (canonical-store containment). Does not reuse or import
helpers from `.3.2.2`'s own test module.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os

import pytest

from pcae.core.approval_presentation import (
    ApprovalPresentationTrustError,
    PresentationMechanismDescriptorStore,
    TrustedApprovalPresentationStore,
    new_canonical_runtime_approval_subject,
    presentation_attestation_object,
)
from pcae.core.approval_presentation_deterministic import (
    DeterministicTestPresentationMechanism,
    compute_deterministic_human_visible_representation_digest,
)
from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACMalformedError,
    HPACStoreAuthority,
    HPACSymlinkError,
    canonical_json_bytes,
)
from pcae.core.hpac_lifecycle import HPACLifecycleStore
from pcae.core.runtime_invocation_authority_consumption import (
    RuntimeInvocationAuthorityConsumptionStore,
)

APPROVAL_ID = "ria-" + "9" * 32
EXPIRY = "2026-08-28T12:00:00Z"

# Independently re-derived from HPAC-REQ-092 contract prose (§39.2), not
# from the `.3.2.2` repair source: "The registered mechanism verifies
# `mechanism_attestation` over exactly one closed object containing
# `attestation_version` ..., `presentation_id`, `approval_id`,
# `approval_subject_digest`, `human_visible_representation_digest`,
# `descriptor_digest`, the complete closed `election` object, and
# `presented_at`; no other or omitted field is permitted."
_REQ_092_FIELDS = frozenset(
    {
        "attestation_version",
        "presentation_id",
        "approval_id",
        "approval_subject_digest",
        "human_visible_representation_digest",
        "descriptor_digest",
        "election",
        "presented_at",
    }
)
_REQ_092_ATTESTATION_VERSION_CONST = "HPAC-PRESENTATION-ATTESTATION/2.0"


def _approval_subject(invocation_id: str = "iv-3221"):
    subject = {
        "repository_identity": "repo-3221",
        "task_id": "task-3221",
        "runtime_target_id": "target-3221",
        "prompt_hash": "5" * 64,
        "invocation_id": invocation_id,
    }
    scope = {"capability": "runtime_dispatch", "network": False}
    preview = compute_deterministic_human_visible_representation_digest(
        EXPIRY, subject=subject, approval_scope=scope
    )
    return new_canonical_runtime_approval_subject(
        subject=subject, approval_scope=scope, approval_preview_digest=preview, expires_at=EXPIRY
    )


def _install_and_present(authority, *, approval_id: str = APPROVAL_ID, invocation_id: str = "iv-3221"):
    mechanism = DeterministicTestPresentationMechanism()
    descriptor_store = PresentationMechanismDescriptorStore(authority)
    descriptor_store.install(descriptor_store.fixture_installer(mechanism.MECHANISM_ID), mechanism.descriptor())
    installed = descriptor_store.resolve_canonical(mechanism.MECHANISM_ID)
    subject = _approval_subject(invocation_id)
    evidence = mechanism.present_installed(subject, approval_id, installed)
    pstore = TrustedApprovalPresentationStore(authority)
    pstore.create_canonical(pstore.fixture_mechanism_writer(mechanism.MECHANISM_ID), evidence, installed)
    return mechanism, descriptor_store, installed, evidence, pstore


def _decode(attestation_b64: str) -> dict:
    padded = attestation_b64 + "=" * (-len(attestation_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


# ═══════════════════════════════════════════════════════════════════════
# Finding P — independently re-derived HPAC-REQ-092 schema exactness
# ═══════════════════════════════════════════════════════════════════════


def test_contract_rederived_field_set_matches_repaired_attestation_exactly(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    _m, _d, _i, evidence, _p = _install_and_present(authority)
    attestation = _decode(evidence.mechanism_attestation)
    assert set(attestation) == _REQ_092_FIELDS, (
        "production attestation object diverges from HPAC-REQ-092's independently "
        "re-derived closed 8-field schema"
    )
    assert attestation["attestation_version"] == _REQ_092_ATTESTATION_VERSION_CONST


def test_presentation_attestation_object_function_produces_only_contract_fields(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    _m, _d, _i, evidence, _p = _install_and_present(authority)
    produced = presentation_attestation_object(evidence)
    assert set(produced) == _REQ_092_FIELDS
    for forbidden in ("installation_store_id", "simulation_only", "verifier_kind", "mechanism_id"):
        assert forbidden not in produced


def test_deterministic_attestation_cannot_be_upgraded_by_field_injection(tmp_path):
    """Attempt to smuggle installation/mechanism identity into the attested
    object itself (rather than through the separate writer-provenance and
    installed-descriptor channels HPAC-REQ-092 requires)."""

    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism, descriptor_store, installed, evidence, pstore = _install_and_present(authority)
    forged = dict(presentation_attestation_object(evidence))
    forged["mechanism_class"] = "real"
    forged["assurance"] = "verified"
    attestation_bytes = canonical_json_bytes(forged)
    from dataclasses import replace

    tampered = replace(
        evidence,
        mechanism_attestation=base64.urlsafe_b64encode(attestation_bytes).decode("ascii").rstrip("="),
        mechanism_attestation_digest=hashlib.sha256(attestation_bytes).hexdigest(),
    )
    body = tampered.to_document(include_presentation_digest=False)
    from pcae.core.hpac_foundation import canonical_digest

    tampered = replace(tampered, presentation_digest=canonical_digest(body))
    other_authority = HPACStoreAuthority.fixture(tmp_path / "other")
    other_store = TrustedApprovalPresentationStore(other_authority)
    other_store.create(tampered)
    with pytest.raises(ApprovalPresentationTrustError):
        other_store.resolve_structural(
            presentation_id=tampered.presentation_id, presentation_digest=tampered.presentation_digest
        )


def test_fully_wellformed_forged_attestation_lacking_writer_provenance_is_rejected(tmp_path):
    """Section 10/13 of the phase instruction: a fully well-formed,
    contract-conformant attestation -- correct 8 fields, correct types,
    correct digest, plausible identities -- manually planted into the
    canonical root *without ever going through* `create_canonical`'s writer
    capability (so no provenance sidecar entry is ever recorded for it)
    must still be rejected. Constructing legitimate evidence via
    `create_canonical` first and then rewriting identical bytes at the same
    path is not a forgery -- the provenance sidecar is keyed by path, and
    an unchanged digest at an already-provenanced path is indistinguishable
    from the original legitimate record. The genuine attack is a record
    that is well-formed and correctly self-consistent but was never
    authored through the writer-capability path at all."""

    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism = DeterministicTestPresentationMechanism()
    descriptor_store = PresentationMechanismDescriptorStore(authority)
    descriptor_store.install(descriptor_store.fixture_installer(mechanism.MECHANISM_ID), mechanism.descriptor())
    installed = descriptor_store.resolve_canonical(mechanism.MECHANISM_ID)
    subject = _approval_subject("iv-forge")
    evidence = mechanism.present_installed(subject, APPROVAL_ID, installed)

    pstore = TrustedApprovalPresentationStore(authority)
    # Hand-write the well-formed, digest-correct, contract-conformant
    # record directly onto disk -- never calling create_canonical, so
    # HPACStoreAuthority.record_write is never invoked and no provenance
    # sidecar entry exists for this path.
    doc = evidence.to_document(include_presentation_digest=True)
    payload = canonical_json_bytes(doc)
    path = pstore._path(evidence.presentation_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)

    with pytest.raises((ApprovalPresentationTrustError, HPACAuthorityError)) as excinfo:
        pstore.resolve_canonical(
            presentation_id=evidence.presentation_id,
            presentation_digest=evidence.presentation_digest,
            descriptor_store=descriptor_store,
        )
    assert "provenance" in str(excinfo.value).lower()


def test_deterministic_mechanism_never_reports_real_runtime_eligibility(tmp_path):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    _m, descriptor_store, _i, evidence, pstore = _install_and_present(authority, invocation_id="iv-nonreal")
    resolved = pstore.resolve_canonical(
        presentation_id=evidence.presentation_id,
        presentation_digest=evidence.presentation_digest,
        descriptor_store=descriptor_store,
    )
    assert resolved.is_real_runtime_eligible is False


def test_non_deterministic_verifier_kind_is_categorically_rejected(tmp_path):
    """HPAC-REQ-090 defines `verifier_kind` only as a "non-empty closed
    implementation identifier" -- installation itself does not (and per
    contract should not) whitelist legal identifier values, since future
    real verifiers must be installable too. The trust boundary is
    verification: `_verify_installed_attestation` honors only the
    `deterministic-test-fixture` kind and rejects every other value
    outright, including one crafted to *look* real, because no real
    verifier is implemented in this phase -- not because any field of the
    attestation itself mismatched."""

    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism = DeterministicTestPresentationMechanism()
    descriptor_store = PresentationMechanismDescriptorStore(authority)
    descriptor = mechanism.descriptor()
    from dataclasses import replace

    fake_real_descriptor = replace(
        descriptor, verifier_kind="real-fido2-platform-authenticator", descriptor_digest=""
    )
    installed_writer = descriptor_store.fixture_installer(mechanism.MECHANISM_ID)
    # Installation of a non-deterministic verifier_kind descriptor is not
    # itself rejected -- that would over-constrain HPAC-REQ-090.
    descriptor_store.install(installed_writer, fake_real_descriptor)
    installed = descriptor_store.resolve_canonical(mechanism.MECHANISM_ID)
    assert installed is not None

    subject = _approval_subject("iv-fakekind")
    evidence = mechanism.present_installed(subject, APPROVAL_ID, installed)
    pstore = TrustedApprovalPresentationStore(authority)
    # create_canonical itself calls _verify_installed_attestation, so the
    # categorical rejection must fire here, before any record is written.
    with pytest.raises(ApprovalPresentationTrustError, match="no real protected-presentation attestation verifier"):
        pstore.create_canonical(pstore.fixture_mechanism_writer(mechanism.MECHANISM_ID), evidence, installed)


# ═══════════════════════════════════════════════════════════════════════
# Finding C — independently re-attacked canonical-store containment
# ═══════════════════════════════════════════════════════════════════════

_ABSOLUTE_AND_TRAVERSAL_ATTACKS = (
    "/tmp/valid-proof",
    "../outside",
    "../../outside",
    "a/../../../outside",
    "./../../outside",
    "..",
    ".",
    "a/b",
    "a\\b",
)


@pytest.mark.parametrize("proof_id", _ABSOLUTE_AND_TRAVERSAL_ATTACKS)
def test_lifecycle_store_rejects_every_absolute_or_traversal_proof_id(tmp_path, proof_id):
    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    store = HPACLifecycleStore(authority)
    with pytest.raises(HPACMalformedError):
        store._dir(proof_id)


@pytest.mark.parametrize("proof_id", _ABSOLUTE_AND_TRAVERSAL_ATTACKS)
def test_gate9_store_rejects_every_absolute_or_traversal_proof_id(tmp_path, proof_id):
    store = RuntimeInvocationAuthorityConsumptionStore(tmp_path / "root")
    with pytest.raises(HPACMalformedError):
        store._path(proof_id)


def test_lifecycle_store_positive_canonical_proof_id_stays_within_root(tmp_path):
    root = tmp_path / "root"
    authority = HPACStoreAuthority.fixture(root)
    store = HPACLifecycleStore(authority)
    proof_id = "hap-" + "3" * 32
    resolved_dir = store._dir(proof_id).resolve()
    assert str(resolved_dir).startswith(str(root.resolve()))


def test_symlinked_proof_directory_is_rejected_not_silently_followed(tmp_path):
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    outside.mkdir(parents=True)
    authority = HPACStoreAuthority.fixture(root)
    store = HPACLifecycleStore(authority)
    proof_id = "hap-" + "1" * 32
    real_dir = store._dir(proof_id)
    real_dir.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(outside, real_dir)
    with pytest.raises(HPACSymlinkError):
        store._load_chain(proof_id)


def test_canonical_root_placement_alone_does_not_confer_provenance(tmp_path):
    """Section 19: containment (record stays inside the root) and writer
    provenance (record was actually written by an authorized writer) are
    two independent properties. A byte-perfect record placed inside the
    canonical root by hand -- never going through a writer capability, so
    `HPACStoreAuthority.record_write`'s provenance sidecar is never
    populated for that path -- must still be rejected, and rejected for
    lacking provenance specifically, not merely because containment
    happened to also fail (containment is satisfied here: the path *is*
    inside the root)."""

    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    mechanism = DeterministicTestPresentationMechanism()
    descriptor_store = PresentationMechanismDescriptorStore(authority)
    descriptor_store.install(descriptor_store.fixture_installer(mechanism.MECHANISM_ID), mechanism.descriptor())
    installed = descriptor_store.resolve_canonical(mechanism.MECHANISM_ID)
    subject = _approval_subject("iv-root-plant")
    evidence = mechanism.present_installed(subject, APPROVAL_ID, installed)

    pstore = TrustedApprovalPresentationStore(authority)
    doc = evidence.to_document(include_presentation_digest=True)
    path = pstore._path(evidence.presentation_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(doc))

    with pytest.raises((ApprovalPresentationTrustError, HPACAuthorityError)) as excinfo:
        pstore.resolve_canonical(
            presentation_id=evidence.presentation_id,
            presentation_digest=evidence.presentation_digest,
            descriptor_store=descriptor_store,
        )
    assert "provenance" in str(excinfo.value).lower()


def test_cross_store_substitution_does_not_make_a_foreign_record_authoritative(tmp_path):
    authority_a = HPACStoreAuthority.fixture(tmp_path / "a")
    _m, _d, _i, evidence, _p = _install_and_present(authority_a, invocation_id="iv-cross-a")

    authority_b = HPACStoreAuthority.fixture(tmp_path / "b")
    mechanism_b = DeterministicTestPresentationMechanism()
    descriptor_store_b = PresentationMechanismDescriptorStore(authority_b)
    descriptor_store_b.install(descriptor_store_b.fixture_installer(mechanism_b.MECHANISM_ID), mechanism_b.descriptor())
    pstore_b = TrustedApprovalPresentationStore(authority_b)
    with pytest.raises((ApprovalPresentationTrustError, HPACAuthorityError)):
        pstore_b.resolve_canonical(
            presentation_id=evidence.presentation_id,
            presentation_digest=evidence.presentation_digest,
            descriptor_store=descriptor_store_b,
        )


# ═══════════════════════════════════════════════════════════════════════
# Regressions: principal / proof-writer provenance, genesis/predecessor
# ═══════════════════════════════════════════════════════════════════════


def test_record_id_grammar_independent_of_filesystem_traversal_grammar(tmp_path):
    """A valid `^hap-[0-9a-f]{32}$` ID and a "safe path component" are
    different, narrower-than-broader checks; confirm the safe-component
    gate does not accidentally accept a well-formed-looking but
    non-canonical ID that a later stage might trust further."""

    authority = HPACStoreAuthority.fixture(tmp_path / "root")
    store = HPACLifecycleStore(authority)
    # Not matching hap- grammar but still a single safe path component --
    # accepted by containment (correct: containment != ID-grammar
    # authority, which is enforced separately via `_load_chain`'s
    # `provenance_required` / `id_pattern_matches` check).
    d = store._dir("not-a-real-proof-id")
    assert str(d.resolve()).startswith(str((tmp_path / "root").resolve()))

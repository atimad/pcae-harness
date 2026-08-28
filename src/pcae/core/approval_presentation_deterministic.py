"""
`DeterministicTestPresentationMechanism` — HPAC-001 plan §13's
simulation-only `ProtectedApprovalPresentationMechanism` fixture.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.3. Exercises the full B-3 conjunction
adversarially: parameterizable to produce a presentation whose
`human_visible_representation_digest` deliberately does not match
`canonical_subject.approval_preview_digest` (display/subject mismatch),
an `election.occurred_at` before `presented_at` (ordering violation), a
`mechanism_attestation_digest` that does not match its own attestation
object (forged attestation), or no `election` at all (blind-touch
equivalent, modeled as an empty election id).

DETERMINISTIC PRESENTATION FIXTURE != REAL TRUSTED HUMAN PRESENTATION.
`SIMULATION_ONLY` and a fixed, non-real `mechanism_id` enforce this
structurally, mirroring `human_authenticator_deterministic.py`'s
identical discipline.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from typing import Final

from pcae.core.approval_presentation import (
    CanonicalRuntimeApprovalSubject,
    PRESENTATION_EVIDENCE_SCHEMA_VERSION,
    PresentationMechanismDescriptor,
    TrustedApprovalPresentationEvidence,
    new_election_event_id,
    new_presentation_id,
    presentation_attestation_object,
)
from pcae.core.hpac_foundation import (
    HPACAuthorityError,
    HPACResolvedRecord,
    canonical_digest,
    canonical_json_bytes,
)

#: Never equal to a real installed mechanism id.
DETERMINISTIC_PRESENTATION_MECHANISM_ID: Final[str] = "hpac.deterministic.presentation.test-only.v1"


def compute_deterministic_human_visible_representation_digest(
    expires_at: str,
    *,
    subject: dict | None = None,
    approval_scope: dict | None = None,
) -> str:
    """Test-fixture helper: the exact `human_visible_representation_digest`
    `DeterministicTestPresentationMechanism.present()` will compute for a
    given `expires_at`, so a caller can pre-populate
    `CanonicalRuntimeApprovalSubject.approval_preview_digest` with the
    matching value and obtain a structurally non-faulty presentation
    (HPAC-REQ-092's digest-equality requirement). Test-only; production
    code has no analogous shortcut because a real mechanism's rendering
    is not predictable in advance."""

    if subject is not None:
        return canonical_digest(_canonical_fixture_facts(subject, approval_scope or {}, expires_at))
    human_visible_facts = {
        "repository_identity": "deterministic-fixture-repo",
        "repository_display": "deterministic-fixture-repo (fixture)",
        "task_id": "deterministic-fixture-task",
        "task_display": "deterministic-fixture-task (fixture)",
        "runtime_target_id": "deterministic-fixture-target",
        "runtime_target_display": "deterministic-fixture-target (fixture)",
        "operation_effect_scope_display": "deterministic-fixture-scope (fixture)",
        "prompt_hash": canonical_digest({"prompt": "fixture"}),
        "prompt_instruction_display": "deterministic-fixture-prompt (fixture)",
        "invocation_id": "deterministic-fixture-invocation",
        "invocation_display": "deterministic-fixture-invocation (fixture)",
        "expires_at": expires_at,
        "one_shot_notice": True,
    }
    return canonical_digest(human_visible_facts)


def _canonical_fixture_facts(subject: dict, approval_scope: dict, expires_at: str) -> dict:
    repository_identity = subject.get("repository_identity")
    task_id = subject.get("task_id")
    runtime_target_id = subject.get("runtime_target_id")
    prompt_hash = subject.get("prompt_hash")
    invocation_id = subject.get("invocation_id")
    scope_display = json.dumps(approval_scope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "repository_identity": repository_identity,
        "repository_display": f"{repository_identity} (deterministic fixture)",
        "task_id": task_id,
        "task_display": f"{task_id} (deterministic fixture)",
        "runtime_target_id": runtime_target_id,
        "runtime_target_display": f"{runtime_target_id} (deterministic fixture)",
        "operation_effect_scope_display": scope_display,
        "prompt_hash": prompt_hash,
        "prompt_instruction_display": f"prompt {str(prompt_hash)[:12]} (deterministic fixture)",
        "invocation_id": invocation_id,
        "invocation_display": f"{invocation_id} (deterministic fixture)",
        "expires_at": expires_at,
        "one_shot_notice": True,
    }


@dataclass
class DeterministicTestPresentationMechanism:
    """Simulation-only `ProtectedApprovalPresentationMechanism`.

    `fault` selects which adversarial defect (if any) this instance's
    `present()` call injects: `None` (a structurally valid evidence
    object), `"digest_mismatch"`, `"ordering_violation"`,
    `"forged_attestation"`, or `"blind_touch"`.
    """

    fault: str | None = None

    SIMULATION_ONLY: Final[bool] = field(default=True, init=False, repr=False)
    MECHANISM_ID: Final[str] = field(default=DETERMINISTIC_PRESENTATION_MECHANISM_ID, init=False, repr=False)

    def descriptor(self) -> PresentationMechanismDescriptor:
        return PresentationMechanismDescriptor(
            descriptor_schema_version="HPAC-PRESENTATION-MECHANISM/2.0",
            mechanism_id=DETERMINISTIC_PRESENTATION_MECHANISM_ID,
            descriptor_version="test-only-v1",
            verifier_kind="deterministic-test-fixture",
            verifier_configuration_digest=canonical_digest({"fixture": "deterministic"}),
            renderer_profile="deterministic-test-renderer.v1",
            protected_output=True,
            agent_substitution_resistant=True,
            canonical_subject_rendering=True,
            explicit_election_support=True,
            status="active",
        )

    def present(
        self, canonical_subject: CanonicalRuntimeApprovalSubject, approval_id: str
    ) -> TrustedApprovalPresentationEvidence:
        descriptor = self.descriptor()
        descriptor_digest = canonical_digest(descriptor.to_document(include_digest=False))
        sealed_descriptor = PresentationMechanismDescriptor(
            **{**descriptor.__dict__, "descriptor_digest": descriptor_digest}
        )
        return self._present(
            canonical_subject,
            approval_id,
            descriptor=sealed_descriptor,
            canonical_facts=False,
        )

    def present_installed(
        self,
        canonical_subject: CanonicalRuntimeApprovalSubject,
        approval_id: str,
        installed_descriptor: HPACResolvedRecord[PresentationMechanismDescriptor],
    ) -> TrustedApprovalPresentationEvidence:
        """Emit canonical fixture evidence bound to one installed descriptor.

        Even a successful result is permanently non-real because the installed
        descriptor resolution is required to carry ``FIXTURE_NON_REAL``.
        """

        descriptor = installed_descriptor.record
        if installed_descriptor.is_real_runtime_eligible:
            raise HPACAuthorityError("deterministic presentation cannot use production assurance")
        if descriptor.mechanism_id != DETERMINISTIC_PRESENTATION_MECHANISM_ID:
            raise HPACAuthorityError("deterministic presentation mechanism substitution")
        return self._present(
            canonical_subject,
            approval_id,
            descriptor=descriptor,
            canonical_facts=True,
        )

    def _present(
        self,
        canonical_subject: CanonicalRuntimeApprovalSubject,
        approval_id: str,
        *,
        descriptor: PresentationMechanismDescriptor,
        canonical_facts: bool,
    ) -> TrustedApprovalPresentationEvidence:
        presentation_id = new_presentation_id()
        approval_subject_digest = canonical_subject.digest()

        legacy_facts = {
            "repository_identity": "deterministic-fixture-repo",
            "repository_display": "deterministic-fixture-repo (fixture)",
            "task_id": "deterministic-fixture-task",
            "task_display": "deterministic-fixture-task (fixture)",
            "runtime_target_id": "deterministic-fixture-target",
            "runtime_target_display": "deterministic-fixture-target (fixture)",
            "operation_effect_scope_display": "deterministic-fixture-scope (fixture)",
            "prompt_hash": canonical_digest({"prompt": "fixture"}),
            "prompt_instruction_display": "deterministic-fixture-prompt (fixture)",
            "invocation_id": "deterministic-fixture-invocation",
            "invocation_display": "deterministic-fixture-invocation (fixture)",
            "expires_at": canonical_subject.expires_at,
            "one_shot_notice": True,
        }
        human_visible_facts = (
            _canonical_fixture_facts(
                canonical_subject.subject,
                canonical_subject.approval_scope,
                canonical_subject.expires_at,
            )
            if canonical_facts
            else legacy_facts
        )

        human_visible_representation_digest = canonical_digest(human_visible_facts)
        if self.fault == "digest_mismatch":
            # Deliberately diverge from canonical_subject.approval_preview_digest.
            human_visible_representation_digest = canonical_digest({"fixture": "deliberately-mismatched"})

        presented_at = "2026-08-28T00:02:00Z"
        occurred_at = "2026-08-28T00:02:01Z" if self.fault != "ordering_violation" else "2026-08-28T00:01:00Z"

        if self.fault == "blind_touch":
            election = {"event_id": "hpevt-" + "0" * 32, "action": "approve", "occurred_at": occurred_at}
        else:
            election = {"event_id": new_election_event_id(), "action": "approve", "occurred_at": occurred_at}

        mechanism_ref = {
            "mechanism_id": DETERMINISTIC_PRESENTATION_MECHANISM_ID,
            "descriptor_version": descriptor.descriptor_version,
            "descriptor_digest": descriptor.descriptor_digest,
        }

        unsigned_body = {
            "presentation_schema_version": PRESENTATION_EVIDENCE_SCHEMA_VERSION,
            "presentation_id": presentation_id,
            "approval_id": approval_id,
            "canonical_subject": canonical_subject.to_document(),
            "approval_subject_digest": approval_subject_digest,
            "mechanism_ref": mechanism_ref,
            "human_visible_facts": human_visible_facts,
            "human_visible_representation_digest": human_visible_representation_digest,
            "presented_at": presented_at,
            "election": election,
            "mechanism_attestation": "",
            "mechanism_attestation_digest": "",
        }
        unsigned_evidence = TrustedApprovalPresentationEvidence(
            presentation_digest="",
            **unsigned_body,
        )
        attestation_object = presentation_attestation_object(unsigned_evidence)
        attestation_bytes = canonical_json_bytes(attestation_object)
        mechanism_attestation = base64.urlsafe_b64encode(attestation_bytes).decode("ascii").rstrip("=")
        mechanism_attestation_digest = hashlib.sha256(attestation_bytes).hexdigest()
        if self.fault == "forged_attestation":
            mechanism_attestation_digest = "0" * 64

        body_without_digest = {
            **unsigned_body,
            "mechanism_attestation": mechanism_attestation,
            "mechanism_attestation_digest": mechanism_attestation_digest,
        }
        presentation_digest = canonical_digest(body_without_digest)

        return TrustedApprovalPresentationEvidence(
            presentation_digest=presentation_digest,
            **body_without_digest,
        )

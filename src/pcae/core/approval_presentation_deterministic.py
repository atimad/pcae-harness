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

from dataclasses import dataclass, field
from typing import Final

from pcae.core.approval_presentation import (
    CanonicalRuntimeApprovalSubject,
    PRESENTATION_ATTESTATION_VERSION,
    PRESENTATION_EVIDENCE_SCHEMA_VERSION,
    PresentationMechanismDescriptor,
    TrustedApprovalPresentationEvidence,
    new_election_event_id,
    new_presentation_id,
)
from pcae.core.hpac_foundation import canonical_digest

#: Never equal to a real installed mechanism id.
DETERMINISTIC_PRESENTATION_MECHANISM_ID: Final[str] = "hpac.deterministic.presentation.test-only.v1"


def compute_deterministic_human_visible_representation_digest(expires_at: str) -> str:
    """Test-fixture helper: the exact `human_visible_representation_digest`
    `DeterministicTestPresentationMechanism.present()` will compute for a
    given `expires_at`, so a caller can pre-populate
    `CanonicalRuntimeApprovalSubject.approval_preview_digest` with the
    matching value and obtain a structurally non-faulty presentation
    (HPAC-REQ-092's digest-equality requirement). Test-only; production
    code has no analogous shortcut because a real mechanism's rendering
    is not predictable in advance."""

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
        presentation_id = new_presentation_id()
        approval_subject_digest = canonical_subject.digest()

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
            "expires_at": canonical_subject.expires_at,
            "one_shot_notice": True,
        }

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
            "descriptor_version": "test-only-v1",
            "descriptor_digest": canonical_digest({"fixture": "descriptor"}),
        }

        attestation_object = {
            "attestation_version": PRESENTATION_ATTESTATION_VERSION,
            "presentation_id": presentation_id,
            "approval_id": approval_id,
            "approval_subject_digest": approval_subject_digest,
            "human_visible_representation_digest": human_visible_representation_digest,
            "descriptor_digest": mechanism_ref["descriptor_digest"],
            "election": election,
            "presented_at": presented_at,
        }
        mechanism_attestation_digest = canonical_digest(attestation_object)
        if self.fault == "forged_attestation":
            mechanism_attestation_digest = canonical_digest({"forged": True})

        body_without_digest = {
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
            "mechanism_attestation": "ZGV0ZXJtaW5pc3RpYy1maXh0dXJl",  # base64url, non-empty, non-real
            "mechanism_attestation_digest": mechanism_attestation_digest,
        }
        presentation_digest = canonical_digest(body_without_digest)

        return TrustedApprovalPresentationEvidence(
            presentation_digest=presentation_digest,
            **body_without_digest,
        )

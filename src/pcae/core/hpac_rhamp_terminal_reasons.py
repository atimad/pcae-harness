"""RHAMP-001 v1.0 §49 — the closed 41-value ``terminal_reason_code``
vocabulary for the real ``hpac.fido2.uv_presence.v2`` mechanism, the
credential registration / first-credential bootstrap ceremony, and the
protected-presentation resolution boundary.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.4 (merged RHAMP-REQ-156 ``.1R.30``
bundle). This module is a **pure vocabulary + deterministic-mapping**
helper: it recognises no OS state, reads no protected root, mints no
capability, imports nothing agent-reachable, and performs no I/O. Every
terminal failure of enrollment, bootstrap, authentication, presentation,
election, counter evaluation, or consumption maps **deterministically to
exactly one** of the 41 codes (RHAMP-REQ-129); free-form authority-decision
reason strings are prohibited (RHAMP-REQ-129 / HPAC-REQ-095 discipline).

RHAMP-001 v1.0 is **byte-unchanged** by this phase — the vocabulary here is
transcribed from RHAMP-001 §49.1, not authored. A future RHAMP-001 MINOR may
add a code (RHAMP-REQ-168); this module fails closed on an unknown code.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "TerminalReasonCode",
    "TERMINAL_REASON_CODES",
    "HUMAN_VISIBLE_CATEGORY",
    "RhampTerminalError",
    "require_terminal_reason_code",
]


class TerminalReasonCode(str, Enum):
    """RHAMP-001 v1.0 §49.1 — the exact closed set, in the frozen order.

    ``str`` mixin so a code compares/serialises as its literal token; the
    enum guarantees no 42nd value can be added without a source edit that a
    guard test detects.
    """

    BOOTSTRAP_AUTHORITY_UNPROVEN = "bootstrap_authority_unproven"                # 1
    ENROLLMENT_NOT_PROTECTED_ADMIN = "enrollment_not_protected_admin"            # 2
    ENROLLMENT_CEREMONY_EVIDENCE_INVALID = "enrollment_ceremony_evidence_invalid"  # 3
    ENROLLMENT_DUPLICATE_CREDENTIAL = "enrollment_duplicate_credential"          # 4
    ENROLLMENT_PRINCIPAL_INELIGIBLE = "enrollment_principal_ineligible"          # 5
    PRINCIPAL_NOT_FOUND = "principal_not_found"                                  # 6
    PRINCIPAL_NOT_ACTIVE = "principal_not_active"                                # 7
    CREDENTIAL_NOT_FOUND = "credential_not_found"                                # 8
    CREDENTIAL_NOT_ACTIVE = "credential_not_active"                              # 9
    CREDENTIAL_PRINCIPAL_MISMATCH = "credential_principal_mismatch"              # 10
    MECHANISM_UNKNOWN = "mechanism_unknown"                                      # 11
    MECHANISM_BELOW_ASSURANCE = "mechanism_below_assurance"                      # 12
    RP_ID_HASH_MISMATCH = "rp_id_hash_mismatch"                                  # 13
    CLIENT_DATA_CONTEXT_MISMATCH = "client_data_context_mismatch"                # 14
    CLIENT_DATA_HASH_MISMATCH = "client_data_hash_mismatch"                      # 15
    CHALLENGE_DIGEST_MISMATCH = "challenge_digest_mismatch"                      # 16
    CHALLENGE_EXPIRED = "challenge_expired"                                      # 17
    CHALLENGE_REPLAYED = "challenge_replayed"                                    # 18
    SUBJECT_DIGEST_MISMATCH = "subject_digest_mismatch"                          # 19
    PRESENTATION_UNRESOLVED = "presentation_unresolved"                          # 20
    PRESENTATION_DIGEST_MISMATCH = "presentation_digest_mismatch"                # 21
    PRESENTATION_ATTESTATION_INVALID = "presentation_attestation_invalid"        # 22
    HELPER_INTEGRITY_UNVERIFIED = "helper_integrity_unverified"                  # 23
    HELPER_RESPONSE_UNTRUSTED = "helper_response_untrusted"                      # 24
    ELECTION_MISSING = "election_missing"                                        # 25
    ELECTION_ORDERING_INVALID = "election_ordering_invalid"                      # 26
    APPROVAL_REJECTED_BY_HUMAN = "approval_rejected_by_human"                    # 27
    CEREMONY_CANCELLED = "ceremony_cancelled"                                    # 28
    CEREMONY_TIMED_OUT = "ceremony_timed_out"                                    # 29
    CEREMONY_SUPERSEDED = "ceremony_superseded"                                  # 30
    SIGNATURE_INVALID = "signature_invalid"                                      # 31
    USER_PRESENCE_MISSING = "user_presence_missing"                              # 32
    USER_VERIFICATION_MISSING = "user_verification_missing"                      # 33
    SIGNATURE_COUNTER_REGRESSION = "signature_counter_regression"                # 34
    PROOF_AGE_EXCEEDED = "proof_age_exceeded"                                    # 35
    AUTHORITY_GENERATION_STALE = "authority_generation_stale"                    # 36
    LIFECYCLE_FORK = "lifecycle_fork"                                            # 37
    LIFECYCLE_CROSS_BINDING = "lifecycle_cross_binding"                          # 38
    CONSUMPTION_REPLAY = "consumption_replay"                                    # 39
    PROTECTED_ROOT_INVALID = "protected_root_invalid"                            # 40
    INTERNAL_VERIFICATION_ERROR = "internal_verification_error"                  # 41


#: The exact ordered tuple of the 41 literal tokens (RHAMP-001 §49.1). A
#: guard test asserts ``len == 41`` and set-equality with RHAMP-001's table.
TERMINAL_REASON_CODES: tuple[str, ...] = tuple(code.value for code in TerminalReasonCode)
assert len(TERMINAL_REASON_CODES) == 41 and len(set(TERMINAL_REASON_CODES)) == 41

#: RHAMP-001 §49.1 "Human-visible category" column + §50 — five distinct
#: audit categories that SHALL NOT be conflated (RHAMP-REQ-131).
HUMAN_VISIBLE_CATEGORY: dict[str, str] = {
    TerminalReasonCode.BOOTSTRAP_AUTHORITY_UNPROVEN.value: "enrollment_error",
    TerminalReasonCode.ENROLLMENT_NOT_PROTECTED_ADMIN.value: "enrollment_error",
    TerminalReasonCode.ENROLLMENT_CEREMONY_EVIDENCE_INVALID.value: "enrollment_error",
    TerminalReasonCode.ENROLLMENT_DUPLICATE_CREDENTIAL.value: "enrollment_error",
    TerminalReasonCode.ENROLLMENT_PRINCIPAL_INELIGIBLE.value: "enrollment_error",
    TerminalReasonCode.PRINCIPAL_NOT_FOUND.value: "not_authenticated",
    TerminalReasonCode.PRINCIPAL_NOT_ACTIVE.value: "not_authenticated",
    TerminalReasonCode.CREDENTIAL_NOT_FOUND.value: "not_authenticated",
    TerminalReasonCode.CREDENTIAL_NOT_ACTIVE.value: "not_authenticated",
    TerminalReasonCode.CREDENTIAL_PRINCIPAL_MISMATCH.value: "not_authenticated",
    TerminalReasonCode.MECHANISM_UNKNOWN.value: "not_authenticated",
    TerminalReasonCode.MECHANISM_BELOW_ASSURANCE.value: "not_authenticated",
    TerminalReasonCode.RP_ID_HASH_MISMATCH.value: "not_authenticated",
    TerminalReasonCode.CLIENT_DATA_CONTEXT_MISMATCH.value: "not_authenticated",
    TerminalReasonCode.CLIENT_DATA_HASH_MISMATCH.value: "not_authenticated",
    TerminalReasonCode.CHALLENGE_DIGEST_MISMATCH.value: "not_authenticated",
    TerminalReasonCode.CHALLENGE_EXPIRED.value: "not_authenticated",
    TerminalReasonCode.CHALLENGE_REPLAYED.value: "not_authenticated",
    TerminalReasonCode.SUBJECT_DIGEST_MISMATCH.value: "presentation_integrity_error",
    TerminalReasonCode.PRESENTATION_UNRESOLVED.value: "presentation_integrity_error",
    TerminalReasonCode.PRESENTATION_DIGEST_MISMATCH.value: "presentation_integrity_error",
    TerminalReasonCode.PRESENTATION_ATTESTATION_INVALID.value: "presentation_integrity_error",
    TerminalReasonCode.HELPER_INTEGRITY_UNVERIFIED.value: "presentation_integrity_error",
    TerminalReasonCode.HELPER_RESPONSE_UNTRUSTED.value: "presentation_integrity_error",
    TerminalReasonCode.ELECTION_MISSING.value: "presentation_integrity_error",
    TerminalReasonCode.ELECTION_ORDERING_INVALID.value: "presentation_integrity_error",
    TerminalReasonCode.APPROVAL_REJECTED_BY_HUMAN.value: "approval_declined",
    TerminalReasonCode.CEREMONY_CANCELLED.value: "approval_declined",
    TerminalReasonCode.CEREMONY_TIMED_OUT.value: "approval_declined",
    TerminalReasonCode.CEREMONY_SUPERSEDED.value: "approval_declined",
    TerminalReasonCode.SIGNATURE_INVALID.value: "not_authenticated",
    TerminalReasonCode.USER_PRESENCE_MISSING.value: "not_authenticated",
    TerminalReasonCode.USER_VERIFICATION_MISSING.value: "not_authenticated",
    TerminalReasonCode.SIGNATURE_COUNTER_REGRESSION.value: "not_authenticated",
    TerminalReasonCode.PROOF_AGE_EXCEEDED.value: "authority_stale",
    TerminalReasonCode.AUTHORITY_GENERATION_STALE.value: "authority_stale",
    TerminalReasonCode.LIFECYCLE_FORK.value: "presentation_integrity_error",
    TerminalReasonCode.LIFECYCLE_CROSS_BINDING.value: "presentation_integrity_error",
    TerminalReasonCode.CONSUMPTION_REPLAY.value: "authority_stale",
    TerminalReasonCode.PROTECTED_ROOT_INVALID.value: "internal_error",
    TerminalReasonCode.INTERNAL_VERIFICATION_ERROR.value: "internal_error",
}
assert set(HUMAN_VISIBLE_CATEGORY) == set(TERMINAL_REASON_CODES)

#: RHAMP-001 §50 (RHAMP-REQ-131) — the five distinct audit categories.
_AUDIT_CATEGORIES = frozenset(
    {
        "not_authenticated",
        "presentation_integrity_error",
        "approval_declined",
        "authority_stale",
        "internal_error",
        # §49.1 uses the finer "enrollment_error" label for the
        # enrollment/bootstrap rows; §50's five are the *authority-outcome*
        # categories — an enrollment_error yields "no approval authority"
        # exactly as not_authenticated does, but is audited distinctly.
        "enrollment_error",
    }
)
assert set(HUMAN_VISIBLE_CATEGORY.values()) <= _AUDIT_CATEGORIES


class RhampTerminalError(Exception):
    """A terminal RHAMP-001 ceremony failure carrying exactly one closed
    ``terminal_reason_code`` (RHAMP-REQ-129). ``reason`` is a
    :class:`TerminalReasonCode`; ``detail`` is a non-authoritative
    diagnostic string (never itself a reason)."""

    def __init__(self, reason: "TerminalReasonCode | str", detail: str = "") -> None:
        code = require_terminal_reason_code(reason)
        super().__init__(f"{code.value}: {detail}" if detail else code.value)
        self.reason = code
        self.detail = detail

    @property
    def terminal_reason_code(self) -> str:
        return self.reason.value

    @property
    def human_visible_category(self) -> str:
        return HUMAN_VISIBLE_CATEGORY[self.reason.value]


def require_terminal_reason_code(value: "TerminalReasonCode | str") -> TerminalReasonCode:
    """Fail closed on any value outside the closed 41-code set."""

    if isinstance(value, TerminalReasonCode):
        return value
    if isinstance(value, str):
        try:
            return TerminalReasonCode(value)
        except ValueError:
            pass
    raise AssertionError(f"non-vocabulary terminal_reason_code: {value!r}")

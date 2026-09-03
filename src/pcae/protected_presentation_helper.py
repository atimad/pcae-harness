"""``pcae.protected_presentation_helper`` — the PCAE-owned, fixed
protected-presentation helper implementation (RHAMP-001 v1.0 §28–§35,
HPAC-PPA-001 v1.0 §7).

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.4R.1.

This is the process the trusted launcher mediator (:mod:`pcae.core.protected_presentation`)
executes — and the *only* party that renders the closed 13 ``human_visible_facts``,
neutralizes untrusted content, presents the explicit Approve / Reject controls,
observes the human election, and emits the closed one-shot response. It is not
agent-authored, not repository-provided as a runtime input, and not
caller-nominated: the launcher resolves and executes exactly the
administrator-installed, digest-pinned helper (RHAMP-REQ-082/083).

Wire model (HPAC-PPA-REQ-034..036 / RHAMP-REQ-057): the launcher passes the
canonical request as raw bytes on the inherited **request** file descriptor
and reads the canonical response from the inherited **response** file
descriptor. There is no shell, no argv interpolation of untrusted facts, no
network, and no shared stdio with the requesting agent. The fd numbers are
given only via the closed child-environment allowlist keys
``PCAE_PPLP_REQUEST_FD`` / ``PCAE_PPLP_RESPONSE_FD``.

The human decision surface: this phase implements the protocol, the
deterministic neutralized rendering, the display/digest equivalence check,
and the explicit-election binding. A real interactive local surface is
successor work (the mandatory real-CTAP2-hardware verification phase). When
no interactive surface is available and the launcher has not supplied the
disclosed test-only decision seam, the helper fails closed with
``CANCEL`` (RHAMP-REQ-097/100 — never an implicit or timeout approval).

The disclosed **test-only** decision seam (HPAC-PPA §16 discipline;
mirrors ``hpac_protected_admin_writer``'s ``_topology_probe`` /
``_protected_root`` seams): the launcher MAY include a
``test_decision_directive`` object in the request envelope *only* when its
caller passed the ``_test_decision_source`` seam. A guard test asserts no
production caller passes it, and the directive key is rejected outright when
the envelope's ``ceremony_mode`` is ``production``.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import unicodedata

REQUEST_SCHEMA_VERSION = "HPAC-PPLP-REQUEST/1.0"
RESPONSE_SCHEMA_VERSION = "HPAC-PPLP-RESPONSE/1.0"
MECHANISM_ID = "pcae-protected-local-presentation"

#: HPAC-PPA-REQ-036 — the closed response decision vocabulary.
DECISION_APPROVE = "APPROVE"
DECISION_REJECT = "REJECT"

#: HPAC-PPA-REQ-034 — the 13 closed human-visible fact keys (== HPAC-REQ-091).
HUMAN_VISIBLE_FACT_KEYS = (
    "repository_identity",
    "repository_display",
    "task_id",
    "task_display",
    "runtime_target_id",
    "runtime_target_display",
    "operation_effect_scope_display",
    "prompt_hash",
    "prompt_instruction_display",
    "invocation_id",
    "invocation_display",
    "expires_at",
    "one_shot_notice",
)

#: HPAC-PPA-REQ-034 — the closed request binding keys the launcher supplies.
_REQUEST_BINDING_KEYS = frozenset(
    {
        "request_schema_version",
        "ceremony_mode",
        "nonce",
        "request_id",
        "approval_id",
        "challenge_id",
        "presentation_digest",
        "approval_subject_digest",
        "principal_id",
        "invocation_id",
        "attempt_id",
        "expires_at",
        "mechanism_id",
        "installation_id",
        "generation",
        "installation_digest",
        "descriptor_digest",
        "renderer_profile",
        "human_visible_facts",
        "request_digest",
    }
)


class ProtectedPresentationHelperError(Exception):
    """A helper-side protocol / rendering fault. The launcher maps a
    non-response to ``helper_response_untrusted`` / ``ceremony_cancelled``
    (HPAC-PPA-REQ-038 / §18)."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _self_excluding_digest(document: dict, *, field: str) -> str:
    projected = dict(document)
    projected[field] = ""
    return _canonical_digest(projected)


# ─────────────────────────────────────────────────────────────────────────
# Untrusted-content neutralization (RHAMP-REQ-095/096)
# ─────────────────────────────────────────────────────────────────────────

_C0_C1_ALLOWED = {0x09, 0x0A}  # tab, LF only


def neutralize_untrusted_text(value: object) -> str:
    """Escape / strip C0 and C1 control characters, neutralize ANSI / OSC /
    terminal-title escape sequences, and neutralize bidirectional-override
    code points, so a repository-, task-, path-, prompt-, or scope-derived
    string can never alter, spoof, or suppress a trusted label or the
    Approve / Reject controls (RHAMP-REQ-095/096). Idempotent: the digest is
    computed over these neutralized bytes.
    """

    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFC", text)
    out: list[str] = []
    for ch in text:
        cp = ord(ch)
        if cp in _C0_C1_ALLOWED:
            out.append(ch)
            continue
        if cp < 0x20 or 0x7F <= cp <= 0x9F:
            out.append(f"\\x{cp:02x}")
            continue
        # RTL/LTR overrides, isolates, embeddings, ZWSP-class formatters.
        if cp in (0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B,
                  0x202C, 0x202D, 0x202E, 0x2060, 0x2066, 0x2067, 0x2068,
                  0x2069, 0xFEFF):
            out.append(f"\\u{cp:04x}")
            continue
        out.append(ch)
    return "".join(out)


def render_human_visible_bytes(human_visible_facts: dict, *, renderer_profile: str) -> bytes:
    """The frozen deterministic renderer (RHAMP-REQ-093): the closed 13
    facts → byte-identical displayed bytes for a given ``renderer_profile``.
    UTF-8, NFC, LF line endings. Every value is neutralized untrusted text;
    trusted labels are constant. All 13 fields are rendered — no omission,
    truncation, or collapse (RHAMP-REQ-092).
    """

    if set(human_visible_facts) != set(HUMAN_VISIBLE_FACT_KEYS):
        raise ProtectedPresentationHelperError("human_visible_facts is not the closed 13-field set")
    if human_visible_facts.get("one_shot_notice") is not True:
        raise ProtectedPresentationHelperError("one_shot_notice must be the const true")
    lines = [
        f"renderer_profile\t{neutralize_untrusted_text(renderer_profile)}",
        "PCAE PROTECTED LOCAL PRESENTATION — approve exactly this bounded operation",
    ]
    for key in HUMAN_VISIBLE_FACT_KEYS:
        if key == "one_shot_notice":
            lines.append("one_shot_notice\tThis approval authorizes exactly one attempt.")
            continue
        lines.append(f"{key}\t{neutralize_untrusted_text(human_visible_facts[key])}")
    lines.append("[APPROVE] and [REJECT] are the only controls. There is no implicit or timeout approval.")
    return ("\n".join(lines) + "\n").encode("utf-8")


# ─────────────────────────────────────────────────────────────────────────
# Request / response protocol
# ─────────────────────────────────────────────────────────────────────────


def _validate_request(document: object) -> dict:
    if not isinstance(document, dict):
        raise ProtectedPresentationHelperError("request is not an object")
    permitted = set(_REQUEST_BINDING_KEYS) | {"test_decision_directive"}
    if not set(document).issubset(permitted) or not _REQUEST_BINDING_KEYS.issubset(set(document)):
        raise ProtectedPresentationHelperError("request closed-field-set violation")
    if document["request_schema_version"] != REQUEST_SCHEMA_VERSION:
        raise ProtectedPresentationHelperError("request schema version mismatch")
    if document["mechanism_id"] != MECHANISM_ID:
        raise ProtectedPresentationHelperError("request mechanism_id is not the frozen const")
    if document["ceremony_mode"] not in ("production", "test-only"):
        raise ProtectedPresentationHelperError("request ceremony_mode is invalid")
    if document["ceremony_mode"] == "production" and "test_decision_directive" in document:
        # HPAC-PPA §16 — the disclosed test seam can never appear in a
        # production ceremony envelope.
        raise ProtectedPresentationHelperError("test_decision_directive is not permitted in a production ceremony")
    if not isinstance(document["nonce"], str) or len(document["nonce"]) < 64:
        raise ProtectedPresentationHelperError("request nonce is too short")
    digest = document["request_digest"]
    if not isinstance(digest, str) or len(digest) != 64:
        raise ProtectedPresentationHelperError("request_digest is malformed")
    if _self_excluding_digest(
        {k: v for k, v in document.items() if k != "test_decision_directive"}, field="request_digest"
    ) != digest:
        raise ProtectedPresentationHelperError("request_digest does not recompute")
    return document


def _observe_election(request: dict, displayed_bytes: bytes) -> str:
    """Present the neutralized displayed bytes and obtain an explicit human
    decision. This phase supports the disclosed test-only decision seam and,
    otherwise, fails closed with ``CANCEL`` (there is no interactive local
    surface in this phase — RHAMP-REQ-097/100; successor hardware phase)."""

    directive = request.get("test_decision_directive")
    if directive is not None:
        if not isinstance(directive, dict) or set(directive) != {"decision", "displayed_digest_ack"}:
            raise ProtectedPresentationHelperError("test_decision_directive has an invalid closed shape")
        # The directive must acknowledge the exact bytes this helper rendered,
        # so a test cannot approve a payload different from what was shown.
        if directive["displayed_digest_ack"] != hashlib.sha256(displayed_bytes).hexdigest():
            raise ProtectedPresentationHelperError("test_decision_directive does not acknowledge the rendered bytes")
        decision = directive["decision"]
        if decision in (DECISION_APPROVE, DECISION_REJECT):
            return decision
        if decision in ("CANCEL", "EOF"):
            return "CANCEL"
        if decision == "MALFORMED_RESPONSE":
            return "MALFORMED_RESPONSE"
        if decision == "NO_RESPONSE":
            os._exit(0)
        if decision == "CRASH":
            os._exit(3)
        raise ProtectedPresentationHelperError(f"unknown test decision {decision!r}")
    # No interactive surface available this phase → explicit cancel.
    return "CANCEL"


def _build_response(request: dict, decision: str, displayed_digest: str, *, now: str) -> dict:
    document = {
        "response_schema_version": RESPONSE_SCHEMA_VERSION,
        "nonce": request["nonce"],
        "request_id": request["request_id"],
        "approval_id": request["approval_id"],
        "challenge_id": request["challenge_id"],
        "presentation_digest": request["presentation_digest"],
        "mechanism_id": request["mechanism_id"],
        "installation_id": request["installation_id"],
        "generation": request["generation"],
        "installation_digest": request["installation_digest"],
        "descriptor_digest": request["descriptor_digest"],
        "renderer_profile": request["renderer_profile"],
        "human_visible_representation_digest": displayed_digest,
        "decision": decision,
        "responded_at": now,
        "response_digest": "",
    }
    document["response_digest"] = _self_excluding_digest(document, field="response_digest")
    return document


def run_helper(request_fd: int, response_fd: int, *, now: str) -> int:
    raw = _read_all(request_fd)
    try:
        request = _validate_request(json.loads(raw.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtectedPresentationHelperError(f"request is not canonical JSON: {exc}") from exc

    displayed = render_human_visible_bytes(
        request["human_visible_facts"], renderer_profile=request["renderer_profile"]
    )
    displayed_digest = hashlib.sha256(displayed).hexdigest()
    # RHAMP-REQ-094 — the digested payload is the exact bytes displayed.
    if request["presentation_digest"] and not isinstance(request["presentation_digest"], str):
        raise ProtectedPresentationHelperError("presentation_digest malformed")

    decision = _observe_election(request, displayed)
    if decision == "CANCEL":
        # No response, no approval (HPAC-PPA-REQ-036).
        return 0
    if decision == "MALFORMED_RESPONSE":
        os.write(response_fd, b"{ this is not canonical json")
        return 0

    response = _build_response(request, decision, displayed_digest, now=now)
    os.write(response_fd, _canonical_bytes(response))
    return 0


def _read_all(fd: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            break
        chunks.append(chunk)
    return b"".join(chunks)


def main(argv=None) -> int:
    from datetime import datetime, timezone

    try:
        request_fd = int(os.environ["PCAE_PPLP_REQUEST_FD"])
        response_fd = int(os.environ["PCAE_PPLP_RESPONSE_FD"])
    except (KeyError, ValueError):
        print("ERROR: PCAE_PPLP_REQUEST_FD / PCAE_PPLP_RESPONSE_FD are required", file=sys.stderr)
        return 2
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    try:
        return run_helper(request_fd, response_fd, now=now)
    except ProtectedPresentationHelperError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        try:
            os.close(response_fd)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

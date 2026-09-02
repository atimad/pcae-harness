"""HPAC-PAWA-001 v1.1 §32A — the configured-agent-principal resolution
source: ``HPAC-PAWA-AGENT-EXCLUSION/1.0`` and
``resolve_configured_agent_identity()``.

Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.3.1 (Slice 1, atomic unit A1 —
this resolver ships **together with** the writer factory in
``hpac_protected_admin_writer.py`` and never without it,
HPAC-PAWA-REQ-208).

**This module is inside the non-agent-importable consumer-inventory fence.**
Ordinary agent / runtime / Gate / plugin / ``pcae`` CLI code SHALL NOT
import it (guard: the fresh ``.1R.30R.3.1`` suite, HPAC-PAWA-REQ-209).

What it does (HPAC-PAWA-REQ-164/165, §32A):

1. Validate the closed ``HPAC-PAWA-AGENT-EXCLUSION/1.0`` record (12 fields,
   canonical bytes, self-excluding ``record_digest``, grammar) and its
   binding to the current installation, protected root, and the
   ``HPAC-PAWA-CURRENT-GENERATION/1.0`` anchor's ``agent_exclusion_digest``
   (§20A / C-2).
2. Read its ``symbolic_account`` (an OS account **name**, never a uid
   integer, never caller / env / current-euid derived — §32A.2 / §32A.8).
3. Resolve that account **live** through the trusted OS account database
   and require the live uid to equal the record's ``provisioned_uid``
   (C-1 — closes the delete → recreate-under-a-new-uid silent rebind;
   §32A.4 / §32A.5). No reverse-uid fallback, no stored-uid fallback.
4. Enumerate the account's **current** primary + supplementary groups
   **live** (§32A.6, PAWA-INV-12 — group membership is never persisted as
   authority).

Every fault fails closed. The recognition sequence in
``hpac_protected_admin_writer.py`` maps every fault here onto
``agent_principal_unknown`` (#3) — no new ``pawa_failure_code``
(§42A / HPAC-PAWA-REQ-202). Whether the resolved ``(uid, gids)`` can then
*write* the protected root (group drift → ``agent_has_protected_write_
authority`` #4) is the recognition sequence's step 3, not this module's.

The authority basis is **live effective filesystem write access**, never
the uid integer — ``provisioned_uid`` is an account-instance continuity
pin, not an authority input (HPAC-PAWA-REQ-180).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Callable, Optional

from pcae.core.hpac_foundation import HPACMalformedError
from pcae.core.hpac_pawa_schemas import (
    ANCHOR_STATE_VOCAB,
    AUTHORITY_NAMESPACE,
    PawaSchemaError,
    require_hex64,
    require_installation_id,
    require_pawa_timestamp,
    require_root_identity,
    self_excluding_digest,
)

__all__ = [
    "AGENT_EXCLUSION_SCHEMA",
    "AgentExclusionError",
    "ConfiguredAgentAuthorityIdentity",
    "ParsedAgentExclusion",
    "AgentIdentitySource",
    "validate_agent_exclusion_record",
    "resolve_live_authority_identity",
    "resolve_configured_agent_identity",
    "build_agent_exclusion_document",
    "AGENT_EXCLUSION_FIELDS",
]

AGENT_EXCLUSION_SCHEMA = "HPAC-PAWA-AGENT-EXCLUSION/1.0"

#: §32A.2 — an OS account name; NOT a uid integer, NOT a display name,
#: NOT a path. Grammar-bounded (HPAC-PAWA-REQ-175).
_SYMBOLIC_ACCOUNT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]{0,63}$")

AGENT_EXCLUSION_FIELDS = frozenset(
    {
        "artifact_schema_version",
        "record_digest",
        "symbolic_account",
        "provisioned_uid",
        "installation_id",
        "protected_root_identity",
        "authority_namespace",
        "generation",
        "created_at",
        "supersedes",
        "provenance_ref",
        "state",
    }
)

#: A documented fixture-only injection point (HPAC-PAWA-REQ-166 / §32A.8 /
#: R3 test-seam). Given the record's ``symbolic_account`` and
#: ``provisioned_uid`` it returns ``(live_uid, live_gids)`` or raises
#: :class:`LookupError` for an unresolvable account. Production always
#: passes ``None`` and resolves through ``pwd`` / ``os.getgrouplist``.
AgentIdentitySource = Callable[[str, int], "tuple[int, frozenset[int]]"]


class AgentExclusionError(HPACMalformedError):
    """The configured agent principal could not be trustworthily resolved.

    Every instance maps to ``agent_principal_unknown`` (#3, §42A). Never a
    new ``pawa_failure_code``; never a default to ``os.geteuid()``, to
    "no agent", or to a permissive outcome (HPAC-PAWA-REQ-167).
    """


@dataclass(frozen=True)
class ConfiguredAgentAuthorityIdentity:
    """§2 — the OS authority identity ``(uid, gids)`` of the configured
    PCAE agent principal, for evaluating protected-root write authority in
    §33 steps 3 and 7. Its authority basis is live effective filesystem
    write access, never the uid integer itself."""

    uid: int
    gids: "frozenset[int]"
    symbolic_account: str
    record_digest: str


@dataclass(frozen=True)
class ParsedAgentExclusion:
    document: dict
    symbolic_account: str
    provisioned_uid: int
    installation_id: str
    protected_root_identity: dict
    generation: int
    record_digest: str
    state: str
    supersedes: Optional[dict]


def _require_symbolic_account(value: object) -> str:
    if not isinstance(value, str) or not _SYMBOLIC_ACCOUNT_RE.fullmatch(value):
        raise AgentExclusionError(
            "symbolic_account: expected an OS account name matching ^[A-Za-z_][A-Za-z0-9_.-]{0,63}$"
        )
    return value


def _require_uid(value: object, *, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AgentExclusionError(f"{context}: expected a non-negative integer uid")
    return value


def _require_generation(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise AgentExclusionError("generation: expected an integer >= 1")
    return value


def _validate_supersedes(value: object, generation: int) -> Optional[dict]:
    if generation == 1:
        if value is not None:
            raise AgentExclusionError("supersedes: must be null for the record's first generation")
        return None
    if not isinstance(value, dict) or set(value) != {"previous_generation", "previous_record_digest"}:
        raise AgentExclusionError(
            "supersedes: expected a closed {previous_generation, previous_record_digest} object"
        )
    previous = value["previous_generation"]
    if not isinstance(previous, int) or isinstance(previous, bool) or previous < 1 or previous >= generation:
        raise AgentExclusionError("supersedes.previous_generation: must be an integer in [1, generation)")
    require_hex64(value["previous_record_digest"], context="supersedes.previous_record_digest")
    return value


def validate_agent_exclusion_record(
    document: object,
    *,
    installation_id: str,
    live_root_identity: dict,
    manifest_root_identity: dict,
    anchor_agent_exclusion_digest: str,
) -> ParsedAgentExclusion:
    """§32A.1 / HPAC-PAWA-REQ-177 — the full pure validation.

    ``document`` MUST already have been read through
    ``read_canonical_json_document`` (exact canonical bytes, single-link
    regular file, no symlink) and its ownership / mode / not-agent-writable
    checks performed by the recognition sequence. This function validates
    the closed schema, the self-excluding digest, the grammar, the
    installation / root-identity binding, and — crucially (C-2) — that the
    record's ``record_digest`` equals the current-generation anchor's
    ``agent_exclusion_digest``.
    """

    if not isinstance(document, dict):
        raise AgentExclusionError("agent-exclusion record is not an object")
    if set(document) != AGENT_EXCLUSION_FIELDS:
        raise AgentExclusionError(
            f"agent-exclusion record closed-field-set violation: "
            f"{sorted(set(document) ^ AGENT_EXCLUSION_FIELDS)}"
        )
    if document["artifact_schema_version"] != AGENT_EXCLUSION_SCHEMA:
        raise AgentExclusionError("agent-exclusion record artifact_schema_version is not the frozen const")
    record_digest = require_hex64(document["record_digest"], context="agent_exclusion.record_digest")
    try:
        recomputed = self_excluding_digest(document, digest_field="record_digest")
    except PawaSchemaError as exc:
        raise AgentExclusionError(str(exc)) from exc
    if recomputed != record_digest:
        raise AgentExclusionError("agent-exclusion record record_digest does not recompute")
    symbolic_account = _require_symbolic_account(document["symbolic_account"])
    provisioned_uid = _require_uid(document["provisioned_uid"], context="provisioned_uid")
    record_installation_id = require_installation_id(document["installation_id"])
    if record_installation_id != installation_id:
        raise AgentExclusionError("agent-exclusion record installation_id does not match the current installation")
    root_identity = require_root_identity(document["protected_root_identity"])
    if root_identity != live_root_identity or root_identity != manifest_root_identity:
        raise AgentExclusionError(
            "agent-exclusion record protected_root_identity does not match the live root / store manifest "
            "(a copied record never validates, PAWA-INV-5/PAWA-INV-12)"
        )
    if document["authority_namespace"] != AUTHORITY_NAMESPACE:
        raise AgentExclusionError("agent-exclusion record authority_namespace is not the frozen const")
    generation = _require_generation(document["generation"])
    require_pawa_timestamp(document["created_at"], context="agent_exclusion.created_at")
    supersedes = _validate_supersedes(document["supersedes"], generation)
    provenance_ref = document["provenance_ref"]
    if not isinstance(provenance_ref, str) or provenance_ref.strip() != provenance_ref or provenance_ref == "":
        raise AgentExclusionError("agent-exclusion record provenance_ref is malformed")
    state = document["state"]
    if state not in ANCHOR_STATE_VOCAB:
        raise AgentExclusionError("agent-exclusion record state is outside the closed vocabulary")
    if state != "ACTIVE":
        raise AgentExclusionError(f"agent-exclusion record state is {state!r}, not ACTIVE")
    require_hex64(anchor_agent_exclusion_digest, context="anchor.agent_exclusion_digest")
    if record_digest != anchor_agent_exclusion_digest:
        # C-2 — a restored superseded record whose digest != the anchor
        # fails closed; it does not become current merely because its bytes
        # are restored (§20A / §32C / HPAC-PAWA-REQ-171).
        raise AgentExclusionError(
            "agent-exclusion record_digest does not equal current-generation.agent_exclusion_digest "
            "(restored / stale exclusion record — independent rollback is impossible, C-2)"
        )
    return ParsedAgentExclusion(
        document=document,
        symbolic_account=symbolic_account,
        provisioned_uid=provisioned_uid,
        installation_id=record_installation_id,
        protected_root_identity=root_identity,
        generation=generation,
        record_digest=record_digest,
        state=state,
        supersedes=supersedes,
    )


def _live_identity_from_os(symbolic_account: str, provisioned_uid: int) -> "tuple[int, frozenset[int]]":
    """§32A.4 / §32A.6 — live resolution through the trusted OS account
    database (``pwd`` + ``os.getgrouplist``). ``os.getgrouplist`` returns
    the account's current primary + supplementary groups on both Linux and
    macOS (HPAC-PAWA-REQ-206 — a platform-adapter detail within §63's
    frozen normative properties).
    """

    import pwd

    try:
        entry = pwd.getpwnam(symbolic_account)
    except KeyError as exc:
        raise AgentExclusionError(
            f"symbolic_account {symbolic_account!r} is unknown to the OS account database "
            "(deletion / rename) — no fallback to provisioned_uid alone (HPAC-PAWA-REQ-183/186)"
        ) from exc
    except OSError as exc:  # NSS failure, etc. — fail closed.
        raise AgentExclusionError(
            f"OS account database lookup for {symbolic_account!r} failed: {exc!r}"
        ) from exc
    live_uid = entry.pw_uid
    if live_uid != provisioned_uid:
        raise AgentExclusionError(
            f"live uid {live_uid} for {symbolic_account!r} != provisioned_uid {provisioned_uid} "
            "(recreated under a new uid / UID reuse / rename) — a deliberate protected reprovision is "
            "required, no silent rebind (C-1, HPAC-PAWA-REQ-184/185)"
        )
    try:
        gids = os.getgrouplist(symbolic_account, entry.pw_gid)
    except OSError as exc:
        raise AgentExclusionError(
            f"live group enumeration for {symbolic_account!r} failed: {exc!r}"
        ) from exc
    group_set = frozenset(int(g) for g in gids) | {int(entry.pw_gid)}
    return live_uid, group_set


def resolve_live_authority_identity(
    symbolic_account: str,
    provisioned_uid: int,
    *,
    _configured_agent_identity_source: Optional[AgentIdentitySource] = None,
) -> "tuple[int, frozenset[int]]":
    """Resolve ``(uid, gids)`` live. ``_configured_agent_identity_source``
    is a documented fixture-only seam (HPAC-PAWA-REQ-166) — ``None`` in
    production. A guard test asserts no non-test module ever passes it."""

    if _configured_agent_identity_source is None:
        return _live_identity_from_os(symbolic_account, provisioned_uid)
    try:
        uid, gids = _configured_agent_identity_source(symbolic_account, provisioned_uid)
    except LookupError as exc:
        raise AgentExclusionError(
            f"fixture identity source could not resolve {symbolic_account!r}: {exc!r}"
        ) from exc
    if not isinstance(uid, int) or isinstance(uid, bool) or uid < 0:
        raise AgentExclusionError("fixture identity source returned a non-uid value")
    if uid != provisioned_uid:
        raise AgentExclusionError(
            f"fixture identity source live uid {uid} != provisioned_uid {provisioned_uid}"
        )
    return uid, frozenset(int(g) for g in gids)


def resolve_configured_agent_identity(
    document: object,
    *,
    installation_id: str,
    live_root_identity: dict,
    manifest_root_identity: dict,
    anchor_agent_exclusion_digest: str,
    _configured_agent_identity_source: Optional[AgentIdentitySource] = None,
) -> ConfiguredAgentAuthorityIdentity:
    """§9.1 / HPAC-PAWA-REQ-165 — the named resolution source entry point.

    Reads the ``HPAC-PAWA-AGENT-EXCLUSION/1.0`` protected record, **not**
    ``os.geteuid()``. Returns the ``ConfiguredAgentAuthorityIdentity``
    that parameterizes the §33 step-3 negative boundary check and is one
    operand of the §33 step-7 not-configured-agent current-context check.
    Every fault → :class:`AgentExclusionError` → ``agent_principal_unknown``.
    """

    parsed = validate_agent_exclusion_record(
        document,
        installation_id=installation_id,
        live_root_identity=live_root_identity,
        manifest_root_identity=manifest_root_identity,
        anchor_agent_exclusion_digest=anchor_agent_exclusion_digest,
    )
    uid, gids = resolve_live_authority_identity(
        parsed.symbolic_account,
        parsed.provisioned_uid,
        _configured_agent_identity_source=_configured_agent_identity_source,
    )
    return ConfiguredAgentAuthorityIdentity(
        uid=uid,
        gids=gids,
        symbolic_account=parsed.symbolic_account,
        record_digest=parsed.record_digest,
    )


def build_agent_exclusion_document(
    *,
    symbolic_account: str,
    provisioned_uid: int,
    installation_id: str,
    protected_root_identity: dict,
    generation: int,
    created_at: str,
    provenance_ref: str,
    supersedes: Optional[dict],
    state: str = "ACTIVE",
) -> dict:
    """Out-of-band provisioning / rotation only (§32B). Builds the closed
    record and stamps its self-excluding ``record_digest``."""

    document = {
        "artifact_schema_version": AGENT_EXCLUSION_SCHEMA,
        "record_digest": "",
        "symbolic_account": _require_symbolic_account(symbolic_account),
        "provisioned_uid": _require_uid(provisioned_uid, context="provisioned_uid"),
        "installation_id": require_installation_id(installation_id),
        "protected_root_identity": require_root_identity(protected_root_identity),
        "authority_namespace": AUTHORITY_NAMESPACE,
        "generation": _require_generation(generation),
        "created_at": require_pawa_timestamp(created_at, context="created_at"),
        "supersedes": _validate_supersedes(supersedes, generation),
        "provenance_ref": provenance_ref,
        "state": state if state in ANCHOR_STATE_VOCAB else _raise_state(state),
    }
    if not isinstance(provenance_ref, str) or provenance_ref == "" or provenance_ref.strip() != provenance_ref:
        raise AgentExclusionError("provenance_ref is malformed")
    document["record_digest"] = self_excluding_digest(document, digest_field="record_digest")
    return document


def _raise_state(state: object):
    raise AgentExclusionError(f"state {state!r} is outside the closed vocabulary")

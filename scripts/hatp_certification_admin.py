#!/usr/bin/env python3
"""HMIC-001 v1.0 Protected-Admin Certification / Revocation Surface (Wave
E, Phase 149O.19.5E), `docs/PHASE_149O_19_4_HATP_MANDATORY_INDEPENDENT_
VERIFICATION_CERTIFICATION_IMPLEMENTATION_PLAN.md` §9.2-9.5.

This is a **standalone script, deliberately outside `src/pcae/`** — never
imported by `cli.py`, `commands/agent.py`, `core/agent.py`, or any other
`src/pcae/**` module (HMIC-REQ-079). It is not packaged, not installed as
a console-script entry point, and not reachable from any agent-executable
code path. It is invoked manually,

    python scripts/hatp_certification_admin.py create   --repository-root . --certified-by "<name>" --verification-record-path <path>
    python scripts/hatp_certification_admin.py activate --repository-root . --certification-id <id>
    python scripts/hatp_certification_admin.py revoke   --certification-id <id>

by an operator running under the Class-B Protected Administrator OS
principal (HMIC-REQ-013) — the only principal with real write access to
`HATPTrustStore.production().root`. It imports `hatp_mandatory_
certification.py`'s public `derive_*`/`load_*` functions and its
internal (non-`__all__`-exported) writer functions
(`_append_certification_record`, `_write_active_binding`,
`_write_revocation`) directly.

Real security boundary (HMIC-REQ-079, HMIC-REQ-018, HMIC-REQ-020):
**OS filesystem write permission on the Protected Root**, never an
in-process authority check. Nothing in this script — no username string,
no `--admin` flag, no environment variable, no CLI boolean, no Git
author identity — establishes or substitutes for that permission
(HMIC-REQ-017/020). If the OS principal invoking this script lacks real
write access to `HATPTrustStore.production().root`, every write below
fails with a normal `OSError`/`PermissionError` from the underlying
`os.replace`/`fcntl.flock` call in Wave C's writer primitives — this
script neither catches nor launders that into a misleading message
implying it *is* the boundary. A leading underscore on the imported
writer functions reduces accidental API discovery inside `src/pcae/**`;
it is not itself, and is never described here as, a security control
(governing-prompt item 52).

Ceremonies implemented (exactly HMIC-REQ-076-078, HMIC-REQ-086-088,
HMIC-REQ-091-093):

* ``create``   — HMIC-REQ-076 steps 1-6: derives the full authority
  tuple fresh and read-only, presents it for explicit human confirmation,
  then atomically appends a new, immutable, ``status="active"``
  `CertificationRecord`. Never activates it (HMIC-REQ-086/088 — a
  *separate* explicit write is always required).
* ``activate`` — HMIC-REQ-076 step 7 / HMIC-REQ-088: explicitly binds an
  *existing*, named ``--certification-id`` as the active certification
  for the current repository/deployment. No "latest"/"newest"/implicit
  selection exists (HMIC-REQ-085/092).
* ``revoke``   — HMIC-REQ-091-093: field-mutates the named
  ``--certification-id`` to ``status="revoked"``. Never deletes, never
  un-revokes (monotonic), never touches the active-binding pointer
  (HMIC-REQ-094's readiness consequence is left entirely to Wave D's
  validator — this script does not clear or switch the binding).

Minimized human-entered authority-sensitive input (HMIC-REQ-077-078):
this script never accepts `--repository-id`, `--deployment-id`,
`--implementation-commit`, `--implementation-digest`,
`--contract-version`, `--certification-id` (for *creation*; it is only
ever accepted as a *locator* for `activate`/`revoke`, identifying an
already-existing object — HMIC-REQ-item-61 "Locator != authority"), or
any `--verified`/`--valid`-shaped boolean. `--repository-root` is a
neutral working-tree *locator* only — the exact same non-authority-
bearing parameter shape `validate_active_hatp_mandatory_independent_
verification_certification(repository_root: Path)` already accepts
(HMIC-REQ-109's own docstring) — never itself a `repository_instance_id`
or `canonical_deployment_root` value. `--verification-record-path`
(``create`` only) is likewise a locator: the script reads and hashes the
file at that path; it never accepts a pre-computed digest string
directly (governing-prompt item 62 — "no arbitrary 'verification_passed
=True'").

No automatic phase-completion coupling (governing-prompt item 15): this
script never reads `PROJECT_STATUS.md`, `tasks/TODO.md`,
`CHANGELOG.md`, a phase report's `status` field, or a test result to
decide whether to certify. Every invocation is a deliberate, explicit
admin action; `--verification-record-path` is a human-selected locator
only, evidentiary metadata (HMIC-REQ-071/073), never authority.

No readiness/PB/RAE/AG3/AG5/HMRC coupling (HMIC-REQ-118-127): this
script never imports `hatp_mandatory_cutover.py`, `permission_broker.py`,
`permission_broker_foundation.py`, or `rollback_approval_evidence.py`,
and never calls `activate_hatp_mandatory`. `CERTIFY`/`ACTIVATE`
(certification) and HMRC's own `ACTIVATE` (`PREPARED -> HATP_MANDATORY`)
remain separate ceremonies (HMIC-REQ-118).

Root resolution (HMIC-REQ-080): the Protected Root is always
`HATPTrustStore.production().root`, resolved internally by each
ceremony function below with **no** `--root`/`--store-root` override
flag and **no** `PCAE_HMIC_ROOT` (or equivalent) environment variable —
mirroring `HATPTrustStore.production()`'s own no-argument constructor
exactly. Each ceremony function additionally accepts a private,
underscore-prefixed ``_protected_root`` keyword — structurally outside
the CLI argument surface — used only by this phase's own isolated
``tmp_path`` tests, mirroring `HATPTrustStore.__init__`'s own
``_test_only_root`` pattern and `_validate_at_root`'s own test-only seam
(HMIC-REQ-080's own text names this exact mirrored pattern). No
production caller of this script's `main()` ever supplies it.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pcae.core.hatp_bootstrap import HATPTrustStore, HATPTrustStoreError
from pcae.core.hatp_mandatory_certification import (
    CertificationBinding,
    CertificationConflictError,
    CertificationIdentityMismatchError,
    CertificationMalformedError,
    CertificationRecord,
    CertificationRecordNotFoundError,
    HMICIdentityDerivationError,
    _append_certification_record,
    _write_active_binding,
    _write_revocation,
    derive_canonical_deployment_root,
    derive_certification_id,
    derive_contract_versions,
    derive_implementation_commit,
    derive_implementation_scope_digest,
    derive_repository_instance_id,
    load_certification,
)
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import RepositoryIdentityError

# ═══════════════════════════════════════════════════════════════════════════
# Canonical clock helper (HMIC-REQ-032 `certified_at` / `revoked_at`
# format). Deliberately duplicated from `hatp_mandatory_cutover.py::
# _format_timestamp` rather than imported — this script imports nothing
# from `hatp_mandatory_cutover.py` (HMIC-REQ-118-127's own "no HMRC
# coupling" boundary), and this is the identical narrow-duplication
# pattern `hatp_bootstrap.py::_parse_iso_timestamp` already documents
# ("duplicated deliberately ... rather than imported, to keep this
# module's only upstream dependency ... independent").
# ═══════════════════════════════════════════════════════════════════════════


def _canonical_timestamp_now() -> str:
    """HMIC-REQ-032: strict `YYYY-MM-DDTHH:MM:SS[.ffffff]Z`, wall-clock at
    invocation (HMIC-REQ-076 step 4) — never accepted as human-entered
    input (governing-prompt item 12)."""

    moment = datetime.now(timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _sha256_hex_of_file(path: Path) -> str:
    hasher = hashlib.sha256()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def _resolve_protected_root(_protected_root: Optional[Path]) -> Path:
    """HMIC-REQ-080: no `--root`/env override on the production path.
    `_protected_root` exists only as a private, non-CLI, test-only seam
    (never populated by `main()`)."""

    if _protected_root is not None:
        return _protected_root
    return HATPTrustStore.production().root


# ═══════════════════════════════════════════════════════════════════════════
# Typed ceremony results (governing-prompt item 70: never HMICValidationResult)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CreateCeremonyResult:
    """`create`'s sole return type. Never `ValidationStatus.VALID` or any
    other Wave-D-shaped field (HMIC-REQ item-79 — writer != validator).
    `already_existed=True` means an exact byte-identical record was
    already stored (HMIC-REQ-084/098 idempotent create); it never means
    the record is currently active or `VALID`."""

    certification_id: str
    already_existed: bool
    record: CertificationRecord


@dataclass(frozen=True)
class ActivateCeremonyResult:
    certification_id: str
    repository_instance_id: str
    canonical_deployment_root: str


@dataclass(frozen=True)
class RevokeCeremonyResult:
    certification_id: str
    already_revoked: bool
    revoked_at: str


class AdminCeremonyError(Exception):
    """Base class for this script's own ceremony-level errors — distinct
    in kind from `HATPMandatoryCertificationError` (storage/identity
    layer) and never conflated with a `CertificationStatus` outcome
    (governing-prompt item 71)."""


class ConfirmationDeclinedError(AdminCeremonyError):
    """The human operator did not confirm the tool-derived target tuple
    (HMIC-REQ-076 step 5). No write of any kind occurs."""


# ═══════════════════════════════════════════════════════════════════════════
# CREATE (HMIC-REQ-076 steps 1-6; never step 7 -- see `activate` below)
# ═══════════════════════════════════════════════════════════════════════════


def certify(
    *,
    repository_root: Path,
    certified_by: str,
    verification_record_path: Path,
    confirm: bool,
    _protected_root: Optional[Path] = None,
) -> CreateCeremonyResult:
    """HMIC-REQ-076 steps 1-6. `confirm` stands in for HMIC-REQ-076 step
    5's human confirmation of the tool-derived target tuple — `main()`
    always resolves it from an interactive prompt; this function accepts
    it as an already-decided boolean so tests can exercise both the
    accept and decline paths deterministically without a real TTY. No
    caller of this function may supply `repository_instance_id`,
    `canonical_deployment_root`, `implementation_commit`,
    `implementation_scope_digest`, `contract_versions`, or
    `certification_id` directly (HMIC-REQ-045/077) -- every one of those
    is derived here, read-only, from `repository_root` alone."""

    harness_root = HarnessPath(repository_root)

    # HMIC-REQ-076 step 4: tool-derived, read-only. A derivation failure
    # here is a genuine environment failure -- fails closed, no partial
    # or placeholder record is ever assembled.
    repository_instance_id = derive_repository_instance_id(harness_root)
    canonical_deployment_root = derive_canonical_deployment_root(harness_root)
    implementation_commit = derive_implementation_commit(harness_root)
    implementation_scope_digest = derive_implementation_scope_digest(harness_root)
    contract_versions = derive_contract_versions(harness_root)
    certified_at = _canonical_timestamp_now()

    # HMIC-REQ-078: the only additional human input is a verification-
    # record *locator* -- this script reads and hashes it; the human
    # never supplies the digest string itself.
    verification_record_digest = _sha256_hex_of_file(verification_record_path)

    # HMIC-REQ-076 step 5: present the tool-derived target for
    # confirmation. `main()` is the only caller that turns this into a
    # real interactive prompt; see module docstring.
    if not confirm:
        raise ConfirmationDeclinedError(
            "certification creation was not confirmed by the operator; no record was written"
        )

    fields = {
        "repository_instance_id": repository_instance_id,
        "canonical_deployment_root": canonical_deployment_root,
        "implementation_commit": implementation_commit,
        "implementation_scope_digest": implementation_scope_digest,
        "contract_versions": contract_versions,
        "verification_record_digest": verification_record_digest,
        "certified_at": certified_at,
        "certified_by": certified_by,
    }
    certification_id = derive_certification_id(fields)

    record = CertificationRecord(
        certification_id=certification_id,
        repository_instance_id=repository_instance_id,
        canonical_deployment_root=canonical_deployment_root,
        implementation_commit=implementation_commit,
        implementation_scope_digest=implementation_scope_digest,
        contract_versions=contract_versions,
        verification_record_digest=verification_record_digest,
        certified_at=certified_at,
        certified_by=certified_by,
        status="active",
        revoked_at=None,
    )

    protected_root = _resolve_protected_root(_protected_root)
    # HMIC-REQ-076 step 6 / HMIC-REQ-083-084/097-098: atomic, create-once,
    # under the certification-transition lock.
    append_result = _append_certification_record(protected_root, record)
    return CreateCeremonyResult(
        certification_id=append_result.record.certification_id,
        already_existed=append_result.idempotent,
        record=append_result.record,
    )


# ═══════════════════════════════════════════════════════════════════════════
# ACTIVATE (HMIC-REQ-076 step 7 / HMIC-REQ-086-088; a separate, explicit
# admin write -- never automatic, never coupled to `certify` above)
# ═══════════════════════════════════════════════════════════════════════════


def activate(
    *,
    repository_root: Path,
    certification_id: str,
    confirm: bool,
    _protected_root: Optional[Path] = None,
) -> ActivateCeremonyResult:
    """Explicitly binds `certification_id` (HMIC-REQ-092: exact ID only,
    no "latest"/"newest" selection) as the active certification for the
    current repository/deployment, derived fresh from `repository_root`
    exactly as `certify` derives it (HMIC-REQ-045). Requires the
    candidate record to already exist and parse (a structural
    precondition -- HMIC-REQ item-20's "store/binding mutation !=
    validator decision" distinction) but never requires it to be
    currently HMIC `VALID`; that judgment remains Wave D's alone
    (governing-prompt item 21 -- no pre-validation is invented here
    because HMIC-001 does not require one)."""

    harness_root = HarnessPath(repository_root)
    repository_instance_id = derive_repository_instance_id(harness_root)
    canonical_deployment_root = derive_canonical_deployment_root(harness_root)

    protected_root = _resolve_protected_root(_protected_root)

    # Structural existence/parse precondition only -- not a VALID check.
    if _protected_root is None:
        load_certification(certification_id, harness_root)
    else:
        _load_by_id_from_root(protected_root, certification_id)

    if not confirm:
        raise ConfirmationDeclinedError(
            f"activation of certification_id={certification_id!r} was not confirmed by the operator; "
            "no binding was written"
        )

    binding = CertificationBinding(
        repository_instance_id=repository_instance_id,
        canonical_deployment_root=canonical_deployment_root,
        active_certification_id=certification_id,
    )
    _write_active_binding(protected_root, binding)
    return ActivateCeremonyResult(
        certification_id=certification_id,
        repository_instance_id=repository_instance_id,
        canonical_deployment_root=canonical_deployment_root,
    )


def _load_by_id_from_root(protected_root: Path, certification_id: str) -> CertificationRecord:
    """Test-seam-root variant of the existence/parse precondition:
    `load_certification` (the production entrypoint) always resolves
    `HATPTrustStore.production().root` internally, so it cannot be used
    against an isolated `tmp_path` protected root. This calls the same
    Wave C reader (`_load_certification_record`, imported lazily to avoid
    widening this script's top-level import surface with another
    underscore-prefixed symbol) against the exact `_protected_root` the
    ceremony itself was given -- structurally equivalent, never a second
    parsing implementation."""

    from pcae.core.hatp_mandatory_certification import _load_certification_record

    return _load_certification_record(protected_root, certification_id)


# ═══════════════════════════════════════════════════════════════════════════
# REVOKE (HMIC-REQ-091-093; monotonic field mutation, never deletion)
# ═══════════════════════════════════════════════════════════════════════════


def revoke(
    *,
    certification_id: str,
    confirm: bool,
    _protected_root: Optional[Path] = None,
) -> RevokeCeremonyResult:
    """HMIC-REQ-092: `certification_id` is always an explicit, caller-
    named locator here -- never derived, never "revoke active/latest".
    HMIC-REQ-094's readiness consequence (a revoked *active* certification
    yields `REVOKED`) is left entirely to Wave D's validator; this
    function never reads, clears, or switches `certification-
    bindings.json` (governing-prompt item 24)."""

    if not confirm:
        raise ConfirmationDeclinedError(
            f"revocation of certification_id={certification_id!r} was not confirmed by the operator; "
            "no revocation was written"
        )

    protected_root = _resolve_protected_root(_protected_root)

    # Structural existence/parse precondition (also raises
    # `CertificationRecordNotFoundError` for an unknown ID, identically
    # to `_write_revocation`'s own check -- read here first only so this
    # ceremony can report `already_revoked` accurately, mirroring
    # `CreateCeremonyResult.already_existed`'s own pre/post distinction).
    existing = _load_by_id_from_root(protected_root, certification_id)
    already_revoked_before = existing.status == "revoked"

    revoked_at = _canonical_timestamp_now()
    try:
        revoked_record = _write_revocation(protected_root, certification_id=certification_id, revoked_at=revoked_at)
    except CertificationConflictError:
        # HMIC-REQ item-40/94: already revoked at a *different* timestamp
        # -- the first-recorded revocation always wins; report it, don't
        # mask it as a fresh success.
        raise
    return RevokeCeremonyResult(
        certification_id=revoked_record.certification_id,
        already_revoked=already_revoked_before,
        revoked_at=revoked_record.revoked_at,
    )


# ═══════════════════════════════════════════════════════════════════════════
# CLI (interactive confirmation only -- HMIC-REQ-076 step 5; never
# reachable from `src/pcae/**`, HMIC-REQ-079/082)
# ═══════════════════════════════════════════════════════════════════════════


def _prompt_confirm(target_description: str) -> bool:
    print(target_description, file=sys.stderr)
    print("Type 'yes' to confirm this exact tool-derived target, anything else to abort:", file=sys.stderr)
    try:
        response = input()
    except EOFError:
        return False
    return response.strip() == "yes"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hatp_certification_admin.py",
        description=(
            "Protected-admin HMIC-001 certification/revocation ceremony. "
            "Not reachable from the ordinary pcae CLI or any agent-executed code path (HMIC-REQ-079/082). "
            "Requires real OS write access to HATPTrustStore.production().root."
        ),
    )
    sub = parser.add_subparsers(dest="ceremony", required=True)

    create_parser = sub.add_parser("create", help="Create a new CertificationRecord (does not activate it).")
    create_parser.add_argument(
        "--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd)."
    )
    create_parser.add_argument("--certified-by", required=True, help="Operator identity string (audit metadata only).")
    create_parser.add_argument(
        "--verification-record-path",
        type=Path,
        required=True,
        help="Path to the canonical phase-report artifact this certification attests to; its bytes are hashed here.",
    )
    create_parser.add_argument(
        "--assume-yes",
        action="store_true",
        help="Skip the interactive confirmation prompt (non-interactive/scripted admin invocation only).",
    )

    activate_parser = sub.add_parser("activate", help="Explicitly bind an existing certification_id as active.")
    activate_parser.add_argument(
        "--repository-root", type=Path, default=Path.cwd(), help="Neutral working-tree locator (default: cwd)."
    )
    activate_parser.add_argument("--certification-id", required=True, help="Exact certification_id to activate.")
    activate_parser.add_argument("--assume-yes", action="store_true")

    revoke_parser = sub.add_parser("revoke", help="Revoke an existing certification_id (field mutation, not deletion).")
    revoke_parser.add_argument("--certification-id", required=True, help="Exact certification_id to revoke.")
    revoke_parser.add_argument("--assume-yes", action="store_true")

    return parser


def main(argv: "Optional[list]" = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        if args.ceremony == "create":
            target = (
                f"CREATE certification for repository_root={args.repository_root}\n"
                f"  certified_by={args.certified_by!r}\n"
                f"  verification_record_path={args.verification_record_path}"
            )
            confirmed = args.assume_yes or _prompt_confirm(target)
            result = certify(
                repository_root=args.repository_root,
                certified_by=args.certified_by,
                verification_record_path=args.verification_record_path,
                confirm=confirmed,
            )
            print(f"certification_id={result.certification_id} already_existed={result.already_existed}")
        elif args.ceremony == "activate":
            target = (
                f"ACTIVATE certification_id={args.certification_id} for repository_root={args.repository_root}"
            )
            confirmed = args.assume_yes or _prompt_confirm(target)
            result = activate(
                repository_root=args.repository_root,
                certification_id=args.certification_id,
                confirm=confirmed,
            )
            print(
                f"bound certification_id={result.certification_id} "
                f"repository_instance_id={result.repository_instance_id} "
                f"canonical_deployment_root={result.canonical_deployment_root}"
            )
        else:
            target = f"REVOKE certification_id={args.certification_id}"
            confirmed = args.assume_yes or _prompt_confirm(target)
            result = revoke(certification_id=args.certification_id, confirm=confirmed)
            print(f"certification_id={result.certification_id} already_revoked={result.already_revoked} revoked_at={result.revoked_at}")
    except ConfirmationDeclinedError as exc:
        print(f"ABORTED: {exc}", file=sys.stderr)
        return 1
    except (
        HMICIdentityDerivationError,
        RepositoryIdentityError,
        CertificationMalformedError,
        CertificationConflictError,
        CertificationIdentityMismatchError,
        CertificationRecordNotFoundError,
        HATPTrustStoreError,
        OSError,
    ) as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

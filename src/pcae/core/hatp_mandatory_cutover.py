"""HATP Mandatory Cutover State Foundation — Phase 149O.18A (Wave A of
the HMRC-001 v1.0 implementation, `docs/PHASE_149O_17_HATP_MANDATORY_
PRODUCTION_CONSUMPTION_IMPLEMENTATION_PLAN.md` §9.1).

Owns, and only owns: the Cutover Mode vocabulary (HMRC-REQ-031), the
Cutover Record model/parser (HMRC-REQ-045-047), protected persistence
(HMRC-REQ-043/051), mode resolution (HMRC-REQ-052/074), the monotonic
activation-history marker (HMRC-REQ-049/050), and cutover-transition
validation (HMRC-REQ-038-040). It owns **no** evidence verification, **no**
Permission Broker logic, and **no** rollback effects (HMRC-REQ-044) — see
`docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md`.

This module does not wire into `execute_rollback`/`build_rollback_
execution` (Waves C/D), does not perform evidence-ID consumption
(Wave B), and does not activate `HATP_MANDATORY` for any real deployment
(this phase's tests use only isolated protected-root fixtures, never
`HATPTrustStore.production()` for writes).

**Activation-authority scope decision (149O.18A, recorded here rather
than invented at implementation time):** HMRC-REQ-041 requires
`PREPARED -> HATP_MANDATORY` activation to be reachable only by "Protected
Activation Authority" — the existing Class-B protected administrative
mechanism 149O.6/149O.7 established. Direct source reading of
`hatp_bootstrap.py`, `hatp_hardware_credentials.py`, and a repository-wide
grep for any `Principal`/`Admin`-gated write API confirms no such
application-level authority-check mechanism exists anywhere in this
codebase yet — `HATPTrustStore` itself is deliberately read-only
("enrollment, revocation, and rotation ... are not implemented by this
phase at all"). Per the governing prompt's stop-condition guidance (do not
approximate protected-admin authority with a caller-supplied username/env
flag), this module does **not** invent a `ProtectedAdminPrincipal` type or
any application-level authority check. Instead it mirrors the *actual*
mechanism this repository already uses for the sibling `registry.json`
file under the same protected root: the authority boundary is enforced by
the operating system's file permissions on the fixed, non-agent-writable
protected root itself (`hatp_bootstrap.py::_default_production_trust_root`),
not by an in-process principal check. Consistent with this, the internal
transition-write function below (`_write_cutover_transition`) takes an
explicit `protected_root: Path` parameter and is never paired, anywhere in
this module, with `HATPTrustStore.production().root` — there is no
production-reachable, CLI-reachable, or agent-reachable call path that can
cause a real activation. It exists only for isolated-fixture testing of
the transition/monotonicity/concurrency invariants, and for a future human
operator to invoke directly (e.g. from a privileged shell with real write
access to the protected root), exactly mirroring how `registry.json`
itself is expected to be provisioned out-of-band today. `activated_by` is
therefore accepted as an explicit, caller-supplied string with no default
and no derivation from process/session/environment state — never an agent
identity, never a session/task ID (HMRC-REQ-045) — because the only
legitimate caller is a human operator who already possesses real
filesystem write access to the protected root, not any in-process
identity this module could observe.

**`PREPARED -> LEGACY_COMPATIBLE` (149O.17 §9.1, restated):** not frozen
one way or the other by HMRC-001. This module's transition graph
deliberately omits it (conservative omission, not a guess) until a future
HMRC-001 amendment resolves it.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from pcae.core.hatp_bootstrap import HATPTrustStore
from pcae.core.paths import HarnessPath
from pcae.core.repository_identity import is_valid_repository_instance_id, read_repository_identity

CUTOVER_RECORD_SCHEMA_VERSION = 1
CUTOVER_ACTIVATION_MARKER_SCHEMA_VERSION = 1

_CUTOVER_RECORD_FILE_NAME = "cutover-record.json"
_CUTOVER_ACTIVATION_MARKER_FILE_NAME = "cutover-activation-marker.json"
_CUTOVER_TRANSITION_LOCK_FILE_NAME = ".cutover-transition.lock"

# Strict lexical timestamp grammar (149O.17 plan §14 / HMRC-REQ hardening):
# `Z`-suffix-only, matching this repository's existing precedent for a new,
# authority-bearing timestamp field (`cltr/authority/envelope.py::
# _TIMESTAMP_PATTERN`) rather than either existing repository parser's
# permissive `fromisoformat`-based handling. Fully anchored (`fullmatch`)
# so no double-Z-class or trailing-garbage input can slip through:
# `...ZZ`, `...Z+00:00`, `...Z ` (trailing space), lowercase `z`, and any
# non-`Z` offset are all rejected by construction, independent of which
# CPython version executes this code (149O.12B-Obs-PY39-1 is not
# reintroduced here).
_TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$")


# ═══════════════════════════════════════════════════════════════════════════
# Errors
# ═══════════════════════════════════════════════════════════════════════════


class HATPMandatoryCutoverError(Exception):
    """Base error for HATP mandatory-cutover-state operations."""


class CutoverStateMalformedError(HATPMandatoryCutoverError):
    """A Cutover Record or activation-marker document exists but fails
    strict validation. Never partially accepted."""


class CutoverStateSymlinkError(HATPMandatoryCutoverError):
    """A Cutover Record or activation-marker path is (or resolves
    through) a symlink. Refused rather than followed."""


class CutoverTransitionRejectedError(HATPMandatoryCutoverError):
    """A requested cutover-mode transition is not permitted (HMRC-REQ-038
    /039), or the on-disk mode changed between resolution and write
    (stale/concurrent transition, refused rather than overwritten)."""


# ═══════════════════════════════════════════════════════════════════════════
# Cutover Mode vocabulary (HMRC-REQ-031)
# ═══════════════════════════════════════════════════════════════════════════


class CutoverMode(str, Enum):
    """Exactly three Consumption Modes (HMRC-REQ-031). No fourth mode
    value exists anywhere in this module — fail-closed outcomes reuse
    `HATP_MANDATORY`, the strictest existing mode, rather than inventing a
    new one (governing-prompt item 6)."""

    LEGACY_COMPATIBLE = "LEGACY_COMPATIBLE"
    PREPARED = "PREPARED"
    HATP_MANDATORY = "HATP_MANDATORY"


# Modes a Cutover Record may actually store on disk. `LEGACY_COMPATIBLE`
# is never itself persisted (HMRC-REQ-050 defines it as the *absence* of a
# record, not a record value).
_STORED_MODES = frozenset({CutoverMode.PREPARED, CutoverMode.HATP_MANDATORY})

# The only two writable transitions (HMRC-REQ-038/039). Every reverse
# transition, every direct LEGACY_COMPATIBLE -> HATP_MANDATORY skip, and
# every self-transition is absent from this set and therefore rejected by
# `is_valid_cutover_transition`.
_ALLOWED_TRANSITIONS = frozenset(
    {
        (CutoverMode.LEGACY_COMPATIBLE, CutoverMode.PREPARED),
        (CutoverMode.PREPARED, CutoverMode.HATP_MANDATORY),
    }
)


def is_valid_cutover_transition(current: CutoverMode, target: CutoverMode) -> bool:
    """Centralized transition-graph validation (HMRC-REQ-038/039). No
    individual writer path may apply separate rules (governing-prompt item
    53)."""

    return (current, target) in _ALLOWED_TRANSITIONS


# ═══════════════════════════════════════════════════════════════════════════
# Strict timestamp validation
# ═══════════════════════════════════════════════════════════════════════════


def _validate_timestamp(value: object, *, context: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP_PATTERN.fullmatch(value):
        raise CutoverStateMalformedError(
            f"{context}: expected a strict 'YYYY-MM-DDTHH:MM:SS[.ffffff]Z' timestamp, got {value!r}"
        )
    normalized = value[:-1] + "+00:00"
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise CutoverStateMalformedError(f"{context}: not a calendar-valid timestamp: {value!r}") from exc
    return value


def _format_timestamp(moment: datetime) -> str:
    utc = moment.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ═══════════════════════════════════════════════════════════════════════════
# Duplicate-JSON-key-rejecting strict loader (HMRC-REQ-047)
# ═══════════════════════════════════════════════════════════════════════════


def _reject_duplicate_keys(pairs: list) -> dict:
    seen: set = set()
    result: dict = {}
    for key, value in pairs:
        if key in seen:
            raise CutoverStateMalformedError(f"duplicate JSON object key: {key!r}")
        seen.add(key)
        result[key] = value
    return result


def _load_json_no_duplicate_keys(raw: str) -> object:
    try:
        return json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise CutoverStateMalformedError(f"document is not valid JSON: {exc}") from exc


# ═══════════════════════════════════════════════════════════════════════════
# Cutover Record model (HMRC-REQ-045-047)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CutoverRecord:
    version: int
    repository_instance_id: str
    mode: CutoverMode
    activated_at: str
    activated_by: str


_CUTOVER_RECORD_ALLOWED_FIELDS = frozenset(
    {"version", "repository_instance_id", "mode", "activated_at", "activated_by"}
)


def parse_cutover_record(document: object) -> CutoverRecord:
    """Strict, closed-schema parser (HMRC-REQ-045-047). Constructor and
    parser share one validation domain: every field check here is the
    same check `CutoverRecord.__post_init__`-equivalent construction would
    need, and no state is directly constructible that this parser would
    reject (governing-prompt item 9) — this module always routes
    construction through this function, never through the dataclass
    constructor with unchecked inputs."""

    if not isinstance(document, dict):
        raise CutoverStateMalformedError("cutover record is not a JSON object")

    unknown = set(document.keys()) - _CUTOVER_RECORD_ALLOWED_FIELDS
    if unknown:
        raise CutoverStateMalformedError(f"cutover record has unrecognized fields: {sorted(unknown)}")

    missing = _CUTOVER_RECORD_ALLOWED_FIELDS - set(document.keys())
    if missing:
        raise CutoverStateMalformedError(f"cutover record is missing fields: {sorted(missing)}")

    version = document["version"]
    # Strict integer: `bool` is an `int` subclass in Python, so `True`/
    # `False` must be explicitly rejected (HMRC-REQ-046).
    if not isinstance(version, int) or isinstance(version, bool) or version != CUTOVER_RECORD_SCHEMA_VERSION:
        raise CutoverStateMalformedError(
            f"cutover record version must be the strict integer {CUTOVER_RECORD_SCHEMA_VERSION}, got {version!r}"
        )

    repository_instance_id = document["repository_instance_id"]
    if not is_valid_repository_instance_id(repository_instance_id):
        raise CutoverStateMalformedError("cutover record repository_instance_id is not a valid UUID4 string")

    mode_value = document["mode"]
    if not isinstance(mode_value, str) or mode_value not in {m.value for m in _STORED_MODES}:
        raise CutoverStateMalformedError(
            f"cutover record mode must be one of {sorted(m.value for m in _STORED_MODES)}, got {mode_value!r}"
        )
    mode = CutoverMode(mode_value)

    activated_at = _validate_timestamp(document["activated_at"], context="cutover record activated_at")

    activated_by = document["activated_by"]
    if not isinstance(activated_by, str) or not activated_by:
        raise CutoverStateMalformedError(f"cutover record activated_by: expected a non-empty string, got {activated_by!r}")

    return CutoverRecord(
        version=version,
        repository_instance_id=repository_instance_id,
        mode=mode,
        activated_at=activated_at,
        activated_by=activated_by,
    )


def _cutover_record_to_document(record: CutoverRecord) -> dict:
    return {
        "version": record.version,
        "repository_instance_id": record.repository_instance_id,
        "mode": record.mode.value,
        "activated_at": record.activated_at,
        "activated_by": record.activated_by,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Monotonic activation-history marker (HMRC-REQ-049/050)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CutoverActivationMarker:
    version: int
    repository_instance_id: str
    first_activated_at: str


_MARKER_ALLOWED_FIELDS = frozenset({"version", "repository_instance_id", "first_activated_at"})


def parse_cutover_activation_marker(document: object) -> CutoverActivationMarker:
    if not isinstance(document, dict):
        raise CutoverStateMalformedError("cutover activation marker is not a JSON object")

    unknown = set(document.keys()) - _MARKER_ALLOWED_FIELDS
    if unknown:
        raise CutoverStateMalformedError(f"cutover activation marker has unrecognized fields: {sorted(unknown)}")

    missing = _MARKER_ALLOWED_FIELDS - set(document.keys())
    if missing:
        raise CutoverStateMalformedError(f"cutover activation marker is missing fields: {sorted(missing)}")

    version = document["version"]
    if not isinstance(version, int) or isinstance(version, bool) or version != CUTOVER_ACTIVATION_MARKER_SCHEMA_VERSION:
        raise CutoverStateMalformedError(
            f"cutover activation marker version must be the strict integer "
            f"{CUTOVER_ACTIVATION_MARKER_SCHEMA_VERSION}, got {version!r}"
        )

    repository_instance_id = document["repository_instance_id"]
    if not is_valid_repository_instance_id(repository_instance_id):
        raise CutoverStateMalformedError("cutover activation marker repository_instance_id is not a valid UUID4 string")

    first_activated_at = _validate_timestamp(
        document["first_activated_at"], context="cutover activation marker first_activated_at"
    )

    return CutoverActivationMarker(
        version=version,
        repository_instance_id=repository_instance_id,
        first_activated_at=first_activated_at,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Protected path safety (local re-implementation — 149O.17 plan §9.5:
# `hatp_bootstrap.py::_reject_symlink` is a private module internal, not
# re-exported; duplicating this two-line check locally is judged
# lower-risk than widening that module's public surface for a single
# one-line reuse)
# ═══════════════════════════════════════════════════════════════════════════


def _reject_symlink(target: Path) -> None:
    if target.is_symlink():
        raise CutoverStateSymlinkError(f"HATP cutover-state path is a symlink, refusing: {target}")
    if target.parent.exists() and target.parent.is_symlink():
        raise CutoverStateSymlinkError(f"HATP cutover-state parent directory is a symlink, refusing: {target.parent}")


def _atomic_write_json(path: Path, document: dict) -> None:
    """Mirrors the existing project idiom (`repository_identity.py::
    _write_atomic`, `cltr/persistence.py::_write_atomic`): temp file in
    the same directory, fsync, atomic `os.replace`. Used for the Cutover
    Record, which legitimately transitions forward (unlike the
    create-once marker below) — `os.replace` clobbering the previous
    value is the intended, monotonic-forward-only semantics here, not a
    HSCE-style no-clobber evidence publication (governing-prompt item
    48)."""

    _reject_symlink(path)
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp-hatp-cutover-", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        _reject_symlink(path)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _write_activation_marker_if_absent(protected_root: Path, repository_instance_id: str, first_activated_at: str) -> None:
    """Write-once semantics (HMRC-REQ-049): created exactly once, at the
    first successful `PREPARED -> HATP_MANDATORY` activation, and never
    rewritten or deleted by any ordinary code path thereafter. Uses
    `O_CREAT | O_EXCL` (create-only, HSCE-style no-clobber) — deliberately
    different from the Cutover Record's own `os.replace` semantics, since
    the marker specifically must never change once written."""

    marker_path = protected_root / _CUTOVER_ACTIVATION_MARKER_FILE_NAME
    _reject_symlink(marker_path)
    protected_root.mkdir(parents=True, exist_ok=True)
    document = {
        "version": CUTOVER_ACTIVATION_MARKER_SCHEMA_VERSION,
        "repository_instance_id": repository_instance_id,
        "first_activated_at": first_activated_at,
    }
    payload = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    try:
        fd = os.open(str(marker_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


# ═══════════════════════════════════════════════════════════════════════════
# Read outcomes (tri-state: OK / ABSENT / CORRUPT — HMRC-REQ-049 groups
# "missing, corrupt, or unreadable" together; only a *genuinely absent*
# file is distinguished from every other failure mode, since a corrupt or
# unreadable file must never be silently treated the same as "no file was
# ever written here" — that would be a corruption-triggered downgrade)
# ═══════════════════════════════════════════════════════════════════════════


class _ReadStatus(str, Enum):
    OK = "ok"
    ABSENT = "absent"
    CORRUPT = "corrupt"


@dataclass(frozen=True)
class _RecordReadResult:
    status: _ReadStatus
    record: Optional[CutoverRecord] = None


@dataclass(frozen=True)
class _MarkerReadResult:
    status: _ReadStatus
    marker: Optional[CutoverActivationMarker] = None


def _read_cutover_record(path: Path) -> _RecordReadResult:
    try:
        _reject_symlink(path)
        if not path.exists():
            return _RecordReadResult(_ReadStatus.ABSENT)
        raw = path.read_text(encoding="utf-8")
        document = _load_json_no_duplicate_keys(raw)
        record = parse_cutover_record(document)
        return _RecordReadResult(_ReadStatus.OK, record)
    except (OSError, HATPMandatoryCutoverError):
        return _RecordReadResult(_ReadStatus.CORRUPT)


def _read_cutover_activation_marker(path: Path) -> _MarkerReadResult:
    try:
        _reject_symlink(path)
        if not path.exists():
            return _MarkerReadResult(_ReadStatus.ABSENT)
        raw = path.read_text(encoding="utf-8")
        document = _load_json_no_duplicate_keys(raw)
        marker = parse_cutover_activation_marker(document)
        return _MarkerReadResult(_ReadStatus.OK, marker)
    except (OSError, HATPMandatoryCutoverError):
        # A corrupt/unreadable marker is deliberately NOT treated as
        # "absent" (anti-corruption-downgrade hardening): if it were, an
        # attacker could force "first install" treatment for a
        # previously-activated deployment merely by corrupting the
        # marker file, exactly the downgrade HMRC-REQ-040/049 forbids.
        return _MarkerReadResult(_ReadStatus.CORRUPT)


# ═══════════════════════════════════════════════════════════════════════════
# Mode resolution (HMRC-REQ-048-052/074)
# ═══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class CutoverModeResolution:
    mode: CutoverMode
    reason: str


REASON_FIRST_INSTALL = "first_install_no_activation_history"
REASON_RECORD_VALID = "cutover_record_valid"
REASON_FAIL_CLOSED_RECORD_MISSING_AFTER_PRIOR_ACTIVATION = "fail_closed_record_missing_after_prior_activation"
REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION = "fail_closed_record_corrupt_or_unreadable_after_prior_activation"
REASON_FAIL_CLOSED_INTERNAL_CONSISTENCY = "fail_closed_corrupt_record_no_activation_history_internal_consistency_failure"
REASON_FAIL_CLOSED_NO_REPOSITORY_IDENTITY = "fail_closed_no_local_repository_identity_provisioned"


def _resolve_absent_record_state(marker_path: Path, repository_instance_id: str) -> CutoverModeResolution:
    marker_result = _read_cutover_activation_marker(marker_path)

    if marker_result.status == _ReadStatus.ABSENT:
        return CutoverModeResolution(CutoverMode.LEGACY_COMPATIBLE, REASON_FIRST_INSTALL)

    if marker_result.status == _ReadStatus.OK and marker_result.marker.repository_instance_id == repository_instance_id:
        return CutoverModeResolution(CutoverMode.HATP_MANDATORY, REASON_FAIL_CLOSED_RECORD_MISSING_AFTER_PRIOR_ACTIVATION)

    # Marker present but corrupt, or present for a different repository:
    # neither proves "this repository was never activated" (a single
    # protected root may serve multiple repositories, HMRC-REQ-048's
    # principle extended symmetrically to the marker) -- fail closed
    # rather than assume first-install.
    return CutoverModeResolution(CutoverMode.HATP_MANDATORY, REASON_FAIL_CLOSED_RECORD_MISSING_AFTER_PRIOR_ACTIVATION)


def _resolve_cutover_mode_at_root(protected_root: Path, repository_instance_id: Optional[str]) -> CutoverModeResolution:
    """Internal test seam: accepts an explicit protected root and
    repository identity. Never production-callable — no public wrapper
    ever forwards a caller-supplied root here (governing-prompt items
    16-18); the only production entrypoint is
    `resolve_production_hatp_cutover_mode`, which resolves both arguments
    itself. Performs a full read/validate sequence on every call — no
    cache (HMRC-REQ-052)."""

    record_path = protected_root / _CUTOVER_RECORD_FILE_NAME
    marker_path = protected_root / _CUTOVER_ACTIVATION_MARKER_FILE_NAME

    if repository_instance_id is None:
        # Phase 149O.18C narrow correction (classified API defect, not a
        # redesign): identity-absence alone must not fail closed to
        # HATP_MANDATORY when the protected root itself carries zero
        # activation evidence either (both the Cutover Record and the
        # monotonic marker genuinely ABSENT, not merely unmatched) -- a
        # deployment with no local repository identity AND no protected-root
        # activation history cannot possibly have been cutover-activated
        # (HMRC-REQ-045's Cutover Record schema itself requires a
        # repository_instance_id to have existed at write time), so treating
        # it as fail-closed-mandatory contradicts HMRC-REQ-032's explicit
        # "every existing deployment, including the current local
        # development host" LEGACY_COMPATIBLE default -- confirmed against
        # this repository's own real, unprovisioned state (149O.18C AG3
        # regression: `execute_rollback` wired to this resolver, as
        # HMRC-REQ-066/074 require, broke 8 pre-existing LEGACY_COMPATIBLE
        # rollback tests before this correction). Any record or marker
        # presence at all (valid, corrupt, or symlinked -- i.e. any status
        # other than ABSENT) is still treated exactly as conservatively as
        # before: fail-closed HATP_MANDATORY, unchanged. This branch changes
        # only the doubly-absent case, and reuses the existing
        # `_read_cutover_record`/`_read_cutover_activation_marker` readers
        # unmodified rather than duplicating their logic.
        record_probe = _read_cutover_record(record_path)
        marker_probe = _read_cutover_activation_marker(marker_path)
        if record_probe.status == _ReadStatus.ABSENT and marker_probe.status == _ReadStatus.ABSENT:
            return CutoverModeResolution(CutoverMode.LEGACY_COMPATIBLE, REASON_FIRST_INSTALL)
        return CutoverModeResolution(CutoverMode.HATP_MANDATORY, REASON_FAIL_CLOSED_NO_REPOSITORY_IDENTITY)

    record_result = _read_cutover_record(record_path)

    if record_result.status == _ReadStatus.OK:
        record = record_result.record
        if record.repository_instance_id != repository_instance_id:
            # Not-present-for-this-repository (HMRC-REQ-048): never
            # activates the wrong deployment, and is not itself proof
            # this repository was never activated either.
            return _resolve_absent_record_state(marker_path, repository_instance_id)
        return CutoverModeResolution(record.mode, REASON_RECORD_VALID)

    if record_result.status == _ReadStatus.ABSENT:
        return _resolve_absent_record_state(marker_path, repository_instance_id)

    # CORRUPT (malformed, unreadable, symlinked, or unknown/future
    # version -- `parse_cutover_record` already rejects those into this
    # same branch, so "unknown version" fails closed automatically
    # without a special case, HMRC-REQ-046/081-style discipline).
    marker_result = _read_cutover_activation_marker(marker_path)
    if marker_result.status == _ReadStatus.OK and marker_result.marker.repository_instance_id == repository_instance_id:
        return CutoverModeResolution(CutoverMode.HATP_MANDATORY, REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION)
    if marker_result.status == _ReadStatus.ABSENT:
        # A genuinely first-install deployment cannot organically produce
        # a corrupt record, since nothing ever wrote one -- this branch
        # should be unreachable in practice (149O.17 plan §9.1 step 5).
        # Treated as an internal-consistency failure: fail closed, never
        # a silent LEGACY_COMPATIBLE.
        return CutoverModeResolution(CutoverMode.HATP_MANDATORY, REASON_FAIL_CLOSED_INTERNAL_CONSISTENCY)
    # Marker present but corrupt, or present for a different repository.
    return CutoverModeResolution(CutoverMode.HATP_MANDATORY, REASON_FAIL_CLOSED_RECORD_CORRUPT_AFTER_PRIOR_ACTIVATION)


def _resolve_current_repository_instance_id(root: HarnessPath) -> Optional[str]:
    identity = read_repository_identity(root)
    return identity.repository_instance_id if identity is not None else None


def resolve_production_hatp_cutover_mode(root: HarnessPath) -> CutoverModeResolution:
    """The sole production entrypoint (HMRC-REQ-074): mode is derived
    exclusively from the protected Cutover Record, read fresh on every
    call. `root` is a neutral repository locator only (used solely to
    read the repo-local, non-authority-bearing `repository_instance_id`
    via the existing `repository_identity.py` API, exactly mirroring
    `hatp_ag_authority.py::_resolve_production_repository_context`'s
    precedent) — it never selects the protected trust root itself, which
    is always resolved internally via `HATPTrustStore.production().root`
    and is never caller-selectable (no env, CLI, or repo-local path
    accepted)."""

    repository_instance_id = _resolve_current_repository_instance_id(root)
    protected_root = HATPTrustStore.production().root
    return _resolve_cutover_mode_at_root(protected_root, repository_instance_id)


# ═══════════════════════════════════════════════════════════════════════════
# Cutover transition write (internal only — see module docstring's
# activation-authority scope decision). Never called with
# `HATPTrustStore.production().root` anywhere in this module.
# ═══════════════════════════════════════════════════════════════════════════


def _write_cutover_transition(
    protected_root: Path,
    *,
    target_mode: CutoverMode,
    repository_instance_id: str,
    activated_by: str,
    now: Optional[datetime] = None,
) -> CutoverRecord:
    """Internal, non-CLI, non-agent-reachable transition write. Re-checks
    the current resolved mode immediately before writing while holding an
    exclusive lock on the protected root (TOCTOU discipline,
    governing-prompt items 50-52): a concurrent racing writer either
    serializes behind this one and is then itself rejected by
    `is_valid_cutover_transition` (its `target_mode` no longer follows the
    now-current mode), or serializes ahead of this one and this call
    observes the new current mode and is rejected the same way. No
    downgrade or lost-update race is possible because only two, strictly
    ordered forward transitions exist at all (HMRC-REQ-038/039)."""

    if target_mode not in _STORED_MODES:
        raise ValueError(f"cannot write a cutover record for non-stored mode: {target_mode!r}")
    if not is_valid_repository_instance_id(repository_instance_id):
        raise ValueError("repository_instance_id is not a valid UUID4 string")
    if not isinstance(activated_by, str) or not activated_by:
        raise ValueError("activated_by must be a non-empty string")

    protected_root.mkdir(parents=True, exist_ok=True)
    lock_path = protected_root / _CUTOVER_TRANSITION_LOCK_FILE_NAME
    _reject_symlink(lock_path)
    lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        current_resolution = _resolve_cutover_mode_at_root(protected_root, repository_instance_id)
        if not is_valid_cutover_transition(current_resolution.mode, target_mode):
            raise CutoverTransitionRejectedError(
                f"transition {current_resolution.mode.value} -> {target_mode.value} is not permitted "
                f"(current mode resolved as: {current_resolution.reason})"
            )
        timestamp = _format_timestamp(now if now is not None else datetime.now(timezone.utc))
        record = CutoverRecord(
            version=CUTOVER_RECORD_SCHEMA_VERSION,
            repository_instance_id=repository_instance_id,
            mode=target_mode,
            activated_at=timestamp,
            activated_by=activated_by,
        )
        _atomic_write_json(protected_root / _CUTOVER_RECORD_FILE_NAME, _cutover_record_to_document(record))
        if target_mode == CutoverMode.HATP_MANDATORY:
            _write_activation_marker_if_absent(protected_root, repository_instance_id, timestamp)
        return record
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)

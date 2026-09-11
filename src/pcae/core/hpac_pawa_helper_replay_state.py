"""HPAC-PAWA-HELPER-001 v1.0 — durable, cross-process one-shot replay state
(§19 / §20.81 / §21 / §22, PAWAH-INV-10).

Phase N16-5-F-5-TB-REPLAY-REPAIR. This module closes the REPLAY-AFTER-RESTART
defect confirmed by N16-5-F-5-TB-HELPER-IV: the foundation's
:class:`~pcae.core.hpac_pawa_helper_protocol.ReplayLedger` kept spent
``(request_id, nonce)`` state in a process-local ``dict``, so a request
admitted and consumed by helper process A became ``FRESH`` again in helper
process B. Because a real helper is *one-shot per exec*, every request is
processed in a brand-new process — which made the in-memory ledger
unconditionally ineffective in production and made HPAC-PAWA-HELPER-REQ-076
("consumed ... cannot be accepted again, even if its response was lost"),
REQ-077 and PAWAH-INV-10 unenforceable.

**Scope discipline.** This repair introduces **no** new trust root, **no** new
datastore, **no** new schema in ``schemas/``, **no** new ``pawa_failure_code``
and **no** new RHAMP ``terminal_reason_code``. The durable state lives as
sibling records inside the *already-contracted*
``<HPAC_PROTECTED_ROOT>/pawa-helper/`` namespace (HPAC-PAWA-REQ-336 /
HPAC-PAWA-REQ-326, HPAC-PAWA-HELPER-001 §6.21-§6.23), under the same
protected-root trust boundary and the same deployment-owner ownership that
already guards the helper installation records and the §22 staged audit
evidence. It is the smallest thing that can make the §19 dispositions
survive the one-shot process lifetime.

**What a replay record is and is not.** A replay record is a *negative* fact:
evidence that a given ``(installation_id, generation, request_id, nonce)`` has
been reserved or spent. It carries no capability, no ``_seal``, no authority
object, and nothing from which one could be reconstructed
(HPAC-PAWA-HELPER-REQ-088 / REQ-091, PAWAH-INV-10). Loading the store in a
fresh process can only ever cause a **denial**; it can never revive authority,
re-emit a ``PERFORMED`` response, or reconstruct the dead helper's privileges.

**Record provenance (structurally valid != trusted).** Parsing successfully is
not trust. A record is only *usable for a replay decision* after it also
proves it belongs where it was found: its own bound fields must re-derive the
content-addressed ``replay_key`` that names its slot. A record that parses but
fails that binding — or whose ``record_digest`` does not recompute — is treated
as **corruption and fails closed** (``internal_fail_closed``), never as
"absent". Treating a malformed record as absent would itself be the replay
hole this phase exists to close.

**Non-agent-importability (HPAC-PAWA-HELPER-REQ-033).** Like its siblings this
module does not import ``pcae.core.hpac_protected_admin_writer``. It also
deliberately does not import ``pcae.core.hpac_foundation``'s
``reject_symlink``: every path operation here is performed through an
``O_NOFOLLOW``/``O_DIRECTORY`` descriptor chain with ``dir_fd``-relative
syscalls, which is strictly stronger than an ``lstat`` pre-check (it has no
check-then-use window at all), so no cross-module dependency is needed to get
the same property.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, FrozenSet, List, Mapping, Optional, Tuple

from pcae.core.hpac_pawa_helper_protocol import (
    FORBIDDEN_AUTHORITY_TOKENS,
    HelperProtocolError,
    HelperRequest,
    ReplayOutcome,
)

#: Record schema-version literal. This is a *record* marker inside the
#: already-contracted ``pawa-helper/`` namespace, not a new file in
#: ``schemas/`` and not a new protocol/request/response schema version.
REPLAY_RECORD_SCHEMA_VERSION = "HPAC-PAWA-HELPER-REPLAY-STATE/1.0"

#: Domain-separation tag for the durable replay key. Changing this string
#: would repartition the whole store, so it is frozen alongside the record
#: schema version.
_REPLAY_KEY_DOMAIN = "HPAC-PAWA-HELPER-REPLAY-KEY/1.0"

#: The contracted namespace this repair reuses (HPAC-PAWA-REQ-326/336).
PAWA_HELPER_NAMESPACE = "pawa-helper"
REPLAY_NAMESPACE = "replay"

_DIR_MODE = 0o700
_FILE_MODE = 0o600


class DurableReplayState(str, Enum):
    """The durable §20 state model, as persisted.

    ``REQUEST_RECEIVED`` is the *reservation* state: exactly one helper
    process holds the slot and no protected-root mutation has been attempted
    (HPAC-PAWA-HELPER-REQ-081). Every other member means the
    ``(request_id, nonce)`` is **spent** (HPAC-PAWA-HELPER-REQ-077) and can
    never be admitted again, whatever happened to the response.
    """

    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    MUTATION_ATTEMPT_STARTED = "MUTATION_ATTEMPT_STARTED"
    MUTATION_COMMITTED = "MUTATION_COMMITTED"
    EVIDENCE_WRITTEN = "EVIDENCE_WRITTEN"
    RESPONSE_EMITTED = "RESPONSE_EMITTED"
    RESULT_EMITTED = "RESULT_EMITTED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


#: Every state except the reservation state means spent (REQ-076 "consumed").
SPENT_STATES: FrozenSet[str] = frozenset(
    s.value for s in DurableReplayState if s is not DurableReplayState.REQUEST_RECEIVED
)

#: Legal forward-only durable transitions. A transition not in this table
#: fails closed rather than silently rewriting durable history.
_LEGAL_TRANSITIONS: Mapping[str, FrozenSet[str]] = {
    DurableReplayState.REQUEST_RECEIVED.value: frozenset(
        {
            DurableReplayState.MUTATION_ATTEMPT_STARTED.value,
            DurableReplayState.RESULT_EMITTED.value,
        }
    ),
    DurableReplayState.MUTATION_ATTEMPT_STARTED.value: frozenset(
        {
            DurableReplayState.MUTATION_COMMITTED.value,
            DurableReplayState.RECONCILIATION_REQUIRED.value,
        }
    ),
    DurableReplayState.MUTATION_COMMITTED.value: frozenset(
        {
            DurableReplayState.EVIDENCE_WRITTEN.value,
            DurableReplayState.RECONCILIATION_REQUIRED.value,
        }
    ),
    DurableReplayState.EVIDENCE_WRITTEN.value: frozenset(
        {DurableReplayState.RESPONSE_EMITTED.value}
    ),
    DurableReplayState.RESPONSE_EMITTED.value: frozenset(),
    DurableReplayState.RESULT_EMITTED.value: frozenset(),
    DurableReplayState.RECONCILIATION_REQUIRED.value: frozenset(),
}

#: The exact closed field set of a durable replay record. Unknown or missing
#: fields fail closed (same discipline as the §11 request schema).
_RECORD_FIELDS: FrozenSet[str] = frozenset(
    {
        "record_schema_version",
        "replay_key",
        "installation_id",
        "generation",
        "request_id",
        "nonce",
        "operation",
        "session_id",
        "subject",
        "request_digest",
        "expiry",
        "durable_state",
        "evidence_ref",
        "committed_digest",
        "reserved_at",
        "updated_at",
        "owner_pid",
        "record_digest",
    }
)


class ReplayStateCorruption(HelperProtocolError):
    """A durable replay record exists but cannot be trusted.

    Deliberately a subclass of :class:`HelperProtocolError` carrying the
    existing ``internal_fail_closed`` vocabulary member — this repair adds
    **no** new ``pawa_failure_code`` (HPAC-PAWA-HELPER-REQ-004).
    """

    def __init__(self, detail: str) -> None:
        super().__init__("internal_fail_closed", detail)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _rfc3339(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_expiry(raw: str) -> Optional[datetime]:
    """Parse a §11 ``expiry``. Returns ``None`` when unparseable, which every
    caller MUST treat as *expired* (fail closed), never as "no deadline"."""
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def compute_replay_key(
    *, installation_id: str, generation: int, request_id: str, nonce: str
) -> str:
    """The **durable replay key** (§19).

    ``sha256(domain || installation_id || generation || request_id || nonce)``,
    with each part length-prefixed so no two distinct tuples can collide by
    concatenation ambiguity.

    Three properties matter:

    * **It is the identity the contract replays on.** ``(request_id, nonce)``
      is the §19 one-shot identity; ``installation_id`` and ``generation``
      are folded in because a request is bound to exactly one installation
      and helper generation (§11), so a rotation ``G -> G+1`` partitions the
      keyspace rather than letting a G-bound request be re-presented to a
      G+1 helper against G's history.
    * **It is never caller-chosen.** ``request_id`` and ``nonce`` are
      attacker-influenced strings; they are *hashed*, so the on-disk name is
      always 64 lowercase hex characters. No caller value can traverse a
      path, choose a filename, or collide with another namespace's file.
    * **It binds a record to its slot.** A record's own fields must
      re-derive the key naming the slot it was found in, so a record copied
      or moved between slots is detected (see :func:`_validate_record`).
    """

    hasher = hashlib.sha256()
    for part in (
        _REPLAY_KEY_DOMAIN,
        installation_id,
        str(int(generation)),
        request_id,
        nonce,
    ):
        encoded = part.encode("utf-8")
        hasher.update(str(len(encoded)).encode("ascii"))
        hasher.update(b":")
        hasher.update(encoded)
    return hasher.hexdigest()


def request_subject(request: HelperRequest) -> str:
    """The §19 'subject' conjunct of a conflicting-replay comparison. Matches
    the foundation ledger's existing derivation exactly."""
    return request.principal_id or request.credential_id or request.proof_id or ""


def _canonical_bytes(record: Mapping[str, object]) -> bytes:
    payload = {k: v for k, v in record.items() if k != "record_digest"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _record_digest(record: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_bytes(record)).hexdigest()


@dataclass(frozen=True)
class ReplayRecord:
    """A validated durable replay record. Constructing one of these is the
    *only* way content read off disk becomes usable for a decision."""

    replay_key: str
    installation_id: str
    generation: int
    request_id: str
    nonce: str
    operation: str
    session_id: str
    subject: str
    request_digest: str
    expiry: str
    durable_state: str
    reserved_at: str
    updated_at: str
    owner_pid: int
    evidence_ref: Optional[str] = None
    committed_digest: Optional[str] = None

    @property
    def is_spent(self) -> bool:
        return self.durable_state in SPENT_STATES

    def to_mapping(self) -> Dict[str, object]:
        record: Dict[str, object] = {
            "record_schema_version": REPLAY_RECORD_SCHEMA_VERSION,
            "replay_key": self.replay_key,
            "installation_id": self.installation_id,
            "generation": self.generation,
            "request_id": self.request_id,
            "nonce": self.nonce,
            "operation": self.operation,
            "session_id": self.session_id,
            "subject": self.subject,
            "request_digest": self.request_digest,
            "expiry": self.expiry,
            "durable_state": self.durable_state,
            "evidence_ref": self.evidence_ref,
            "committed_digest": self.committed_digest,
            "reserved_at": self.reserved_at,
            "updated_at": self.updated_at,
            "owner_pid": self.owner_pid,
        }
        record["record_digest"] = _record_digest(record)
        return record


def _validate_record(raw: object, *, expected_key: str) -> ReplayRecord:
    """Turn untrusted on-disk bytes into a trusted :class:`ReplayRecord`, or
    fail closed.

    **Provenance separation.** Each step below is a separate conjunct; a
    record that satisfies some but not all of them is corruption, not a
    weaker-but-usable record:

    1. it is a JSON object with *exactly* the closed field set;
    2. its ``record_schema_version`` is the exact frozen literal;
    3. its ``durable_state`` is a member of the closed state enum;
    4. its ``record_digest`` recomputes over its own canonical bytes;
    5. its own ``(installation_id, generation, request_id, nonce)``
       re-derive ``replay_key``, **and** that key equals the slot the record
       was found in.

    (5) is what makes structural validity insufficient for trust: an attacker
    who can write into the replay directory still cannot relocate a benign
    record to mask a different request's spent state, nor forge one without
    also producing a matching content-addressed name.
    """

    if not isinstance(raw, dict):
        raise ReplayStateCorruption("durable replay record is not a JSON object")
    present = set(raw)
    if present != set(_RECORD_FIELDS):
        missing = sorted(set(_RECORD_FIELDS) - present)
        unknown = sorted(present - set(_RECORD_FIELDS))
        raise ReplayStateCorruption(
            f"durable replay record field set invalid (missing={missing}, unknown={unknown})"
        )
    if raw.get("record_schema_version") != REPLAY_RECORD_SCHEMA_VERSION:
        raise ReplayStateCorruption("durable replay record schema version mismatch")
    state = raw.get("durable_state")
    if not isinstance(state, str) or state not in {s.value for s in DurableReplayState}:
        raise ReplayStateCorruption(f"durable replay record has unknown state {state!r}")
    if raw.get("record_digest") != _record_digest(raw):
        raise ReplayStateCorruption("durable replay record digest mismatch (tampered or torn)")

    try:
        generation = int(raw["generation"])
        installation_id = str(raw["installation_id"])
        request_id = str(raw["request_id"])
        nonce = str(raw["nonce"])
        owner_pid = int(raw["owner_pid"])
    except (TypeError, ValueError) as exc:
        raise ReplayStateCorruption(f"durable replay record has malformed field types: {exc}")

    rederived = compute_replay_key(
        installation_id=installation_id,
        generation=generation,
        request_id=request_id,
        nonce=nonce,
    )
    if rederived != str(raw["replay_key"]) or rederived != expected_key:
        raise ReplayStateCorruption(
            "durable replay record is not bound to the slot it was found in"
        )

    evidence_ref = raw.get("evidence_ref")
    committed_digest = raw.get("committed_digest")
    if evidence_ref is not None and not isinstance(evidence_ref, str):
        raise ReplayStateCorruption("evidence_ref must be a string or null")
    if committed_digest is not None and not isinstance(committed_digest, str):
        raise ReplayStateCorruption("committed_digest must be a string or null")

    return ReplayRecord(
        replay_key=rederived,
        installation_id=installation_id,
        generation=generation,
        request_id=request_id,
        nonce=nonce,
        operation=str(raw["operation"]),
        session_id=str(raw["session_id"]),
        subject=str(raw["subject"]),
        request_digest=str(raw["request_digest"]),
        expiry=str(raw["expiry"]),
        durable_state=state,
        evidence_ref=evidence_ref,
        committed_digest=committed_digest,
        reserved_at=str(raw["reserved_at"]),
        updated_at=str(raw["updated_at"]),
        owner_pid=owner_pid,
    )


# ---------------------------------------------------------------------------
# Filesystem safety primitives.
#
# Every operation is performed relative to an open O_DIRECTORY|O_NOFOLLOW
# descriptor chain, so there is no path string re-resolved between a check and
# a use, and no component of the chain can be a symlink. This is the same
# anti-TOCTOU discipline ``hpac_pawa_helper_os.verify_helper_executable``
# applies to the helper binary, applied to the replay namespace.
# ---------------------------------------------------------------------------


def _open_dir(parent_fd: Optional[int], name: str, *, create: bool) -> int:
    flags = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0)
    try:
        if parent_fd is None:
            return os.open(name, flags)
        return os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ReplayStateCorruption(
                f"replay namespace component {name!r} is a symlink; refusing to traverse"
            )
        if exc.errno == errno.ENOTDIR:
            raise ReplayStateCorruption(
                f"replay namespace component {name!r} is not a directory"
            )
        if exc.errno != errno.ENOENT or not create or parent_fd is None:
            raise ReplayStateCorruption(f"cannot open replay namespace {name!r}: {exc}")
    try:
        os.mkdir(name, _DIR_MODE, dir_fd=parent_fd)
    except FileExistsError:
        pass
    except OSError as exc:
        raise ReplayStateCorruption(f"cannot create replay namespace {name!r}: {exc}")
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise ReplayStateCorruption(f"cannot open replay namespace {name!r}: {exc}")


def _fsync_dir(dir_fd: int) -> None:
    """Flush a directory entry creation/rename/removal.

    Ordering matters: the entry must be on stable storage *before* the caller
    is told the reservation succeeded, because the caller is allowed to cross
    the ``MUTATION_ATTEMPT_STARTED`` boundary immediately afterwards.
    """
    try:
        os.fsync(dir_fd)
    except OSError:
        # Some filesystems reject fsync on a directory fd. The O_EXCL
        # mutual exclusion and the atomic rename are unaffected; only the
        # power-loss ordering guarantee weakens, which this module does not
        # claim unconditionally (see the class docstring).
        pass


class _DirChain:
    """Owns the open descriptor chain for one replay generation directory."""

    def __init__(self, protected_root: str, generation: int, *, create: bool) -> None:
        self._fds: List[int] = []
        root_fd = _open_dir(None, protected_root, create=False)
        self._fds.append(root_fd)
        try:
            ns_fd = _open_dir(root_fd, PAWA_HELPER_NAMESPACE, create=create)
            self._fds.append(ns_fd)
            replay_fd = _open_dir(ns_fd, REPLAY_NAMESPACE, create=create)
            self._fds.append(replay_fd)
            gen_fd = _open_dir(replay_fd, f"g{int(generation)}", create=create)
            self._fds.append(gen_fd)
        except Exception:
            self.close()
            raise
        self.fd = gen_fd

    def close(self) -> None:
        while self._fds:
            fd = self._fds.pop()
            try:
                os.close(fd)
            except OSError:
                pass


class DurableReplayStore:
    """Cross-process, crash-surviving §19 replay state under the existing
    protected-root trust boundary.

    Concurrency and crash behaviour, stated precisely (no overclaiming):

    * **Reservation is atomic, not check-then-create.** The complete record is
      written and fsynced to a private temp name, then published into its slot
      with ``link()``. POSIX requires ``link`` to fail ``EEXIST`` if the target
      exists, atomically with respect to other linkers of the same name in the
      same directory: exactly one racer's ``link`` succeeds, every other racer
      gets ``EEXIST``. There is no window in which two processes both believe
      the request is ``FRESH``.

      This is stronger than claiming the slot with a bare
      ``open(O_CREAT|O_EXCL)``, which publishes the *name* before the
      *content* and so lets a racing reader observe an empty file — a real
      race this module's concurrency tests caught. Publishing by ``link``
      makes the slot atomic in content as well as in existence.
    * **State updates are atomic, not in-place.** A transition writes a fresh
      temporary file in the *same* directory and ``os.replace``s it over the
      record. A crash mid-update therefore leaves either the whole old record
      or the whole new one — never a torn or half-written record that would
      read back as corruption.
    * **Process-crash survival is verified.** ``fsync`` is called on the
      record descriptor before it is exposed, and on the directory descriptor
      after the entry appears. This module's tests prove survival across real
      ``SIGKILL`` and across ordinary process exit, by separate OS processes.
    * **Power-loss survival is NOT claimed.** ``fsync`` returning success only
      means the kernel handed the data to the device; whether the device
      honours cache-flush barriers is outside anything this module can verify,
      and directory ``fsync`` is best-effort here (see :func:`_fsync_dir`).
      The honest guarantee is: *atomic against concurrent helper processes,
      and durable across process death*.
    """

    def __init__(
        self,
        *,
        protected_root: str,
        installation_id: str,
        generation: int,
        create: bool = True,
    ) -> None:
        self.protected_root = str(protected_root)
        self.installation_id = str(installation_id)
        self.generation = int(generation)
        self._create = bool(create)
        chain = _DirChain(self.protected_root, self.generation, create=self._create)
        try:
            st = os.fstat(chain.fd)
            if stat.S_IMODE(st.st_mode) & (stat.S_IWGRP | stat.S_IWOTH):
                raise ReplayStateCorruption(
                    "replay namespace is group/other-writable; refusing to use it"
                )
            if st.st_uid != os.getuid():
                raise ReplayStateCorruption(
                    "replay namespace is not owned by the current (deployment-owner) uid"
                )
        except Exception:
            chain.close()
            raise
        self._chain = chain

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        self._chain.close()

    def __enter__(self) -> "DurableReplayStore":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    # -- internals ---------------------------------------------------------

    def _key(self, request: HelperRequest) -> str:
        return compute_replay_key(
            installation_id=self.installation_id,
            generation=self.generation,
            request_id=request.request_id,
            nonce=request.nonce,
        )

    def _name(self, key: str) -> str:
        return f"{key}.json"

    def _read(self, key: str) -> Optional[ReplayRecord]:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(self._name(key), flags, dir_fd=self._chain.fd)
        except FileNotFoundError:
            return None
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise ReplayStateCorruption("replay record slot is a symlink; refusing to read")
            raise ReplayStateCorruption(f"cannot read replay record: {exc}")
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise ReplayStateCorruption("replay record slot is not a regular file")
            if st.st_uid != os.getuid():
                raise ReplayStateCorruption(
                    "replay record is not owned by the current (deployment-owner) uid"
                )
            if stat.S_IMODE(st.st_mode) & (stat.S_IWGRP | stat.S_IWOTH):
                raise ReplayStateCorruption(
                    "replay record is group/other-writable; refusing to trust it"
                )
            chunks = []
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(fd)
        blob = b"".join(chunks)
        try:
            raw = json.loads(blob.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReplayStateCorruption(f"replay record is not valid JSON: {exc}")
        return _validate_record(raw, expected_key=key)

    def _write_temp(self, record: Mapping[str, object]) -> str:
        """Write a complete, fsynced record to a fresh private temp name in
        the same directory. Returns the temp name."""
        temp_name = f".{os.getpid()}.{os.urandom(12).hex()}.tmp"
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(temp_name, flags, _FILE_MODE, dir_fd=self._chain.fd)
        except OSError as exc:
            raise ReplayStateCorruption(f"cannot stage replay record: {exc}")
        try:
            os.write(fd, json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)
        return temp_name

    def _unlink_quietly(self, name: str) -> None:
        try:
            os.unlink(name, dir_fd=self._chain.fd)
        except OSError:
            pass

    def _write_new(self, key: str, record: Mapping[str, object]) -> bool:
        """Atomically claim ``key``. Returns False iff the slot already
        existed — the single, race-free reservation point.

        The record is written **complete and fsynced to a private temp name
        first**, then published with ``link()``, which fails ``EEXIST`` if the
        slot is taken. This is deliberately not a bare
        ``open(O_CREAT|O_EXCL)`` on the final name: that publishes the *name*
        before the *content*, so a racing helper process could read the slot
        in the window between create and write and see an empty file — which
        this module (correctly) treats as corruption. Publishing by ``link``
        makes the slot atomic in content as well as in existence: any process
        that can see the name can read a whole, valid record.
        """
        temp_name = self._write_temp(record)
        try:
            os.link(
                temp_name,
                self._name(key),
                src_dir_fd=self._chain.fd,
                dst_dir_fd=self._chain.fd,
            )
        except FileExistsError:
            self._unlink_quietly(temp_name)
            return False
        except OSError as exc:
            self._unlink_quietly(temp_name)
            raise ReplayStateCorruption(f"cannot publish replay reservation: {exc}")
        self._unlink_quietly(temp_name)
        _fsync_dir(self._chain.fd)
        return True

    def _replace(self, key: str, record: Mapping[str, object]) -> None:
        """Atomically overwrite ``key`` via same-directory temp + rename, so a
        reader never observes a torn or half-updated record."""
        temp_name = self._write_temp(record)
        try:
            os.replace(
                temp_name, self._name(key), src_dir_fd=self._chain.fd, dst_dir_fd=self._chain.fd
            )
        except Exception:
            self._unlink_quietly(temp_name)
            raise
        _fsync_dir(self._chain.fd)

    # -- §19 dispositions --------------------------------------------------

    def check_and_reserve(
        self, request: HelperRequest, *, now: Optional[datetime] = None
    ) -> ReplayOutcome:
        """The single §19 admission decision, durable across processes.

        Mirrors :meth:`ReplayLedger.check_and_mark_in_flight`'s contract
        exactly — same :class:`ReplayOutcome` vocabulary, same conjuncts —
        but the state it consults survives the one-shot helper process.
        """
        if (
            request.installation_id != self.installation_id
            or int(request.generation) != self.generation
        ):
            # The request is bound to a different installation/generation than
            # this helper's replay namespace, so this store holds no history
            # that could speak for it. Returning FRESH here would let a
            # rotation G -> G+1 resurrect a request already spent under G
            # (spec §26: "rotation/revocation must fail closed for outstanding
            # operations"), so a binding mismatch is a CONFLICTING replay, not
            # a new request. The correct forward path is a new request bound to
            # the current generation.
            return ReplayOutcome.CONFLICTING

        moment = now or _now()
        expiry = parse_expiry(request.expiry)
        if expiry is None or moment > expiry:
            # An unparseable expiry is treated as expired, never as "no
            # deadline" (HPAC-PAWA-HELPER-REQ-074 fail-closed).
            return ReplayOutcome.EXPIRED

        key = self._key(request)
        existing = self._read(key)  # raises ReplayStateCorruption, never returns junk
        if existing is None:
            stamp = _rfc3339(moment)
            candidate = ReplayRecord(
                replay_key=key,
                installation_id=self.installation_id,
                generation=self.generation,
                request_id=request.request_id,
                nonce=request.nonce,
                operation=request.operation,
                session_id=request.session_id,
                subject=request_subject(request),
                request_digest=request.request_digest,
                expiry=request.expiry,
                durable_state=DurableReplayState.REQUEST_RECEIVED.value,
                reserved_at=stamp,
                updated_at=stamp,
                owner_pid=os.getpid(),
            )
            if self._write_new(key, candidate.to_mapping()):
                return ReplayOutcome.FRESH
            # Lost the O_EXCL race to a concurrent helper process. Re-read
            # and fall through to the same disposition logic the loser would
            # have taken had it arrived second in the first place.
            existing = self._read(key)
            if existing is None:  # pragma: no cover - only if the winner unlinked in between
                raise ReplayStateCorruption("replay slot vanished during reservation race")

        if (
            existing.operation != request.operation
            or existing.session_id != request.session_id
            or existing.subject != request_subject(request)
            or existing.request_digest != request.request_digest
        ):
            return ReplayOutcome.CONFLICTING
        if existing.is_spent:
            return ReplayOutcome.CONSUMED
        return ReplayOutcome.DUPLICATE_IN_FLIGHT

    def transition(
        self,
        request: HelperRequest,
        target: DurableReplayState,
        *,
        evidence_ref: Optional[str] = None,
        committed_digest: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> ReplayRecord:
        """Durably advance a reserved request's state. Forward-only; an
        illegal transition fails closed rather than rewriting history."""
        key = self._key(request)
        existing = self._read(key)
        if existing is None:
            raise ReplayStateCorruption(
                "cannot transition a replay record that was never reserved"
            )
        allowed = _LEGAL_TRANSITIONS[existing.durable_state]
        if target.value not in allowed:
            raise ReplayStateCorruption(
                f"illegal durable replay transition {existing.durable_state} -> {target.value}"
            )
        updated = ReplayRecord(
            replay_key=existing.replay_key,
            installation_id=existing.installation_id,
            generation=existing.generation,
            request_id=existing.request_id,
            nonce=existing.nonce,
            operation=existing.operation,
            session_id=existing.session_id,
            subject=existing.subject,
            request_digest=existing.request_digest,
            expiry=existing.expiry,
            durable_state=target.value,
            evidence_ref=evidence_ref if evidence_ref is not None else existing.evidence_ref,
            committed_digest=(
                committed_digest if committed_digest is not None else existing.committed_digest
            ),
            reserved_at=existing.reserved_at,
            updated_at=_rfc3339(now or _now()),
            owner_pid=existing.owner_pid,
        )
        self._replace(key, updated.to_mapping())
        return updated

    def release_reservation(self, request: HelperRequest) -> bool:
        """Release a reservation that never crossed ``MUTATION_ATTEMPT_STARTED``
        (HPAC-PAWA-HELPER-REQ-083 'no protected-root effect').

        Two guards make this unusable as a replay reset:

        * a record in any **spent** state is never removed — this method
          returns False and leaves it in place, so a consumed request stays
          consumed for ever;
        * only the process that *holds* the reservation may release it
          (``owner_pid`` must match), so one helper process cannot clear
          another's in-flight slot.
        """
        key = self._key(request)
        existing = self._read(key)
        if existing is None:
            return False
        if existing.is_spent:
            return False
        if existing.owner_pid != os.getpid():
            return False
        try:
            os.unlink(self._name(key), dir_fd=self._chain.fd)
        except FileNotFoundError:
            return False
        _fsync_dir(self._chain.fd)
        return True

    # -- reconciliation / retention ---------------------------------------

    def read_record(self, request: HelperRequest) -> Optional[ReplayRecord]:
        """Reconciliation read (§21/§84): what the durable store says about a
        request. Returns a validated record or None; corruption raises."""
        return self._read(self._key(request))

    def iter_records(self) -> List[ReplayRecord]:
        """Every validated record in this generation. A corrupt entry raises
        rather than being skipped — silent skipping would be the replay hole."""
        records: List[ReplayRecord] = []
        for name in sorted(os.listdir(self._chain.fd)):
            if name.startswith(".") or not name.endswith(".json"):
                continue
            key = name[: -len(".json")]
            record = self._read(key)
            if record is not None:
                records.append(record)
        return records

    def prune_expired(
        self, *, retention: timedelta, now: Optional[datetime] = None
    ) -> Tuple[int, int]:
        """Retention (§19): drop records whose ``expiry`` is older than
        ``retention``.

        This is safe precisely because expiry is checked **before** the store
        is consulted: once a request is past ``expiry`` it is denied as
        ``EXPIRED`` whether or not a record survives, so removing it cannot
        revive it. Records still within ``expiry + retention`` are always
        kept, and a record in ``RECONCILIATION_REQUIRED`` is **never** pruned
        — an unreconciled indeterminate outcome must stay visible to the
        deployment owner indefinitely.

        This is an out-of-band, deployment-owner maintenance operation. It is
        **not reachable from any of the five closed operations** — no request
        field, ``operation_params`` shape, or dispatch handler calls it.

        Returns ``(pruned, retained)``.
        """
        moment = now or _now()
        pruned = 0
        retained = 0
        for record in self.iter_records():
            expiry = parse_expiry(record.expiry)
            if (
                record.durable_state == DurableReplayState.RECONCILIATION_REQUIRED.value
                or expiry is None
                or moment <= expiry + retention
            ):
                retained += 1
                continue
            try:
                os.unlink(self._name(record.replay_key), dir_fd=self._chain.fd)
                pruned += 1
            except FileNotFoundError:  # pragma: no cover - concurrent prune
                pass
        if pruned:
            _fsync_dir(self._chain.fd)
        return pruned, retained


def record_exports_no_authority(record: ReplayRecord) -> bool:
    """True iff nothing in a durable record looks like exported authority
    (§24 / PAWAH-INV-10). Used by production code as defence in depth and by
    the tests as the persistent-history-is-not-revived-authority proof."""
    for name, value in record.to_mapping().items():
        if any(token in str(name).lower() for token in FORBIDDEN_AUTHORITY_TOKENS):
            return False
        if isinstance(value, str) and any(
            token in value.lower() for token in FORBIDDEN_AUTHORITY_TOKENS
        ):
            return False
    return True


def open_durable_replay_ledger(
    *, protected_root: str, installation_id: str, generation: int
):
    """Production entry point: a :class:`ReplayLedger` backed by durable,
    cross-process state under ``<HPAC_PROTECTED_ROOT>/pawa-helper/replay/``.

    Helper wiring MUST construct its ledger through this function (or pass a
    :class:`DurableReplayStore` explicitly). A bare ``ReplayLedger()`` is the
    deterministic in-memory foundation only, and cannot enforce §19 across the
    one-shot helper process lifetime.
    """
    from pcae.core.hpac_pawa_helper_protocol import ReplayLedger

    return ReplayLedger(
        durable_store=DurableReplayStore(
            protected_root=protected_root,
            installation_id=installation_id,
            generation=generation,
        )
    )

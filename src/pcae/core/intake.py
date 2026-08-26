"""Phase 149O.20L.7O.2U.2 -- Reference Adapter Intake (implements the
generic diff/JSON contract frozen in Phase 149O.20L.7O.2U.1).

Hard invariant, enforced throughout this module: received != validated !=
authorized != permitted != promoted != executed. An accepted Intake
Candidate becomes evidence only -- an ExecutionChangePackage (ECP) with
execution_allowed=False and promotion_executed=False, identical in shape
to an ECP captured from PCAE's own sandboxed execution-activation path.
No field read from a submitted candidate document is ever copied into an
authorization- or promotion-bearing field. promotion_authorized is set
only by a human via `pcae promotion-review create --promotion-authorized`,
a separate command this module never calls and cannot influence.

This module does not replace or modify execution-activation,
execution-snapshot, execution-change, promotion-review, promote, or
rollback. It only adds a second, additive way to produce an
ECP-compatible artifact -- from an externally-supplied diff instead of
from PCAE's own sandboxed run -- reusing the existing ECP store,
task-scope allow-list check, and file-exclusion classification
unchanged.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from pcae.core import agent as agent_core
from pcae.core.check import path_matches_any
from pcae.core.paths import HarnessPath
from pcae.core.tasks import find_latest_active_task

INTAKE_CONTRACT_VERSION: str = "1.0"
SUPPORTED_INTAKE_VERSIONS: frozenset[str] = frozenset({"1.0"})

_INTAKE_STORE_DIR: Path = Path(".pcae") / "intake-candidates"
_INTAKE_GIT_TIMEOUT_SECONDS: float = 10.0
_VALID_OPERATIONS: frozenset[str] = frozenset({"modify", "create", "delete"})

INTAKE_ADVISORY: str = (
    "Intake Candidates are evidence only. received != validated != authorized "
    "!= permitted != promoted != executed. Accepting a candidate never sets "
    "promotion_authorized or execution_allowed; those remain False on every "
    "artifact this module produces. Promotion still requires a separate, "
    "explicit human `pcae promotion-review create --promotion-authorized` "
    "followed by `pcae promote`, unchanged."
)


# ---------------------------------------------------------------------------
# Repo / base-commit binding
# ---------------------------------------------------------------------------

def compute_repo_fingerprint(root: HarnessPath) -> str | None:
    """SHA256 of this repository's sorted root-commit hash(es). Stable across
    clones/forks of the same history; used to reject a candidate diff that
    was computed against a different repository."""
    try:
        proc = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True, timeout=_INTAKE_GIT_TIMEOUT_SECONDS,
            shell=False, cwd=str(root.path),
        )
        if proc.returncode != 0:
            return None
        roots = sorted(
            line.strip() for line in proc.stdout.decode("utf-8", errors="replace").splitlines() if line.strip()
        )
        if not roots:
            return None
        return hashlib.sha256("|".join(roots).encode("utf-8")).hexdigest()
    except Exception:
        return None


def _commit_exists(root: HarnessPath, commit: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            capture_output=True, timeout=_INTAKE_GIT_TIMEOUT_SECONDS,
            shell=False, cwd=str(root.path),
        )
        return proc.returncode == 0
    except Exception:
        return False


def _commit_is_ancestor_or_equal_head(root: HarnessPath, commit: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            capture_output=True, timeout=_INTAKE_GIT_TIMEOUT_SECONDS,
            shell=False, cwd=str(root.path),
        )
        return proc.returncode == 0
    except Exception:
        return False


def _read_blob_at_commit(root: HarnessPath, commit: str, path: str) -> bytes | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            capture_output=True, timeout=_INTAKE_GIT_TIMEOUT_SECONDS,
            shell=False, cwd=str(root.path),
        )
        if proc.returncode != 0:
            return None
        return proc.stdout
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Path safety (independent of, and stricter than, ECP's exclusion bookkeeping)
# ---------------------------------------------------------------------------

def _path_is_safe_relative(path_text: object) -> bool:
    """Reject anything that is not a clean repo-relative POSIX path: no
    absolute paths, no '..' components, no empty/NUL/backslash content.
    This is admission control -- a failure here rejects the whole intake
    candidate rather than merely excluding one file entry, because a
    traversal attempt is a security signal, not an ordinary scope miss."""
    if not isinstance(path_text, str) or not path_text:
        return False
    if "\x00" in path_text:
        return False
    if path_text.startswith("/") or path_text.startswith("\\"):
        return False
    if ":" in path_text.split("/")[0] and len(path_text.split("/")[0]) == 2:
        return False  # e.g. "C:\..." on a case where '/' wasn't normalized
    parts = path_text.replace("\\", "/").split("/")
    if any(part in ("..", "") for part in parts[:-1]):
        return False
    if parts[-1] in ("..", ""):
        return False
    if any(part == "." for part in parts):
        return False
    return True


# ---------------------------------------------------------------------------
# Intake record store (audit trail of every submission, accepted or not)
# ---------------------------------------------------------------------------

def _record_integrity_payload(record: dict) -> dict:
    return {k: v for k, v in record.items() if k != "record_integrity_hash"}


def compute_record_integrity_hash(record: dict) -> str:
    payload = _record_integrity_payload(record)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_record_integrity(record: dict) -> bool:
    stored_hash = record.get("record_integrity_hash")
    if not isinstance(stored_hash, str) or not stored_hash:
        return False
    return compute_record_integrity_hash(record) == stored_hash


def _store_intake_record(root: HarnessPath, record: dict) -> str:
    store_dir = root.path / _INTAKE_STORE_DIR
    store_dir.mkdir(parents=True, exist_ok=True)
    record = dict(record)
    record["record_integrity_hash"] = compute_record_integrity_hash(record)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    filename = f"{record['intake_id']}-{ts}.json"
    path = store_dir / filename
    path.write_text(json.dumps(record, indent=2, sort_keys=True))
    return str(path)


def lookup_intake_record(root: HarnessPath, intake_id: str) -> dict | None:
    store_dir = root.path / _INTAKE_STORE_DIR
    if not store_dir.exists():
        return None
    matches = sorted(store_dir.glob(f"{intake_id}-*.json"), reverse=True)
    for match in matches:
        try:
            record = json.loads(match.read_text())
        except Exception:
            continue
        record["integrity_verified"] = verify_record_integrity(record)
        return record
    return None


def list_intake_records(root: HarnessPath, task_id: str | None = None) -> list[dict]:
    store_dir = root.path / _INTAKE_STORE_DIR
    if not store_dir.exists():
        return []
    records: list[dict] = []
    for path in sorted(store_dir.glob("intake-*.json"), reverse=True):
        try:
            record = json.loads(path.read_text())
        except Exception:
            continue
        if task_id is not None and record.get("task_id") != task_id:
            continue
        record["integrity_verified"] = verify_record_integrity(record)
        records.append(record)
    return records


def _find_accepted_record_by_candidate_id(root: HarnessPath, candidate_id: str) -> dict | None:
    store_dir = root.path / _INTAKE_STORE_DIR
    if not store_dir.exists():
        return None
    for path in sorted(store_dir.glob(f"intake-*.json")):
        try:
            record = json.loads(path.read_text())
        except Exception:
            continue
        if record.get("candidate_id") == candidate_id and record.get("validation_outcome") == "accepted":
            return record
    return None


# ---------------------------------------------------------------------------
# Candidate validation and ECP construction
# ---------------------------------------------------------------------------

def _reject(candidate_id: str | None, task_id: str | None, reasons: list[str], root: HarnessPath) -> dict:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    intake_id = f"intake-{task_id or 'unknown'}-{ts}"
    record = {
        "intake_id": intake_id,
        "intake_contract_version": INTAKE_CONTRACT_VERSION,
        "candidate_id": candidate_id,
        "task_id": task_id,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "validation_outcome": "rejected",
        "rejection_reasons": reasons,
        "ecp_id": None,
        "execution_allowed": False,
        "promotion_executed": False,
    }
    stored_path = _store_intake_record(root, record)
    return {
        "accepted": False,
        "intake_id": intake_id,
        "ecp_id": None,
        "rejection_reasons": reasons,
        "stored_path": stored_path,
        "execution_allowed": False,
        "promotion_executed": False,
        "advisory": INTAKE_ADVISORY,
    }


def validate_and_ingest_intake_candidate(root: HarnessPath, candidate: object) -> dict:
    """Validate an Intake Candidate document (already-parsed JSON value) and,
    if it passes every fail-closed check, construct and store an
    ECP-compatible artifact via the existing ECP store. Always returns a
    dict and always writes an audit record -- rejection is never silent.

    No field of `candidate` is ever forwarded into an authorization- or
    promotion-bearing field. Rejections never set execution_allowed or
    promotion_executed; neither does acceptance."""
    if not isinstance(candidate, dict):
        return _reject(None, None, ["malformed_candidate_not_an_object"], root)

    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        return _reject(None, None, ["missing_candidate_id"], root)

    version = candidate.get("intake_contract_version")
    if version not in SUPPORTED_INTAKE_VERSIONS:
        return _reject(candidate_id, None, [f"unsupported_schema_version:{version!r}"], root)

    task_context = candidate.get("task_context")
    if not isinstance(task_context, dict):
        return _reject(candidate_id, None, ["missing_task_context"], root)
    task_id = task_context.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        return _reject(candidate_id, None, ["missing_task_id"], root)

    # Idempotency / ID-collision handling -- checked before any further
    # validation so a resubmission of an already-accepted candidate never
    # re-derives a different outcome from a since-changed repo state.
    existing = _find_accepted_record_by_candidate_id(root, candidate_id)
    if existing is not None:
        existing_hash = existing.get("candidate_content_hash")
        this_hash = _hash_candidate_content(candidate)
        if existing_hash == this_hash:
            return {
                "accepted": True,
                "intake_id": existing["intake_id"],
                "ecp_id": existing.get("ecp_id"),
                "idempotent_replay": True,
                "rejection_reasons": [],
                "execution_allowed": False,
                "promotion_executed": False,
                "advisory": INTAKE_ADVISORY,
            }
        return _reject(
            candidate_id, task_id,
            ["candidate_id_collision_conflicting_content"],
            root,
        )

    reasons: list[str] = []

    active_task = find_latest_active_task(root)
    if active_task is None or active_task.task_id != task_id:
        return _reject(candidate_id, task_id, ["task_not_active"], root)

    repo_binding = candidate.get("repo_binding")
    if not isinstance(repo_binding, dict):
        return _reject(candidate_id, task_id, ["missing_repo_binding"], root)
    declared_fingerprint = repo_binding.get("repo_fingerprint")
    actual_fingerprint = compute_repo_fingerprint(root)
    if not declared_fingerprint or declared_fingerprint != actual_fingerprint:
        return _reject(candidate_id, task_id, ["repo_binding_mismatch"], root)

    base_commit = repo_binding.get("base_commit")
    if not isinstance(base_commit, str) or not base_commit:
        return _reject(candidate_id, task_id, ["missing_base_commit"], root)
    if not _commit_exists(root, base_commit):
        return _reject(candidate_id, task_id, ["invalid_base_commit"], root)
    if not _commit_is_ancestor_or_equal_head(root, base_commit):
        return _reject(candidate_id, task_id, ["base_commit_not_ancestor_of_head"], root)

    proposed_changes = candidate.get("proposed_changes")
    if not isinstance(proposed_changes, list) or not proposed_changes:
        return _reject(candidate_id, task_id, ["missing_proposed_changes"], root)

    file_entries: list[dict] = []
    seen_paths: set[str] = set()
    for change in proposed_changes:
        if not isinstance(change, dict):
            return _reject(candidate_id, task_id, ["malformed_proposed_change"], root)

        path_text = change.get("path")
        if not _path_is_safe_relative(path_text):
            return _reject(candidate_id, task_id, [f"path_traversal_or_absolute_path:{path_text!r}"], root)
        if path_text in seen_paths:
            return _reject(candidate_id, task_id, [f"duplicate_path_in_candidate:{path_text}"], root)
        seen_paths.add(path_text)

        operation = change.get("operation")
        if operation not in _VALID_OPERATIONS:
            return _reject(candidate_id, task_id, [f"invalid_operation:{operation!r}"], root)

        if not path_matches_any(Path(path_text), active_task.allowed_files):
            return _reject(candidate_id, task_id, [f"out_of_scope_path:{path_text}"], root)

        before_data = _read_blob_at_commit(root, base_commit, path_text)
        before_hash = hashlib.sha256(before_data).hexdigest() if before_data is not None else None

        if operation == "delete":
            after_data = None
            after_hash = None
            declared_hash = change.get("content_hash_after")
            if declared_hash is not None:
                return _reject(candidate_id, task_id, [f"delete_must_not_declare_content_hash:{path_text}"], root)
        else:
            content_after = change.get("content_after")
            declared_hash = change.get("content_hash_after")
            if not isinstance(content_after, str):
                return _reject(candidate_id, task_id, [f"missing_content_after:{path_text}"], root)
            if not isinstance(declared_hash, str) or not declared_hash:
                return _reject(candidate_id, task_id, [f"missing_content_hash_after:{path_text}"], root)
            after_data = content_after.encode("utf-8")
            after_hash = hashlib.sha256(after_data).hexdigest()
            if after_hash != declared_hash:
                return _reject(candidate_id, task_id, [f"hash_mismatch:{path_text}"], root)

        gitignored_set = agent_core._ecp_compute_gitignored(root, [path_text])
        binary = agent_core._ecp_is_binary(after_data) or agent_core._ecp_is_binary(before_data)
        symlink = False
        external_target = None
        gitignored = path_text in gitignored_set
        after_size = len(after_data) if after_data is not None else None
        promotion_eligible, exclusion_reason = agent_core._ecp_classify_exclusion(
            path_text, symlink, external_target, gitignored, binary, after_size,
        )

        diff_text = None
        content = after_data.decode("utf-8", errors="replace") if after_data is not None else None
        before_content = before_data.decode("utf-8", errors="replace") if before_data is not None else None

        file_entries.append({
            "path": path_text,
            "change_type": {"modify": "modified", "create": "added", "delete": "deleted"}[operation],
            "before_exists": before_data is not None,
            "after_exists": after_data is not None,
            "before_hash": before_hash,
            "after_hash": after_hash,
            "diff": diff_text,
            "content": content,
            "before_content": before_content,
            "binary": binary,
            "symlink": symlink,
            "external_target": external_target,
            "gitignored": gitignored,
            "promotion_eligible": promotion_eligible,
            "exclusion_reason": exclusion_reason,
        })

    declared_goal = task_context.get("declared_goal")
    producer = candidate.get("producer") if isinstance(candidate.get("producer"), dict) else {}
    producer_claims = candidate.get("producer_claims") if isinstance(candidate.get("producer_claims"), dict) else {}

    captured_at = datetime.now(timezone.utc).isoformat()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    ecp_id = f"ecp-intake-{task_id}-{ts}"
    excluded = [e for e in file_entries if not e["promotion_eligible"]]
    manifest_hash = hashlib.sha256(
        "|".join(f"{e['path']}:{e['after_hash'] or ''}" for e in sorted(file_entries, key=lambda e: e["path"]))
        .encode("utf-8")
    ).hexdigest() if file_entries else None

    ecp_record = {
        "ecp_id": ecp_id,
        "ecp_version": agent_core._ECP_VERSION,
        "prompt_id": f"intake:{task_id}",
        "authorization_id": f"intake-no-ear:{candidate_id}",
        "audit_id": f"intake-no-audit:{candidate_id}",
        "execution_result_id": f"intake-no-err:{candidate_id}",
        "snapshot_id": None,
        "change_record_id": None,
        "captured_at": captured_at,
        "capture_source": "intake_candidate",
        "capture_outcome": "success",
        "sandbox_id": None,
        "sandbox_provider": None,
        "pre_git_head": base_commit,
        "post_git_head": None,
        "git_head_diverged": False,
        "git_commit_detected": False,
        "esa_available": False,
        "absolute_path_writes_detected": False,
        "manifest_hash": manifest_hash,
        "file_count": len(file_entries),
        "file_entries": file_entries,
        "capture_errors": [],
        "binary_file_count": sum(1 for e in file_entries if e["binary"]),
        "symlink_count": 0,
        "external_symlink_count": 0,
        "excluded_file_count": len(excluded),
        "excluded_paths": [e["path"] for e in excluded],
        "promotion_eligible_count": len(file_entries) - len(excluded),
        "execution_allowed": False,
        "promotion_executed": False,
        "rollback_executed": False,
        "intake_producer": dict(producer),
        "intake_producer_claims": dict(producer_claims),
        "intake_candidate_id": candidate_id,
    }

    stored = agent_core.store_execution_change_package(root, ecp_record)
    if not stored.get("stored"):
        return _reject(candidate_id, task_id, [f"ecp_store_failed:{e}" for e in stored.get("errors", [])], root)

    ts2 = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    intake_id = f"intake-{task_id}-{ts2}"
    record = {
        "intake_id": intake_id,
        "intake_contract_version": INTAKE_CONTRACT_VERSION,
        "candidate_id": candidate_id,
        "candidate_content_hash": _hash_candidate_content(candidate),
        "task_id": task_id,
        "declared_goal": declared_goal,
        "producer": dict(producer),
        "producer_claims": dict(producer_claims),
        "repo_fingerprint": actual_fingerprint,
        "base_commit": base_commit,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "validation_outcome": "accepted",
        "rejection_reasons": [],
        "ecp_id": ecp_id,
        "file_count": len(file_entries),
        "promotion_eligible_count": len(file_entries) - len(excluded),
        "execution_allowed": False,
        "promotion_executed": False,
    }
    stored_path = _store_intake_record(root, record)

    return {
        "accepted": True,
        "intake_id": intake_id,
        "ecp_id": ecp_id,
        "idempotent_replay": False,
        "rejection_reasons": [],
        "file_count": len(file_entries),
        "promotion_eligible_count": len(file_entries) - len(excluded),
        "stored_path": stored_path,
        "execution_allowed": False,
        "promotion_executed": False,
        "advisory": INTAKE_ADVISORY,
    }


def _hash_candidate_content(candidate: dict) -> str:
    canonical = json.dumps(candidate, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Generic producer-neutral candidate construction (Phase 149O.20L.7O.2W)
#
# This section is the single shared implementation of the logic every
# intake producer needs (repo/base binding, content hashing, generic
# candidate assembly) and the one place producer provenance is derived
# from PCAE governance session state. It supersedes the duplicated logic
# that used to live only in the reference producer adapter script under
# scripts/.
#
# Hard invariant carried over unchanged from the rest of this module:
# producer provenance is descriptive metadata only. It is never read by
# validate_and_ingest_intake_candidate for any allow/deny/authority
# decision -- see that function above, which never inspects
# candidate["producer"] except to copy it verbatim into the stored ECP
# and intake record for audit purposes.
# ---------------------------------------------------------------------------

FROM_FILES_ADAPTER_VERSION: str = "2W-generic-from-files-1"


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_file_change_spec(raw: str) -> dict:
    """Parse a `path:operation[:content_file]` spec (the same shape the
    reference producer adapter used) into a `proposed_changes` entry
    using this module's own operation vocabulary (_VALID_OPERATIONS) --
    no new operations are introduced."""
    parts = raw.split(":", 2)
    if len(parts) < 2:
        raise ValueError(f"invalid file spec (need path:operation[:content_file]): {raw!r}")
    path, operation = parts[0], parts[1]
    if operation not in _VALID_OPERATIONS:
        raise ValueError(
            f"invalid operation {operation!r} in file spec {raw!r}; "
            f"must be one of: {', '.join(sorted(_VALID_OPERATIONS))}"
        )
    if operation == "delete":
        return {"path": path, "operation": "delete"}
    if len(parts) != 3:
        raise ValueError(f"file spec for operation {operation!r} needs a content file: {raw!r}")
    content = Path(parts[2]).read_text(encoding="utf-8")
    return {
        "path": path,
        "operation": operation,
        "content_after": content,
        "content_hash_after": compute_content_hash(content),
    }


def current_head_commit(root: HarnessPath) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, timeout=_INTAKE_GIT_TIMEOUT_SECONDS,
            shell=False, cwd=str(root.path),
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.decode("utf-8", errors="replace").strip() or None
    except Exception:
        return None


def derive_producer_provenance(
    root: HarnessPath, explicit_producer_kind: str | None = None,
) -> tuple[dict | None, list[str]]:
    """Determine `producer.kind` for a generic from-files submission.

    Primary source: `agent_core.read_agent_lock(root)` -- the PCAE
    governance agent lock (`.pcae/agent-lock.json`). It is the correct
    source for descriptive governance-session provenance because (a) it
    accepts arbitrary caller-supplied agent identities the same way this
    helper needs to, unlike the narrower six-name backend/session-lock
    vocabulary in `.pcae/agent-locks/latest.json`, which is
    execution/backend-oriented rather than governance-session-oriented;
    and (b) it is the one identity PCAE already records for the current
    session, so an operator should not need to repeat it via a flag.

    - Governance lock active, no explicit producer given: derive from the
      lock. producer_source = "agent_lock".
    - Governance lock active, explicit producer given and it matches the
      lock's agent_id: no-op consistent, derive from the lock.
    - Governance lock active, explicit producer given and it conflicts:
      reject deterministically. This is provenance-consistency handling,
      not an authority decision -- the caller must resolve the conflict
      (drop --producer, or release/re-acquire the lock) rather than have
      the helper silently pick a side.
    - No governance lock: preserve the v0.3 external/unbootstrapped
      compatibility path -- require an explicit producer (never invent
      "unknown"). producer_source = "candidate".
    - Governance lock file present but malformed (invalid JSON / unreadable,
      or well-formed JSON that is not an object -- an array, string,
      number, boolean, or null): reject deterministically rather than
      raising or silently falling through to the no-lock path -- a
      corrupted lock file is a distinct, fail-closed condition from "no
      lock was ever acquired", and treating it as the latter would
      silently accept an --producer value the operator may not have
      intended once the real lock is repaired.
      (Phase 149O.20L.7O.2Y bounded hardening of a 2W.1 NON-BLOCKING
      finding: this function's own docstring/callers assume it never
      raises for ordinary input problems; a malformed lock file is an
      ordinary, user-reachable input problem. Phase 149O.20L.7O.2Z
      extends this same handling to well-formed-JSON-but-wrong-type lock
      payloads, independently found during release-candidate
      verification to still raise an uncaught AttributeError -- valid
      JSON that decodes to a non-dict value passes `read_agent_lock`
      without error, so the crash previously occurred one line later, at
      `lock.agent_id`, outside the original try/except.)
    """
    try:
        lock = agent_core.read_agent_lock(root)
    except (json.JSONDecodeError, OSError) as exc:
        return None, [f"malformed_agent_lock:{exc}"]
    if lock is not None:
        if not isinstance(lock.data, dict):
            return None, [
                "malformed_agent_lock:agent-lock.json must contain a JSON "
                f"object, got {type(lock.data).__name__}"
            ]
        lock_agent_id = lock.agent_id
        if explicit_producer_kind and explicit_producer_kind != lock_agent_id:
            return None, [
                "producer_conflicts_with_active_agent_lock:"
                f"explicit={explicit_producer_kind!r},lock={lock_agent_id!r}"
            ]
        return {"kind": lock_agent_id, "source": "agent_lock"}, []

    if not explicit_producer_kind:
        return None, ["no_active_agent_lock_and_no_explicit_producer_supplied"]
    return {"kind": explicit_producer_kind, "source": "candidate"}, []


def build_intake_candidate_from_files(
    root: HarnessPath,
    task_id: str,
    candidate_id: str,
    file_specs: list[str],
    summary: str = "",
    self_reported_complete: bool = False,
    explicit_producer_kind: str | None = None,
    adapter_version: str = FROM_FILES_ADAPTER_VERSION,
) -> dict:
    """Build a generic Intake Candidate document from a producer-neutral
    description of file changes, deriving repo/base binding, content
    hashes, and producer provenance the same way for every caller
    regardless of which tool produced the changes. Returns
    {"candidate": <doc>, "errors": []} on success or
    {"candidate": None, "errors": [...]} on failure -- never raises for
    ordinary input problems, matching this module's fail-closed style.

    This function never invokes any agent/tool; it only translates
    already-produced file changes into the frozen generic intake schema
    (Phase 149O.20L.7O.2U.1), then leaves submission to the caller via
    `validate_and_ingest_intake_candidate` / `pcae intake create`.
    """
    producer, producer_errors = derive_producer_provenance(root, explicit_producer_kind)
    if producer_errors:
        return {"candidate": None, "errors": producer_errors}

    try:
        proposed_changes = [parse_file_change_spec(spec) for spec in file_specs]
    except (ValueError, OSError) as exc:
        return {"candidate": None, "errors": [f"file_spec_error:{exc}"]}

    if not proposed_changes:
        return {"candidate": None, "errors": ["no_file_changes_supplied"]}

    fingerprint = compute_repo_fingerprint(root)
    base_commit = current_head_commit(root)
    if fingerprint is None or base_commit is None:
        return {"candidate": None, "errors": ["repo_binding_unavailable"]}

    candidate = {
        "intake_contract_version": INTAKE_CONTRACT_VERSION,
        "candidate_id": candidate_id,
        "producer": {
            "kind": producer["kind"],
            "source": producer["source"],
            "adapter_version": adapter_version,
        },
        "task_context": {
            "task_id": task_id,
            "declared_goal": summary,
        },
        "repo_binding": {
            "repo_fingerprint": fingerprint,
            "base_commit": base_commit,
        },
        "proposed_changes": proposed_changes,
        "producer_claims": {
            "summary": summary,
            "self_reported_complete": bool(self_reported_complete),
        },
    }
    return {"candidate": candidate, "errors": []}


def build_intake_candidate_from_changes(
    *,
    repository_fingerprint: str,
    base_commit: str,
    task_id: str,
    candidate_id: str,
    changed_files: list[dict],
    producer_kind: str,
    producer_source: str = "runtime_adapter",
    summary: str = "",
    adapter_version: str = "pcae.mock-dry/1.0",
) -> dict:
    """Phase 149O.20L.7O.3S -- RPAC-001 Stage B generic in-memory-change
    candidate builder (RPAC-REQ-080, RPAC-001 §15). Producer-neutral: no
    runtime-adapter-specific branch exists here, so this same function
    serves the mock adapter today and any future RPAC-conformant real
    adapter unchanged.

    Unlike `build_intake_candidate_from_files` above, this function reads
    no git state and calls no subprocess -- repository/base binding is
    supplied by the caller's already-authoritative binding (an
    `AuthoritySnapshot`, never adapter/runtime output; see
    `runtime_invocation.AuthoritySnapshot`), preserving the RPAC mock
    slice's zero-subprocess proof.

    It never calls `validate_and_ingest_intake_candidate` -- Stage B stops
    at producing a schema-correct candidate document only (RPAC-REQ-080/
    081). If `changed_files` is empty, it returns the explicit
    `not_applicable_no_changes` disposition rather than a fabricated
    candidate (RPAC-REQ-081)."""
    if not changed_files:
        return {"candidate": None, "disposition": "not_applicable_no_changes", "errors": []}

    proposed_changes: list[dict] = []
    for change in changed_files:
        entry = {"path": change["path"], "operation": change["operation"]}
        if change["operation"] != "delete":
            entry["content_after"] = change["content_after"]
            entry["content_hash_after"] = change["content_hash_after"]
        proposed_changes.append(entry)

    candidate = {
        "intake_contract_version": INTAKE_CONTRACT_VERSION,
        "candidate_id": candidate_id,
        "producer": {
            "kind": producer_kind,
            "source": producer_source,
            "adapter_version": adapter_version,
        },
        "task_context": {"task_id": task_id, "declared_goal": summary},
        "repo_binding": {
            "repo_fingerprint": repository_fingerprint,
            "base_commit": base_commit,
        },
        "proposed_changes": proposed_changes,
        "producer_claims": {"summary": summary, "self_reported_complete": False},
    }
    return {
        "candidate": candidate,
        "disposition": "candidate_built",
        "errors": [],
        "candidate_content_hash": _hash_candidate_content(candidate),
    }

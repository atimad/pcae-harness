"""
Runtime Invocation Approval Store — Phase 149O.20L.7O.3W.

Canonical, create-only, path-confined persistence for
`RuntimeInvocationApproval` documents (RIHAC-001 §15 / RIASC-001 §12):

    .pcae/runtime-invocation-approvals/v1/<approval_id>/approval.json

This is a separate store from `RuntimeInvocationStore`
(`runtime_invocation.py`, the pre-existing mock-v1 dry-path store) --
RIHAC-001 §15 forbids embedding the approval in CHGR or the invocation
record, and 3S.2.1's MUST-FIX #2 (path traversal via an unsanitized
`invocation_id`) is repaired-by-design here, not inherited: `approval_id`
is validated against the exact `^ria-[0-9a-f]{32}$` pattern *before* any
path is constructed from it, and no other caller-supplied string is ever
used to build a path.

Uses directory-relative, no-follow, create-exclusive filesystem operations
so an adversarial pre-created symlink or hardlink cannot redirect a write.
No `subprocess`, no network, no credential access.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from .runtime_authority import (
    AdapterBinding,
    ApprovalProvenance,
    ApprovalScope,
    ApprovalSubject,
    ArtifactRef,
    FreshnessSnapshot,
    GovernanceContext,
    RuntimeInvocationApproval,
    is_valid_approval_id,
    validate_riasc_schema_shape,
)

STORE_ROOT = Path(".pcae") / "runtime-invocation-approvals" / "v1"


class ApprovalStoreIntegrityError(Exception):
    """Raised for any conflicting, corrupt, or malformed persisted
    approval, or for any caller-supplied identifier that fails path
    confinement. Callers must treat this as fail-closed: never auto-repair,
    never treat a partially-valid load as authority."""


class RuntimeInvocationApprovalStore:
    """Canonical approval store. Lookup is by `approval_id` only, resolved
    to the fixed canonical path -- never a caller-supplied arbitrary path
    (RIHAC-001 §15)."""

    def __init__(self, root: Path):
        self._repository_root = Path(root)
        self._root = self._repository_root / STORE_ROOT

    def _ensure_store_root(self, *, create: bool) -> bool:
        """Walk the canonical store path without following directory links."""
        try:
            root_stat = self._repository_root.lstat()
        except FileNotFoundError:
            if not create:
                return False
            raise ApprovalStoreIntegrityError("repository_root_missing")
        if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
            raise ApprovalStoreIntegrityError("repository_root_not_trusted_directory")

        current = self._repository_root
        for component in STORE_ROOT.parts:
            current = current / component
            try:
                entry_stat = current.lstat()
            except FileNotFoundError:
                if not create:
                    return False
                try:
                    current.mkdir(mode=0o700)
                except FileExistsError:
                    entry_stat = current.lstat()
                else:
                    entry_stat = current.lstat()
            if not stat.S_ISDIR(entry_stat.st_mode) or stat.S_ISLNK(entry_stat.st_mode):
                raise ApprovalStoreIntegrityError(f"untrusted_store_component:{component}")
        return True

    def _approval_dir(self, approval_id: str) -> Path:
        if not is_valid_approval_id(approval_id):
            raise ApprovalStoreIntegrityError(f"invalid_approval_id_pattern:{approval_id!r}")
        # `approval_id` is now proven to match `^ria-[0-9a-f]{32}$`: no
        # path separator, no "..", no leading "/" is representable by that
        # pattern, so confinement holds by construction, not by string
        # post-processing.
        return self._root / approval_id

    def _approval_path(self, approval_id: str) -> Path:
        return self._approval_dir(approval_id) / "approval.json"

    def create(self, approval: RuntimeInvocationApproval) -> None:
        """Create-only write. A second write to the same `approval_id` is
        always a hard integrity failure -- never a silent overwrite and
        never an idempotent no-op, even with byte-identical content
        (RIHAC-001 §1: approvals are immutable one-shot human acts, not
        replayable requests; RIASC-001 §9 has no mutable `consumed` field
        to make "same content" a meaningful resume signal)."""
        approval_dir = self._approval_dir(approval.approval_id)
        document = approval.to_dict()
        issues = validate_riasc_schema_shape(document)
        if issues:
            raise ApprovalStoreIntegrityError(
                f"approval_schema_invalid:{approval.approval_id}:{','.join(issues)}"
            )
        self._ensure_store_root(create=True)
        try:
            approval_dir.mkdir(mode=0o700)
        except FileExistsError as exc:
            raise ApprovalStoreIntegrityError(
                f"approval_already_exists:{approval.approval_id}"
            ) from exc

        directory_fd: int | None = None
        temporary_created = False
        try:
            directory_fd = os.open(
                approval_dir,
                os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
            )
            payload = json.dumps(
                document, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
            file_fd = os.open(
                "approval.json.tmp",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=directory_fd,
            )
            temporary_created = True
            try:
                view = memoryview(payload)
                while view:
                    written = os.write(file_fd, view)
                    view = view[written:]
                os.fsync(file_fd)
            finally:
                os.close(file_fd)
            os.link(
                "approval.json.tmp",
                "approval.json",
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
                follow_symlinks=False,
            )
            os.unlink("approval.json.tmp", dir_fd=directory_fd)
            temporary_created = False
            os.fsync(directory_fd)
        except OSError as exc:
            raise ApprovalStoreIntegrityError(
                f"approval_create_failed:{approval.approval_id}"
            ) from exc
        finally:
            if directory_fd is not None:
                if temporary_created:
                    try:
                        os.unlink("approval.json.tmp", dir_fd=directory_fd)
                    except OSError:
                        pass
                os.close(directory_fd)

    def load(self, approval_id: str) -> RuntimeInvocationApproval | None:
        """Load and structurally validate exactly one canonical artifact.
        Returns `None` if no artifact exists. Raises
        `ApprovalStoreIntegrityError` for any malformed, truncated,
        schema-invalid, or mismatched-identity artifact -- never a silent
        fallback and never partial trust (RIHAC-001 §15/§18)."""
        approval_dir = self._approval_dir(approval_id)
        if not self._ensure_store_root(create=False):
            return None
        try:
            approval_dir_stat = approval_dir.lstat()
        except FileNotFoundError:
            return None
        if not stat.S_ISDIR(approval_dir_stat.st_mode) or stat.S_ISLNK(approval_dir_stat.st_mode):
            raise ApprovalStoreIntegrityError(f"untrusted_approval_directory:{approval_id}")
        directory_fd: int | None = None
        file_fd: int | None = None
        try:
            directory_fd = os.open(
                approval_dir,
                os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_NOFOLLOW", 0),
            )
            file_fd = os.open(
                "approval.json",
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=directory_fd,
            )
            file_stat = os.fstat(file_fd)
            if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
                raise ApprovalStoreIntegrityError(f"untrusted_approval_file:{approval_id}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(file_fd, 65536)
                if not chunk:
                    break
                chunks.append(chunk)
            raw_text = b"".join(chunks).decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ApprovalStoreIntegrityError(f"approval_not_utf8:{approval_id}") from exc
        except OSError as exc:
            raise ApprovalStoreIntegrityError(f"approval_unreadable:{approval_id}") from exc
        finally:
            if file_fd is not None:
                os.close(file_fd)
            if directory_fd is not None:
                os.close(directory_fd)
        try:
            data = json.loads(raw_text, object_pairs_hook=_reject_duplicate_keys)
        except (json.JSONDecodeError, _DuplicateKeyError) as exc:
            raise ApprovalStoreIntegrityError(f"approval_malformed_json:{approval_id}") from exc

        issues = validate_riasc_schema_shape(data)
        if issues:
            raise ApprovalStoreIntegrityError(
                f"approval_schema_invalid:{approval_id}:{','.join(issues)}"
            )
        if data.get("approval_id") != approval_id:
            raise ApprovalStoreIntegrityError(
                f"approval_identity_mismatch:{approval_id}!={data.get('approval_id')}"
            )

        return _approval_from_dict(data)

    def exists(self, approval_id: str) -> bool:
        return self.load(approval_id) is not None


class _DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _approval_from_dict(data: dict) -> RuntimeInvocationApproval:
    subject = data["subject"]
    gov = data["governance_context"]
    scope = data["approval_scope"]
    adapter = data["adapter_binding"]
    freshness = data["freshness_snapshot"]
    provenance = data["provenance"]
    return RuntimeInvocationApproval(
        approval_id=data["approval_id"],
        record_digest=data["record_digest"],
        created_at=data["created_at"],
        expires_at=data["expires_at"],
        subject=ApprovalSubject(**subject),
        governance_context=GovernanceContext(
            phase_id=gov["phase_id"], session_id=gov.get("session_id")
        ),
        approval_scope=ApprovalScope(
            requested_capability=scope["requested_capability"],
            filesystem_scope_ref=ArtifactRef(**scope["filesystem_scope_ref"]),
            process_profile_ref=ArtifactRef(**scope["process_profile_ref"]),
            transport_type=scope["transport_type"],
            effect_class=scope["effect_class"],
            dispatch_limit=scope["dispatch_limit"],
            network_required=scope["network_required"],
        ),
        adapter_binding=AdapterBinding(**adapter),
        freshness_snapshot=FreshnessSnapshot(
            head_commit=freshness["head_commit"],
            task_contract_digest=freshness["task_contract_digest"],
            policy_version=freshness["policy_version"],
            task_state=freshness["task_state"],
        ),
        provenance=ApprovalProvenance(**provenance),
        schema_id=data["schema_id"],
        schema_version=data["schema_version"],
        contract_version=data["contract_version"],
        record_type=data["record_type"],
        prompt_hash_profile=data["prompt_hash_profile"],
        attempt_limit=data["attempt_limit"],
    )

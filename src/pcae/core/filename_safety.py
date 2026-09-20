"""Bounded, deterministic filesystem-component naming (PCAE-LIFECYCLE-FILENAME-LENGTH-HARDENING).

A long-lived governed lifecycle produces ever-growing dotted CPIPC phase
identities and free-text task titles. When such an identifier is embedded
verbatim into a single filesystem path component (a phase-report or
task-contract filename), the component can exceed the host filesystem's
component length limit (255 bytes on APFS and most POSIX filesystems),
causing ``OSError: [Errno 63]/[Errno 36] File name too long`` before any
governance logic runs.

This module provides exactly one shared primitive,
:func:`bounded_filename_component`, for every writer that turns a
canonical identity (phase ID, task ID/title) into part of a filename. It
never shortens the canonical identity itself -- callers must continue to
record the full, untruncated identity in the artifact's own
content/structured metadata. A filename is only a locator: FILE LOCATION
!= TRUSTED ORIGIN; the digest suffix below is for collision resistance
only, never authority.
"""
from __future__ import annotations

import hashlib

#: Deterministic, portable filesystem component byte budget, chosen
#: instead of a host-derived ``os.pathconf(..., "PC_NAME_MAX")`` value so
#: that a given canonical identity produces the identical filename on
#: every supported host (APFS, most Linux filesystems, and NTFS-via-exFAT
#: all support at least 255 bytes per path component). A host-specific
#: limit would make otherwise-identical identities produce different
#: filenames on different machines, breaking this repository's
#: determinism/reproducibility invariants.
MAX_FILENAME_COMPONENT_BYTES = 255

_SEPARATOR = "--"
_DIGEST_HEX_LEN = 16  # 64 bits of entropy: negligible collision risk for a locator suffix.


def _truncate_utf8(text: str, max_bytes: int) -> str:
    """Truncate ``text`` to at most ``max_bytes`` UTF-8 bytes without
    splitting a multi-byte code point."""
    if max_bytes <= 0:
        return ""
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    # A raw byte-slice can land mid-code-point; decoding with
    # errors="ignore" drops only the resulting incomplete trailing
    # fragment (never a complete character), which is always safe.
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def bounded_filename_component(
    raw: str, *, extension: str = "", max_bytes: int = MAX_FILENAME_COMPONENT_BYTES
) -> str:
    """Return a filesystem-safe basename (without ``extension``) such that
    ``basename + extension`` never exceeds ``max_bytes`` UTF-8 bytes.

    - If ``raw + extension`` already fits, ``raw`` is returned byte-for-byte
      unchanged (every existing short filename is untouched).
    - Otherwise returns a deterministic ``<truncated-prefix>--<digest>``,
      where ``digest`` is a stable SHA-256-derived hex digest of the
      *full, untruncated* ``raw`` string -- so two overlong names that
      happen to share a truncated prefix never collide.

    This only ever shortens the *filename*; the caller must still record
    the canonical identity ``raw`` was derived from, verbatim, in the
    artifact's own content/structured metadata.
    """
    candidate = raw + extension
    if len(candidate.encode("utf-8")) <= max_bytes:
        return raw

    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:_DIGEST_HEX_LEN]
    reserved = len((_SEPARATOR + digest + extension).encode("utf-8"))
    available = max_bytes - reserved
    if available <= 0:
        # extension + digest + separator alone consume the whole budget;
        # the digest alone is still a valid, collision-resistant,
        # bounded component.
        return digest

    prefix = _truncate_utf8(raw, available)
    if not prefix:
        return digest
    return f"{prefix}{_SEPARATOR}{digest}"

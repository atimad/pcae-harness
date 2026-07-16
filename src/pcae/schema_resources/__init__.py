"""Packaged, non-authoritative schema resources (Phase 136F, extended 136H).

Resolves PREREQUISITE-136E-1: the previous wheel/sdist packaging did
not include any schema-resource directory. Phase 136F proved the
packaging mechanism using a generic packaging smoke-test schema
(``smoke/generic_smoke_record.schema.json``); Phase 136H adds the
first real content, the Stage 3 Companion Executable Schema shared
core (``cltr_cutover/shared/*``, Implementation Group 1 only), while
still packaging the smoke schema unchanged.

No authority-bearing Stage 3 record schema, typed model, semantic
validator, or authority resolver/state/pointer is packaged here. See
``cltr_cutover/README.md`` and
``docs/PHASE_136_COMPANION_EXECUTABLE_SCHEMA_SHARED_CORE_IMPLEMENTATION.md``
for the full disposition.
"""
from __future__ import annotations

from contextlib import contextmanager
from importlib import resources
from pathlib import Path
from typing import Iterator


@contextmanager
def smoke_schema_root() -> Iterator[Path]:
    """Yield a real filesystem path to the packaged generic smoke-schema root.

    Works from an editable install, an installed wheel, or a source
    checkout. Performs no network access.
    """
    package_root = resources.files(__package__) / "smoke"
    with resources.as_file(package_root) as path:
        yield path


@contextmanager
def cltr_cutover_root() -> Iterator[Path]:
    """Yield a real filesystem path to the packaged ``cltr_cutover`` root.

    Contains only the Implementation Group 1 shared core (Phase 136H):
    ``shared/*.schema.json``, ``manifest.schema.json``, ``manifest.json``,
    and ``README.md``. No ``records/`` directory exists. Works from an
    editable install, an installed wheel, or a source checkout. Performs
    no network access.
    """
    package_root = resources.files(__package__) / "cltr_cutover"
    with resources.as_file(package_root) as path:
        yield path

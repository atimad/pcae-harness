"""Packaged, non-authoritative schema resources (Phase 136F).

Resolves PREREQUISITE-136E-1: the previous wheel/sdist packaging did
not include any schema-resource directory. This package currently
contains only a generic packaging smoke-test schema
(``smoke/generic_smoke_record.schema.json``) used to prove that a
schema resource packaged here is included in editable installs,
wheels, and source distributions, and is loadable offline via
``importlib.resources``.

No Stage 3 companion executable schema is packaged here. That
authoring is explicitly deferred beyond Phase 136F.
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

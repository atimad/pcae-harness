"""Centrally recorded conservative limits for schema_runtime infrastructure.

Phase 136F prerequisite infrastructure. These limits bound generic
Layer-1/Layer-2 schema-validation inputs; they carry no authority
semantics and are independent of any Stage 3 record contract.
"""
from __future__ import annotations

# Maximum size, in bytes, of a single JSON document passed to the strict parser.
DEFAULT_MAX_INPUT_BYTES = 5 * 1024 * 1024

# Maximum size, in bytes, of a single schema resource file loaded from disk.
DEFAULT_MAX_SCHEMA_RESOURCE_BYTES = 1 * 1024 * 1024

# Maximum number of validation issues returned by shape validation.
DEFAULT_MAX_ISSUE_COUNT = 200

# Maximum number of schema resources accepted into a single offline registry.
DEFAULT_MAX_REGISTRY_RESOURCES = 500

# Maximum object/array nesting depth accepted by the strict JSON parser.
# Phase 136G repair: the hand-written recursive-descent parser previously
# had no explicit depth bound and relied only on CPython's own interpreter
# recursion limit as a backstop (136F limitations, §10). Independent
# adversarial testing showed that well-formed JSON far smaller than
# DEFAULT_MAX_INPUT_BYTES (e.g. ~500 levels of nested arrays) could raise an
# *uncaught* RecursionError, violating parse_strict_json's own documented
# contract that it "never raises on ordinary invalid input." This limit is
# set conservatively below the empirically observed crash threshold so the
# parser fails closed with a structured JsonParseResult instead.
DEFAULT_MAX_NESTING_DEPTH = 200

# Maximum dict/list nesting depth accepted by validate_record_shape() before
# invoking the underlying jsonschema validator. Phase 136G repair: distinct
# from DEFAULT_MAX_NESTING_DEPTH (which bounds parse_strict_json's own
# recursive-descent parser). Draft202012Validator.iter_errors() recurses
# once per nesting level of a self-referential schema traversing the
# record; independent testing showed this crashes with an uncaught
# RecursionError at a materially shallower record depth (~300) than the
# parser's own limit, and can be reached even by a record that
# parse_strict_json itself already accepted. Checked via an explicit
# (non-recursive) stack walk -- see validation.py's _exceeds_max_depth --
# so the guard itself cannot be defeated by the same class of attack.
DEFAULT_MAX_RECORD_DEPTH = 150

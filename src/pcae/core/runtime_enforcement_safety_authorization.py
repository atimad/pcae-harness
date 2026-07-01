"""Phase 104C — Shared Runtime Enforcement Safety/Authorization Contract.

Design-only. Non-executing. Non-authorizing. Provides canonical constant definitions
for authorization and safety flags shared across runtime-enforcement artifacts.
"""
from __future__ import annotations
from typing import Final

# ═══════════════════════════════════════════════════════════════════════════
# Canonical Authorization Flag Names (12)
# ═══════════════════════════════════════════════════════════════════════════

AUTHORIZATION_FLAG_NAMES: Final[tuple[str, ...]] = (
    "execution_available",
    "execution_authorized",
    "backend_invocation_authorized",
    "adapter_execution_authorized",
    "network_authorized",
    "subprocess_authorized",
    "shell_authorized",
    "mutation_authorized",
    "apply_authorized",
    "rollback_authorized",
    "commit_authorized",
    "push_authorized",
)

# ═══════════════════════════════════════════════════════════════════════════
# Canonical Safety Flag Names (5)
# ═══════════════════════════════════════════════════════════════════════════

SAFETY_FLAG_NAMES: Final[tuple[str, ...]] = (
    "simulation_only",
    "no_execution",
    "evidence_only",
    "non_authorizing",
    "design_only",
)

# ═══════════════════════════════════════════════════════════════════════════
# Default Values — all auth flags False, all safety flags True
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_AUTHORIZATION_FLAGS: Final[dict[str, bool]] = {
    name: False for name in AUTHORIZATION_FLAG_NAMES
}

DEFAULT_SAFETY_FLAGS: Final[dict[str, bool]] = {
    name: True for name in SAFETY_FLAG_NAMES
}

# ═══════════════════════════════════════════════════════════════════════════
# RE-NOGO Registry Mappings
# ═══════════════════════════════════════════════════════════════════════════

AUTH_FLAG_TO_NO_GO: Final[dict[str, str]] = {
    "execution_available": "RE-NOGO-002",
    "execution_authorized": "RE-NOGO-002",
    "backend_invocation_authorized": "RE-NOGO-003",
    "adapter_execution_authorized": "RE-NOGO-004",
    "network_authorized": "RE-NOGO-005",
    "subprocess_authorized": "RE-NOGO-005",
    "shell_authorized": "RE-NOGO-005",
    "mutation_authorized": "RE-NOGO-006",
    "apply_authorized": "RE-NOGO-006",
    "rollback_authorized": "RE-NOGO-007",
    "commit_authorized": "RE-NOGO-008",
    "push_authorized": "RE-NOGO-008",
}

SAFETY_FLAG_TO_NO_GO: Final[dict[str, str]] = {
    "simulation_only": "RE-NOGO-011",
    "no_execution": "RE-NOGO-001",
    "evidence_only": "RE-NOGO-001",
    "non_authorizing": "RE-NOGO-001",
    "design_only": "RE-NOGO-010",
}

# ═══════════════════════════════════════════════════════════════════════════
# Validation Helpers (non-executing, non-authorizing)
# ═══════════════════════════════════════════════════════════════════════════

def validate_all_authorization_false(flags: dict[str, bool]) -> list[str]:
    """Return list of authorization flags that are True (should be empty)."""
    return [name for name in AUTHORIZATION_FLAG_NAMES if flags.get(name, False)]


def validate_all_safety_true(flags: dict[str, bool]) -> list[str]:
    """Return list of safety flags that are False (should be empty)."""
    return [name for name in SAFETY_FLAG_NAMES if not flags.get(name, True)]


def build_authorization_summary(flags: dict[str, bool]) -> dict[str, bool]:
    """Build canonical authorization_summary dict for to_dict() output."""
    return {name: flags.get(name, DEFAULT_AUTHORIZATION_FLAGS[name]) for name in AUTHORIZATION_FLAG_NAMES}

"""Stage 2 rehearsal feature configuration (135Q §45/§46).

Separate from Stage 1's flags. Disabled by default. No combination of
flags this module resolves can ever grant CLTR authority, activate
Stage 3, or change ``production_authority`` -- that remains a
separately hardcoded ``ProductionAuthority.LEGACY`` literal untouched by
every flag this module reads.
"""

from __future__ import annotations

import dataclasses
import os

from pcae.cltr.migration.configuration import (
    MigrationConfiguration,
    MigrationConfigurationError,
    load_configuration,
)
from pcae.cltr.migration.enums import ACTIVE_STAGES, MigrationStage, ProductionAuthority

ATOMIC_REHEARSAL_ENABLED_ENV_VAR = "PCAE_CLTR_ATOMIC_REHEARSAL_ENABLED"

_TRUTHY = ("1", "true", "yes")

#: Stage 3+ authority-flag name patterns rejected outright if ever
#: introduced prematurely (135Q §46) -- none exists yet; this is a
#: forward-looking, conservative rejection list.
_RESERVED_STAGE3_ENV_VARS = (
    "PCAE_CLTR_AUTHORITY_CUTOVER_ENABLED",
    "PCAE_CLTR_AUTHORITY_ENABLED",
    "PCAE_CLTR_LEGACY_DEMOTION_ENABLED",
    "PCAE_CLTR_LEGACY_RETIREMENT_ENABLED",
)

MANIFEST_SCHEMA_ID = "pcae.cltr.rehearsal.v1"
MANIFEST_SCHEMA_VERSION = "1.0.0"


class RehearsalConfigurationError(ValueError):
    """Fail-closed: an invalid Stage 2 configuration is never silently
    repaired or defaulted to a guessed value."""


@dataclasses.dataclass(frozen=True)
class RehearsalConfiguration:
    atomic_rehearsal_enabled: bool
    stage1: MigrationConfiguration

    @property
    def effectively_active(self) -> bool:
        return self.atomic_rehearsal_enabled and self.stage1.effectively_active


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def load_rehearsal_configuration() -> RehearsalConfiguration:
    """Safe default: Stage 2 disabled. Raises
    ``RehearsalConfigurationError`` only when an invalid value would
    otherwise be treated as active -- mirrors
    ``pcae.cltr.migration.configuration.load_configuration``'s exact
    fail-closed discipline (135Q §45's own precedent)."""

    atomic_enabled = _env_bool(ATOMIC_REHEARSAL_ENABLED_ENV_VAR)

    try:
        stage1 = load_configuration()
    except MigrationConfigurationError as exc:
        if not atomic_enabled:
            # Stage 1 misconfiguration is harmless if Stage 2 is off too.
            return RehearsalConfiguration(
                atomic_rehearsal_enabled=False,
                stage1=MigrationConfiguration(
                    dual_derivation_enabled=False,
                    migration_stage=MigrationStage.SHADOW_OBSERVATION,
                    migration_epoch=None,
                    shadow_enabled=False,
                ),
            )
        raise RehearsalConfigurationError(f"Stage 1 configuration invalid: {exc}") from exc

    if not atomic_enabled:
        return RehearsalConfiguration(atomic_rehearsal_enabled=False, stage1=stage1)

    # 135Q §46's invalid-configuration matrix, checked in order so the
    # diagnostic identifies exactly which combination failed (never a
    # generic message).
    if not stage1.dual_derivation_enabled:
        raise RehearsalConfigurationError(
            f"{ATOMIC_REHEARSAL_ENABLED_ENV_VAR} requires Stage 1 dual derivation "
            "(PCAE_CLTR_DUAL_DERIVATION_ENABLED) to already be enabled"
        )
    if stage1.migration_stage != MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY:
        raise RehearsalConfigurationError(
            f"{ATOMIC_REHEARSAL_ENABLED_ENV_VAR} requires migration_stage="
            f"{MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY.value!r}; got {stage1.migration_stage.value!r}"
        )
    if stage1.migration_stage not in ACTIVE_STAGES:
        raise RehearsalConfigurationError(
            f"migration stage {stage1.migration_stage.value!r} has no active implementation; "
            "Stage 2 cannot rehearse against an inactive stage"
        )
    if not stage1.migration_epoch:
        raise RehearsalConfigurationError(f"{ATOMIC_REHEARSAL_ENABLED_ENV_VAR} requires a non-empty migration epoch")
    if stage1.production_authority != ProductionAuthority.LEGACY:
        raise RehearsalConfigurationError(
            "Stage 2 rehearsal requires legacy-authoritative production_authority; "
            f"got {stage1.production_authority.value!r}"
        )
    present_reserved = [name for name in _RESERVED_STAGE3_ENV_VARS if _env_bool(name)]
    if present_reserved:
        raise RehearsalConfigurationError(
            f"Stage 3 authority-cutover flag(s) present alongside {ATOMIC_REHEARSAL_ENABLED_ENV_VAR}: "
            f"{present_reserved} -- rejected, Stage 2 can never coexist with a Stage 3 authority flag"
        )

    return RehearsalConfiguration(atomic_rehearsal_enabled=True, stage1=stage1)

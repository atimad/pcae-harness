"""Stage 1 migration feature configuration (phase brief §3).

135M §42 freezes only ``PCAE_CLTR_SHADOW_ENABLED`` verbatim; every other
flag name is explicitly left to 135O to name (confirmed during required
source inspection: no other flag name appears anywhere in 135M/135N). The
names below are 135O's implementation choice, matching the phase brief's
own suggested naming exactly.

No single boolean can grant CLTR authority: ``PCAE_CLTR_DUAL_DERIVATION_ENABLED``
only ever gates *evidence generation*; ``ProductionAuthority`` is always
``LEGACY`` for every ``MigrationConfiguration`` this module can construct
during Stage 1 -- there is no flag, combination of flags, or migration
stage value that this module will resolve to ``ProductionAuthority.CLTR``.
"""

from __future__ import annotations

import dataclasses
import os

from pcae.cltr.migration.enums import ACTIVE_STAGES, MigrationStage, ProductionAuthority
from pcae.cltr.shadow import is_shadow_enabled

DUAL_DERIVATION_ENABLED_ENV_VAR = "PCAE_CLTR_DUAL_DERIVATION_ENABLED"
MIGRATION_STAGE_ENV_VAR = "PCAE_CLTR_MIGRATION_STAGE"
MIGRATION_EPOCH_ENV_VAR = "PCAE_CLTR_MIGRATION_EPOCH"

_TRUTHY = ("1", "true", "yes")


class MigrationConfigurationError(ValueError):
    """Raised (never silently repaired) when Stage 1 configuration is
    malformed, unsupported, or internally inconsistent. Fail-closed:
    the caller must treat this as "dual derivation is not safely
    enabled", never fall back to a guessed default stage/epoch."""


@dataclasses.dataclass(frozen=True)
class MigrationConfiguration:
    dual_derivation_enabled: bool
    migration_stage: MigrationStage
    migration_epoch: str | None
    shadow_enabled: bool
    production_authority: ProductionAuthority = ProductionAuthority.LEGACY

    @property
    def effectively_active(self) -> bool:
        return self.dual_derivation_enabled and self.migration_stage in ACTIVE_STAGES


def _env_bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


def load_configuration() -> MigrationConfiguration:
    """Resolve Stage 1 configuration from environment. Safe default: Stage
    1 disabled. Never raises for the disabled case -- an invalid *value*
    while disabled is recorded as inactive, not fatal, since it cannot
    affect production. Raises ``MigrationConfigurationError`` only when
    the invalid value would otherwise be treated as active."""

    dual_derivation_enabled = _env_bool(DUAL_DERIVATION_ENABLED_ENV_VAR)
    shadow_enabled = is_shadow_enabled()
    raw_stage = os.environ.get(MIGRATION_STAGE_ENV_VAR, "").strip()
    raw_epoch = os.environ.get(MIGRATION_EPOCH_ENV_VAR, "").strip() or None

    if not dual_derivation_enabled:
        # Safe default path: disabled. A malformed stage/epoch while
        # disabled is disclosed as inert, not raised -- it cannot reach
        # production because ``effectively_active`` is False regardless.
        try:
            stage = MigrationStage(raw_stage) if raw_stage else MigrationStage.SHADOW_OBSERVATION
        except ValueError:
            stage = MigrationStage.SHADOW_OBSERVATION
        return MigrationConfiguration(
            dual_derivation_enabled=False,
            migration_stage=stage,
            migration_epoch=raw_epoch,
            shadow_enabled=shadow_enabled,
        )

    if not raw_stage:
        raise MigrationConfigurationError(
            f"{MIGRATION_STAGE_ENV_VAR} is required when {DUAL_DERIVATION_ENABLED_ENV_VAR} is enabled"
        )
    try:
        stage = MigrationStage(raw_stage)
    except ValueError as exc:
        raise MigrationConfigurationError(f"unsupported migration stage: {raw_stage!r}") from exc

    if stage not in ACTIVE_STAGES:
        raise MigrationConfigurationError(
            f"migration stage {stage.value!r} has no active Stage-1 implementation; "
            "unsupported stages must fail closed, not silently degrade"
        )
    if stage != MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY:
        raise MigrationConfigurationError(
            f"{DUAL_DERIVATION_ENABLED_ENV_VAR} requires migration_stage="
            f"{MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY.value!r}; "
            f"got {stage.value!r} (dual derivation cannot be enabled for a non-dual-derivation stage)"
        )

    if not raw_epoch:
        raise MigrationConfigurationError(
            f"{MIGRATION_EPOCH_ENV_VAR} is required and must be non-empty when Stage 1 is enabled "
            "(a missing epoch must fail safely, never be inferred from time, git, or titles)"
        )
    if not raw_epoch.isascii() or any(ch.isspace() for ch in raw_epoch):
        raise MigrationConfigurationError(f"malformed {MIGRATION_EPOCH_ENV_VAR}: {raw_epoch!r}")

    return MigrationConfiguration(
        dual_derivation_enabled=True,
        migration_stage=stage,
        migration_epoch=raw_epoch,
        shadow_enabled=shadow_enabled,
    )

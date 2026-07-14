"""Phase 135O — Stage 1 migration configuration tests."""

from __future__ import annotations

import pytest

from pcae.cltr.migration.configuration import (
    DUAL_DERIVATION_ENABLED_ENV_VAR,
    MIGRATION_EPOCH_ENV_VAR,
    MIGRATION_STAGE_ENV_VAR,
    MigrationConfigurationError,
    load_configuration,
)
from pcae.cltr.migration.enums import MigrationStage, ProductionAuthority


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv(DUAL_DERIVATION_ENABLED_ENV_VAR, raising=False)
    config = load_configuration()
    assert config.dual_derivation_enabled is False
    assert config.effectively_active is False
    assert config.production_authority == ProductionAuthority.LEGACY


def test_valid_stage1_configuration(monkeypatch):
    monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, "1")
    monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY.value)
    monkeypatch.setenv(MIGRATION_EPOCH_ENV_VAR, "epoch-1")
    config = load_configuration()
    assert config.effectively_active is True
    assert config.migration_epoch == "epoch-1"
    assert config.production_authority == ProductionAuthority.LEGACY


def test_missing_migration_stage_when_enabled_raises(monkeypatch):
    monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, "1")
    monkeypatch.delenv(MIGRATION_STAGE_ENV_VAR, raising=False)
    monkeypatch.setenv(MIGRATION_EPOCH_ENV_VAR, "epoch-1")
    with pytest.raises(MigrationConfigurationError):
        load_configuration()


def test_missing_migration_epoch_when_enabled_raises(monkeypatch):
    monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, "1")
    monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY.value)
    monkeypatch.delenv(MIGRATION_EPOCH_ENV_VAR, raising=False)
    with pytest.raises(MigrationConfigurationError):
        load_configuration()


def test_malformed_migration_epoch_raises(monkeypatch):
    monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, "1")
    monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY.value)
    monkeypatch.setenv(MIGRATION_EPOCH_ENV_VAR, "has a space")
    with pytest.raises(MigrationConfigurationError):
        load_configuration()


def test_unsupported_stage_fails_closed(monkeypatch):
    monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, "1")
    monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, "not_a_real_stage")
    monkeypatch.setenv(MIGRATION_EPOCH_ENV_VAR, "epoch-1")
    with pytest.raises(MigrationConfigurationError):
        load_configuration()


def test_later_stage_value_fails_closed_even_though_it_is_a_known_enum(monkeypatch):
    monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, "1")
    monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, MigrationStage.CLTR_AUTHORITY_WITH_LEGACY_VERIFICATION.value)
    monkeypatch.setenv(MIGRATION_EPOCH_ENV_VAR, "epoch-1")
    with pytest.raises(MigrationConfigurationError):
        load_configuration()


def test_shadow_observation_stage_cannot_be_paired_with_dual_derivation_enabled(monkeypatch):
    monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, "1")
    monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, MigrationStage.SHADOW_OBSERVATION.value)
    monkeypatch.setenv(MIGRATION_EPOCH_ENV_VAR, "epoch-1")
    with pytest.raises(MigrationConfigurationError):
        load_configuration()


def test_malformed_stage_while_disabled_is_inert_not_raised(monkeypatch):
    monkeypatch.delenv(DUAL_DERIVATION_ENABLED_ENV_VAR, raising=False)
    monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, "garbage")
    config = load_configuration()
    assert config.dual_derivation_enabled is False
    assert config.effectively_active is False


def test_shadow_and_dual_derivation_can_both_be_enabled(monkeypatch):
    monkeypatch.setenv("PCAE_CLTR_SHADOW_ENABLED", "1")
    monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, "1")
    monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY.value)
    monkeypatch.setenv(MIGRATION_EPOCH_ENV_VAR, "epoch-1")
    config = load_configuration()
    assert config.shadow_enabled is True
    assert config.effectively_active is True


def test_no_boolean_can_grant_cltr_authority(monkeypatch):
    for flag_value in ("1", "true", "yes"):
        monkeypatch.setenv(DUAL_DERIVATION_ENABLED_ENV_VAR, flag_value)
        monkeypatch.setenv(MIGRATION_STAGE_ENV_VAR, MigrationStage.DUAL_DERIVATION_LEGACY_AUTHORITY.value)
        monkeypatch.setenv(MIGRATION_EPOCH_ENV_VAR, "epoch-1")
        config = load_configuration()
        assert config.production_authority == ProductionAuthority.LEGACY

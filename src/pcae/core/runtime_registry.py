"""
Runtime Registry Prototype — Phase 110E.

The first passive implementation of the Runtime Registry frozen by 110C
(`docs/PCAE_RUNTIME_SERVICE_REGISTRY.md`) and contracted by 110D
(`docs/PCAE_RUNTIME_REGISTRY_CONTRACT.md`). This module owns plugin
*metadata only* — it never loads, imports, instantiates, invokes, or
executes a plugin, and it holds no reference to any plugin's actual
code. A `PluginDescriptor` is a plain, inert data record; nothing in
this module can turn one into a running plugin instance.

Metadata precedes behavior (110E's own addition to the roadmap
ordering, alongside "Discoverable always," 110C): a plugin's existence
is knowable, queryable, and validatable entirely independent of any
capability to run it. This module proves that claim by implementing
exactly the metadata half and nothing else.

Isolation (by design, verified by tests reading this module's own
source, mirroring 108A's isolation guarantee for
`permission_broker_foundation.py`): this module imports only the
standard library. It uses no `subprocess`, no shell, no network, no
file mutation, no `importlib`, no `eval`/`exec`/`compile`, and no
dependency on `shell_gate`, `backend_invocations`, `notifications`, or
any other execution-adjacent module. `RuntimeRegistry` is a pure
in-memory data store — nothing it does has any effect outside the
Python process holding it.

Implements, metadata-only, five of the nine canonical Registry API
operations frozen by 110D (`docs/PCAE_RUNTIME_REGISTRY_CONTRACT.md`
§2): `RegisterPlugin()` -> `register_metadata()`, `ListPlugins()` ->
`list_plugins()`, `DiscoverCapabilities()`/`ListCapabilityProviders()`
-> `list_capabilities()`/`find_capability()`, `GetPluginMetadata()`
-> `get_plugin_metadata()`. Deliberately does **not** implement
`UnregisterPlugin()` (no lifecycle-driving behavior in this phase),
`ResolveCapability()` (110D's resolution-outcome semantics —
`Resolved`/`MultipleCandidates`/`NoProvider`/etc. — require Runtime-side
selection behavior this phase does not introduce), `GetPluginHealth()`
as a live signal (a plugin's `health_state` is accepted as inert,
caller-supplied metadata here, never computed or polled), or
`ValidateCompatibility()` as a gating check (this module *reports*
version-format and runtime-version-declaration mismatches for
observation; it never blocks or gates anything on the result).

Current implementation status: **execution unavailable**. No plugin
loading mechanism, dependency injection framework, or execution
boundary exists anywhere in this codebase. Registering a plugin
descriptor here does not make the described plugin runnable, callable,
or discoverable to any code path outside this module. Current maximum
runtime state remains `Observed` (110A §8); current maximum plugin
capability remains `observe` (110B §3) — this module does not change
either ceiling, and structurally cannot, since it holds no executable
reference to anything.

110F hardening (verification phase, no new behavior): `PluginDescriptor.manifest`
is now stored as an immutable `MappingProxyType` wrapping a shallow
copy taken at construction time, closing an aliasing gap where a
caller-held reference to the original manifest dict could otherwise
mutate what the registry has already stored, even though the
dataclass itself is frozen.

See `docs/PHASE_110_RUNTIME_REGISTRY_PROTOTYPE.md`,
`docs/PHASE_110_RUNTIME_REGISTRY_VERIFICATION.md` (110F),
`docs/PCAE_RUNTIME_SERVICE_REGISTRY.md` (110C), and
`docs/PCAE_RUNTIME_REGISTRY_CONTRACT.md` (110D).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

# ═══════════════════════════════════════════════════════════════════════
# Frozen vocabularies (restated from 110B/110C/110D — not redefined here)
# ═══════════════════════════════════════════════════════════════════════

#: The ten plugin categories frozen by 110A §3 / 110B §2.
PLUGIN_CATEGORIES: tuple[str, ...] = (
    "Intent Source",
    "Policy",
    "Decision",
    "Approval",
    "Execution Adapter",
    "Audit",
    "Notification",
    "Storage",
    "Identity",
    "Context",
)

#: The eight plugin lifecycle states frozen by 110B §4. This registry
#: only ever *stores* whichever state a caller declares — it never
#: drives, computes, or transitions a plugin between states (110D §7,
#: "Registry never executes lifecycle").
LIFECYCLE_STATES: tuple[str, ...] = (
    "defined",
    "registered",
    "configured",
    "healthy",
    "available",
    "disabled",
    "failed",
    "retired",
)

#: The ten plugin capability classes frozen by 110B §3.
CAPABILITY_CLASSES: tuple[str, ...] = (
    "observe",
    "advise",
    "approve",
    "deny",
    "enforce",
    "execute",
    "audit",
    "notify",
    "store",
    "rollback_prepare",
)

#: `enforce` and `execute` remain undeclarable by any plugin today
#: (110B §3: "no category may currently declare this"). This registry
#: enforces that guarantee at the metadata layer: a descriptor
#: declaring either is rejected by `validate_descriptor()`, never
#: stored. This is the one validation rule that exists specifically to
#: preserve the execution-unavailable guarantee, not merely to check
#: data hygiene.
UNDECLARABLE_CAPABILITIES: frozenset[str] = frozenset({"enforce", "execute"})

#: The three permitted "Current implementation status" values frozen by
#: 110B §1 field 18. `"implemented"` is deliberately never a member of
#: this tuple — no plugin contract may claim it (110B: "No plugin
#: contract may claim implemented -- no plugin loading mechanism exists
#: to make any contract runnable").
IMPLEMENTATION_STATUSES: tuple[str, ...] = (
    "not_implemented",
    "foundation_implemented",
    "partially_implemented",
)

#: Health-state vocabulary for the `health_state` metadata field. This
#: registry never computes or polls health — it only stores whatever
#: value a caller supplies at registration time (110D §7 draws the same
#: "surfaces, never drives" distinction for lifecycle; the same
#: distinction applies to health here).
HEALTH_STATES: tuple[str, ...] = ("healthy", "unhealthy", "unknown")

_SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


# ═══════════════════════════════════════════════════════════════════════
# Plugin descriptor — inert metadata, never a runnable plugin
# ═══════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PluginDescriptor:
    """Metadata describing one plugin instance, using the fields the
    110B canonical Plugin Contract Model and 110C's plugin manifest
    concept name as relevant to registration and discovery. This is a
    plain data record — it holds no callable, no module reference, no
    class, and no import path. Nothing about a `PluginDescriptor`
    allows the Runtime (or anything else) to invoke the plugin it
    describes.

    Field correspondence:
    - `plugin_id`, `plugin_type`, `version` -- 110B §1 fields 1, 2, 11.
    - `capabilities` -- 110B §1 field 8 (Capability declaration).
    - `lifecycle_state` -- 110B §4.
    - `health_state` -- surfaces 110B §1 field 10 (Health reporting) as
      inert, caller-supplied data; this registry does not compute it.
    - `implementation_status` -- 110B §1 field 18.
    - `manifest` -- an open, read-only mapping for any of 110C §3's
      fifteen manifest fields not otherwise named above (e.g. Plugin
      name, Compatible runtime version, Dependencies). No schema is
      enforced beyond the cross-field consistency checks
      `validate_descriptor()` performs (§ below).

    110F hardening: `manifest` is converted, at construction time, into
    a `MappingProxyType` wrapping a *shallow copy* of whatever was
    passed in. `@dataclass(frozen=True)` alone only prevents
    *reassigning* `descriptor.manifest` — without this, the dict object
    the field points at would remain independently mutable, and would
    be the exact same object a caller's own reference points at (alias
    mutation risk). This closes that gap: mutating a manifest dict after
    constructing a descriptor from it, or attempting to mutate
    `descriptor.manifest` directly, can never change what the registry
    has stored.
    """

    plugin_id: str
    plugin_type: str
    version: str
    capabilities: tuple[str, ...] = ()
    lifecycle_state: str = "defined"
    health_state: str = "unknown"
    implementation_status: str = "not_implemented"
    manifest: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "manifest", MappingProxyType(dict(self.manifest)))


@dataclass(frozen=True)
class RegistrationResult:
    """Outcome of one `register_metadata()` call. Registration never
    raises on invalid input -- it fails closed, exactly as
    `permission_broker_foundation.py`'s `_sanitize_result()` (108C)
    never lets a malformed rule crash evaluation. An unaccepted
    registration leaves the registry's stored state unchanged."""

    plugin_id: str
    accepted: bool
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegistrySnapshot:
    """Metadata-only runtime health, per 110E objective 5: registered
    plugins, registered capabilities, registry status, and metadata
    validity. Carries no behavioral health signal -- nothing here
    reflects whether any plugin actually works, only what has been
    recorded about it."""

    registered_plugin_count: int
    registered_capability_count: int
    registry_status: str
    metadata_validity: str
    plugin_ids: tuple[str, ...]
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class RegistryValidationReport:
    """Result of `RuntimeRegistry.validate_consistency()` -- a
    read-only re-scan of everything currently stored, independent of
    the fail-closed checks `register_metadata()` already performed at
    admission time. Every field name matches a check named by 110E
    objective 6. All fields are expected empty in normal operation --
    `register_metadata()` refuses to store anything that would appear
    here -- this report exists to make that invariant independently
    verifiable rather than merely assumed."""

    duplicate_plugin_ids: tuple[str, ...]
    plugins_with_duplicate_capability_declarations: tuple[str, ...]
    plugins_with_manifest_inconsistencies: tuple[str, ...]
    plugins_with_invalid_contract_fields: tuple[str, ...]
    plugins_with_invalid_version_format: tuple[str, ...]
    consistent: bool


# ═══════════════════════════════════════════════════════════════════════
# Descriptor validation (observation only — reports issues, never raises)
# ═══════════════════════════════════════════════════════════════════════


def validate_descriptor(descriptor: PluginDescriptor) -> tuple[str, ...]:
    """Return every validation issue code found in `descriptor`, or an
    empty tuple if it is fully valid. Pure function -- no side effects,
    no registry state consulted. Used both by `register_metadata()`
    (pre-store, fail-closed admission) and by
    `RuntimeRegistry.validate_consistency()` (post-store re-scan) so
    the two checks can never drift out of sync with each other."""
    issues: list[str] = []

    if not descriptor.plugin_id:
        issues.append("empty_plugin_id")

    if descriptor.plugin_type not in PLUGIN_CATEGORIES:
        issues.append("invalid_plugin_type")

    if descriptor.lifecycle_state not in LIFECYCLE_STATES:
        issues.append("invalid_lifecycle_state")

    if descriptor.health_state not in HEALTH_STATES:
        issues.append("invalid_health_state")

    if descriptor.implementation_status not in IMPLEMENTATION_STATUSES:
        issues.append("invalid_implementation_status")

    if not _SEMVER_PATTERN.match(descriptor.version):
        issues.append("invalid_version_format")

    if len(set(descriptor.capabilities)) != len(descriptor.capabilities):
        issues.append("duplicate_capability_declaration")

    for capability in descriptor.capabilities:
        if capability in UNDECLARABLE_CAPABILITIES:
            issues.append("undeclarable_capability")
        elif capability not in CAPABILITY_CLASSES:
            issues.append("invalid_capability")

    issues.extend(_manifest_consistency_issues(descriptor))

    return tuple(issues)


def _manifest_consistency_issues(descriptor: PluginDescriptor) -> tuple[str, ...]:
    """A manifest (110C §3) is optional, open metadata -- but if it
    names a plugin_id, plugin_type, or version, that value must agree
    with the descriptor's own fields. This registry does not require a
    manifest to be present, only that a present one not contradict
    itself."""
    issues: list[str] = []
    manifest = descriptor.manifest
    if "plugin_id" in manifest and manifest["plugin_id"] != descriptor.plugin_id:
        issues.append("manifest_plugin_id_mismatch")
    if "plugin_type" in manifest and manifest["plugin_type"] != descriptor.plugin_type:
        issues.append("manifest_plugin_type_mismatch")
    if "version" in manifest and manifest["version"] != descriptor.version:
        issues.append("manifest_version_mismatch")
    return tuple(issues)


# ═══════════════════════════════════════════════════════════════════════
# Runtime Registry — passive in-memory metadata store
# ═══════════════════════════════════════════════════════════════════════


class RuntimeRegistry:
    """The passive Runtime Registry prototype. Owns plugin metadata
    only -- no plugin loading, instantiation, invocation, dependency
    injection, or execution of any kind. Every public method either
    reads or writes plain `PluginDescriptor` records in an in-memory
    dict; none of them imports, calls, or executes anything the stored
    metadata might describe.

    Registry never orchestrates, decides, approves, or executes (110C
    §1, restated as contract by 110D §8) -- this class is the first
    concrete proof of that boundary: it cannot orchestrate, decide,
    approve, or execute anything, because it holds no capability to do
    so in the first place.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginDescriptor] = {}

    def register_metadata(self, descriptor: PluginDescriptor) -> RegistrationResult:
        """Admit one plugin descriptor's metadata. Fails closed: any
        validation issue, or a plugin_id already registered, is
        rejected and the registry's stored state is left unchanged --
        this method never raises and never partially stores a rejected
        descriptor."""
        if descriptor.plugin_id in self._plugins:
            return RegistrationResult(
                plugin_id=descriptor.plugin_id,
                accepted=False,
                issues=("duplicate_plugin_id",),
            )

        issues = validate_descriptor(descriptor)
        if issues:
            return RegistrationResult(
                plugin_id=descriptor.plugin_id,
                accepted=False,
                issues=issues,
            )

        self._plugins[descriptor.plugin_id] = descriptor
        return RegistrationResult(plugin_id=descriptor.plugin_id, accepted=True)

    def list_plugins(self) -> tuple[PluginDescriptor, ...]:
        """Every currently registered plugin descriptor, in
        registration order."""
        return tuple(self._plugins.values())

    def list_capabilities(self) -> tuple[str, ...]:
        """Every distinct capability declared by any registered
        plugin, sorted for deterministic output."""
        seen: set[str] = set()
        for descriptor in self._plugins.values():
            seen.update(descriptor.capabilities)
        return tuple(sorted(seen))

    def find_capability(self, capability: str) -> tuple[PluginDescriptor, ...]:
        """Every registered plugin declaring `capability` -- the
        unfiltered "declared" view 110D §2 names as
        `ListCapabilityProviders()`, not the compatibility/health/
        lifecycle-filtered `ResolveCapability()` view (110D §4), which
        this phase deliberately does not implement (it would require
        Runtime-side resolution behavior, not metadata storage)."""
        return tuple(
            descriptor
            for descriptor in self._plugins.values()
            if capability in descriptor.capabilities
        )

    def get_plugin_metadata(self, plugin_id: str) -> PluginDescriptor | None:
        """A single registered plugin's descriptor, or `None` if no
        plugin with that ID is registered."""
        return self._plugins.get(plugin_id)

    def registry_health(self) -> RegistrySnapshot:
        """Metadata-only runtime health (110E objective 5): counts,
        status, and an aggregate validity signal -- never a behavioral
        health check of anything the metadata describes."""
        plugin_ids = tuple(self._plugins.keys())
        capabilities = self.list_capabilities()
        all_valid = all(not validate_descriptor(d) for d in self._plugins.values())
        return RegistrySnapshot(
            registered_plugin_count=len(plugin_ids),
            registered_capability_count=len(capabilities),
            registry_status="populated" if plugin_ids else "empty",
            metadata_validity="valid" if all_valid else "invalid",
            plugin_ids=plugin_ids,
            capabilities=capabilities,
        )

    def validate_consistency(self) -> RegistryValidationReport:
        """Re-scan every currently stored descriptor independent of
        `register_metadata()`'s admission-time checks (110E objective
        6). In normal operation every field of the returned report is
        empty, since nothing failing these checks could have been
        stored in the first place -- this method makes that invariant
        independently verifiable rather than merely assumed, mirroring
        the read-only re-verification pattern `pcae governance audit`
        already applies elsewhere in this codebase."""
        id_counts: dict[str, int] = {}
        for plugin_id in self._plugins:
            id_counts[plugin_id] = id_counts.get(plugin_id, 0) + 1
        duplicate_ids = tuple(pid for pid, count in id_counts.items() if count > 1)

        duplicate_capability_plugins: list[str] = []
        manifest_inconsistent_plugins: list[str] = []
        invalid_contract_plugins: list[str] = []
        invalid_version_plugins: list[str] = []

        for plugin_id, descriptor in self._plugins.items():
            issues = validate_descriptor(descriptor)
            if "duplicate_capability_declaration" in issues:
                duplicate_capability_plugins.append(plugin_id)
            if any(i.startswith("manifest_") for i in issues):
                manifest_inconsistent_plugins.append(plugin_id)
            if any(
                i
                in (
                    "invalid_plugin_type",
                    "invalid_lifecycle_state",
                    "invalid_health_state",
                    "invalid_implementation_status",
                    "invalid_capability",
                    "undeclarable_capability",
                )
                for i in issues
            ):
                invalid_contract_plugins.append(plugin_id)
            if "invalid_version_format" in issues:
                invalid_version_plugins.append(plugin_id)

        report = RegistryValidationReport(
            duplicate_plugin_ids=duplicate_ids,
            plugins_with_duplicate_capability_declarations=tuple(duplicate_capability_plugins),
            plugins_with_manifest_inconsistencies=tuple(manifest_inconsistent_plugins),
            plugins_with_invalid_contract_fields=tuple(invalid_contract_plugins),
            plugins_with_invalid_version_format=tuple(invalid_version_plugins),
            consistent=not (
                duplicate_ids
                or duplicate_capability_plugins
                or manifest_inconsistent_plugins
                or invalid_contract_plugins
                or invalid_version_plugins
            ),
        )
        return report

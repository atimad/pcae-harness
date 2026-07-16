# Phase 136P: Publication Schema Implementation (Implementation Group 5)

## Status

Complete. Implemented exactly `records/publication_attempt.schema.json` and
`records/publication_evidence.schema.json` (Implementation Group 5), plus
the third and final embedding site for the shared `cas_expectation` `$def`
in `shared/references.schema.json`. Legacy lifecycle remains the sole
production authority; CLTR remains derivative. Runtime remains Observed,
maximum capability remains observe, execution availability remains
unavailable.

## 1. Pre-implementation inventory checkpoint

| Item | Contract-derived result |
|---|---|
| Exact Group 5 record families | `PublicationAttempt` (`records/publication_attempt.schema.json`), `PublicationEvidence` (`records/publication_evidence.schema.json`) — derived from the frozen contract's own §46 grouping table, **not** the task prompt's "expected" three-family inventory |
| Required embedded shared definitions | `cas_expectation` (§24), third and final embedding site, in `publication_attempt.schema.json` only |
| Existing record count (pre-136P) | 7 |
| Expected record count after 136P | 9 |
| Existing manifest count (pre-136P) | 14 |
| Expected manifest count after 136P | 16 |
| Required Group 5 dependencies | `cutover_request`, `cutover_candidate`, `certification`, `authority_epoch` (all Group 2–4, already implemented); `publication_attempt` (intra-group, for `publication_evidence`) |
| Group 6+ families explicitly excluded | `ConcurrencyConflict`, `RecoveryJournalEntry`, `QuarantineRecord`, `ReconciliationResult`, `CompatibilityState`, `HistoricalAuthorityReference`, the three binding schemas |
| Contract/task discrepancies | See §2 below — **the task prompt's expected Group 5 inventory (including `ConcurrencyConflict`) is not the contract's Group 5** |

## 2. Contract/task discrepancy: exact Group 5 inventory

The active task prompt's "expected Group 5 inventory" was
`PublicationAttempt`, `PublicationEvidence`, `ConcurrencyConflict`, explicitly
flagged as "not authoritative" and subordinate to the frozen contract.

Independently re-deriving from
`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md` §46
("Schema implementation groups", which "restat[es] and freez[es] 136B §41's
file-level grouping as binding"):

```
| Group | Files                                                          | Prerequisite group(s) |
|   5   | human_authorization.schema.json                                | 1, 3, 4                |
|   6   | cutover_candidate.schema.json, certification.schema.json       | 1-5                    |
|   7   | publication_attempt.schema.json, publication_evidence.schema.json | 1-6                 |
|   8   | concurrency_conflict.schema.json, recovery_journal_entry.schema.json | 1-7            |
```

The contract's own §46 groups **do not** number 1:1 with this repository's
established `implementation_group` manifest tag / phase-sequence numbering
(each of which is a coarser, monotonically-increasing per-phase batch
counter, not the document's internal group index — e.g. 136L's manifest tag
`3` already covers both contract-groups 3 and 4; 136N's tag `4` already
covers contract-groups 5 and 6). This repository-level renumbering is itself
already disclosed and accepted precedent (see 136M's own
`test_136m_independent_group3_inventory_is_exactly_request_and_readiness`
docstring, which discloses the same phenomenon for `cutover_request`/
`readiness_package`).

Given that precedent, the next phase-sequence batch (this repository's
"Group 5", manifest tag `5`) would naively be expected to cover contract-
groups 7 **and** 8 combined (mirroring 136L's 3+4 and 136N's 5+6 merges).
However:

- Contract-group 8 is `{ConcurrencyConflict, RecoveryJournalEntry}` as an
  **atomic pair** — §46's own row lists them together, and
  `CSCH-EXEC-REQ-062` requires each of the 11 contract-groups to receive its
  own independent verification before the next begins, meaning a
  contract-group's two files are not meant to be split across separate
  implementation phases.
- The active task's own "Strict 136P No-Go Boundary" explicitly forbids
  `RecoveryJournal` in this phase.
- Splitting `ConcurrencyConflict` out of its atomic pairing with
  `RecoveryJournalEntry` to satisfy the task prompt's suggested three-family
  list would violate `CSCH-EXEC-REQ-062`'s per-group atomicity and the
  frozen contract's own binding grouping — an unauthorized broadening the
  task's own instructions ("If the frozen contract defines a different
  Group 5 inventory: follow the frozen contract; document the discrepancy;
  implement only the contract-defined inventory") explicitly forbid.

**Resolution:** this repository's "Group 5" (manifest tag `5`, this phase)
is exactly contract-group 7: `{PublicationAttempt, PublicationEvidence}`.
`ConcurrencyConflict` is **not** implemented in this phase; it remains
paired with `RecoveryJournalEntry` for a future phase (contract-group 8,
this repository's presumptive future "Group 6"). This is documented,
disclosed, and not silently resolved — the task prompt's own expected
inventory was demonstrably wrong against the frozen contract's binding text,
and the frozen contract governs.

## 3. Field tables (from §25/§26)

### 3.1 `PublicationAttempt` (Tier 1 strict)

| Field | Required | Type |
|---|---|---|
| `migration_epoch` | yes | `migration_epoch` |
| `transition_id` | yes | `transition_identity` (§7.2: attempt is transition_id-required, not phase_id-required) |
| `attempt_id` | yes | deterministic digest-shaped identifier (bound-field tuple: `request_reference` + `candidate_reference` + `attempt_sequence`), never timestamp-derived alone |
| `request_reference` | yes | `record_reference` → `cutover_request`, schema_id/schema_version required |
| `candidate_reference` | yes | `record_reference` → `cutover_candidate`, schema_id/schema_version required |
| `certification_reference` | yes | `record_reference` → `certification`, schema_id/schema_version required |
| `cas_expectation` | yes | embedded `$def`, third and final site |
| `source_authority_reference`, `target_authority_reference` | yes (both) | `record_reference` → `authority_epoch`, no schema_id/schema_version required (mirrors `certification.epoch_reference` precedent) |
| `attempt_sequence` | yes | non-negative integer, monotonic per `request_reference` (Layer 4) |
| `temporary_pointer_reference` | conditional, undisclosed §16 trigger | `record_reference`, left freely optional (NON-BLOCKING-136P-1) |
| `state` | yes | shared `PublicationState` (§8.5, 12 values) |
| `uncertainty` | conditional | required iff `state == "publication_uncertain"` |
| `failure_classification` | conditional | required iff `state` in `{gate_rejected, conflict}` |
| `limitations`, `authority_disclosure` | yes | standard; `authority_role` locally forbidden from `authoritative` |

### 3.2 `PublicationEvidence` (Tier 1 strict)

| Field | Required | Type |
|---|---|---|
| `migration_epoch` | yes | `migration_epoch` |
| `transition_id` | yes | `transition_identity` |
| `attempt_reference` | yes | `record_reference` → `publication_attempt`, schema_id/schema_version required |
| `outcome` | yes | local `PublicationOutcome` enum (8 values, home schema this file) |
| `uncertainty_detail` | conditional | required iff `outcome == "publication_uncertain"`; object `{last_known_state, retry_recommended}` |
| `target_readback` | conditional | required iff `outcome == "published_and_verified"`; generic `record_reference` |
| `authoritative_generation` | conditional | required iff `outcome == "published_and_verified"`; `generation_reference` shape (mirrors `authority_state.authoritative_generation`) |
| `limitations`, `authority_disclosure` | yes | standard; `authority_role` **may** structurally be `authoritative` (§9 exception), `is_authoritative` remains const false regardless (NON-BLOCKING-136P-2, mirrors NON-BLOCKING-136J-1) |

## 4. Record-local enums

- `PublicationOutcome` (8 values: `not_attempted`, `cas_rejected`,
  `failed_before_replacement`, `publication_uncertain`,
  `published_and_verified`, `post_publication_verification_failed`,
  `conflict`, `quarantined`) — home schema `publication_evidence.schema.json`
  per §8.8; declared locally (inline `enum`), not centralized in
  `shared/enums.schema.json`, matching all 13 other local-enum families'
  precedent.
- No new shared enum was added. `PublicationState` (shared, §8.5) was
  already defined in `shared/enums.schema.json` at Phase 136H and is reused
  by `publication_attempt.state` unchanged.

## 5. Embedded/shared definitions

`cas_expectation` (`shared/references.schema.json#/$defs/cas_expectation`)
is reused unchanged in structure at its third and final embedding site,
`publication_attempt.schema.json`. Only the file's own `description` text
was updated to record that all three sites now exist (Group 4's two plus
Group 5's one); no field, requiredness, or shape changed. No standalone
`CASExpectation` record family was created. No new or conflicting CAS
shape was introduced.

## 6. Dependency / identity / digest graphs

**`$ref` graph:** `publication_attempt.schema.json` depends on `envelope`,
`identity`, `digest`, `enums`, `references`, `failures`, `limitations`
(all Group 1). `publication_evidence.schema.json` depends on `envelope`,
`identity`, `digest`, `enums`, `references`, `limitations` (no `failures`
dependency — it declares no `reason_code` field). Neither file `$ref`s the
other, or any Group 6+ file. Acyclic (confirmed by
`test_136p_manifest_group5_entries_do_not_depend_on_each_other` and
`test_136p_manifest_group5_dependencies_are_direct_ref_targets`).

**Record identity graph:** `PublicationAttempt` binds to `CutoverRequest`,
`CutoverCandidate`, `Certification`, and `AuthorityEpoch` (all pre-existing
Group 2–4 families) via `record_reference`. `PublicationEvidence` binds only
to `PublicationAttempt`. No cycle: `CutoverRequest`/`ReadinessPackage` →
`HumanAuthorization` → `CutoverCandidate`/`Certification` →
`PublicationAttempt` → `PublicationEvidence`.

**Digest graph:** identical shape to the identity graph — every reference
carries an `id`+`digest`+`family` tuple; no record's digest computation
depends on a later-created record's digest.

**Valid creation order:** `AuthorityEpoch` → `AuthorityState` →
`ReadinessPackage` → `CutoverRequest` → `HumanAuthorization` →
`CutoverCandidate` → `Certification` → `PublicationAttempt` →
`PublicationEvidence`. No `-v2` or re-creation mechanism is used or needed.

## 7. Strictness tiers

Both `PublicationAttempt` and `PublicationEvidence` are Tier 1 (strict,
`additionalProperties: false`, no `_extensions`), matching §14's explicit
8-file Tier 1 list (which names `publication_attempt` and
`publication_evidence` alongside `authority_epoch`, `authority_state`,
`cutover_request`, `human_authorization`, `certification`, and the embedded
`cas_expectation`). Neither schema copies `CutoverCandidate`'s Tier 2
`_extensions` behavior — confirmed unnecessary and unimplemented by
`test_136p_attempt_extensions_key_rejected_tier1` and
`test_136p_evidence_extensions_key_rejected_tier1`.

## 8. Family-specific references

Every cross-family reference field on both new schemas is restricted via a
local `$defs` entry combining `record_reference` with a `const` restriction
on `record_family`. Wrong-family substitution is attacked exhaustively
across all 16 record families for `request_reference`,
`candidate_reference`, `certification_reference`,
`source_authority_reference`, `target_authority_reference` (on
`PublicationAttempt`) and `attempt_reference` (on `PublicationEvidence`);
every non-matching family is confirmed rejected.

## 9. `PublicationAttempt` boundary

Implemented exactly as a record describing an attempted publication
operation: stable deterministic `attempt_id`, candidate/certification/
request/readiness lineage (via candidate/certification references),
source/target authority references, embedded `cas_expectation`,
`PublicationState`, monotonic `attempt_sequence`, conditional uncertainty/
failure disclosure, `limitations`, `authority_disclosure` (authoritative
forbidden). It does **not** perform publication, invoke CAS, mutate a
pointer, prove a publication occurred, prove CAS succeeded, activate CLTR
authority, demote/retire legacy authority, notify, or create markers/
receipts — no code path exists anywhere in this schema file capable of any
of those actions; it is pure JSON Schema.

## 10. `PublicationEvidence` boundary

Implemented exactly as evidence describing a claimed publication outcome:
attempt reference, local `PublicationOutcome` (8 structurally distinct
values), conditional uncertainty detail, conditional target-readback +
authoritative-generation (gated to the terminal `published_and_verified`
outcome), `limitations`, `authority_disclosure`. Schema validity never
proves the claimed outcome is true, never activates authority, and never
replaces semantic verification, recovery evidence, or lifecycle authority.

## 11. `ConcurrencyConflict` boundary

**Not implemented in this phase** — see §2's discrepancy disclosure.
Deferred, alongside `RecoveryJournalEntry`, to a future phase.

## 12. CAS expectation reuse

Confirmed: `publication_attempt.schema.json` embeds the unchanged,
contract-frozen `cas_expectation` `$def`; no standalone `CASExpectation`
family was created; no conflicting shape was introduced; no schema implies
CAS execution or success anywhere. All 11 expected-state fields remain
unconditionally required (tested:
`test_136p_attempt_cas_expectation_no_field_is_omittable`,
parametrized over all 11 fields).

## 13. Manifest delta

Two new entries added, `implementation_group: 5`:

| `file_path` | `family` | Dependencies |
|---|---|---|
| `records/publication_attempt.schema.json` | `publication_attempt` | envelope, identity, digest, enums, references, failures, limitations |
| `records/publication_evidence.schema.json` | `publication_evidence` | envelope, identity, digest, enums, references, limitations |

`shared/references.schema.json`'s manifest entry `file_digest` was updated
(description-only content change: the `cas_expectation` docstring now
reflects all three embedding sites existing). No dependency-list or shape
change. Total manifest entries: 14 → 16. Total registered schema resources
(including `manifest.schema.json`): 15 → 17.

Every declared Group 5 dependency was independently confirmed to be an
actual `$ref` target in the corresponding file's text (no spurious
dependency was introduced, unlike 136N's `human_authorization`/
`certification` → `shared/enums.schema.json` instance of
`NON-BLOCKING-136M-2`, reproduced again in 136O — this phase does not
repair those two Group 4 entries, per the task's own instruction not to
broaden 136P into that repair unless a Blocking interaction is proven, and
none was found).

## 14. Registry behavior

`build_offline_registry` loads all 17 resources with unique `$id`s,
deterministic (sorted) order, confirmed stable across repeated builds and
across a subprocess invocation.

## 15. Fixtures

`tests/test_cltr_cutover_136p_publication_schema.py` provides, for each of
the two new families: a minimal valid record, valid records for every
non-conditional enum value, valid records for every conditional branch
(`publication_uncertain`, `gate_rejected`/`conflict`,
`published_and_verified`), wrong-family reference attacks across all 16
families per reference field, malformed digest/timestamp attacks, unknown
top-level field rejection, `_extensions` rejection (Tier 1), null
`cas_expectation` rejection, and every one of the 11 `cas_expectation`
sub-field omission attacks. No fixture contains a real secret, password, or
credential.

## 16. Package inclusion / installed-wheel verification

Fresh wheel and sdist builds (`test_schema_runtime_packaging.py`,
`test_136f_wheel_contains_smoke_schema_and_no_stage3_record_schema` /
`_sdist_...`) confirm exactly the 9 expected `records/` files are packaged,
including both new Group 5 files, and no Group 6+ file. Isolated-checkout
fixture validation
(`test_136p_group5_fixtures_validate_outside_repository_checkout`) confirms
both new schemas validate correctly from a copied tree outside the
repository checkout.

## 17. No-network / no-authority / no-publication / no-execution proofs

- `test_136p_no_network_during_registry_and_validation` blocks
  `socket.socket`/`socket.create_connection` and confirms registry
  construction and validation still succeed offline.
- `test_136p_no_authority_resolver_symbol_referenced_in_new_schema_text` and
  `test_136p_no_authority_pointer_or_state_persistence_path_referenced`
  confirm no authority-resolver symbol or `.pcae/cltr-authority/` path
  string appears in either new schema file.
- `test_136p_no_persistence_directory_created_during_validation` and
  `test_136p_validation_never_mutates_input_record` confirm validation is
  side-effect-free.
- No `.pcae/cltr-authority/` directory exists anywhere in the repository
  (independently confirmed at governed-startup inspection and again before
  finalization).
- No subprocess, shell, socket, or dynamic-execution string appears in
  either new schema file's raw text
  (`test_136p_no_subprocess_shell_socket_or_dynamic_execution_in_new_files`).

## 18. Inherited-finding dispositions

| Finding | Disposition under Group 5 |
|---|---|
| Generic record-ID prefix convention (136M/136K) | Unchanged. `attempt_id` reuses the generic `record_identity` shape (same pattern as `record_id`), consistent with prior families; no new prefix convention invented. |
| Manifest authoring metadata not cross-checked (`NON-BLOCKING-136M-2`) | Not reproduced in Group 5 — every declared dependency for the two new entries was independently confirmed as an actual `$ref` target. The existing Group 4 instance (`human_authorization`/`certification` → `enums.schema.json`) is left unrepaired, per task scope. |
| Layer 4 semantic invariants (136M) | Unchanged; Group 5 introduces no semantic validator. `attempt_sequence` monotonicity, `attempt_id` determinism recomputation, and CAS/publication truth all remain explicitly Layer 4/5/6, disclosed in-schema. |
| Tier 2 extension risk (136M) | Not applicable — both Group 5 schemas are Tier 1 (no `_extensions`). |
| 136N's 8 disclosed `NON-BLOCKING`/`DEFERRED` findings (scope-gap fills, self-reference, `generation_reference` typing precedent, etc.) | Unchanged; none interact with Group 5's new fields. `human_authorization.use_binding`'s forward reference to `publication_attempt` (previously a shape-only forward reference to a not-yet-existing family) is now resolved to a real, existing family — no schema text change was needed for this resolution to become effective, since the reference was already correctly family-restricted. |
| `NON-BLOCKING-136O-1` (spurious `shared/enums.schema.json` dependency on `human_authorization`/`certification`) | Unchanged; not repaired in this phase (no Blocking interaction found); not reproduced in either new Group 5 entry. |

New findings this phase:

- `NON-BLOCKING-136P-1`: §25's `temporary_pointer_reference` field is
  documented as "present only during in-flight publication" but §16's local
  conditional-validation table names no enum value that triggers its
  requirement or forbiddance. Left freely optional; no unfrozen if/then
  invented.
- `NON-BLOCKING-136P-2`: `PublicationEvidence`'s conditional
  `authority_role: "authoritative"` permission (§9) is not expressed as a
  local schema-level conditional tying it to `outcome ==
  "published_and_verified"` — `is_authoritative` remains unconditionally
  `const false` regardless, mirroring `NON-BLOCKING-136J-1`'s identical
  disposition for `AuthorityState`.

## 19. Lifecycle-reporting debt disclosure

136O independently discovered that 136N's committed
`.pcae/phase-completion-report.md` retitled itself to "Phase 136N Complete"
while its body remained verbatim 136M content — inherited lifecycle/
reporting debt, not a schema defect. This phase's own canonical report and
metadata were independently verified before finalization to contain 136P's
own content, the exact title "Publication Schema Implementation", and only
136P-owned commits — no stale prior-phase body content was retained (see
§20).

## 20. Limitations / deferred work

- Semantic validation (Layer 4+) for all cross-record invariants
  (`attempt_sequence` monotonicity, `attempt_id` determinism, CAS/
  publication truth, authority resolution) remains future work, not built
  by this phase.
- `ConcurrencyConflict` and `RecoveryJournalEntry` (contract-group 8)
  remain deferred to a future phase.
- No recovery schema, reconciliation function, quarantine record,
  notification/marker/receipt binding, compatibility state, historical
  reference, typed model, or authority resolver/persistence/pointer exists.
- `NON-BLOCKING-136P-1` and `NON-BLOCKING-136P-2` (above) remain open,
  non-blocking disclosures.

## 21. Required regression runs

- 136P focused tests: 113/113 passed
  (`tests/test_cltr_cutover_136p_publication_schema.py`).
- 136O independent Group 4 tests: passed (part of combined run below).
- 136N Group 4 implementation tests: passed (migrated for Group 5
  legitimacy: manifest/registry counts 14→16 / 15→17; `LATER_GROUP_*`
  lists updated to remove `publication_attempt`/`publication_evidence`).
- 136M/136L/136K/136J/136I/136H: all migrated and passed (same count/list
  updates applied, mirroring the bounded migration discipline used at
  136L→136N).
- Combined `test_cltr_cutover_136*` + `test_schema_runtime_*` suite:
  1008/1008 passed (excluding `slow`-marked packaging tests), plus 4
  packaging tests (wheel/sdist build + install) passed separately.
  Combined with the 113 new 136P tests: 1121/1121.
- Fast Green: 4391/4391 passed, identical to the 136H–136O baseline, zero
  regressions.
- Full unmarked suite: see final confirmation before finalization.

## 22. Recommended next phase

If 136P completes with zero unresolved Blocking findings: **136Q —
Publication Schema Independent Verification**, per the frozen contract and
this repository's established per-group independent-verification
precedent. Must independently attack the exact Group 5 inventory (as
corrected in §2 of this document, not the task-prompt's original
suggestion), all field tables, CAS expectation reuse, publication-attempt/
evidence separation, graph acyclicity, family restrictions, manifest
correctness, packaging, and offline/no-authority/no-publication/no-execution
behavior.

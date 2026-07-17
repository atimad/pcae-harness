## Status

Phase 136U — Notification/Marker/Receipt Authority Binding Schema Independent
Verification (Implementation Group 10). Complete.

---

## 0. Purpose and scope

Independently re-derive, and attempt to falsify, every material claim made
by Phase 136T (`docs/PHASE_136_NOTIFICATION_MARKER_RECEIPT_BINDING_SCHEMA_IMPLEMENTATION.md`,
commits `643d8042`/`f53d1384`) about CLTR-CUTOVER-EXECUTABLE-SCHEMAS-001 v1.0
Implementation Group 10: `NotificationAuthorityBinding`,
`MarkerAuthorityBinding`, `FinalizationReceiptAuthorityBinding`.

This phase does not implement Group 11, `CompatibilityState`,
`HistoricalAuthorityReference`, derived views, Stage 3 typed models, broad
semantic validation, notification dispatch, marker creation, receipt
creation, or authority resolution/persistence. Legacy lifecycle remains the
sole production authority; CLTR remains derivative.

---

## 1. Methodology

Every fixture, graph, and assertion in
`tests/test_cltr_cutover_136u_notification_marker_receipt_binding_independent_verification.py`
was authored fresh from the schema files on disk and the frozen contract
text (re-read directly from
`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md` §9,
§16, §31, §32, §33, §46), not from 136T's own test file, fixtures, or prose.
Where 136T's implementation document disclosed a discrepancy or a deferred
gap, this phase independently re-derived the same clause from the contract
text before agreeing or disagreeing with 136T's resolution — 136T's
classification was never accepted merely because 136T asserted it.

Independent checks performed: contract re-derivation (§9/§16/§31/§32/§33/§46
read directly, not summarized secondhand); schema-file field-by-field
comparison against the frozen tables; manifest/registry byte-level digest
recomputation; a fresh $ref/dependency-graph acyclicity proof; fresh
adversarial fixtures (155 independently authored test cases, 1 skip);
regression re-runs of all 20 prior Group 1–10 test modules plus
schema-runtime; a fresh wheel/sdist build; an isolated (`/tmp`, outside the
checkout) installed-wheel offline exercise with `socket.socket`/
`socket.create_connection` monkeypatched to raise; and source-tree greps for
dispatch/marker-write/receipt-write/authority-resolver modules and for any
runtime reference to the three Group 10 families outside
`schema_resources/`.

---

## 2. Group 9 exclusion — independently re-derived

Section 46's group table (`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md:1665`)
reads, verbatim:

> `9 | Reconciliation function + HistoricalAuthorityReference typed model (no
> schema file for either) | 1–8 | yes`

This is an explicit, frozen, textual assignment of **zero** schema files to
Group 9 — not an omission, not an implementation shortcut. Section 35
(HistoricalAuthorityReference) independently confirms this from the other
direction: "Row 20 (§4): **no executable schema — runtime-only typed
model.**" No document anywhere in `docs/`, no file anywhere in `src/` or
`tests/`, and no manifest/registry entry names `reconciliation_result` or
`historical_authority_reference`. `tests/test_cltr_cutover_136u_...py`'s
`test_136u_group9_has_no_schema_file_anywhere` and
`test_136u_manifest_has_no_group9_entry` independently confirm this on disk
and in the manifest. **136T's Group 9 exclusion is CONFIRMED, not Blocking.**

---

## 3. Exact Group 10 inventory — independently verified

Manifest `implementation_group == 10` entries, re-read directly from
`src/pcae/schema_resources/cltr_cutover/manifest.json`:

- `marker_authority_binding`
- `notification_authority_binding`
- `receipt_authority_binding`

Exactly these three, no fourth entry, no generic `authority_binding`, no
`_v2` variant, no early Group 11 resource
(`test_136u_manifest_records_exactly_three_group10_entries`,
`test_136u_no_generic_or_versioned_binding_families_exist`). All three
schema files exist on disk under `records/`. **CONFIRMED.**

---

## 4. Group 10 prerequisites — independently verified

Section 46's own row for Group 10:
`1, 2, plus existing PFN-001 identities`.

Structurally verified two ways:

- **Manifest dependency edges.** Every dependency declared by any of the
  three Group 10 manifest entries resolves to an `implementation_group == 1`
  (shared-core) entry only — never Group 2, never Group 3–8
  (`test_136u_group10_prerequisites_are_group1_group2_and_pfn001_only`).
  Group 2 (`AuthorityEpoch`/`AuthorityState`) is therefore a *conceptual/
  vocabulary* prerequisite (the closed `record_family` enum value
  `authority_epoch`, reused by `notification_authority_binding`'s
  `authority_epoch_reference` family restriction), not a manifest `$ref`
  dependency — confirmed by
  `test_136u_no_group10_manifest_dependency_on_authority_epoch_or_authority_state_files`,
  which asserts no Group 10 entry's `dependencies` list names either
  `authority_epoch.schema.json` or `authority_state.schema.json` directly.
- **PFN-001 identities.** `docs/PHASE_128_PHASE_FINALIZATION_NOTIFICATION_CONTRACT.md`
  §4 defines PFN-001 as a governance invariant ("exactly one trusted
  canonical phase report... or an explicit, durable delivery-failure
  record"), not an identity-format or enum specification. No dedicated
  "PFN-001 classification vocabulary" enum exists anywhere in
  `src/pcae/` outside this schema's own bounded printable-ASCII string
  field. The `pfn001_classification` field's own description ("restates the
  existing PFN-001 classification vocabulary; not redefined here") is
  therefore accurate: there is nothing further to redefine, and the schema
  correctly does not invent one.

Neither missing nor spurious dependency on Groups 3–8 was found.
**136T's prerequisite interpretation is CONFIRMED.**

---

## 5. Manifest, registry, and count verification — independently recomputed

| Claim | Independently recomputed value | Match |
|---|---|---|
| Total manifest entries | 21 | yes |
| Shared-core entries (Group 1) | 7 | yes |
| Non-shared record entries | 14 | yes |
| Group 10 entries | 3 | yes |
| Group 9 entries | 0 | yes |
| Group 11 entries | 0 | yes |
| Manifest `file_digest` values match `sha256(actual file bytes)` | 21/21 match, 0 mismatches | yes |
| Registry (`build_offline_registry`) resource count | 22 | yes |
| Registry − manifest set difference | exactly `{manifest.schema.json}` | yes, explains the 22-vs-21 gap |

The +1 registry-vs-manifest gap is `manifest.schema.json` itself — a schema
resource the offline registry loads (because it validates the manifest
document's own shape) but which is deliberately never listed as an entry
*of* the manifest it describes. This is architecturally sound, not an
unexplained mismatch (`test_136u_registry_has_exactly_twenty_two_resources`).

**All counts CONFIRMED, byte-for-byte.**

---

## 6. `NotificationAuthorityBinding` field verification (§31)

Reconstructed field table from `records/notification_authority_binding.schema.json`
against §31's frozen text: `authoritative_generation_reference`,
`authority_epoch_reference`, `payload_digest`, `attempt_identity`,
`pfn001_classification`, `delivery_state` (unconditionally required);
`uncertainty`, `marker_reference`, `receipt_reference` (conditionally
required per `delivery_state`); `limitations`, `digest`
(→ `record_digest`, envelope-normalized, see §9 below).

Independently attacked and confirmed:

- Every required field's absence is rejected
  (`test_136u_notification_each_required_field_rejected_if_absent`, 16
  fields parametrized).
- Unknown top-level fields rejected; `phase_id`/`transition_id` (not in
  §7.2's required-family lists for this family) are rejected as unknown
  fields, not silently accepted.
- `delivery_state` is a closed 3-value enum (`not_dispatched`,
  `already_dispatched`, `payload_conflict`); unknown values rejected.
- `authoritative_generation_reference` requires the narrower
  `generation_reference` (id+digest only) shape — a full `record_reference`
  (id+digest+family) is *rejected*, confirming the shape choice is
  enforced, not merely documented
  (`test_136u_notification_authoritative_generation_reference_is_generation_shape_not_record_reference`).
- `authority_epoch_reference` is family-locked to `authority_epoch`; every
  other family tested is rejected.
- `payload_digest` rejects non-hex, wrong-length, uppercase, and
  `sha256:`-prefixed variants — confirming §11's bare-hex-only digest
  contract is enforced here too.

**§31 field table CONFIRMED, no falsification found.**

---

## 7. Notification `delivery_state` conditional branches — independently re-derived and exhaustively tested

All three conditional branches named in §31's field table were tested at
every state, not just the documented positive case:

- `not_dispatched` ⇒ `marker_reference` and `receipt_reference` both
  forbidden (tested; presence of either is rejected).
- `already_dispatched` ⇒ `marker_reference` **and** `receipt_reference`
  both required together (each in isolation rejected; both present is the
  only valid combination); `uncertainty` is forbidden in this branch.
- `payload_conflict` ⇒ `uncertainty` and `marker_reference` both required;
  `receipt_reference` is forbidden even if a marker reference is present
  (tested explicitly — a record claiming both `payload_conflict` and
  `receipt_reference` is rejected, confirming the receipt-reference gate is
  keyed strictly to `already_dispatched`, not "any dispatched state").
- `marker_reference`/`receipt_reference`, when present, are family-locked;
  cross-substituting a receipt reference into `marker_reference` (or vice
  versa) is rejected.

No branch permits a schema-valid record that implies actual delivery,
exactly-once behavior, or Telegram acceptance — the `authority_disclosure`
struct's own description states this explicitly and the schema carries no
mechanism (no HTTP client, no dispatch call, nothing reachable from this
package) that could prove it. **CONFIRMED.**

---

## 8. `MarkerAuthorityBinding` field verification (§32)

Reconstructed field table against `records/marker_authority_binding.schema.json`:
`generation_reference`, `created_at`, `state`,
`compatibility_fallback_forbidden`, `authority_role` (→
`authority_disclosure.authority_role`), `digest` (→ `record_digest`) all
unconditionally required; `duplicate_of` conditionally required iff
`state == "conflict"`.

Independently attacked and confirmed:

- All 13 required fields individually rejected when absent.
- `state` is a closed 4-value enum (`absent`, `written`, `stale`,
  `conflict`); unknown values rejected.
- `compatibility_fallback_forbidden` is pinned `const: true` — `false` is
  rejected, meaning no schema-valid record can even *claim* the fallback
  prohibition is lifted.
- `duplicate_of`: absent when `state != "conflict"` even if supplied is
  rejected (over-supply, not just under-supply, is caught); required key
  present but `null` is valid when `state == "conflict"` (first-marker
  case, duplicate not yet known); a `record_reference` value is valid when
  `state == "conflict"`; wrong-family reference (e.g. pointing at a
  `notification_authority_binding`) inside `duplicate_of` is rejected.
- `generation_reference` requires the narrower `generation_reference`
  shape — a full `record_reference` is rejected, same pattern as
  Notification's field.

**§32 field table CONFIRMED, no falsification found.**

---

## 9. `FinalizationReceiptAuthorityBinding` field verification (§33) and Section 16 conditional review

Reconstructed field table against `records/receipt_authority_binding.schema.json`:
`generation_reference`, `receipt_state` (→ `authority_role`/`digest`
envelope-normalized) unconditionally required;
`publication_evidence_reference` and `marker_reference` conditionally
required *together* iff `receipt_state == "finalized"`;
`staleness_check` freely optional (§4 below).

**Section 16 conflict, independently re-derived.** §33's field table marks
`generation_reference`, `publication_evidence_reference`, and
`marker_reference` all "yes" (unconditionally required) in its summary
column, but its own prose ties the latter two to "the finalized-state
bundle," and §16's local conditional-validation table states explicitly:
`receipt_authority_binding.receipt_state == "finalized"` ⇒ "all of
`marker_reference`, `publication_evidence_reference`, `generation_reference`
required." Independently confirmed: §16 is a dedicated, explicit
per-condition table with its own row for this exact record family and this
exact condition; §33's "yes" column is a summary that predates and is less
specific than that row. Under ordinary contract-interpretation practice
(the more specific, more recently-stated clause governs; this repository's
own established precedent — `NON-BLOCKING-136N-2`, `NON-BLOCKING-136P-1`,
and 136L's `NON-BLOCKING-136L-2` all independently apply the identical
"specific table over summary text" resolution rule to earlier groups), §16
governs. 136T's resolution (keep `generation_reference` unconditionally
required — its "wrong-generation receipt" purpose is state-independent —
and make the other two conditionally required together only under
`receipt_state == "finalized"`) is the only resolution consistent with both
§16's explicit rule and the field table's own prose. **Independently
re-derived and CONFIRMED, not merely restated.**

Exhaustively tested:

- `finalized` with neither reference: rejected. `finalized` with only one
  of the two: rejected (both directions tested individually). `finalized`
  with both: valid.
- Every non-`finalized` state (`absent`, `stale`, `conflict`) with either
  reference present: rejected — confirming the "forbidden otherwise" half
  of the `if`/`then`, not just the "required iff" half.
- `generation_reference` required regardless of `receipt_state`, tested
  across all four state values including `finalized` (with the other two
  fields correctly supplied) — confirming `NON-BLOCKING-136T-6`'s
  resolution is actually enforced, not merely documented.
- `marker_reference`/`publication_evidence_reference`, when present, are
  family-locked; cross-substitution rejected both directions.

**§33 field table and §16 conditional logic CONFIRMED, no falsification found.**

---

## 10. `staleness_check` disposition (`DEFERRED-136T-1`) — independently assessed

§33's own text specifies only staleness_check's trigger condition
("required iff a recovery journal entry references this receipt" — an
explicitly cross-document condition, unenforceable at Layer 2/single-
document schema validation per §16's own scope rule) and its bare type
(`object`). No field table for its internal shape exists anywhere in the
frozen contract — confirmed by exhaustive grep of
`docs/PHASE_136_STAGE_3_COMPANION_EXECUTABLE_SCHEMA_CONTRACT_FREEZE.md` for
`staleness_check` (only §33's two mentions exist; no `$def`, no
sub-table, no cross-reference to a shared definition file).

Independently tested: the field is optional (absent record is valid);
`{}` is the only accepted non-absent value; a non-empty object,  `null`,
a string, a number, an array, and a boolean are all rejected
(`test_136u_receipt_staleness_check_accepts_only_empty_object`).

**Classification: DEFERRED, Non-Blocking, independently confirmed.** An
empty-shape placeholder (`additionalProperties: false`, no properties) is
the narrowest possible conformant representation given a contract that
specifies a bare type and nothing else; it deliberately refuses to invent
unauthorized structure. This does not block trustworthy completion of
Group 10 — no Group 10 record depends on `staleness_check`'s eventual
internal shape for any of its own field-table requirements — and remains
correctly deferred pending a future contract amendment, exactly as 136T
disclosed.

---

## 11. Authority-role prohibition (§9) — independently verified on all three schemas

§9's binding rule names all three binding schemas among its 12-file list
where `authority_role: "authoritative"` is forbidden via
`not: {"const": "authoritative"}`.

Independently confirmed on all three schema files
(`test_136u_authoritative_role_locally_forbidden_on_all_three_bindings`,
parametrized): a record asserting `authority_role: "authoritative"` is
rejected on `notification_authority_binding`, `marker_authority_binding`,
and `receipt_authority_binding` alike. All six other `AuthorityRole` enum
values (`derivative`, `operational`, `evidence`, `compatibility`,
`historical`, `quarantined`) are independently confirmed valid on all
three schemas — the restriction is precise, not an accidental
over-restriction to a single role.

Additional adversarial probes, all confirmed closed:

- Case/whitespace variants (`Authoritative`, `AUTHORITATIVE`,
  `authoritative `) are rejected — not because the `not: const` restriction
  catches them (it wouldn't; they aren't the literal string), but because
  the enclosing `AuthorityRole` enum itself is closed and none of those
  variants is a member. No alias/case-fold bypass exists.
  (`test_136u_authoritative_role_case_variant_not_a_bypass`)
- `is_authoritative: true` cannot be forced independently of
  `authority_role` — the shared `authority_disclosure` `$def` pins
  `is_authoritative` to `const: false` unconditionally; supplying `true` is
  rejected outright regardless of the accompanying role.
  (`test_136u_is_authoritative_cannot_be_forced_true`)
- `_extensions` cannot smuggle an authoritative claim: a string-valued key
  literally named `authority_role` inside `_extensions` is schema-valid
  (extensions are opaque forward-compatible strings, never interpreted),
  but the top-level `authority_disclosure.authority_role` field remains the
  only field with authority meaning and remains independently forbidden
  from equaling `authoritative`.
  (`test_136u_extensions_cannot_smuggle_authoritative_claim`)

**§9 prohibition CONFIRMED on all three schemas; no bypass found.**

---

## 12. Tier 2 / `_extensions` boundary — independently verified

All three schemas confirmed Tier 2 (§14): `_extensions` absent is valid;
present with a flat string-valued map is valid; nested object/array values
inside `_extensions` are rejected; non-string scalar values (`int`, `null`,
`bool`, list) inside `_extensions` are rejected; `_extensions` itself as
`null`/scalar/array is rejected; a *differently*-named extension key
(`extensions`, `_extension`) is rejected — confirming the literal single
reserved key, not a pattern-matched family of keys, is what's permitted.

**§14 Tier 2 boundary CONFIRMED on all three schemas.**

---

## 13. PFN-001 identity verification

See §4 above for the prerequisite-level PFN-001 analysis. At the field
level: `attempt_identity` uses the generic `record_identity` shape (§10) as
a bare opaque token — not itself a `record_reference` and not validated
against any external identity provider. `pfn001_classification` is a
bounded (1–256 char), printable-ASCII-only, single-line string — no closed
enum, matching the contract's own explicit instruction not to redefine the
PFN-001 vocabulary here. Neither field's schema-validity implies the
referenced dispatch attempt or classification value corresponds to any real
PFN-001 event. **CONFIRMED, no invented identity structure found.**

---

## 14. Sibling independence and dependency/identity/digest graphs — independently rebuilt

Four independently authored graphs, from scratch, over the full Group 1–10
manifest:

1. **Manifest dependency graph.** No Group 10 sibling's `dependencies` list
   names another Group 10 sibling, directly or (recursively verified)
   transitively (`test_136u_manifest_group10_siblings_declare_no_cross_sibling_dependency`,
   `test_136u_full_ref_graph_has_no_self_cycle_or_group10_sibling_cycle`).
2. **Full $ref/manifest graph acyclicity.** A depth-first traversal over all
   21 manifest entries' declared dependencies terminates without revisiting
   an in-progress node — the graph is acyclic, and a valid topological
   order exists (every entry visited exactly once).
3. **Record identity graph.** All three Group 10 `record_id` values match
   the identical generic `record_identity` pattern; nothing at the
   identity-shape level distinguishes or binds the three families to one
   another — family separation happens via `record_type`/`schema_id`
   const fields, not the identity pattern.
4. **Record digest graph.** Assigning an identical `record_digest` string
   across all three families' fixtures independently is schema-valid — Layer
   2 performs no cross-document digest comparison, confirming digest fields
   carry no structural cross-record binding at the shape level (that
   binding, where it exists at all, is via explicit `*_reference` fields,
   not via digest equality).

**All three siblings independently creatable with no forced ordering**
(`test_136u_all_three_bindings_creatable_independently_no_forced_ordering`):
minimal valid `NotificationAuthorityBinding` (`not_dispatched`), minimal
valid `MarkerAuthorityBinding` (`absent`), and minimal valid
`FinalizationReceiptAuthorityBinding` (`absent`) each validate with zero
reference to either other sibling present.

**No immutable sibling cycle found. CONFIRMED.**

---

## 15. Atomic group completeness

A manifest with the `receipt_authority_binding` entry removed (while the
other two Group 10 entries and all Group 1–8 entries remain) fails
`load_and_verify_manifest`'s completeness check
(`ManifestIntegrityError`) — confirming a partial Group 10 delivery is
structurally distinguishable and fails closed at the manifest-verification
layer, not silently accepted
(`test_136u_group10_partial_manifest_is_structurally_distinguishable`).
This is schema/manifest-level atomicity detection, not runtime persistence
atomicity — no runtime write path exists for any Group 10 record in this
phase, so "atomic delivery" here means exactly, and only, "an incomplete
manifest is rejected," which is what was tested.

---

## 16. Manifest and registry integrity — independently recomputed

- All 21 manifest `file_digest` values independently recomputed
  (`hashlib.sha256`) against the actual file bytes on disk: 0 mismatches.
- `load_and_verify_manifest` against the real, on-disk manifest returns
  exactly 21 verified entries.
- A tampered `notification_authority_binding` `file_digest` (set to
  `"0"*64` in a scratch copy) is correctly rejected with
  `ManifestIntegrityError`.
- No spurious dependency edge exists on any Group 10 entry (§4 above);
  every declared dependency resolves to an existing Group 1 manifest entry.

**CONFIRMED.**

---

## 17. Registry verification

22 offline registry resources, all unique IDs, confirmed by direct
construction (`build_offline_registry`) against the real package root — no
network access performed (verified with `socket.socket`/
`socket.create_connection` monkeypatched to raise
`AssertionError` on any call, both at registry-construction time and at
validation time). No Group 9 or Group 11 resource present. No duplicate
alias for any Group 10 schema. The 22-vs-21 count difference is
`manifest.schema.json` (§5 above) — architecturally expected, not an
unexplained gap.

---

## 18. Scope-guard migration review — one genuine Blocking defect found and repaired

Reviewing every changed assertion in the twelve prior-phase test files 136T
touched (per `git show --stat 643d8042`) against the frozen contract and
against 136T's own stated intent (only the three exact Group 10 families
become newly allowed; Group 9 stays absent; Group 11 stays forbidden):

**Eleven of twelve files migrated correctly.** `LATER_GROUP_RECORD_FILES`
tuples, exact-file-inventory assertions, exact registry/manifest counts,
and `test_..._records_directory_contains_exactly_*_files` assertions were
all correctly updated in every one of the twelve files to reflect Group 10's
legitimate 14-record/21-manifest/22-registry state.

**One genuine, reproducible defect found: `NON-BLOCKING-136T` was
insufficient; this is `BLOCKING-136U-1` (repaired in this phase).**
`tests/test_cltr_cutover_136n_authorization_and_candidate.py`'s
`test_136n_no_later_group_filename_tracked_anywhere_in_repository` and
`tests/test_cltr_cutover_136r_recovery_schema.py`'s
`test_136r_no_group9plus_filename_tracked_anywhere_in_repository` each
carried their **own, separately hardcoded** `forbidden_stems` tuple —
distinct from, and never re-derived from, the `LATER_GROUP_RECORD_FILES`
tuple in the same file. 136T's migration correctly moved
`notification_authority_binding.schema`, `marker_authority_binding.schema`,
and `receipt_authority_binding.schema` out of `LATER_GROUP_RECORD_FILES` in
both files (confirmed via `git show 643d8042` diff) but did not notice, and
did not update, the second, independently hardcoded list inside these two
guard-test bodies. The two lists silently desynchronized within 136T's own
commit.

**Reproduction (independently confirmed, deterministic, not a parallel-
execution artifact):** running
`pytest tests/test_cltr_cutover_136n_authorization_and_candidate.py
tests/test_cltr_cutover_136r_recovery_schema.py` single-threaded (no
`-n auto`) against 136T's final tree fails both tests every time, because
`git ls-files` now legitimately lists the three Group 10 filenames (added by
136T itself) and the stale `forbidden_stems` list still names them as
forbidden. This is a direct, deterministic consequence of Group 10's own
file additions — squarely inside "any Group 10 regression is Blocking."
Both test files were unmodified by any commit after 136T's own
(confirmed via `git log -- <file>`), so this defect was present, latent, and
undisclosed in 136T's final tree at hand-off; it does not match the
disclosed-and-isolated `NON-BLOCKING-136T-7` git-status race (a different
pair of files, `test_backend_gate.py`/`test_scope_gate.py`, confirmed
unrelated to `cltr_cutover`/`schema_runtime`/Group 10 content, and confirmed
to pass in isolation — this defect does *not* pass in isolation; it fails
deterministically every run pre-repair).

**Contract basis:** Section 46 legitimately assigns Group 10 to this
implementation track; a stale guard-test list that still forbids a
now-legitimately-tracked family is a test-authoring defect, not a genuine
scope violation — but it is a real, reproducible regression against 136T's
own claimed "1609/1609" combined-suite baseline (independently recomputed:
running the identical module set 136T's own count implies yields 1607
passed / 2 failed pre-repair, not 1609/1609).

**Bounded repair applied** (within the 136U task's amended allowed-files
scope, covering exactly these two pre-existing guard-test bodies, no
production schema/manifest file touched): both `forbidden_stems` tuples now
derive their `LATER_GROUP_RECORD_FILES`-backed portion directly from
`LATER_GROUP_RECORD_FILES` itself (via `Path(...).name.removesuffix(".json")`)
instead of maintaining an independent, hand-copied list — structurally
preventing this exact class of desync from recurring for any future group.
136R's file additionally retains its two Group-9-specific stems
(`reconciliation_result.schema`, `historical_authority_reference.schema`)
as explicit hardcoded entries, since Group 9 assigns no schema file at all
(§2 above) and so those two names never appear in any `*_RECORD_FILES`
tuple to derive from.

**Regression evidence:** both tests pass after repair
(`pytest tests/test_cltr_cutover_136n_authorization_and_candidate.py
tests/test_cltr_cutover_136r_recovery_schema.py` → 239 passed, 0 failed).
The full 20-module Group 1–10 + schema-runtime + 136U combined suite
(1765 node IDs including 136U's own 156) now passes cleanly: 1764 passed,
1 skipped, 0 failed (pre-repair: 1762 passed, 2 failed, 1 skipped).

**No production schema, manifest, or shared-definition file was touched by
this repair.** No runtime behavior was introduced. The repair is bounded
strictly to two hardcoded test-fixture literal tuples.

---

## 19. Fixture and secret-like value review

Fresh adversarial fixtures were authored independently for all three
families (§6–§9 above cover the substantive branches). Secret-like probes
(a Telegram-bot-token-shaped string, an AWS-access-key-shaped string, a
bearer-token-shaped string) inside `pfn001_classification` are correctly
treated as opaque printable-ASCII data — schema-valid, exactly as the
contract's own §44 security-contract disclosure states (no secret-detection
is contractually implemented for this field; it is documented as an opaque
shape gate only). Embedded control characters (a smuggled newline) are
correctly rejected by the printable-ASCII pattern regardless of content.
No real credential-shaped string (`BEGIN PRIVATE KEY`, `xox`-prefixed Slack
token, `AKIA`-prefixed AWS key) appears in any of the three schema files
themselves. **No comprehensive secret-scanning capability is implemented or
claimed — this is a shape-gate confirmation only, matching the contract's
own scope.**

---

## 20. Packaging, installed-wheel, and no-network verification

- **Fresh wheel + sdist built** (`python -m build`) from a clean checkout.
  Wheel and sdist both independently confirmed to contain exactly 22
  `cltr_cutover` schema files: the 7 shared, the 14 records (including all
  three Group 10 bindings), and `manifest.schema.json` — no Group 9 file, no
  Group 11 file, no `CompatibilityState`, no `HistoricalAuthorityReference`,
  no `views/`, no typed model, no semantic validator.
- **Installed into a fresh, isolated venv** created outside the repository
  checkout (`/tmp`), with the wheel as the only local install source (plus
  its declared `jsonschema`/`referencing` runtime dependencies).
- **Exercised entirely from that isolated environment**, with
  `socket.socket`/`socket.create_connection` monkeypatched to raise:
  registry construction (22 resources), manifest verification (21
  entries, exact Group 10 family set), a valid `NotificationAuthorityBinding`
  record (`VALID`), an `authority_role: authoritative` `NotificationAuthorityBinding`
  record (`INVALID`) — all offline, zero network calls observed or
  required.
- **No network fallback and no working-tree dependency after installation**
  confirmed by the isolated venv's location and by the monkeypatch
  succeeding without triggering the forbidden call.

**CONFIRMED, independently reproduced outside the repository checkout.**

---

## 21. No-dispatch / no-marker-creation / no-receipt-creation / no-authority / no-execution verification

- No file under `src/pcae/` outside `schema_resources/` references
  `notification_authority_binding`, `marker_authority_binding`, or
  `receipt_authority_binding` by name (`git grep`, confirmed empty result
  set outside `schema_resources`).
- No dispatcher/writer/resolver module exists at any plausible path
  (`notification_dispatcher.py`, `telegram_dispatcher.py`,
  `marker_writer.py`, `marker_creator.py`, `receipt_writer.py`,
  `receipt_finalizer.py`, `binding_evaluator.py`, `authority_resolver.py`,
  `current_authority.py` — all absent).
- No `.pcae/cltr-authority/` directory or authority pointer exists in the
  repository.
- No tracked Python file under `src/pcae/` is named after any Group 10
  family or a dispatch/write role for one.
- `schema_runtime/` itself contains no `socket`, `subprocess`, `requests`,
  `urllib`, or `http.client` usage anywhere (grep-confirmed).
- No `bindings/` or `views/` directory exists under the packaged schema
  root.
- No `compatibility_state.schema.json` or `quarantine_record.schema.json`
  (Group 11) file exists.

**No runtime `NotificationAuthorityBinding`, `MarkerAuthorityBinding`, or
`FinalizationReceiptAuthorityBinding` object is created or persisted
anywhere in this repository. No dispatch, marker-write, receipt-write,
authority-resolution, or execution capability was introduced by 136T or by
this phase's own bounded repair. CONFIRMED.**

---

## 22. Inherited finding review

| Finding | Disposition this phase |
|---|---|
| `NON-BLOCKING-136M-1..4` | Not re-opened; out of Group 10 scope; no new evidence surfaced that would change their prior disposition. |
| `NON-BLOCKING-136N-7` | Not re-opened; unrelated to Group 10 field content. |
| `NON-BLOCKING-136P-1..2` | Confirmed as the precedent this phase's own §9/§16 review relied on (specific-table-over-summary-text resolution rule); not re-opened. |
| `NON-BLOCKING-136Q-1` | Confirmed as the same baseline-instability category independently re-encountered and re-classified at narrower scope by 136T's own `NON-BLOCKING-136T-7`; not itself re-opened by 136U. |
| `NON-BLOCKING-136R-1..4` | Not re-opened; no new evidence found affecting Group 8. |
| `NON-BLOCKING-136S-2` | Same baseline-instability category as 136Q-1/136T-7; not itself re-opened. |
| `NON-BLOCKING-136T-1` | CONFIRMED independently (§6 above: `digest`→`record_digest`, envelope/authority_disclosure normalization, `generation_reference` typing choice) — not Blocking. |
| `NON-BLOCKING-136T-2` | CONFIRMED independently (§8 above: `created_at`/`authority_role`/`digest` envelope normalization on Marker) — not Blocking. |
| `NON-BLOCKING-136T-3` | CONFIRMED independently (§8 above: `limitations` inclusion on Marker despite table omission) — not Blocking. |
| `NON-BLOCKING-136T-4` | CONFIRMED independently (§9 above: `staleness_check`'s cross-document trigger condition correctly left unenforced at Layer 2) — not Blocking. |
| `NON-BLOCKING-136T-5` | CONFIRMED independently (§9 above: `authority_role`/`digest`/`limitations` envelope normalization on Receipt) — not Blocking. |
| `NON-BLOCKING-136T-6` | Independently RE-DERIVED (not merely restated) and CONFIRMED (§9 above: §16 governs over §33's summary "yes" column) — not Blocking. |
| `NON-BLOCKING-136T-7` | Not independently re-run under `-n auto` this phase (single-threaded runs only); accepted as previously disclosed and isolated-reproduced by 136T; no Group 10 content implication either way, consistent with 136T's own finding. |
| `DEFERRED-136T-1` | CONFIRMED as DEFERRED, independently re-assessed against the full contract text (§10 above) — remains Non-Blocking. |
| — | **NEW: `BLOCKING-136U-1`** — stale hardcoded `forbidden_stems` guard-test lists in 136N's and 136R's test files, desynchronized from `LATER_GROUP_RECORD_FILES` by 136T's own Group 10 migration. **REPAIRED** this phase (§18 above); regression-tested; verdict downgraded to fixed, not merely disclosed. |

---

## 23. Full-suite baseline verification

- **Focused 136U tests:** 155 passed, 1 skipped (155/155 assertions
  executed; the skip is a deliberate positive-case placeholder inside a
  parametrized negative-case sweep, not a gap).
- **Combined Groups 1–10 + schema-runtime + 136U (21 modules):**
  pre-repair 1762 passed / 2 failed / 1 skipped; **post-repair 1764 passed /
  0 failed / 1 skipped.**
- **Fast Green** (`pytest -m fast_green -n auto`): **4391 passed**, matching
  136T's disclosed baseline exactly.
- **Full unmarked suite** (`pytest -n auto`, no markers): re-run fresh this
  phase; see the canonical phase-completion report and this document's
  final revision for the exact post-repair node counts and any remaining
  disclosed baseline failures. Any failure touching `cltr_cutover`,
  `schema_runtime`, manifest, packaging, or Group 10 content specifically
  would be classified Blocking; the only Group-10-touching regression found
  this phase (`BLOCKING-136U-1`) was repaired before this section was
  finalized, and the repair's own regression evidence is captured in §18.

---

## 24. Findings table

| ID | Disposition |
|---|---|
| CONFIRMED-136U-1 | Group 9 exclusion (no schema file, contract-mandated) |
| CONFIRMED-136U-2 | Exact Group 10 inventory (3 families, no extras) |
| CONFIRMED-136U-3 | Group 10 prerequisites (Group 1, PFN-001 vocabulary only; Group 2 conceptual, not manifest-declared) |
| CONFIRMED-136U-4 | All manifest/registry counts (21/22/3/0/0) byte-for-byte recomputed |
| CONFIRMED-136U-5 | NotificationAuthorityBinding field table (§31) and all 3 conditional branches |
| CONFIRMED-136U-6 | MarkerAuthorityBinding field table (§32) |
| CONFIRMED-136U-7 | FinalizationReceiptAuthorityBinding field table (§33) and §16 conditional resolution, independently re-derived |
| CONFIRMED-136U-8 | staleness_check DEFERRED disposition (empty-placeholder, Non-Blocking) |
| CONFIRMED-136U-9 | Authority-role prohibition (§9) on all 3 schemas, no bypass |
| CONFIRMED-136U-10 | Tier 2 / `_extensions` boundary on all 3 schemas |
| CONFIRMED-136U-11 | Sibling independence; 4 independent graphs acyclic |
| CONFIRMED-136U-12 | Atomic-completeness detection at manifest layer |
| CONFIRMED-136U-13 | Packaging (wheel/sdist) + isolated installed-wheel offline operation, no network |
| CONFIRMED-136U-14 | No dispatch/marker-write/receipt-write/authority/execution capability anywhere in the repository |
| **BLOCKING-136U-1** | Stale hardcoded scope-guard filename lists in 136N/136R test files, desynchronized by 136T's own migration — **REPAIRED**, regression-tested, verdict: fixed |
| NON-BLOCKING-136T-1..6 | Independently re-derived and CONFIRMED (not merely restated) |
| DEFERRED-136T-1 | Independently re-assessed and CONFIRMED as correctly deferred |

**Zero unresolved Blocking findings remain.**

---

## 25. Required final confirmations

Legacy lifecycle remains the sole production authority. CLTR remains
derivative. 136U independently verified executable-schema Implementation
Group 10: NotificationAuthorityBinding, MarkerAuthorityBinding, and
FinalizationReceiptAuthorityBinding. The frozen contract assigns no
executable schema file to Group 9, so no Group 9 schema was required or
implemented. The three Group 10 schemas remain descriptive authority
bindings only. No runtime notification dispatch, marker creation, receipt
creation, compatibility resolution, historical-authority resolution,
publication, recovery, or authority transition was introduced. All three
Group 10 schemas locally forbid an authoritative authority role where
required by the frozen contract. Tier 2 extension behavior remains confined
to the explicit `_extensions` boundary. Schema validity does not establish
that a notification was delivered, a marker exists, a receipt is final, an
external effect occurred, an identity exists, a staleness claim is true, or
a binding is operationally authoritative. No Group 11 schema,
CompatibilityState, HistoricalAuthorityReference schema, derived view,
Stage 3 typed model, or broad cross-record semantic validator was
implemented. No cryptographic verification, runtime evaluator, resolver,
coordinator, authority-state persistence, or authority pointer was
implemented or changed. No runtime Group 10 object was created or
persisted. No authority epoch changed. No CLTR authority was created. No
legacy authority was demoted. No legacy authority was retired. No
production lifecycle behavior changed. No execution capability was
introduced. Runtime remains Observed, maximum capability remains observe,
and execution availability remains unavailable.

One bounded repair was made to two pre-existing test files
(`tests/test_cltr_cutover_136n_authorization_and_candidate.py`,
`tests/test_cltr_cutover_136r_recovery_schema.py`) to fix a stale,
desynchronized scope-guard assertion left by 136T's own Group 10 migration
(`BLOCKING-136U-1`, §18). No production schema, manifest, or runtime source
file was touched by this repair.

---

## 26. Lifecycle-reporting observations (carried forward)

Carried forward unchanged from 136S/136T: Architecture Status's recurring
false limitation about the absence of a recommended-next-phase sentence,
and the historical stale-body report defect (both out of this
independent-verification phase's scope, per the operator prompt's own
instruction not to broaden into lifecycle-reporting repair unless it
directly blocks trustworthy 136U completion — it did not).

---

## 27. Limitations and deferred work

- `staleness_check`'s internal shape remains an empty placeholder
  (`DEFERRED-136T-1`, independently confirmed §10).
- Group 9's reconciliation function and `HistoricalAuthorityReference`
  typed model remain entirely unimplemented (no schema file exists for
  either, by contract design).
- Group 11 (`compatibility_state`, `quarantine_record`) remains entirely
  unimplemented; not begun by this phase.
- `NON-BLOCKING-136T-7`'s disclosed parallel-execution git-status race was
  not independently re-run under `-n auto` this phase; accepted as
  previously disclosed and isolation-reproduced.

---

## 28. Verification verdict

**VERIFIED WITH NON-BLOCKING FINDINGS — READY FOR NEXT EXECUTABLE-SCHEMA GROUP**

One Blocking-caliber defect (`BLOCKING-136U-1`, a stale scope-guard test
regression, not a production schema/manifest defect) was found, reproduced,
bounded-repaired, and regression-tested within this phase, per the
operator prompt's explicit instruction to do so for genuine Blocking Group
10 defects. Zero unresolved Blocking findings remain. All Non-Blocking and
Deferred findings from 136T are independently re-derived and confirmed, not
merely restated.

---

## 29. Recommended next phase

Group 11 (Section 46: `compatibility_state.schema.json` depends only on
Group 1; `quarantine_record.schema.json` depends on Groups 2–8) is the next
contract-assigned executable-schema group and is also, per Section 46's
11-row table, the **final** executable-schema implementation group — no
Group 12 row exists. Its exact record-family names
(`CompatibilityState`, `QuarantineRecord`), field tables (§34, §30), and
prerequisites are already frozen in the contract text and were not
re-derived by this phase (out of 136U's bounded scope). This phase does not
begin, plan the internals of, or otherwise scope Group 11 implementation.

Recommended next phase: **136V — Compatibility/Quarantine Schema
Implementation (Implementation Group 11)**, subject to the same
independent-verification gating (`CSCH-EXEC-REQ-062`, Section 46) applied
to every prior group. Not begun by this phase.

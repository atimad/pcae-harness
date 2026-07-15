# Phase 135W — Stage 3 Authority-Cutover Contract Freeze

## Contract identifier

**CLTR-CUTOVER-001 v1.0**

Status: **FROZEN** as of Phase 135W. This document is the binding contract text.
It is contract-only. It defines future Stage 3 behavior. It does not implement,
activate, or authorize any of the behavior it defines.

## Normative language

This document uses RFC-2119-style normative language, consistent with prior
Track 135 contracts (CLTR-001, CLTR-SCHEMA-001):

- **must / shall** — a binding requirement; a future implementation that
  violates it is non-conformant with CLTR-CUTOVER-001.
- **must not / shall not** — a binding prohibition.
- **should** — a strong recommendation; a future implementation may deviate
  only with an explicit, documented, governed justification.
- **may** — optional, permitted.
- **[GUIDANCE]** — explanatory or illustrative material that is not itself
  binding; used the same way CLTR-SCHEMA-001 §2/§24 uses it.

Every normative rule in this document is traced to one of: a prior binding
contract, independently verified implementation evidence, an explicit safety
requirement, or a clearly labelled new Stage 3 contract decision (marked
**[NEW]**). Citations use the form `135V §N`, `135M §N`, `CLTR-001 §N`,
`CLTR-SCHEMA-001 §N`, `PFN-001 §N`, `PFR-001 §N`, `135U §N`, etc.

---

## 0. Relationship to prior contracts and evidence

### 0.1 Relationship to CLTR-001 (v1.0)

CLTR-001 defines the semantic content of "the Canonical Lifecycle Transition
Record" — one governed lifecycle transition, from proposal through terminal
outcome — as thirty required semantic fields (CLTR-001 §6.2), without fixing
wire schema. CLTR-001 is explicitly **advisory only** with respect to the
existing Track 134 finalization transaction and entry points (CLTR-001 §1),
and states plainly that CLTR is **not currently authoritative** in production
(CLTR-001 §4.3, §24.3, §25).

CLTR-CUTOVER-001 does not modify CLTR-001. It adds a new, separate binding
contract governing the *transition* from legacy authority to CLTR-backed
authority — a topic CLTR-001 explicitly leaves open (CLTR-001 never uses the
words "epoch," "cutover," or "Stage 3"; its only forward-looking authority
language is §25's classification table, which freezes required *future*
classifications without defining a mechanism). CLTR-CUTOVER-001 is additive
to CLTR-001 in the same sense CLTR-001 is additive to 134B: it does not amend,
weaken, or supersede any clause of CLTR-001.

### 0.2 Relationship to CLTR-SCHEMA-001 v1.0.1

CLTR-SCHEMA-001 is the wire-format contract satisfying CLTR-001; both remain
frozen and in force; neither supersedes the other. As of v1.0.1 (Phase 135J,
a PATCH closing an adapter-assignment gap, zero wire-format effect),
CLTR-SCHEMA-001 defines: the `lifecycle_state`/`transition_type` enums, the
`authority_role` field, the fifteen representation-kind bindings, the
state-dependent field-presence table, the required-fields catalog, the
enumerations catalog, commit-ownership/evidence-reference encodings, the
37-invariant catalog, temporal fields, canonical serialization and digest
rules, the persistence contract (`current` pointer, generation directories),
the nine-step atomic-publication *specification* (§16–17, not implemented),
compatibility adapters (§21, fully assigned across all fifteen kinds as of
v1.0.1), conformance classes, and the diagnostic envelope (§25), whose
`authority_mode` enum (`shadow | authoritative | compatibility`) is the
closest existing analog to an authority concept — but it is scoped to
diagnostics output, not to the CLTR record's own identity fields.

CLTR-SCHEMA-001 §24 (Migration, entirely [GUIDANCE], non-binding) already
sketches the cutover path in outline, citing "135H's nine-stage retirement
order" and "135H's nine cutover gates," without defining either. This
document (§30, Schema readiness contract, below) evaluates CLTR-SCHEMA-001
v1.0.1 against Stage 3's concrete needs and produces a normative disposition.
**No field, enum, or binding is added to CLTR-SCHEMA-001 by this phase.**
Where a gap requires a schema change, it is registered as a prerequisite
(§34) for a future, separately governed schema-amendment phase, per
CLTR-SCHEMA-001 §2's own MINOR/MAJOR amendment discipline.

### 0.3 Relationship to PFN-001

PFN-001 (Phase 128B.2) freezes: exactly one trusted canonical phase report
delivered to the configured sink per terminal phase outcome; the canonical
report at `.pcae/phase-reports/latest.json`/`latest.md` (or its timestamped
sibling) as the **only** authorized notification source; exactly-once,
idempotent dispatch via `certify_notification_transition()` plus the
`.last-notified.json` marker; and a mandatory durable failure record when
delivery does not succeed (PFN-001 §4, §5, §8, §9).

CLTR-CUTOVER-001 does not amend PFN-001's dispatch guarantee, its
idempotency mechanism, or its failure contract. It defines only how
notification *intent* — the decision that a notification is due, and the
generation whose content the notification carries — binds to the
authoritative generation once Stage 3 is active for a given authority epoch
(§23 below). Consistent with 135V §14's proposal, the **input** to PFN-001's
existing dispatch mechanism changes for Stage-3-active epochs; the mechanism,
guarantee, and contract text of PFN-001 do not.

### 0.4 Relationship to PFR-001

PFR-001 (Phase 133A/133B) freezes thirteen mandatory sections for every
canonical phase report (Phase Identity, Executive Summary, Architectural
Findings, Implementation Findings, Verification Findings, Technical Debt
Review, Notable Engineering Knowledge, Governance Results, Test Results,
No-Go Confirmation, Architectural Boundary Confirmation, Track Progress,
Next Phase), derived from the `PhaseReport` artifact/trust pipeline in
`src/pcae/core/phase_reports.py`, not from independently authored narrative.

CLTR-CUTOVER-001 does not amend PFR-001's section structure or its
derivation source discipline. It defines only that, once Stage 3 is active
for an authority epoch, the canonical report's content is rendered from the
certified content of the authoritative generation rather than from legacy's
`PhaseReport` object directly (§20 below) — an input substitution, not a
structural change. This phase 135W's own final report and this document
both continue to satisfy PFR-001 unchanged.

### 0.5 Relationship to the 135M migration plan

135M (Phase 135M/135N) freezes a six-stage authority-stage model: Stage 0
(Shadow Observation, current baseline), Stage 1 (Dual Derivation, Legacy
Authority — verified 135O/135P), Stage 2 (Dual Publication Rehearsal, Legacy
Authority — verified 135S/135T, plus Rollback Rehearsal verified 135U),
Stage 3 (CLTR Authority With Legacy Verification — **the subject of this
contract**), Stage 4 (Legacy Demotion), Stage 5 (Legacy Retirement).

135M §6 states Stage 3 "requires a separate contract, independent
verification, and an explicit operator-approved implementation phase... this
document does not authorize entry into Stage 3; it only defines what
entering it will require." 135M §53's originally *recommended* phase letters
for that contract (135S/135T) were superseded by the actually-executed
sequence — 135S/135T became Stage 2 implementation/verification, 135U became
Rollback Rehearsal, 135V became Stage 3 Readiness Architecture, and 135V
recommends **135W = Stage 3 Authority-Cutover Contract Freeze**, which is
this phase. Per 135M §53's own disclaimer, "the exact phase letters ... are
not binding if a future phase derives a safer sequence; the binding
requirement is the ordering discipline itself" — satisfied here.

This contract adopts, without re-litigating, 135M's stage model (§6), its
Stage 3 entry-gate discipline (§7: 135T VERIFIED, zero Blocking, explicit
cutover-approval artifact), its cutover-approval requirements (§41: human
approver, evidence review, findings review, effective boundary, rollback
readiness, expiry, revocation, "no implicit cutover through a feature flag
alone"), its atomic-generation model (§18–20), its publication/split-brain
principles (§22–23), its rollback architecture (§38–39), its authority-epoch
disclosure requirement (§40), and its risk register (§55) as source material,
re-derived below into binding normative sections rather than copied as
prose.

### 0.6 Relationship to verified Stage 1 and Stage 2 evidence

Stage 1 (135O/135P, VERIFIED WITH NON-BLOCKING FINDINGS, zero Blocking)
established: a `SharedTransitionInputPackage` assembled once, immutable, at
two capture points (`PRE_TRANSACTION`, `LEGACY_COMPLETION`); a `transition_id`
independently generated (UUID4, decoupled from `phase_id`, retry-stable via a
logical-key digest); a `migration_epoch` read once from
`PCAE_CLTR_MIGRATION_EPOCH`, never inferred; a deterministic
`authority_epoch` string `"legacy|<migration_stage>|<migration_epoch>|<schema_id>|<schema_version>"`, with `ProductionAuthority.LEGACY`
structurally the only value any code path can produce today.

Stage 2 (135S/135T, VERIFIED WITH NON-BLOCKING FINDINGS after in-phase repair
of two CONFIRMED BLOCKING findings) established: a rehearsal-namespace
pointer (`current-rehearsal`) published via validate-then-atomic-replace
(`mkstemp`+`fsync`+`os.replace`) with mandatory post-write readback
verification — but **ordinary atomic replacement, not compare-and-swap**
against an expected prior value (135V §11, confirmed independently in this
phase's source review, §5 below). Rollback Rehearsal (135U, VERIFIED WITH
NON-BLOCKING FINDINGS after in-phase repair of two CONFIRMED findings)
established rollback-within-the-rehearsal-namespace, explicitly declining to
implement rollback-to-empty-pointer, cross-epoch reconciliation, or a
dedicated roll-forward command (135U §1, §13, §19 — quoted verbatim in §16
below).

All of this evidence remains **derivative and non-authoritative**: it proves
mechanisms work in the rehearsal namespace, never that production authority
has moved. This contract treats it as necessary but not sufficient input to
the readiness evidence package (§9) and pre-cutover gate (§10).

### 0.7 Compatibility and amendment rules

See §38 (Versioning and amendment) for the full normative treatment. In
summary: CLTR-CUTOVER-001 is version 1.0; a Blocking-invariant change
requires a new major version and a governed contract-amendment phase; a
verifier built for one contract version must reject an unrecognized
`contract_version`, never silently accept it; this contract is never
silently reinterpreted by an implementation phase.

---

## 1. Purpose contract

Stage 3 exists to transfer production lifecycle authority **exactly once**
per authority-epoch transition, from legacy authority to a CLTR-backed
authoritative generation, under governed human authorization, with no
interval in which more than one artifact is simultaneously authoritative at
any externally visible boundary (§5).

Stage 3 **shall not**:

1. create permanent dual authority — the cutover-request/certification/
   publication lifecycle (§7–§13) exists precisely to make the authority
   transition atomic and singular, never a steady state with two valid
   authorities (§5, §27);
2. treat Stage 2 rehearsal as production authority — the rehearsal pointer,
   generations, and evidence remain namespace-isolated and non-authoritative
   forever; certification (§12) is the only mechanism that may promote a
   verified rehearsal generation toward candidacy, and even certification
   does not itself publish authority (§12.5);
3. retire legacy code in the same transition unless separately authorized —
   authority cutover (Stage 3), legacy demotion (Stage 4), and legacy
   retirement (Stage 5) are distinct governed stages with distinct exit
   criteria (§33, carrying forward 135M §37's "retirement requires strictly
   stronger evidence than demotion");
4. introduce execution capability — Stage 3 as contracted here operates
   entirely within the existing `Observed` / `observe` /
   `execution_unavailable` runtime posture (135V's own no-implementation
   proof, reaffirmed in §"No-implementation proof" below); nothing in this
   contract authorizes runtime execution capability;
5. alter Decision Evaluation or repository execution boundaries — out of
   scope entirely (§2).

---

## 2. Scope contract

**Explicitly included** (each has its own normative section below):
authority object (§3), authority resolver (§4), authority epochs (§6),
cutover request (§7), human authorization (§8), pre-cutover evidence package
(§9), cutover candidate (§11), certification (§12), authority publication
(§13), concurrency (§15), stale-writer rejection (§14), crash recovery
(§18), external-effect sequencing (§19), report/metadata derivation (§20),
Architecture Status derivation (§21), checkpoint and promotion migration
(§22), notification intent and dispatch authorization (§23), marker and
receipt binding (§24, §25), reconciliation (§18, §27), rollback/roll-forward
policy (§17), legacy compatibility (§32), demotion stages (§33), activation
gates (§10, §36).

**Explicitly excluded**: implementation of any of the above; cutover
execution; authority activation; legacy retirement; execution adapters;
shell or network mediation; Telegram inbound control. This phase produces
no code.

---

## 3. Authoritative object contract

**[NEW, re-deriving 135V §4 and §8]** The authoritative production object
for a Stage-3-active authority epoch is **one immutable, certified,
manifest-bound lifecycle generation**, identified by a stable
`transition_id` and a verified content digest (`generation_digest`) — not a
bare CLTR record in isolation.

A bare CLTR JSON `record.json` file **shall not** independently become
production authority. The authoritative object binds together, as a single
manifest-bound unit, using the existing `record.json` + `manifest.json` pair
CLTR-SCHEMA-001 already freezes (CLTR-SCHEMA-001 §5, §16), plus fields new to
this contract:

- phase identity (`phase_id`);
- transition identity (`transition_id`);
- migration epoch (`migration_epoch`);
- authority epoch (`authority_epoch` — see §6, superseding the string-prefix
  format inherited from Stage 1 with a typed model);
- the CLTR record itself (schema-conformant per CLTR-SCHEMA-001 v1.0.1);
- shared-input final revision (from the Stage 1
  `SharedTransitionInputPackage`, §0.6);
- certification result (§12);
- the required lifecycle representations (all fifteen kinds CLTR-SCHEMA-001
  §5 enumerates, each with an adapter fully assigned per §21.4 as of
  v1.0.1);
- the manifest and per-artifact digests (CLTR-SCHEMA-001 §16);
- the generation digest (a digest over the manifest-bound whole, self-
  exclusion per CLTR-SCHEMA-001's digest contract);
- authority-transition evidence (the cutover request + certification
  record, §7, §12);
- schema versions (`schema_id`, `schema_version`, `contract_version`,
  `compatibility_id` per CLTR-SCHEMA-001 §1.1);
- limitations and compatibility metadata (`compatibility_metadata.limitations`,
  CLTR-SCHEMA-001 §7/§23).

This is a binding requirement on any future implementation: authority
resolution (§4) **must** resolve to this composite object, never to a CLTR
record read in isolation from its manifest, digests, and certification
evidence.

---

## 4. Authority resolver contract

**[NEW, re-deriving 135V §12]** There **shall** be exactly one shared
production authority resolver, conceptually a single function invoked once
per finalization transaction (inside `run_finalization_transaction`, per
135V §12's proposed integration point), and it is the **only** component in
the codebase permitted to answer "what generation is currently authoritative
for this transition."

The resolver **must** return at minimum:

- authority kind (`legacy` | `cltr`);
- authority epoch;
- authoritative generation identity (`transition_id`) when kind is `cltr`;
- generation digest;
- schema/version (`schema_id`, `schema_version`, `contract_version`);
- verification state;
- lifecycle transition identity;
- source pointer/evidence (what artifact the resolver actually read);
- uncertainty state (explicit, never inferred from absence);
- limitations;
- compatibility mode.

The resolver **must**:

- fail closed on any ambiguity (§5);
- reject multiple valid authorities;
- reject mismatched epoch/generation pairs;
- reject stale or substituted pointers;
- reject unverified generations;
- reject quarantined generations (§29);
- reject unsupported schema/contract versions;
- never infer authority from report titles, filenames, Git history, "latest"
  files, task titles, or prose — this rule directly closes the live hazard
  135V identified in Architecture Status's narrative-parsing derivation
  (F-135V-6, §21 below).

All four production entry points (§26) — `run_phase_complete`,
`run_task_finish`, `run_phase_report_create`, `run_notify_send_report`, each
in `src/pcae/commands/`, all converging through
`run_finalization_transaction` in `src/pcae/core/finalization_transaction.py`
— **must** call the same resolver, with no entry-point-specific authority
logic. No caller-specific authority resolution is permitted, including on
recovery paths (`run_task_finish_recover`): recovery **must** use the same
read-only resolver semantics as the ordinary path.

---

## 5. Single-authority invariant

**[NEW, re-deriving 135V §6 and 135M §22–23]** At every externally visible
production lifecycle boundary, exactly one authority epoch and exactly one
verified authoritative generation **shall** control lifecycle truth.

Externally visible boundaries include: production report visibility;
completion metadata visibility; Architecture Status visibility; checkpoint
and promotion state; notification authorization; notification marker state;
finalization receipt state; terminal reconciliation; any production
latest/current pointer.

This contract **forbids**, as invalid steady states — not merely as
transient conditions to be minimized, but as states that must never persist
beyond the atomic publication instant (§13):

- legacy and CLTR being independently authoritative;
- two CLTR generations being current;
- two authority epochs being active;
- caller-specific authority (violates §4);
- "prefer legacy if ambiguous" as a valid steady state;
- "prefer CLTR if both exist" as a valid steady state.

**Ambiguity must fail closed.** Any state the resolver cannot classify with
certainty **must** be treated as a conflict (§10, gate outcome `conflict`)
or quarantined (§29), never resolved by a default preference rule.

---

## 6. Authority epoch contract

**[NEW, re-deriving 135V §7, closing F-135V-1]** Authority epochs **shall**
be typed values, not free-form strings interpreted by substring or prefix
matching. Stage 1 introduced a working but explicitly insufficient format —
`"legacy|<migration_stage>|<migration_epoch>|<schema_id>|<schema_version>"`
— checked in Stage 2/Rollback Rehearsal by prefix comparison (a design 135U
§19 disclosed and F-135U-2 exposed as a bug: substring match, not
authority-epoch-aware prefix match, later repaired within 135U). 135V §11
formalizes this as **F-135V-1: "insufficient for production ... requires
typed model"** and this contract adopts that finding as binding: a future
implementation phase **must** replace substring/prefix-based epoch
comparison with an exact typed-value comparison before Stage 3 activation.

At minimum, this contract distinguishes two epoch kinds:

- **legacy authority epoch** — any epoch whose `authority_kind` is `legacy`;
  the format above (or its typed successor) applies;
- **CLTR authority epoch** — any epoch whose `authority_kind` is `cltr`.

The typed model **must** freeze, in a future implementation-phase contract
(registered as a prerequisite, §34, PREREQ-1):

- epoch identifier syntax (structured, not a delimited string requiring
  substring parsing);
- epoch immutability (an epoch, once minted, is never mutated in place);
- migration-epoch binding (each authority epoch binds to exactly one
  `migration_epoch`, consistent with Stage 1's model);
- source epoch / target epoch fields on every cutover request (§7);
- transition rules (§7, §13);
- stale-epoch rejection (§14);
- unknown-epoch rejection (fail closed, §4);
- historical interpretation (an old epoch remains inspectable forever, per
  §32's immutable-history principle);
- schema compatibility (§30);
- report/metadata/marker/receipt binding (§20, §24, §25).

This document does **not** implement the typed model. It freezes that the
typed model is required and enumerates what it must define.

---

## 7. Cutover request contract

**[NEW, re-deriving 135V §5]** A cutover request is a deterministic, fully
identified object binding:

- phase ID;
- transition ID;
- migration epoch;
- source authority epoch (legacy);
- target authority epoch (CLTR);
- source authoritative generation, or — for the first-ever cutover in an
  epoch lineage — an explicit legacy-authority identity marker (since there
  is no prior CLTR generation to cite);
- target generation identity and digest;
- shared-input final revision (from the Stage 1 package, §0.6);
- Stage 1 evidence identity;
- Stage 2 evidence identity;
- rollback evidence identity;
- readiness package digest (§9);
- human authorization identity (§8);
- requested operation (`cutover`);
- contract version (`CLTR-CUTOVER-001/1.0`).

The cutover-request identity **must** be deterministic — computed from the
binding fields above (e.g., a digest of the tuple), never a random UUID and
never wall-clock time. This mirrors Stage 1's `package_id` design (a digest
of `(migration_epoch, authority_epoch, phase_id, transition_id, entry_point,
predecessor_transition_id)`, §0.6) and CLTR-001's general preference for
content-derived identity over generated identity where determinism matters.

Conflicting reuse of the same cutover-request identity — the same identity
resolving to different binding-field values — **must** fail closed (rejected,
never silently overwritten or merged).

---

## 8. Human authorization contract

**[NEW, re-deriving 135M §41 and 135V §25]** Authorization **must** bind:

- operator identity or approved principal;
- cutover request identity;
- migration epoch;
- source and target authority epochs;
- target generation identity and digest;
- contract version (`CLTR-CUTOVER-001/1.0`);
- authorization scope;
- authorization timestamp;
- freshness or expiry;
- revocation state;
- replay protection;
- explicit acknowledgement of irreversible effects;
- required evidence package digest (§9).

Authorization **must** be explicit, phase-bound, generation-bound,
digest-bound, non-transferable, auditable, revocable before authority
publication (§13), and non-replayable after use. "No implicit cutover
through a feature flag alone" (135M §41) is adopted verbatim as binding.

**One-person vs. two-person authorization** — 135V §"Findings register"
raised this as **F-135V-7**, explicitly **DEFERRED** to a future governance
phase, not required for 135W. This contract adopts that disposition: **one
human operator's authorization is sufficient for the initial Stage 3
implementation**, subject to all binding fields above; two-person approval
remains an available future strengthening, not a Stage 3 prerequisite,
registered as PREREQ-8 (Deferred) in §34.

**Authorization freshness/expiration window** — 135V §"Findings register"
raised this as **F-135V-8**, "DEFERRED — quantitative parameter for 135W" —
i.e., this contract, not a later phase, must set it. **[NEW binding
decision]**: authorization freshness expires **24 hours** after the
authorization timestamp, or immediately upon any change to the cutover
request's binding fields (source/target epoch, target generation identity or
digest, readiness package digest), whichever is sooner. An expired
authorization **must not** be used to publish authority (§13); a fresh
authorization is required. This window is a contract parameter, amendable
per §38, not hardcoded architecture — a future implementation may make it
configurable within governance bounds, but the default and floor are frozen
here at 24 hours.

This document does **not** implement authorization handling.

---

## 9. Readiness evidence package contract

**[NEW, re-deriving 135V §26]** The Stage 3 readiness package is a
deterministic, digest-identified aggregate of verified evidence from:

- Stage 1 dual derivation (135O) and its independent verification (135P);
- Stage 2 forward rehearsal (135S) and its independent verification (135T);
- rollback rehearsal (135U) and its independent verification (135U, combined
  phase);
- production-output equivalence (Stage 1's comparison evidence, 135O/135P);
- all-four-entry-point coverage (§26);
- recovery-path coverage (§18);
- pointer containment (§28);
- immutable persistence (CLTR-SCHEMA-001 §16–17);
- manifest and digest verification (CLTR-SCHEMA-001 §16, §21);
- concurrency readiness (§15, gated on PREREQ-2's resolution — see §34);
- notification migration readiness (§23);
- marker and receipt migration readiness (§24, §25);
- schema readiness (§30);
- security review (§28);
- unresolved findings (§35, from this phase's own findings classification
  plus all inherited findings from 135M/135O–135V);
- human-authorization readiness (§8).

The readiness package remains **derivative evidence**. It **shall not**
activate cutover by its own existence. Its identity and digest **must** be
deterministic (a digest over its aggregated evidence references, not
independently generated). Missing or stale evidence **must** fail closed —
an incomplete or unrefreshed readiness package makes the pre-cutover gate
(§10) evaluate to `ineligible` or `uncertain`, never `eligible`.

---

## 10. Pre-cutover gate contract

**[NEW, re-deriving 135V §9 and 135M §7]** The gate evaluates, at minimum:

supported CLTR schema (CLTR-SCHEMA-001 v1.0.1 or later within the same
major); supported cutover contract version (`CLTR-CUTOVER-001/1.0` or later
compatible minor); valid migration epoch; valid source authority epoch;
valid target authority epoch; valid shared-input final revision; valid
Stage 1 evidence; valid Stage 2 forward-rehearsal evidence; valid
independent Stage 2 verification evidence; valid rollback-rehearsal
evidence; valid rollback verification evidence; exact candidate inventory
(§11); verified manifest; verified artifact digests; verified generation
digest; valid readiness package (§9); no unresolved Blocking findings (this
contract's own §35 findings, plus 135M §55's risk register items still open);
no stale or conflicting authority state; no quarantined target (§29); no
pointer ambiguity; no concurrent cutover in progress (§15); explicit human
authorization (§8); production recovery readiness (§18); notification
exactly-once readiness (§23); marker and receipt migration readiness (§24,
§25); all-four-entry-point readiness (§26).

The gate **must** produce exactly one of: `eligible`, `ineligible`,
`uncertain`, `conflict`. **Only `eligible` may proceed** to certification
(§12). `uncertain` and `conflict` **must** fail closed — no partial or
best-effort proceeding is permitted.

135M §7's entry-gate discipline for the 2→3 transition ("135T verdict
VERIFIED, zero Blocking findings, explicit cutover-approval artifact
executed") is subsumed by, and does not conflict with, this gate: the
cutover-approval artifact **is** §8's human-authorization object, and 135T's
VERIFIED verdict is one of the readiness-package inputs (§9).

---

## 11. Cutover candidate contract

**[NEW, re-deriving 135V §8]** This contract distinguishes:

- **rehearsal candidate** — a generation prepared inside the Stage 2
  rehearsal namespace, not yet verified;
- **verified rehearsal generation** — a rehearsal candidate that has passed
  Stage 2's verification checks (135S/135T mechanics: manifest verification,
  digest verification, containment checks);
- **cutover candidate** — a verified rehearsal generation additionally
  submitted for Stage 3 certification (§12); existence in this state alone
  confers no authority;
- **certified cutover generation** — a cutover candidate that has passed
  certification (§12);
- **authoritative production generation** — a certified cutover generation
  that has been published (§13) and is the current target of the resolver
  (§4) for its authority epoch;
- **historical generation** — a prior authoritative generation, superseded
  but immutably preserved and inspectable (§32);
- **superseded generation** — synonym for historical generation in the
  context of an explicit supersession event;
- **quarantined generation** — a generation that failed integrity,
  containment, or gate checks and is permanently excluded from authority
  (§29).

A verified Stage 2 generation **shall not** become authoritative merely
because it exists or because a pointer targets it — this is the precise
boundary 135V's model draws between rehearsal and production, and it is
adopted as binding: existence in the rehearsal namespace, even verified
existence, is necessary but not sufficient. Certification (§12) is the only
step that adds cutover-specific evidence.

---

## 12. Certification contract

**[NEW, re-deriving 135V §8]** Certification inputs: cutover request (§7),
readiness package (§9), target generation (candidate, §11), manifest and
digest, authority epochs (source and target), authorization (§8), cutover
contract version, schema version, gate result (§10, must be `eligible`),
limitations, and verifier identity or process evidence.

Certification **must** add explicit evidence that: the Stage 3 gate passed;
human authorization is valid (unexpired, matching binding fields); source
authority is verified (the resolver's current read of legacy state matches
the cutover request's stated source); target generation is verified
(manifest/digest match); target authority epoch is valid; concurrency
preconditions hold (no competing in-flight cutover, §15); a recovery plan is
available (§18); external-effect sequencing is valid (§19, notification not
yet dispatched from this generation).

Certification output **must** be immutable and deterministic except for
approved timestamps (mirroring CLTR-SCHEMA-001's general digest-and-freeze
discipline). **Certification shall not itself publish authority** — §13 is
the sole publication boundary, deliberately kept separate so that
certification failure cannot corrupt current authority state.
**Certification failure must not modify current authority.**

---

## 13. Authority publication contract

**[NEW, re-deriving 135M §22–23 and 135V §4, §11]** There **shall** be
exactly one externally visible authority-publication boundary.

**Publication artifact**: one repository-contained production authority
pointer, atomically replaced to reference one certified, immutable
authoritative generation. This is structurally analogous to, but namespace-
distinct from, the Stage 2 rehearsal pointer (`current-rehearsal`,
`src/pcae/cltr/migration/rehearsal/pointer.py`) — the production pointer
**must** live in a separate namespace/path so that no code path can confuse
a rehearsal target with a production target (135M §22–23's split-brain
principle: "there is one generation pointer, not independent 'latest'
pointers ... acting as competing authorities").

This contract freezes:

- pointer path/namespace: production-authority-specific, distinct from
  `current-rehearsal` and from legacy's `latest.*` files (§20);
- target form: `transition_id` + `generation_digest` pair, never a bare
  filename or mutable reference;
- temporary pointer: write-then-atomic-replace, following the same
  `mkstemp`+`fsync`+`os.replace` pattern already proven in
  `_save_checkpoint` (`finalization_transaction.py:251`) and the Stage 2
  rehearsal pointer's `write_pointer_atomic`;
- atomic replacement: single `os.replace` call, no partial-write window
  observable by readers;
- expected-current binding and compare-and-swap semantics: see §14 — the
  production pointer **must** implement genuine CAS, which today's Stage 2
  rehearsal pointer and legacy writers do **not** (confirmed by this
  phase's source review, §14 below; this is the direct implementation of
  F-135V-2);
- source authority epoch / target authority epoch: both recorded in the
  publication evidence, not only in the cutover request;
- source generation digest / target generation digest: both recorded, so a
  post-hoc audit can reconstruct exactly what was replaced with what;
- post-publication readback: mandatory, mirroring the Stage 2 rehearsal
  pointer's `verify_published_target` and Stage 1's general discipline of
  never silently trusting a write;
- target verification: the readback **must** confirm the published pointer's
  digest matches the certified generation's digest;
- uncertainty classification: an unconfirmed readback **must** produce an
  explicit `UNCERTAIN_PUBLICATION` state (mirroring the Stage 2 rehearsal
  pointer's existing behavior), never a silent success;
- result evidence: durable record of the publication attempt and its
  outcome, independent of the pointer file itself;
- durability assumptions: `fsync` before `os.replace`, consistent with
  existing atomic-write primitives in this codebase.

**No second independent current-authority pointer may exist.** If legacy
currently has a separate authority mechanism (it does not today — legacy's
"authority" is implicit, the absence of any published CLTR pointer, per
Stage 1's `ProductionAuthority.LEGACY` default), this contract defines that
legacy becomes non-authoritative at the exact same logical publication
boundary: the instant the production authority pointer is atomically
replaced to target a CLTR generation for a given authority epoch, legacy
ceases to be authoritative for that same epoch. There is no separate
"legacy off" switch — publication and legacy's cessation of authority for
that epoch are the same event, checked by the same resolver read (§4).

---

## 14. Compare-and-swap and stale-writer contract

**[NEW, re-deriving 135V §11, directly implementing the requirement F-135V-2
registers]** This phase's source review (§0.6, and independently confirmed
here) establishes as ground truth: **no writer in this codebase today
implements genuine compare-and-swap.** Specifically —

- `canonical_artifact_promotion.py`'s `promote_artifact`/`quarantine_artifact`
  use plain `path.write_text(...)`, no temp file, no `os.replace`, no CAS;
- `phase_reports.py`'s `write_canonical_report` uses direct overwrite, no
  atomic replace, no CAS;
- `phase_reports.py`'s notification marker write uses read-modify-write via
  `path.write_text(json.dumps(...))`, no temp+`os.replace`, no digest-based
  CAS (idempotency is enforced by payload/digest *comparison logic* inside
  `notification_dispatch_state`, which is a different guarantee than
  filesystem-level CAS on the write itself);
- `finalization_transaction.py`'s `_save_checkpoint` **does** use
  temp-file + `os.replace` (atomic), but has **no** compare-and-swap
  precondition against an expected prior digest — it is atomic-write, not
  CAS;
- the Stage 2 rehearsal pointer (`cltr/migration/rehearsal/pointer.py`)
  validates the target (existence, finalization, digest match, non-
  quarantine) **before** an atomic replace, and reads back **after** — but
  evaluates no precondition against the pointer's *expected current value*
  as part of the same atomic operation. This is validate-then-write, not
  compare-and-swap.

Stage 3 **must** include repository-level stale-writer protection that none
of the above provides today. The production authority pointer's publisher
(§13) **must** evaluate, as an atomic precondition of the same operation
that performs the replace (not a separate check-then-act with a window
between them):

- expected current authority epoch;
- expected current authority identity (generation, or explicit legacy
  marker);
- expected pointer digest;
- expected source generation or legacy state;
- expected migration epoch;
- cutover request identity.

A publisher **must fail closed** when any expected value differs from the
value actually observed at write time. This contract defines required
behavior for: a stale process attempting publication after its expected
state has changed elsewhere (reject); repeated operator action re-submitting
the same cutover request (idempotent no-op if already published with
matching digest, reject if attempting a different target); a second cutover
attempt racing the first (exactly one wins, per whichever CAS precondition
still holds; the loser's request record remains on disk, auditable, per the
pattern 135U §13 already established for the rehearsal pointer's ordinary
`os.replace`-wins-second semantics — except Stage 3's CAS strengthens this
from "second writer always wins" to "first writer to satisfy the still-valid
precondition wins, second writer's stale precondition is rejected");
concurrent finalization (ordinary legacy finalization proceeding while a
cutover publish is in flight, §15); concurrent recovery; concurrent
rollback; a pointer that changed after gate evaluation but before
publication (the CAS precondition catches this by construction); source
authority that changed after authorization (the CAS precondition's "expected
source generation or legacy state" field catches this).

**Process-local locking alone is insufficient** — this is adopted directly
from the phase brief and confirmed by this phase's source review: nothing in
the current legacy or Stage 2 mechanisms provides cross-process,
repository-level CAS. This is the concrete implementation target for
PREREQ-2 (§34).

---

## 15. Concurrency contract

**[NEW, re-deriving 135M §55 and 135V §11]** This contract defines required
behavior for:

- two cutover attempts (resolved by §14's CAS: exactly one publishes,
  the other is rejected with an auditable record);
- cutover versus legacy finalization (an ordinary `run_phase_complete` etc.
  invocation proceeding concurrently with a cutover publish attempt — the
  resolver's read (§4) and the publisher's CAS precondition (§14) together
  ensure no reader observes a torn state, and no legacy finalization can
  silently "win" against a cutover it has no CAS-relationship with unless
  the resolver correctly attributes authority post-publication);
- cutover versus Stage 2 forward rehearsal (namespace-isolated by
  construction — the rehearsal pointer and production pointer are different
  files; a rehearsal publish never affects production authority, and a
  cutover publish never touches the rehearsal namespace);
- cutover versus rollback rehearsal (same namespace isolation applies; but
  see §17 for why post-cutover *production* rollback is a distinct, stricter
  mechanism than rehearsal-namespace rollback);
- cutover versus production recovery (recovery reads recorded state only,
  §18; a recovery process **must not** attempt to resolve authority from
  anything other than the last successfully-read, CAS-verified pointer
  state — no independent inference);
- cutover versus reconciliation (`pcae phase-report reconcile` and
  equivalent commands **must** remain read-only with respect to authority
  state, consistent with this phase's own use of `--phase-id` reconciliation
  as read-only, §"Initial inspection" evidence);
- two production finalization entry points racing each other (resolved
  identically to the general concurrency model above — both funnel through
  the same `run_finalization_transaction`, so this is not a new race Stage 3
  introduces, but the checkpoint mechanism, §18, must correctly serialize
  or reject overlapping in-flight transactions for the same transition);
- operator retry (idempotent against the cutover-request identity, §7);
- process restart (recovery, §18, resumes from recorded state, never
  re-derives from scratch);
- stale replay (rejected by §14's CAS).

Required elements: serialization boundary (the CAS-protected production
pointer write is the serialization point for authority changes); lock scope
(scoped to one authority epoch's production pointer, not global); compare-
and-swap state (§14); lock/evidence persistence (durable, on disk, never
in-memory-only); stale-writer rejection (§14); conflict evidence (every
rejected attempt leaves an auditable record); winner/loser semantics (first
writer to satisfy a still-valid CAS precondition wins); recovery
classification (§18); no pointer churn (a rejected writer never partially
mutates the pointer — CAS failure is all-or-nothing).

135U's disclosed gap — "the concurrent-rollback-vs-forward race ... still
has no dedicated concurrency stress test" (135U §19, F-135R-4 lineage) — is
registered as **PREREQ-2** (§34), Blocking for implementation, because
Stage 3's CAS requirement (§14) is precisely the mechanism that would let a
future implementation close it with a real test, not merely "resolved by
construction."

---

## 16. Cross-epoch contract

**[Re-deriving 135V §10's final disposition, adopted as binding]**
**Rollback is allowed only within one authority epoch. Movement between
authority epochs is a new governed authority transition and must roll
forward** (never rollback).

This contract resolves all four 135U-identified gaps normatively, adopting
135V's dispositions (135V §9, §10, §11) as binding requirements on any
future implementation:

1. **Cross-epoch rollback is permanently forbidden.** 135U's own choice —
   "any epoch mismatch between the rollback request and the target [is] a
   hard rejection, not an attempted reconciliation" (135U §19, quoted
   verbatim) — is confirmed as the final architecture, not merely a
   disclosed limitation awaiting a future mechanism. A future
   implementation **must not** build cross-epoch reconciliation; it **must**
   continue rejecting epoch-mismatched rollback requests outright.
2. **A prior epoch may never be reactivated as current production
   authority.** Once an authority epoch is superseded by a newer one via a
   governed cutover (a "new governed authority transition"), the only way to
   return to behavior resembling the prior epoch is a *new* transition that
   creates a *new* epoch — never a reactivation of the old epoch identifier.
3. **Historical generations remain inspectable forever**, regardless of
   epoch, per §32's immutable-history principle — cross-epoch rollback being
   forbidden as a *production authority operation* does not restrict
   read-only historical inspection or reconciliation tooling.
4. **Reconciliation interprets previous epochs read-only.** Any
   reconciliation command (e.g. `pcae phase-report reconcile`,
   `pcae cltr migration rehearsal reconcile`) operating against a historical
   epoch **must** report that epoch's recorded state without attempting to
   resolve it against current authority — it is history, not a candidate for
   restoration.
5. **Disaster recovery differs from ordinary rollback**: ordinary rollback
   (§17) operates within one epoch, using recorded verified prior
   generations. Disaster recovery (a scenario where the production pointer
   or its generation store is itself corrupted or lost) is explicitly **out
   of this contract's scope** — it is not "rollback" in the sense this
   contract defines, and any such mechanism requires its own separately
   governed contract, registered as PREREQ-9 (Deferred, §34).
6. **Rollback to no current authority is forbidden as a production state**,
   directly implementing 135V's disposition of the first 135U gap
   ("rollback to no current rehearsal"): **"Mandatory before Stage 3
   implementation; permanently forbidden as a production authority state.
   Legacy is the implicit default authority absent a published CLTR
   pointer"** (135V §10, quoted). This contract adopts that as binding: a
   production authority pointer, once published for an epoch, may only be
   replaced by CAS-protected publication of another valid generation within
   the same epoch (§14) or by a new-epoch cutover (§13) — never unpublished
   to an empty/absent state while claiming CLTR authority for that epoch. If
   an epoch's CLTR authority must be abandoned, the correct operation is
   legacy-authority reversion via a new governed transition that explicitly
   re-establishes legacy as authoritative for a new epoch (see §17), not a
   silent pointer deletion.

---

## 17. Rollback and roll-forward contract

**[NEW, re-deriving 135M §38–39, 135U, 135V §20]** This contract
distinguishes:

- **Stage 2 rehearsal rollback** — already implemented and verified (135U);
  operates entirely within the rehearsal namespace; never touches production
  authority; remains available unchanged.
- **Pre-publication cutover cancellation** — revoking a human authorization
  (§8) or abandoning a certified-but-unpublished cutover candidate (§11)
  before §13's publication boundary. This is **supported**: because nothing
  externally visible has changed yet (§19's sequencing places publication
  before any external effect), cancellation before publication is safe and
  cheap — simply do not publish.
- **Post-publication local pointer recovery** — restoring the production
  pointer to its immediately prior CAS-verified value, within the same
  authority epoch, before any irreversible external effect (notification,
  §23) has occurred. This is **supported**, using the same CAS mechanism
  (§14) in reverse: a recovery operation is itself a new CAS-protected
  publication targeting the prior generation.
- **Authority-epoch rollback** — forbidden across epochs (§16); within one
  epoch, "rollback" as a production operation is exactly the "post-
  publication local pointer recovery" case above, not a separate mechanism.
- **Production-state rollback** — this contract's scope is limited to the
  authority pointer itself (§13); it does **not** define rollback semantics
  for other production state (git history, other repositories, etc.),
  which is out of scope entirely (§2).
- **External-effect compensation** — after an irreversible external effect
  has occurred (notification dispatched, §19), this contract **prefers
  explicit compensating roll-forward over rollback**, adopting 135M §39's
  principle directly: roll-forward (a new governed transition explicitly
  correcting the error, with its own notification if warranted) is
  preferred because it cannot re-open a window where an already-notified
  recipient sees contradictory state without an explicit, visible
  correction record. This contract does **not** prove that post-
  notification rollback is safe, and therefore does **not** authorize it;
  where compensation is needed after notification, it **must** be roll-
  forward.
- **Governed roll-forward** — per 135U's own precedent ("rolling forward ...
  is simply issuing a new, distinct rollback request whose target is the
  newer generation," 135U §13, verified end-to-end), roll-forward for
  production authority is likewise **not** a distinct mechanism: it is an
  ordinary new cutover request (§7) targeting a newer generation. 135V's
  disposition of the "separate roll-forward command" gap — **"Not required
  for Stage 3 contract freeze or implementation ... Deferred, post-cutover
  hardening at most, not a prerequisite of any kind"** (135V §10, quoted) —
  is adopted as binding: this contract does **not** require a dedicated
  roll-forward command, now or as an implementation prerequisite.

**Stage 2 rollback is explicitly insufficient for production authority
rollback** — the rehearsal pointer's rollback mechanism proves the
mechanics work in an isolated namespace with no external-effect
consequences; it does not prove safety once notification, marker, and
receipt state are in play (§19). Production rollback (the "post-publication
local pointer recovery" case above) **must** additionally satisfy §19's
sequencing constraints, which Stage 2 rollback was never required to.

---

## 18. Crash and recovery contract

**[NEW, re-deriving 135V §19 and 135M's checkpoint model]** Every Stage 3
recovery state **shall** be enumerated and, for each, this contract freezes
the authoritative epoch/generation, allowed retry, allowed replay, required
operator review, rollback/roll-forward policy, evidence requirements, and
reconciliation output:

| State | Authority remains | Retry | Replay | Operator review | Recovery |
|---|---|---|---|---|---|
| No request | unchanged (whatever it was) | n/a | n/a | no | n/a |
| Request persisted, not yet gated | unchanged | yes, idempotent (§7) | yes | no | resume gate eval |
| Gate failed | unchanged | yes, new request | no (stale gate result discarded) | no | resume from readiness package |
| Authorization invalid/expired | unchanged | yes, re-authorize (§8) | no | no | re-authorize |
| Target generation invalid | unchanged | yes, new candidate | no | yes | investigate candidate |
| Certification incomplete | unchanged | yes | no | no | resume certification |
| Certification complete, publication not attempted | unchanged | yes, proceed to publish | yes (cert record reusable if unexpired) | no | resume to publication |
| Temporary pointer written, pre-replacement failure | unchanged (temp file discarded) | yes | n/a | no | clean up temp, retry |
| Atomic replacement attempted, outcome uncertain | **uncertain — must reconcile before further action** | no | no | **yes, mandatory** | readback + reconcile (§13, `UNCERTAIN_PUBLICATION`) |
| Publication verified | new target | n/a (already done) | n/a | no | proceed to derivatives |
| Production derivatives incomplete (report/metadata/status not yet regenerated) | new target (pointer already moved) | yes, regenerate derivatives | idempotent | no | resume derivative generation |
| Report visible, notification not attempted | new target | yes, dispatch | idempotent (PFN-001) | no | resume notification |
| Notification uncertain | new target | **no auto-retry without operator review** | no | **yes** | PFN-001's existing durable-failure-record discipline (§9 of PFN-001) applies unchanged |
| Notification confirmed | new target | n/a | n/a | no | proceed |
| Marker incomplete | new target | yes | idempotent | no | resume marker write |
| Receipt incomplete | new target | yes | idempotent | no | resume receipt finalization |
| Terminal completion | new target | n/a | n/a | no | none needed |
| Conflict (§5, §10) | **fails closed — no new authority established** | no | no | **yes, mandatory** | governed investigation, no automated resolution |
| Quarantine (§29) | unaffected — quarantined material never was authoritative | no | no | **yes, mandatory** | governed disposition |

**Recovery must use recorded state only** — this is the same discipline
already governing legacy's `_load_checkpoint`/`_save_checkpoint` (atomic
write, no CAS today, §14) and Stage 1's shared-input capture: no recovery
path may re-derive or infer authority state from anything other than what
was durably recorded before the interruption. This directly forbids the
class of hazard 135V flagged in Architecture Status (§21 below): inferring
current state from titles, filenames, or "latest" heuristics.

---

## 19. External-effect sequencing contract

**[NEW, re-deriving 135V §"Findings register" ordering discussion and PFN-001
§7]** The required order, with gating, is:

1. target generation verification (§11);
2. certification (§12) — does not publish;
3. authority publication (§13) — the sole externally-visible-authority
   boundary; CAS-protected (§14);
4. production derivative visibility (report/metadata/Architecture Status
   regenerated from the now-authoritative generation, §20–§21);
5. notification authorization (§23 — eligibility certified against the
   *published* generation, never a candidate or certified-but-unpublished
   one);
6. dispatch (PFN-001's unchanged mechanism, §0.3);
7. marker persistence (§24);
8. receipt finalization (§25);
9. terminal reconciliation.

Lifecycle success becomes externally visible **only at step 4 onward** —
specifically, no step before publication (step 3) may produce any artifact a
human or external system could observe as "this transition succeeded,"
because until step 3 nothing is yet authoritative. This directly prevents:

- **notification from a generation that is not authoritative** — step 5's
  gate explicitly requires the *published* generation, closing the
  hazard where a certified-but-unpublished candidate could be notified
  about (which would be a false lifecycle completion, one of the specific
  harms this contract's Purpose section is written against);
- **report, marker, and receipt binding different generations** — because
  each of steps 4, 7, and 8 reads its generation identity from the same
  single publication event (step 3), not from independently-resolved
  state at each step.

---

## 20. Report and metadata contract

**[NEW, re-deriving 135V §16]** For a Stage-3-active authority epoch, the
canonical production report and completion metadata become deterministic
derivatives of the authoritative generation (§3), rendered from its
certified content rather than from legacy's `PhaseReport` object.

Definition: source generation (the published authoritative generation, §13);
derivation rules (deterministic rendering from the generation's bound
representations, CLTR-SCHEMA-001 §5); phase and transition binding
(`phase_id`, `transition_id` both present); authority epoch binding
(recorded in the report); generation digest binding (recorded in the
report); schema/version (recorded); visibility order (per §19, step 4);
atomicity expectations (the report write itself **must** use an atomic
mechanism — this closes **F-135V-5**, the "Gap B" legacy non-atomic
`write_canonical_report`/marker writes this phase's own source review
reconfirmed as live, §14 above; a future implementation **must not**
inherit legacy's plain-`write_text` pattern for Stage-3-authoritative
report writes); "latest" semantics (the production authority pointer, §13,
is the single source of truth for "latest," not a separately-tracked report
file pointer); historical preservation (prior reports remain immutably
readable, §32); compatibility fields (present, per CLTR-SCHEMA-001's
compatibility-adapter discipline, §21); recovery (§18).

**PFR-001 remains binding, unchanged** (§0.4). The report **shall not**
independently establish authority — it is a derivative *of* the
authoritative generation, never a second source of truth competing with the
resolver (§4). Completion metadata **shall not** independently establish
authority, for the same reason.

**F-135V-5 disposition**: 135V classified this as "DEFERRED — should-fix-
before-implementation, not blocking [contract freeze], Before 136A." This
contract adopts that disposition and registers it as **PREREQ-5** (§34):
Blocking for implementation (a Stage-3-authoritative report write using
legacy's non-atomic pattern would itself violate this section's atomicity
requirement), not Blocking for this contract freeze.

---

## 21. Architecture Status contract

**[NEW, re-deriving 135V §17, closing F-135V-6]** Architecture Status
becomes a deterministic presentation derivative, binding: authoritative
generation; phase identity; transition identity; authority epoch;
generation digest; source revision; limitations.

It **must not**: infer identity from titles; infer current state from
prose; become fallback authority; read unbound mutable state.

**F-135V-6 — Architecture Status's narrative-parsing derivation remains
unmigrated** (inherited from 135C, reconfirmed live through 135U, per this
phase's source-review agent locating `parse_phase_id`, `is_valid_phase_id`,
`phase_sort_key` in `src/pcae/core/architecture_status.py` — title/filename-
based parsing, not authority-pointer-based resolution). 135V's disposition:
**"PREREQUISITE for Stage 3 activation (must not consult it as authority),
DEFERRED for contract freeze/implementation, Before 136A activation."** This
contract adopts that disposition and registers it as **PREREQ-6** (§34):
**Blocking for activation** (Architecture Status must not be consulted as
an authority source once Stage 3 is active for an epoch — the resolver rule
in §4 already forbids this categorically), **not Blocking** for contract
freeze or for implementation of the resolver/publication mechanism itself.
Until PREREQ-6 is closed, Architecture Status **may continue** operating on
its existing narrative-parsing derivation as a **presentation-only**
artifact, exactly as it does today — chapter grouping remains
presentation-only, unaffected by this contract.

---

## 22. Checkpoint and promotion contract

**[NEW, re-deriving 135V §18]** Target roles: pre-adapter checkpoint
(`_save_checkpoint` in `finalization_transaction.py`) becomes, for
Stage-3-active epochs, a checkpoint of the cutover-transaction's progress
through §19's sequencing steps, reusing its existing atomic-write mechanism
but requiring the CAS strengthening of §14 where it checkpoints
authority-affecting state; promotion checkpoint and promoted report
generation (`canonical_artifact_promotion.py`'s `promote_artifact`) become a
**compatibility adapter** producing a derivative, legacy-format promoted
output for consumers not yet migrated to read the authoritative generation
directly — never itself authoritative once Stage 3 is active; the
authoritative CLTR generation (§3) is the sole authority; the production
authority pointer (§13) is the sole pointer; recovery state follows §18.

Legacy report promotion becomes a **compatibility adapter**, not a
derivative output that happens to also be authoritative, and not a
mechanism scheduled for immediate retirement — that classification decision
(compatibility-adapter vs. later-retired) is itself frozen here as
"compatibility adapter," with retirement deferred to Stage 5 (§33). **No
checkpoint or promoted report shall independently establish lifecycle
authority after cutover** — this is the same non-authority principle §20
applies to reports, applied here to checkpoints and promoted artifacts.

---

## 23. Notification authority contract

**[NEW, re-deriving 135V §14, preserving PFN-001 per §0.3]** Authoritative
notification intent source: the published authoritative generation (§13),
for Stage-3-active epochs; payload derivation source: the generation's
certified content, rendered the same way §20 renders the report; payload
digest: the generation digest (§3), bound into the notification payload
identity; generation binding: `transition_id` + `generation_digest` present
in the payload; authorization boundary: PFN-001's existing eligibility
certification (`certify_notification_transition`), unchanged, gated
additionally on the resolver (§4) confirming the source generation is
currently authoritative — **Stage 3 shall not dispatch from a
non-authoritative rehearsal or candidate generation**; dispatch adapter
role: PFN-001's existing `notifications.py` dispatch mechanism, unchanged;
exactly-once identity: PFN-001's existing marker-based mechanism, unchanged
mechanism, new input (§24); uncertain-delivery state: PFN-001's existing
`ATTEMPTED`/`SENT`/`SKIPPED_WITH_REASON`/`FAILED_WITH_REASON` outcome
model, unchanged; retry and reconciliation: PFN-001's existing discipline,
unchanged; production marker binding: §24; compatibility treatment of
legacy markers: legacy markers remain valid, unchanged, for legacy-epoch
transitions; they are never reinterpreted as authoritative for a
CLTR-epoch transition.

**Legacy notification code may remain only as a delivery adapter** — this
contract adopts that model explicitly: `notifications.py`'s dispatch
mechanism is preserved unchanged as the *how*; only the *what* (payload
source) and *whether* (authorization boundary) change, and only for
Stage-3-active epochs.

---

## 24. Marker contract

**[NEW, re-deriving 135V §15, preserving PFN-001's `.last-notified.json`
mechanism per §0.3]** A production marker, for Stage-3-active epochs,
**must** bind: authoritative generation ID (`transition_id`); generation
digest; authority epoch; notification intent identity; delivery attempt
identity; delivery outcome; timestamp where allowed (per PFN-001's existing
discipline); contract version (`CLTR-CUTOVER-001/1.0`).

This extends, rather than replaces, the existing marker fields
(`phase_id`, `commit`, `report_digest`, `finalization_snapshot_id`,
`delivery_purpose`) confirmed present today in `.last-notified.json` — the
new fields are additive, consistent with CLTR-SCHEMA-001's own additive-
amendment discipline (§30).

The marker **remains operational evidence. It shall not independently
establish lifecycle truth.** Conflicting markers (two markers claiming
different generations for the same transition/epoch) **must fail closed** —
treated as a conflict state (§5, §18), requiring governed investigation,
never silently resolved by "last write wins."

---

## 25. Receipt contract

**[NEW, re-deriving 135V §15, preserving `delivery_receipt.py`'s existing
mechanism]** The production finalization receipt **must** bind:
authoritative generation; authority epoch; report digest; notification
state; marker identity; checkpoint state; publication evidence; finalization
state; recovery state; contract version.

This extends the existing receipt schema (`receipt_id`, `receipt_digest`,
`phase_id`, `logical_delivery_id`, `logical_state`, `plan_digest`,
`rendering_digest`, `attempts[]`, `authorization_evidence`, `provenance`,
etc., confirmed present in `delivery_receipt.py`) additively — no existing
field is removed or reinterpreted; authority-epoch and generation-digest
fields are new, optional, additive.

**The receipt must not be finalized before all required authoritative and
exactly-once conditions are satisfied** — i.e., receipt finalization occurs
at §19 step 8, strictly after publication (step 3), derivative visibility
(step 4), notification authorization (step 5), and dispatch (step 6). **The
receipt remains derived evidence, not a second authority** — no field
added by this contract may let a receipt substitute for the authority
pointer (§13) as a truth source, adopting 135V §15's own explicit
constraint verbatim.

---

## 26. All-four-entry-point contract

**[NEW, re-deriving 135V §12, grounded in this phase's own source review]**
The four production entry points, confirmed by direct source inspection:

1. `run_phase_complete` (`src/pcae/commands/phase.py:48`) —
   `entry_point="phase_complete"`;
2. `run_task_finish` (`src/pcae/commands/task.py:181`) —
   `entry_point="task_finish"` (plus its recovery-path helper
   `run_task_finish_recover` at `task.py:1021`, not a fifth entry point, but
   a recovery variant of entry point 2, subject to the same rules);
3. `run_phase_report_create` (`src/pcae/commands/phase_reports.py:54`) —
   `entry_point="phase_report_create"`;
4. `run_notify_send_report` (`src/pcae/commands/notifications.py:157`) —
   `entry_point="notify_send_report"`.

All four define a local `_promote_and_dispatch()` closure and call
`run_finalization_transaction(..., promote_and_dispatch=_promote_and_dispatch,
entry_point=<name>)`. This contract freezes that all four **must**: use one
authority resolver (§4); use one cutover/finalization coordinator (the
shared `run_finalization_transaction`, already structurally shared today);
consume the same authoritative generation for a given transition; apply
identical gates (§10); preserve exactly-once behavior (PFN-001, §0.3);
use explicit phase-bound identity; cannot fall back to narrative parsing
(§4, §21); cannot independently publish authority (§13 is the sole
boundary, invoked identically regardless of entry point); cannot dispatch
from legacy data after cutover for that epoch (§23); cannot bypass recovery
state (§18).

**Ordinary and recovery paths are both included** — this phase's source
review found that today's `_ENTRY_POINT_RECOVERY_CLASSIFICATION` mapping in
`finalization_transaction.py` only has dedicated entries for
`"phase_complete"` and `"task_finish"`, falling back to
`"ordinary_finalization"` for the other two entry points (this is the
residue of **F-135P-1**, fixed for the general case in 135S but the
fallback for `phase_report_create`/`notify_send_report` was noted as an
accepted design in 135P/135S, not re-litigated here). This contract does
**not** require closing that fallback as a Stage 3 prerequisite — it is
orthogonal to authority resolution (§4 applies identically regardless of
recovery classification) — but flags it for future hardening consideration,
registered as PREREQ-10 (Deferred, §34) for completeness.

---

## 27. Split-brain prevention contract

**[NEW, re-deriving 135M §22–23 and 135V §21]** Enumerated forbidden states,
each with prevention/detection/classification/reconciliation/recovery/audit:

| Scenario | Prevention | Detection | Classification | Recovery |
|---|---|---|---|---|
| Legacy and CLTR both authoritative | §5 invariant; resolver (§4) reads exactly one pointer state | resolver returns ambiguous read | conflict (§5) | governed investigation, §18 |
| Two CLTR generations current | CAS on production pointer (§14) prevents two publications succeeding | post-publish readback (§13) | conflict if detected post-hoc | investigate, may require quarantine (§29) |
| Two authority epochs current | epoch is part of the CAS precondition (§14); pointer namespace is per-epoch or epoch-qualified | resolver epoch check (§4) | conflict | governed investigation |
| Report from one generation, marker from another | §19 sequencing — both derive from the same publication event | marker/report generation-ID mismatch check | conflict (§24) | governed investigation, never silent accept |
| Notification payload from one generation, receipt from another | §19 sequencing — both derive from the same publication event | receipt/notification generation-ID mismatch check | conflict (§25) | governed investigation |
| Stale recovery process resolving old authority | §18 — recovery uses recorded state only, re-reads current pointer | resolver read at recovery time is authoritative, not cached | stale-writer case (§14) | recovery re-reads current state |
| Different entry points resolving different authority | §26 — one shared resolver, called identically | any divergence is a resolver bug, not a valid state | conflict | investigate resolver implementation |
| Authority pointer and evidence record disagreement | CAS binds pointer write to evidence digests (§13, §14) | readback + digest comparison | conflict | governed investigation |
| Compatibility pointer interpreted as authority | §22 — compatibility/promotion artifacts explicitly non-authoritative; resolver never reads them | code review / conformance check that resolver only reads the production authority pointer | design violation if found | fix resolver implementation |

---

## 28. Security and containment contract

**[Carrying forward Stage 2 protections per 135V §22]** Stage 3 **must**
carry forward and, where production authority is at stake, strengthen: path
traversal protection; absolute-path escape protection; symlink escape
protection (closing the class of hazard 135T's F-135T-1 found — a defined-
but-never-called containment check — Stage 3's publisher **must** ensure
every containment check it relies on is actually wired into the call path,
not merely defined); pointer substitution protection; generation
substitution protection; manifest substitution protection; artifact
substitution protection; phase/transition mismatch detection; final-
revision mismatch detection; migration-epoch mismatch detection; authority-
epoch mismatch detection (§6, §14); schema substitution detection; digest
substitution detection; stale-writer protection (§14); concurrent
publication protection (§15); conflicting replay protection (§14);
quarantine bypass protection (§29); compatibility-pointer confusion
protection (§27, last row).

**No unsafe target may become authoritative.** This is an absolute
requirement, not a best-effort one: any generation failing any containment,
integrity, or gate check **must** be excluded from candidacy entirely (§11),
never published with a caveat.

---

## 29. Quarantine contract

**[NEW, re-deriving 135V §"security and containment" and CLTR-SCHEMA-001's
existing quarantine concept]** Quarantine triggers: invalid target
generation; failed manifest; failed digest; unsupported schema; wrong
authority epoch; stale authorization; conflicting request; pointer
substitution; containment violation; authority ambiguity; post-publication
integrity failure.

Quarantined material: remains auditable (never deleted); cannot be
authoritative (excluded from the resolver's valid-target set, §4); cannot
satisfy readiness (§9 — a quarantined generation cannot count toward the
readiness package); cannot be silently repaired into authority (any
disposition requires explicit governed action, never an automated "un-
quarantine"); cannot be selected by compatibility fallback (§22, §27); and
requires explicit future governed disposition (a separate phase or
explicit operator action, not defined by this contract).

---

## 30. Schema readiness contract

**[NEW — this phase's own evaluation, implementing F-135V-4]** Evaluating
CLTR-SCHEMA-001 v1.0.1 against this contract's requirements:

| Concept | Disposition |
|---|---|
| Authoritative generation identity | **Already represented** — `transition_id` + manifest/digest bindings (CLTR-SCHEMA-001 §16) satisfy §3's needs without change. |
| Authority epoch | **Requires clarification, then minor schema revision.** CLTR-SCHEMA-001 has no dedicated authority-epoch field on the record; the closest analog, `authority_mode` (§25.1, `shadow \| authoritative \| compatibility`), is scoped to the diagnostic envelope, not record identity, and has no epoch-numbering concept. §6's typed-epoch model needs a new field. |
| Cutover request | **Requires new companion schema or minor extension.** No existing binding; §7's fields (source/target epoch, generation identity, evidence digests) are new. |
| Certification | **Requires new companion schema or minor extension.** No existing binding for §12's certification record. |
| Readiness evidence | **Represented by existing extension point.** `compatibility_metadata.limitations` (§7, §23) is structurally suited to carry readiness/limitation disclosures, though §9's full aggregate digest concept is new. |
| Publication state | **Requires minor schema revision.** §13's production-pointer target form (transition_id + generation_digest with CAS precondition fields) has no existing binding; the *rehearsal* pointer's persistence contract (§16–17) is the nearest analog but is explicitly namespace-isolated and non-authoritative. |
| Concurrency conflict / stale-writer evidence | **Requires new companion schema or minor extension.** §14's CAS precondition record has no existing binding. |
| Uncertainty | **Already represented by existing extension point.** `UNCERTAIN_PUBLICATION`-style states already exist in the rehearsal pointer's vocabulary (135S/135T); extending this vocabulary to the production pointer is additive. |
| Rollback/roll-forward classification | **Already represented by existing extension point** — `commit_relationship_classification` and the rehearsal rollback vocabulary (135U) cover the mechanics; §16/§17's policy layer is documentation, not new schema. |
| Notification binding | **Already represented** — existing marker/notification fields (§24) extend additively. |
| Marker binding | **Requires minor schema revision** — §24's new fields (authority epoch, generation digest on the marker) are additive but not yet defined. |
| Receipt binding | **Requires minor schema revision** — §25's new fields likewise additive but undefined. |
| Historical compatibility | **Already represented** — CLTR-SCHEMA-001 §2.6/§2.7's unknown-field-preservation and fail-closed-on-unknown-major rules already cover this. |

**Overall disposition**: several concepts (authority epoch, cutover
request, certification, production publication state, CAS/stale-writer
evidence, marker/receipt extension fields) **require a minor schema
revision** to CLTR-SCHEMA-001 (a MINOR version bump per CLTR-SCHEMA-001
§2's own additive-only discipline — new optional fields and new enum
values, never removing or restructuring existing ones). This is registered
as **PREREQ-4** (§34), directly implementing **F-135V-4**'s classification:
"PREREQUISITE, additive schema revision, Within 135W" — this phase
satisfies the "identify and classify" obligation F-135V-4 imposed; the
actual schema amendment is deferred to a future, separately governed
schema-amendment phase, per §0.2. **No schema is modified by 135W.**

---

## 31. Configuration contract

**[NEW, re-deriving 135V §24]** Conceptually separate configuration
classes, none of which this phase activates:

- shadow mode (Stage 0, already exists, `PCAE_CLTR_MIGRATION_EPOCH` etc.);
- Stage 1 dual derivation (already exists, `dual_derivation_enabled`);
- Stage 2 rehearsal (already exists, `atomic_rehearsal_enabled`);
- rollback rehearsal (already exists, part of Stage 2's rehearsal
  configuration surface);
- Stage 3 code availability (a future flag gating whether Stage 3 code
  *exists and can run at all* — separate from whether it is *used*);
- readiness evaluation (a future flag/mode gating whether the pre-cutover
  gate, §10, may be evaluated — read-only, no side effects);
- cutover request (a future flag/mode gating whether a cutover request may
  be *submitted* — distinct from whether it may be *authorized* or
  *published*);
- authority activation (a future flag gating whether a certified cutover
  may actually be *published*, §13 — the most consequential flag, and the
  one 135M §41 insists must never alone constitute authorization: "no
  implicit cutover through a feature flag alone" means this flag being
  `true` is necessary but never sufficient — human authorization, §8, is
  always additionally required);
- recovery-only mode (a future flag restricting the system to recovery
  operations only, no new cutover requests);
- legacy compatibility mode (governs whether legacy compatibility adapters,
  §22, §32, remain active);
- legacy retirement mode (Stage 5, out of this contract's activation scope,
  §33).

**No single Boolean should silently combine readiness, authorization, and
activation.** These **must** remain independently toggleable, independently
observable configuration dimensions. Invalid combinations (e.g., activation
enabled while Stage 3 code availability is disabled) **must fail closed** —
the more restrictive setting always wins. **This phase adds no active
configuration.**

---

## 32. Compatibility contract

**[NEW, re-deriving 135V §29 and CLTR-001 §25]** Legacy components, once
Stage 3 is active for an epoch, are classified as: delivery adapter
(notification dispatch, §23); formatting adapter (report rendering
compatibility, §20); compatibility output (promoted reports/checkpoints,
§22); historical reader (reading pre-cutover-epoch artifacts); disabled
authority source (legacy's implicit "authority" for that epoch ceases at
publication, §13, but legacy *code* is not deleted); later-retired code
(subject to Stage 5's separate governed plan, §33).

**Compatibility does not imply authority** — this is the same non-authority
discipline applied throughout this contract (§20 for reports, §22 for
checkpoints, §24–§25 for markers/receipts), restated here as the general
principle governing every legacy compatibility component.

**Historical pre-cutover phases remain readable and verifiable** — no
historical artifact is rewritten by Stage 3 activation; every prior
phase's report, metadata, and CLTR shadow/migration/rehearsal evidence
remains exactly as it was, immutably. **No historical artifact shall be
rewritten.**

---

## 33. Demotion and retirement contract

**[NEW, re-deriving 135M §37 and 135V §29]** Distinct stages: authority
cutover (Stage 3, this contract's subject); legacy authority read
disablement (part of Stage 4, legacy demotion — legacy components stop
being *read* as potential authority sources, even as compatibility
adapters they may still be *written* for output purposes); compatibility-
only operation (Stage 4 steady state — legacy fully demoted to
compatibility-adapter role, no read-authority path remains); fallback
disablement (any "if CLTR authority is ambiguous, fall back to legacy"
logic — which this contract already forbids as a steady state, §5 — is
formally removed from the codeleve at this stage, not merely unused);
code retirement (Stage 5 — legacy code deleted).

Exit criteria for each stage are **not** frozen by this contract beyond the
general principle carried forward from 135M §37: **legacy retirement
requires strictly stronger evidence than demotion**, and each stage
requires its own separate governed plan and independent verification.
**135W does not authorize immediate code deletion** — nothing in this
contract, or in any future phase implementing it, may delete legacy code as
part of Stage 3 authority cutover itself.

---

## 34. Prerequisite register

Turning 135V's findings and this phase's own analysis into a binding
prerequisite register:

| ID | Title | Source | Blocking milestone | Deferral status |
|---|---|---|---|---|
| PREREQ-1 | Typed authority-epoch model (replace substring/prefix comparison) | F-135V-1, §6 | **Implementation** | Not deferred — required before Stage 3 code is written |
| PREREQ-2 | Genuine compare-and-swap on production authority pointer (and closing the concurrent rollback-vs-forward race with a real test) | F-135V-2 (from F-135R-4), §14, §15 | **Implementation** | Not deferred |
| PREREQ-3 | Wire adapter comparison sources at real production call sites | F-135V-3 (from F-135L-2) | **Implementation-readiness** (evidence accumulation), not contract-freeze | Not deferred, but does not block this contract |
| PREREQ-4 | Additive CLTR-SCHEMA-001 minor revision (authority epoch, cutover request, certification, publication state, CAS/stale-writer evidence, marker/receipt extension fields) | F-135V-4, §30 | **Implementation** (a schema-amendment phase must precede or accompany implementation) | Classification complete within 135W per F-135V-4's own instruction; amendment itself deferred to a future phase |
| PREREQ-5 | Atomic writes for Stage-3-authoritative report/metadata/marker (closing legacy's non-atomic "Gap B" pattern for the authoritative path) | F-135V-5, §20 | **Implementation** | Deferred (should-fix-before-implementation), "Before 136A" per 135V |
| PREREQ-6 | Architecture Status must not be consulted as an authority source once Stage 3 is active | F-135V-6, §21 | **Activation** | Deferred, "Before 136A activation" per 135V; presentation-only use may continue meanwhile |
| PREREQ-7 | Two-person cutover authorization (optional strengthening) | F-135V-7, §8 | None (optional) | Deferred indefinitely, future governance phase if ever adopted |
| PREREQ-8 | Authorization freshness/expiration window | F-135V-8, §8 | **This contract** | **Resolved within 135W**: 24-hour default, §8 |
| PREREQ-9 | Disaster-recovery mechanism for a corrupted/lost production authority pointer or generation store | §16 (new, this phase) | **Out of this contract's scope entirely** | Deferred to a future, separately governed contract if ever needed |
| PREREQ-10 | `_ENTRY_POINT_RECOVERY_CLASSIFICATION` fallback for `phase_report_create`/`notify_send_report` (orthogonal hardening, not an authority concern) | this phase's own source review, §26 | None — orthogonal to authority resolution | Deferred, non-blocking |

Classification for advancing to each milestone:

- **Blocking for contract freeze (this phase, 135W)**: none. PREREQ-8 is
  the only item this contract itself was required to resolve, and it has
  been (§8).
- **Blocking for implementation**: PREREQ-1, PREREQ-2, PREREQ-4 (the schema
  amendment must land before or alongside implementation code that depends
  on the new fields), PREREQ-5.
- **Blocking for activation** (i.e., may be implemented and tested but not
  turned on in production): PREREQ-6.
- **Deferred / unsupported by design**: PREREQ-3 (accumulates over time, not
  a hard implementation gate), PREREQ-7, PREREQ-9, PREREQ-10.

---

## 35. Acceptance criteria

Exact criteria for advancing to Stage 3 implementation planning (135X and
beyond):

1. Authoritative object is unambiguous (§3) — **complete, this contract**.
2. Resolver is singular (§4) — **complete, this contract** (specified;
   not implemented).
3. Authority publication boundary is singular (§13) — **complete, this
   contract**.
4. Typed authority epochs defined (§6) — **specified as a requirement,
   PREREQ-1**; the typed model itself is an implementation-phase
   deliverable.
5. Cutover request defined (§7) — **complete, this contract**.
6. Authorization defined (§8) — **complete, this contract**, including the
   freshness window (PREREQ-8, resolved).
7. Readiness package defined (§9) — **complete, this contract**.
8. Pre-cutover gate complete (§10) — **complete, this contract**.
9. Compare-and-swap defined (§14) — **specified as a requirement,
   PREREQ-2**; mechanism design frozen here, implementation deferred.
10. Concurrency protocol complete (§15) — **complete, this contract**.
11. Crash/recovery complete (§18) — **complete, this contract**.
12. All-four-entry-point model complete (§26) — **complete, this contract**.
13. Report/metadata migration complete (§20) — **complete as contract**;
    PREREQ-5 gates implementation.
14. Architecture Status migration complete (§21) — **complete as contract**;
    PREREQ-6 gates activation.
15. Checkpoint/promotion migration complete (§22) — **complete, this
    contract**.
16. Notification exactly-once migration complete (§23) — **complete, this
    contract** (PFN-001 unchanged, binding rules frozen).
17. Marker/receipt bindings complete (§24, §25) — **complete as contract**;
    PREREQ-4 gates the schema fields.
18. Cross-epoch policy complete (§16) — **complete, this contract**.
19. Rollback/roll-forward policy complete (§17) — **complete, this
    contract**.
20. Split-brain prevention complete (§27) — **complete, this contract**.
21. Schema disposition complete (§30) — **complete, this contract**
    (classification); PREREQ-4 gates the actual amendment.
22. Configuration contract complete (§31) — **complete, this contract**.
23. No unresolved Blocking contract finding — **true, see §35 verdict
    below and §"Required findings classification"**.

All twenty-three criteria are satisfied **as contract obligations**. Where a
criterion's *implementation* remains open, it is explicitly tracked as a
prerequisite (§34), never silently treated as closed.

---

## 36. No-go criteria

Conditions that prohibit implementation or activation, none of which are
present at contract-freeze time (each cross-referenced to why it is not
currently triggered):

- unclear authoritative object — not present, §3 resolves this;
- more than one authority resolver — not present, §4 mandates exactly one;
- dual-authority interval — not present as a *steady state*, §5, §13, §19
  bound it to zero duration by design;
- no stale-writer protection — **currently true of legacy/Stage 2 code**
  (§14's own findings), which is exactly why PREREQ-2 is Blocking for
  implementation — this is a no-go **for implementation**, not for this
  contract freeze;
- no repository-level concurrency control — same as above, PREREQ-2;
- no post-publication recovery state — not present as a contract gap, §18
  fully enumerates it; would only become a no-go if an implementation
  omitted it;
- no notification exactly-once design — not present, PFN-001 already
  provides it, §23 binds Stage 3 to it;
- mismatched report/marker/receipt generation risk — mitigated by design,
  §19's sequencing, §27's detection table; would become a no-go only if an
  implementation violated §19;
- unresolved schema gap — **currently true**, PREREQ-4, Blocking for
  implementation, not for this contract;
- unsupported cross-epoch ambiguity — resolved, §16 forbids cross-epoch
  rollback outright rather than leaving it ambiguous;
- unclear rollback/roll-forward policy — resolved, §17;
- missing human authorization — not present as a contract gap, §8 fully
  specifies it; would be a no-go if an implementation attempted cutover
  without it;
- unresolved containment issue — not present as a contract gap, §28
  carries forward and extends Stage 2's protections; F-135T-1's specific
  containment bug was already repaired within 135T;
- unresolved Blocking finding — none identified in this phase (§35 below);
- inability to prove production outputs bind one generation — not present
  as a contract gap, §19's sequencing plus §27's split-brain table address
  this; a future implementation must actually prove it, which is a
  verification-phase (135X) responsibility, not a 135W gap;
- inability to disable legacy authority atomically — not present as a
  contract gap; §13's last paragraph specifically defines legacy's
  cessation of authority as the same atomic event as CLTR's publication.

**None of these conditions currently block this contract freeze.** Several
(stale-writer protection, schema gap) correctly block *implementation*
until PREREQ-2 and PREREQ-4 close — this is by design, not an oversight.

---

## 37. Verification matrix

This matrix governs 135X (Stage 3 Authority-Cutover Contract Independent
Verification). Each row is a requirement ID, its contract section, source
rationale, verification method, expected evidence, Blocking classification,
and implementation milestone.

| Req ID | Section | Source | Verification method | Expected evidence | Blocking? | Milestone |
|---|---|---|---|---|---|---|
| VR-1 | §3 Authoritative object | 135V §4, §8 [NEW binding] | Independent re-derivation: does the object definition actually prevent a bare CLTR record from being treated as authoritative? | Adversarial argument or counterexample search | Blocking if VR-1 fails | 135X |
| VR-2 | §4 Authority resolver | 135V §12 [NEW binding] | Trace all four entry points' call graphs; confirm no entry-point-specific authority logic exists or is implied | Source-level confirmation (post-implementation) or design-level confirmation (at 135X) | Blocking | 135X, re-confirmed at implementation verification |
| VR-3 | §5 Single-authority invariant | [NEW] | Enumerate every externally visible boundary listed; confirm none is missing | Boundary checklist cross-check against actual codebase surfaces | Blocking | 135X |
| VR-4 | §6 Authority epochs | F-135V-1 [NEW] | Confirm the typed-model requirement is unambiguous enough to implement without further interpretation | Independent reviewer attempts to specify the typed format from this contract alone | Non-blocking (implementation detail) | 135X, closed at implementation |
| VR-5 | §7 Cutover request | 135V §5 [NEW] | Confirm determinism requirement is implementable (no wall-clock/UUID dependency) | Design walkthrough | Blocking | 135X |
| VR-6 | §8 Human authorization | 135M §41 [binding], 24h window [NEW] | Confirm freshness window and revocation semantics are unambiguous | Design walkthrough | Blocking | 135X |
| VR-7 | §9 Readiness package | 135V §26 [NEW] | Confirm aggregation sources are all independently verifiable evidence, not self-reported | Cross-check each listed source against its actual verification phase | Blocking | 135X |
| VR-8 | §10 Pre-cutover gate | 135M §7, 135V §9 [NEW] | Confirm the four-outcome model (eligible/ineligible/uncertain/conflict) is exhaustive and fail-closed | Adversarial state enumeration | Blocking | 135X |
| VR-9 | §11–§12 Candidate/certification | 135V §8 [NEW] | Confirm certification cannot itself publish authority (separation of concerns) | Design walkthrough | Blocking | 135X |
| VR-10 | §13 Authority publication | 135M §22–23, 135V §4/§11 [NEW] | Confirm exactly one publication boundary; confirm legacy cessation is the same event as CLTR publication | Design walkthrough; adversarial search for a second boundary | Blocking | 135X |
| VR-11 | §14 CAS / stale-writer | F-135V-2 [NEW] | Confirm CAS precondition set is complete (no missing expected-state field that could allow a stale write) | Adversarial enumeration of writer scenarios | **Blocking** | 135X, then implementation-time test verification |
| VR-12 | §15 Concurrency | 135M §55, 135U F-135R-4 lineage [NEW] | Confirm every named concurrency scenario has a defined resolution | Scenario-by-scenario cross-check | Blocking | 135X |
| VR-13 | §16 Cross-epoch | 135V §10 [binding disposition] | Confirm all four 135U gaps are genuinely closed by this section, not merely restated | Direct comparison against 135U §1/§13/§19 quotes | Blocking | 135X |
| VR-14 | §17 Rollback/roll-forward | 135M §38–39, 135U §13 [binding] | Confirm post-notification rollback is genuinely forbidden (not merely discouraged) | Text audit for normative strength ("must" vs. "should") | Blocking | 135X |
| VR-15 | §18 Crash/recovery | 135V §19 [NEW] | Confirm every state in the table has a defined, non-contradictory recovery action | State-machine completeness check | Blocking | 135X |
| VR-16 | §19 External-effect sequencing | PFN-001 §7, 135V [NEW ordering] | Confirm the nine-step order actually prevents false lifecycle completion under every crash point in §18's table | Cross-reference §18 states against §19 steps | Blocking | 135X |
| VR-17 | §20 Report/metadata | 135V §16, PFR-001 [preserved] | Confirm PFR-001's thirteen sections remain satisfiable under the new derivation source | Section-by-section mapping | Blocking | 135X |
| VR-18 | §21 Architecture Status | F-135V-6 [binding disposition] | Confirm the "must not consult as authority" rule is actually enforceable given Architecture Status's current narrative-parsing implementation | Source-level gap confirmation (already done, §21) | Blocking for activation only | 135X notes; re-verified at PREREQ-6 closure |
| VR-19 | §22 Checkpoint/promotion | 135V §18 [NEW] | Confirm promoted-report compatibility-adapter classification doesn't create a second authority path | Design walkthrough | Blocking | 135X |
| VR-20 | §23 Notification | PFN-001 [preserved], 135V §14 [NEW binding] | Confirm PFN-001's contract text is genuinely unmodified by this section | Diff against PFN-001 §4/§5/§8/§9 | Blocking | 135X |
| VR-21 | §24 Marker | 135V §15 [NEW binding] | Confirm additive-only field extension, no removal/reinterpretation of existing marker fields | Diff against current `.last-notified.json` schema | Blocking | 135X |
| VR-22 | §25 Receipt | 135V §15 [NEW binding] | Confirm additive-only field extension | Diff against current receipt schema | Blocking | 135X |
| VR-23 | §26 All-four-entry-point | 135V §12 [confirmed by source review] | Confirm entry-point enumeration is still accurate (no fifth entry point added since) | Source re-grep at verification time | Blocking | 135X |
| VR-24 | §27 Split-brain | 135M §22–23 [NEW table] | Confirm every scenario has both prevention and detection, not merely one | Table completeness check | Blocking | 135X |
| VR-25 | §28 Security/containment | 135V §22, F-135T-1 lineage [carried forward] | Confirm containment checks are actually wired at call sites (not merely defined, as F-135T-1 found) | Source-level wiring check at implementation time | Blocking at implementation | 135X notes; closed at implementation |
| VR-26 | §29 Quarantine | [NEW] | Confirm quarantine triggers are exhaustive relative to the failure modes enumerated elsewhere in this contract | Cross-reference against §14, §28 failure modes | Blocking | 135X |
| VR-27 | §30 Schema readiness | F-135V-4 [this phase's classification] | Confirm the disposition table is complete relative to CLTR-SCHEMA-001 v1.0.1's actual field catalog | Independent schema re-read | Blocking | 135X |
| VR-28 | §31 Configuration | 135V §24 [NEW]| Confirm no configuration class silently combines readiness/authorization/activation | Enumeration check | Blocking | 135X |
| VR-29 | §32 Compatibility | CLTR-001 §25 [preserved], 135V §29 [NEW] | Confirm historical immutability is genuinely preserved (no rewrite path exists) | Design walkthrough | Blocking | 135X |
| VR-30 | §33 Demotion/retirement | 135M §37 [binding] | Confirm 135W does not itself authorize any code deletion | Diff review (this phase changed no production/test source) | Blocking | 135X |
| VR-31 | §34 Prerequisite register | F-135V-1..8, this phase's source review [NEW] | Confirm every prerequisite traces to a real, cited finding, none invented without source | Citation audit | Blocking | 135X |
| VR-32 | §35–§36 Acceptance/no-go | [NEW] | Confirm the acceptance criteria are neither trivially satisfied nor impossible to satisfy | Adversarial critique | Blocking | 135X |

---

## 38. Versioning and amendment

- **Contract version**: `CLTR-CUTOVER-001 v1.0`, frozen as of Phase 135W.
- **Backward-compatible clarification rules**: a future amendment that adds
  detail without changing any "must/shall" requirement's meaning, or adds a
  new optional field, may be released as `v1.1`, `v1.2`, etc. (minor),
  following CLTR-001 §27's and CLTR-SCHEMA-001 §2's precedent.
- **Breaking-change rules**: any change to a Blocking invariant (§5's
  single-authority invariant, §14's CAS requirement, §16's cross-epoch
  prohibition, §19's sequencing order, or any requirement marked
  **must**/**shall**/**must not**/**shall not** above) requires a new major
  version (`v2.0`) and a separate governed contract-amendment phase — never
  a silent reinterpretation within v1.x.
- **Relationship to schema versions**: `CLTR-CUTOVER-001`'s version is
  independent of `CLTR-SCHEMA-001`'s version (per §0.2's "both frozen, both
  in force, neither supersedes the other" pattern already established
  between CLTR-001 and CLTR-SCHEMA-001). A CLTR-SCHEMA-001 minor revision
  implementing PREREQ-4 does not itself require a CLTR-CUTOVER-001 version
  bump, provided it satisfies this contract's field requirements as
  specified.
- **Migration rules**: a future major version of this contract must specify
  its own compatibility floor and, per CLTR-SCHEMA-001 §2.9's guidance
  precedent, should (not must) ship a field-by-field migration map.
- **Amendment authority**: only a governed contract-amendment phase,
  explicitly named as such, may change this contract's binding text.
- **Historical verification**: a verifier built against `v1.0` must reject
  (not silently accept) a record or request claiming an unrecognized
  `contract_version`, per CLTR-001 §27's precedent, applied here identically.

**No implementation may silently reinterpret CLTR-CUTOVER-001.**

---

## Required findings classification

| ID | Title | Source | Affected section | Authority impact | Concurrency impact | Recovery impact | Exactly-once impact | Schema impact | Required resolution | Latest acceptable resolution phase |
|---|---|---|---|---|---|---|---|---|---|---|
| CONFIRMED-135W-1 | 135V's F-135V-1 through F-135V-8 are all traced to real, quoted source material; none were reinterpreted in this phase's drafting | This phase's own citation audit | throughout | none — confirms accuracy | none | none | none | none | none, informational | n/a |
| PREREQUISITE-135W-1 | Typed authority-epoch model | F-135V-1 | §6 | High — resolver correctness depends on it | Low | None | None | Low | Implement before Stage 3 code | Implementation phase |
| PREREQUISITE-135W-2 | Genuine CAS on production pointer | F-135V-2 | §13, §14, §15 | High — the core split-brain prevention mechanism | **High** — this is the concurrency-safety mechanism itself | Medium — crash-during-publish states depend on it | Low | None | Implement before Stage 3 code | Implementation phase |
| PREREQUISITE-135W-3 | Wire adapter comparison sources | F-135V-3 | §9 (readiness evidence) | Low — affects evidence completeness, not the resolver itself | None | None | None | None | Accumulate over time | Implementation-readiness, ongoing |
| PREREQUISITE-135W-4 | Additive CLTR-SCHEMA-001 minor revision | F-135V-4 | §30, throughout (field bindings) | Medium — needed fields don't exist yet | None | None | Low | **High** — this is a schema change | Separate governed schema-amendment phase | Before/alongside implementation |
| PREREQUISITE-135W-5 | Atomic writes for Stage-3-authoritative artifacts | F-135V-5 | §20 | Medium — split-visibility hazard if unaddressed | Low | Low | Low | None | Implement before Stage 3 activation | Before 136A per 135V |
| PREREQUISITE-135W-6 | Architecture Status must not be authority source | F-135V-6 | §21 | High if violated — would reintroduce narrative-parsing hazard | None | None | None | None | Enforce at resolver level (already contracted, §4); migrate Architecture Status derivation before activation | Before 136A activation per 135V |
| BLOCKING-135W-NONE | No CONFIRMED-BLOCKING-for-contract-freeze finding was identified | This phase's own analysis, consistent with 135V's own "no CONFIRMED-BLOCKING-for-contract-freeze finding exists" | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| DEFERRED-135W-1 | Two-person authorization | F-135V-7 | §8 | Low (optional strengthening) | None | None | None | None | Future governance decision if ever adopted | Indefinite |
| DEFERRED-135W-2 | Disaster recovery for corrupted pointer/store | this phase, §16 | §16, §17 | Medium, but explicitly out of scope | None | High if ever needed | None | None | Separate future contract if ever needed | Indefinite |
| DEFERRED-135W-3 | Entry-point recovery-classification fallback | this phase, §26 | §26 | None (orthogonal) | None | Low | None | None | Optional hardening | Indefinite |

No prerequisite above is labelled "Non-Blocking" without stating the exact
milestone it blocks (§34's table restates this per-item).

---

## Contract verdict

**CONTRACT FROZEN WITH PREREQUISITES — READY FOR INDEPENDENT VERIFICATION**

Rationale: every scope item in §2 has a complete normative section (§3–§33);
the prerequisite register (§34) traces every open item to a specific,
cited 135V finding or this phase's own source-grounded analysis, each with
an explicit Blocking milestone (never left as an unqualified "Non-
Blocking"); no finding in this phase's own classification (above) rises to
CONFIRMED-BLOCKING-for-contract-freeze; the two items this contract was
itself obligated to resolve — the authorization freshness window (F-135V-8)
and the schema-gap classification (F-135V-4) — are both resolved within
this document (§8's 24-hour window; §30's disposition table). Four items
remain Blocking for **implementation** (PREREQ-1, PREREQ-2, PREREQ-4,
PREREQ-5) and one for **activation** (PREREQ-6) — this is the expected and
correct shape of a "frozen with prerequisites" verdict, not a defect in the
freeze itself.

---

## No-implementation proof

This phase changed no production source, no test source, and no schema.
Confirmed by this phase's own diff (see "Before finalization" below) and by
direct statement:

- No production source changed.
- No test source changed.
- No schema changed.
- No Stage 3 code was added.
- No authority resolver was implemented.
- No authority pointer was implemented or changed.
- No cutover request was executed.
- No authority epoch changed.
- No CLTR authority was created.
- No legacy authority was demoted.
- No legacy authority was retired.
- No notification, marker, receipt, report, metadata, Architecture Status,
  checkpoint, or promotion behavior changed.
- No execution capability was introduced.

Runtime remains: **Observed / observe / execution unavailable** — confirmed
by this phase's `pcae runtime inspect` re-run (see Initial Inspection
evidence in the accompanying phase-completion report), unchanged from
135V's own confirmation.

---

## Recommended next phase

**135X — Stage 3 Authority-Cutover Contract Independent Verification**

135X must independently re-derive and attack this contract — in particular
the verification matrix (§37), the prerequisite register (§34), and the
cross-epoch/rollback dispositions (§16, §17) that resolve all four 135U
gaps. 135X must not begin implementation planning. 135X must not begin
Stage 3 implementation.

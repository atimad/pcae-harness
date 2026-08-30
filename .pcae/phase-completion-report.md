# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 Complete — Runtime-Dispatch Contract Normalization Implementation

**Phase ID:** 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4
**Type:** contract normalization + durable-representation implementation
**Status:** IMPLEMENTED — INDEPENDENT VERIFICATION PENDING (×3)
**Production source changed:** `src/pcae/core/runtime_invocation_authority_consumption.py` + `src/pcae/core/runtime_dispatch_gate9.py` only (`git diff --name-only 1babaa95 HEAD -- src/pcae`)
**Normative contracts changed:** RDGO-001 v3.0 → **v3.1**, PBRD-001 v2.0 → **v2.1**, HPAC-001 v2.0 → **v2.1**, RIASC-001 v3.0 **+ §9 errata note (no bump)**, RIHAC-001 **cross-refs refreshed (no bump)**, RE No-Go Registry schema 1.0 → **1.1**
**Consumption-record schema:** `HPAC-AUTHORITY-CONSUMPTION/2.0` → **`/2.1`** (new closed binding object `authority_generation_binding` / `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`)
**Runtime:** `not_implemented / Observed / observe / unavailable`; POL-005 byte-unchanged; real execution UNAVAILABLE; deterministic authentication NON_REAL
**Phase-entry SHA:** `1babaa95` · **immutable A/B baseline:** `4d480553` (`.1R.15.3` final)

## Summary

Normalized the frozen runtime-dispatch contracts to the independently
verified Gate 5→Gate 9 architecture (`.1R.15.1` blueprint §7–§20) and added
the durable authority-generation-snapshot representation required before
Gate-10 planning.

**RDGO-001 v3.1 (MINOR).** §4/§6/§16 — the HPAC-001 v2.1 verifier's
assurance-independent HPAC-REQ-054 step 10 creates HPAC lifecycle sequence 3
at gate 3; gate 5 does **not** create it, gate 5 read-only **re-confirms**
(V-2/V-3); sequence 3 binds the `HPAC-APPROVAL-SUBJECT/2.0` subject digest,
not the completed approval `record_digest`. §8 — PB policy is owned
exclusively by gate 6; gates 7/9 revalidate authority currentness + posture
only (V-13-3-1). §9 — three-layer Gate-8 containment model: direct
validation + canonical commitment of the complete launch environment into
`containment_evidence_digest` + gate-9 recomputation; effect plan is
coordinator-assembled so no caller cwd/env/transport reference to diff
(V-13-5-1). §10 — the per-`proof_id` create-only atomic primitive **is** the
linearization point and sole transaction mechanism; revalidation battery →
`S1` → record build → `S2` re-read with zero effectful I/O → `S2 != S1`
fails closed; a residual instruction-level micro-window is the acknowledged
practical limit, no external effect (V-15-1); "eight items" → **nine
items** (item 9 = `authority_generation_binding`); `/2.0` → `/2.1`. §11 —
gate-10 forward read-back prerequisite (semantics only; no gate-10 design,
no phase ID): `is_gate9_result` + `status=="consumed"` + durable
`consumption.json` re-read with `authority_generation_binding` present/valid
+ exact lineage + runtime capability eligible + re-validation of all mutable
authority *and* re-derivation of the current generation vector vs the
durable snapshot. §21 — v3.1 MINOR verdict; durable items 9.

**PBRD-001 v2.1 (MINOR).** §4a `human_authority_binding`
representation-equivalence clause (V-4): the 7 *logical* fields, their
meaning, and `DENY > HUMAN_REVIEW > ALLOW` precedence are unchanged; the
closed 3-tuple `(approval_id, approval_record_digest,
validation_evidence_digest)` is a permitted equivalent under three provisos;
two contexts differing in any logical field MUST NOT collapse.

**HPAC-001 v2.1 (MINOR).** §41 HPAC-REQ-098 nine closed binding objects (the
eight `/2.0` byte-unchanged + `authority_generation_binding`); new
HPAC-REQ-098a defines the closed 6-field `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`
(schema-version const + 5 markers over durable state); HPAC-REQ-099
rewritten to the create-only-linearization + zero-I/O `S1`/`S2` model with
the residual-micro-window disclosure; HPAC-REQ-097 sequence-3 cross-ref.
§37/§44 — v2.1 MINOR (additive verification evidence, no authority widened).

**RIASC-001 §9 errata note (no version change).** `record_digest` and the
`HPAC-APPROVAL-SUBJECT/2.0` digest are distinct commitments; sequence 3 does
not bind `record_digest` (V-3).

**RE No-Go Registry schema 1.1.** Additive "Enforcement class" column
classifying all 17 entries — per-decision (001–008, 010, 011) /
environmental-readiness (009, 013, 015, 016, 017) / advisory (012, 014) —
plus a scoping paragraph: `Gate7Result.matched_no_go_ids` projects only the
per-decision subset; gate-7 progression depends on the authoritative
decision, not projection completeness (V-13-3-2).

**RIHAC-001 (unchanged).** Sibling-contract version cross-references
refreshed to v3.1 / v2.1 / v2.1; §23 note — the §14 append-only
early-revocation-artifact boundary is confirmed, **not amended** (the gate-9
`approval_generation` marker carries only a `null` forward hook for it).

**Both `.1R.15.1` MAJOR-candidate judgment calls** — RDGO sequence-3-creation
narration, PBRD closed-shape — adjudicated **MINOR** with primary-source
justification: neither alters external trust semantics, the required
authority shape, or consumption-record compatibility fundamentally.

## Durable authority-generation snapshot

`HPAC-AUTHORITY-CONSUMPTION/2.1` adds the closed 6-field
`authority_generation_binding` object as a **new top-level sibling binding
object** (Option A's dedicated typed/closed object, not nested in
`authority_binding`, not a reference — chosen for consistency with the
store's flat sibling closed-binding-object pattern, not minimal diff).
Gate 9 durably commits the **exact `S1`** snapshot it verified unchanged at
`S2` immediately before the create-only linearization — built at step 15
from the step-14a capture, **never rebuilt from post-`S2` state**. It is
**verification evidence for gate 10's mandatory re-read, not a bearer
token**: no capability field, grants nothing on possession. A `/2.0` record
(no `authority_generation_binding`) is readable historical/test data but
**gate-10-ineligible**; gate 9 writes only `/2.1`; an unknown schema
version is durability-uncertain → fail closed. No `/2.0` durable record
exists in the repository.

## N-15-3-2 — production authority-generation resolver completeness

`build_production_authority_generation_resolver(*, principal_registry,
principal_id, credential_id, approval_store, approval_id)` (new, exported
from `runtime_dispatch_gate9`) folds the current resolved immutable approval
`record_digest` + `approval_id` + a `null` RIHAC-001 v2.0 §14 forward hook
into `approval_generation`, and fails closed on an absent/unreadable
principal / credential / approval. **RIHAC-001 v2.0 §14 (frozen, NOT
amended):** there is no separate approval-revocation store; approval
revocation is transitively principal / credential / lifecycle / expiry (all
own tokens). Not invoked on any production path (no production Gate-9
caller); the coordinator body reads no approval store (HPAC-REQ-102).
Completeness matrix (`.1R.15.4` §5.3): every authority-relevant mutable
source moves a token or fails closed — **not blocking**.

## Phase-document errata (originals preserved; historical verdicts intact)

`.1R.9` §12/§13.5 (the "acquire a lock before the §12 battery" bullet is
internally contradicted by "do not invent a new lock" — the latter + §18
are the frozen model); `.1R.13.1` §11.2 (strike `gate8_transport_drift`,
reword cwd/env rows) / §13/§19.1 ("sole source" → "sole source *for the
per-decision projection*") / §16.2-inv-4 (no held lock); `.1R.13.2` prose
(transitive-PB-policy-coverage overstatement — V-13-3-1); `.1R.14`/`.1R.15`
top-of-doc (v3.0→v3.1, `/2.0`→`/2.1`, serialization-boundary wording).

## Tests & regression

New `tests/test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4.py`
— **36/36** (contract traceability for every finding; `/2.1` durable schema
closed-field / malformed / `/2.0` compat; N-15-3-2 resolver completeness;
durable write / restart / read-back / reconstruction; post-consumption
drift; no-bearer; Gate9Result forward semantics). `.1R.15.3` §35 critical
properties re-run unchanged (56/56); Gate-9 `.1R.14`/`.1R.15`/`.1R.15.2` and
Gate 5–8 integration + verification suites all green.

**Fixed-SHA A/B** — immutable baseline `4d480553` via a dedicated `git
worktree`, deterministic `-p no:randomly`, **no xdist**, 36-file targeted
set: **1339 passed / 60 pre-existing failed identical at baseline and
HEAD**; +36 new passing. **CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING
NODES = 0; UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.** The 60
baseline=HEAD failures are pre-existing and unrelated (the `3V.1` /
`3V.1R.1` / `3V.1R` suites pin RDGO v2.0 / PBRD v1.1 / RIHAC v1.0 — stale
since the `.1R` v3/v2 freeze; HPAC-foundation `blocking_reproduction_*`
fixtures; a HATP contract-byte test; `_GATE5_RESULTS` / `_GATE6_DECISIONS`
xdist cross-file-pollution flakes). 24 byte-identity / production-scope
scope-fence assertions from `.1R.10` → `.1R.15.3` were repinned to the fixed
`.1R.15.3` end SHA `4d480553` (intended contract-byte test changes,
classified per phase-prompt §42); cardinality tests updated to nine durable
items; cross-contract version-graph and contract-hash pins refreshed.

## Verdict

**RUNTIME-DISPATCH CONTRACT NORMALIZATION: IMPLEMENTED — INDEPENDENT
VERIFICATION PENDING.**
**DURABLE GATE-10 GENERATION-SNAPSHOT REPRESENTATION: IMPLEMENTED —
INDEPENDENT VERIFICATION PENDING.**
**N-15-3-2 APPROVAL-GENERATION COMPLETENESS: IMPLEMENTED — INDEPENDENT
VERIFICATION PENDING.**

No self-close. V-2 / V-3 / V-4 / V-13-3-1 / V-13-3-2 / V-13-5-1 / V-15-1
NORMALIZED and N-15-3-2 IMPLEMENTED subject to `.1R.15.5`. V-15-2 / V-15-3
remain independently CLOSED (`.1R.15.3`). Production diff =
`runtime_invocation_authority_consumption.py` + `runtime_dispatch_gate9.py`
ONLY; Gate 5/6/7/8 byte-unchanged. New findings: N-15-4-1 (INFO — the `/2.0`
read tolerance is defence-in-depth); no new blocking; no class E. Gate 10
keeps **NO phase ID** (`.1R.15.1` §20 items 1, 8, 10 not satisfied until
`.1R.15.5`). `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`
preserved; governed PCAE lifecycle only.

## Recommended next phase

**`149O.20L.7O.3W.1R.2B.1R.1.1R.15.5` — Independent Verification of the
Runtime-Dispatch Contract Normalization.** Not begun. Requires its own
separate explicit human authorization. Do not begin `.1R.15.5`. Do not plan
or implement Gate 10; it keeps no phase ID. Do not enable execution.

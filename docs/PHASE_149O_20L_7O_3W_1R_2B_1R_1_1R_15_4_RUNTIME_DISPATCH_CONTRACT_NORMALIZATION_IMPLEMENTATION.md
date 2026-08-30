# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 — Runtime-Dispatch Contract Normalization Implementation

**Type:** contract normalization + durable-representation implementation.
**Status:** IN PROGRESS (this document is authored incrementally during the phase).
**Phase-entry SHA:** `1babaa95` (`Phase …1R.15.4: open dedicated governed phase task`); pre-phase `origin/main` / immutable A/B baseline `4d480553` (`.1R.15.3` final).
**Governance:** governed `pcae` lifecycle only. The delegated `.3` finalization / commit / push incident remains **UNAUTHORIZED**; only the primary human-authorized operator holds `.1R.15.4` lifecycle authority.

Do not begin `.1R.15.5`. Do not plan or implement Gate 10 (no module, symbol, plan, or phase ID). Do not enable execution — runtime remains `not_implemented / Observed / observe / unavailable`; POL-005 unchanged.

---

## 1. Governing prerequisite state (treated as independently verified)

Gate 5 / 6 / 7 / 8 / 9 — CLOSED. V-15-1 Gate-9 serialization window — CLOSED. V-15-2 — CLOSED. V-15-3 — CLOSED. Runtime: `Observed / observe / unavailable`. Gate 10 — no phase ID, not authorized.

## 2. Initial repository inspection (phase prompt §4)

```
git status --short                       -> clean
git status --branch --short              -> ## main...origin/main
git log --oneline origin/main..HEAD      -> (empty at bootstrap; 4d480553 latest)
git rev-list --count origin/main..HEAD   -> 0
pcae health                              -> healthy; agent lock claude-local; continuity verified
pcae check                               -> passed
pcae status coherence                    -> coherent
pcae doctor task-memory                  -> warning-only historical tasks/DONE.md omissions (pre-existing O4)
pcae push check                          -> nothing_to_push; phase-report trust + identity passed
pcae runtime inspect                     -> not_implemented / Observed / observe / unavailable; 0 plugins / 0 capabilities; PB execution_unavailable; non-executing
source ~/.config/pcae/telegram.env; pcae notify status -> configured, enabled, outbound-ready
pcae phase-report show --latest          -> .1R.15.3 completed, complete, pushed, origin/main..HEAD 0
```

Confirmed: `.1R.15.3` latest completed; repository clean; no active governed phase before task open; runtime unchanged.

### 2.1 Primary sources read in full

- `.1R.15.1` planning/reconciliation (1469 lines) — §7–§20 proposed deltas, §22 forward invariant, §23 Path C.
- `.1R.15.2` (Gate-9 serialization repair) — §3 contract-embedding deferral, §4.2 token inventory, §13 N-15-2-2.
- `.1R.15.3` (independent verification) — §5.2 finding N-15-3-2.
- `.1R.9` §12 / §13.5 / §18 (lock self-contradiction); `.1R.13.1` §11.2 / §13 / §16.2.
- Contracts (current frozen text): RDGO-001 v3.0, PBRD-001 v2.0, RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0, `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` (schema 1.0).
- Production source line-by-line: `runtime_dispatch_gate9.py`, `runtime_invocation_authority_consumption.py`, `runtime_dispatch_gate5.py` (sequence-3 confirmation), `hpac_verifier.py` (`bind_gate5_canonical`), `runtime_invocation_approval_store.py`, `human_principal_registry.py`.

## 3. Versioning adjudication (phase prompt §5, §40)

| Contract | Current | New | Bar met | MAJOR-candidate check |
|---|---|---|---|---|
| RDGO-001 | v3.0 | **v3.1 (MINOR)** | §21 "additive only if gates 1–11 … retain their meaning and order" — no gate reorder, no first-effect-boundary move, no authority/permission merge | **(i) sequence-3 *creation* narration** (V-2): reallocating which gate the existing HPAC-REQ-054-step-10 mechanism runs under changes **no** lifecycle event bytes, binding, assurance decision, or consumption. External trust semantics unchanged. **MINOR.** |
| PBRD-001 | v2.0 | **v2.1 (MINOR)** | §16 "additive request evidence … only when existing meanings, action behavior, and precedence remain unchanged" | **(ii) closed *shape* of `human_authority_binding`** (V-4): the 7 logical fields, their meaning, and `DENY>HUMAN_REVIEW>ALLOW` precedence are unchanged; only a documented equivalent representation is added. **MINOR.** |
| HPAC-001 | v2.0 | **v2.1 (MINOR)** | §37 "additive clarification or optional evidence may increment MINOR only when it does not widen existing authority" — the durable generation snapshot is verification evidence, grants no capability (phase prompt §16) | not a MAJOR candidate |
| HPAC-AUTHORITY-CONSUMPTION | /2.0 | **/2.1** | additive closed binding object; no field removed, no meaning changed | — |
| HPAC-AUTHORITY-GENERATION-SNAPSHOT | — | **/1.0** (new) | new closed schema | — |
| RIASC-001 | v3.0 | **v3.0 + errata note** (no bump) | §1 "an additive future field requires a new schema MINOR … " — no field added; a non-normative cross-reference clarification only | — |
| RE No-Go Registry | schema 1.0 | **schema 1.1** | "Canonical statements amended only via versioned change"; additive classification column | — |

No MAJOR is forced. Both `.1R.15.1` MAJOR-candidate judgment calls are adjudicated **MINOR** with the primary-source justification above.

## 4. Durable authority-generation snapshot — architecture (phase prompt §14–§18)

### 4.1 Selected representation — a new closed top-level binding object

`.1R.15.1` §14 offered Option A (new field *inside* `authority_binding`) and Option B (a separate object *referenced by* `authority_binding` via a digest). **Selected: Option A's "dedicated typed/closed object", placed as a new top-level sibling binding object `authority_generation_binding`** — not nested inside `authority_binding`, and not a reference.

Rationale (phase prompt §14 "best fits existing canonical-store and contract patterns … not merely for minimal diff"):

1. **The store's established pattern is flat sibling closed binding objects.** HPAC-REQ-098 enumerates the record as `consumption_schema_version` + `record_digest` + eight closed binding objects, each "containing exactly" its field set. A ninth sibling binding object is the exact same shape.
2. **A reference (Option B) does not fit.** `dispatch_binding.containment_evidence_ref` is a reference because the containment evidence is stored elsewhere. The generation snapshot is computed at Gate 9 and has **nowhere else to live** — the data itself must be embedded, so a `*_ref` + `*_digest` pair would dangle.
3. **Keeping it out of `authority_binding` preserves V-4.** `authority_binding` is the subject of the PBRD-001 v2.1 §4 fact-14 representation-equivalence analysis; leaving its closed 12-field set byte-unchanged means the V-4 normalization and the durable-snapshot addition are independent.
4. **Distinct concern.** `authority_binding` commits *authority identity* (approval/proof/projection/presentation/challenge). `authority_generation_binding` commits *the mutable-authority-generation state at the linearization instant* — a different question (RDGO-001 v3.1 §10; `.1R.15.1` §22 forward invariant).

### 4.2 Exact durable schema — `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`

Closed object, exactly six fields (each `*_generation` a non-empty ≤256-char stripped string):

| Field | Meaning | Source at Gate 9 |
|---|---|---|
| `snapshot_schema_version` | const `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0` | fixed |
| `principal_generation` | whole-record canonical digest of the principal registry record | trusted resolver → `resolve_canonical_principal(principal_id).record_digest` |
| `credential_generation` | whole-record canonical digest of the credential registry record | trusted resolver → `resolve_canonical_credential(credential_id).record_digest` |
| `approval_generation` | canonical digest folding the current resolved immutable approval `record_digest` + `approval_id` + a RIHAC-001 §14 forward hook | trusted resolver factory (N-15-3-2, §5) |
| `lifecycle_generation` | digest over every `(sequence, state, event_digest)` of the full hash-chained proof lifecycle chain | `_lifecycle_generation_token(lifecycle_store, proof_id)` |
| `consumption_generation` | consumption-record state at linearization — `"absent"` on the create path (a present/uncertain record short-circuits before create) | `_serialize_consumption_generation(S1["consumption_generation"])` |

The object is the exact `S1` snapshot verified unchanged at `S2` immediately before the create-only linearization — built at step 15 from the step-14a capture, **never rebuilt from post-`S2` state** (phase prompt §22). Every field is a pure function of durable state, restart-reconstructible, carrying no wall clock / mtime / nonce / process identity (`.1R.15.2` §7).

### 4.3 Not a bearer token (phase prompt §16)

`authority_generation_binding` carries no capability field and no identity claim beyond digests. `is_gate9_result` stays provenance-only. Possession or reconstruction of the snapshot grants nothing. A future Gate 10 MUST re-read current canonical generation state and compare it against this durable snapshot; the snapshot is historical/verification evidence, not execution authority.

### 4.4 Consumption-record schema evolution + backward compatibility (phase prompt §17–§18)

- `CONSUMPTION_SCHEMA_VERSION` → `HPAC-AUTHORITY-CONSUMPTION/2.1`. `_TOP_ALLOWED_FIELDS` gains `authority_generation_binding` (11 top-level fields). `new_inert_consumption_record` requires it; `_validate_authority_generation_binding` enforces the closed field set + schema-version const + value shapes. `record_digest` covers it (canonical digest over the full body).
- **`/2.0` policy:** `resolve` still parses a well-formed `/2.0` record as **historical/test data** with `authority_generation_binding is None` — Gate-10-**ineligible** (RDGO-001 v3.1 §10's durable snapshot is absent). Gate 9 writes **only** `/2.1` after `.1R.15.4`. An unknown schema version, or a field set matching neither the `/2.0` nor the `/2.1` closed set, is durability-uncertain → fail closed. One record per `proof_id`, so no mixed store per proof.
- No `/2.0` durable record exists anywhere in the repository (the only consumption-store caller is the test-only Gate-9 coordinator), so migration burden is nil; the `/2.0` read tolerance is defence-in-depth, not a live path.

## 5. N-15-3-2 — production authority-generation resolver completeness (phase prompt §19–§20)

### 5.1 The actual approval revocation / currentness source

**RIHAC-001 v2.0 §14 (frozen; NOT amended by this phase):** the immutable `RuntimeInvocationApproval` has no mutable `revoked` field and v2 defines **no separate approval-revocation store**; "any future explicit early-revocation mechanism must be a separate append-only, digest-bound artifact and requires its own governed contract amendment." Approval revocation is a **transitive** consequence of:

1. **principal / credential revocation** — "a live upstream freshness input … immediately invalidates every unconsumed approval" → `principal_generation` / `credential_generation` (whole-record digests; move on real `revoke_principal` / `revoke_credential`);
2. **proof lifecycle terminal state** (`EXPIRED` / `REVOKED` / `REJECTED`) → `lifecycle_generation` (chain digest over every event);
3. **wall-clock expiry** (`expires_at` vs trusted clock) → evaluated by `validate_approval` at Gate-9 step 9 against the fixed `authority_current_time`;
4. **approval-record removal / quarantine / tamper** → the approval store `load` raises / returns `None`.

The `.1R.15.3` N-15-3-2 finding phrasing ("fold approval-revocation-*store* currentness") presupposes a store that RIHAC-001 §14 says does not exist and cannot be created without a separate contract amendment (out of `.1R.15.4` scope). The in-scope resolution: the production resolver's `approval_generation` commits the **current resolved immutable approval digest** (catches replacement/tamper), fails closed on removal, and carries a **forward hook** for a future §14 artifact.

### 5.2 The production resolver factory

`build_production_authority_generation_resolver(*, principal_registry, principal_id, credential_id, approval_store, approval_id) -> Callable[[], dict]` (new, exported from `runtime_dispatch_gate9`). Each call re-reads canonical durable state only and returns `{principal_generation, credential_generation, approval_generation}`:

- `principal_generation` = `resolve_canonical_principal(principal_id).record_digest`
- `credential_generation` = `resolve_canonical_credential(credential_id).record_digest`
- `approval_generation` = `compute_canonical_digest({"approval_id": …, "approval_record_digest": approval.record_digest, "revocation_artifact_digest": None})`

Raises `_AuthorityGenerationResolverError` (caught by the coordinator's outer `except` → `gate9_internal_error_fail_closed`) if the principal, credential, or approval record is absent or unreadable. No wall clock / mtime / nonce / process identity. It is **not invoked on any production path** (no production Gate-9 caller exists); it is the canonical construction a future caller MUST use, exercised only by tests.

The coordinator body itself still reads **no** approval store (HPAC-REQ-102 — the RIHAC approval store is not mutated by Gate 9; the factory only `load`s it).

### 5.3 Resolver completeness matrix

| Generation token | Canonical inputs | Relevant mutations | Production resolver implementation | Durable representation field | Future Gate-10 re-read source |
|---|---|---|---|---|---|
| principal | `HumanPrincipalRegistry` canonical principal record | revocation (`status active→revoked` + `revoked_at`), disablement, eligibility change, record replacement | `resolve_canonical_principal(principal_id).record_digest` | `authority_generation_binding.principal_generation` | re-resolve the principal record; recompute digest; compare |
| credential | canonical credential record | revocation, replacement, mechanism/public-key/binding change | `resolve_canonical_credential(credential_id).record_digest` | `.credential_generation` | re-resolve; recompute; compare |
| lifecycle / proof | full hash-chained proof lifecycle chain | new successor, terminal `EXPIRED`/`REVOKED`/`REJECTED`, transition, fork (resolver raises → fail closed) | `_lifecycle_generation_token` (digest over every `(sequence,state,event_digest)`) — **subsumes** the proof-state token (HPAC-REQ-094/095) | `.lifecycle_generation` | re-resolve the chain; recompute; compare |
| approval | immutable RIASC approval record (RIHAC-001 §14: no separate revocation store) | record replacement / removal / tamper; transitively principal/credential/lifecycle/expiry (own tokens); future §14 artifact (forward hook) | `compute_canonical_digest({approval_id, approval_record_digest, revocation_artifact_digest:None})`; raise on absent/unreadable | `.approval_generation` | re-load the approval; recompute the same digest; compare; also re-validate all mutable authority (`.1R.15.1` §22 item 6) |
| consumption | `<root>/proofs/v2/<proof_id>/consumption.json` | a record appearing (→ deterministic `already_consumed`, not drift); durability-uncertain (→ fail closed) | `_consumption_generation_token` / `_serialize_consumption_generation` | `.consumption_generation` (`"absent"` at linearization) | re-read the durable record; the record's own `record_digest` is the post-linearization state |

No authority-relevant mutable state is uncovered: every mutation moves some token or fails closed. **Not blocking.**

## 6. Production changes (phase prompt §21, §45)

`git diff --name-only 4d480553 -- src/pcae` (expected, narrow):

- `src/pcae/core/runtime_invocation_authority_consumption.py` — `HPAC-AUTHORITY-CONSUMPTION/2.1`; `authority_generation_binding` closed binding object; `_validate_authority_generation_binding`; version-aware `resolve`; `/2.0` legacy read tolerance.
- `src/pcae/core/runtime_dispatch_gate9.py` — `_authority_generation_binding_fields` / `_serialize_consumption_generation`; `_build_consumption_record` embeds the exact `S1`; `build_production_authority_generation_resolver` factory (N-15-3-2); docstrings updated (`v3.0`→`v3.1`, "eight-item"→"nine-item", deferral note → implemented).

**No Gate 5 / 6 / 7 / 8 production module changed** (`runtime_dispatch_{gate5,permission,gate7,gate8}.py` byte-unchanged; also listed as forbidden files on the phase task). No second lock or transaction mechanism. No Gate-10 symbol. No runtime-adapter / effect code.

## 7. Contract normalization (phase prompt §6–§13, §25)

| Finding | Contract | Edit |
|---|---|---|
| V-2 | RDGO-001 §4 | "Gate 5, not gate 3, creates the final `PROOF_VERIFIED_AND_BOUND` … over the completed approval digest" → a **Sequence-3 creation (v3.1 normalization)** paragraph: the HPAC-001 v2.1 verifier's assurance-independent HPAC-REQ-054 step 10 (`bind_gate5_canonical`) creates it **at gate 3** over the `HPAC-APPROVAL-SUBJECT/2.0` digest; gate 5 does **not** create it, gate 5 read-only **re-confirms** and fails closed on divergence; the assurance decision stays gate 5's. |
| V-2 | RDGO-001 §6 | "It atomically creates HPAC lifecycle sequence 3 … but does not consume …" → "It re-confirms (read-only) the current HPAC lifecycle sequence 3 … created by … HPAC-REQ-054 step 10 (§4) … and does not consume …". |
| V-2/V-3 | RDGO-001 §16 | "Approval" row prose: sequence-3 is **created** at gate 3 (verifier step 10), **re-confirmed** at gate 5, **consumed** at gate 9; new "Authority-generation snapshot (v3.1)" row → item 9. |
| V-3 | RDGO-001 §4 | sequence-3 binds the `HPAC-APPROVAL-SUBJECT/2.0` subject digest, **not** the completed RIASC-001 v3.0 approval `record_digest` (which is carried in the RIHAC-001 v2.0 projection and consumed at gate 9). |
| V-3 | RIASC-001 §9 | non-normative errata note (no version change): `record_digest` and the `HPAC-APPROVAL-SUBJECT/2.0` digest are distinct commitments; sequence 3 does not bind `record_digest`; RDGO-001 v3.1 §4 is corrected. |
| V-3 | HPAC-001 HPAC-REQ-097 | added a cross-reference note: in the verified flow the event is created by the **first** HPAC-REQ-054 run (verifier step 10 at gate 3); gate 5's rerun takes the idempotent-accept path; step 10's wording already covers both. |
| V-4 | PBRD-001 §4 fact 14 + new §4a | the row now points to §4a; §4a adds the normative representation-equivalence clause: the 7 *logical* fields remain the semantic requirement; the closed 3-tuple `(approval_id, approval_record_digest, validation_evidence_digest)` is a permitted equivalent, provided (1) the ID and approval-record digest are direct, (2) every other logical field is committed inside `validation_evidence_digest` OR structurally enforced OR a zero-entropy constant, (3) the request binding is re-enforced by recomputation; two contexts differing in any logical field MUST NOT collapse. |
| V-13-3-1 | RDGO-001 §8 | added a "PB policy ownership (v3.1)" paragraph: PB policy is owned exclusively by gate 6; gates 7/9 revalidate authority currentness + posture only; a stale `policy_version` is resolved by re-entering gate 6; `policy_drift_requires_fresh_pb_re_evaluation` is advisory only; `gate7_pb_decision_stale_policy_version` is a reserved future-shape concern, not a prerequisite. |
| V-13-5-1 | RDGO-001 §9 | added the "Three-layer containment model (v3.1)" paragraph: (a) direct validation, (b) canonical commitment of the complete launch environment (incl. cwd/env bytes, `transport_type=local_cli`) into `containment_evidence_digest`, (c) gate-9 recomputation. The effect plan is coordinator-assembled → no caller cwd/env/transport reference to diff, and none is required. |
| V-15-1 | RDGO-001 §10 | added item 9 (`HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`); replaced the "Immediately before compare-and-create … while holding the protected evidence-store serialization boundary … without a TOCTOU allowance" paragraph with the "Gate-9 linearization semantics (v3.1)" model: the per-`proof_id` create-only primitive **is** the linearization point and sole transaction mechanism (no second lock); revalidation battery → `S1` → record build → `S2` re-read with zero effectful I/O → `S2 != S1` fails closed; a residual instruction-level micro-window is the acknowledged practical limit, no external effect. §10's "eight items" → "nine items"; `/2.0` → `/2.1`; `/2.0` records readable historical/test data but gate-10-ineligible. |
| V-15-1 | RDGO-001 §11 | added "Gate-10 forward read-back prerequisite (v3.1 — prerequisite semantics only; no gate-10 design, no phase ID)": the six-item list (`is_gate9_result` + `status=="consumed"` + durable `consumption.json`/`HPAC-AUTHORITY-CONSUMPTION/2.1` re-read with `authority_generation_binding` present/valid + exact lineage + runtime capability eligible + re-validation of all mutable authority *and* re-derivation of the current generation vector vs the durable snapshot). "data, not a bearer token." |
| V-15-1 | RDGO-001 §21 | added the "v3.1 normalization … MINOR" verdict paragraph + "Durable-before-effect items: 9 (v3.1)". Header supersedes v3.0-narration of sequence-3 creation. |
| V-15-1 / durable | HPAC-001 §41 | HPAC-REQ-098: `HPAC-AUTHORITY-CONSUMPTION/2.1`, nine closed binding objects (eight `/2.0` byte-unchanged + `authority_generation_binding`); new HPAC-REQ-098a defines the closed 6-field `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0` (schema-version const + 5 markers over durable state), the exact `S1` verified at `S2`, restart-reconstructible, verification evidence not authority; HPAC-REQ-099 rewritten to the create-only-linearization + zero-I/O `S1`/`S2` model with the residual-micro-window disclosure. §37 + §44: v2.1 MINOR verdict. |
| V-13-3-2 | RE No-Go Registry | schema 1.0 → 1.1: additive "Enforcement class" column classifying all 17 entries (per-decision 001–008/010/011; environmental-readiness 009/013/015/016/017; advisory 012/014) + a scoping paragraph (`matched_no_go_ids` projects only the per-decision subset; gate-7 progression depends on the authoritative decision, not projection completeness; "sole source" → "sole source *for the per-decision projection*"). |
| cross-refs | RIHAC-001 | "Related contracts" line and the §16 step-7 reference refreshed to RDGO-001 v3.1 / PBRD-001 v2.1 / HPAC-001 v2.1; §23 freeze-verdict note added (no semantic change, no bump; §14 append-only revocation-artifact boundary confirmed — the gate-9 `approval_generation` marker carries only a `null` forward hook for it, N-15-3-2). |
| cross-refs | RDGO/PBRD | remaining in-contract `RDGO-001 v3.0` / `HPAC-001 v2.0` prose references in §4/§12/§14 refreshed to v3.1 / v2.1. |

**Repository-wide cross-reference scope (phase prompt §25, §43).** The
active contract set (RDGO / PBRD / HPAC / RIASC / RIHAC / RE-registry) is
updated. Historical phase documents that cite `RDGO-001 v3.0` etc. **as the
version-at-the-time** are accurate historical records and are **not**
rewritten (phase prompt §26); only the five phase documents `.1R.15.1` §11
named receive errata annotations (§8). `git grep 'RDGO-001 v3.0'` /
`'HPAC-AUTHORITY-CONSUMPTION/2.0'` across `docs/` returns only historical
verdict prose and the deliberate `/2.0` legacy-compat references.

## 8. Phase-document errata (phase prompt §26)

Added as clearly-labelled `> **Erratum — Phase …1R.15.4 …**` blocks
(original text preserved; historical verdicts intact):

- **`.1R.9` §12** — "Inside the protected Gate-9 serialization boundary" = the create-only-primitive window; no held lock.
- **`.1R.9` §13.5** — the "Lock scope / Lock ordering: single lock … acquired before the §12 battery" bullet is **internally contradicted** by the "Do not invent a new lock … SHALL NOT introduce a second transaction mechanism" bullet; V-15-1; the second bullet + §18 are the correct frozen model; RDGO-001 v3.1 §10 / HPAC-001 v2.1 HPAC-REQ-099 are the normalized statement.
- **`.1R.13.1` §11.2** — the `gate8_transport_drift` row is **STRUCK** (transport is a fixed const); the `gate8_cwd_drift` / `gate8_environment_allowlist_drift` rows are **reworded** to repo-scope containment + digest commitment + gate-9 recomputation (RDGO-001 v3.1 §9); the other six rows stand.
- **`.1R.13.1` §13 / §19.1** — "sole" Gate-7 no-go source → "sole source *for the per-decision projection*" (RE-registry schema 1.1).
- **`.1R.13.1` §16.2 invariant 4** — "while holding the protected serialization boundary" normalized: no held lock; battery + zero-I/O `S1`/`S2` re-check before the create.
- **`.1R.13.2`** — "PB-policy drift is covered transitively via projection revalidation" **overstates** `revalidate_validated_authority_projection` (it does not re-read live PB policy; policy drift is advisory-only and resolved by re-entering gate 6). V-13-3-1.
- **`.1R.14` / `.1R.15`** — top-of-document errata: RDGO-001 v3.0 → v3.1, `HPAC-AUTHORITY-CONSUMPTION/2.0` (eight objects) → `/2.1` (nine objects), "while holding the protected serialization boundary" → create-only-linearization + zero-I/O `S1`/`S2`. Both phase verdicts (IMPLEMENTED; GATE-9 CLOSED) stand.

## 9. Contract evolution manifest (phase prompt §41)

| Artifact | Old version / identity | New version / identity | Finding(s) | Semantic or errata | Dependent references updated |
|---|---|---|---|---|---|
| `RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md` (RDGO-001) | v3.0 | **v3.1** | V-2, V-3, V-13-3-1, V-13-5-1, V-15-1 | clarification (MINOR) — re-states verified behaviour; item 8→9; no gate reorder / boundary move / merge | PBRD-001, HPAC-001, RIASC-001, RIHAC-001; `.1R.9` / `.1R.13.1` / `.1R.13.2` / `.1R.14` / `.1R.15` errata |
| `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md` (PBRD-001) | v2.0 | **v2.1** | V-4 | additive representation-equivalence clause (MINOR) — 7 logical fields + precedence unchanged | RIHAC-001 (projection payload); RDGO-001 §16 |
| `HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md` (HPAC-001) | v2.0 | **v2.1** | V-15-1, durable snapshot | additive verification-evidence binding object (MINOR) — no authority widened | RDGO-001; RIASC-001; RIHAC-001 |
| `HPAC-AUTHORITY-CONSUMPTION` record schema | `/2.0` | **`/2.1`** | V-15-1 | additive closed binding object; `/2.0` readable historical/test data, gate-10-ineligible | `runtime_invocation_authority_consumption.py`; `runtime_dispatch_gate9.py`; test suites |
| `HPAC-AUTHORITY-GENERATION-SNAPSHOT` schema | — | **`/1.0`** (new) | V-15-1 | new closed 6-field schema (verification evidence) | HPAC-001 §41 |
| `RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md` (RIASC-001) | v3.0 | **v3.0 + §9 errata note** | V-3 | non-normative cross-reference clarification (no bump) | HPAC-001 cross-refs → v2.1 |
| `RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` | schema 1.0 | **schema 1.1** | V-13-3-2 | additive classification column + scoping paragraph (no ID / verdict / statement changed) | `.1R.13.1` §13 errata |
| `RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md` (RIHAC-001) | v2.0 | **v2.0** (unchanged) | N-15-3-2 boundary | cross-reference refresh + §23 note; §14 boundary confirmed, not amended | RDGO-001 v3.1 / PBRD-001 v2.1 / HPAC-001 v2.1 |

**Contract identity after normalization (phase prompt §44).** Final canonical
`sha256` digests are recorded in the fixed-SHA-pinned byte-identity test
suites (`test_runtime_authority_production_repair_3w1r2b1r1117.py`,
`test_gate5_…_1r11.py`, `test_trusted_approval_…_111r.py`). No unplanned
contract file changed: `git diff --name-only 1babaa95 HEAD -- docs/contracts
docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md` = exactly the five contracts +
the registry above.

## 10. Tests (phase prompt §28–§34)

New suite `tests/test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4.py`
— **36 tests, 0 failed**:

- **§28 contract traceability** — the normalized RDGO/PBRD/HPAC/RIASC/RE-registry
  wording matches the verified architecture for V-2/V-3/V-4/V-13-3-1/V-13-3-2/V-13-5-1/V-15-1,
  and the phase-document errata are present; the coordinator's `S1`→build→`S2`→create
  source order matches HPAC-REQ-099.
- **§29 durable schema** — `CONSUMPTION_SCHEMA_VERSION == /2.1`; the record has nine
  binding objects; `authority_generation_binding` is the closed 6-field set; malformed
  schema-version / blank / oversized / non-string / extra / missing-field values are
  rejected (`HPACMalformedError`); `record_digest` covers the object; `/2.0` record is
  readable with `authority_generation_binding is None` (gate-10-ineligible); an unknown
  schema version is durability-uncertain.
- **§30 N-15-3-2 resolver completeness** — `build_production_authority_generation_resolver`
  returns the three keys from canonical registry/approval state; `approval_generation`
  moves on approval-record replacement; the resolver fails closed on an absent/unreadable
  principal/credential/approval; no wall clock / mtime / nonce / uuid in the `_resolve`
  body; the RIHAC-001 §14 forward hook (`revocation_artifact_digest`) is present and the
  §14 boundary is confirmed unamended; a real `revoke_principal` moves `principal_generation`.
- **§20 completeness matrix** — the phase-doc §5.3 matrix covers all five generation
  tokens; the coordinator's snapshot = 3 resolver keys + lifecycle + consumption.
- **§31 durable write / restart / read-back** — a bounded synthetic gate-9 consumption
  writes a `/2.1` record whose `authority_generation_binding` equals the `S1` the resolver
  + stores produced (four tokens; `consumption_generation == "absent"`); a fresh store
  object over the same on-disk tree reconstructs the record and it round-trips to the same
  `record_digest`.
- **§32 post-consumption drift** — after consumption, revoking the principal leaves the
  durable record byte-identical while the current principal generation now differs from
  the persisted snapshot.
- **§33 not a bearer token** — no capability/authority field name in the object; a
  deep-copied snapshot dict and a fabricated record carrying it are rejected by
  `is_gate9_result`; the contracts say "verification evidence, not execution authority" /
  "data, not a bearer token".
- **§34 Gate9Result forward semantics** — `is_gate9_result` provenance-only (`status ==
  "consumed"` is the success signal); `__reduce__` raises; a copy is not provenanced;
  RDGO-001 v3.1 §11 enumerates six additional gate-10 requirements (necessary-not-sufficient).

Existing gate9 + consumption suites (`.1R.14` / `.1R.15` / `.1R.15.2` / `.1R.15.3` /
`test_hpac_authority_consumption`) updated for the schema evolution — **all green** — with
the `.1R.15.3` phase-scoped no-change assertions superseded (approval-generation is now
resolver-*wired*; the durable snapshot is now *implemented*) and the `.1R.15.2`/`.1R.15.3`
scope-fence tests pinned to the `.1R.15.3` end SHA `4d480553` so they remain permanent
window checks. `.1R.15.3` §35 critical properties (S1/S2 ordering, drift rejection,
one-shot, replay, concurrency, crash-before/after, restart, V-13-5-1 containment read-back)
re-run unchanged (56/56).

## 11. Fixed-SHA A/B regression attribution (phase prompt §42)

**Immutable baseline:** `4d480553` (`.1R.15.3` final; pre-`.1R.15.4`). **Method:**
dedicated `git worktree` at `4d480553`; deterministic `-p no:randomly`; **no xdist**.
**Targeted set** (36 files): the new `.1R.15.4` suite + Gate-9 `.1R.14` / `.1R.15` /
`.1R.15.2` / `.1R.15.3` + consumption store + HPAC verifier / lifecycle / foundation +
Gate 5–8 integration & verification + B1/B7/N1/N2 + runtime-authority/PB + the `3V.1` /
`3V.1R.1` / `3V.1R` contract-verification suites + the two cross-contract freeze
verification suites + attempt-idempotency.

| | baseline `4d480553` | HEAD | delta |
|---|---|---|---|
| targeted set (35 pre-existing files) | 1339 passed / **60 failed** | 1339 passed / **60 failed** | **0** |
| new `.1R.15.4` suite | — | 36 passed | +36 (new) |

**CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0.**
**UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.**

The 60 baseline=HEAD failures are all pre-existing and unrelated to `.1R.15.4`:
the `3V.1` / `3V.1R.1` / `3V.1R` suites pin RDGO to v2.0 / PBRD to v1.1 / RIHAC to
v1.0 (stale since the `.1R` v3/v2 freeze, many phases before this one); HPAC-foundation
`blocking_reproduction_*` fixtures; a HATP contract-byte identity test; and the
`_GATE5_RESULTS` / `_GATE6_DECISIONS` xdist cross-file-pollution flakes documented by
`.1R.15` §26 / `.1R.15.2` §10.

**Intended contract-byte / production-scope test changes (phase prompt §42 —
classified explicitly).** 24 byte-identity / "only file X changed since baseline"
assertions from `.1R.10` → `.1R.15.3` would trip on the authorized `.1R.15.4`
contract normalization + `runtime_invocation_authority_consumption.py` schema
evolution. Each is a `git diff <that phase's baseline> HEAD -- docs/contracts src/pcae`
scope-fence; each was **repinned to the fixed end SHA `4d480553`** (the end of the
`.1R.15.3` window — a permanent historical fact) so it remains a live guard against
*unauthorized* drift within its own window. Files touched (test-only, one-line endpoint
pins + phase-authorization comments): `test_gate5_…_1r10`, `test_gate5_…_1r11`,
`test_gate6_…_1r12`, `test_gate6_…_1r13`, `test_gate7_…_1r13_2`, `test_gate7_…_1r13_3`,
`test_gate8_…_1r13_4`, `test_gate8_…_1r13_5`, `test_gate9_…_1r14`, `test_gate9_…_1r15`,
`test_gate9_…_1r15_3`, `test_b1_b7_n1_n2_…_1r8`, `test_runtime_authority_production_repair_3w1r2b1r1117`,
`test_trusted_approval_…_111r`, `test_trusted_approval_…_111r1`. The `3V.1` /
`3V.1R.1` cardinality tests (`…_eight_durable_items…` / `…durable_items_still_eight`)
were updated to expect **nine** (item 9 added). The two cross-contract freeze suites'
version-graph tests were updated to `v3.1` / `v2.1` / `v2.1`. Contract-hash pins in
`_1117` / `_1r11` / `_111r` were recomputed to the normalized bytes.

## 12. Runtime zero-effect proof (phase prompt §46)

Over the `.1R.15.4` + Gate-9 suites at completion:

```
canonical local test-store writes = expected (tmp_path stores only; 0 under the repo tree)
runtime subprocess    = 0   (test infrastructure: git subprocess in scope-fence assertions, disclosed)
adapter invocation    = 0
provider / network    = 0
credential operations = 0
hardware operations   = 0
Gate-10 effects       = 0
```

`pcae runtime inspect` at finalization: `not_implemented / Observed / observe /
unavailable`; 0 plugins / 0 capabilities; PB `execution_unavailable`; non-executing —
unchanged. No `runtime_dispatch_gate10.py`; no `DispatchReceipt`, adapter, subprocess,
socket, provider, credential, or hardware symbol in `runtime_dispatch_gate9.py`. POL-005
byte-unchanged.

## 13. Historical finding disposition (phase prompt §27)

| Finding | Disposition |
|---|---|
| V-2 | NORMALIZED (RDGO-001 v3.1 §4/§6/§16) |
| V-3 | NORMALIZED (RDGO-001 v3.1 §4; RIASC-001 errata note) |
| V-4 | NORMALIZED (PBRD-001 v2.1 §4 fact 14 representation-equivalence clause) |
| V-13-3-1 | NORMALIZED (RDGO-001 v3.1 §8 clarifying sentence; `.1R.13.2` prose erratum) |
| V-13-3-2 | NORMALIZED (RE No-Go Registry schema 1.1 classification) |
| V-13-5-1 | NORMALIZED (RDGO-001 v3.1 §9 three-layer model; `.1R.13.1` §11.2/§25 erratum) |
| V-15-1 | NORMALIZED after independently verified production repair (RDGO-001 v3.1 §10; `.1R.9` §13.5 / `.1R.13.1` §16.2 errata) + durable representation (HPAC-001 v2.1 §41) |
| N-15-3-2 | IMPLEMENTED / NORMALIZED (production resolver factory; §5) |
| V-15-2 / V-15-3 | already independently CLOSED (`.1R.15.3`); no further production work; history preserved |

## 14. `.3` governance incident

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved unchanged. No delegated worker committed, finalized, or pushed in this phase. Only the primary human-authorized operator holds `.1R.15.4` lifecycle authority.

## 15. Gate-10 prerequisite re-evaluation (phase prompt §48; `.1R.15.1` §20)

| # | Prerequisite | Status after `.1R.15.4` |
|---|---|---|
| 1 | Contract model internally consistent — RDGO v3.1 + PBRD v2.1 + RIASC errata + RE-registry 1.1 published **and independently verified** | RDGO v3.1 / PBRD v2.1 / HPAC v2.1 / RIASC errata / RE 1.1 **published**; the `.1R.15.4` §7/§9 self-consistency check ("one clarification does not create another contradiction") passes; **independent verification (`.1R.15.5`) NOT yet done → NOT satisfied** |
| 2 | V-15-1 resolved (`.1R.15.2` + `.1R.15.3` closed VERIFIED) | **satisfied** (`.1R.15.3` closed VERIFIED) + durable representation now added |
| 3 | Gate-9 semantics normalized (RDGO §10 / `.1R.13.1` §16.2 / `.1R.9` §12/§13.5) | **satisfied** (RDGO v3.1 §10 + the three errata) |
| 4 | Runtime-capability model frozen (`not_implemented / Observed / observe / unavailable`; the snapshot shape Gate 9 checks == the one Gate 10 must re-check) | **satisfied / unchanged** — RDGO v3.1 §11 item 5 states it |
| 5 | Real human-authority status accurately NON_REAL (no FIDO2/WebAuthn/CTAP, no protected UI) | **satisfied / unchanged** — no contract implies otherwise |
| 6 | `Gate9Result` success semantics frozen (`is_gate9_result` = provenance; `status=="consumed"` = success) | **satisfied** — RDGO v3.1 §11 item 2; `.1R.15.4` suite §34 |
| 7 | Durable consumption read-back + re-validation forward invariant frozen | **satisfied** — RDGO v3.1 §11 (six items) + item 9 durable snapshot; `.1R.15.1` §22 carried in |
| 8 | No unresolved blocking findings from `.1R.15.2`–`.1R.15.5` | `.1R.15.2`/`.1R.15.3` = none; `.1R.15.4` = none (this phase); **`.1R.15.5` NOT yet run → NOT satisfied** |
| 9 | The two 3S.2.1 prerequisite repairs at their required reachability point | tracked separately (PBRD-001 §12 items 9–10); **not this phase's scope**; unchanged |
| 10 | Independent verification of the contract normalization (`.1R.15.5`) | **NOT satisfied** — `.1R.15.5` not begun |

Items 1, 8, 10 are **not** satisfied until `.1R.15.5` closes VERIFIED. **Gate 10 keeps NO phase ID.** Do not invent one.

## 16. Historical finding disposition (phase prompt §27) — see §13

## 17. New findings

- **No new blocking findings.**
- **N-15-4-1 (INFO).** `runtime_invocation_authority_consumption.RuntimeInvocationAuthorityConsumption.authority_generation_binding` is an `Optional[dict]` defaulting to `None`, populated on every `/2.1` record and `None` only for a parsed legacy `/2.0` record. No `/2.0` durable record exists anywhere in the repository (the only consumption-store caller is the test-only Gate-9 coordinator), so the `/2.0` read path is defence-in-depth, exercised only by `test_legacy_2_0_record_is_readable_but_gate10_ineligible`. A future phase MAY drop `/2.0` read tolerance once `.1R.15.5` confirms nothing depends on it; not a prerequisite.
- **N-15-2-1 / N-15-2-2** (carried from `.1R.15.2`): N-15-2-1 (shared principal/credential registry document → `principal_generation` also moves on a pure credential revocation; fail-safe) — confirmed still correct. N-15-2-2 (durable snapshot needs a schema change) — **RESOLVED by this phase**.
- **N-15-3-1** (INFO, from `.1R.15.3`) — `.1R.15.2`'s `test_snapshot_has_exactly_the_six_generation_tokens` name overstates its five-token body; unchanged, harmless.

## 18. Implementation verdict (phase prompt §47)

**RUNTIME-DISPATCH CONTRACT NORMALIZATION: IMPLEMENTED — INDEPENDENT VERIFICATION PENDING.**
**DURABLE GATE-10 GENERATION-SNAPSHOT REPRESENTATION: IMPLEMENTED — INDEPENDENT VERIFICATION PENDING.**
**N-15-3-2 APPROVAL-GENERATION COMPLETENESS: IMPLEMENTED — INDEPENDENT VERIFICATION PENDING.**

No self-close. V-2 / V-3 / V-4 / V-13-3-1 / V-13-3-2 / V-13-5-1 / V-15-1 are NORMALIZED and N-15-3-2 IMPLEMENTED subject to `.1R.15.5` independent verification. V-15-2 / V-15-3 remain independently CLOSED (`.1R.15.3`); no further work; history preserved.

## 19. Recommended next phase (phase prompt §49)

**`149O.20L.7O.3W.1R.2B.1R.1.1R.15.5` — Independent Verification of the Runtime-Dispatch Contract Normalization.** Not begun. Requires its own separate explicit human authorization; this phase grants none. It must RE-DERIVE every published delta against the verified implementation and the other contracts, confirm each clarification codifies verified behaviour and introduces no new contradiction, re-run the `.1R.15.1` §18 consistency checks, and confirm the `.1R.15.1` §20 Gate-10 prerequisite list (items 1–8). Its verdict gates whether Gate 10 may be assigned an ID. **Do not begin `.1R.15.5`. Do not plan or implement Gate 10. Do not enable execution.**

---

## 20. REQUIRED FINAL REPORT (phase prompt §54)

**Phase ID / title.** 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4 — Runtime-Dispatch Contract Normalization Implementation.

**Phase-entry SHA.** `1babaa95` (governed task-open commit). Immutable A/B baseline `4d480553` (`.1R.15.3` final).

**Sources / contracts inspected.** RDGO-001 v3.0, PBRD-001 v2.0, RIHAC-001 v2.0, RIASC-001 v3.0, HPAC-001 v2.0, RE No-Go Registry schema 1.0 — read in full at their frozen text. Phase docs `.1R.15.1` (blueprint, 1469 lines), `.1R.15.2`, `.1R.15.3`, `.1R.9` §12/§13.5/§18, `.1R.13.1` §11.2/§13/§16.2, `.1R.14`, `.1R.15`. Production source line-by-line: `runtime_dispatch_gate9.py`, `runtime_invocation_authority_consumption.py`, `runtime_dispatch_gate5.py`, `hpac_verifier.py` (`bind_gate5_canonical`), `runtime_invocation_approval_store.py`, `human_principal_registry.py`.

**Versioning adjudication.** RDGO-001 **v3.0 → v3.1 (MINOR)**; PBRD-001 **v2.0 → v2.1 (MINOR)**; HPAC-001 **v2.0 → v2.1 (MINOR)**; `HPAC-AUTHORITY-CONSUMPTION` **/2.0 → /2.1**; `HPAC-AUTHORITY-GENERATION-SNAPSHOT` **/1.0 (new)**; RIASC-001 **v3.0 + §9 errata (no bump)**; RE No-Go Registry **schema 1.0 → 1.1**; RIHAC-001 **v2.0 (unchanged; cross-refs refreshed)**. Both `.1R.15.1` MAJOR-candidate judgment calls — RDGO sequence-3-creation narration, PBRD closed-shape — adjudicated **MINOR** (§3): neither alters external trust semantics, the required authority shape, or consumption-record compatibility fundamentally.

**RDGO old/new version.** v3.0 → **v3.1**. **PBRD old/new version.** v2.0 → **v2.1**. **HPAC schema/version adjudication.** HPAC-001 v2.0 → **v2.1** (additive verification-evidence binding object, no authority widened — §37 MINOR bar met); `HPAC-AUTHORITY-CONSUMPTION/2.1`; `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0` new. **RIASC errata.** §9 non-normative note (V-3), no version change. **RE No-Go schema change.** 1.0 → **1.1** — additive "Enforcement class" column + scoping paragraph; no ID / verdict / canonical statement changed.

**V-2 normalization.** RDGO-001 v3.1 §4/§6/§16 — the HPAC-001 v2.1 verifier's HPAC-REQ-054 step 10 creates sequence 3 at gate 3; gate 5 read-only re-confirms; assurance decision stays gate 5's; HPAC-REQ-097 cross-reference note added.

**V-3 normalization.** RDGO-001 v3.1 §4 — sequence 3 binds the `HPAC-APPROVAL-SUBJECT/2.0` subject digest, not the completed approval `record_digest`; RIASC-001 §9 errata note distinguishing the two commitments.

**V-4 normalization.** PBRD-001 v2.1 §4a representation-equivalence clause — the 7 logical `human_authority_binding` fields remain the semantic requirement; the closed 3-tuple `(approval_id, approval_record_digest, validation_evidence_digest)` is a permitted equivalent under three provisos; no distinguishable collision.

**V-13-3-1 normalization.** RDGO-001 v3.1 §8 "PB policy ownership" paragraph — gate 6 owns PB policy; gates 7/9 revalidate authority currentness + posture only; stale `policy_version` → re-enter gate 6; `.1R.13.2` prose erratum.

**V-13-3-2 normalization.** RE No-Go Registry schema 1.1 — per-decision (001–008, 010, 011) / environmental-readiness (009, 013, 015, 016, 017) / advisory (012, 014); `matched_no_go_ids` projects only the per-decision subset; `.1R.13.1` §13 erratum.

**V-13-5-1 normalization.** RDGO-001 v3.1 §9 three-layer model — (a) direct validation, (b) canonical commitment of the complete launch environment into `containment_evidence_digest`, (c) gate-9 recomputation; effect plan is coordinator-assembled so no caller cwd/env/transport reference to diff; `.1R.13.1` §11.2 erratum (strike `gate8_transport_drift`, reword cwd/env rows).

**V-15-1 normalization.** RDGO-001 v3.1 §10 create-only-linearization + zero-effectful-I/O `S1`/`S2` authority-generation-token re-check model; no held lock; residual instruction-level micro-window disclosed; item 8 → 9; HPAC-001 v2.1 HPAC-REQ-098/098a/099; `.1R.9` §12/§13.5 + `.1R.13.1` §16.2 errata.

**Selected durable generation-snapshot architecture (§4).** Option A's "dedicated typed/closed object", placed as a **new top-level closed binding object `authority_generation_binding`** (a ninth sibling of the existing eight) — not nested in `authority_binding`, not a reference. Rationale: the store's established pattern is flat sibling closed binding objects; a *reference* does not fit (the snapshot is computed at gate 9 and has nowhere else to live); keeping it out of `authority_binding` preserves the V-4 analysis; it is a distinct concern (mutable-generation state vs authority identity).

**Exact durable schema.** `HPAC-AUTHORITY-GENERATION-SNAPSHOT/1.0`, closed 6 fields: `snapshot_schema_version` (const) + `principal_generation` / `credential_generation` / `approval_generation` / `lifecycle_generation` / `consumption_generation` (each a non-empty ≤256-char stripped digest/marker over durable state; `consumption_generation == "absent"` on the create path). The committed object is the exact `S1` verified unchanged at `S2`, built at step 15 from the step-14a capture, never rebuilt from post-`S2` state.

**Backward-compatibility policy (§18).** Gate 9 writes only `/2.1`. `resolve` parses a well-formed `/2.0` record as historical/test data with `authority_generation_binding is None` — **gate-10-ineligible**. An unknown schema version, or a field set matching neither closed set, is durability-uncertain → fail closed. No `/2.0` durable record exists in the repository; the `/2.0` read path is defence-in-depth.

**N-15-3-2 production resolver implementation (§5).** `build_production_authority_generation_resolver(*, principal_registry, principal_id, credential_id, approval_store, approval_id)` (new, exported from `runtime_dispatch_gate9`). `principal_generation` / `credential_generation` = `resolve_canonical_{principal,credential}(...).record_digest`; `approval_generation` = `compute_canonical_digest({approval_id, approval_record_digest, revocation_artifact_digest: None})` — folds the current resolved immutable approval digest (catches replacement/tamper), fails closed on absent/unreadable, carries a `null` forward hook for a future RIHAC-001 v2.0 §14 append-only revocation artifact. RIHAC-001 v2.0 §14 (frozen; **NOT amended**): no separate approval-revocation store; approval revocation is transitively principal/credential/lifecycle/expiry. Not invoked on any production path (no production Gate-9 caller); the coordinator body itself reads no approval store (HPAC-REQ-102).

**Resolver completeness matrix.** §5.3 — principal / credential / lifecycle-proof / approval / consumption; every authority-relevant mutation moves a token or fails closed; **not blocking**.

**Gate-9 S1/S2 regression.** `.1R.15.3` §35 critical properties re-run unchanged (56/56): S1 after the full battery; S2 the last authority read before create; zero effectful I/O between the `S2 == S1` decision and `create`; drift injection (principal / credential / lifecycle / approval / multi) → `gate9_authority_generation_drift:*`, 0 `consumption.json`; consumption record appearing → deterministic `already_consumed`; stable → exactly one `consumed`; concurrency one-winner; crash-before/after; restart.

**Durable write / read-back test.** `test_gate9_consumption_durably_commits_the_exact_s1_snapshot` + `test_restart_reconstructs_the_snapshot_purely_from_the_durable_record` — a bounded synthetic gate-9 consumption writes a `/2.1` record whose four `*_generation` markers equal the resolver+store `S1`; a fresh store object over the same tree reconstructs it and it round-trips to the same `record_digest`.

**Post-consumption drift tests.** `test_post_consumption_authority_mutation_leaves_the_record_intact` — after consumption, `revoke_principal` leaves the durable record byte-identical while the current principal generation now differs from the persisted snapshot (the future Gate-10 prerequisite semantics, no dispatch).

**Gate9Result forward semantics.** Unchanged — `is_gate9_result` provenance-only; `status == "consumed"` is the success signal; `__reduce__` raises; RDGO-001 v3.1 §11 enumerates six additional gate-10 requirements (necessary-not-sufficient).

**Gate-10 prerequisite wording.** RDGO-001 v3.1 §11 — prerequisite semantics only; no gate-10 module / symbol / plan / phase ID.

**Phase-document errata.** §8 — `.1R.9` §12/§13.5, `.1R.13.1` §11.2/§13/§16.2, `.1R.13.2`, `.1R.14`, `.1R.15`. Originals preserved; historical verdicts intact.

**Cross-reference updates.** §7 last paragraph + §9 manifest. Active contract set updated; historical phase docs citing the version-at-the-time NOT rewritten.

**Contract evolution manifest.** §9.

**Production files changed.** `src/pcae/core/runtime_invocation_authority_consumption.py` (`/2.1` schema + `authority_generation_binding` + `_validate_authority_generation_binding` + version-aware `resolve`); `src/pcae/core/runtime_dispatch_gate9.py` (`_authority_generation_binding_fields` / `_serialize_consumption_generation`; `_build_consumption_record` embeds the exact `S1`; `build_production_authority_generation_resolver` + `_AuthorityGenerationResolverError`; docstrings). `git diff --name-only 1babaa95 HEAD -- src/pcae` = exactly these two. **No Gate 5 / 6 / 7 / 8 production module changed** (forbidden files; byte-unchanged). No second lock. No Gate-10 symbol. No runtime-adapter / effect code. POL-005 byte-unchanged.

**Contract files changed.** `RUNTIME_DISPATCH_GATE_ORDERING_CONTRACT.md`, `PB_RUNTIME_DISPATCH_EXTENSION_CONTRACT.md`, `HUMAN_PRINCIPAL_AUTHENTICATION_CONTRACT.md`, `RUNTIME_INVOCATION_APPROVAL_SCHEMA_CONTRACT.md`, `RUNTIME_INVOCATION_HUMAN_AUTHORITY_CONTRACT.md`, `docs/RUNTIME_ENFORCEMENT_NO_GO_REGISTRY.md`. No unplanned contract file changed.

**Contract / reference tests.** New suite `test_runtime_dispatch_contract_normalization_3w1r2b1r1_1r15_4.py` — 36/36.

**Gate-5/6/7/8 regressions.** All CLOSED / green — `.1R.10`–`.1R.13.5` integration + verification suites, 337 + 262 passed in the confirmation runs; their production modules byte-unchanged (contract-reference constants required no in-module change).

**Gate-9 regressions.** `.1R.14` (63) / `.1R.15` (76) / `.1R.15.2` (44) / `.1R.15.3` (56) all green after the schema evolution.

**Fixed-SHA A/B.** §11 — baseline `4d480553`, no xdist, 36-file targeted set: **0 new failures**; 60 pre-existing = at baseline and HEAD; +36 new passing.

**Candidate-only regression count.** **CANDIDATE-ONLY UNEXPLAINED FUNCTIONAL NONPASSING NODES = 0; UNEXPLAINED ATTRIBUTABLE FUNCTIONAL REGRESSIONS = 0.** 24 intended contract-byte / production-scope test changes classified and repinned (§11).

**Runtime / no-effect proof.** §12 — 0 subprocess / adapter / provider / network / credential / hardware / Gate-10 effect (test git subprocesses disclosed).

**Runtime state.** `not_implemented / Observed / observe / unavailable` — unchanged.

**Gate 10 still absent.** No module, symbol, plan, phase ID. §15 items 1, 8, 10 NOT satisfied until `.1R.15.5`.

**All new findings.** §17 — no new blocking; N-15-4-1 (INFO, `/2.0` read tolerance); N-15-2-2 RESOLVED; N-15-2-1 / N-15-3-1 carried, confirmed.

**Implementation verdict.** §18 — IMPLEMENTED — INDEPENDENT VERIFICATION PENDING (×3). No self-close.

**`.3` governance incident status.** `DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved unchanged.

**Commits.** `1babaa95` (task open), `8232a164` (`/2.1` schema + N-15-3-2 factory + gate9 tests), `145ab1dd` (contract normalization), `f1135ad4` (phase-document errata + traceability suite + scope-fence repins), plus the governed finalization commits.

**Pushed status / `origin/main..HEAD`.** Recorded in `.pcae/phase-completion-metadata.json` `phase_commits` after governed finalization; `pushed_status: pushed`; `origin/main..HEAD = 0` after the governed push.

**Exact `.1R.15.5` recommendation.** §19 — `149O.20L.7O.3W.1R.2B.1R.1.1R.15.5` — Independent Verification of the Runtime-Dispatch Contract Normalization. Not begun. Requires its own separate explicit human authorization.

---

## No-Go Confirmations

- No `src/pcae` file changed beyond `runtime_dispatch_gate9.py` + `runtime_invocation_authority_consumption.py`; Gate 5/6/7/8 production modules byte-unchanged; no runtime-adapter / effect / Gate-10 code.
- No second global lock, advisory-lock object, or transaction system; the per-`proof_id` create-only primitive remains the sole linearization point.
- No Gate-10 module, symbol, `DispatchReceipt`, adapter dispatch, subprocess, provider/network, credential, or hardware path; Gate 10 keeps no phase ID.
- No execution enabled; runtime remains `not_implemented / Observed / observe / unavailable`; no capability/plugin registered; POL-005 byte-unchanged.
- No real FIDO2 / WebAuthn / CTAP / protected approval UI / physical authenticator access; deterministic authentication remains NON_REAL.
- No approval / proof / presentation / challenge / nonce consumed on any production path; no `consumption.json` created outside disposable `tmp_path` test stores.
- No third-party system, unrelated account, external credential, provider API, external network, or deployment target accessed.
- No test weakened to pass; the concurrency-loser / drift-rejection / one-shot guarantees are intact; expected contract-byte test changes are classified explicitly (§11).
- No raw `git commit` / `git push`, no `--no-verify`, no force push, no history rewrite, no hook bypass — governed `pcae` lifecycle only.
- No delegated worker committed, finalized, or pushed; only the primary human-authorized operator holds `.1R.15.4` lifecycle authority.
- No begin of `.1R.15.5`; it requires its own separate explicit human authorization.
- No MAJOR contract version forced; both `.1R.15.1` MAJOR-candidate calls adjudicated MINOR with primary-source justification.
- No unplanned contract file changed; RPAC-001, PBPA-001, POL-005 byte-unchanged.
- No reopening of a closed gate boundary (Gate 5 / 6 / 7 / 8 / 9); their production modules are byte-unchanged.
- No self-close of any finding; V-2 / V-3 / V-4 / V-13-3-1 / V-13-3-2 / V-13-5-1 / V-15-1 NORMALIZED and N-15-3-2 IMPLEMENTED subject to `.1R.15.5`.
- No authorization of the historical delegated `.3` finalization, commit, or push; it remains UNAUTHORIZED.
- No Gate-10 design beyond the RDGO-001 v3.1 §11 prerequisite-only wording and the `.1R.15.1` §22 forward invariant.

---
*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4.*

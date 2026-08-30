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

(authored below as each contract edit lands)

## 8. Phase-document errata (phase prompt §26)

(authored below)

## 9. Contract evolution manifest (phase prompt §41)

(authored below)

## 10. Tests (phase prompt §28–§34)

(authored below)

## 11. Fixed-SHA A/B regression attribution (phase prompt §42)

(authored below)

## 12. Runtime zero-effect proof (phase prompt §46)

(authored below)

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

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved unchanged. No delegated worker committed, finalized, or pushed in this phase.

---
*Canonical artifact — Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.15.4. Authored incrementally.*

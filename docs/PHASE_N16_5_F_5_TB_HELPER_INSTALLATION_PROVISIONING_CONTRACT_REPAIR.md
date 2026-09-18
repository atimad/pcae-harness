# Phase N16-5-F-5-TB-HELPER-INSTALLATION-PROVISIONING-CONTRACT-REPAIR — Evidence

Phase ID: `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
(direct `.1` CPIPC child of the predecessor IV; alias
**N16-5-F-5-TB-HELPER-INSTALLATION-PROVISIONING-CONTRACT-REPAIR**).

Predecessor: `docs/PHASE_N16_5_F_5_TB_HELPER_INSTALLATION_IDENTITY_CONTRACT_REPAIR_IV.md` —
**COMPLETE — NOT VERIFIED / BLOCKED (F1)**.

**Disposition of this phase: CONTRACT REPAIRED / FROZEN — PENDING INDEPENDENT VERIFICATION.**

**Primary-operator review (this section only, added post-delegation).** I
independently re-read HPAC-PAWA-001 REQ-326/327/328 and §80.2 (REQ-219-228)
from the pre-repair contract text (`git show HEAD:...`) to confirm the F1
root-cause citation is accurate and not fabricated: REQ-326 does cite
"the §80.2 `configure_presentation_mechanism` model," REQ-223/REQ-226
confirm §80.2's dispatch is a standalone script with a direct, non-helper-
mediated PAWA capability and an explicitly "non-circular bootstrap," and
REQ-328's "driven through the §33C helper boundary" text is the literal,
verifiable contradiction. I independently re-diffed both contract files and
the edited test file; ran `tests/test_n16_5_f5_tb_prov_repair_contract.py`
(23/23 pass) and `tests/test_hpac_pawa_helper_writer_authority_contract_v2.py`
(39/39 pass) myself; and independently re-derived the regression triage by
diffing a true `git stash`-isolated baseline run against the candidate run
of the full `helper|pawa|ppa|hpac`-keyword sweep (85 failed / both), finding
the same ~14 pre-existing historical-snapshot version-pin failures the
delegated worker identified, plus one test
(`test_hpac_trust_root_repair_independent_verification_3w1r2b1r111r321.py::
test_concurrent_conflicting_successors_have_one_canonical_winner`) that
appeared candidate-only in one sweep ordering but passed both alone and in a
second full-sweep rerun — confirmed as pre-existing test-order flakiness in
that file (it fails 5 *different* tests when run standalone vs. in the
sweep), not a regression attributable to this phase's diff. Confirmed
`src/pcae/**` byte-unchanged (`git diff --stat` shows only `docs/**` and
`tests/**`). I concur with the disposition below.

`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED`

---

## 1. F1 independently reconstructed from source (not accepted from prose)

### 1.1 Concepts distinguished

- **hpahi / hpawi / hppi** — three disjoint `^h(pa|pah|pp)[wh]?i-[0-9a-f]{32}$`-shaped
  component lineages (HELPER §30D REQ-172); never OS identities.
- **Configured-agent exclusion identity** — `ConfiguredAgentAuthorityIdentity`,
  resolved live from `HPAC-PAWA-AGENT-EXCLUSION/1.0` (PAWA §9/§32A); the
  entity that must **never** be able to perform any of the below.
- **Deployment owner / protected-root owner** — the OS account with real
  filesystem write authority over `<HPAC_PROTECTED_ROOT>` (PAWA §4/§10).
- **Helper executor** — the `exec`'d one-shot privileged-helper OS process
  (HELPER §4).
- **Admitted helper peer** — an executor that has passed §7 (PAWA §33 steps
  1-8) and §10 (peer credential) admission.
- **Current generation** — the sole H (or P) lineage generation the anchor
  (`current-generation.json`) currently names as current (HELPER §6).
- **Parent installation relationship** — the typed, non-bearer
  `pawa_binding` tuple (HELPER §30D REQ-174) binding a component to the
  recognized live PAWA descriptor/anchor/exclusion state — never a self-
  reference.

### 1.2 F1-A — provisioning/bootstrap circularity: CONFIRMED, source-located

Chain, read directly from the live contracts:

1. HPAC-PAWA-HELPER-001 REQ-053 (operation vocabulary, pre-repair) lists
   `configure_privileged_helper` as an `admin_mutation` subtype — i.e. an
   operation **H itself performs**, once admitted.
2. HPAC-PAWA-001 REQ-328 (pre-repair): *"The `configure_privileged_helper`
   transaction is itself driven through the §33C helper boundary … so the
   helper-registration metadata is also written by a verified helper
   process."* — i.e. writing H's own registration record requires an
   **already-admitted H**.
3. HPAC-PAWA-001 §33C (REQ-311/342) admission requires the executing H to
   already have a registered current schema-2 generation and PAWA parent
   binding — i.e. **admission requires the registration REQ-328 says only an
   admitted H can write.**
4. This is the literal cycle: `H registration → admitted-H-mediated write →
   H registration`. At genesis (no H record exists at all), step 2's
   mechanism has no admitted H to invoke it; REQ-327's own text
   ("non-circular bootstrap … no pre-existing privileged-helper operation
   … required") **contradicts** REQ-328's own mechanism in the same
   contract, one section later.
5. **Root cause, independently located, not previously identified by the
   predecessor's prose:** REQ-326 itself cites `configure_privileged_helper`
   as following **"the §80.2 `configure_presentation_mechanism` model."**
   HPAC-PPA-001 §5 (REQ-021/REQ-022, frozen v1.2, byte-unchanged) specifies
   `configure_presentation_mechanism` is dispatched by a **standalone script
   obtaining one PAWA capability directly** — never through any helper
   boundary (none existed when §5 was frozen). REQ-328 silently diverges
   from the very precedent REQ-326 names, and that divergence is the entire
   defect. This is verified by direct comparison of PAWA REQ-021/022 against
   REQ-328's text — no source code exists yet to consult (no implementation
   phase has run), so contract text is the complete and sufficient evidence.

**Verdict: F1-A independently CONFIRMED**, with a more precise root cause
than the predecessor's report gives (predecessor located the cycle;
this phase locates the exact contradicting requirement pair and its
already-correct sibling precedent).

### 1.3 F1-B — self-lineage / sole-current rotation contradiction: CONFIRMED

HELPER §30D REQ-175: *"A helper cannot register/rotate/revoke its own active
executing lineage via `admin_mutation`; lifecycle control remains external
deployment-owner provisioning."* But pre-repair, the **only** specified
mechanism for `admin_mutation` dispatch of `configure_privileged_helper` is
"through the §33C helper boundary" (REQ-328) — and at rotation time, the
**only** admitted, current H is generation `G`, the very generation about to
be superseded. Dispatching `configure_privileged_helper(rotate)` "through"
the helper boundary necessarily means `G` is the executing process — i.e.
`G` participates in writing the record that supersedes it, which is exactly
what REQ-175 forbids. No alternative executor is specified anywhere in the
pre-repair contract set (the predecessor's report reaches the same
conclusion; this phase confirms it by the same direct-source method used for
F1-A, and locates it as **the same root cause** — REQ-328's erroneous
helper-boundary requirement — rather than a second, independent defect).

**Verdict: F1-B independently CONFIRMED, same root cause as F1-A.**

---

## 2. Provisioning-model adjudication

| | P-A (external deployment-owner) | P-B (bootstrap artifact) | P-C (prior-generation authority) | **P-D (deployment-root-mediated) — SELECTED** |
|---|---|---|---|---|
| Solves genesis | yes | yes | no (no prior generation exists) | yes |
| Solves rotation | yes, if re-invoked per-transition | yes, but needs replay defense | yes, but makes H a generic installer (rejected by §7 of the governing brief) | yes, uniformly with genesis |
| Second trust root | no, if grounded in existing deployment-owner root | risk of becoming a bearer artifact | no | no — reuses PAWA's existing §23/§32B-style deployment-owner root, and specifically HPAC-PPA-REQ-021/022's **already-frozen, already-independently-verified** instance of exactly this pattern |
| Generic-broker risk | low if narrowly scoped per mutation family | medium (a artifact "authorizes a transition" is broker-shaped if not exact) | high (H becomes able to install components) | low — capability is process-local, single-use, scoped to exactly one mutation family, mirroring PAWA-INV-15 |
| Precedent in this repo | HPAC-PAWA-REQ-056 (root bootstrap), REQ-194 (agent-exclusion bootstrap/rotation, REQ-197) | none clean | none | **HPAC-PPA-REQ-021/022** (byte-identical shape, for the sibling P component) |
| Selected | — | — | — | **Yes** |

**Why P-D and not the others:** P-D was selected not as a new invention but
because HPAC-PPA-001 already implements it, frozen and independently
untouched, for the P (`hppi`) sibling component — and HPAC-PAWA-001's own
REQ-326 already *declares* this as the intended model for H before REQ-328
silently diverges from it. Adopting P-D is therefore the **minimal, already-
precedented, already-partially-frozen** repair: it does not invent a new
authority concept, reuses the existing single trust root, and immediately
also resolves a second, previously unflagged cross-contract inconsistency
(§3 below).

P-C was rejected per the governing brief's explicit prohibition ("does not
make the helper a generic installer") and because it cannot solve genesis
(no prior generation exists at generation 1). P-B alone (a free-standing
bootstrap artifact) was rejected because it would introduce a new artifact
kind requiring its own replay/bearer-token analysis where the existing
PAWA-capability-mint pattern (PAWA-INV-15: process-local, non-bearer,
non-exportable, dies with the process) already provides everything needed.
P-A alone (without grounding in the specific already-frozen §5 PPA shape)
was rejected as under-specified relative to reusing precedent exactly.

---

## 3. Second, previously unflagged defect found and fixed as part of the same repair

Pre-repair, HELPER REQ-053/REQ-057 listed **both** `configure_privileged_helper`
**and** `configure_presentation_mechanism` as `admin_mutation` subtypes
dispatched through H — but PPA REQ-021/022 (frozen, byte-unchanged, v1.2,
predates HELPER-001's existence) already specifies `configure_presentation_mechanism`
is dispatched by a **standalone script with a direct PAWA capability**, never
through H. This is a live, source-confirmed, three-contract inconsistency
independent of F1 (P was never actually circular — it has no self-reference
problem regardless of dispatch route — but the *vocabulary* claimed a route
that never matched P's own contract). The repair in §98/§30E removes both
mutation ids from H's vocabulary uniformly, which resolves this cross-
contract inconsistency as a side effect of the F1 fix, at zero extra cost.
PPA itself required **no edit** — it was already correct.

---

## 4. Genesis / rotation / recovery semantics (PAWA §98, REQ-346/347/348)

| State | Admissible executor | Provenance source | Parent relation | Currentness precondition | Currentness postcondition | Failure behavior | Resumable after crash |
|---|---|---|---|---|---|---|---|
| **Genesis** | standalone helper-admin script, deployment-owner OS principal, direct PAWA capability | out-of-band installed bytes + REQ-345 capability | none (`supersedes = null`) | no current generation exists | generation 1 current | fail closed, no partial record (create-only) | yes — re-invocation is idempotent-preserve per PAWA-INV pattern if byte-identical, else `duplicate_bootstrap`-shaped rejection |
| **Rotation** | same script, **never** the current generation `G` itself | new bytes installed out of band + fresh REQ-345 capability | `supersedes = {G, digest(G)}` | exactly one current generation `G` | `G+1` current, `G` stale by derivation | fail closed; no anchor switch without both record + readback verified | yes — orphaned non-current `G+1` record detected via `supersedes` linkage; anchor switch is a bounded explicit repeat, never automatic |
| **Recovery** | same script, explicit new lineage | out-of-band installed bytes + fresh REQ-345 capability | `supersedes = null`, **new** `installation_id` | current generation missing/corrupted/unusable | new generation 1 (new lineage) current | fail closed; damaged lineage made unavailable first, never auto-healed | yes — same create-only semantics as genesis, under a fresh lineage id |

No automatic retry exists in any state (PAWA REQ-349). Exactly one anchor is
current at all times by construction of the existing atomic
create-then-replace-with-readback anchor mechanism (HELPER REQ-022) — this
repair does not alter that mechanism, only who invokes it.

---

## 5. Lineage / self-lineage test cases (worked through)

| Case | Outcome under repaired model |
|---|---|
| H0 genesis → H1 current | genesis path (§4); H0 never existed, H1 is generation 1 |
| H1 current → H2 successor | rotation path; script dispatches, H1 never executes the transition |
| H2 current → H3 successor | rotation path, same as above, `supersedes={2,digest(H2)}` |
| attempt H2 → H2 | rejected: `configure_privileged_helper` is not a member of any operation H2 can request of itself (it cannot request `admin_mutation` with this id at all, REQ-184); and the script-side transaction requires the *live* current generation to equal the *from*-generation, so a same-generation request has no valid target |
| H1 retired trying to provision H3 | rejected: H1 is not the script; H1 cannot invoke §98 at all (H has no path to this mutation family post-repair) |
| H1 trying to provision H1 | same as above — H cannot reach this operation |
| H1 trying to replace H2 after H2 is current | rejected: the script's rotation transaction requires the live anchor to equal the *from*-generation named in the transaction; a stale `from` fails `descriptor_generation_stale` |
| generation rollback H2 → H1 | rejected: REQ-347/HELPER REQ-027 — restoring an older generation record alone fails current-anchor comparison |
| unrelated installation X trying to become parent of H2 | rejected: `pawa_binding`/`installation_id` typed grammar (HELPER REQ-172/174) — X's id is not H2's registered lineage |
| same installation ID with different bytes | rejected: `helper_sha256` mismatch on pre-launch recognition (HELPER REQ-028) |
| different installation ID with same bytes | two distinct lineages sharing bytes is permitted at the artifact level but each has its own registration; neither can claim the other's currentness |
| same generation number under a different installation lineage | permitted — generation counters are independent per `installation_id` (HELPER REQ-172); component generations are never compared across lineages (HELPER REQ-176) |
| stale parent generation | rejected: PAWA parent-binding digest/generation mismatch, `descriptor_generation_stale` |
| mixed PAWA/PPA parent tuple | rejected: `pawa_binding` is typed to PAWA only; a PPA descriptor cannot satisfy it (HELPER REQ-172 disjoint grammar) |

"Parent" in this contract set means exactly one thing after this repair: the
typed `pawa_binding` tuple — the recognized live PAWA descriptor/anchor/
exclusion state a component is bound to. It never means "installing
authority" (that's now always the external script, never a component),
"prior generation" (that's `supersedes`, a distinct field), or "component
ownership." No field is overloaded with two meanings.

---

## 6. Adversarial cases (phase-authorization §15) — disposition

All 30 enumerated cases were walked. None defeat the repaired model; the
load-bearing ones (H self-provisioning: cases 11/12/13; races: case 14;
crash leaving two currents: case 15; authority reuse across boundaries:
cases 26-28) are covered explicitly in §4/§5 above and in HELPER REQ-187.
Case 20/21 (PAWA or PPA installation substituted for H) are rejected by the
disjoint `hpawi`/`hpahi`/`hppi` grammar (pre-existing, §30D, unchanged).
Case 29/30 (provisioning result treated as human approval / PB permission)
are structurally impossible — REQ-345's capability is a metadata-mutation
capability with no path to RHAMP/PB/runtime code at all, unchanged from the
pre-repair Model E boundary.

---

## 7. Model E / cross-contract preservation

- Model E (HELPER §30B) is **untouched**: three sealed authority families,
  typed facades, no shared base with `HPACWriterCapability`, no export.
  `configure_privileged_helper` was **never** one of Model E's three families
  (`admin_mutation` proper / `certification_write` / `presentation_evidence_write`
  are Model E; `configure_privileged_helper` was a *different* `admin_mutation`
  subtype dispatched through the legacy pre-Model-E in-process PAWA mint path
  described in PAWA §36-38, now scoped down to exactly the two component-
  lifecycle families by §98/REQ-345). Removing it from H's reachable
  vocabulary cannot leak into challenge/proof/Gate5/counter/presentation
  scope — those are the four other operations, all Model E, all unchanged.
- HPAC-PPA-001 stays **v2.1, byte-unchanged**.
- HPAC-PAWA-001: v3.0 → **v4.0** (MAJOR, §98, REQ-352).
- HPAC-PAWA-HELPER-001: v4.0 → **v5.0** (MAJOR, §30E, REQ-188).
- All three contracts are cross-consistent: HELPER no longer claims a
  vocabulary member PAWA no longer routes through it; PAWA's REQ-326
  precedent-citation and REQ-345 dispatch model now agree; PPA's REQ-021/022
  and PAWA's REQ-345 are now textually identical in shape.

---

## 8. Source-impact map (read-only; no implementation performed)

| Item | Category |
|---|---|
| `scripts/hpac_pawa_helper_admin.py` (or a `configure_privileged_helper` subcommand on the existing `scripts/hpac_protected_root_admin.py`) | **required future production change** — does not exist yet |
| `src/pcae/core/hpac_pawa_helper_writer_authority.py` | no change — Model E facades untouched |
| `src/pcae/core/hpac_pawa_helper_store_adapter.py` | no change |
| `src/pcae/core/hpac_pawa_agent_exclusion.py` | no change — same resolution predicate reused (REQ-350), not modified |
| `src/pcae/core/hpac_foundation.py` | **unrelated, still-open** dependency (the `_validate_production_boundary` / configured-agent-vs-live-process gap from N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL) — this phase does not touch or claim to repair it |
| helper deployment packaging | **required future packaging/deployment change** — the standalone script needs an out-of-band install/registration procedure documented alongside the existing root-provisioning runbook |
| any live host generation state | **no change** — no Dell/Mac protected root touched |
| `docs/contracts/*.md` (three files) | tests only / contract text — this phase's actual deliverable |

---

## 9. Recommended next phase

`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1.1`
— **N16-5-F-5-TB-HELPER-INSTALLATION-PROVISIONING-CONTRACT-REPAIR-IV**
(fresh independent verification). **NOT BEGUN.** N-16-5 remains **NOT
CLOSED**. N-16-6/N-16-7 untouched. The still-open
`hpac_foundation.py` configured-agent-vs-live-process write-boundary gap
(from N16-5-F-5-TB-HELPER-WRITER-AUTHORITY-IMPL) is untouched by this repair
and remains a **separate** prerequisite before real writes are possible,
independent of this phase's provisioning-circularity repair.

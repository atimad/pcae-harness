# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1 (alias N16-5-F-5-TB-CONTRACT) — N-16-5 Privileged Production Authority Trust-Boundary Contract Evolution

**Status: COMPLETE — CONTRACT FROZEN.**
**HPAC-PAWA-001 evolved v1.4 → v2.0 (MAJOR, S-4). New companion
HPAC-PAWA-HELPER-001 v1.0 FROZEN.**
**Trust-boundary status: OUT-OF-PROCESS TYPED-OPERATION CONTRACT FROZEN / IV
PENDING.**
**F-5-B2: BLOCKED PENDING CONTRACT IV + IMPLEMENTATION. F-5: CERTIFICATION
BLOCKED. N-16-5: NOT CLOSED. N-16-6 / N-16-7: OPEN / UNTOUCHED (N-16-7 strictly
last).**

This is a **contract-only** governed phase. It evolves one frozen contract in
place, freezes one new companion contract, reconciles downstream point-in-time
guards (widen-not-weaken), and adds one contract-verification test suite. It
implements **no** helper executable, launcher, IPC channel,
`configure_privileged_helper` transaction, or caller migration; it removes **no**
in-process code; it mutates **no** protected host state; it performs **no**
ceremony. Runtime posture is unchanged throughout: `not_implemented` /
`Observed` / `observe` / `unavailable` / 0 plugins / 0 capabilities; the first
governed runtime external effect remains **ABSENT / UNREACHABLE**.

---

## 0. Governance / phase identity

### 0.1 Repository state at phase entry

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD | `05056eeb1d38d92d7eda749a4334f7626c5e6a8f` |
| `origin/main` | `05056eeb1d38d92d7eda749a4334f7626c5e6a8f` (identical; fetched at entry) |
| `origin/main..HEAD` | 0 commits |
| Working tree | clean at entry |
| Conflicting active governed phase | none — only the idle placeholder `20260910-0236-idle-…`; phase queue empty; no handoff newer than the latest completed phase report other than the informational 2026-09-04 "Switching agents" handoff |

### 0.2 Predecessor

| Field | Value |
|---|---|
| Alias | **N16-5-F-5-TB-ARCH** |
| Canonical Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1` (48 subphase segments) |
| Predecessor finalizing HEAD | `05056eeb` (report commit `71f9e337`) |
| Predecessor completion — canonical artifacts | `PROJECT_STATUS.md` "## Current Phase" = this predecessor, **STATUS: COMPLETE — contract-evolution verdict B**; `.pcae/phase-completion-metadata.json` `status = "completed"`, `phase_id` matches; `.pcae/phase-completion-report.md` staging header matches; governed done task `tasks/done/20260910-0236-…`; canonical report `docs/PHASE_N16_5_F_5_TB_ARCH.md` |
| CPIPC validation | **VALID** — see §0.3 |

### 0.3 CPIPC-valid successor derivation

Independently derived via `pcae.core.phase_id` (CPIPC-001 v1.0, the sole
authority per CPIPC-REQ-018), **not** taken from any precomputed value in the
authorizing prompt:

```
candidate = <predecessor phase id> + exactly one ".1" subphase segment
          = 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1
```

| CPIPC check | Result |
|---|---|
| `is_valid(candidate)` | `True` |
| `validate(candidate)` | no error |
| `format(parse(candidate)) == candidate` | `True` — exact canonical text, no normalization drift |
| `compare(predecessor, candidate)` | `less` — candidate is a **strict** successor |
| `same_series(predecessor, candidate)` | `True` — series `149` |
| `same_branch(predecessor, candidate)` | `True` — branch `O` |
| Successor-segment count | predecessor 48 subphase segments → candidate 49; exactly one appended `(1, "")` — the canonical first-child |
| Uniqueness / collision | `git log --all` for the exact dotted string: **no match**; `grep -rF` over `docs/`, `tasks/`, `.pcae/`: **no match** |
| Conflicting active governed phase | none (§0.1) |

Recorded in PCAE authoritative artifacts by this phase: the active task title,
`PROJECT_STATUS.md` "## Current Phase", `.pcae/phase-completion-metadata.json`
`phase_id` / `phase_title`, the staging `.pcae/phase-completion-report.md`, and
`tasks/DECISIONS.md`. Alias **N16-5-F-5-TB-CONTRACT** is display-only, written
hyphenated in every governed identity source so the CPIPC token scanner
(`pcae.core.phase_id.scan_tokens`, greedy `[0-9]+[A-Za-z]+`) extracts no stray
phase token from it (`feedback_cpipc_alias_token_trap`).

---

## 1. Predecessor architecture baseline (carried forward, not re-adjudicated)

The predecessor **N16-5-F-5-TB-ARCH** (`docs/PHASE_N16_5_F_5_TB_ARCH.md`)
selected, and this phase translates into frozen normative text:

> **Candidate 6C — a short-lived, one-shot privileged helper process**, realized
> as a generalization of the independently verified HPAC-PPA-001 verified-helper
> pattern, anchored on the **existing** HPAC-PAWA §4 OS filesystem trust root.

Carried-forward axiom (predecessor **N16-5-F-5-B2R2-IMPL**, independently
proved): the frozen HPAC-PAWA-001 v1.4 consumer-authenticity property is
**unsatisfiable within a same-process Python interpreter** for all four
privileged factories — `gc.get_objects()` / `gc.get_referrers()` reach any
authority-bearing object or state regardless of encapsulation, and ordinary
in-process code can `exec` a new function into an already-imported trusted
module's `__dict__`. The frozen trust root (§4, *"never an in-process check"*)
never sanctioned an in-process authority object; the defect was that the
implementation **delivered authority as an in-process object and enforced
consumer identity with an in-process check**.

Core architectural properties frozen: no `HPACWriterCapability` /
`HPACStoreAuthority` / privileged handle crosses back to the ordinary Python
interpreter or the launcher; the privileged side performs the bounded operation;
the ordinary side receives only typed result / evidence; helper execution is
integrity-verified; protected trust comes from OS / filesystem / process
properties, not Python caller identity; **no second trust root**; the exact
five-role certification family stays closed; human authentication / approval stay
semantically separate; runtime stays Observed / observe / unavailable.

---

## 2. Current HPAC-PAWA-001 v1.4 baseline — reconstructed

Reconstructed from primary repository artifacts (the contract file header,
§4, §5, §7C, §8, §32, §33, §33A, §33B, §36–§39, §41, §42 / §42B / §42D / §42E,
§49–§49B, §60, §68 / §68A / §68B, §80 / §80.1–§80.4, §90.4, §91, §92
(PAWA-INV-1..14), §94, §95C, §96C) — **not** taken on the predecessor's
assertion:

| Question | Finding |
|---|---|
| Current version | **HPAC-PAWA-001 v1.4, FROZEN, MINOR (S-3)**. Lineage v1.0 → v1.1 → v1.2 → v1.3 → v1.4, every evolution MINOR. |
| Independently verified? | **FROZEN**; independently verified at the contract level (the F-5-B1 IV lineage **N16-5-F5B1-READAUTH-IV** / **N16-5-F-5-B1-IV** is reflected in `git log`). Not validated against the *same-process unsatisfiability* the later F-5-B2 line discovered — that discovery is why the architecture phase and this phase exist. |
| Trust root | OS filesystem write authority on the out-of-band-provisioned protected root (HPAC-PAWA-REQ-010 / REQ-300), *"never an in-process check"*. |
| §32 / §33 | §32 predicate 6 = the in-process **calling-module** authorized-factory-consumer check; §33 = 11 steps, frozen order, step 9 = that in-process check; §33A / §33B reuse §33 steps 1–9 verbatim and add parallel certification-writer / read-authority sequences. |
| §36–§38 / §41 | an in-process factory (`production_writer` / `certification_writer` / `recognized_certification_read_authority` / `mint_protected_presentation_evidence_writer`) mints and **returns** an `HPACWriterCapability` / `HPACStoreAuthority` / `CertificationReadAuthority` handle to a same-process caller. |
| §42B five-role family | closed allowlist `{ hpac_challenge_coordinator, hpac_assertion_recorder, human_authentication_proof_verifier, hpac_gate5_binder, hpac_rhamp_counter_state_verifier }`; `hpac_lifecycle_terminator` excluded; per-role authority table frozen (HPAC-PAWA-REQ-247). |
| §42D read authority | one recognized read-only `HPACStoreAuthority` accessor; enumerated closed read set; one ceremony entry; `HPACStoreAuthority.writer()` still raises; `hpac_rhamp_counter_state_verifier` sole counter mutation authority; `mint_protected_presentation_evidence_writer` sole `HPAC-PRESENTATION-EVIDENCE/2.0` author. |
| §49B / PAWA-INV-14 | `CertificationReadAuthority` handle — process-local / non-bearer / non-serialisable / restart-dead / one-session / one-ceremony-entry. |
| Requirement / invariant count (v1.4) | **309** `HPAC-PAWA-REQ-###` (contiguous 1–309); **14** `PAWA-INV-#`. |
| `pawa_failure_code` | 21 closed values; every v1.1 / v1.2 / v1.3 / v1.4 rejection maps onto them; RHAMP-001 v1.0 §49 (41 `terminal_reason_code`) byte-unchanged. |
| Sibling contracts at v1.4 | HPAC-001 v2.1, RHAMP-001 v1.0, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1, HBDC-001 v1.2, HPAC-PPA-001 v1.0, the descriptor + current-generation schemas — all **byte-unchanged**. |

v1.4 lineage is consistent and not ambiguous (header / §7C / §80.4 / §90.4 / §94
/ completion metadata agree). This phase therefore proceeds (no §3-mandated
STOP).

---

## 3. Version-classification adjudication — HPAC-PAWA-001 v1.4 → v2.0 (MAJOR)

| Field | Value |
|---|---|
| Prior version | **1.4** |
| New version | **2.0** |
| Classification | **MAJOR** |
| Governing rule | **HPAC-PAWA-REQ-152** read with **HPAC-PAWA-REQ-153** and §80. §153's MINOR permits are a **closed enumeration** ("re-state verified behaviour"; "add a `pawa_failure_code` …"; "add an authorized-consumer **category** by explicit enumeration"; "tighten (never loosen) a bound"; "clarify a platform-adapter detail"; "add an additional macOS / Linux adapter … provided no meaning above changes"; "add **one** explicitly enumerated protected-admin **metadata mutation family** …"). This evolution is outside **every** one of them: it **removes and replaces a normative recognition predicate** (§32 predicate 6 / §33 step 9) and **restructures the authority-delivery model** of §36–§38 / §41 / §42B / §42D / §33B from "an in-process factory returns an `HPACWriterCapability` / handle to a same-process caller" to "a distinct out-of-process protected helper performs the bounded operation and returns typed evidence only". §153's closing clause ("provided no meaning above changes") is not satisfied — the meaning of §32, §33, §36–§38, §41, §42B, §42D, §46, §49B, PAWA-INV-13, PAWA-INV-14 changes materially. §152 reserves authority-model restructuring for MAJOR; §80 additionally requires a MAJOR to carry **explicit human authorization and independent verification** — both are present (this phase's authorizing prompt; the derived N16-5-F-5-TB-CONTRACT-IV). Frozen as **HPAC-PAWA-REQ-331** (Explicit MAJOR rule, S-4, §80.5). |
| Rationale | Every prior evolution (v1.1 S-1, v1.2 §80.2, v1.3 S-2, v1.4 S-3) was argued a MINOR **because it reused §33 steps 1–9 verbatim and added only a parallel sequence / an enumerated consumer / a read-only accessor**. This phase **rewrites §33 step 9 itself** and the §32 predicate-6 definition, and eliminates the return-authority-object-to-caller delivery path for all four factory families. The predecessor architecture (`TB-ARCH` §8, §31) reached the same conclusion: the change "is **not** expressible as HPAC-PAWA-REQ-153's permitted MINOR moves — it **restructures the frozen recognition-sequence delivery model** and the factory / handle semantics." Counter-argument "replacing an unsound predicate with a stronger one is a §153 'tighten a bound'" — **rejected**: a tightening keeps the same predicate and narrows its acceptance set; this replaces the predicate with a structurally different one and changes which OS actor performs the privileged operation. |
| §152 verbatim-trigger review | Recorded in HPAC-PAWA-REQ-332 — **no §152 trigger fires literally** (the one-shot channel is a **local** private pipe / `AF_UNIX` socket, not remote / network / cloud; the trust root is unchanged; the helper-hash pin is a digest, not a cryptographic authority key; consumer enumeration is not widened by wildcard — it is *replaced by the stronger* "was `exec`'d from the verified helper" property). The classification therefore rests on §153's **closed permit list**, not on a §152 verbatim trigger. |
| Contract-versioning-rule ambiguity | **None found.** §153's permits are a closed list; the evolution falls outside all of them; §80's MAJOR pathway (explicit authorization + IV) is available and taken. No §4-mandated STOP-and-report-a-contract-versioning-blocker. |

---

## 4. Companion-contract adjudication — B (new companion HPAC-PAWA-HELPER-001 v1.0)

| Field | Value |
|---|---|
| Decision | **B — a distinct new companion helper-protocol contract**, `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`, contract id **HPAC-PAWA-HELPER-001**, **v1.0 FROZEN**, independent `HPAC-PAWA-HELPER-REQ-###` namespace. **Not** option A (extend HPAC-PPA-001); **not** an in-line HPAC-PAWA-001 section. Frozen as **HPAC-PAWA-REQ-334**. |
| Companion name / version | **HPAC-PAWA-HELPER-001 v1.0** (protocol wire id `HPAC-PAWA-HELPER/1.0`). Token-safe: no `<digit><letter>` substring in the identity form. |
| Why not extend HPAC-PPA-001 | HPAC-PPA-001 is, by its own §1 / §2 / §19 / PPA-INV-1 / PPA-INV-2, the **protected-presentation** installation + one-shot launch + `HPAC-PRESENTATION-EVIDENCE/2.0` evidence-writer contract, scoped to `pcae-protected-local-presentation` and the human-APPROVE ceremony. The helper protocol covers privileged operations **well beyond** protected presentation — the §42 administrative-mutation family, the §42B five-role certification-lifecycle writes, the §42D enumerated reads, **and** the ceremony-entry hand-off. Folding those in would "broaden presentation semantics into a generic privileged operation protocol" — explicitly discouraged by the authorizing prompt §5 and inconsistent with PPA-INV-2. HPAC-PAWA-REQ-308 (v1.4) itself anticipated that a genuine second-contract need means a **separate** contract. |
| Why a companion, not an in-line section | The helper wire protocol, executable-provenance / launch model, private-channel and OS peer-authentication logical properties, request / response schema, freshness / replay / crash / audit-ordering semantics, and cross-platform peer-credential profiles are a self-contained protocol specification (the REPRC-001 / PBNDE-001 / RHAMP-001 / HPAC-PPA-001 "companion born to avoid overloading the parent" precedent, HPAC-PPA-REQ-068). |
| Semantic separation preserved | protected presentation (HPAC-PPA-001) ≠ protected authority operations (HPAC-PAWA-HELPER-001) ≠ human authentication (HPAC-001 / RHAMP-001) ≠ approval (the HPAC-PPA-001 ceremony) ≠ Gate 5 ≠ counter-state verification. |
| Cross-contract question deferred to the IV | HPAC-PPA-001 v1.0's evidence-writer authority (HPAC-PPA-REQ-041, "held only by the trusted launcher mediator … never sent to the helper") interacts with the v2.0 out-of-process model — `presentation_evidence_write` is now minted and consumed inside the already-out-of-process presentation helper. Whether this is within HPAC-PPA-REQ-041's "or repository-equivalent … primitive" / HPAC-PPA-REQ-070's "platform adapter within these exact properties" (a tightening — authority moves *further* from the agent interpreter), or a re-meaning of "never sent to the helper" needing a **fresh aligned HPAC-PPA-001 successor**, is an **explicit question for N16-5-F-5-TB-CONTRACT-IV**. This phase does **not** silently edit HPAC-PPA-001 (HPAC-PAWA-HELPER-001 §17 cross-contract note; §80.5 / HPAC-PAWA-REQ-334 discipline). |

---

## 5. Normative changes — HPAC-PAWA-001 v1.4 → v2.0

Every prior freeze record is immutable; v2.0 is **append-only**. No
`HPAC-PAWA-REQ-###` id is deleted or renumbered.

### 5.1 Header / lineage / delta table

- Header `# HPAC-PAWA-001 v1.4 —` → `# HPAC-PAWA-001 v2.0 —`; `**Version:** 1.4`
  → `**Version:** 2.0`; an "**Evolved to v2.0 by:**" block; the lineage
  paragraph gains "(every evolution MINOR) **→ v2.0** (**MAJOR**, S-4)" and
  "v2.0 adds **one** new companion, **HPAC-PAWA-HELPER-001 v1.0**"; the
  "adds normative text only" paragraph gains the v2.0 clause (no helper /
  launcher / protocol / channel / peer-cred call / registration record /
  in-process-mechanism removal in this freeze).
- **§7D. v1.4 → v2.0 normative delta table** — 11 rows.

### 5.2 Superseded-in-place clauses (annotated "**(v2.0) …**", not deleted)

| Clause | v1.4 | v2.0 disposition |
|---|---|---|
| §32 predicate 6 (HPAC-PAWA-REQ-073) | "verify the **calling module** is an authorized factory consumer" | **SUPERSEDED by §33C** — the trusted consumer is the distinct helper process (`exec`'d, peer credential, §33 1–8 in the helper) |
| §33 step 9 (HPAC-PAWA-REQ-074/075) | in-process check | **§33C step 9′**; steps 10 / 11 become "perform the one bounded operation in the helper" / "audit with the §22 ordering" — added as a trailing **(v2.0) note**, the numbered list left byte-identical |
| §33A (HPAC-PAWA-REQ-238 trailing note) | in-process `certification_writer` | runs inside the helper for a `certification_write`; five-role closure byte-unchanged |
| §33B (HPAC-PAWA-REQ-280 trailing note) | in-process accessor + `CertificationReadAuthority` handle | runs inside the helper for `certification_read` / `ceremony_entry`; the `_bind_configured_agent_identity` bind still in the helper before the session-binding reads; **no** handle / `HPACStoreAuthority` crosses back |
| §36 (HPAC-PAWA-REQ-083 trailing note) | factory returns a capability | minted **and consumed inside** the one-shot helper; never returned; `production_writer` / `certification_writer` become helper operations |
| §37 (HPAC-PAWA-REQ-086 trailing note) | recognition / mint in a non-agent-importable module | recognition / mint in the **`exec`'d out-of-band helper executable**; the main interpreter imports no writer module |
| §42B (HPAC-PAWA-REQ-250 trailing note) | in-process `certification_writer` mint | `certification_write` helper operation; per-role authority table byte-unchanged in substance |
| §42D (HPAC-PAWA-REQ-288 trailing note) | `CertificationReadAuthority` handle | `certification_read` returns record **contents**; `ceremony_entry` returns an acknowledgement; enumerated read scope byte-unchanged; `PawaOperation` count 6 → 7 (the one new `configure_privileged_helper` mutation) |
| §49B (trailing note) | handle lifetime | there is no returnable type; §45–§49 / §49A / §49B become **process-boundary** properties (§49C) |
| §68B (HPAC-PAWA-REQ-300 trailing note) | no second trust root (F-5-B1) | restated for the out-of-process model — the helper registration is an integrity-pinned artifact of the existing kind, not a bootstrap authority |
| PAWA-INV-13 / PAWA-INV-14 | in-process delivery wording | annotated "**(v2.0) delivery superseded by §33C — substance unchanged**" |

### 5.3 New v2.0 sections and invariants (HPAC-PAWA-REQ-310..340)

| Section | Content |
|---|---|
| **§33C** (REQ-310..316) | Out-of-process privileged-helper recognition; the frozen `TrustedProtectedAuthorityConsumer(request)` 13-conjunct conjunction; consumer authenticity ≠ IPC access; fresh per `exec`; fail-closed; no in-process authority object / predicate; `FILE LOCATION != TRUSTED ORIGIN` etc. preserved |
| **§38C** (REQ-317..320) | Authorized privileged-helper launchers — **exactly** the standalone deployment-owner entry points of §38 / §38A / §38B; launcher obligations / prohibitions; possession ≠ authority; no wildcard; the §39 / §39A / §38B guards extended |
| **§42F** (REQ-321..325) | Out-of-process typed-operation delivery; no authority-object export (PAWA-INV-15); the closed operation vocabulary; the four-factory → operation mapping; the code path leaves the main interpreter entirely |
| **§42G** (REQ-326..328) | `configure_privileged_helper`, role `privileged_helper_installer` — the one new §42 mutation family; metadata-only install / rotate / revoke of `HPAC-PAWA-HELPER-INSTALLATION/1.0`; non-circular bootstrap; itself driven through the helper boundary |
| **§42H** (REQ-329) | Every v2.0 rejection maps onto the existing 21 `pawa_failure_code` values (table); no new code; no `terminal_reason_code`; RHAMP-001 v1.0 §49 byte-unchanged |
| **§49C** (REQ-337) | Non-bearer / restart-dead as process-boundary properties |
| **§68C** (REQ-338) | v2.0 walls — every §5 / §13 / §67 / §68 / §68A / §68B wall preserved verbatim; restated for the out-of-process model |
| **§80.5** (REQ-330..336, 339) | The S-4 MAJOR versioning rule; the §152 verbatim-trigger review; MAJOR triggers extended; the companion-contract determination; "no production change in the v2.0 freeze phase"; schemas byte-unchanged; traceability |
| **§90.5** | The v2.0 contract-freeze verdict block |
| **§95D** | Out-of-process delivery contract-shape disposition (6C frozen; 6A / 6B / 6E / network / single-contract rejected) |
| **§96D** (REQ-340) | Recommended next phases (derived, NOT begun) |
| **PAWA-INV-15** | No production privileged authority object crosses from the helper process into the launcher or the ordinary PCAE interpreter |
| **PAWA-INV-16** | The trusted production consumer is the §33C out-of-process conjunction; failure of ANY conjunct → hard DENY; no single conjunct sufficient; no caller self-assertion |
| **PAWA-INV-17** | No second trust root; the seven distinct evidence / predicates are never conflated |

### 5.4 Requirement / invariant inventory (v2.0)

- **340** `HPAC-PAWA-REQ-###`, contiguous `001`..`340`, no gaps, no duplicates
  (v2.0 additions `HPAC-PAWA-REQ-310`..`340`). Verified programmatically.
- **17** `PAWA-INV-#` (`PAWA-INV-15` / `-16` / `-17` added), each referenced
  once in §92.

---

## 6. HPAC-PAWA-HELPER-001 v1.0 — the new companion contract

`docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`. **114**
`HPAC-PAWA-HELPER-REQ-###` (contiguous `001`..`114`), **10** `PAWAH-INV-#`.
35 numbered sections modelled on the HPAC-PPA-001 companion shape.

Minimum-content coverage (authorizing prompt §40): scope §1; non-goals §2;
trust root §3; actors / principals §4; platform-profile abstraction §5;
installation / provisioning §6; helper integrity recognition §6 (same-file-object
/ anti-TOCTOU §6.29); launcher requirements §8; private channel §9; peer
authentication §10; request schema §11 (`HPAC-PAWA-HELPER-REQUEST/1.0`, closed,
self-excluding digest, unknown-field fail-closed, ≥ 256-bit CSPRNG nonce);
response schema §12 (`HPAC-PAWA-HELPER-RESPONSE/1.0`); operation vocabulary §13
(closed enum: `admin_mutation` | `certification_write` | `certification_read` |
`ceremony_entry` | `presentation_evidence_write`); five-role mapping §14.2
(closed allowlist reused verbatim; `hpac_lifecycle_terminator` excluded);
typed-read vocabulary §15 (enumerated §42D set; repeated reads cannot
reconstruct store authority); ceremony-entry semantics §16 (hand-off only; every
wall verbatim); presentation-evidence write semantics §17 (+ the HPAC-PPA-001
cross-contract note); freshness §18; replay §19 (fresh / consumed / duplicate /
expired / unknown / conflicting-replay dispositions); one-shot semantics §20 /
§49C; crash / uncertainty §21 (the INDETERMINATE / RECONCILIATION-REQUIRED
state); audit / evidence §22 (**ordering model A — evidence durably staged
before the mutation, finalized after commit**; the "audit failure means the
mutation did not occur" phrase is **not** frozen — the *ordering* is);
no-auto-retry §23; no authority-object export §24 / PAWAH-INV-1; no generic
privileged broker §25 / PAWAH-INV-5; deterministic-vs-real wall §26.1;
mechanism neutrality §27; cross-platform profiles §5 / §28 (`SO_PEERCRED` /
`LOCAL_PEERCRED` / `getpeereid` — not assumed byte-for-byte equivalent);
security invariants §29 (PAWAH-INV-1..10); versioning / evolution rules §30;
test / verification requirements §31 (specifications for future phases, not
authored now).

---

## 7. Contract-cross-reference review

| Contract | Version-pinned reference to HPAC-PAWA-001? | Disposition |
|---|---|---|
| **HPAC-001** v2.1 | no (companion; walls preserved) | **byte-unchanged**; §68C preserves every wall |
| **RHAMP-001** v1.0 | RHAMP-REQ-047 names "the trust anchor … external to PCAE" (not version-pinned); counter is a **read** in §42D only | **byte-unchanged**; no mutation, no new `terminal_reason_code`, no §49 change |
| **HPAC-PPA-001** v1.0 | header "Protected administration: HPAC-PAWA-001 v1.2"; HPAC-PPA-REQ-005 names "HPAC-PAWA-001 v1.2" — historical / when-frozen references | **byte-unchanged**; the ceremony signature and `mint_protected_presentation_evidence_writer` path are reused; the evidence-writer-delivery question is deferred to the IV (§4) and, if it needs a normative change, a **fresh governed HPAC-PPA-001 evolution phase** — **not** silently edited here |
| **HBDC-001** v1.2 | precedent, not a shared authority root | **byte-unchanged** |
| **RIHAC-001** v2.0 / **RIASC-001** v3.0 / **RDGO-001** v3.1 | unaffected | **byte-unchanged** |
| descriptor + current-generation schemas | — | **byte-unchanged**; the helper-registration records are new siblings in a `pawa-helper/` namespace, adding no field to any existing schema |

**No other contract requires a normative change** for the v2.0 + HELPER-001
freeze to be coherent. The one genuine open cross-contract question
(HPAC-PPA-001 evidence-writer delivery) is recorded for the IV and, if needed, a
fresh successor — the phase does not force a cross-contract edit outside scope
(authorizing prompt §39; §58 valid-BLOCKED discipline was considered and **not
triggered** — the evolution freezes coherently with the question deferred).

---

## 8. Guard reconciliation (widen-not-weaken)

A/B: baseline `05056eeb` (phase entry, last v1.4 commit) vs HEAD over the
affected guard-set + `docs/contracts` consumers.

- **Baseline failures:** 40 pre-existing, node-for-node identical at baseline
  and HEAD — unrelated point-in-time / protected-root-presence guards from the
  F-5 / F-5-B2 / N-16-3 / N-16-4 lines (a verification phase re-baselines them).
- **Attributable failures:** **27**, all reconciled; **0 remaining** across the
  gsel + PPA + N-16-3/4 + v1.1-meta guard set (`comm -23` HEAD-vs-baseline =
  empty).
- `def test_` counts **identical** per file (17 touched files); **0** test
  function renamed, removed, or disabled; **no** bare `xfail` / `fnmatch` /
  `.rglob(` / `@pytest.mark.skip` / `def test_` token added in reconciliation
  code or comments.

Reconciliation classes (full detail in `tasks/DECISIONS.md`):

| Class | Guards | Method |
|---|---|---|
| "only the PAWA anchor changed under `docs/contracts`" subset (`<=`) | `.5R.2.1R.1R` f4 / f6-iv / f6-repair / f7 / f8 / f9-iv / f9-deployment; `.30R.4R` `test_32`; `.30R.4R.1` `test_03`; H3-PAWA13 `test_39` | widened the allowed set by **exactly** the one new companion file; `<=` orientation preserved |
| "no contract byte change since <SHA>" moving-`HEAD` | f5b1_impl `test_02`; f5b1_iv `test_03`; h3_impl `test_93`; h3-iv `test_iv03`; f5b2 `test_31` | re-anchored the moving `HEAD` to the fixed SHA `05056eeb` (last v1.4 commit) — the N16-5-F5B1-READAUTH re-anchor precedent |
| v1.4-freeze-fact guards | f5b1_readauth_contract `test_10` / `test_54` / `test_71` / `test_74` / `test_75` | re-anchored the contract read from the live worktree to the fixed SHA `05056eeb` via a new `R2` const + `at_r2` / `text_r2` helpers |
| contract-version-header `startswith` | H3-PAWA13 `test_04`, f5b1_impl `test_01`, r4r_2-iv `test_07` | extended the accepted prefix tuple by `"# HPAC-PAWA-001 v2."` / `"v2.0"`; the v1.3 lineage prefix preserved verbatim |
| requirement-numbering closure | `.30R.4R` `test_33` | added `list(range(1, 341))` to the accepted set |
| byte-freeze / verbatim-body | `pawa_v1_3_contract_iv` `test_06` | **passes unchanged** — every v1.3 REQ body survives verbatim and contiguous (all v2.0 notes are appended bullets / new sections; a transient mid-list edit was reverted) |

---

## 9. Contract-verification test suite

`tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1_1_1_n16_5_f_5_tb_contract.py`
— **45 tests, 45 passed, 0 failed.** Contract-only / read-only. Verifies:
the v2.0 header / lineage-prefix preservation / requirement contiguity (1–340) /
v2.0 additions (310–340) / 17 invariants; every v1.4 requirement body survives
verbatim; historical freeze verdicts intact; §32/§33-step-9 superseded-by-§33C;
the `TrustedProtectedAuthorityConsumer` 13-conjunct conjunction frozen;
PAWA-INV-15 / -16 / -17; single trust root / no second root; the one new
`configure_privileged_helper` mutation and `PawaOperation` count 7; the closed
operation vocabulary; five-role closure preserved verbatim; the S-4 MAJOR
adjudication and the companion-contract decision; the dedicated IV requirement;
walls / runtime posture; the full HELPER-001 structure (header, contiguity
1–114, PAWAH-INV-1..10, trust root, no-authority-export, closed vocabulary,
five-role, typed-read, peer-auth, anti-TOCTOU, state-transition + audit
ordering, replay, mechanism neutrality, cross-platform, deterministic-vs-real,
versioning, bounded security claims, PPA cross-contract note); no
`src` / `scripts` / `pyproject` change since entry; exactly the two contract
files changed under `docs/contracts`; sibling contracts + schemas byte-unchanged;
no protected-root / helper-installation artifact; runtime posture unchanged;
`tasks/DECISIONS.md` records both adjudications.

The §33C / §38C / §42F / §42G / §42H functional guards and the HELPER-001
§6–§13 / §20 / §22 / §24 functional tests are **specifications for the
implementation phase and the dedicated N16-5-F-5-TB-CONTRACT-IV**, not tests
authored now (HPAC-PAWA-REQ-158 / 217 / 273 / 307 / 335 discipline).

---

## 10. Verification results

| Check | Result |
|---|---|
| `pcae check` | passed |
| `pcae health` | healthy |
| `pcae status coherence` | passed |
| `pcae doctor task-memory` | pre-existing DONE.md-omission warnings only (unrelated completed F-5-B2 tasks); no errors introduced |
| `pcae push check` | recorded in `.pcae/phase-completion-metadata.json` / `.pcae/phase-completion-report.md` |
| Contract-verification suite | **45 / 0** |
| Affected-guard A/B regression | **0 attributable regressions**; 40 pre-existing failures identical at baseline and HEAD |
| `git diff <entry 05056eeb> HEAD -- src/pcae scripts pyproject.toml` | **empty** |
| `git diff --name-only <entry> HEAD -- docs/contracts` | exactly `HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` (evolved in place) + `HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` (new) |
| Sibling contracts + `hpac_pawa_schemas.py` | byte-unchanged since entry |
| Live protected-host writes | **none** |
| Real ceremony | **NOT PERFORMED** |
| Runtime | `not_implemented` / `Observed` / `observe` / `unavailable` |
| Plugins / capabilities | 0 / 0 |
| First governed runtime external effect | **ABSENT / UNREACHABLE** |
| `origin/main..HEAD` (at finalization) | recorded post-push in the completion metadata |

---

## 11. Final canonical status (authorizing prompt §61)

| Field | Value |
|---|---|
| Full canonical Phase ID | `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1` |
| Display alias | N16-5-F-5-TB-CONTRACT |
| Predecessor canonical Phase ID | `…1.1.1` (alias N16-5-F-5-TB-ARCH) |
| Predecessor HEAD | `05056eeb` |
| CPIPC validation result | VALID (§0.3) |
| Previous HPAC-PAWA version | 1.4 |
| New HPAC-PAWA version | **2.0** |
| Version-classification rule | HPAC-PAWA-REQ-152 + REQ-153 + §80 → HPAC-PAWA-REQ-331 (S-4) |
| Version-classification result | **MAJOR** |
| Companion-contract decision | **B** — new companion |
| Companion contract name / version | **HPAC-PAWA-HELPER-001 v1.0** (FROZEN) |
| Exact normative sections changed | §7D (new); §32 / §33 / §33A / §33B / §36 / §37 / §42B / §42D / §49B / §68B / PAWA-INV-13 / PAWA-INV-14 (annotated **(v2.0)**, not deleted); §33C / §38C / §42F / §42G / §42H / §49C / §68C / §80.5 / §90.5 / §95D / §96D (new); §91 / §92 / §93 / §94 updated |
| Old same-process predicate disposition | §32 predicate 6 / §33 step 9 **SUPERSEDED by §33C**; **no** in-process fallback; physical removal of `_PINNED_*` / `_verified_production_caller_name` is a later governed slice; a compatibility shim MUST NOT preserve it |
| New consumer-authenticity conjunction | `TrustedProtectedAuthorityConsumer(request)` — 13 conjuncts (§33C / HPAC-PAWA-REQ-311); any conjunct fails → hard DENY; no single conjunct sufficient; no caller self-assertion |
| No-authority-export invariant | **PAWA-INV-15** (HPAC-PAWA-001) / **PAWAH-INV-1** (HPAC-PAWA-HELPER-001) |
| Single trust-root result | **preserved** — OS filesystem write authority on the out-of-band-provisioned protected root; helper registration is an integrity-pinned artifact of the existing kind; **PAWA-INV-17** / **PAWAH-INV-7**; no second root |
| Helper-provenance model | out-of-band immutable bytes + `helper_sha256` + owner / mode / type / no-symlink / one-hard-link + same-file-object exec + current-generation-anchor agreement + PAWA writer provenance (HPAC-PAWA-HELPER-001 §6) |
| Launcher role | enumerated standalone deployment-owner script; builds the request, integrity-verifies the helper, creates the private channel, `exec`s, sends one request, receives typed evidence; holds **no** authority object; possession ≠ authority (§38C / HPAC-PAWA-HELPER-001 §8) |
| Helper role | `exec`'d one-shot child; own interpreter; verifies peer credential; runs §33 1–8; validates the typed request; performs **exactly one** bounded operation; writes staged-then-finalized audit evidence; returns typed evidence; exits (§33C / HPAC-PAWA-HELPER-001 §4) |
| Peer-auth model | kernel-authenticated OS `(uid[, gid, pid])` of the channel peer = deployment owner **and** ≠ configured agent principal, bound to the channel, evaluated before admission; platform profiles `SO_PEERCRED` / `LOCAL_PEERCRED` / `getpeereid` (not assumed equivalent); OS peer credential ≠ human identity / approval (HPAC-PAWA-HELPER-001 §10 / PAWAH-INV-8) |
| Same-file-object / anti-TOCTOU property | the executed helper SHALL be the **same opened file object** whose properties were verified; no pathname re-open after validation; a platform without substitution-free exec **STOPS BLOCKED** (HPAC-PAWA-HELPER-001 §6.29) |
| Configured-agent identity rule | the negative boundary is evaluated against the configured PCAE agent principal resolved live from `HPAC-PAWA-AGENT-EXCLUSION/1.0` — never `os.geteuid()` / ambient root / a `SUDO_*` variable; `euid == 0` inside the helper mints nothing (§33C `ConfiguredAgentIdentityBindingValid` / HPAC-PAWA-HELPER-001 §7.32) |
| Operation vocabulary | closed: `admin_mutation` \| `certification_write` (role ∈ the closed five) \| `certification_read` (enumerated §42D set) \| `ceremony_entry` \| `presentation_evidence_write`; unknown / prefix / wildcard / unrecognized-version → DENY (§42F / HPAC-PAWA-HELPER-001 §13) |
| Four-factory replacement mapping | `production_writer` → `admin_mutation`; `certification_writer` → `certification_write`; `recognized_certification_read_authority` → `certification_read` + `ceremony_entry`; `mint_protected_presentation_evidence_writer` → `presentation_evidence_write` (invoked by the presentation helper itself) |
| Exact five-role mapping | `{ hpac_challenge_coordinator, hpac_assertion_recorder, human_authentication_proof_verifier, hpac_gate5_binder, hpac_rhamp_counter_state_verifier }` — closed allowlist reused verbatim; `hpac_lifecycle_terminator` excluded; per-role authority (§42B / HPAC-PAWA-REQ-247) byte-unchanged in substance |
| Typed-read model | enumerated closed §42D record set for the bound session; record **contents** returned, not a store handle; repeated reads SHALL NOT reconstruct unrestricted store authority; no arbitrary path / key / table / dump / OS secret / FIDO2 PIN (HPAC-PAWA-HELPER-001 §15) |
| Ceremony-entry model | a separate typed operation that only hands the canonical ceremony request to the HPAC-PPA-001 presentation helper for exactly one ceremony; returns an acknowledgement, never the outcome; every wall verbatim (HPAC-PAWA-HELPER-001 §16) |
| Presentation-evidence write model | the existing `mint_protected_presentation_evidence_writer` semantics restated as a helper operation invoked by the presentation helper itself; sole author of `HPAC-PRESENTATION-EVIDENCE/2.0` unchanged; cannot self-assert `approved` / `verified` / `human_present` / `authenticated` (HPAC-PAWA-HELPER-001 §17) |
| Freshness / replay model | `expiry` (trusted clock) + CSPRNG ≥ 256-bit nonce; fresh / consumed / duplicate / expired / unknown / conflicting-replay dispositions; a lost response never frees a spent one-shot request (HPAC-PAWA-HELPER-001 §18 / §19) |
| State-transition model | `REQUEST_RECEIVED → REQUEST_AUTHENTICATED → OPERATION_ADMITTED → MUTATION_ATTEMPT_STARTED → MUTATION_COMMITTED → EVIDENCE_WRITTEN → RESPONSE_EMITTED`; durable = `MUTATION_COMMITTED` / `EVIDENCE_WRITTEN`; `MUTATION_ATTEMPT_STARTED` = the no-auto-retry boundary (HPAC-PAWA-HELPER-001 §20) |
| Crash / uncertainty model | per-state disposition table; a crash after commit before evidence finalize = **INDETERMINATE / RECONCILIATION REQUIRED** (a BLOCKED reconcile condition, never a silent success, never an auto-retry); response absence is never proof; unknown stays unknown until reconciled against the durable protected-root record (HPAC-PAWA-HELPER-001 §21) |
| Audit-write ordering | **model A** — evidence durably staged **before** `MUTATION_ATTEMPT_STARTED` (staged-write failure aborts before any mutation), finalized after commit; a crash between commit and finalize is a detectable reconciliation condition. The phrase "audit failure means the mutation did not occur" is **not** frozen; the **ordering** that makes a pre-mutation staged-evidence failure abort is (HPAC-PAWA-HELPER-001 §22) |
| Non-bearer / restart-dead semantics | process-boundary properties (§49C / HPAC-PAWA-HELPER-001 §49C / PAWAH-INV-10); the helper process and any authority it held are gone at exit; a fresh launch re-runs the entire recognition |
| Generic-broker prohibition | HPAC-PAWA-HELPER-001 §25 / PAWAH-INV-5; no arbitrary filesystem / command / shell / Python / store-method / role-mint / registry / secret / process-launch; `operation_params` a closed typed struct per operation |
| Human-authentication / approval separation | every wall of §67 / §68 / §68A / §68B / §14 / §20 of `TB-ARCH` preserved verbatim (§68C); OS peer credential ≠ human identity / approval; ceremony entry ≠ APPROVE / Gate 5 / PB permission / execution; YubiKey touch = UP ≠ approval |
| Mechanism-neutral / mobile result | HPAC-PAWA-HELPER-001 §27 — no YubiKey / FIDO2 / USB / AAGUID / TTY hardcoded; a future mobile-only / passkey path stays open; local TTY / physical YubiKey not a prerequisite for ordinary development |
| PB / POL / runtime / effect non-expansion | §68C / HPAC-PAWA-HELPER-REQ-003 — no PB permission, policy exception, RE result, `DispatchEnvelope`, adapter admission, Gate result, runtime capability, or execution; POL-005 hard DENY unchanged; runtime `Observed` / `observe` / `unavailable`, 0 / 0; first external effect ABSENT / UNREACHABLE |
| Security claim boundaries | protects against ordinary same-interpreter compromise, malicious plugin, `gc` introspection, `import` / `sys.modules` manipulation, ordinary configured-agent account, protocol replay, fake helper, forged launcher, forged request fields; does **not** claim protection against hostile root / admin, compromised kernel, compromised registered helper binary after an authorized mutation, whole-snapshot restore, or a single-account host (HPAC-PAWA-HELPER-001 §26.2) |
| Cross-contract impact | HPAC-001 v2.1 / RHAMP-001 v1.0 / HPAC-PPA-001 v1.0 / HBDC-001 v1.2 / RIHAC-001 v2.0 / RIASC-001 v3.0 / RDGO-001 v3.1 / schemas — **byte-unchanged**; one HPAC-PPA-001 evidence-writer-delivery question deferred to the IV, and a fresh HPAC-PPA-001 successor if it needs a normative change |
| Files changed | `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md` (v1.4 → v2.0, in place); `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md` (new); `tests/test_…_n16_5_f_5_tb_contract.py` (new, 45/0) + 17 downstream guard-reconciliation test files; `tasks/DECISIONS.md`; `PROJECT_STATUS.md`; `CHANGELOG.md`; `tasks/**`; `.pcae/phase-completion-*` |
| Production source changes | **none** (`src/pcae` / `scripts` / `pyproject.toml` diff empty since entry) |
| Tests / contract guards run | contract-verification suite 45/0; affected-guard A/B regression (gsel + PPA + N-16-3/4 + v1.1-meta) — 0 attributable regressions |
| Broader regression tally | 40 pre-existing point-in-time / protected-root-presence failures, node-for-node identical at baseline `05056eeb` and HEAD (unrelated completed phases; a verification phase re-baselines them) |
| Attributable regressions | **0** |
| Live protected-host writes | **none** |
| Real ceremony | **NOT PERFORMED** |
| Runtime state | `not_implemented` / `Observed` / `observe` / `unavailable` |
| Plugin / capability counts | 0 / 0 |
| First external effect | **ABSENT / UNREACHABLE** |
| `pcae_check` | passed |
| `pcae_health` | healthy |
| `pcae_push_check` | recorded in the completion metadata / report |
| `pcae_status_coherence` | passed |
| `doctor / task-memory` | pre-existing DONE.md-omission warnings only; no errors introduced |
| Completion notification | dispatched by `pcae phase complete` (Telegram runtime loaded; no fabricated credentials) |
| `origin/main..HEAD` | 0 after push (recorded in the completion metadata) |
| F-5-B2 status | **BLOCKED** pending contract IV + implementation |
| F-5 status | **CERTIFICATION BLOCKED** |
| N-16-5 status | **NOT CLOSED** |
| N-16-6 / N-16-7 status | **OPEN / UNTOUCHED**; N-16-7 strictly last |
| Recommended contract-IV successor | **N16-5-F-5-TB-CONTRACT-IV** — dedicated independent verification of HPAC-PAWA-001 v2.0 **and** HPAC-PAWA-HELPER-001 v1.0 together (§80.5 / HPAC-PAWA-REQ-330; required, **not** foldable) |
| Successor NOT begun | **Confirmed** — N16-5-F-5-TB-CONTRACT-IV, the helper + protocol implementation, caller integration, in-process-path removal, packaging / clean-install, the security IV, deployment, and a fresh N16-5-FINAL-CERT are all **derived, NOT begun**; each requires its own explicit human authorization. N-16-6 / N-16-7 not begun. No first external effect implemented or called. Execution not enabled. |

---

## 12. Historical governance integrity

Preserved exactly, no retroactive authorization or reinterpretation:

```
N16-5-F-5-B2       : NOT VERIFIED / BLOCKED
N16-5-F-5-B2R-IV   : NOT VERIFIED / BLOCKED
N16-5-F-5-B2R2-IMPL: COMPLETE — BLOCKED
N16-5-F-5-TB-ARCH  : COMPLETE
DELEGATED .3 FINALIZATION / COMMIT / PUSH : UNAUTHORIZED
```

Historical HPAC-PAWA-001 v1.0 / v1.1 / v1.2 / v1.3 / v1.4 freeze records and
their independent verifications remain **immutable**; v2.0 is append-only.

---

## 13. Delegated-worker rule

No delegated workers were used in this phase; all repository-state inspection,
predecessor confirmation, CPIPC derivation, HPAC-PAWA-001 v1.4 baseline
reconstruction, version-classification and companion-contract adjudication,
normative drafting, cross-reference review, guard reconciliation, and
contract-verification authoring were performed directly by the primary operator
session. Had any been delegated, the constraints (no finalize / mutate canonical
status / commit / push / mutate protected host / install / authenticate /
certify; primary operator independently adjudicates) would apply, and
`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` remains an immutable
historical outcome.

---

## 14. REPORTING-UX-1

The architecture-status current-phase display parser limitation
(**REPORTING-UX-1**) remains **open and non-blocking**. Canonical phase identity
and metadata for this phase were verified independently via `pcae.core.phase_id`
and direct artifact inspection (§0). This phase does **not** expand into parser
repair. REPORTING-UX-1 is **recorded as still present**.

---

## 15. Absolute stop boundary

This phase ends at **contract freeze**. It does **not**, and no successor may
without its own fresh human authorization: begin N16-5-F-5-TB-CONTRACT-IV;
implement the helper / launcher / IPC; migrate caller integration; remove the
in-process authority path; package / install the helper; mutate PAWA / PPA
production state; perform protected-host writes; begin deployment; begin final
certification; request a FIDO2 PIN or YubiKey touch; launch protected approval;
create a production challenge; issue real proof; mutate live counter state;
issue a PRODUCTION principal; perform Gate-5 final certification; close N-16-5;
begin N-16-6; begin N-16-7.

---

## Canonical evidence

- Phase ID CPIPC derivation: `pcae.core.phase_id` (§0.3).
- Predecessor state: `PROJECT_STATUS.md`, `.pcae/phase-completion-metadata.json`,
  `docs/PHASE_N16_5_F_5_TB_ARCH.md`, `tasks/done/20260910-0236-…md`.
- Contract baseline: `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  at `05056eeb` (HPAC-PAWA-001 v1.4) §4 / §5 / §7C / §8 / §32 / §33 / §33A /
  §33B / §36–§39 / §41 / §42B / §42D / §49B / §60 / §68 / §68A / §68B / §80.4 /
  §90.4 / §91 / §92 (PAWA-INV-1..14) / §94 / §95C / §96C;
  `docs/contracts/HPAC_PROTECTED_PRESENTATION_AUTHORITY_CONTRACT.md`
  (HPAC-PPA-001 v1.0) §1 / §2 / §6 / §7 / §19.
- Frozen evolution: `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`
  (HPAC-PAWA-001 v2.0) §7D / §33C / §38C / §42F / §42G / §42H / §49C / §68C /
  §80.5 / §90.5 / §95D / §96D / PAWA-INV-15..17;
  `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`
  (HPAC-PAWA-HELPER-001 v1.0).
- Adjudications: `tasks/DECISIONS.md` — "Phase 149O…1.1.1.1 (alias
  N16-5-F-5-TB-CONTRACT)".
- Contract-verification suite: `tests/test_phase_149o_…_n16_5_f_5_tb_contract.py`
  (45/0).
- Runtime posture: `pcae runtime inspect` — `not_implemented` / `Observed` /
  `observe` / `unavailable` / 0 / 0.
- `git diff 05056eeb HEAD -- src/pcae scripts pyproject.toml` — **empty**;
  `git diff --name-only 05056eeb HEAD -- docs/contracts` — exactly the two
  contract files.

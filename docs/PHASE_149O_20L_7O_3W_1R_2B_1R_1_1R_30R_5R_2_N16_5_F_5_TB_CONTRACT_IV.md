# Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1 — Independent Verification of HPAC-PAWA-001 v2.0 and HPAC-PAWA-HELPER-001 v1.0

- **Phase:** `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1`
- **Alias:** **N16-5-F-5-TB-CONTRACT-IV** (operator readability only; the full canonical CPIPC id is authoritative in task state, lifecycle, reports, completion metadata, evidence, and canonical project status)
- **Predecessor:** **N16-5-F-5-TB-CONTRACT** (`149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1`) — COMPLETE / CONTRACT FROZEN
- **Predecessor HEAD:** `3cdc3c089e5f8952b0d46b7c95b6c6bf580754e8` (also this phase's entry HEAD; `origin/main..HEAD` = 0; tree clean)
- **Type:** dedicated contract Independent Verification (HPAC-PAWA-REQ-330; a MAJOR always carries its own IV, §80 / §80.5 — folding is NOT permitted). Contract-verification only — no production source, no `scripts/`, no `pyproject.toml`, no schema, no protected-host interaction, no ceremony.

## OVERALL CONTRACT-IV VERDICT

**N16-5-F-5-TB-CONTRACT-IV: COMPLETE — NOT VERIFIED / BLOCKED.**

The blocker is a single, mandatory, cross-contract determination that the
authorizing prompt (§25 / §45) forbids leaving "deferred":

- **HPAC-PPA-001 EVIDENCE-WRITER ADJUDICATION: B — HPAC-PPA-001 CONTRACT
  EVOLUTION REQUIRED.**

HPAC-PAWA-HELPER-001 v1.0 §17 (HPAC-PAWA-HELPER-REQ-070) freezes the
`presentation_evidence_write` operation — one of the five closed operation-
vocabulary members — as *"invoked **by the HPAC-PPA-001 presentation helper
itself**"*. HPAC-PPA-001 v1.0, byte-unchanged, states the opposite in
normative text:

| HPAC-PPA-001 v1.0 clause | Verbatim | Conflict with v2.0 `presentation_evidence_write` |
|---|---|---|
| HPAC-PPA-REQ-041 | the evidence-writer capability is *"held only by the trusted launcher mediator … **never sent to the helper** or requesting caller"* | v2.0 mints and holds it **inside the presentation helper** |
| HPAC-PPA-REQ-054 | *"Evidence producer is **only** the launcher mediator after a response from the verified helper"* | v2.0 makes the **helper** the evidence producer |
| HPAC-PPA-REQ-052 | the evidence-writer **issuer** is `pcae.core.protected_presentation` (the launcher/mediator), a **distinct module** from `pcae.protected_presentation_helper` | v2.0 collapses the write into the helper process |
| PPA-INV-2 | *"Installer, launcher, **helper response**, and **evidence writer** are **distinct trust actions with no authority transfer**"* | v2.0 merges the "helper response" and "evidence writer" trust actions into one actor |
| HPAC-PPA-REQ-069 (MAJOR triggers) | *"allowing caller-selected … writer; merging PAWA and runtime evidence authority; or transferring authority into … requires a new MAJOR"* | moving the writer-holder is a MAJOR-class change for HPAC-PPA-001 |
| HPAC-PPA-REQ-070 (MINOR permits) | *"add a platform adapter **within these exact properties**, tighten a bound, or add a failure mapping"* | the properties themselves ("held only by the launcher mediator", "never sent to the helper", "distinct trust actions") are what change — this is **not** a within-properties adapter |

The HPAC-PAWA-HELPER-001 §17 cross-contract note argues option (a) — that
this is within HPAC-PPA-REQ-041's *"or repository-equivalent use of the same
existing capability/provenance primitive"* and HPAC-PPA-REQ-070's platform-
adapter permit, since the authority moves *further* from the agent
interpreter. That reading does not survive independent scrutiny: REQ-041's
parenthetical governs *which primitive* is used, not *who holds it*; the
"held only by the trusted launcher mediator … never sent to the helper"
clause is a separate, explicit, unconditional constraint on the holder;
PPA-INV-2 is re-meant, not merely adapted. The authorizing prompt (§13, §38)
requires a MAJOR contract IV not to "paper over a normative contradiction …
with vague 'equivalent' language". HPAC-PAWA-HELPER-001 §17 itself records
the question as unresolved and defers it; the prompt (§25, §45) forbids
deferral and requires exactly A or B.

The v2.0 `presentation_evidence_write` design is the *correct* security
direction — HPAC-PPA-001 v1.0's launcher-mediator evidence writer is an
in-interpreter `HPACWriterCapability` with the **same `gc`-reachability
vulnerability** the whole N-16-5 F-5 line exists to eliminate. But
HPAC-PPA-001 v1.0 as frozen does **not** authorize moving it out of process,
and its REQ-041 / REQ-054 / REQ-052 / PPA-INV-2 forbid it. The fix is
well-scoped and small: a fresh governed HPAC-PPA-001 successor that moves its
evidence-writer authority into the verified presentation helper, aligned with
HPAC-PAWA-001 v2.0 §42F / HPAC-PAWA-HELPER-001 §17, explicitly re-meaning
REQ-041 / REQ-054 / PPA-INV-2 rather than silently.

Per §45 of the authorizing prompt: **option B ⇒ this IV is COMPLETE — NOT
VERIFIED / BLOCKED**, and the required successor is a **fresh governed
HPAC-PPA-001 contract-evolution phase** (derived, **NOT begun** — each
successor requires its own explicit human authorization).

HPAC-PAWA-001 v2.0 and HPAC-PAWA-HELPER-001 v1.0 are **not defective** in the
PAWA-side authority model — every other load-bearing IV criterion below was
independently established. The block is the un-adjudicated HPAC-PPA-001
dependency of one vocabulary member. This IV does **not** edit any normative
contract.

---

## Section 0 — Governance / phase identity

- **Current branch:** `main`. **HEAD:** `3cdc3c089e5f8952b0d46b7c95b6c6bf580754e8`. **origin/main:** `3cdc3c08` (equal). **`origin/main..HEAD`:** 0. **Tree:** clean. **No conflicting active governed phase** (only the post-CONTRACT idle task was active at entry).
- **Predecessor completion confirmed** from: `PROJECT_STATUS.md` ("STATUS: N16-5-F-5-TB-CONTRACT COMPLETE — CONTRACT FROZEN"); `.pcae/phase-completion-metadata.json` (`phase_id` == the predecessor canonical id, `status: "completed"`); `.pcae/phase-completion-report.md` (title "Phase … Complete"); the governed done task; `git log` (`c9bbd92e` HPAC-PAWA-001 v1.4 → v2.0 + companion freeze, `3cdc3c08` finalize).
- **CPIPC result — VALID.** Independently re-derived via `pcae.core.phase_id`:
  `is_valid` True; `validate` returns no error; `format(parse(candidate)) == candidate`; `compare(predecessor, candidate) == "less"`; `same_series` (`149`) True; `same_branch` (`O`) True; exactly one appended `.1` subphase segment (predecessor 50 subphase segments → 51); exact canonical text; absent from `git log --all` and from `git grep -F` over `docs/` / `tasks/` / `.pcae/`; reuses no completed or blocked phase id; no parallel numbering. **Canonical Phase ID recorded verbatim** in this report, the staging report, `PROJECT_STATUS.md`, `CHANGELOG.md`, `.pcae/phase-completion-metadata.json`, `tasks/DECISIONS.md`, and the task lifecycle. Alias `N16-5-F-5-TB-CONTRACT-IV` is display-only (hyphenated — the CPIPC token scanner extracts no stray `<digit><letter>` phase token).

## Section 1 — Byte baselines

- **HPAC-PAWA-001 v2.0** — `docs/contracts/HPAC_PRODUCTION_PROTECTED_ADMIN_WRITER_ANCHOR_CONTRACT.md`, blob `c5bf6dc1935e4e0d76efbe9a94453fee153e8ce3`, 5440 lines, header `# HPAC-PAWA-001 v2.0 —`, `**Version:** 2.0`, `**Status:** FROZEN`. Requirement ids **contiguous `HPAC-PAWA-REQ-001` … `HPAC-PAWA-REQ-340`**, no gaps, no duplicates (340). v2.0 additions are exactly `HPAC-PAWA-REQ-310` … `HPAC-PAWA-REQ-340` (v1.4 max was 309). Invariants **`PAWA-INV-1` … `PAWA-INV-17`**, each defined once (`-15` / `-16` / `-17` added at v2.0). Every v1.0–v1.4 requirement body survives verbatim (append-only; `(v2.0) … SUPERSEDED` / `delivery superseded — substance unchanged` notes appended in place, no id deleted or renumbered). All historical freeze verdicts (v1.1 / v1.3 / v1.4 MINOR; §80.4 / §90.3 / §90.4) intact.
- **HPAC-PAWA-HELPER-001 v1.0** — `docs/contracts/HPAC_PAWA_PROTECTED_HELPER_PROTOCOL_CONTRACT.md`, blob `bbf8c1d3f9e8979ec92febe724f1da553fd82dad`, 1327 lines, header `# HPAC-PAWA-HELPER-001 v1.0 —`, `**Version:** 1.0`, `**Status:** FROZEN — IMPLEMENTATION AND INDEPENDENT VERIFICATION PENDING`. Requirement ids **contiguous `HPAC-PAWA-HELPER-REQ-001` … `HPAC-PAWA-HELPER-REQ-114`**, no gaps, no duplicates (114). Invariants **`PAWAH-INV-1` … `PAWAH-INV-10`**, each once. Independent `HPAC-PAWA-HELPER-REQ-*` namespace (HPSE-001 / RHAMP-001 / HPAC-PPA-001 precedent). Every cross-reference to HPAC-PAWA-001 / HPAC-PPA-001 / HPAC-001 / RHAMP-001 resolves.
- **`git diff --name-only 3cdc3c08 HEAD -- docs/contracts`** — **empty** (this IV edits no contract byte).
- **Sibling contracts byte-unchanged** since the HPAC-PAWA-001 v2.0 freeze commit (`c9bbd92e`), verified by `git diff --name-only`: HPAC-001 **v2.1** (blob `16509b6b…`); RHAMP-001 **v1.0** (`ef218e99…`); HPAC-PPA-001 **v1.0** (`3832eb92…`); HBDC-001 **v1.2** (HATP Class-B Deployment Contract); RIHAC-001 **v2.0** (`9cce2e77…`); RIASC-001 **v3.0** (`5256b0cc…`); RDGO-001 **v3.1** (`8cb4894f…`). Protected-root schemas (`HPAC-PAWA-AUTHORITY-DESCRIPTOR/1.0`, `HPAC-PAWA-CURRENT-GENERATION/1.0`) are defined in the (unchanged) sibling / contract text; `schemas/` tree unchanged. **No unexpected normative sibling-contract change found** — the only two files changed `05056eeb..HEAD` are HPAC-PAWA-001 (in place → v2.0) and the new HPAC-PAWA-HELPER-001.

## Section 2 — MAJOR version classification — **VERIFIED**

**MAJOR CLASSIFICATION VERIFIED (S-4).** Independently re-walked:

- **Governing rule:** `HPAC-PAWA-REQ-152` (verbatim MAJOR triggers) read with `HPAC-PAWA-REQ-153` (the **closed** MINOR-permit enumeration) and §80. `HPAC-PAWA-REQ-153` was **not** widened by v2.0 (a MAJOR does not expand the MINOR permits).
- **Outside every §153 MINOR permit.** §153 permits: re-state verified behaviour; add a `pawa_failure_code` without re-meaning; add an authorized-consumer **category** by explicit enumeration; **tighten** (never loosen) a bound; clarify a platform-adapter detail; add a macOS/Linux adapter within §63 frozen properties; add **one** explicitly enumerated protected-admin **metadata mutation family** (target inside the protected root, executable bytes + runtime evidence outside PAWA, capability process-local/non-bearer/one-op, no §152 trigger). v2.0 **replaces a normative recognition predicate** (§32 predicate 6 / §33 step 9 — "the calling module is an authorized factory consumer") and **restructures the authority-delivery model** of §36–§38 / §41 / §42B / §42D / §33B (in-process factory returns a handle → out-of-process helper returns typed evidence). §153's closing clause *"provided no meaning above changes"* is **not** satisfied — the meaning of §32, §33, §36–§38, §41, §42B, §42D, §46, §49B, PAWA-INV-13, PAWA-INV-14 changes.
- **"Replacing an unsound predicate with a stronger one is a §153 'tighten a bound'" — rejected.** A tightening keeps the *same* predicate and narrows its acceptance set. v2.0 substitutes a *structurally different* out-of-process predicate that changes *which OS actor performs the operation*. Independently concur with `HPAC-PAWA-REQ-331`.
- **`configure_privileged_helper` alone** would be a permissible §153 metadata-mutation family (the `configure_presentation_mechanism` / HPAC-PPA-001 v1.2 precedent). It rides along with the MAJOR; it does not by itself force MAJOR.
- **§152 verbatim-trigger review — none fires literally** (independently checked each): `sudo`/`euid`/env-var sufficient — **no** (`euid == 0` inside the helper mints nothing, HPAC-PAWA-HELPER-REQ-032); collapse/remove configured-agent exclusion — **no** (preserved, executed inside the helper, §33C `ConfiguredAgentIdentityBindingValid`); same-principal agent/deployment-owner topology — **no** (two-principal preserved; single-account host → REAL issuance ineligible / fail closed); **remote/network/cloud authority service or transport** — **no** (the one-shot channel is a **local** private parent/child pipe or `AF_UNIX` socket beneath the protected root — the closest call, correctly not triggered; a network authority service was explicitly rejected — §95D); writer capability bearer/durable/serialisable/reusable — **no** (strengthened; non-bearer / restart-dead become process-boundary properties, §49C); broaden capability into runtime approval / PB / RE / runtime capability / execution — **no** (§68C; path terminates at the bounded Gate-5 assurance result); change the bootstrap trust root — **no** (unchanged OS filesystem write authority, PAWA-INV-17); remove `generation` / rollback-prevention — **no** (reused; helper registration generation-bound); **add a signing key / pinned key / keychain requirement as an authority input** — **no** (the second-closest call — `helper_sha256` is a byte-hash *content-integrity digest* of an OS-protected executable, the same construct already used for the descriptor / agent-exclusion / anchor, and it is defense-in-depth *in addition to, never a substitute for* the filesystem properties, PAWAH-INV-3 — not an asymmetric verification/authority key); widen the authorized-consumer inventory by wildcard/prefix/glob — **no** (exact enumeration preserved; consumer identity **replaced by the stronger** "was `exec`'d from the verified helper executable" property; §38C same standalone scripts).
- **Verdict:** MAJOR (S-4) is not merely defensible — it is the **only** sound classification. `HPAC-PAWA-REQ-333` extends the MAJOR trigger set for v2.0 coherently. **A dedicated IV is mandatory** (§80 / §80.5 / `HPAC-PAWA-REQ-330`; not foldable) — this phase is that IV.

## Section 3 — §33C `TrustedProtectedAuthorityConsumer` conjunction — **VERIFIED (exact, fully fail-closed, no single conjunct sufficient)**

`HPAC-PAWA-REQ-311` composes the frozen replacement for §32 predicate 6 / §33
step 9 as a **13-conjunct AND**, admitted **iff ALL** hold, failure of **ANY**
a hard **DENY / fail-closed** (§42H), **no** single conjunct sufficient, **no**
caller self-assertion, **no** in-process fallback:

| # | Conjunct | Proves | Does NOT prove | Failure disposition (§42H) | Caller-controlled? | Bypassable by another conjunct? |
|---|---|---|---|---|---|---|
| 1 | `RegisteredGenerationMatch` | this helper file is the canonically registered helper for the active generation (§42G) | byte integrity (#3); that it is running | `unauthorized_factory_consumer` (#15) | no — PAWA-writer-provenance'd metadata under the protected root | no |
| 2 | `ProtectedHelperFilesystemPropertiesValid` | admin-owned / mode 0755 / regular / one hard link / no-symlink chain | byte integrity; provenance | #15 | no | no — "in addition to, never a substitute for" the digest (PAWAH-INV-3) |
| 3 | `HelperIntegrityBindingValid` | SHA-256 of the **opened** bytes == registered `helper_sha256` | that the same file is `exec`'d (#4); peer identity | #15 | no | no |
| 4 | `VerifiedExecutionObjectValid` | the same opened file object is `exec`'d — no pathname re-open gap; a platform without substitution-free exec **STOPS BLOCKED** | peer identity | #15 | no | no — closes the TOCTOU window #3 alone leaves |
| 5 | `ProtectedProcessPrincipalValid` | the helper runs under the deployment-owner OS principal | that the channel peer is the owner (#7) | #15 | no | no |
| 6 | `PrivateChannelValid` | the one-shot channel was established through an approved §38C launcher path, not inherited by / reachable to any agent-principal process | consumer authenticity | `unauthorized_factory_consumer` / `current_context_is_agent` (#15 / #5) | no | no — "possession of the channel fd alone is not authority" (`HPAC-PAWA-REQ-312`) |
| 7 | `PeerCredentialValid` | the **kernel-authenticated** OS `(uid[, gid, pid])` of the channel peer is the deployment owner **and not** the configured agent principal, bound to this channel | human identity / approval / presence (§68C) | #15, or #5/#6 | **no** — obtained from the kernel, never a peer-supplied field | no |
| 8 | `PAWAOSRecognitionValid` | §33 steps 1–8 pass **inside the helper** (root resolution, agent exclusion, negative boundary, `{device, inode}`, descriptor, current generation, not-configured-agent, `O_EXCL\|O_NOFOLLOW` write probe) | operation validity | its exact existing §56 code (#1–#14) | no | no (PAWA-INV-3 — atomic recognition unit) |
| 9 | `ConfiguredAgentIdentityBindingValid` | the configured agent identity resolved **live** from `HPAC-PAWA-AGENT-EXCLUSION/1.0` — used for the negative boundary, **never** `os.geteuid()` / ambient root / `SUDO_*` | that a human authorized anything | #5 / #6 | no | no — F-1 / F-5-B1 preserved and executed inside the helper (HPAC-PAWA-HELPER-REQ-032) |
| 10 | `RequestSchemaValid` | `HPAC-PAWA-HELPER-REQUEST/1.0` — closed schema, self-excluding `request_digest`, unknown field fails closed | admissibility (needs #11–#13 too) | `operation_scope_invalid` (#16) | fields are caller-supplied but **carry no authority** (HPAC-PAWA-HELPER-REQ-048) | no |
| 11 | `ClosedOperationMembershipValid` | `operation ∈` the closed §42F / HELPER §13 vocabulary **and** `∈` this build's `supported_operations`; unknown / prefix / wildcard / unrecognized version → DENY | that the subject binding is valid (#12) | #16 | validated, not asserted | no |
| 12 | `OperationSpecificAuthorityPredicatesValid` | `role ∈` the closed §42B five-role allowlist (for `certification_write`); the exact §42 mutation class; the enumerated §42D record; session / subject binding | freshness (#13) | `target_scope_invalid` (#17) | validated against canonical stores | no |
| 13 | `FreshnessAndReplayPredicatesValid` | within `expiry`; nonce (CSPRNG ≥ 256 b) fresh; `(request_id, nonce)` not consumed / not a conflicting replay | anything else | `capability_stale` (#18) / `target_scope_invalid` (#17) | no | no — evaluated regardless of every other conjunct passing (HPAC-PAWA-HELPER-REQ-074) |

- **`HPAC-PAWA-REQ-312` — consumer authenticity vs IPC access, not conflated.** None of {a channel connection; possession of the channel fd; `euid == 0` / `sudo` / a `SUDO_*` variable inside the helper; an environment variable; the helper executable path; the helper hash alone; the launcher's identity alone; the peer credential alone; a socket / process existing} is, in whole or in part, on its own the positive recognition predicate. **NO SINGLE CONJUNCT IS SUFFICIENT AUTHORITY** (PAWA-INV-16 / PAWAH-INV-2; HPAC-PAWA-HELPER-REQ-012).
- **`HPAC-PAWA-REQ-313`** — §33C runs **fresh on every `exec`**; no result cached across processes; the helper process (and any capability it minted internally) is gone at exit; a second operation re-runs the entire §33C + §33 1–8 sequence in a fresh helper process.
- **`HPAC-PAWA-REQ-314`** — the sequence **fails closed**: any failed conjunct → the corresponding §56 code (§42H); no operation, no read view, no ceremony; recorded with the HELPER §22 evidence-staged-before-mutation ordering; *"the absence of a denial is never authority"*.

## Section 4 — Same-interpreter production predicate — **ELIMINATED (VERIFIED)**

- §32 `HPAC-PAWA-REQ-073` predicate 6 and §33 step 9 are **SUPERSEDED by §33C**. The predecessor phase kept every v1.0–v1.4 requirement **body byte-verbatim** (commit `b34cc348` explicitly *"revert transient mid-list contract edit to keep every v1.x REQ body verbatim"*): the supersession is expressed only as **appended** notes — the §32 note (`SUPERSEDED by §33C`), the `HPAC-PAWA-REQ-075` / §33A / §33B notes (*"Step 9 is replaced per §33C step 9′"*), the §7D delta table, and §33C `HPAC-PAWA-REQ-311` — never a mid-body edit. Under v2.0 the trusted production consumer is **not a calling module** — it is the distinct short-lived protected helper process. This append-only discipline is itself a positive IV finding (no v1.x normative body was reworded to force the MAJOR through).
- `HPAC-PAWA-REQ-315` — **no in-process authority object and no in-process recognition predicate**: under v2.0 the ordinary PCAE interpreter contains **no** `HPACWriterCapability` / `HPACStoreAuthority` / `CertificationReadAuthority` / `ProductionWriterHandle` for any `PRODUCTION` class, and the recognition predicate is **not** `_verified_production_caller_name` / `_detect_caller_module` / the `_PINNED_*` dicts / an in-process `_PRODUCTION_WRITER_FACTORY_SEAL` identity check. The predecessor bypass PoCs (`gc`-reachability, `exec`-into-`__dict__`, closure capture) target a mechanism that **no longer bears authority**.
- `HPAC-PAWA-REQ-316` — trust rests on OS process isolation + OS filesystem permissions + OS peer credentials + out-of-band executable provenance, and on **none** of: Python underscore privacy; module / function name; `__module__` / `__file__`; `inspect.stack()` textual identity; `sys.modules` keys; mutable module globals; closure hiding; class-private state; in-process bearer-object possession; a filesystem path alone; digest consistency alone.
- **No hidden normative fallback remains.** Search of the assembled v2.0 text for any *production* authority still depending on calling-module name / `inspect.stack` / in-process seal possession / module globals / `sys.modules` identity / a caller-provided consumer string / a returned writer handle: the only such references are (a) the superseded §32 / §33 clauses, explicitly annotated `SUPERSEDED`, and (b) the description of the in-process mechanism marked for physical removal in a later governed slice with the hard rule *"a compatibility shim MUST NOT preserve the insecure in-process authority path"* (appears **≥ 3×** across §7D / §36 note / §33C / §94 / §96D). The in-process mechanism's *physical* presence in `src/pcae` is not removed by the CONTRACT phase or by this IV — but the **normative text** no longer sanctions it as a production authority root.

## Section 5 — No authority-object export — **VERIFIED**

- **PAWA-INV-15** (and HELPER §24 / PAWAH-INV-1): **no production privileged authority object crosses from the protected helper process into the standalone launcher or the ordinary PCAE interpreter** — by name (`HPACWriterCapability`, `HPACStoreAuthority`, `CertificationReadAuthority`, `ProductionWriterHandle`, the §42B certification-lifecycle capability, the `mint_protected_presentation_evidence_writer` output, any generic writer / authority object) **and by semantic equivalence** ("any transferable object whose possession enables an equivalent privileged operation", "any 'capability token', opaque handle, serialized seal, or **reconstructable field set** from which a bearer writer could be recreated outside the helper").
- **PAWA-INV-16** restates the §33C conjunction as the consumer-authenticity definition; **PAWA-INV-17** the single-root / distinct-evidence rule.
- **Generic bearer-equivalent search** (§7 of the prompt): the caller receives **only** `decision` (`PERFORMED` / `REJECTED` + an existing `pawa_failure_code` `terminal_code`), `evidence_ref` / `evidence_digest`, and — for `certification_read` / `ceremony_entry` — `result_payload` = the enumerated §42D record **contents** / a ceremony-entry acknowledgement. `HPAC-PAWA-REQ-323`: *"Nothing else."* `HPAC-PAWA-HELPER-REQ-092`: *"There is **no** 'capability token' workaround that recreates a bearer writer outside the helper."* A new opaque id / token that reconstructs a generic privileged handle is covered by the "reconstructable field set" clause and by `reconstruction_attempt` (#20). **Typed result / evidence ≠ transferable privileged authority — VERIFIED.**
- **Protected side owns the operation** (`HPAC-PAWA-REQ-321` / `-325`; HELPER §8 / §24 / HPAC-PAWA-HELPER-REQ-093): request → helper admission (§33C) → **helper performs the exact operation in its own process** → typed evidence returned → helper exits. The rejected model ("caller asks for a privileged writer → writer object returned → caller invokes methods later") is *"no longer a production boundary"*. Every privileged mutation / read / ceremony-entry action terminates inside the protected boundary; **no delayed generic privilege delegation.**

## Section 6 — Closed operation vocabulary — **VERIFIED**

- Exactly five closed members (HELPER §13 `HPAC-PAWA-HELPER-REQ-052` / `-053`; §42F `HPAC-PAWA-REQ-324`): `admin_mutation` | `certification_write` (role ∈ the closed five) | `certification_read` (over the enumerated §42D record set) | `ceremony_entry` | `presentation_evidence_write`. Each has a stable operation id, an exact `operation_version`, an exact permitted consumer context, exact preconditions, exact state reads / writes, an exact typed `operation_params` struct, an exact result, exact evidence, exact failure semantics, a replay / single-use rule, and an audit rule.
- **Unknown operation → DENY. Unrecognized operation version → DENY. Prefix / wildcard / extension matching → DENY.** No generic file write, command, expression, store-method dispatch, role mint, registry edit, secret retrieval, process launch, "run this operation by name", or "apply this JSON patch" entry point (PAWAH-INV-5; §25 `HPAC-PAWA-HELPER-REQ-094`).
- `operation_params` is a **closed typed struct per operation** — *"never a free path string, expression, shell command, module name, JSON-patch blob, or executable path"*.
- **`supported_operations` gating** (`HPAC-PAWA-HELPER-REQ-054`): a valid §13 member that the current registered generation does not implement fails closed (`operation_scope_invalid`).
- Adding an operation id / family is MINOR only if explicitly enumerated, typed, bounded, single-use, consumed by an already-enumerated HPAC-PAWA-001 consumer, firing no §107 / §152 trigger; **a generic / free-form / wildcard operation is never permitted at any version.**
- **No operation is open-ended enough to become a generic broker.**

## Section 7 — `configure_privileged_helper` (§42G) — **VERIFIED**

Independently scrutinized against the prompt's 12-point checklist:
1. **metadata-only** — `HPAC-PAWA-REQ-326`: one bounded, protected, metadata-only transaction for the `HPAC-PAWA-HELPER-INSTALLATION/1.0` generation record + `HPAC-PAWA-HELPER-CURRENT-GENERATION/1.0` anchor + provenance sidecars.
2. **cannot install executable bytes** — *"SHALL **NOT** create, copy, replace, `chmod`, `chown`, or execute helper bytes"* (the §80.2 `configure_presentation_mechanism` model; HPAC-PPA-REQ-004).
3. **cannot replace the protected trust root** — PAWA-INV-17; the one trust root is unchanged.
4. **cannot self-authorize an untrusted caller** — the transaction is itself driven **through the §33C helper boundary** as an `admin_mutation` (`HPAC-PAWA-REQ-328`); the exact future consumer is the standalone principal-admin / helper-admin script only (§38 / §38C).
5. **cannot be called merely because a process speaks the protocol** — every §33C conjunct still applies; peer credential = deployment owner, not the configured agent.
6. **caller/consumer authority explicitly bounded** — subject = the exact `helper_implementation_id` (`hpac-pawa-privileged-helper`); one nonempty transaction id.
7. **helper path / hash / version / generation fields constrained** — the content-addressed path is **derived, not caller-selectable** (HELPER §6.19); `helper_sha256` is 64 lowercase hex.
8. **generation changes governed** — monotonic `G → G+1`, exact `supersedes`, atomic anchor switch, read-back verified.
9. **no wildcard helper identity** — const `helper_implementation_id`; no prefix / glob.
10. **no arbitrary executable path becomes trusted by request data** — `registration != executable provenance`; the digest of the **opened** bytes is re-checked on every launch.
11. **`registration != executable provenance`** — explicit (PAWAH-INV-3; §42G).
12. **`metadata record != trusted origin`** — `HPAC-PAWA-REQ-316` (`STRUCTURALLY VALID OBJECT != TRUSTED CANONICAL STATE`).
- **Non-circular bootstrap** — `HPAC-PAWA-REQ-327`: the already-recognized deployment-owner PAWA anchor authorizes generation 1 **after** the helper bytes are installed out of band; no prior privileged-helper operation, ceremony, or PCAE principal required; first-caller-wins / self-install / repository install / environment install / deterministic-fixture promotion prohibited.
- **`configure_privileged_helper` cannot redefine the trusted helper from the ordinary process** — the transaction runs in a verified helper process, not the main interpreter. **VERIFIED.**

## Section 8 — Single trust root / no second trust root — **VERIFIED**

- **PAWA-INV-17** / **PAWAH-INV-7**: the one trust root stays **OS filesystem write authority on the out-of-band-provisioned `<HPAC_PROTECTED_ROOT>`** (`HPAC-PAWA-REQ-010` / `-300`), *"never an in-process check"*.
- `trust root` ≠ `installed helper metadata` ≠ `helper hash` (`helper_sha256`) ≠ `executable path` ≠ `launcher identity` ≠ `peer credential` ≠ `operation authorization` — **distinct evidence / predicates, none individually a trust root, no single one sufficient** (`HPAC-PAWA-REQ-312`; HPAC-PAWA-HELPER-REQ-012).
- The helper registration is an **integrity-pinned artifact of the existing kind** (the HPAC-PPA-001 `helper_sha256` pattern), authored only by the enumerated deployment-owner PAWA metadata authority (§42G). Registration is **not** a bootstrap authority.
- v2.0 adds **no** new global seal, secret, trust token, magic environment variable, persistent authority record, bearer secret the main interpreter can receive, or independent factory root.
- **No second root is effectively introduced.**

## Section 9 — Helper provenance / same-file-object exec / cross-platform — **VERIFIED**

- **Same-file-object / anti-TOCTOU** (`HPAC-PAWA-HELPER-REQ-029`; §33C `VerifiedExecutionObjectValid`): *"the helper that is executed SHALL be the **same file object** whose integrity / ownership / type properties the launcher verified — validation and execution address one opened descriptor … a pathname re-open after validation is **forbidden**"*. `verify(path A)` then `execute(A via a fresh pathname resolution)` is **rejected**. The contract freezes the **property**; the concrete syscall (`fexecve`, `execveat` with `AT_EMPTY_PATH`, or a documented platform equivalent) is an implementation **profile** (§5). *"If the platform cannot execute the verified object without a substitution window, the implementation **STOPS BLOCKED**"* — not downgraded.
- The contract **distinguishes** the logical assurance property (§16 frozen table) from the platform implementation profile (§5 / §28), and does **not** require a specific syscall.
- **macOS feasibility** — `LOCAL_PEERCRED` / `getpeereid(3)` (peer credential); `fexecve` / identity-preserving exec of the validated descriptor (macOS ≥ 10.15); `socketpair(AF_UNIX, SOCK_STREAM)` inherited only across `exec` (one-shot private channel); `posix_spawn` / `fork`+`fexecve` of the validated descriptor (substitution-free launch). **A plausible conforming mechanism exists for every §16 property.**
- **Linux (Dell Ubuntu) feasibility** — `SO_PEERCRED` / `getsockopt(SO_PEERCRED)`; `execveat(AT_EMPTY_PATH)` / `fexecve`; `AF_UNIX socketpair`; `posix_spawn` / `fork`+`fexecve`. **A plausible conforming mechanism exists for every §16 property.**
- The profiles are *"**not** assumed byte-for-byte equivalent"*; a platform with no kernel-authenticated peer credential **or** no substitution-free exec of a verified descriptor is **BLOCKED** (`HPAC-PAWA-HELPER-REQ-104` / `-017`), not a downgrade. **The contract does not freeze a property impossible to realize on either supported platform, and does not paper over infeasibility with vague "equivalent" language** (the "platform-equivalent" wording is always paired with an explicit BLOCKED alternative). **VERIFIED.**
- A copied or lookalike executable is *"a different file"* — different `helper_sha256`, or, if bytes match, a file object not opened from beneath the current live protected-root `{device, inode}` — and fails §28 (`HPAC-PAWA-HELPER-REQ-030`).

## Section 10 — Peer authentication — **VERIFIED**

- `HPAC-PAWA-HELPER-REQ-042` — before admitting any operation the helper obtains the **kernel-authenticated** OS `(uid, gid[, pid])` of the channel peer (§5 profile), **not** from any peer-supplied protocol field, and requires: (1) peer `uid` is the deployment-owner OS principal (resolved from the filesystem, not the request); (2) peer `uid` is **not** the configured agent principal; (3) the credential is **bound to the actual channel**; (4) on the two-principal topology (1)/(2) are distinct accounts, and where the topology is **absent** → REAL issuance **ineligible**, fail closed (§61 / PAWA-INV-7).
- `HPAC-PAWA-HELPER-REQ-043` — a **required conjunct**, evaluated **before** operation admission **and before any protected-store read** the request would drive; neither sufficient alone nor omissible.
- `HPAC-PAWA-HELPER-REQ-044` / **PAWAH-INV-8** — **OS peer credential ≠ human identity ≠ human approval ≠ informed intent**. `deployment-owner peer ≠ configured agent principal`.
- A peer whose credential is unavailable / unauthenticated / forgeable under the §26 threat model / not the deployment owner / the configured agent / not channel-bound → **fail closed** (`unauthorized_factory_consumer` / `current_context_is_agent`), no operation admitted. **A claimed UID/GID/PID inside JSON cannot satisfy the requirement** (it is not read from the request). **VERIFIED.**

## Section 11 — Configured agent identity — **VERIFIED**

`HPAC-PAWA-HELPER-REQ-032` (finding F-1 / F-5-B1, preserved and executed
**inside the helper**): the helper process principal is the deployment owner
and MAY run with elevated (`sudo` / root EUID) privilege; the negative
boundary (step 3 / step 7) SHALL still be evaluated against the **configured
PCAE agent principal** resolved live from `HPAC-PAWA-AGENT-EXCLUSION/1.0` —
**never** `os.geteuid()`, an ambient root EUID, a `SUDO_*` variable, or a
caller parameter. `euid == 0` inside the helper *"mints **nothing**"* (§34,
PAWA-INV-1). The normative source for configured-agent identity is explicit
and protected from ambient substitution (`USER` / `LOGNAME` / `SUDO_USER` /
shell env / caller-provided UID / ambient root all excluded). §33C
`ConfiguredAgentIdentityBindingValid` makes this a named conjunct.

## Section 12 — Request / response schema — **VERIFIED**

- **Request** (`HPAC-PAWA-HELPER-REQUEST/1.0`, HELPER §11): closed, versioned, canonically serialized; **unknown fields fail closed**; bounded fields for `protocol_version`, `request_schema_version`, `operation`, `operation_version`, `role` (present only for `certification_write`, member of the closed five), `session_id`, subject binding (`principal_id` / `credential_id` / `proof_id`), `operation_params` (closed typed struct per operation), `request_id` (monotonic within `session_id`), `nonce` (CSPRNG ≥ 256 b), `expiry` (trusted-clock), echoed `installation_id` / `generation`, self-excluding `request_digest`.
- `HPAC-PAWA-HELPER-REQ-047` / **PAWAH-INV-5** — **forbidden in a request**: an arbitrary Python expression; a module / import path; a shell command; an executable path; a role string beyond the enumerated five; a generic / free filesystem path; an unrestricted JSON mutation payload; a caller-provided `approved=True` / decision / response bytes / helper process / channel / attestation / evidence digest; a caller-selected authority class / seal / `_bind_configured_agent_identity` argument.
- `HPAC-PAWA-HELPER-REQ-048` — **the request carries no authority**; *"a well-formed request ≠ an admitted operation"*.
- **Response** (`HPAC-PAWA-HELPER-RESPONSE/1.0`, HELPER §12): closed, versioned; echoed `protocol_version` / `request_id` / `nonce` **must match** exactly (any mismatch → launcher fails closed, treats as no-result, reconciles per §21); `decision ∈ {PERFORMED, REJECTED}`; `terminal_code` present iff `REJECTED`, an existing `pawa_failure_code`; `evidence_ref` / `evidence_digest` iff `PERFORMED` and a record was written — *"**not** an authority object"*; `result_payload` only for `certification_read` / a `ceremony_entry` ack — *"**never** an `HPACStoreAuthority` … or any object from which privileged authority could be reconstructed"*; `state_reached` informative only, *"the durable protected-root record is authoritative, not this field"*; self-excluding `response_digest`.
- **No request field may assert** trusted consumer / approved / authenticated / Gate5 ALLOW / valid signature / accepted counter transition / production principal — confirmed by the §11 field table and §47.
- Malformed / unknown fields → frozen fail-closed rules (`HPAC-PAWA-HELPER-REQ-002`).

## Section 13 — Freshness / replay — **VERIFIED**

- Every request carries `expiry` (trusted-clock) + per-request CSPRNG `nonce` ≥ 256 b; the helper validates freshness against **its own** trusted clock; past `expiry` → **fail closed** (`capability_stale`) regardless of every other conjunct passing.
- `HPAC-PAWA-HELPER-REQ-076` — the helper distinguishes and treats distinctly: **fresh** (admit once) / **consumed** (DENY `capability_stale` — *"cannot be accepted again, even if its response was lost"*) / **duplicate** (DENY — at most one helper process may admit a given `(request_id, nonce)`) / **expired** (DENY) / **unknown** (DENY `operation_scope_invalid`) / **conflicting replay** (a `(request_id, nonce)` reused with different `operation` / `session_id` / subject → DENY `target_scope_invalid`).
- `HPAC-PAWA-HELPER-REQ-077` — *"A lost response does not make the original request unused."* Once a one-shot op crosses `MUTATION_ATTEMPT_STARTED` its `(request_id, nonce)` is **spent**; the caller reconciles against the protected-root evidence record, does not resend.
- **A request id or nonce is not itself authority**; request freshness is bound to the operation / session / context. `certification_read` is idempotent (each call a fresh helper process, full recognition). **`receipt = evidence ≠ authority`; `response absence ≠ proof no mutation happened` — VERIFIED.**

## Section 14 — State-transition model — **VERIFIED**

- `HPAC-PAWA-HELPER-REQ-079` frozen ordered model: `REQUEST_RECEIVED → REQUEST_AUTHENTICATED → OPERATION_ADMITTED → MUTATION_ATTEMPT_STARTED → MUTATION_COMMITTED → EVIDENCE_WRITTEN → RESPONSE_EMITTED`.
- `HPAC-PAWA-HELPER-REQ-080` — what each transition proves / does not prove (frozen table): `MUTATION_ATTEMPT_STARTED ≠ MUTATION_COMMITTED`; `MUTATION_COMMITTED ≠ RESPONSE_EMITTED / observed`; `RESPONSE_EMITTED ≠ caller received / human observed`.
- `HPAC-PAWA-HELPER-REQ-081` — **durable** transitions (survive a crash, reconcilable from `<HPAC_PROTECTED_ROOT>`): `MUTATION_COMMITTED` and `EVIDENCE_WRITTEN`. `REQUEST_RECEIVED … MUTATION_ATTEMPT_STARTED` are process-local and leave **no protected-root effect**.
- `HPAC-PAWA-HELPER-REQ-082` — **no automatic retry** once `MUTATION_ATTEMPT_STARTED` is crossed, unless the operation contract proves the mutation idempotent or reconcilable. The no-auto-retry boundary begins at the correct point (`MUTATION_ATTEMPT_STARTED`, not `OPERATION_ADMITTED`).

## Section 15 — Audit / evidence ordering — **VERIFIED**

- `HPAC-PAWA-HELPER-REQ-086` — ordering model **A**, evidence **durably staged before** the mutation, **finalized after** commit: (1) before `MUTATION_ATTEMPT_STARTED` the helper durably writes a `state = "staged"` record binding request digest / operation / role / session / subject / nonce / expiry; (2) **staged write failure → abort before any mutation**, fail closed (`internal_fail_closed`); (3) the helper performs the one mutation; (4) the helper **finalizes** the staged record (`state = "committed"`, + committed-record digest) — `EVIDENCE_WRITTEN`; (5) a crash between (3) and (4) leaves a `staged` record + a committed canonical record → the **INDETERMINATE / RECONCILIATION REQUIRED** state (deployment-owner reconciliation finalizes or quarantines) — *"never reported as success and never auto-retried"*.
- `HPAC-PAWA-HELPER-REQ-087` — the contract explicitly does **not** claim *"audit-write failure means the mutation did not occur"* unconditionally; it **guarantees the ordering** that makes a pre-mutation staged-evidence failure abort before any mutation, and a post-commit finalization failure a detectable reconciliation condition rather than a silent success.
- An explicit reconciliation / indeterminate disposition exists for the commit/finalize gap. **Successful mutation has a durable evidence-finalization path; a crash after commit before evidence finalization is NOT silently "no mutation". VERIFIED.**

## Section 16 — Crash / uncertainty semantics — **VERIFIED**

`HPAC-PAWA-HELPER-REQ-083` table covers **every material stage**: before
`REQUEST_AUTHENTICATED`; after auth / before `OPERATION_ADMITTED`; after
admission / before `MUTATION_ATTEMPT_STARTED` (all → no protected-root effect;
request unused; a fresh request MAY be built); after
`MUTATION_ATTEMPT_STARTED` / before `MUTATION_COMMITTED` (**no committed
record**; the `(request_id, nonce)` is **spent** — do **not** retry;
reconcile; a **new** request required); after `MUTATION_COMMITTED` / before
`EVIDENCE_WRITTEN` (**INDETERMINATE / RECONCILIATION REQUIRED**); after
`EVIDENCE_WRITTEN` / before `RESPONSE_EMITTED`, and after `RESPONSE_EMITTED`
lost in transit (committed record + finalized evidence exist; the operation
**succeeded**; do not retry — *"response loss is never proof the mutation did
not happen"*). `HPAC-PAWA-HELPER-REQ-084` — *"Unknown outcome remains unknown
until reconciled"* against the durable protected-root evidence record. **No
unsafe retry rule; no auto-retry after the defined uncertainty boundary.**

## Section 17 — Exact five-role certification closure — **VERIFIED**

- The role family is **exactly** `{ hpac_challenge_coordinator, hpac_assertion_recorder, human_authentication_proof_verifier, hpac_gate5_binder, hpac_rhamp_counter_state_verifier }` (HELPER §14.2 `HPAC-PAWA-HELPER-REQ-059`; §42B / PAWA-INV-13 reused verbatim).
- **No sixth role**; `hpac_lifecycle_terminator` **explicitly NOT** a member (a rejected / expired ceremony fails closed with no production write; a future terminator write needs a new governed contract evolution); **no** wildcard, prefix, `fnmatch`, case-fold, or arbitrary caller-selected role.
- Per-role authority tables (§42B / `HPAC-PAWA-REQ-247`) **byte-unchanged in substance**; PAWA-INV-13 annotated *"(v2.0) delivery superseded by §33C — substance unchanged"*.
- All five roles map through the single `certification_write` operation, but **role-specific semantics remain closed** (`HPAC-PAWA-HELPER-REQ-060` / `-061`): each invocation performs exactly one of the §42B per-role bounded actions with the exact per-role permitted store / prohibited actions / issuance prerequisites / capability bindings `(role, subject, session_id)` / cardinality one — *"the generic outer operation does not erase internal restrictions"*. `hpac_rhamp_counter_state_verifier` remains the **sole** counter-state mutation authority; `mint_protected_presentation_evidence_writer` remains the **sole** author of `HPAC-PRESENTATION-EVIDENCE/2.0`.
- `HPAC-PAWA-HELPER-REQ-062` — **FACTORY ≠ CONSUMER, CONSUMER ≠ MINTER**: a `PERFORMED` `certification_write` permits no remint / delegate / convert-to-generic / serialise / store / reissue; a second write re-runs the full §7 / §10 / §13 sequence in a fresh helper process.

## Section 18 — Challenge / assertion / proof / Gate5 / counter separation — **VERIFIED**

`HPAC-PAWA-HELPER-REQ-061` preserves every wall: `challenge issued ≠
approved`; `assertion recorded ≠ assertion valid`; `proof exists ≠ proof
valid`; `proof verified ≠ informed approval`; `Gate5 ALLOW ≠ PB permission ≠
runtime capability ≠ adapter admission ≠ external-effect permission`; `counter
evidence ≠ authority`; `counter transition ≠ human approval`. The
`hpac_gate5_binder` *"SHALL NOT manufacture the principal or the Gate result;
the N16-5 authority path **terminates** at the Gate-5 assurance result"*. No
helper operation manufactures the next semantic stage from a prior
`PERFORMED`.

## Section 19 — Typed read model — non-reconstructibility — **VERIFIED**

- `certification_read` (HELPER §15) returns **only reads**, over an **explicitly enumerated closed** set of canonical protected-store records **for the bound session** — the exact §42D set (`PrincipalRecord` / `CredentialRecord` + provenance; the RHAMP sidecar + **current** counter-state record, read only; the current-generation protected-presentation installation record + HPAC-REQ-090 mechanism descriptor + trusted-approval-presentation record; the PAWA anchor / descriptor / `HPAC-PAWA-AGENT-EXCLUSION/1.0` + §6 helper-registration records the §7 recognition already reads).
- Each read specifies an **exact record type**, **exact permitted fields**, **exact purpose**, **exact bound session / subject**. `HPAC-PAWA-HELPER-REQ-064` forbids: an arbitrary filesystem read; an open-ended HPAC store enumeration beyond the set; a wildcard field selection; a read of OS secrets / keychain / keyring / a FIDO2 PIN / Telegram or other application secrets / a private key; a read of an unrelated principal / credential / proof / session; a `proofs/v2` read outside a bound session; **any** write / create / replace / `chmod` / `chown` / execute.
- **`HPAC-PAWA-HELPER-REQ-065` — repeated typed reads SHALL NOT reconstruct unrestricted store authority.** The enumeration is by exact record identity bound to the session; *"a caller cannot iterate it into a generic read broker"*; the helper returns record **contents**, not a store handle or an `HPACStoreAuthority`. **Semantic reconstruction-risk test:** the enumerated set is bounded to the *bound session's* principal / credential / proof plus the deployment-wide presentation-installation and PAWA-recognition records; it is **not** "effectively the entire privileged store" — it cannot be composed into the effect of `HPACStoreAuthority` (arbitrary path / key / table / query) because every read is session-scoped and record-typed, and no write / mint / counter transition is reachable through it (`HPAC-PAWA-REQ-286` / `-287` preserved). A future broader bounded read must state and justify the **minimum** form and evolve the contract explicitly. **VERIFIED — not blockable on reconstruction.**
- `HPAC-PAWA-HELPER-REQ-066` / **PAWAH-INV-4** — the read result is non-authoritative except for the exact evidentiary claim its schema defines.

## Section 20 — Ceremony-entry separation — **VERIFIED**

`ceremony_entry` (HELPER §16) is a **separate typed operation** whose **only**
effect is to hand the canonical ceremony request bytes (HPAC-PPA-REQ-034
shape) to the **existing HPAC-PPA-001 v1.0 presentation helper** for
**exactly one** ceremony in the bound session — *"not a Python
`HPACStoreAuthority`, not a handle, not a seal"*. Every wall verbatim:
`ceremony entry ≠ approval ≠ authentication ≠ Gate-5 ALLOW ≠ PB permission ≠
execution ≠ FIDO2 UP / UV ≠ a real authenticator assertion ≠ real assurance`.
The result (`result_payload`) is a **ceremony-entry acknowledgement** — a
reference to the started ceremony — *"and nothing more"*; the human APPROVE /
REJECT election and the `HPAC-PRESENTATION-EVIDENCE/2.0` write are conducted
by HPAC-PPA-001, unchanged. The presentation helper *"remains a **distinct
semantic component** … even though the one-shot-verified-helper process
infrastructure pattern is shared"*. **Ceremony entry remains
non-authoritative.**

## Section 21 — HPAC-PPA-001 evidence-writer delivery — **ADJUDICATION: B**

See **OVERALL CONTRACT-IV VERDICT** above. The determination is **B —
HPAC-PPA-001 CONTRACT EVOLUTION REQUIRED**, on the strength of HPAC-PPA-REQ-041
("never sent to the helper"), HPAC-PPA-REQ-054 ("evidence producer is only the
launcher mediator"), HPAC-PPA-REQ-052 (distinct issuer module), PPA-INV-2
(helper response ≠ evidence writer, distinct trust actions), and HPAC-PPA-REQ-069
/ HPAC-PPA-REQ-070 (moving the writer-holder is MAJOR-class, not a
within-properties platform adapter). The v2.0 `presentation_evidence_write`
design is the correct security direction but is not authorized by HPAC-PPA-001
v1.0 as frozen; it is **not silently reinterpreted** and **not edited** in this
IV. **Required next: a fresh governed HPAC-PPA-001 contract-evolution phase**
(derived, **NOT begun**).

## Section 22 — Presentation-evidence write semantics

Moot under Adjudication B, but recorded: `HPAC-PAWA-HELPER-REQ-071` correctly
forbids the `presentation_evidence_write` request from **self-asserting**
`approved = true` / `verified = true` / `human_present = true` /
`authenticated = true` — those facts arise only from their designated trusted
mechanisms (the HPAC-PPA-001 ceremony's authenticated `APPROVE`; the RHAMP
verifier; the genuine authenticator). `HPAC-PAWA-HELPER-REQ-072` — `REJECT` /
cancel / timeout / crash / malformed / any validation failure → **no**
evidence write, fail closed; *"there is no returnable writer"*.
`presentation evidence ≠ authentication proof ≠ PB permission ≠ runtime
capability`. The **helper does not manufacture human approval.** These
semantics are sound **once HPAC-PPA-001 is evolved to authorize the
out-of-process holder.**

## Section 23 — `PawaOperation` count / `configure_privileged_helper`

- Prior `PawaOperation` count: **6** (v1.2 added `configure_presentation_mechanism`; the v1.3 `certification_write` family is not a `PawaOperation`).
- New count: **7** (`HPAC-PAWA-REQ-326`) — v2.0 adds **exactly** `configure_privileged_helper` (role `privileged_helper_installer`).
- **No accidental widening** — no hidden generic "helper operation" was added; the closed operation *vocabulary* of the wire protocol (5 members) is distinct from the `PawaOperation` *mutation* count (7); a read / ceremony entry is still not a `PawaOperation`.

## Section 24 — Failure-code reuse — **VERIFIED**

`HPAC-PAWA-REQ-329` (§42H) maps **every** v2.0 rejection deterministically and
unambiguously onto an **existing** `pawa_failure_code` — **no new code; the
taxonomy remains 21 closed values**. Independently checked the mapping table:
not-`exec`'d-from-verified-helper / bad peer credential → `unauthorized_factory_consumer`
(#15); peer **is** the configured agent / topology absent →
`current_context_is_agent` / `agent_has_protected_write_authority` (#5 / #6);
any §33 step 1–8 failure → its exact existing code (#1–#14); malformed / unknown
operation / version / prefix / wildcard / generic `operation_params` / `role ∉`
five → `operation_scope_invalid` (#16); session/subject/proof/credential
mismatch / read outside §42D / attempt to reach a mint through a read →
`target_scope_invalid` (#17); reuse after `MUTATION_ATTEMPT_STARTED` / duplicate
`(request_id, nonce)` / expiry / second `ceremony_entry` → `capability_stale`
(#18); forged / deserialised helper-side handle → `reconstruction_attempt`
(#20); staged-audit-write failure before mutation / otherwise unclassified
fail-closed → `internal_fail_closed` (#21). **No semantically overloaded code
hides a security-critical distinction** — the mapping preserves the existing
recognition / issuance failure classes at a new process boundary. The
PAWA→RHAMP map (§57) is **unchanged**. **No contract defect.**

## Section 25 — RHAMP terminal reason / counter semantics — **VERIFIED**

- RHAMP-001 v1.0 `terminal_reason_code` count **unchanged** (41), RHAMP-001 v1.0 **byte-unchanged** (`git diff` confirms), no helper contract invents a new RHAMP outcome (`HPAC-PAWA-HELPER-REQ-004`).
- RHAMP counter semantics remain governed by RHAMP-001; the helper *"introduces **no** new TTL and SHALL NOT bypass any existing one"*; `hpac_rhamp_counter_state_verifier` performs one authorized post-verification bounded transition on an **accepted** canonical counter decision only; *"SHALL NOT … trust a caller-provided 'counter accepted'"*; monotonicity / currentness owned by RHAMP-001.
- **No helper operation bypasses the RHAMP verifier; a caller cannot self-assert counter ACCEPT.** RHAMP-001 not edited.

## Section 26 — Generic privileged broker prohibition — **VERIFIED**

`HPAC-PAWA-HELPER-REQ-094` / **PAWAH-INV-5** / `HPAC-PAWA-REQ-324` — the two
contracts together explicitly prevent the helper from being / becoming /
being reachable as: an arbitrary filesystem-path mutator; an arbitrary command
/ shell executor; an arbitrary Python `eval` / `exec` of caller bytes; an
arbitrary store-method dispatcher; an arbitrary / caller-driven role minter;
an unrestricted registry editor; a generic secret retriever; a generic
environment modifier; an unrestricted process launcher; a "run this operation
by name" / "apply this JSON patch" entry point; a universal privileged RPC
interface. Every permitted operation is enumerated (§13), typed (§11), bounded
(§14–§17), contract-bound. **Essential IV criterion — MET.**

## Section 27 — Installer / launcher / helper / approver separation — **VERIFIED**

`HPAC-PAWA-HELPER-REQ-013` / `-014` / **PPA-INV-2 pattern**: `deployment owner
≠ installer ≠ launcher ≠ helper ≠ evidence writer ≠ authenticated human ≠
human approver ≠ PB ≠ runtime`. *"Where **one OS principal** performs multiple
deployment roles … the **semantic authority of each role stays distinct**;
authority SHALL NOT be inferred merely because the same administrator owns two
files or runs two scripts."* Each role's authority is established by its own
predicate (§6 helper, §8 launcher, §10 peer, §13 operation). **No "same UID
therefore same authority" shortcut.**

## Section 28 — Non-bearer / restart-dead — **VERIFIED**

§49C `HPAC-PAWA-REQ-337` / **PAWAH-INV-10**: §45–§49 / §49A / §49B become
**properties of the helper-process boundary** — no returnable authority object
to serialise / copy / capture; the helper process (and any capability it
minted internally) is **gone at exit**; a restart cannot revive stale consumed
authority; a fresh launch re-runs the entire §33C + §33 1–8 recognition; a
lost response **never** frees a spent one-shot `(request_id, nonce)`.
Authority is operation-specific, one-shot where specified, non-serialisable as
a generic capability, dead when the helper exits, not revived by process
restart / response loss, not recreated from typed evidence. **A fresh process
repeats the full trust / admission sequence.**

## Section 29 — Deterministic vs real — **VERIFIED**

`HPAC-PAWA-HELPER-REQ-095` / `-096` / `-097`: `deterministic test mechanism ≠
real human authentication`; `a test helper speaking the protocol ≠ production
authority` — *"it is a **different file** and fails §28"*. The only permitted
test injection point is a disclosed, one-leading-underscore, documented-
fixture-only, keyword-only seam, and a guard SHALL assert no non-test module
passes it into any helper / launcher path; the disclosed seams remain
**NON-PRODUCTION** and this contract *"legitimizes none of them"*. A
deterministic authenticator / presentation / fixture launcher / fixture peer
credential / fixture helper *"remains permanently unable to produce
`PRODUCTION` authority or be relabelled with the real kind"*.
`verify_human_authentication(require_real_assurance=True)` still requires every
resolved record's `authority_class is PRODUCTION` **and** the real
authentication-mechanism id **and** the real presentation-mechanism id — *"the
helper only makes those PRODUCTION records **reachable**; it does not relax the
check"*. **No deterministic result becomes REAL by traversing the helper
protocol.**

## Section 30 — Human authentication / approval / presence walls — **VERIFIED**

§68C `HPAC-PAWA-REQ-338` preserves every §5 / §13 / §67 / §68 / §68A / §68B
wall and PAWA-INV-1..14 **verbatim** and adds **no** authority. Restated for
the out-of-process model: `helper execution / peer-credential check ≠ human
APPROVE / REJECT`; `OS peer credential ≠ human identity ≠ informed intent`;
`successful §33C recognition ≠ real assurance`; `typed evidence / a typed read
result ≠ HPACWriterCapability / HPACStoreAuthority`; `a PERFORMED
admin_mutation ≠ further authority`; `a PERFORMED certification_write ≠ a
manufactured principal / Gate result / PB / RE / runtime / effect`;
`ceremony_entry ≠ approval ≠ authentication ≠ Gate-5 ALLOW ≠ PB permission ≠
execution`; `a certification_read result ≠ validity / approval / presence /
assurance`; `deterministic input never becomes REAL assurance through the
helper`. `confirmation ≠ approval`; `approval ≠ PB permission`; `PB permission
≠ runtime capability`; `YubiKey touch = UP`, `YubiKey touch ≠ approval`. **All
walls explicit and preserved.**

## Section 31 — Mechanism neutrality / mobile future — **VERIFIED**

`HPAC-PAWA-HELPER-REQ-100` / `-101` / `-102`: neither contract requires
YubiKey / FIDO2 / USB / a specific AAGUID / one hardware brand / a local TTY /
`pcae-protected-local-presentation/1.0` as the universal authority-helper
prerequisite. The helper's existence and trust are bound to **OS process + OS
filesystem + OS peer-credential** facts. A future **mobile-only / passkey**
authentication-and-approval path stays open — it delivers a verified
authentication result and a protected APPROVE to the same `certification_write`
/ `ceremony_entry` / `certification_read` operations **unchanged**. *"Local TTY
or a physical YubiKey SHALL NOT be a prerequisite for ordinary non-effecting
PCAE development."* The canonical `PrincipalRecord` stays mechanism-neutral.

## Section 32 — PB / POL / runtime / effect non-expansion — **VERIFIED**

`HPAC-PAWA-HELPER-REQ-003` / `-113` and §68C: the contracts create **no** PB
permission, POL exception, Runtime Enforcement allow, runtime capability,
plugin capability, `DispatchEnvelope`, adapter admission, Gate6+ authority, or
external-effect authority. `Gate5 ALLOW ≠ external-effect permission`;
`DispatchEnvelope ≠ permission to dispatch`; `execution unavailable → no
external effect`. **Nothing in these contracts enables `adapter.dispatch()`.**
The certification-authority path terminates no later than the bounded Gate-5
assurance result; the read / ceremony-entry path terminates at trusted reads +
one ceremony entry.

## Section 33 — Security claim boundaries — **VERIFIED (no overclaim)**

`HPAC-PAWA-HELPER-REQ-098` — **protects against:** ordinary same-interpreter
PCAE process compromise; a malicious plugin in the ordinary process;
`gc.get_objects` / `gc.get_referrers` object-graph introspection; `import` /
module / `sys.modules` manipulation; an ordinary configured-agent OS account;
protocol replay; a fake helper started by an unprivileged process (fails the
§28 hash / owner / same-file check); a fake launcher without the protected
root and the deployment-owner peer credential (fails §7 / §10); forged request
fields (closed schema, self-excluding digests, fail-closed on unknown fields).
`HPAC-PAWA-HELPER-REQ-099` — **does NOT claim protection against:** a hostile
root / admin who controls the protected files or the registered helper binary;
a compromised OS kernel; a compromised registered helper binary after an
authorized protected-root mutation; a deployment owner restoring a
byte-identical whole trusted-machine snapshot; a single-account host (→
two-principal topology absent → REAL issuance **ineligible**, fail closed).
These bounds match HPAC-PAWA-001 §8(c) / §60 / PAWA-INV-6, HBDC-001 §18,
`TB-ARCH` §4 / §26 — **inherited unchanged, no overclaiming.**

## Section 34 — Cross-contract consistency — **CONSISTENT EXCEPT HPAC-PPA-001**

- HPAC-001 v2.1, RHAMP-001 v1.0, HBDC-001 v1.2, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1, and the descriptor + current-generation schemas: **byte-unchanged AND semantically consistent** — the v2.0 / helper language contradicts no unchanged sibling normative requirement (the RHAMP counter authority, the HPAC descriptor / evidence / attestation model, the RDGO dispatch-gate ordering, the RIHAC / RIASC runtime-invocation human-authority chain are all referenced, not re-meant; the certification-authority path still terminates at the Gate-5 assurance result).
- **HPAC-PPA-001 v1.0: byte-unchanged but a material semantic conflict exists** in the `presentation_evidence_write` operation's holder model (§21 / the OVERALL VERDICT). This is the IV's blocking finding.

## Section 35 — Contract guard / widen-not-weaken review — **VERIFIED**

The predecessor CONTRACT phase reconciled 27 point-in-time guards across 17
completed-predecessor suites (widen-not-weaken, A/B against the fixed baseline
`05056eeb`, 40 pre-existing failures identical at baseline and HEAD, 0
attributable regressions, 0 `def test_` renamed / removed / skipped /
disabled). This IV changed **no** `src/pcae` and **no** contract, so **no**
downstream point-in-time guard is perturbed by this phase — the predecessor's
reconciliation stands. Independently re-ran the predecessor's own 45-case
contract-verification suite at this HEAD: **45 passed, 0 failed** (regression
lock — encoded in `test_d1` of this phase's suite). No previously defensive
requirement was weakened to accommodate v2.0: every v1.0–v1.4 requirement body
survives verbatim (`test_06` predecessor / independently re-checked); PAWA-INV-13 /
-14 are annotated *"delivery superseded — substance unchanged"*, not deleted;
the `_PINNED_*` anti-bypass PoCs become regression locks for the later removal
slice. **No security regression is hidden as a "version update".**

## Section 36 — Tests / guards run

- **New independent contract-IV suite:** `tests/test_phase_149o_20l_7o_3w_1r_2b_1r_1_1r_30r_5r_2_1r_1r_2r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1r_1_1_1_1_1_n16_5_f_5_tb_contract_iv.py` — static / read-only; independently encodes the IV criteria (CPIPC identity; both byte baselines; sibling byte-identity + version headers; the MAJOR (S-4) classification incl. the closed §153 permit list and the §152 no-verbatim-trigger review; the exact 13-conjunct §33C conjunction, fail-closed, no-single-conjunct; same-interpreter predicate elimination + no-in-process-authority-object + no-compat-shim; PAWA-INV-15 named + semantic-equivalent no-export; the closed 5-member operation vocabulary + unknown/prefix/wildcard/version denial + `operation_params` closed struct + `supported_operations` gating; `configure_privileged_helper` metadata-only + no-second-root + helper-boundary-driven + non-circular bootstrap; helper REQ contiguity 1–114 + PAWAH-INV 1–10; same-file-object frozen-property + macOS/Linux feasibility-or-BLOCKED; peer-auth precedes-admission + kernel-authenticated + never-caller-asserted; configured-agent-identity-never-ambient-root; request carries-no-authority + no-field-asserts-trust; replay dispositions all distinct + lost-response-never-frees; state model + no-auto-retry boundary; INDETERMINATE/RECONCILIATION-REQUIRED; evidence-staged-before-mutation; five-role closure + terminator excluded; typed-read non-reconstructibility + no-secret-reads; ceremony-entry bounded-handoff + walls; §42H no-new-code deterministic mapping; RHAMP not-edited; generic-broker prohibition; §68C walls verbatim; deterministic-vs-real permanent; mechanism-neutral / mobile-future; runtime posture 0/0/ABSENT; bounded security claims no-overclaim; **the mandatory HPAC-PPA-001 adjudication → B and the BLOCKED phase verdict**; historical outcomes preserved verbatim; the predecessor 45-case suite still green).
- **Predecessor suite** `…_n16_5_f_5_tb_contract.py`: **45 passed, 0 failed** at this HEAD.

## Section 37 — Broader regression raw tally & attributable-failure analysis

- `python -m pytest -m fast_green` repo-wide carries a large pre-existing
  baseline of point-in-time / protected-root-presence / Python-3.14 /
  blocking-reproduction failures from the F-5 / F-5-B2 / N-16-3 / N-16-4 lines
  (the predecessor CONTRACT phase recorded **40** over its affected guard-set,
  A/B identical at `05056eeb` and HEAD). This IV adds **no** `src/pcae` and
  **no** contract change, so it perturbs **none** of them: `git diff --stat
  3cdc3c08 HEAD -- src/pcae docs/contracts scripts pyproject.toml` is **empty**;
  the only additions are `tests/…_iv.py`, this canonical report,
  `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DECISIONS.md`, the task lifecycle,
  and the `.pcae/` completion artifacts.
- **Attributable regressions: 0.** The new IV suite is the only new test file;
  it is green. No existing test file is modified. No `def test_` renamed,
  removed, skipped, or disabled.
- `test_results.fast_green` for this phase is reported as the **targeted** new
  suite ("N passed, 0 failed") per the repo's finalization-gate discipline; the
  pre-existing repo-wide baseline is recorded here in prose, not in the scanned
  structured field.

## Section 38 — Files changed · production / normative-contract / protected-host

- **Files changed this phase:** `tests/…_n16_5_f_5_tb_contract_iv.py` (new); `docs/PHASE_…_N16_5_F_5_TB_CONTRACT_IV.md` (this report, new); `PROJECT_STATUS.md`; `CHANGELOG.md`; `tasks/DECISIONS.md`; the task lifecycle (`tasks/active/**`, `tasks/done/**`, `tasks/DONE.md`); `.pcae/phase-completion-metadata.json`; `.pcae/phase-completion-report.md`.
- **Production source changes:** **NONE** (`git diff --name-only 3cdc3c08 HEAD -- src/pcae scripts pyproject.toml` empty).
- **Normative contract changes:** **NONE** (`git diff --name-only 3cdc3c08 HEAD -- docs/contracts` empty).
- **Live protected-host writes:** **NONE.**
- **Real ceremony:** **NOT PERFORMED** — no protected APPROVE / REJECT, no certification session, no challenge, no protected presentation, no presentation evidence, no FIDO2 `getAssertion` / `makeCredential` / PIN, no YubiKey touch, no proof issuance, no counter mutation, no `verify_human_authentication(require_real_assurance=True)`, no PRODUCTION principal issuance, no Gate-5 certification.

## Section 39 — Runtime state / plugins / capabilities / first external effect

- **Runtime state:** Observed. **Maximum capability:** observe. **Execution availability:** unavailable (`not_implemented`).
- **Plugins:** 0. **Capabilities:** 0.
- **First governed runtime external effect:** ABSENT / UNREACHABLE. No `adapter.dispatch`. No Gate10 effect reachability. **N-16-6 not begun. N-16-7 not begun (strictly last).**

## Section 40 — Governance validation

- `pcae check` — pass (advisory). `pcae health` — healthy. `pcae push check` — `nothing_to_push` after the governed push. `pcae status coherence` — pass. `pcae doctor task-memory` — pass (single active task; DONE.md pre-existing omission warnings historical / unrelated, recorded). Report / metadata consistency — the canonical Phase ID, the Adjudication-B / BLOCKED verdict, and the immutable-status set (F-5-B2 BLOCKED / F-5 CERTIFICATION BLOCKED / N-16-5 NOT CLOSED / N-16-6 / N-16-7 OPEN-UNTOUCHED) are identical across this report, `.pcae/phase-completion-report.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, `tasks/DECISIONS.md`, and `.pcae/phase-completion-metadata.json`.
- **`origin/main..HEAD` after push: 0.** Governed completion notification dispatched by `pcae phase complete` (the canonical BLOCKED report).
- **REPORTING-UX-1** — open, non-blocking; phase identity was verified independently through `pcae.core.phase_id`, not through the report parser; no evidence that canonical phase identity or governance truth is affected.

## Section 41 — IV pass-criteria roll-up (authorizing prompt §44)

Independently established: 1 CPIPC valid ✓ · 2 predecessor coherent ✓ · 3 v2.0
byte baseline ✓ · 4 helper v1.0 byte baseline ✓ · 5 MAJOR S-4 ✓ · 6 dedicated
IV requirement satisfied (this phase) ✓ · 7 §33C fully replaces the
same-interpreter predicate ✓ · 8 consumer conjunction exact ✓ · 9 every
conjunct fails closed ✓ · 10 no single conjunct sufficient ✓ · 11 no
production same-process fallback ✓ · 12 no authority object / handle / seal /
export crosses ✓ · 13 no reconstructable bearer-equivalent crosses ✓ · 14
helper owns the operation ✓ · 15 vocabulary closed ✓ · 16 unknown / prefix /
wildcard / version denied ✓ · 17 `configure_privileged_helper` cannot
bootstrap an untrusted helper ✓ · 18 single trust root ✓ · 19 no second root ✓
· 20 same-file-object anti-TOCTOU clear + implementable on both profiles ✓ · 21
peer-auth exact + not caller-asserted ✓ · 22 configured-agent identity
distinct from helper / root ✓ · 23 freshness / replay coherent ✓ · 24
state-transition coherent ✓ · 25 audit / evidence ordering coherent ✓ · 26
crash / uncertainty fails closed ✓ · 27 no unsafe auto-retry ✓ · 28 five-role
closure ✓ · 29 typed reads cannot reconstruct store authority ✓ · 30 ceremony
entry non-authoritative ✓ · 31 presentation-evidence semantics separated ✓
(conditional on HPAC-PPA-001 evolution) · **32 HPAC-PPA-001 evidence-writer
question conclusively adjudicated → B — EVOLUTION REQUIRED ✗ (BLOCKS)** · 33
sibling contracts consistent ✓ except HPAC-PPA-001 ✗ · 34 no generic
privileged broker ✓ · 35 non-bearer / restart-dead ✓ · 36 deterministic-vs-real
✓ · 37 human approval / auth walls ✓ · 38 mechanism neutrality / mobile ✓ · 39
PB / POL / runtime / effect walls ✓ · 40 no unauthorized production source
change ✓ · 41 no protected-host mutation ✓ · 42 no real ceremony ✓ · 43
runtime Observed / observe / unavailable ✓ · 44 plugins / capabilities 0 / 0 ✓
· 45 first external effect ABSENT / UNREACHABLE ✓ · 46 N-16-6 / N-16-7
untouched ✓.

**Any security-critical failure → NOT VERIFIED / BLOCKED. Criterion 32 fails.
Verdict: NOT VERIFIED / BLOCKED.** This is not "verified with caveat" — a
normative contradiction remains between HPAC-PAWA-HELPER-001 §17 and
HPAC-PPA-001 v1.0.

## Section 45 — Mandatory PPA question outcome

**B. HPAC-PPA-001 EVOLUTION REQUIRED.**

```
N16-5-F-5-TB-CONTRACT-IV: COMPLETE — NOT VERIFIED / BLOCKED
HPAC-PPA-001 EVIDENCE-WRITER ADJUDICATION: B
Required next: a fresh governed HPAC-PPA-001 contract-evolution phase
  — move HPAC-PPA-001's presentation-evidence-writer authority out of process
    (into the verified presentation helper), re-meaning HPAC-PPA-REQ-041 /
    HPAC-PPA-REQ-054 / HPAC-PPA-REQ-052 / PPA-INV-2 explicitly, aligned with
    HPAC-PAWA-001 v2.0 §42F / HPAC-PAWA-HELPER-001 §17.
  — magnitude: MAJOR for HPAC-PPA-001 (HPAC-PPA-REQ-069 — moving the
    writer-holder / merging trust actions); the evolution phase decides.
  — after it: a fresh HPAC-PAWA-001 v2.0 + HPAC-PAWA-HELPER-001 v1.0 +
    HPAC-PPA-001 vN contract-IV (or a scoped re-IV of the resolved point),
    THEN the implementation sequence of HPAC-PAWA-REQ-340 steps 2–8.
DO NOT BEGIN IT. Each successor requires its own explicit human authorization.
```

## Section 47 — Expected fail state (attributable defect)

- **Exact defect:** HPAC-PAWA-HELPER-001 v1.0 §17 (`HPAC-PAWA-HELPER-REQ-070`) freezes `presentation_evidence_write` as *"invoked by the HPAC-PPA-001 presentation helper itself"*, which re-means HPAC-PPA-001 v1.0 `HPAC-PPA-REQ-041` ("never sent to the helper"), `HPAC-PPA-REQ-054` ("evidence producer is only the launcher mediator"), `HPAC-PPA-REQ-052` (distinct issuer module), and `PPA-INV-2` (helper response ≠ evidence writer). The contract's own §17 note defers this; the IV cannot.
- **Successor:** a fresh governed **HPAC-PPA-001 contract-evolution phase** (not HPAC-PAWA v2.0 repair — the PAWA-side model is sound; not a helper-protocol repair — the operation is correct once its dependency is authorized).
- **F-5:** CERTIFICATION BLOCKED. **N-16-5:** NOT CLOSED. **N-16-6 / N-16-7:** OPEN / UNTOUCHED (N-16-7 strictly last).
- **This IV repairs no normative contract.**

## Section 48 — Historical governance integrity

Preserved verbatim, not rewritten:
`N16-5-F-5-B2` NOT VERIFIED / BLOCKED ·
`N16-5-F-5-B2R-IV` NOT VERIFIED / BLOCKED ·
`N16-5-F-5-B2R2-IMPL` COMPLETE — BLOCKED ·
`N16-5-F-5-TB-ARCH` COMPLETE ·
`N16-5-F-5-TB-CONTRACT` COMPLETE / CONTRACT FROZEN ·
`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` ·
HPAC-PAWA-001 v1.0 / v1.1 / v1.2 / v1.3 / v1.4 freeze records and their IVs —
**immutable**. No retroactive authorization or reinterpretation.

## Section 49 — Delegated worker rule

No delegated worker performed any part of this phase. All repository-state
inspection, predecessor confirmation, CPIPC derivation, both contract
baselines, the MAJOR classification re-walk, the §33C conjunct matrix, the
§42H mapping check, the sibling byte-identity check, the HPAC-PPA-001
adjudication, the independent contract-IV suite, and this report were produced
directly by the primary human-authorized operator session.
`DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED` — preserved.

## Section 55 — Absolute stop boundary

This phase ENDS at contract independent verification. No helper / launcher /
IPC implementation, no caller integration, no in-process-path removal, no
packaging, no protected-root mutation, no security implementation IV, no
deployment, no final certification, no FIDO2 PIN / YubiKey touch, no real
certification session / challenge / proof / counter mutation, no PRODUCTION
principal, no Gate-5 certification. **N-16-5 not closed. N-16-6 / N-16-7 not
begun.** Awaiting fresh human authorization for the recommended HPAC-PPA-001
contract-evolution successor.

---

## Final canonical status

| Item | Status |
|---|---|
| **N16-5-F-5-TB-CONTRACT-IV** | **COMPLETE — NOT VERIFIED / BLOCKED** |
| HPAC-PAWA-001 v2.0 (PAWA-side authority model) | independently verified on every criterion checked; **not** independently verified overall (the cross-contract dependency blocks) |
| HPAC-PAWA-HELPER-001 v1.0 (PAWA-side) | independently verified on every criterion checked; `presentation_evidence_write` blocked on its HPAC-PPA-001 dependency |
| Trust-boundary contract | **NOT VERIFIED / BLOCKED** — HPAC-PPA-001 evidence-writer adjudication = B |
| HPAC-PPA evidence-writer adjudication | **B — HPAC-PPA-001 CONTRACT EVOLUTION REQUIRED** |
| MAJOR (S-4) classification | **VERIFIED** |
| §33C 13-conjunct conjunction | **VERIFIED** (exact, fully fail-closed, no single conjunct sufficient) |
| Same-interpreter production predicate | **ELIMINATED (VERIFIED)** |
| Single trust root / no second root | **VERIFIED** |
| Sibling contracts byte-unchanged | **VERIFIED** (HPAC-001 v2.1, RHAMP-001 v1.0, HPAC-PPA-001 v1.0, HBDC-001 v1.2, RIHAC-001 v2.0, RIASC-001 v3.0, RDGO-001 v3.1, schemas) |
| No new `pawa_failure_code` / `terminal_reason_code` | **VERIFIED** (21 / 41 unchanged) |
| Production source / normative contract changes | **NONE** |
| Real ceremony | **NOT PERFORMED** |
| Runtime | Observed / observe / unavailable — 0 plugins / 0 capabilities |
| First governed runtime external effect | ABSENT / UNREACHABLE |
| **F-5-B2** | **BLOCKED** (pending HPAC-PPA-001 evolution → contract-IV completion → implementation) |
| **F-5** | **CERTIFICATION BLOCKED** |
| **N-16-5** | **NOT CLOSED** |
| **N-16-6 / N-16-7** | **OPEN / UNTOUCHED** (N-16-7 strictly last) |
| REPORTING-UX-1 | open, non-blocking |
| **Recommended successor** | a fresh governed **HPAC-PPA-001 contract-evolution phase** — **NOT begun** |

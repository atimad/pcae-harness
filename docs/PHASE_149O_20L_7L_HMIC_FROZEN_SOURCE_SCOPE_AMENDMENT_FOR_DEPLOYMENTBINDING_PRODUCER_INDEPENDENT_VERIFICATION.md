# Phase 149O.20L.7L — HMIC Frozen Source-Scope Amendment for the DeploymentBinding Producer: Independent Verification

**Phase type:** independent verification (documentation mode). No production
source, no contract, no producer, no admin script, no test owned by an earlier
phase was modified. No repair of any kind was performed.

**Verdict:** **NOT VERIFIED — CONTRACT REPAIR REQUIRED**

The frozen source-scope *membership decision, its production alignment, and its
digest binding are independently verified correct and complete*. The verdict is
withheld because HMIC-001 v1.4 asserts, inside HMIC-REQ-052's own requirement
body and twice more, a statement about this repository's production wiring that
is demonstrably false and was already false when Phase 149O.20L.7K wrote it
(finding **F-7L-1**, §12). A narrow, same-version, contract-text-only repair
phase (**149O.20L.7L.1**) is required before HMIC-001 v1.4 may be relied upon.

---

## 0. Verification wall (restated, and honoured throughout)

1. A scope amendment is not an independently verified scope.
2. A verified source scope is not a certification.
3. A certified source is not authorisation to invoke the producer.
4. A deployed producer is not an authorised binding.
5. An authorised binding is not Boundary C.

Nothing below crosses any of these. This phase reconstructed everything from
immutable Git objects and live code; 149O.20L.7K's own report, counts, digests,
and tests were treated as claims to be checked, never as evidence.

---

## 1. True phase-entry state

| Item | Value |
|---|---|
| Phase-entry commit (`HEAD` at 7L start) | `13a35e346bb8e4e32ef0b101ed128f1df9b8f5b2` |
| `origin/main` at 7L start | `13a35e346bb8e4e32ef0b101ed128f1df9b8f5b2` (identical) |
| `origin/main..HEAD` at 7L start | empty (0 commits) |
| Working tree | clean |
| `pcae health` | healthy |
| `pcae check` | passed |
| `pcae status coherence` | coherent |
| `pcae push check` | clean, `nothing_to_push`; phase-report trust passed; phase-report identity passed; lifecycle review missing (pre-existing) |
| `pcae doctor task-memory` | warnings — pre-existing historical `tasks/done/` entries absent from `tasks/DONE.md`; not remediated (outside allowed-file scope) |
| `pcae runtime inspect` | Observed / observe / unavailable; Permission Broker `execution_unavailable` |
| `pcae notify status` | telegram configured, enabled, ready |

## 2. Immutable pre-7K baseline

- 7K's substantive implementation commit: `1c9f4aa722b85cc0ce55d654d7d078354af94886`.
- Its first parent, independently resolved via `git rev-parse <sha>^`, is
  `6f7073cef2fb2ff839a0ad7e8fee641ba2d53a76` ("Phase 149O.20L.7J: sync
  active-task allowed-file list"). This is the true, immutable pre-7K baseline;
  every "before" figure below is read from that object, not from 7K's prose.
- Two disposable `git worktree` checkouts (pre and post) were created under the
  session scratch directory for all measurement and perturbation work, then
  removed. The real working tree was never made dirty by an experiment.

## 3. Exact HMIC v1.3 → v1.4 contract diff (independently reconstructed)

Both revisions were partitioned on `## <n>.` headings and compared
section-by-section:

| Section | Result |
|---|---|
| Preamble (title/version/status/amendment headers) | changed |
| §17 (HMIC-REQ-050 enumeration, HMIC-REQ-051/052 closure rule) | changed (106 lines) |
| §41 (attack matrix) | changed — heading `38 Scenarios` → `39 Scenarios`, one row appended |
| §54 (149O.20L.1A repair record) | changed **only** by an appended `---` separator |
| §55 | **new** |
| **All other sections (§0–16, §18–40, §42–53)** | **byte-identical** |
| Sections removed | none |

Attack-matrix rows 1–38 are byte-identical; row 39 is appended; row numbering is
sequential 1..39 and the heading count matches. No pre-existing attack row was
weakened, renumbered, or re-scoped.

**Correction to 7K's own wording.** 7K's phase metadata and `PROJECT_STATUS.md`
state "Original sections 0-54 byte-untouched". That is imprecise: §17 and §41
were (necessarily) edited, and §54 gained a separator. §55's own preamble is
precise — it claims only that the *history* sections (§0–48, §49–52, §53, §54)
were not modified, which is true up to the separator. Recorded as **F-7L-6**
(documentary only).

## 4. Version-policy verification

`**Version:** 1.3` → `**Version:** 1.4`; live `HEAD` still v1.4. §55.14's
rationale was independently checked against this contract's own precedent: v1.0
→ v1.1 (§50, new limb + 2 files), v1.1 → v1.2 (§51), v1.2 → v1.3 (§53, new limb
+ 3 files) were minor bumps for scope widenings; §52 and §54 were same-version
in-place repairs of defects in existing bindings. This amendment adds a closure
anchor and two members without redefining any field, schema, or algorithm.
**A minor bump to v1.4 is the correct classification** — not v2.0, not a
same-version repair. Verified.

## 5. HMIC-REQ-052 verification (read from v1.4 directly)

Limb (c) at v1.4 binds, in addition to its v1.3 call-graph anchor, the
`create_deployment_binding` / `rotate_deployment_binding` /
`revoke_deployment_binding` functions in `core/hatp_deployment_binding_admin.py`
and their sole intended Protected Admin ceremony caller
`scripts/hatp_deployment_binding_admin.py`, transitively.

Independently confirmed at the source level:

- `hatp_class_b_conformance.py` does **not** import the producer (AST walk, §7).
  So the producer genuinely is *not* reachable from
  `verify_class_b_deployment_conformance`'s own call graph — the v1.3 text did
  not cover it, and the "second, non-call-graph anchor" construction (mirroring
  limb (b)'s v1.1 dual anchor for `scripts/hatp_certification_admin.py`) is the
  structurally correct repair model, not a fourth limb.
- The data path the limb relies on exists: `_check_deployment_identity` in
  `hatp_class_b_conformance.py` reads registry state through already-frozen
  `hatp_bootstrap.py` primitives, against exactly the `registry.json` the
  producer writes.

**Limb (c) is precise and correct in its binding effect.** Its final paragraph,
however, contains the false factual claim recorded as **F-7L-1** (§12).

## 6. HMIC-REQ-050 verification

The requirement gives both a normative cardinality ("exactly these thirty
files, no more, no fewer") **and** an explicit fenced enumeration. The
enumeration is the operative artifact; "thirty" is a redundant, checkable
restatement of it, and production carries the same redundancy as
`assert len(_FROZEN_AUTHORITY_BEARING_FILES) == 30`. The two agree.

## 7. Production frozen-set reconstruction and contract/implementation synchronisation

Read live from `src/pcae/core/hatp_mandatory_certification.py`:

- `_FROZEN_SRC_PCAE_RELATIVE_FILES` — 23 entries
- `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES` — 7 entries
- `_FROZEN_AUTHORITY_BEARING_FILES` — 30 entries
- `_CONTRACT_IDENTITY_FILES` — 5 pairs (`HMRC-001`, `HATP-001`, `HSCE-001`,
  `RAE-001`, `HBDC-001`); `derive_contract_versions()` on the live repository
  returns exactly those five keys.

HMIC-REQ-050's enumeration was re-extracted from the contract document by an
independent parser (fenced block after the requirement heading, first token per
line). **Contract and production agree entry-for-entry, in the same order, with
identical spelling, at 30 entries.** Zero divergence — no contract member absent
from code, no code member absent from contract, no count disagreement, no path
spelling mismatch.

Canonical order: `_frozen_canonical_paths()` prefixes the first
`_FROZEN_SRC_PCAE_RELATIVE_COUNT` entries with `src/pcae/`, leaves the rest
repository-root-relative, and returns the result **lexicographically sorted**
(HMIC-REQ-056). Order therefore does not contribute to the digest — verified
empirically in §10.

## 8. Exact pre/post membership delta

Pre-7K (from `6f7073ce`): **28** entries. Post-7K (from `1c9f4aa7`, and at
`HEAD`): **30** entries.

**Added (exactly two):**

- `core/hatp_deployment_binding_admin.py` (appended to the `src/pcae/`-relative bucket)
- `scripts/hatp_deployment_binding_admin.py` (appended to the root-relative bucket)

**Removed: none.** The relative order of every pre-amendment entry is preserved
(each addition lands at the end of its own bucket, so the old list is a
subsequence, not a prefix, of the new one — a detail 7K's "presentation order"
prose leaves implicit).

## 9. Producer and admin-script inclusion proofs (independent, not by analogy)

**`src/pcae/core/hatp_deployment_binding_admin.py` — MUST INCLUDE.** Read
directly: it owns `create_deployment_binding`/`rotate_deployment_binding`/
`revoke_deployment_binding`; the idempotency comparison
(`_binding_fields_equal_for_idempotency` over `_COMPARED_AUTHORITY_FIELDS`); the
fail-closed branches (`DuplicateConflictingBindingError` on a conflicting or
revoked existing entry — `create()` never reactivates a revoked binding); the
atomic write (`_atomic_write_registry`, `os.replace`); the mandatory read-back
verification (`_read_back_and_verify`, which re-parses through the production
read path and rejects any mismatch); and the `fcntl`-based transition lock. A
byte edit here changes what `DeploymentBinding` becomes durably authoritative.
Authority-bearing on its own terms.

**`scripts/hatp_deployment_binding_admin.py` — MUST INCLUDE.** Not inert
delegation: it owns the operator confirmation gate (`_prompt_confirm`, bypassable
only via an explicit `--assume-yes`), the argument grammar for every
authority-bearing field (`--principal-id`, `--signer-key-id`,
`--provider-profile`, `--authority-scope`, all `required=True`), the
`AuthorityEvidence(...)` construction from raw CLI strings, and the
create/rotate/revoke operation selection. A byte edit here (defaulting
`--assume-yes`, dropping a required field, mis-mapping a subcommand) changes what
authority evidence reaches the producer without touching the producer.

**Certification-admin comparison.** `scripts/hatp_certification_admin.py` was
read and compared. It is the same shape of artifact — a repository-root-relative
privileged ceremony script that constructs authority evidence and gates a
trust-store mutation — and has been frozen since v1.1 under limb (b)'s second
anchor. The source-scope policy is internally consistent. This comparison is
recorded as *corroborating* evidence; the inclusion conclusions above stand
without it.

## 10. Privileged-writer inventory (independent repository sweep)

`scripts/` contains exactly two Python files; both are frozen. Sweeping all of
`src/` and `scripts/` for modules that touch `registry.json`,
`certifications.json`, `certification-bindings.json`, `DeploymentBinding`, or
repository identity yields thirteen files. Classification:

| File | Disposition |
|---|---|
| `core/hatp_deployment_binding_admin.py` | frozen (v1.4) |
| `scripts/hatp_deployment_binding_admin.py` | frozen (v1.4) |
| `scripts/hatp_certification_admin.py` | frozen (v1.1) |
| `core/hatp_bootstrap.py`, `core/repository_identity.py`, `core/hatp_mandatory_certification.py`, `core/hatp_mandatory_cutover.py`, `core/human_approval_trusted_provenance.py`, `core/hatp_class_b_conformance.py`, `core/hatp_class_b_topology_verifier.py` | frozen (limb (a)/(c) first anchor) |
| `core/templates.py` | not a writer of any authority state (template inventory only) — correctly non-frozen |
| `commands/init.py` | **not frozen** — sole production caller of `ensure_repository_identity`; see **F-7L-3** |
| `core/hatp_signing_ceremony.py` | **not frozen** — see **F-7L-4** |

No omitted writer of `DeploymentBinding` state exists. The two flagged files are
pre-existing, adjacent scope questions outside 149O.20L.7K's declared scope.

## 11. Transitive dependency graphs and the authority-path matrix

Independent `ast.parse` + `ast.walk` import extraction over the current on-disk
bytes of both new members (7K's narrative was not consulted):

- `core/hatp_deployment_binding_admin.py` → `pcae.core.hatp_bootstrap`,
  `pcae.core.paths`, `pcae.core.provenance`, `pcae.core.repository_identity`;
  stdlib `contextlib`, `dataclasses`, `datetime`, `enum`, `fcntl`, `json`, `os`,
  `pathlib`, `re`, `tempfile`, `typing`.
- `scripts/hatp_deployment_binding_admin.py` → `pcae.core.hatp_bootstrap`,
  `pcae.core.hatp_deployment_binding_admin`, `pcae.core.repository_identity`;
  stdlib `argparse`, `pathlib`, `sys`.

This reproduces §55.3 exactly. Neither file contains `importlib.import_module`,
`__import__`, `subprocess`, or `os.system` — no dynamic import or path-override
escape hatch, so the existing environment-lock assumptions continue to govern
import resolution and no new reachability is introduced.

**Complete authority-path coverage matrix (independently derived):**

| Component | Authority effect | HMIC-frozen? | Basis | Evidence |
|---|---|---|---|---|
| `scripts/hatp_deployment_binding_admin.py` | operator gate, `AuthorityEvidence` construction, operation selection | **Yes (v1.4)** | limb (c) 3rd anchor | §9 |
| `core/hatp_deployment_binding_admin.py` | create/rotate/revoke decision, idempotency, fail-closed branches, durable write | **Yes (v1.4)** | limb (c) 3rd anchor | §9 |
| `hatp_bootstrap.py` — `DeploymentBinding` schema, `HATPTrustStore`, `_parse_registry_document`, atomic-write idiom, `deployment_binding_matches` | defines and matches the authoritative record | Yes (v1.1) | limb (a) | §7 |
| `repository_identity.py` — `read_repository_identity` | selects the binding subject | Yes (v1.1) | limb (a) | §7 |
| `hatp_bootstrap.resolve_canonical_deployment_root` | selects the bound root | Yes (v1.1) | limb (a) | §7 |
| `hatp_class_b_conformance.py` — `_check_deployment_identity` | folds the match into the verdict | Yes (v1.3) | limb (c) 1st anchor | §7 |
| `hatp_mandatory_cutover.py` — 8th readiness term | consumes the Class-B verdict | Yes (v1.1) | limb (a) | §12 |
| `pcae.core.paths` (`HarnessPath`) | path value type | No — intentional | §49/§50/§53 precedent | §11 (omitted-helper attack) |
| `pcae.core.provenance` (`append_provenance_event`) | post-mutation audit sink | No — intentional | §55.5 Category B | §11 (omitted-helper attack) |
| Python interpreter / stdlib | — | No — out of scope | HMIC-REQ-065 | residual trust, disclosed |

**No unaccounted executable component remains on the create-to-verdict path.**

**Omitted-helper attack.** For each non-frozen PCAE helper reached by the pair,
the question "could a byte edit here alter binding content, a lifecycle
decision, root selection, privilege-confirmation gating, audit-required success
behaviour, or serialisation?" was asked directly against the source:

- `pcae.core.paths` — a path value type with no decision logic. No.
- `pcae.core.provenance` — reached only through the producer's `_audit` helper.
  Independently verified by reading the call ordering: `_atomic_write_registry`
  and `_read_back_and_verify` both complete, and the transition lock is
  released, **before** `_audit` runs, in all three operations. It therefore
  cannot change what is written or what the read path subsequently matches. Its
  only failure mode is losing audit evidence for an already-durable mutation —
  which is exactly 7J's §17 finding, carried forward unchanged, not repaired
  here. The exclusion is correct. *(Nuance for the record: `pcae.core.provenance`
  itself imports `subprocess` transitively via `pcae.core.git_status`, so §55.5's
  Category-D phrasing "the producer pair invokes no external binary or
  subprocess" is true of the two files directly but not of their full transitive
  closure. Immaterial to the exclusion, which rests on call ordering, not on
  subprocess absence.)*

**Standard-library exclusion.** The thirteen stdlib modules are not treated as
PCAE frozen source; HMIC-REQ-065 already names the interpreter and stdlib as an
explicit out-of-scope transitive boundary. Residual trust in them is unchanged
and disclosed, not assumed away.

## 12. Findings

### F-7L-1 — **Blocking (contract repair required).** HMIC-001 v1.4 asserts zero production consumers of `verify_class_b_deployment_conformance`; there is one.

HMIC-001 v1.4 states, in three places:

1. inside **HMIC-REQ-052 limb (c)'s own requirement body** — "as of v1.4, no
   readiness, certification, or activation code path calls
   `verify_class_b_deployment_conformance` or consults its result (§53/§55
   reconfirm zero production consumers)";
2. in **§55.4** — presented as an independently re-derived result of this
   phase's own search;
3. in **attack-matrix row 39, clause (a)** — used to justify "not functionally
   load-bearing".

This is false. `src/pcae/core/hatp_mandatory_cutover.py` line 74 imports
`verify_class_b_deployment_conformance` and line 952 calls it inside
`_assess_hatp_mandatory_activation_readiness_at_root`, appending the resulting
`class_b_deployment_conformance_satisfies_readiness` check to the readiness
vector that determines `ready`. That wiring was introduced by **Phase
149O.20L.3** (commit `e2ccb7a3`, HMRC-REQ-086–100, HMRC-001 v1.1 §19A) and
independently verified by **149O.20L.4** — both of which are ancestors of 7K's
own phase-entry commit `6f7073ce`. The live readiness vector has **eight**
terms, the eighth being the Class-B verdict.

The claim was true at v1.3 (§53, Phase 149O.20K) and became false at 149O.20L.3.
7K reasserted it at v1.4 by citing §53 rather than re-measuring, and recorded it
in §55.4 as though independently reconfirmed.

**Consequence.** The scope amendment itself is *more* justified, not less: the
Class-B verdict is a live activation-readiness term today, so the newly bound
producer pair sits on a path that already reaches a production readiness
decision. No live security consequence exists at this moment, because attack row
39's clauses (b) and (c) remain true — no real `DeploymentBinding` has ever been
created and no HMIC certification exists. But limb (c)'s "anticipatory" framing
and row 39's risk characterisation both understate the current state, inside a
frozen normative document.

**Disposition:** not repaired here (this phase is verification-only). Requires a
narrow, contract-text-only, same-version repair phase — the same shape as §52
(B-149O.20D-1) and §54 (B-149O.20L.1-1). See §18.

### F-7L-2 — Non-blocking (descriptive). Stale `Depends on` header for HBDC-001.

HMIC-001 v1.4's `**Depends on (current, HMIC-unamended):**` line reads
`... HBDC-001 v1.0`. Live HBDC-001 has been **v1.1** since Phase 149O.20L.7G.
This is precisely the defect class of B-149O.20L.1-1 (§54), where the same line
was stale for HMRC-001 and was repaired in place at the same version. 7K edited
the surrounding header block and did not repair it.

Verified harmless to mechanism: `derive_contract_versions()` reads live document
headers and correctly returns `HBDC-001: 1.1`; §20's live-header comparison is
unaffected. Descriptive only. Fold into the same repair phase.

### F-7L-3 — Non-blocking observation (pre-existing, out of 7K's scope). RepositoryIdentity writer caller is not frozen.

The amendment's own precedent binds a producer module together with its sole
intended caller. `core/repository_identity.py` (the RepositoryIdentity writer)
is frozen; `src/pcae/commands/init.py` — the only production caller of
`ensure_repository_identity` — is not, even though it is reached from the frozen
`cli.py`. All identity *content* logic lives in the frozen module and the caller
supplies only `HarnessPath.cwd()`, so the exposure is narrow. Recorded, not
repaired: it is a limb-(a)-scope question predating 7K, and HMIC-REQ-052
explicitly forbids adding a file merely because a frozen file imports it.
Recommend a future source-scope review phase.

### F-7L-4 — Non-blocking observation (pre-existing). `hatp_signing_ceremony.py` is a readiness input but is not frozen.

`hatp_mandatory_cutover.py` dynamically imports `pcae.core.hatp_signing_ceremony`
and turns its importability into the readiness term
`hsce_signing_implementation_available`. The module is not in the frozen set.
Assessed against the contract's own authority-sensitivity criterion: only an
import-*breaking* edit can change the term, and that fails closed to `False`.
Exclusion is therefore defensible. Pre-existing; unchanged by 7K.

### F-7L-5 — Non-blocking observation (pre-existing). Stale "not yet operative" caveats in the attack matrix.

Rows #33/#34/#36/#37/#38 carry caveats of the form "until production identity
derivation is realigned to HMIC-REQ-050's twenty-{four,five,eight}-file set (a
distinct future phase), production still computes the …-file digest". Production
has been realigned since 149O.20F (25/5) and 149O.20K.2 (28), and is now at 30.
Every one of these caveats was already stale **before** 7K; none was introduced
by it. Row 39 correctly does not repeat the error for itself. Descriptive only;
fold into the same repair phase.

### F-7L-6 — Documentary. "Sections 0-54 byte-untouched" is imprecise.

See §3. 7K's metadata/status prose overstates; §55's own preamble is accurate.

### F-7L-7 — Non-blocking. Guard-test exemption is broader than necessary.

7K widened two 7I/7J guards
(`test_no_src_pcae_module_imports_the_producer_except_itself`,
`test_producer_module_not_imported_anywhere_in_src_pcae_except_itself`) to skip
`hatp_mandatory_certification.py` wholesale. Both perform a **textual** search,
so a genuine `import` of the producer added to that module would no longer be
caught by either guard. The exemption is legitimate in motivation (the frozen
tuple must name the path as a literal string) but is implemented at file
granularity rather than at occurrence granularity. See §15 for the strictly
stronger replacement this phase adds as its own artifact.

## 13. Byte-identity proofs (Git object comparison, not diff inference)

Blob SHA at `6f7073ce` vs `1c9f4aa7` vs `HEAD`, all identical:

| Path | Blob |
|---|---|
| `src/pcae/core/hatp_deployment_binding_admin.py` | `c7950f302ba5714764de5fa0fd86699a07cfad1c` |
| `scripts/hatp_deployment_binding_admin.py` | `286db838d573ef9311a6d0df78a6842b5f4ef296` |
| `src/pcae/core/hatp_bootstrap.py` (HBDC consumer / read path) | `cda8e518d5d8794922ebdcd195c3886228fe8f2f` |
| `src/pcae/core/repository_identity.py` | `eae1db10dcc0c6cdf9267574f60615fdbda55143` |
| `src/pcae/core/hatp_class_b_conformance.py` | `be1ed4df7929224135e6dbcbdc1e4ccafc72e9ab` |
| `src/pcae/core/hatp_class_b_topology_verifier.py` | `af961e15442be8b91f6f093986386924bd71bf6a` |
| `src/pcae/core/hatp_environment_lock_verifier.py` | `4f94ff10cbfe1161918f753b1f9427c3415a2a46` |
| `src/pcae/core/hatp_providers.py` | `109486bc8dd75337acf0511b82cc010fe76094e2` |
| `src/pcae/core/hatp_fido2_provider.py` | `ff48e2d9d25820ac5f9c42aec33b0521b5bc7d37` |
| `src/pcae/core/hatp_piv_provider.py` | `1b96858353f81e12b93b3db99a777c80a7be433c` |
| `src/pcae/core/hatp_hardware_credentials.py` | `bbfb72a64bffe614beb9f30b01baf96afaf7c7b7` |
| `scripts/hatp_certification_admin.py` | `f9fbcc8bbf526a9870919f2164e94e077d8ff79b` |
| `docs/contracts/HATP_CLASS_B_DEPLOYMENT_CONTRACT.md` (HBDC-001 v1.1) | `ccc4efba78b39633b63f25e1415b915598a49772` |

**No behavioural surface changed.** Additionally, an AST-level comparison of
`hatp_mandatory_certification.py` across the amendment shows every function and
class body byte-identical, and the only module-level constants that changed are
`_FROZEN_SRC_PCAE_RELATIVE_FILES` and `_FROZEN_REPOSITORY_ROOT_RELATIVE_FILES`.
No derivation logic was touched.

## 14. Digest results (measured, decomposed, and perturbed)

All four cells computed against the real `derive_implementation_scope_digest`
mechanism in disposable worktrees:

| | 28-member scope | 30-member scope |
|---|---|---|
| **pre-7K tree** (`6f7073ce`) | `d5129ce26c98b595c6583ec2097274d9257c1f73b2b347503f5b66d7286996ca` | `3a74752f504555cb9569fc0b68adfdf122cf8332542aece7b41244e4de2d9e3d` |
| **post-7K tree** (`HEAD`) | `008762bb64c1558446078d9e5fd825d0cd9926436aba1dfd7882c925b82e1fa2` | `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` |

The live digest at `HEAD` on the real working tree is
`65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8`, matching the
post/30 cell — and matching 7K's reported value, which is therefore
independently confirmed rather than accepted. `derive_implementation_commit()`
returns `13a35e346bb8e4e32ef0b101ed128f1df9b8f5b2`.

**Decomposition of the change (`d5129ce2…` → `65ff8ab0…`) into independent causes:**

1. **File bytes that already existed** — `d5129ce2…` → `008762bb…`: same
   28-member scope, different tree. Attributable solely to
   `hatp_mandatory_certification.py`'s own bytes changing (it is itself a frozen
   member since v1.1). This is §55.16's "changes twice over", confirmed.
2. **Source membership expansion** — `008762bb…` → `65ff8ab0…`: same tree,
   scope widened by the two new members.
3. **Contract identity** — *separate and not conflated*: HMIC-001 is **not**
   itself a member of its own frozen set, so the v1.3 → v1.4 document edit does
   **not** enter `implementation_scope_digest` at all. HMIC's contract identity
   is carried by `derive_contract_versions` (five members, live-header parsed),
   which returns `{HMRC-001: 1.1, HATP-001: 1.0, HSCE-001: 1.1, RAE-001: 1.0,
   HBDC-001: 1.1}` — unchanged in membership by this amendment, and correctly
   reflecting HBDC-001 v1.1 despite F-7L-2's stale prose header.

**Perturbation results** (disposable scratch tree materialised from Git blobs):

| Experiment | Result |
|---|---|
| Perturb `core/hatp_deployment_binding_admin.py`, 30-member scope | digest **changes** |
| Perturb `scripts/hatp_deployment_binding_admin.py`, 30-member scope | digest **changes** |
| **Pre-amendment control:** perturb either new member under the 28-member scope | digest **unchanged** — the historical gap demonstrated, not asserted |
| **Non-member control:** perturb `src/pcae/core/provenance.py` (a real, deliberately excluded PCAE dependency of the producer) | digest **unchanged** — no accidental scope broadening |
| Non-member controls: `hatp_signing_ceremony.py`, `commands/init.py` | digest **unchanged** |
| Remove `core/hatp_deployment_binding_admin.py` | `FrozenFileDerivationError: frozen file does not exist: …` — **fails closed**, no partial digest |
| Remove `scripts/hatp_deployment_binding_admin.py` | same — fails closed |
| Replace either new member with a symlink | `FrozenFileDerivationError: frozen file path component is a symlink, refusing` (HMIC-REQ-061) |
| Reverse each bucket's literal order | digest **unchanged** — order is not digest-relevant (HMIC-REQ-056 sort confirmed empirically) |
| Duplicate a member in the literal tuple | 31 canonical paths, 30 unique; digest **changes** deterministically (double-hashed, never silently deduplicated) — see below |

**Path normalisation over all 30 entries:** every canonical path is
repository-relative, POSIX-separated, free of `.`/`..`/empty segments and
backslashes, has no duplicate normalised alias, exists, is a regular file, and
is not a symlink. `_resolve_and_reject_unsafe_frozen_file` additionally walks
every parent component up to the repository root rejecting symlinks, and
`_read_frozen_file_bytes` opens with `O_NOFOLLOW` plus an `fstat` re-check —
TOCTOU-resistant. Verified.

**Duplicate-membership semantics** are a latent ambiguity of the mechanism, not
of this amendment: `_frozen_canonical_paths()` sorts but neither deduplicates
nor rejects, so a duplicated literal would be hashed twice, yielding a different
but still fully deterministic digest. It is unreachable from caller input
(HMIC-REQ-051: there is no caller-suppliable path list), no duplicate exists in
the live 30-entry set, and the behaviour is unchanged by 7K. Recorded as a
characterised property, not a finding against this phase.

## 15. Guard-test amendment analysis

7K changed three tests in 7I/7J files. Each was independently inspected:

1. `test_hmic_frozen_file_set_does_not_yet_include_deployment_binding_admin_files`
   → `…now_includes…`. **Legitimate.** The original assertion's own failure
   message instructed exactly this flip once the gap closed. It now guards
   against silent reopening. Not a weakening.
2. & 3. The two "no `src/pcae` module imports the producer" guards were widened
   to skip `hatp_mandatory_certification.py`. **Narrow weakening — F-7L-7.** Both
   guards match on raw text, so the file-wide exemption also suppresses
   detection of a genuine import added to that module.

**This phase's own replacement** (a 7L-native verification artifact, not a
migration or repair of 7K's tests): an AST-level guard with **no** per-file
exemption, asserting that no module under `src/pcae` has an `Import`/`ImportFrom`
node naming `hatp_deployment_binding_admin`, plus a companion asserting that
`hatp_mandatory_certification.py`'s references are exclusively non-import path
data. This is strictly stronger than either amended guard and covers the residue.

**Agent reachability re-verified whole-tree:** zero AST-level imports of the
producer anywhere in `src/pcae`; the only textual occurrences in
`hatp_mandatory_certification.py` are at lines 952, 983 and 1008 — a docstring
comment, the frozen tuple entry, and a comment. `cli.py` contains no
`deployment_binding` command surface. **Freezing the files did not make them
callable from any agent or runtime path.**

## 16. Regression A/B and historical-pin adjudication

Two disposable worktrees, identical invocation
(`pytest -m fast_green -q -p no:randomly -n auto`), full sorted `FAILED`/`ERROR`
node-ID diff — not aggregate-count inference:

| Tree | Result |
|---|---|
| pre-7K (`6f7073ce`) | **215 failed, 7628 passed, 4 skipped, 9 errors** (224 failing node IDs) |
| post-7K (`HEAD`) | **253 failed, 7614 passed, 4 skipped, 9 errors** (262 failing node IDs) |
| Net-new | **38** |
| Resolved | **0** |

The net-new count independently reproduces 7K's reported 38. Every one of the 38
was classified by node ID:

| Group | Count | Nature |
|---|---|---|
| 149O.20K / 20K.1 / 20K.2 / 20K.3 | 16 | "exactly 28 entries", "38 attack rows", "five union sources", "status line names 20K" — self-pins on the superseded 28-file/v1.3 identity |
| 149O.20L.1A / 1B | 6 | "HMIC still v1.3", "exactly 28 files" |
| 149O.20L.3 / 20L.4 | 6 | byte-identity-since-phase-entry pins on HMIC-001 and `hatp_mandatory_certification.py` |
| 149O.20L.7D.8 / 7D.10 / 7E | 9 | "exactly 28", "v1.3 unchanged candidate→HEAD", historical digest recomputation against a 28-era tree |
| 149O.20L.7I | 1 | "no `docs/contracts/**` file may change in an implementation phase" |

Three were opened and read in full to confirm the classification rather than
inferring it from the name: `test_implementation_scope_digest_independently_recomputed`
fails with `FrozenFileDerivationError: frozen file does not exist:
scripts/hatp_deployment_binding_admin.py` (the current 30-member constant applied
to a historical tree that predates the file);
`test_three_repaired_verifiers_are_hmic_frozen_members` fails on
`assert 30 == 28`; `test_no_hmic_hatp_hmrc_contract_modified` fails because the
HMIC contract legitimately changed. All three are textbook identity-pin
migration, not regressions.

**Zero net-new failures are security, authority, or behavioural regressions.**
Note that with random ordering disabled, the `test_backend_cli.py` order-dependent
flake 7K reported as 2 of its 38 does not appear; this phase's 38 are all
historical self-pins. These historical suites are intentionally left as
historical evidence — this phase migrates nothing.

**Regression verdict: REGRESSION CLEAN WITH EXPECTED HISTORICAL IDENTITY-PIN
MIGRATION.** The raw unfiltered Fast Green tally at `HEAD` is red (253 failed /
7614 passed) and is *not* claimed to be green; the red is a pre-existing,
attributed condition carried since well before 7K (215 failures already present
at the pre-7K baseline).

**Security-relevant suites re-run and green:** this phase's own 60 tests, plus
the full HMIC/HBDC/producer/Class-B/source-identity families outside the
enumerated historical pins showed no new unexplained failure in the A/B diff.

## 17. Deployment currency, Dell divergence, and first-use status

**Current Mac source candidate.** After 7L's finalisation commits, the exact
full source commit that would *eventually* need deployment is this phase's own
`HEAD` (recorded in `.pcae/phase-completion-metadata.json` and in §21). It is
**not** authorised for Dell. No CHGR names it. Naming it here is bookkeeping,
not authorisation.

**Dell divergence — reconstructed entirely from Git objects; zero Dell access
of any kind, read or write, was performed this phase.** Dell's pinned source is
`28bf137b5dc95d024e8913b678dce0501a46fd0f` (149O.20L.7D.7), `HEAD` is **78
commits** ahead. Exact divergence classes:

| Class | Dell (`28bf137b`) | Mac (`HEAD`) |
|---|---|---|
| DeploymentBinding producer | **absent** (`src/pcae/core/hatp_deployment_binding_admin.py` does not exist at that SHA) | present |
| Admin ceremony script | **absent** | present |
| HBDC-001 | **v1.0** | v1.1 |
| HMIC-001 | **v1.3** | v1.4 |
| Frozen membership | 28 | 30 |
| `implementation_scope_digest` | `4e3452ba…` (149O.20L.7E's measured value) | `65ff8ab0…` |

**Boundary-P status: preserved as INDEPENDENTLY VERIFIED PHYSICAL PROVISIONING**
(149O.20L.7E). Nothing in this phase bears on physical host topology; source
currency is a separate axis and is now four amendments stale on Dell.

**Live HBDC statement, version-qualified precisely:** Dell currently executes
the **HBDC-001 v1.0-era** deployed source. It is *not* claimed that Dell executes
HBDC-001 v1.1, nor that Dell's tree contains the DeploymentBinding producer —
independently disproven above. Future redeployment is a prerequisite for any
first use; it was **not** performed, prepared, or authorised here.

**Certification consequence: none.** No HMIC certification exists on any host
(`/Library/Application Support/PCAE/HATP/trust-store` does not exist on this
Mac; 149O.20L.7E found Dell's registry directory empty). A source-scope
amendment therefore has no live certification-revocation consequence.

**First use remains unauthorised — verified, not assumed.** No `registry.json`,
`repository-identity.json`, `deployment-binding.json`, `certifications.json`,
`certification-bindings.json`, or `active-certification.json` exists in this
repository or in the production trust-store root. No decision session, no
first-use CHGR, no `RepositoryIdentity`, no `DeploymentBinding`, no election, no
certification. A verified source scope still does not authorise use.

## 18. Carried-forward findings (untouched, unrepaired)

| Finding | Status |
|---|---|
| **149O.20L.7J §31 — HMIC frozen-source-membership gap** (no separate alpha ID; canonically "7J §31") | **REPAIR VERIFIED AT THE MEMBERSHIP/DIGEST LAYER; FINDING NOT CLOSED** — the source-scope closure is independently verified complete (§7–§14), but F-7L-1 requires HMIC-001 v1.4 to be repaired before the amendment carrying that closure can be relied upon. 7L therefore does **not** close 7J §31. |
| **HMIC-REQ-103 revocation-does-not-invalidate-existing-validation** | carried unchanged, not repaired, not claimed repaired |
| **7J §17 producer audit-failure-after-mutation exception-type gap** | carried unchanged; independently re-confirmed still present (audit runs after the durable write; `_audit` raises uncaught) |
| **`hatp_bootstrap.py::_parse_iso_timestamp` permissive parser (7I/7J)** | carried unchanged |
| **Stale historical identity-pin tests** | carried unchanged as historical evidence; nothing migrated |
| **HMIC-REQ-063 (import-shadowing / executed-code binding, out of scope)** | **carried unchanged and byte-untouched** by this amendment. Explicitly restated: digest membership proves on-disk byte identity of the frozen set, **not** that the executing interpreter resolved its imports to those files. Nothing in §14 should be read as executed-runtime provenance. |
| **W-1, B-149O.19.3-1, B-149O.20D-1, CBV-S1** | independently re-confirmed still closed/bound; no regression (§ parametrized guards) |

## 19. Verdict

**NOT VERIFIED — CONTRACT REPAIR REQUIRED.**

Independently verified correct and requiring **no** change:

- the inclusion decision for both new members, justified from source behaviour;
- the exact 30-member set, its two additions, its zero removals, its ordering;
- contract ↔ production synchronisation (entry-for-entry, zero divergence);
- the digest binding, its per-member sensitivity, its old-set insensitivity, its
  non-member control, its fail-closed behaviour, its path/order/duplicate
  semantics;
- the absence of any producer, admin-script, consumer, or contract-corpus
  behavioural change;
- transitive coverage — no unaccounted executable component on the
  create-to-verdict path;
- agent unreachability, first-use non-authorisation, Dell non-access.

Withheld because HMIC-001 v1.4 asserts a materially false fact about this
repository's production wiring inside HMIC-REQ-052's requirement body, in §55.4
(presented as an independently derived result), and in attack row 39's risk
justification (**F-7L-1**), compounded by a stale contract-dependency header
(**F-7L-2**) of the same class the contract has already repaired once (§54).

"VERIFIED WITH NON-BLOCKING FINDINGS — GAP CLOSED" was considered and rejected:
a repair phase is genuinely required, and calling a required repair
"non-blocking" would be self-contradictory. "NOT VERIFIED — SOURCE-SCOPE REPAIR
REQUIRED" and "NOT VERIFIED — TRANSITIVE AUTHORITY SCOPE INCOMPLETE" were
considered and rejected: the membership and its transitive closure are
independently verified complete. The defect is confined to contract text.

## 20. Recommended next phase

**149O.20L.7L.1 — HMIC-001 v1.4 Consumer-Status and Dependency-Header Repair.**
Narrow, contract-text-only, **same-version** in-place repair (the §52/§54
precedent shape — no version bump, no membership change, no production change):

1. Correct HMIC-REQ-052 limb (c)'s closing paragraph, §55.4, §55.15, and attack
   row 39 clause (a) to state the true consumer status: the Class-B verdict has
   been an activation-readiness term in `hatp_mandatory_cutover.py` since
   149O.20L.3, and row 39's "not functionally load-bearing" rests on clauses (b)
   and (c) alone (**F-7L-1**).
2. Update the `Depends on (current, HMIC-unamended)` header to `HBDC-001 v1.1`
   (**F-7L-2**).
3. Optionally refresh the stale "not yet operative" caveats in rows #33/#34/#36/
   #37/#38 (**F-7L-5**), and tighten the two 7I/7J guard exemptions from file
   granularity to occurrence granularity (**F-7L-7**).

Then **149O.20L.7L.2** — its independent verification — after which 7J §31 may
be closed.

**Architecture question to be answered by a later, separate phase (deliberately
not decided here).** Reconstructed from the primary contracts and status, the
open first-use sequencing question is a genuine three-way choice, and none of
the primary sources settles it:

- **(A) Redeploy first.** The producer does not exist on Dell at all
  (`28bf137b`, §17). If an election must ratify an *exact* preview of the
  binding to be created, the producer must already be on Dell to materialise it,
  so source redeployment must precede election.
- **(B) Bind a source SHA at proposition time.** The election CHGR could name
  the candidate SHA, with deployment + `RepositoryIdentity` creation + binding
  creation all executed inside one governed execution afterwards.
- **(C) Two CHGRs.** Source deployment and first-use binding are separate
  authority acts requiring separate human confirmations — consistent with how
  149O.20L.7D.11's redeployment already required its own CHGR
  (`chgr-0e37ed1340b14311826722c4dbf3e856`), which notably did *not* name a
  binding.

The likely next-phase title once 7K.1/7K.2 land is
**"149O.20L.7M — DeploymentBinding First-Use Sequencing Architecture"**
(architecture/decision only; no binding, no election, no Dell mutation).
**7L does not decide this.**

## 21. Governance record

- Deliverables: this document and
  `tests/test_phase_149o_20l_7l_hmic_frozen_source_scope_amendment_independent_verification.py`
  (60 tests, all passing; independent of 7K's own suite, which was never
  imported or used as an oracle).
- Two disposable `git worktree` checkouts were created under the session
  scratch directory and removed; the main working tree was never left dirty by
  an experiment.
- No raw `git commit`/`git push`, no `--no-verify`, no force push. All commits
  via `pcae commit`.
- No Dell access of any kind. No producer invocation. No trust-store mutation.
- No source repair, no producer repair, no test migration.

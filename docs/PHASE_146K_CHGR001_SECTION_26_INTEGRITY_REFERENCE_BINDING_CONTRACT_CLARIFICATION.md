# Phase 146K — CHGR-001 §26 Integrity-Reference Binding Contract Clarification

## 1. Executive Summary

Phase 146J independently established a genuine construction-time digest
cycle between `human_governance_record.integrity_ref` and
`governance_record_integrity.payload_digest` (CHGR-REQ-197 vs.
CHGR-REQ-203), separate from and prior to a repairable pure verification
defect affecting `confirmation_evidence_ref`/`provenance_ref`. This phase
independently reconstructed that cycle from primary sources (contract
text, schemas, and both `record.py`/`verification.py`), evaluated six
candidate resolution models, and selected **Model C — directed one-way
integrity binding**: `integrity_ref` identifies its sibling by stable
identity only; the sibling proves the binding back, cryptographically,
through `governance_record_integrity.payload_digest ==
human_governance_record.record_digest`. This model requires **zero**
schema changes — it formalizes behavior `record.py` (construction) and
`verification.py` (verification) already independently exhibit — and is
frozen as CHGR-001 v1.3, §30, CHGR-REQ-210 through CHGR-REQ-216. Every
already-produced Chapter 146 bundle is classified valid under the
clarified semantics without migration or regeneration. No implementation,
schema, or verification code was modified this phase. **Verdict:
CONTRACT CLARIFICATION FROZEN.**

## 2. Authorization and Scope

Authorized by human instruction citing Phase 146J's `ROOT CAUSE
ESTABLISHED WITH OBSERVATIONS` verdict and Classification D (Combined
defect): `confirmation_evidence_ref`/`provenance_ref` are pure
verification-implementation defects (Classification A), while
`integrity_ref` requires a prior, narrowly-scoped contract/schema
clarification (Classification C) before any verifier repair can safely
enforce digest binding for that reference. This phase is authorized as a
**Contract Clarification and Freeze** phase only. Per the No-Go Boundary
(§12 below), no verification implementation, publication construction,
Publication Coordinator, schema runtime change, fixture migration, or
Phase 146L work was performed or is authorized by this phase.

**Predecessor:** 146J — CHGR Verification Cross-Artifact Digest-Binding
Root-Cause Resolution.

**Forbidden files this phase (observed, verified in the diff below):**
`src/pcae/governance/**`, `src/pcae/interactive_workflow/**`, every file
under `src/pcae/schema_resources/chgr/**`, and every test file. Only
`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`, this
report, and governance-bookkeeping files (`.pcae/phase-completion-*`,
`PROJECT_STATUS.md`, `tasks/**`) were touched.

## 3. Bootstrap

```
git status --short                       -> (clean)
git branch --show-current                -> main
git rev-list --count origin/main..HEAD   -> 0
git rev-list --count HEAD..origin/main   -> 0
pcae session bootstrap --agent-id claude-local  -> "Agent lock already held by claude-code"
pcae check                               -> PCAE check passed
pcae health                              -> healthy; agent lock: held by claude-code; git status clean
pcae doctor task-memory                  -> Task memory: clean, no inconsistencies
pcae runtime inspect                     -> Observed / observe / unavailable (unchanged)
pcae push check                          -> nothing_to_push, health/check passed
```

The governing prompt's bootstrap sequence names `--agent-id claude-local`
and `pcae push --check`; the currently active session's actual lock
(`.pcae/agent-lock.json`) is held by `claude-code` (the correct,
already-active session agent for this repository state), and the current
CLI's read-only push-readiness subcommand is `pcae push check` (no `--`),
not `pcae push --check`. Both substitutions are mechanical CLI-surface
corrections, not scope changes; `pcae session bootstrap --agent-id
claude-code` (the effective agent identity) confirmed: active task
`20260729-2257-idle-awaiting-next-governed-phase-post-146j`, latest
completed phase 146J, recommended next phase 146K (this phase), readiness
`blocked` only because the idle-placeholder task is stale relative to
146J — expected and resolved by this phase's own governance-completion
step. Repository confirmed clean, on `main`, local/remote synchronized (0
ahead, 0 behind), no other active governed phase, runtime unchanged.
`PROJECT_STATUS.md` and `tasks/TODO.md` did not conflict; no
authoritative-source tie-break was needed.

## 4. Independence Requirement

This phase did not copy Phase 146J's recommendation text. §30.2–§30.3 of
the amended contract (reproduced in §4/§5 below) independently re-derive
the digest cycle by direct substitution of `references.schema.json`,
`digest.schema.json`, `human_governance_record.schema.json`,
`governance_record_integrity.schema.json`, CHGR-REQ-197/CHGR-REQ-203, and
direct reads of `src/pcae/governance/publication/record.py` (construction)
and `src/pcae/governance/verification.py` lines 232–462 (verification),
independently of Phase 146J's own report prose. One fact was independently
discovered during this re-derivation that Phase 146J's report did not
state explicitly: the currently deployed verifier (`verification.py` line
452, `integrity.get("payload_digest") != declared_digest`) already
performs the reciprocal check the selected model formalizes — it never
compares `integrity_ref.record_digest` against the sibling's own
`record_digest` at all, for any of the three reference types (this is
also the mechanism underlying Phase 146J's own Finding C for
`confirmation_evidence_ref`/`provenance_ref`, but for `integrity_ref` this
omission happens to already be the mathematically necessary treatment,
not an outstanding defect).

## 5. Independent Cycle Reproduction

Full derivation: contract §30.2 (`docs/contracts/CANONICAL_HUMAN_GOVERNANCE_RECORD_CONTRACT.md`).
Summary:

1. `artifact_reference` requires `record_id`+`record_digest`+`record_family`
   on every reference, including `integrity_ref`.
2. CHGR-REQ-197: `governance_record_integrity.record_digest` is computed
   over its own canonical payload, which includes `payload_digest`.
3. CHGR-REQ-203: `payload_digest` = the referencing
   `human_governance_record`'s own final `record_digest`.
4. `human_governance_record.record_digest` is computed over its own
   canonical payload, which includes `integrity_ref.record_digest`
   (required, not excluded from the hash).
5. Substituting steps 1–4: `human_governance_record.record_digest` is a
   function of `governance_record_integrity.record_digest`, which is a
   function of `payload_digest`, which equals
   `human_governance_record.record_digest` — the value being computed. A
   genuine, non-degenerate SHA-256 fixed-point equation, independently
   reproduced by direct text substitution, not assumed from 146J.
6. `record.py` resolves this via a **provisional** digest (real content,
   placeholder `payload_digest`) seeding `integrity_ref`, so
   `integrity_ref.record_digest` never equals the final
   `governance_record_integrity.record_digest`, for any bundle, genuine
   or forged, by construction — confirmed by direct code read, not
   assumed.
7. `verification.py` (lines 438–462) independently confirmed to never
   check `integrity_ref.record_digest` against the resolved sibling's
   `record_digest` — instead checking `integrity.payload_digest !=
   declared_digest` (the primary record's own self-consistency-checked
   digest). This is Model C's reciprocal check, already present,
   un-frozen as contractual authority until this phase.

## 6. Foundational Contract Reconstruction

Full text: contract §30.3. CHGR-REQ-081/CHGR-REQ-082 require a reference
to *cite* an identifier and (where deterministic referencing is required)
a digest; neither specifies that every cited digest must be checked for
exact equality against the referenced artifact's own final digest — that
enforcement rule belongs to verification-layer design, a space
CHGR-REQ-081/082 leave open. `references.schema.json`'s own documented
discipline independently confirms this: "resolving and cross-checking a
reference is a governance/verification.py responsibility," and
`digest.schema.json`'s `referenced_record_digest` is explicitly
"shape-checked only." This phase's clarification therefore operates
entirely within space CHGR-REQ-081/082 already leave open and narrows
neither requirement's text.

## 7. Candidate Binding Models

Full evaluation: contract §30.4. Summary verdicts:

| Model | Description | Verdict |
|---|---|---|
| A | Final integrity artifact digest in `integrity_ref` | **Rejected** — genuine SHA-256 fixed-point equation; not constructible without weakening CHGR-REQ-197/CHGR-REQ-025/CHGR-REQ-109 |
| B | Identity-only integrity reference (nullable/omitted digest) | **Rejected** — resolves the cycle but requires a larger schema migration (new `$def`, or a global weakening of `artifact_reference`) than Model C for an equivalent outcome |
| C | Directed one-way integrity binding (identity + reciprocal `payload_digest`) | **Selected** — zero schema changes; formalizes existing construction/verification behavior |
| D | Reference digest with defined projection (excludes `payload_digest`) | **Rejected** — creates a second, hidden digest meaning under the same field name and same `$ref`; ambiguous, audit risk |
| E | External bundle/envelope digest (new artifact/field) | **Rejected** — broader redesign than the narrowly-scoped defect requires; not the smallest viable model |
| F | Another independently derived model | None found beyond A–E |

## 8. Selected Model and Rationale

**Model C**, evaluated against all twelve selection criteria: full text
contract §30.5. All twelve criteria satisfied; criterion 11 (minimize
schema migration) is satisfied maximally — zero schema files change.
Model C is not selected for convenience: §30.4 independently demonstrates
Models A and D are contractually/mathematically inferior on their own
terms, and Model E is disproportionate to the defect's actual scope
(one field's verification semantics, not a new artifact family).

## 9. Rejected Models

Models A, B, D, E — full rejection rationale in §7 above and contract
§30.4. No model was rejected solely to preserve backward compatibility;
Model A's rejection in particular is a mathematical impossibility finding
independent of any compatibility concern, and Model E's rejection is
explicitly *not* "rejected because it's inconvenient" but "rejected
because it exceeds the smallest viable clarification," per this phase's
own authorizing instruction (§5 Model E: "Do not select it merely because
it is theoretically clean").

## 10. Construction-Order Contract

Full text: contract §30.7, CHGR-REQ-214. Nine-step sequence: identity
allocation; confirmation evidence finalized; provenance finalized;
preliminary `human_governance_record` assembly (with a real,
non-placeholder, but non-authoritative `integrity_ref.record_digest`);
`human_governance_record`'s own final digest computed; integrity artifact
finalized with the true `payload_digest`; no further mutation of
`human_governance_record` (explicit no-op step, so a future
implementation does not attempt to retroactively "correct"
`integrity_ref` after the integrity artifact is finalized); fail-closed
schema-envelope validation of the full bundle; persistence eligibility.
This restates and freezes `record.py`'s own existing, already-correct
construction order — no construction change is required or authorized.

## 11. Verification Contract

Full text: contract §30.8. Fail-closed behavior defined for: no matching
sibling (skipped, disclosed, never silently passed); multiple matching
siblings (reject, CHGR-REQ-213); wrong `record_digest` for
confirmation/provenance (reject, CHGR-REQ-212); wrong `record_digest` for
integrity (**not** a rejection ground — CHGR-REQ-210's narrow exception);
wrong `record_family` (reject, schema-level `const` narrowing, unchanged);
wrong reciprocal `payload_digest` (reject, CHGR-REQ-211); cross-bundle
substitution (reject, via CHGR-REQ-211/212 depending on reference type);
reordered arguments (same result, once CHGR-REQ-213 is implemented);
legacy provisional-reference bundles (valid, no migration, CHGR-REQ-215);
malformed reference (reject, schema-shape validation, unchanged).

## 12. Duplicate-Match Rule

CHGR-REQ-213 (contract §30.7): first-match selection is explicitly
forbidden as the sole resolution rule for **all three** reference types
(`confirmation_evidence_ref`, `provenance_ref`, `integrity_ref`) —
uniform, not integrity-specific. Verification SHALL reject when more than
one caller-supplied candidate matches a reference's `record_id` and
`record_family`. This closes Phase 146I/146J's Finding A
(`_find_related`'s order-dependent first-match behavior) at the contract
level; implementing it in `_find_related` itself is 146L's authorized
scope, not this phase's.

## 13. Security Analysis

Full text: contract §30.9. Demonstrated resistance to: sibling
substitution under a disclosed `record_id` (the attacker cannot choose
the target record's real digest, only read it — CHGR-REQ-211); duplicate
sibling injection (CHGR-REQ-213, unconditional on which candidate is
genuine); cross-bundle mixing (CHGR-REQ-211's `payload_digest` reflects
only its own bundle); locally recomputed self-digest tampering (existing
self-consistency check, unchanged); argument-order manipulation
(CHGR-REQ-213); integrity artifact substitution (same reciprocal-binding
proof as sibling substitution); primary-record tampering (caught upstream
by the primary record's own digest self-consistency gate, which
CHGR-REQ-211 transitively depends on); partial bundle presentation
(every omitted check explicitly disclosed as skipped, never silently
passed). No claim in this analysis depends on any identifier's secrecy —
every proof depends only on SHA-256 second-preimage infeasibility.

## 14. Schema Impact

Full text: contract §30.10. **Contract-only clarification.** No schema
file, manifest entry, construction fixture, or verification fixture is
changed by this phase. `references.schema.json`, `human_governance_record.schema.json`'s
`integrity_ref` property, `governance_record_integrity.schema.json`,
`digest.schema.json`, and `manifest.json` all remain byte-identical to
their Phase 146D state — independently confirmed via `git diff` (§14 of
the Validation results below shows zero changes under
`src/pcae/schema_resources/chgr/**`). Model C's selection criterion 11
made this outcome the deciding factor over Models B and D, both of which
would have required a schema change of some kind.

## 15. Migration and Compatibility

CHGR-REQ-215 (contract §30.7): every already-produced Chapter 146 bundle
is classified **valid under this clarification, without migration,
regeneration, or any file change**, provided
`governance_record_integrity.payload_digest` exactly equals the bundle's
`human_governance_record.record_digest` — which every genuine bundle
`record.py`'s existing construction path already satisfies (verified by
direct code read of `record.py` lines 269–277: `body4["payload_digest"] =
body3["record_digest"]`, always the true final value). This clarification
changes only which already-present field a future verifier treats as
authoritative for which purpose; it does not change any byte of any
already-produced artifact.

## 16. Requirement Amendment

CHGR-001 revised to **v1.3** via new contract §30 (predecessor: v1.2,
Phase 146D). New requirements CHGR-REQ-210 through CHGR-REQ-216 (full
text: contract §30.7), covering: `integrity_ref` semantics and its narrow
non-enforcement exception (CHGR-REQ-210); the reciprocal `payload_digest`
binding as authoritative (CHGR-REQ-211); exact-match enforcement for
`confirmation_evidence_ref`/`provenance_ref` (CHGR-REQ-212); the uniform
duplicate-match fail-closed rule (CHGR-REQ-213); the binding construction
order (CHGR-REQ-214); historical-bundle compatibility (CHGR-REQ-215); and
an explicit no-narrowing clause (CHGR-REQ-216). No existing requirement
(CHGR-REQ-001–209) is renumbered, reworded, or superseded. §30.12
explicitly classifies this section as a **clarification and freeze**
(not a supersession), distinguishing it from a compatibility rule in the
narrow §22 sense.

## 17. Verification Matrix

Full table: contract §30.11 (reproduced here):

| Scenario | Required result |
|---|---|
| Exact confirmation sibling supplied | pass |
| Confirmation `record_id` match, `record_digest` mismatch | reject |
| Duplicate confirmation matches | reject |
| Exact provenance sibling supplied | pass |
| Provenance `record_id` match, `record_digest` mismatch | reject |
| Duplicate provenance matches | reject |
| Exact integrity sibling supplied (genuine `payload_digest`) | pass |
| Integrity `record_id` match, `integrity_ref.record_digest` mismatch (always true for a genuine bundle) | pass (not a rejection ground) |
| Integrity `record_id` match, wrong reciprocal `payload_digest` | reject |
| Duplicate integrity matches | reject |
| Cross-bundle integrity sibling | reject |
| Reordered `--related` arguments | same result |
| Legacy provisional-reference bundle, genuine `payload_digest` | pass, no migration |
| Missing sibling | explicitly skipped and disclosed |
| Malformed reference | reject |

## 18. Findings

No Blocking findings. One Observation, disclosed and resolved within this
phase's own text rather than left open: the currently deployed verifier
(`verification.py` line 452) already implements Model C's reciprocal
check for `integrity_ref`, but did so without contractual authority or
duplicate-match protection until this phase; CHGR-REQ-211 now supplies
that authority, and CHGR-REQ-213 (deferred to 146L for implementation)
will close the remaining duplicate-match gap uniformly across all three
reference types.

## 19. No-Go Confirmation

Confirmed: this phase did not modify verification implementation,
publication construction, the Publication Coordinator, `_find_related`,
production artifacts, fixtures, schema runtime, lifecycle sequencing
beyond contract clarification, authority ownership, execution capability,
policy, or strategic lineage, and did not begin Phase 146L. Only contract
clarification (§30), this report, and governance bookkeeping were
performed, per the phase's own No-Go Boundary.

## Overall Verdict

**CONTRACT CLARIFICATION FROZEN.**

Selected integrity-reference model: **Model C — directed one-way integrity
binding** (identity-only reference plus reciprocal `payload_digest`
binding). Schemas require **no** amendment — this is a contract-only
clarification (§14 above, contract §30.10). Historical provisional-
reference bundles (every Chapter 146 bundle produced to date) are treated
as **valid under the clarified semantics, without migration or
regeneration** (CHGR-REQ-215). The implementation repair boundary
authorized for a future phase (146L) is: verifier-only changes to
`governance/verification.py`'s `_find_related` and its three call sites,
implementing CHGR-REQ-212 (exact-digest enforcement for
confirmation/provenance), CHGR-REQ-213 (uniform duplicate-match
rejection), and citing CHGR-REQ-211 (integrity reciprocal binding,
already implemented, now contractually authoritative) — no construction
change, no schema change, no fixture migration.

## Validation

```
pcae check              -> PCAE check passed
pcae health             -> healthy; required files present; policy valid
pcae doctor task-memory -> clean, no inconsistencies (after tasks/DONE.md
                            back-fill for the post-146J idle task entry)
pcae runtime inspect    -> Observed / observe / unavailable (unchanged)
pcae push check         -> nothing_to_push, Health: healthy, Check: passed
git diff --stat -- src/pcae/schema_resources/chgr/                        -> (empty; zero schema files touched)
git diff --stat -- src/pcae/governance/ src/pcae/interactive_workflow/    -> (empty; zero implementation files touched)
python -m pytest -m fast_green -n auto -q      -> 4391 passed, 105 warnings, 102.25s
python -m pytest -k "chgr or governance_record or schema_registry or manifest" -q
  -> 462 passed, 2 failed (tests/test_chgr_packaging.py -- wheel-build
     subprocess failures), 26334 deselected
```

The two `test_chgr_packaging.py` failures were independently re-run
against a clean `git stash push -u` baseline (this phase's own diff
stashed out) and reproduced identically (`2 failed, 1 passed`) --
confirmed pre-existing and unrelated to this phase's contract-text-only
change, consistent with Phase 146J's own prior disclosure of 10
pre-existing-unrelated packaging-build failures in its broad sweep.
`fast_green` 4391/4391 matches Phase 146J's own baseline exactly, as
expected for a documentation-only diff touching no schema, manifest,
registry, or Python source file.

## Recommended Next Phase

**146L — CHGR Cross-Artifact Digest-Binding and Duplicate-Match
Verification Repair.** Per contract §31: expected to require
**verifier-only changes** (`governance/verification.py`); **no
construction change** (`record.py`'s existing construction order already
satisfies CHGR-REQ-214); **no schema change** (§30.10); and **no fixture
migration** (§30.13, CHGR-REQ-215 — historical bundles verify correctly
under the clarified semantics without modification). This is a
recommendation, not an authorization.

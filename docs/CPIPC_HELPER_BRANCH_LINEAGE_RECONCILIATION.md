# CPIPC Helper-Branch Lineage Reconciliation

**Phase:** N16-5-F-5-TB-CPIPC-IDENTITY-RECONCILE
**Type:** Governance / evidence-only reconciliation. No production, contract, schema, or dependency change.
**Predecessor:** N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR (COMPLETE, final commit `140d3199`)

## 1. Disputed forms

The authorization prompt for this phase claimed a lineage discrepancy between:

- `...30R.5R.2B.1R...` ("with B")
- `...30R.5R.2.1R...` ("without B")

and asked whether the replay-repair phase was canonically the first form while later
descendants dropped the `B`, or some other resolution (dispositions A-D).

## 2. Disposition: **A — NO LINEAGE DEFECT**

**The discrepancy does not exist in repository canonical evidence, and cannot exist as
described**, because the two quoted substrings are not two competing textual forms of
the *same* segment of the phase ID. They are two different segments at two different
positions within one single, unchanging ID string.

Splitting the full canonical phase ID on `.` (0-indexed):

```
0:149O 1:20L 2:7O 3:3W 4:1R 5:2B 6:1R 7:1 8:1R 9:30R 10:5R 11:2 12:1R 13:1R 14:2R ...
```

- Segment **5** is `2B` — part of the fixed prefix `...3W.1R.2B.1R.1.1R...` shared by
  the entire N16-5-F-5-TB branch since long before the replay-repair phase.
- Segment **11** is `2` (no letter suffix), immediately following `...30R.5R...`.

The `2B` the authorization prompt places at position 11 (`...30R.5R.2B.1R...`) has
**never appeared in any commit, task file, metadata file, PROJECT_STATUS.md revision,
canonical phase report, or quarantine record in this repository**, verified two ways:

```
git log --all -p -- '*.json' '*.md' | grep -c '30R\.5R\.2B\.1R'   →  0
```

and independently by a full artifact-by-artifact reconstruction (§5 below) of the
replay-repair phase, which shows unanimous agreement on the real form across every
canonical artifact.

**Origin of the false premise (outside repo-evidence scope, noted for completeness):**
the real ID contains the literal substring `...1R.2B.1R.1.1R.30R.5R...`, in which a `2B`
segment (position 5) sits ~6 segments before a bare `2` segment (position 11). A prose
transcription of this ID that visually conflated the two nearby segments would produce
exactly the false discrepancy described in the authorization prompt. This is a
transcription/memory artifact, not a canonical-state defect — consistent with
Disposition A per §21 of the authorization ("identify where the incorrect
representation originated" so far as repo evidence permits; the true origin is upstream
of this repository's own records).

## 3. CPIPC grammar (`src/pcae/core/phase_id.py`, sole authority per CPIPC-001 v1.0,
frozen at Phase 137R/137T, 2026-07-20 — unchanged since, confirmed via
`git log --follow -- src/pcae/core/phase_id.py` → exactly 2 commits, both predating the
disputed chain by ~7 weeks, so no rule-version drift applies anywhere in this chain)

- `phase-id = series, branch, {".", subphase-segment}`
- `subphase-segment = numeric-segment | letter-segment`
- `numeric-segment = digits, [letters]` (e.g. `"2B"` parses to `(number=2, letters="B")`)
- `letter-segment = letters` (e.g. bare `"R"` parses to `(number=None, letters="R")`)
- `normalize()`/`format()` reassemble each segment as `letters if number is None else
  f"{number}{letters}"`. **No normalization path ever drops a trailing letter from a
  numeric segment** — letters are uppercased only, never removed.
- `equals()` compares `(series, branch, subphase_tuple)` structurally — no fuzzy or
  lenient matching.
- **There is no child/successor/derivation function anywhere in this module.**
  `__all__` exposes `parse, is_valid, normalize, format, validate, scan_tokens,
  find_first_token, match_leading_token, equals, compare, same_series, same_branch` —
  nothing computes "the direct child of parent X." `compare()` gives a total order
  within a comparable family but is not a derivation rule.

Live parser test (executed directly, not simulated):

```python
a = parse(".....2B.1R.....")   # segment with (2, "B")
b = parse(".....2.1R.....")    # segment with (2, "")
equals(a, b)   → False
compare(a, b)  → "greater"     # structurally distinct; no rule normalizes 2B == 2
```

Even under the counterfactual that both forms had been recorded somewhere, the parser
would treat them as distinct, non-equivalent IDs. This confirms Disposition A does not
depend on any lenient-matching escape hatch — the forms are genuinely different, and
only one of them (the bare `2` at position 11) was ever actually used.

## 4. Replay-repair identity (alias N16-5-F-5-TB-REPLAY-REPAIR, completion commit
`29a2ec35859c176e5b0dcfd1fe447a1de757f31f`, 2026-09-11)

| Source | Value at that commit |
|---|---|
| Commit message | `Phase 149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.1R.1R.2R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1R.1.1.1.1.1.1.1.1.1.1.1.1 (N16-5-F-5-TB-REPLAY-REPAIR): durable cross-process replay-state repair` |
| `git show 29a2ec35:.pcae/phase-completion-metadata.json` → `phase_id` | identical string, `...2B.1R.1.1R.30R.5R.2.1R...` |
| `git show 29a2ec35:PROJECT_STATUS.md` → "## Current Phase" | same ID text |
| Canonical phase reports (`.pcae/phase-reports/20260911-184128-*`, `20260911-202614-*`, `20260911-202648-*`) | same ID text |
| 7 prior quarantined attempts (`.pcae/phase-reports/quarantine/2026091[12]-*.blocked.{md,json}`) | same ID text in every quarantined attempt too |

**Unanimous agreement across every canonical artifact on `...2B.1R.1.1R.30R.5R.2.1R...`.**
No artifact ever recorded `...30R.5R.2B.1R...`.

## 5. Full commit-to-phase mapping

All 20 commits inspected (`29a2ec35, a5c8202b, 64c747dd, 102c91e3, 75f605c4, 6900c1a4,
f922c8b1, 73f99c74, 48964ad6, 50a53396, eddcdd1a, a6866b71, a9b75905, c1b2d050,
11336966, 43813b16, 257ac06a, ea902f1e, 3d40d894, 140d3199`, 2026-09-11 through
2026-09-14) carry the identical phase-ID prefix `149O.20L.7O.3W.1R.2B.1R.1.1R.30R.5R.2.
1R.1R.2R.1R.1R.1R.1.1R...` at segments 0-14, differing only in trailing appended
segments (the normal CPIPC deep-subphase-append pattern; each descendant phase adds one
more terminal segment onto the full prior ID rather than diverging). Aliases:
64c747dd/102c91e3 = N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN; 75f605c4/6900c1a4 =
N16-5-F-5-TB-CALLER-INTEGRATION-ARCH; f922c8b1 = real helper store/launcher
implementation; a9b75905/c1b2d050/11336966 = fresh Linux helper IV; 43813b16/257ac06a/
ea902f1e/3d40d894/140d3199 = the current boundary-repair phase.

**Not independently locatable as distinct commit hashes** within this phase's bounded
scope: standalone commits specifically for "blocked certification-read implementation,"
"caller-map correction," or "admin mutation packaging decision" — these may be
sub-events folded into f922c8b1/73f99c74/48964ad6 rather than separately-committed
work. This is disclosed as a scope limitation, not a lineage finding; it does not
affect the disposition since all sampled commits agree on the shared, unbroken prefix.

## 6. Helper-IV-R identity (commit `a5c8202b`, 2026-09-12, alias
N16-5-F-5-TB-HELPER-IV-R)

Commit subject carries the identical, correct prefix as its own declared ID. **No
structured "predecessor" field exists anywhere in the metadata/report schema** — see
§8 (phase-creation path). The predecessor relationship is established only by
convention (commit-message text + PROJECT_STATUS.md's prior "Current Phase" text at
authoring time), never a validated, separately-stored field.

## 7. Descendant chain (lineage-by-extension)

All 20 commits above share byte-identical segments 0-14. Each descendant phase's
identity is formed by **appending** trailing segments to the full prior ID — visible
directly in the monotonically growing `.1R`/`.1` tail across the 2026-09-11 →
2026-09-14 commit sequence. This is CPIPC-consistent lineage-by-extension, not two
divergent branches, and is fully accounted for without any need to invoke a "B dropped"
hypothesis.

## 8. Transition-validator scope
(`src/pcae/core/repository_transition_integration.py` →
`src/pcae/core/repository_transition_validator.py::validate_transition`)

Runs exactly 7 checks (confirmed directly by reading the source, function names at
`repository_transition_validator.py` lines 192-473):
`_check_phase_identity_consistency`, `_check_metadata_consistency`,
`_check_report_completeness`, `_check_recommended_next_phase_presence`,
`_check_canonical_promotion_eligibility`, `_check_notification_eligibility`,
`_check_no_execution_availability_unless_contracted`.

`RepositoryState` — the validator's entire input model — has **no
`predecessor_phase_id`/`parent_phase_id` field at all**; only `phase_id`,
`active_task_phase_id`, `metadata_phase_id`, `lifecycle_current_phase_id`, all checked
for mutual agreement on the *same current* ID.

Per the taxonomy in the authorization prompt (§10, options A-G): this validator
implements **(A) intra-phase identity consistency only**. It does **not** check
(C) predecessor-link existence, (D) valid-direct-child-of-exact-predecessor,
(E) full ancestor-chain validity, or (G) branch/collision uniqueness.

**This is a real, confirmed validator scope gap** (expected per §36 of the
authorization as a "validator weakness finding" requiring only a FOLLOW-UP/DEFERRED
disposition here, not repair). It does not, however, mean the validator's historical
PASS results were wrong about what they claimed — they never claimed to check ancestry.

## 9. Phase-creation path
(`resolve_canonical_phase_identity`, `src/pcae/core/phase_reports.py:2084`)

Fixed resolution precedence: (1) active task's title text (a literal `"Phase X: ..."`
string typed by whoever creates the task) → (2) `phase-completion-metadata.json`'s own
`phase_id` field (also hand/agent-set) → (3) PROJECT_STATUS.md's "Current Phase" line
if not yet completed → (4) explicit `--phase-id` CLI flag (last resort only).

**At every level the ID text is authored, not algorithmically derived.** There is no
"compute child of parent X" step anywhere in the codebase. A malformed-but-
grammar-valid descendant *could* be created by typo, since only `phase_id.parse()`'s
grammar validity is enforced at creation time — never ancestry. This is consistent with
§8's validator finding: nothing in the phase-creation-through-completion path checks
ancestry, only grammar validity and intra-phase self-consistency.

## 10. Artifact consistency matrix

| Phase | task | metadata | PROJECT_STATUS | report | commit msg |
|---|---|---|---|---|---|
| N16-5-F-5-TB-REPLAY-REPAIR | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT |
| N16-5-F-5-TB-HELPER-IV-R | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT |
| N16-5-F-5-TB-REPLAY-STORE-FIFO-HARDEN | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT |
| N16-5-F-5-TB-CALLER-INTEGRATION-ARCH | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT |
| N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT | CONSISTENT |

Zero instances of ABSENT or INCONSISTENT found across any sampled artifact type for
any phase in this chain.

## 11. Direct-child recomputation

No algorithmic direct-child derivation function exists in this codebase (§3, §9), so
"recompute expected_child = derive_direct_child(actual_parent)" is **not
reconstructable as a formal operation** — there is nothing to recompute against. What
*is* verifiable, and was verified, is that every transition in the chain:

1. extends the full prior ID by appending trailing segments (never mutates an
   interior segment, and in particular never touches segment 5 `2B` or segment 11 `2`),
2. parses as valid CPIPC grammar,
3. is unanimously agreed upon across all canonical artifacts at authoring time.

Classification for every transition replay-repair → helper-IV-R →
FIFO-harden → caller-integration-arch → boundary-repair: **VALID** (by
extension-consistency + unanimous artifact agreement; formal ancestry-rule validity is
not independently checkable because no such rule is implemented — see §8).

## 12. Validator table

| Mechanism | Checks ID syntax? | Checks intra-phase equality? | Checks direct-child relation? | Checks full ancestry? | Checks collision? | Fail-closed? |
|---|---|---|---|---|---|---|
| `phase_id.parse`/`is_valid` (used at task/phase creation) | Yes | N/A | No | No | No | Yes (rejects malformed grammar) |
| `repository_transition_validator.validate_transition` | Indirect (via parse) | Yes | No | No | No | Yes |
| `pcae check` / status coherence | Indirect | Yes | No | No | No | Yes |
| `pcae phase complete` report/metadata coherence gates | Indirect | Yes | No | No | No | Yes |
| `pcae push` readiness | Indirect | Yes (via report-identity gate) | No | No | No | Yes |

No mechanism in the current implementation checks direct-child derivation, full
ancestor-chain validity, or branch collision. This matches §36's expected disposition:
**FOLLOW-UP GOVERNANCE HARDENING (deferred)** — not repaired in this phase.

## 13. Final disposition

**DISPOSITION A: NO LINEAGE DEFECT.**

The claimed discrepancy was a reporting/transcription artifact external to this
repository (most likely a visual conflation of segment 5 `2B` with segment 11 `2` in
the same real ID string, both near the substring `...1R.2B.1R.1.1R.30R.5R...`). The
canonical helper-branch ancestry chain (replay-repair → helper-IV-R →
FIFO-harden → caller-integration-arch → real-helper-store/launcher →
Linux-helper-IV → boundary-repair) is internally consistent across every canonical
artifact at every transition, unanimously, with zero exceptions found. No historical
canonical phase ID requires correction. No non-destructive correction mechanism is
needed because no defect was found.

**Separately disclosed governance finding (not a lineage defect, deferred per §36):**
the repository's transition validator and phase-creation path check intra-phase
identity self-consistency only — never predecessor-link existence, direct-child
derivation, full ancestor-chain validity, or branch collision. This is a real scope
gap worth a future FOLLOW-UP GOVERNANCE HARDENING phase, but it is orthogonal to (and
did not cause) the false discrepancy resolved here, since the discrepancy never
existed in canonical state in the first place.

## 14. Unchanged / preserved

- Historical canonical phase IDs: **UNCHANGED**.
- Git history: **UNCHANGED** (no rebase, amend, force-push, tag rewrite).
- Production source (`src/pcae/**`): **NONE changed**.
- Contracts/schemas/dependencies: **NONE changed**.
- Finding C (in-place same-inode content mutation, undefended): **OPEN**, deferred to
  the fresh helper-boundary repair IV, not touched here.
- Predecessor test-file template change: deferred to the fresh IV, not adjudicated
  here.
- Runtime state: Observed / observe / unavailable — unchanged.
- **N-16-5: NOT CLOSED.** N-16-6/N-16-7: untouched.
- Historical governance wording preserved exactly: **DELEGATED .3 FINALIZATION /
  COMMIT / PUSH: UNAUTHORIZED**.

## 15. Recommended successor

**N16-5-F-5-TB-REAL-HELPER-BOUNDARY-REPAIR-IV** (fresh independent Linux verification
of the boundary repair, covering same-file-object execution, descriptor
inheritance/isolation, path substitution, peer credentials, transitive
import/environment attacks, REAL entrypoint canonical-store selection,
certification_read/ceremony_entry real-store, blocked writes, replay,
no-authority-export, no-generic-broker — plus adjudicating Finding C and the
predecessor test-file template change).

**NOT BEGUN.** Requires fresh explicit human authorization, per phase-authorization
§68 of the predecessor governance record.

## 16. Delegated-worker disclosure

Evidence for §3-§12 above was gathered by a bounded, read-only delegated worker
(git/source inspection only — no repository writes, no commits, no state-mutating
`pcae` commands). The primary operator independently re-verified the headline claim
(zero occurrences of the disputed form across full git history; exact metadata/commit
content at the replay-repair completion commit; the transition-validator's 7 check
functions and `RepositoryState` field set by reading the source directly) before
accepting it into this canonical artifact. The delegated worker did not finalize,
commit, push, or begin any successor phase.

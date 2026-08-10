# Phase 149O.19.5E.1 — HMIC v1.1 Validator/Admin Implementation Identity Contract Evolution

**Status:** CONTRACT-LEVEL REPAIR COMPLETE — INDEPENDENT VERIFICATION + PRODUCTION ALIGNMENT PENDING

## 1. Baseline

- Latest completed phase entering this one: **149O.19.5E** (HMIC
  Protected Admin Certification / Revocation Surface, Wave E), commits
  `7fb5efdd`, `0e31b814`, `499efb90`, pushed, `origin/main..HEAD` = 0 at
  entry. Repo clean at entry (`git status --short` empty).
- Waves A–E (149O.19.5A–5E) implemented, entirely inside
  `src/pcae/core/hatp_mandatory_certification.py` (Waves A–D) and
  `scripts/hatp_certification_admin.py` (Wave E): certification/binding
  parsing and canonical serialization; implementation/contract/
  certification-ID identity derivation; protected certification-state
  storage (locking, atomic writes, tri-state readers, internal
  create-once/binding/revocation writers); the 12-step active-
  certification Validation Status engine (zero production callers); and
  the Protected Admin `certify`/`activate`/`revoke` ceremony script
  (standalone, outside `src/pcae/`, no agent-reachable caller).
- `pcae session bootstrap`, `pcae health`, `pcae check`, `pcae status
  coherence`, `pcae doctor task-memory`, `pcae push check`, `pcae
  runtime inspect`, `pcae notify status`, `pcae phase-report show
  --latest`, and `pcae phase-report reconcile --phase-id 149O.19.5E`
  were all run at phase entry. Results: repo clean; `origin/main..HEAD`
  = 0; health healthy; check passed; status coherence coherent; task
  memory warnings (pre-existing `tasks/DONE.md` listing gaps predating
  this phase, unrelated, not remediated here — outside this phase's
  allowed-file scope); push check clean (`nothing_to_push`); runtime
  inspect Observed / observe / unavailable; notify status Telegram
  configured/enabled/ready; the canonical 149O.19.5E phase report shows
  status completed, report completeness complete, and reconcile
  returned `reconciled` / `mutation: none (inspection only)`.
- HMIC-001 v1.0 (as of phase entry): VERIFIED WITH NON-BLOCKING FINDINGS
  — CONFORMS (144 requirements, 12 CIVC invariants, 32 attack scenarios,
  22-file frozen implementation subject). B-149O.19.3-1: INDEPENDENTLY
  CONFIRMED CLOSED. `mandatory_consumption_implementation_
  independently_verified` in `hatp_mandatory_cutover.py`: hard-coded
  `False`, unchanged since 149O.19.2. Zero production callers of the
  Wave-D validator or Wave-E admin script exist anywhere in
  `src/pcae/**`.

## 2. Stop Condition W-1 (Entering This Phase)

Phase 149O.19.4's implementation plan (§10.3, §13) established Stop
Condition **W-1**: Wave F (replacing the hard-coded `False` ceiling with
a real readiness check) SHALL NOT begin until a HMIC-001 v1.1 contract
amendment binds the implemented HMIC validator/admin source into the
frozen file set, and that amendment is independently verified. Every
wave doc (5A–5E) restated W-1 as "not crossed." Phase 149O.19.5E's own
§13 "W-1 Source Inventory" closed that inventory at exactly two files —
`src/pcae/core/hatp_mandatory_certification.py` (already named at Wave D
exit) and `scripts/hatp_certification_admin.py` (named by 5E itself) —
and named this phase, 149O.19.5E.1, as the mandatory next step per its
own §21 "Mandatory Next Phase." This phase performs step 1 of the
5-step sequence the governing instruction freezes explicitly:

1. **HMIC contract evolves to bind the implemented HMIC authority code
   (this phase).**
2. That contract evolution is independently verified (149O.19.5E.2 or
   repository-conventional equivalent — not this phase).
3. Production identity derivation is aligned to the evolved contract's
   frozen file set (a bounded future implementation-alignment phase,
   e.g. 149O.19.5E.3).
4. That production alignment is independently verified.
5. Only after step 4 may Wave F be considered.

This phase type is **CONTRACT EVOLUTION / CONTRACT REPAIR ONLY**. It
touches exactly one file under version control that is not this
document or its accompanying test module:
`docs/contracts/HATP_MANDATORY_INDEPENDENT_VERIFICATION_CERTIFICATION_
CONTRACT.md`. No `src/pcae/**` or `scripts/**` file was read for the
purpose of modifying it, and none was modified.

## 3. Independent Reconstruction of the v1.0 22-File Set

Mechanically re-extracted directly from HMIC-REQ-050's pre-amendment
text (18 `src/pcae/`-relative entries + 4 `docs/contracts/...`
repository-root-relative entries = 22) and cross-checked against
`_FROZEN_SRC_PCAE_RELATIVE_FILES`/`_FROZEN_REPOSITORY_ROOT_RELATIVE_
FILES` (and the module-level `assert len(_FROZEN_AUTHORITY_BEARING_
FILES) == 22`) in `src/pcae/core/hatp_mandatory_certification.py`, and
against `docs/PHASE_149O_19_5B_...md`'s own restatement. All three
sources agree byte-for-byte on the following baseline list:

```
core/hatp_mandatory_cutover.py
core/hatp_ag_authority.py
core/hatp_rollback_consumption.py
core/hatp_bootstrap.py
core/human_approval_trusted_provenance.py
core/repository_identity.py
core/rollback_approval_evidence.py
core/hatp_evidence_store.py
core/hatp_signed_evidence.py
core/agent.py
commands/agent.py
cli.py
core/permission_broker.py
core/permission_broker_foundation.py
core/hatp_providers.py
core/hatp_fido2_provider.py
core/hatp_piv_provider.py
core/hatp_hardware_credentials.py

docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md      (HMRC-001)
docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md        (HATP-001)
docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md     (HSCE-001)
docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md               (RAE-001)
```

Count 22, uniqueness confirmed (no duplicate entries), every path
exists on disk today. No discrepancy found between contract text and
production constants.

## 4. Independent Reconstruction of the Actual Wave A–E Production Diff

Not trusted from phase-summary prose. Read directly, wave by wave:

| Wave | Phase doc | Production file(s) touched | New / Modify |
|---|---|---|---|
| A | 149O.19.5A | `src/pcae/core/hatp_mandatory_certification.py` | **NEW** |
| B | 149O.19.5B | `src/pcae/core/hatp_mandatory_certification.py` | MODIFY (same file) |
| C | 149O.19.5C | `src/pcae/core/hatp_mandatory_certification.py` | MODIFY (same file) |
| D | 149O.19.5D | `src/pcae/core/hatp_mandatory_certification.py` | MODIFY (same file) |
| E | 149O.19.5E | `scripts/hatp_certification_admin.py` | **NEW**; `hatp_mandatory_certification.py` explicitly not touched (5E §3) |

Confirmed by each wave doc's own "only file touched" check (5A §9, 5B
§10, 5C §11, 5D §10, 5E's "Required Final-Report Field Confirmations")
and by direct reading of both files' current content. **Exactly two**
production files exist outside the original 22-file set:
`src/pcae/core/hatp_mandatory_certification.py` and
`scripts/hatp_certification_admin.py`. No third new/modified production
file exists anywhere in `src/pcae/**` or `scripts/**`. `core/hatp_
mandatory_cutover.py` remains byte-unchanged through every wave.

## 5. Authority-Sensitive Source Inventory

| Source file | What it controls | Can it change VALID/non-VALID, parsing, identity derivation, storage, active binding, or revocation semantics? | Classification |
|---|---|---|---|
| `core/hatp_mandatory_certification.py` | Certification/binding parsing, canonical serialization; certification-ID/implementation-identity/contract-identity derivation; protected storage (locking, atomic writes, tri-state readers); active binding; revocation; the sole `_validate_at_root`/`validate_active_hatp_mandatory_independent_verification_certification` Validation Status engine | **Yes — directly.** E.g. an edit to `_validate_at_root`'s final comparison step could make it unconditionally return `CertificationStatus.VALID` | **AUTHORITY-SENSITIVE — MUST BE BOUND** |
| `scripts/hatp_certification_admin.py` | The sole intended caller of the module's internal (non-`__all__`) writer functions (`_append_certification_record`, `_write_active_binding`, `_write_revocation`); controls what content is certified, which candidate is activated, and whether/when revocation is invoked | **Yes — indirectly, on writer content/timing, not on validator soundness** (see §6). Cannot force the validator to accept a false identity, but can create a self-consistent-yet-misleading record or select which record becomes active | **AUTHORITY-SENSITIVE — BIND INTO V1.1, defense-in-depth** |

## 6. Writer vs. Validator — Explicit Distinction (Not Overclaimed)

A malicious or buggy writer (`scripts/hatp_certification_admin.py`)
**cannot** make the validator (`core/hatp_mandatory_certification.py`)
accept a certification for an implementation identity the validator's
own fresh, independent re-derivation does not match: `derive_
implementation_commit`, `derive_implementation_scope_digest`, `derive_
contract_versions`, and `derive_repository_instance_id` are all called
by the validator itself against live repository state at validation
time, never read from the stored record as authoritative (§31 steps
2-3, 9-10 of the contract). At worst, a compromised writer produces a
record that **fails to validate** — a denial, safe by construction —
exactly the 149O.19.4 plan's §10.4 original analysis.

What a compromised writer *can* do, and why this contract still elects
to bind it: control the *content* and *timing* of what gets certified
in the first place — which repository state a human Protected Admin is
asked to confirm, whether a revocation is honored, and which of several
candidate records becomes the active pointer. The validator's soundness
(never accepting a false `VALID`) and the writer's integrity (accurately
recording what a human actually reviewed and decided) are two distinct
properties. This contract binds both files but does not claim they
carry identical security roles — see the amended contract §50 for the
full writeup.

## 7. Additional HMIC-Owned Files — Dependency Walk

Both new files' `import` statements were read directly (not inferred
from docstrings). PCAE-owned modules referenced:

- `pcae.core.hatp_bootstrap` (`HATPTrustStore`, `HATPTrustStoreError`,
  `resolve_canonical_deployment_root`) — **already frozen** (entry 4).
- `pcae.core.paths` (`HarnessPath`) — **not** a frozen file; already
  adjudicated **B — non-authority utility** by the contract's own §49
  transitive-completeness table ("a path-join helper cannot change a
  verification/approval outcome"). That adjudication is inherited
  unchanged by this phase, not redone.
- `pcae.core.repository_identity` (`RepositoryIdentityError`, `is_
  valid_repository_instance_id`, `read_repository_identity`) — **already
  frozen** (entry 6).
- `pcae.core.hatp_mandatory_certification` — imported by the admin
  script; this is the other file already being added in this same
  amendment.

Neither file imports `hatp_mandatory_cutover.py`, `permission_broker.py`,
`permission_broker_foundation.py`, `rollback_approval_evidence.py`,
`hatp_ag_authority.py`, or `hatp_rollback_consumption.py` — confirmed by
direct source reading, not merely by citing each module's own docstring
claim to that effect.

**Classification of all candidates (per the governing instruction's own
A/B/C/D/E scheme):**

- A (must bind): `core/hatp_mandatory_certification.py`,
  `scripts/hatp_certification_admin.py`.
- B (already in original 22): `pcae.core.hatp_bootstrap`, `pcae.core.
  repository_identity`.
- C (non-authority utility): `pcae.core.paths` (pre-adjudicated by §49,
  inherited).
- D (separate trusted environment): none newly identified.
- E (uncertain — STOP): none. No candidate required escalation.

**Conclusion: the transitive-dependency closure for the two new files
adds zero additional PCAE-owned files beyond the two files themselves.**
No other newly-introduced HMIC implementation module exists — all Wave
A–D logic lives in the single `core/hatp_mandatory_certification.py`
module; Wave E introduced no second script.

## 8. `scripts/` Path-Grammar Confirmation and Repair

HMIC-REQ-050's pre-amendment framing sentence read "Paths under
`src/pcae/` are given relative to that directory; contract paths are
given relative to the repository root" — literally naming only two
categories and leaving a repository-root-relative *non-contract* path
(`scripts/hatp_certification_admin.py`) structurally unaddressed by the
prose, even though HMIC-REQ-055's canonicalization rule was already
fully path-shape-agnostic. This phase repairs the framing sentence in
place (amended contract §17) to read "every other path is given
relative to the repository root," removing the implicit
contract-files-only reading. This is a normative clarification of
existing intent (the four `docs/contracts/...` entries were always
repository-root-relative, non-`src/pcae/` paths, so the grammar already
had to support that shape), not a new binding rule. HMIC-REQ-055 itself
required no textual change. No symlink loophole is introduced:
HMIC-REQ-061/062 apply identically to the new `scripts/` entry.

## 9. Exact v1.1 Frozen Set (24 Files)

Confirmed: exactly the two W-1 additions are required (§7). New frozen
subject:

```
core/hatp_mandatory_cutover.py
core/hatp_ag_authority.py
core/hatp_rollback_consumption.py
core/hatp_bootstrap.py
core/human_approval_trusted_provenance.py
core/repository_identity.py
core/rollback_approval_evidence.py
core/hatp_evidence_store.py
core/hatp_signed_evidence.py
core/agent.py
commands/agent.py
cli.py
core/permission_broker.py
core/permission_broker_foundation.py
core/hatp_providers.py
core/hatp_fido2_provider.py
core/hatp_piv_provider.py
core/hatp_hardware_credentials.py
core/hatp_mandatory_certification.py

docs/contracts/HATP_MANDATORY_ROLLBACK_CONSUMPTION_CONTRACT.md      (HMRC-001)
docs/contracts/HUMAN_APPROVAL_TRUSTED_PROVENANCE_CONTRACT.md        (HATP-001)
docs/contracts/HATP_SIGNING_CEREMONY_EVIDENCE_STORE_CONTRACT.md     (HSCE-001)
docs/contracts/ROLLBACK_APPROVAL_EVIDENCE_CONTRACT.md               (RAE-001)
scripts/hatp_certification_admin.py
```

19 `src/pcae/`-relative entries + 5 repository-root-relative entries =
24. The original 22 are preserved byte-for-byte and in their original
relative order; the two new entries were appended to the end of their
respective bucket (`core/hatp_mandatory_certification.py` at the end of
the `src/pcae/`-relative bucket; `scripts/hatp_certification_admin.py`
at the end of the repository-root-relative bucket). No glob, no
directory wildcard, no runtime discovery — every entry is a literal
path. Per HMIC-REQ-056 (unchanged), the *digest-processing* order
remains strict lexicographic sort of canonical path strings regardless
of this prose presentation order — the two new entries' presentation
position therefore has no bearing on their processing order, so no
further ordering amendment was needed.

## 10. Self-Reference Resolution (Freezing §49's Deferred Question)

The original contract's §49 explicitly deferred the question of whether
a future HMIC validator should bind its own source, pending that
validator's existence. It now exists. This phase freezes the answer:
self-binding is **not circular**, for the same reason `core/hatp_
mandatory_cutover.py` has always been bound despite being the file that
*enforces* HMRC-001's readiness gate. Reasoning, in four steps: (1) a
certification stores an *expected* implementation identity at the
moment a human Protected Admin certifies it; (2) at validation time, the
*current* implementation identity is freshly re-derived from the live
repository's own bytes on every call, never cached; (3) the validator's
own source bytes are now among the files that re-derivation hashes; (4)
therefore editing the validator's source changes the current
implementation identity being computed, which then fails to match the
identity a stored certification names — exactly the same mechanism that
already governs every other frozen file. There is no fixed-point
problem: the validator never asks "am I currently valid," only "does
the live repository's current implementation identity match what this
specific stored certification names" — and its own bytes are one input
to the left-hand side of that comparison, computed completely
independently of the stored certification's own claims.

## 11. Admin-Script Self-Binding (No Digest Circularity)

Identical, non-circular structure: at `certify` time, the script
computes `implementation_scope_digest` over the frozen set *including
its own on-disk bytes at that moment*, then constructs a certification
naming that digest. The two computations happen in strict sequence over
disjoint data — the **implementation digest** is computed over frozen
*source* files (including the admin script's own source, once bound);
the **certification ID** is computed *afterward*, over the
*certification payload* (which includes the already-computed
implementation digest as one input) — never over the generated
certification artifact's own bytes a second time. No later step feeds
the certification artifact's own hash back into the implementation
digest.

## 12. No Certification-Artifact Self-Hash

`implementation_scope_digest`'s frozen file set contains only PCAE-owned
production *source* files and the four bound *contract* documents —
never `certifications.json`, `certification-bindings.json`, or any
other generated protected-storage artifact, before or after this
amendment. True circularity (a digest partly a function of its own
prior output) does not exist anywhere in this scheme.

## 13. HMIC-REQ-050/052 Amendment

Both revised **in place**, no new requirement ID minted:

- **HMIC-REQ-050**: enumeration widened from 22 to 24 files (§9 above);
  framing sentence generalized (§8 above); "no more, no fewer" retained,
  now explicitly stated to admit no caller-suppliable legacy-scope
  override.
- **HMIC-REQ-052**: closure rule split into two limbs — (a) the
  original HMRC-001/HATP-001 consumption-chain closure (unchanged), and
  (b) a new limb covering this certification's own implementation
  semantics (parsing, identity derivation, storage, active binding,
  revocation, Validation Status determination), reachable from the
  validator's or admin ceremony's own call graph. Limb (b) is the rule
  under which the two new files are added; §7 above is this phase's own
  worked application of it.

No stale "22 files" claim remains anywhere in the contract outside
historical (§49) or explicitly-labeled transitional (§41 attacks #33-34,
§50) context — verified by direct text search of the amended contract
file.

## 14. HMIC-REQ-063 — Explicitly Preserved

Byte-unchanged. This amendment binds *on-disk source-byte* identity for
two additional files; it does not add, imply, or require any
executed-code/runtime-module-resolution check (import shadowing,
`sitecustomize`, `PYTHONPATH` injection, editable-install redirects
remain unaddressed, exactly as before). Source-byte identity binding and
executed-source provenance binding remain two distinct, independently
tracked concerns.

## 15. Self-Reference Resolution — Not Reopening B-149O.19.3-1

B-149O.19.3-1 (the provider-layer under-binding finding) remains
INDEPENDENTLY CONFIRMED CLOSED, unchanged by this phase. This phase's
own dependency walk (§7) did not find the same defect class recurring
in the two new files' own dependencies.

## 16. Version Evolution — HMIC-001 v1.0 → v1.1

HMIC-001 moves from **v1.0** to **v1.1**, reversing §49's earlier
decision to keep v1.0 unbumped through the B-149O.19.3-1 repair. §49's
rationale for not bumping ("v1.0 was never independently verified...
no implementation of v1.0 has ever been built or certified against it")
no longer holds: v1.0 *was* subsequently independently re-verified
(149O.19.3R.1: VERIFIED WITH NON-BLOCKING FINDINGS — CONFORMS), and a
real implementation of v1.0's certification/validation/admin surface
now exists (Waves A–E). Continuing to call the widened scope "v1.0"
would let "a v1.0 certification" silently mean two different things
depending on when the reader encountered the term — the ambiguity
HMIC-REQ-140 (unknown-version fail-closed) exists to prevent. The
version bump makes the scope change explicit and unambiguous.

## 17. Old v1.0 Certifications — No Grandfathering

No v1.0-scoped certification (had one ever been created — none has;
§21 below) would silently satisfy v1.1 validation. No compatibility
mode, no caller-suppliable `legacy_scope`/`version=1.0`/`file_count=22`
override, and no alternate scope selector exists (HMIC-REQ-050's "no
more, no fewer" enumeration is unconditional). See attack matrix rows
#33-34 (amended contract §41) for the precise mechanism and its honest
"not yet operative until production alignment" caveat.

## 18. Certification Schema Version vs. Contract Semantic Version

`CERTIFICATIONS_DOCUMENT_SCHEMA_VERSION` and `CERTIFICATION_BINDINGS_
DOCUMENT_SCHEMA_VERSION` (the artifact-level JSON schema versions in
`core/hatp_mandatory_certification.py`) are **not** changed and remain
**1**. Nothing about this amendment alters `CertificationRecord`'s field
set, `CertificationBinding`'s field set, or either document's on-disk
JSON shape — only the frozen file list HMIC-REQ-050 enumerates changed.
Contract semantic version and artifact schema version remain two
independent axes; this phase moves only the former.

## 19. Digest Algorithm / Canonicalization / Git-Identity / Contract-Binding

None of HMIC-REQ-054 (file digest algorithm), HMIC-REQ-056 (file
order — unchanged: strict lexicographic sort of canonical path
strings), HMIC-REQ-057 (per-file record domain), HMIC-REQ-058 (digest
derivation), HMIC-REQ-059-062 (missing/extra/symlinked/non-regular
frozen file handling), HMIC-REQ-046-049 (git-identity component), or
§20's contract-binding-set mechanics (HMIC-REQ-067-070) were changed —
only the input file list (HMIC-REQ-050) and its closure rule
(HMIC-REQ-052) changed. The eight-contract bound set (HMIC-001,
HMRC-001, HATP-001, HSCE-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001)
is unchanged; among these, only HMIC-001's own bytes changed. **Note:**
HMIC-001's own version is not a member of any `CertificationRecord`'s
`contract_versions` mapping (HMIC-REQ-067 names exactly HMRC-001/
HATP-001/HSCE-001/RAE-001) — this amendment does not change that. The
mechanism by which this contract's version change becomes enforced
against a stored certification is exclusively through
`implementation_scope_digest`, operative once production identity
derivation is realigned to hash the 24-file v1.1 set (a future phase).

## 20. Requirement / CIVC / Attack Counts After Amendment

- **Requirements:** exactly `HMIC-REQ-001`–`HMIC-REQ-144` (144 total, no
  renumbering, no new ID minted — HMIC-REQ-050/052 revised in place).
  Mechanically re-verified: 144 distinct IDs, contiguous 1–144, no gaps,
  no duplicates.
- **CIVC:** exactly CIVC-1–CIVC-12 (unchanged — CIVC-4 strengthened in
  place to state it now covers the certification/validation
  implementation itself; no invariant added or removed). Mechanically
  re-verified: 12 distinct IDs.
- **Attack matrix:** grows from 32 to **34** rows. Attack #11
  strengthened in place (names the two new files explicitly, mirroring
  the 149O.19.3R precedent for the four provider files). Two genuinely
  new rows added: #33 (v1.0-scope replay under a v1.1 environment) and
  #34 (file-set-downgrade / production-still-22-during-transition) —
  neither pre-existing row addressed a *contract-version-scope* change
  as distinct from a *file-bytes-drift* change (attack #14's
  "contract-version replay" concerns only the four externally-bound
  HMRC/HATP/HSCE/RAE contracts, not HMIC-001's own frozen-scope
  enumeration). Mechanically re-verified: 34 distinct rows, contiguous
  1–34.

## 21. Production-Contract Divergence After This Phase (Expected)

As of this amendment: HMIC-001 v1.1's contract text names a 24-file
frozen subject; `core/hatp_mandatory_certification.py`'s own
`_FROZEN_AUTHORITY_BEARING_FILES` constant (and its module-level
`assert len(...) == 22`) still implements the 22-file v1.0 subject,
**unchanged by this phase**. Production is therefore temporarily **not
conformant** to HMIC-001 v1.1's implementation-scope enumeration, by
intentional sequencing. This divergence has **zero** functional effect
on any real readiness decision: the hard-coded `False` ceiling is
unchanged, zero production callers of the validator exist, and no real
certification state exists anywhere on this host to be validated
against either file count. Fail-closed holds throughout regardless of
which file count production currently computes over.

## 22. W-1 Status After This Amendment

**REPAIRED AT CONTRACT LEVEL — INDEPENDENT VERIFICATION PENDING —
PRODUCTION 24-FILE ALIGNMENT PENDING.** Not CLOSED. Three separate,
still-open facts:

A. This contract now enumerates 24 frozen files, including the
   validator and admin-script source (§9 above).
B. An independent verification phase must confirm that enumeration is
   correct — complete, minimal, structurally sound — before it may be
   relied upon (§24 below).
C. `core/hatp_mandatory_certification.py`'s own production
   identity-derivation code still implements the pre-amendment 22-file
   enumeration and was **not** modified by this phase (§27 below) — a
   dedicated, bounded future implementation-alignment phase must update
   it to the verified 24-file set, and that alignment must itself be
   independently verified, before Wave F may be considered.

## 23. Contract Traceability

The amended contract's §17 (HMIC-REQ-050/052), §40 (CIVC-4), and §41
(attacks #11, #33, #34) each map back to: implementation identity
completeness (§7, §9 above); no self-certification (§10-11 above,
unchanged CIVC-12); implementation-drift invalidation (§16-19 amended
contract, restated §19 above); and validator trust / writer-vs-validator
distinction (§6 above). §50 of the amended contract is the sole new
section, in the same format as §49's own repair-history precedent.

## 24. Implementation Plan Traceability

This phase fulfills 149O.19.4's Stop Condition W-1 (§10.3, §13) at the
contract level only. `docs/PHASE_149O_19_4_...IMPLEMENTATION_PLAN.md`
itself was **not** modified to retroactively claim it always specified
24 files — this new phase document is the amendment-note artifact, per
repository practice of documenting contract evolution in a new phase
document rather than rewriting historical planning text.

## 25. Tests

New test module: `tests/test_phase_149o_19_5e_1_hmic_v1_1_validator_
admin_identity_contract_evolution.py`. Covers: exact new version (v1.1);
exact new file count (24); original 22 preserved; core module path
present; admin script path present; every frozen path exists on disk;
canonical path/grammar rules pass for the `scripts/` entry; no
duplicate entries; requirement/CIVC/attack inventory counts (144/12/34);
W-1 contract language present; production-alignment-still-pending is
mechanically confirmed (production constant still says 22, matching the
amended contract's own §21/§50 disclosure — not a contract-evolution
failure); hard-coded `False` unchanged; zero readiness/cutover callers;
zero production source diff; upstream-contract bytes (HMRC-001,
HATP-001, HSCE-001, RAE-001, RWMPC-001, PBPA-001, PBPC-001) unchanged.

## 26. Findings

No new finding raised by this phase. B-149O.19.3-1 remains
independently closed. B-149O-1..4 remain independently closed at the
system implementation/enforcement boundary with deployment/operational
activation deferred.

## 27. Contract-Evolution Verdict

```
HMIC-001 v1.1: FROZEN
— VALIDATOR/ADMIN IMPLEMENTATION IDENTITY CONTRACT EVOLUTION COMPLETE
— PENDING INDEPENDENT VERIFICATION
```

```
W-1: REPAIRED AT CONTRACT LEVEL
— INDEPENDENT VERIFICATION PENDING
— PRODUCTION 24-FILE ALIGNMENT PENDING
```

Not `W-1 CLOSED`. Not `READY FOR WAVE F`.

## 28. Recommended Next Phase

**149O.19.5E.2 — HMIC v1.1 Validator/Admin Implementation Identity
Contract Independent Verification** (or repository-conventional
equivalent), which must independently: reconstruct the v1.0 22-file set
and the actual Wave A–E implementation; independently determine whether
the two additions are sufficient and complete under HMIC-REQ-052's
broadened closure rule; verify the 24-file transitive closure; verify
the self-reference resolution; verify v1.0-replay-rejection semantics
(and their "not yet operative" caveat); verify path/digest semantics;
verify the W-1 contract-level repair; and verify production remains
intentionally stale at 22 and fail-closed. If v1.1 verifies, the next
phase after that is **not** Wave F — it is a bounded implementation-
alignment phase (e.g. 149O.19.5E.3) that updates production identity
derivation from 22 to the verified v1.1 file set, followed by that
alignment's own independent verification. Only after both may Wave F be
considered.

## 29. Required Final Report

See phase-completion metadata and canonical report for the structured
field-by-field confirmations (Phase ID, HMIC old/new version, W-1
entering/exit status, old/new frozen file counts, exact deltas,
validator/admin classification, transitive closure rationale, `scripts/`
canonicalization result, digest-algorithm-unchanged confirmation,
contract-binding-changed confirmation, v1.0-replay-result,
requirement/CIVC/attack counts, production-alignment-pending
confirmation, hardcoded-False-unchanged confirmation, no-readiness-
integration confirmation, no-production-source-changed confirmation,
HATP production readiness, runtime state). All fields required by the
governing phase instruction §96 are populated identically to this
document's own §1, §16, §20-22, §27-28 above; no field is left implicit.

**Explicit confirmations (restated):** No production source
(`src/pcae/**`, `scripts/**`) was modified. Only HMIC-001 changed among
the eight bound contracts; HMRC-001, HATP-001, HSCE-001, RAE-001,
RWMPC-001, PBPA-001, and PBPC-001 all remain byte-unchanged. The current
production identity implementation was **not** changed from 22 to 24
files during this contract-only phase. The hard-coded `False` readiness
ceiling remained unchanged. No readiness integration occurred. No
certification artifact, active binding, or revocation state was
created. No Cutover Record or activation marker was created or
modified. No real `HATP_MANDATORY` activation occurred. No Class-B
provisioning occurred. No Permission Broker behavior changed. `POL-005`
remained unchanged. No `COMP-002` capability was implemented.
Runtime/executed-source binding remained deferred under HMIC-REQ-063.
W-1 is repaired only at the contract level, not yet closed. Independent
v1.1 contract verification is mandatory next. After contract
verification, production 24-file alignment and its independent
verification remain mandatory before Wave F. B-149O.19.3-1 remains
independently closed. B-149O-1..4 remain independently closed at the
system implementation/enforcement boundary with deployment/operational
activation deferred. HATP production remains **NOT READY**. Runtime
remains **Observed / observe / unavailable**.

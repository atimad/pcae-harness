# Phase 149O.20L.7O.2A.2 — RepositoryIdentity Write-Path Remediation Human Election + CHGR Publication

## 0. Status

**Human election + authority publication only.** No Dell mutation performed (no `chmod`, no `chown`, no `setfacl`). No RepositoryIdentity created. No DeploymentBinding created. No HMIC certification performed. Boundary C, Boundary A, and HATP_MANDATORY activation remain untouched and **NOT AUTHORIZED**.

**Phase-entry commit:** `6d4dc2cef389bec1e31697c626d07a534c5e88f2` (`Phase 149O.20L.7O.2A.1: sync active task allowed-file list`). `git status --short` clean at entry, `pcae check --json` → `passed`.

**Final verdict:** **AUTHORIZED — READY FOR INDEPENDENT AUTHORITY VERIFICATION.**

## 1. Fresh Proposition-Currentness Gate (Performed Live, Read-Only, on hac-dell)

Per the governing instruction's §6 requirement, live read-only checks were issued against hac-dell via `ssh hac-dell` + `sudo -n` (no mutation flag, no write command) before the election was presented:

| Check | Live result | Expected | Match |
|---|---|---|---|
| hostname | `atila-Latitude-E5470` | `atila-Latitude-E5470` | yes |
| machine-id | `54ff22ce400b475aa0d55cb68f4a3334` | `54ff22ce400b475aa0d55cb68f4a3334` | yes |
| source SHA (`git rev-parse HEAD`) | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` | `b0840e96a7ffb12308e95828aa5927c3e7c770c0` | yes |
| detached/clean source | `git status --short` empty; `git symbolic-ref -q HEAD` exit 1 (detached) | clean, detached | yes |
| `.pcae` owner/group/mode | `root:pcae 750` | `root:pcae 0750` | yes |
| extended ACL | `getfacl -p .pcae` → only `user::rwx`/`group::r-x`/`other::---` (no extra ACL lines) | none | yes |
| `RepositoryIdentity` | `ls .pcae/repository-identity.json` → No such file or directory | absent | yes |
| `DeploymentBinding` | no artifact found under `/opt/pcae`; Protected Root inspected directly (below) | absent | yes |
| Protected Root | `ls -la /etc/pcae/hatp/trust-store/` → empty directory, `root:pcae`, mode unchanged since prior phase's own live read | unchanged | yes |
| certification | no `CertificationRecord`/`CertificationBinding` instance artifact found anywhere under `/opt/pcae` (only source files matching the substring `certification`, confirmed by `find -iname` review) | absent | yes |
| HMIC digest (`derive_implementation_scope_digest`, executed live on Dell as `pcae` via the canonical invocation, §2) | `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` | `65ff8ab06b5cd7feb2505742cfbb112ffd386c5b2cf34c2d7f3446d92afe15b8` | yes (also independently reproduced on this Mac's working tree, same digest) |
| canonical HBDC result | `NON_COMPLIANT`, sole residual `HBDC-REQ-042 no_repository_identity_present`; `HBDC-REQ-036` independently confirmed `True` (`launcher_agent_unwritable`) | `NON_COMPLIANT` / sole residual `HBDC-REQ-042` | yes |

Zero mismatch. **Proceeded to election — no STOP.**

## 2. Canonical HBDC Invocation Used

Exactly the corrected Action-9 environment restated at `149O.20L.7O.2A.1 §26`, run live this phase:

```
sudo -n -u pcae env -i \
  PATH=/opt/pcae/runtime/venv/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  HOME=/home/pcae PYTHONNOUSERSITE=1 \
  bash -c 'cd /opt/pcae/runtime/src && python3 <script invoking
    pcae.core.hatp_class_b_conformance.verify_class_b_deployment_conformance()>'
```

The invoking script and the HMIC-digest script were copied to `/tmp` on hac-dell via `scp`, executed read-only (no filesystem write performed by either function), and deleted immediately after use (`rm -f`). Neither script mutated any file inside `/opt/pcae` or `/etc/pcae`.

## 3. Historical CHGR Inventory — Independently Re-Enumerated

```
ls .pcae/publication-execution/records/chgr-*.json
    -> chgr-0e37ed1340b14311826722c4dbf3e856.json
    -> chgr-541cb08c313b4f8884970172d37c5a1d.json
    -> chgr-71bd24f9d3d742d6baac772e480fc876.json
    -> chgr-96a0ce12756e4cc892492a87af1db832.json
    -> chgr-d4343fa51b9743f3abaeb87a881a78b1.json
grep -l "/opt/pcae/runtime/src/.pcae\|1770" .pcae/publication-execution/records/chgr-*.json -> (no match)
```

Exactly the five pre-existing records, none referencing this path/mode. **No historical CHGR authorizes this transition**, including `chgr-71bd24f9d3d742d6baac772e480fc876` (Boundary-P source-redeployment authorization, a different transition, explicitly not reused per the governing instruction).

## 4. Election Materials Presented to the Human

Presented in full, before any decision was requested: exact target (`hac-dell` / `atila-Latitude-E5470` / `54ff22ce400b475aa0d55cb68f4a3334`), exact path (`/opt/pcae/runtime/src/.pcae`), exact before/after state (`root:pcae 0750` → `root:pcae 1770`, no ACL either state), exact command (`chmod 1770 /opt/pcae/runtime/src/.pcae`, no `-R`, no `chown`, no `setfacl`), security rationale (sticky-bit mechanism, §1 of the governing instruction), the required disclosed correction (P-A′ fixes 38 of 39 declared write-required artifacts; `architecture-history.json` is the one exception, separate producer fix, deferred), the sticky-bit evidence-tier qualification (reference-verified, not empirically tested), the fresh currentness table (§1 above), and the full material-effects disclosure of what APPROVE means (§9 of the governing instruction — RepositoryIdentity/DeploymentBinding creation explicitly NOT authorized by this election).

## 5. Human Election

Presented exactly three choices (APPROVE / DECLINE / AMEND) via a structured decision prompt, no default, no inference.

**Selected: APPROVE.**

## 6. Separate Explicit Confirmation

Per the governing instruction, the initial APPROVE did not trigger publication. A second, separate, explicit confirmation was required and presented as its own distinct prompt showing the exact preview:

> "Confirm publication of authority to change /opt/pcae/runtime/src/.pcae on hac-dell from root:pcae 0750 to root:pcae 1770 only (chmod 1770, no -R, no chown, no setfacl), retaining root:pcae ownership and no extended ACL, with no RepositoryIdentity, DeploymentBinding, certification, or activation authorized by this election."

**Confirmed: CONFIRM.** `approval != confirmation` preserved — the decision-session workflow (§7 below) required both the `select` and the subsequent `confirm` step as distinct commands, and the human was asked twice, separately, in the conversation itself.

## 7. Confirmation-Currentness Re-Check (Immediately Before Publication)

```
git rev-parse HEAD (Mac)                          -> 6d4dc2cef389bec1e31697c626d07a534c5e88f2 (unchanged since §1)
git rev-parse HEAD (hac-dell, sudo -n)             -> b0840e96a7ffb12308e95828aa5927c3e7c770c0 (unchanged since §1)
stat -c '%U:%G %a' /opt/pcae/runtime/src/.pcae     -> root:pcae 750 (unchanged since §1)
```

No drift on any authority-critical fact since §1. Selected option remained APPROVE. **Proceeded to publication.**

## 8. Decision-Session Workflow (Single Attempt — Successful)

Unlike `149O.20L.7N.2` (which required two attempts due to a `conditions`-length schema overflow), this phase's `conditions` text (3059 characters) and `rationale` text (2938 characters) were both drafted under the schema's 5000-character limits from the outset (independently re-confirmed against `human_governance_record.schema.json` before drafting), and the workflow succeeded on the first attempt:

1. `pcae decision-session create --template-ref class-b-boundary-p-provisioning-authorization --subject-ref "<367-char decision subject>" --owner-id "Atila Madai"` → `CDS-bc9a70fc-3913-4c8b-b95e-50ca0c26091c` (`Created`).
2. `pcae decision-session evidence <session-id> --declare ...` (both proposition/verification docs plus six live-read evidence tags: source SHA, `.pcae` mode/ACL, hostname, machine-id, canonical HBDC result, HMIC digest) → `EvidenceReady`.
3. `pcae decision-session select <session-id> --option-id approve --options-presented approve --options-presented decline --options-presented amend --template-version 1.0 --as-identity "Atila Madai" --rationale "<2938 chars>" --conditions "<3059 chars>"` → `DecisionSelected`.
4. `pcae decision-session preview <session-id> --as-identity "Atila Madai"` → `preview_digest 616ffc29fc0a6f20110a9decbb0d72a9587426ec91ba1eb9db38eba30530b2bd` — independently confirmed to reproduce subject, template, rationale, conditions, and selected option (`approve`) exactly as entered.
5. `pcae decision-session confirm <session-id> --preview-digest 616ffc29fc0a6f20110a9decbb0d72a9587426ec91ba1eb9db38eba30530b2bd --statement "<confirmation statement, §6>" --as-identity "Atila Madai"` → `Confirmed`, `authority_evaluation_stage_1: indeterminate` (disclosed, advisory-only, non-blocking, consistent with prior phases' own disclosure of the same field).
6. `pcae decision-session readiness <session-id> --as-identity "Atila Madai"` → `package_id prp-b25318907ab842ddadc30bde67722944`, `disposition: pending`.
7. `pcae governance-record publish prp-b25318907ab842ddadc30bde67722944 --operator-id "Atila Madai"` → **success**: `record_id chgr-86aeb5cfa7c44020ad002bc9f80c5856`.

**No failed publication attempts this phase.**

## 9. Published CHGR

**Record ID:** `chgr-86aeb5cfa7c44020ad002bc9f80c5856`
**Path:** `.pcae/publication-execution/records/chgr-86aeb5cfa7c44020ad002bc9f80c5856.json`
**Lifecycle state:** `published`
**Selected option:** `approve`
**Assurance level:** `L0`
**Contract version:** `CHGR-001/1.0`
**Schema version:** `1.1`
**Template ref:** `class-b-boundary-p-provisioning-authorization` v`1.0` (same template family as the two precedents `chgr-0e37ed1340b14311826722c4dbf3e856` and `chgr-71bd24f9d3d742d6baac772e480fc876`)
**Decision session:** `CDS-bc9a70fc-3913-4c8b-b95e-50ca0c26091c`
**Preview digest:** `616ffc29fc0a6f20110a9decbb0d72a9587426ec91ba1eb9db38eba30530b2bd`
**Related records:** `confirmation_evidence_ref` → `chgrconf-698eefcec95841ef8350e94fa7a59ea8`; `provenance_ref` → `chgrprov-5a681f551c3646af81d7ecdb1a3ccff1`; `integrity_ref` → `chgrintg-2fa93bd13e7e440f8c98a283cff99872`.

**`decision_subject` (367 chars, programmatically measured):**

> "Authorize changing only /opt/pcae/runtime/src/.pcae on hac-dell from root:pcae 0750 to root:pcae 1770 (chmod 1770), retaining owner root and group pcae, adding no extended ACL, solely to permit pcae-principal runtime-local file creation while preserving sticky-bit protection of existing root-owned entries. Excludes RepositoryIdentity and DeploymentBinding creation."

## 10. Direct-Bound Facts — Proof

`conditions` (23 numbered items) directly embeds, in the CHGR's own persisted text, not solely via document reference: `hac-dell`, `atila-Latitude-E5470`, `54ff22ce400b475aa0d55cb68f4a3334`; the current source SHA `b0840e96a7ffb12308e95828aa5927c3e7c770c0`; the exact path `/opt/pcae/runtime/src/.pcae`; the exact before state (`root`/`pcae`/`0750`); the exact after state (`root`/`pcae`/`1770`); "no extended ACL added"; the exact command `chmod 1770 /opt/pcae/runtime/src/.pcae`; the reason/purpose; the sticky-bit security assumption with its evidence-tier qualification; the `architecture-history.json` correction; all fifteen exact exclusions (items 10–19); and the exact rollback (`chmod 0750 /opt/pcae/runtime/src/.pcae`, ownership unchanged, no ACL). `rationale` additionally carries the full security-rationale narrative, the disclosed correction, the evidence qualification, and the fresh HBDC/HMIC results.

## 11. Correction Disclosure — Proof

`rationale` and `conditions` (item 9) both state verbatim: *"P-A' fixes 38 of the 39 declared write-required .pcae artifacts. It does NOT fix architecture-history.json (separate producer/write-pattern issue, deferred, out of scope)."* No claim of complete write-required-inventory coverage appears anywhere in the published record.

## 12. Sticky-Bit Evidence Qualification — Proof

`rationale` and `conditions` (item 8) both state verbatim: *"REFERENCE-VERIFIED FROM PRIMARY LINUX/POSIX SOURCES ... not empirically tested by synthetic file creation on hac-dell in this or the prior phase; this is a disclosed evidence-tier qualification, not a blocking finding."*

## 13. Exclusions Binding — Proof

`conditions` items 10–19 explicitly prohibit, in the CHGR's own text: RepositoryIdentity creation (10); DeploymentBinding create/rotate/revoke (11); Protected Root mutation (12); source mutation/`git fetch`/`checkout` (13); venv modification (14); wrapper/launcher modification (14); Permission Broker modification (15); HMIC certification (16); Boundary C, Boundary A, HATP_MANDATORY activation (17); unrelated hac-dell paths/users/services/`hac-windows` (18); recursive chmod, any chown, any setfacl (19).

## 14. Rollback Binding — Proof

`conditions` item 20: exact rollback command `chmod 0750 /opt/pcae/runtime/src/.pcae`, owner `root` unchanged, group `pcae` unchanged, no extended ACL. Rollback is stated as belonging to the later execution phase on defined failure triggers only; no identity cleanup is described as relevant, since identity creation is not part of this transition.

## 15. Governance-Record Verification (Same-Phase Publication Sanity)

```
pcae governance-record inspect .pcae/publication-execution/records/chgr-86aeb5cfa7c44020ad002bc9f80c5856.json
    -> outcome: inspected

pcae governance-record verify .pcae/publication-execution/records/chgr-86aeb5cfa7c44020ad002bc9f80c5856.json \
  --related .pcae/publication-execution/records/chgrconf-698eefcec95841ef8350e94fa7a59ea8.json \
  --related .pcae/publication-execution/records/chgrintg-2fa93bd13e7e440f8c98a283cff99872.json \
  --related .pcae/publication-execution/records/chgrprov-5a681f551c3646af81d7ecdb1a3ccff1.json
    -> outcome: verified
       schema_shape: passed
       digest_self_consistency: passed
       lifecycle_structural_legality: passed
       confirmation_binding: passed
       assurance_truthfulness: passed
       provenance_consistency: passed
       integrity_consistency: passed
       template_resolution: skipped (no matching related template artifact file supplied -- same behavior observed for both historical precedents, not a defect)
```

All applicable checks passed. Per the governing instruction, this is same-phase publication sanity only — it does not replace independent `149O.20L.7O.2A.3` verification, which remains required before any execution phase may begin.

## 16. Lifecycle State

`published`; `selected_option_id: approve`; confirmation present (`confirmation_evidence_ref` resolved). **Not** marked executed/consumed — no execution occurred, none is authorized by this phase.

## 17. No Dell Mutation — Proof

Every command issued against hac-dell this phase was read-only (`hostname`, `cat /etc/machine-id`, `git rev-parse HEAD`, `git status --short`, `git symbolic-ref -q HEAD`, `stat`, `getfacl -p`, `ls`, `find`, and two disposable `python3` scripts invoking only the read-only `verify_class_b_deployment_conformance()` and `derive_implementation_scope_digest()` functions, deleted via `rm -f` immediately after use). No `chmod`, `chown`, `setfacl`, `git fetch`, `git checkout`, or any file-write command was issued against hac-dell. Post-publication re-check (§1 table, re-run): `.pcae` still `root:pcae 750`; `repository-identity.json` still absent; `/etc/pcae/hatp/trust-store` still empty.

## 18. No RepositoryIdentity — Proof

```
find . -iname "*repository-identity*.json" -not -path "*/.git/*"  -> (none, Mac-side)
ssh hac-dell (read-only) ls .pcae/repository-identity.json         -> No such file or directory
```

## 19. No DeploymentBinding — Proof

```
find . -iname "*deploymentbinding*.json" -not -path "*/.git/*"  -> (none, Mac-side)
ssh hac-dell (read-only) find /opt/pcae -iname "*deploymentbinding*.json" -> (none; only source .py files matching the substring)
```

## 20. No Certification — Proof

No `CertificationRecord`, no `CertificationBinding`, no active-certification state artifact created or referenced, on either the Mac working tree or hac-dell (only pre-existing source/doc files whose names contain the substring "certification" were found; none is a persisted instance artifact). No Boundary C, Boundary A, or HATP_MANDATORY activation performed; all remain `NOT AUTHORIZED` (`conditions` item 17).

## 21. Process Observation Carried Forward From 7O.2A.1

`149O.20L.7O.2A.1` used two plain, hook-checked `git commit` invocations for lifecycle bookkeeping because no canonical PCAE wrapper was available for those exact bookkeeping commits. That is **not** treated as a general precedent authorizing raw `git commit` in this phase. This phase used exclusively `pcae task`, `pcae decision-session`, `pcae governance-record publish`, `pcae commit implementation`, and `pcae phase complete` for all governed lifecycle actions; the canonical supported path was available and used throughout, so no lifecycle-tooling gap is reported this phase.

## 22. Runtime State

```
pcae runtime inspect
    -> Runtime state: Observed
       Execution capability: unavailable
       Maximum plugin capability: observe
       Registry status: empty
```

Unchanged — `Observed / observe / unavailable`.

## 23. Governance

Normal governed PCAE lifecycle used throughout this phase (`pcae task transition`, `pcae task update`, `pcae decision-session`, `pcae governance-record publish`, `pcae commit implementation`, `pcae phase complete`, `pcae push`). No raw `git commit`/`git push`. No `--no-verify`. No force push. No hook/finalization bypass. No Dell mutation command issued.

## 24. Final Verdict

**AUTHORIZED — READY FOR INDEPENDENT AUTHORITY VERIFICATION.**

## 25. Expected Clean Authorized State

| Item | Status |
|---|---|
| Proposition | Independently verified (`149O.20L.7O.2A.1`), disclosed correction carried forward |
| Fresh currentness gate | Passed, zero drift (§1) |
| Human election | APPROVE |
| Separate confirmation | Present |
| CHGR | Published (`chgr-86aeb5cfa7c44020ad002bc9f80c5856`) |
| Failed publish attempts | None |
| `.pcae` on hac-dell | Still `root:pcae 0750`, no ACL |
| Execution authority | Published but INDEPENDENT VERIFICATION PENDING |
| Dell mutation | None |
| RepositoryIdentity | Absent |
| DeploymentBinding | Absent |
| Certification | Absent |
| Boundary C / Boundary A | Not authorized |
| Runtime | Observed / observe / unavailable |

## 26. Recommended Next Phase

**`149O.20L.7O.2A.3` — RepositoryIdentity Write-Path Remediation Authority Independent Verification.**

Must independently reconstruct: the human APPROVE choice; the separate confirmation; the exact proposition; currentness; the new CHGR (`chgr-86aeb5cfa7c44020ad002bc9f80c5856`) and its integrity/provenance/confirmation-evidence chain; the direct-bound before/after mode facts; the correction disclosure; the exclusions; the rollback; and zero Dell mutation. Only after a clean `149O.20L.7O.2A.3` may `149O.20L.7O.2A.4` (`chmod 1770` execution) begin, gated in turn on that clean verification. Then `149O.20L.7O.2A.5` (independent real-host verification), and only after a clean `7O.2A.5`, a `RepositoryIdentity` creation retry under a new phase.

## Strategic Breakpoint

Unchanged, unreached, not begun this phase: after eventual `RepositoryIdentity` + `DeploymentBinding` first-use execution and a clean independent real-host verification, pause before Boundary C to begin the DeepSeek Harness comparative study and the PCAE Runtime Adapter/Plugin architecture.

# Independent identity contract version and historical-test review

Read-only review of 79ea7e1644535d011da6ca3869b5557b44c50737 -> c4f452c6a8e5d45b7076cd984d6f701a01cfa5e4. No repository edits, commits, push, provisioning, or production execution performed.

## Contract version verdict

No blocking version-classification defect found. HELPER4.0 replaces impossible hpahi/hpawi equality and changes the singular generic-helper execution interpretation; this cannot fit REQ-108's no-remeaning MINOR permission. PAWA3.0 likewise replaces REQ-336 shared-ID and REQ-311 generic-only currentness recognition beyond REQ-153's permitted clarifications. Both MAJOR classifications are independently justified.

PPA2.1 is independently supportable under REQ-070: stricter parent/currentness recognition with explicit schema2 migration is a tightened acceptance bound. Although schema compatibility breaks, this contract's versioning rule is semantic authority evolution, not ordinary software-library semver. REQ-069 triggers do not require MAJOR merely for a stricter installation schema. The existing v2.0 REQ-077/081/085/086 already put ceremony and evidence authorship in the same protected presentation process. New REQ-106 explicitly specializes the old REQ-084 ambiguous transport wording without changing that holder, moving authority across a process boundary, introducing a channel, or broadening issued authority. The discarded interpretation (generic H receives a second evidence request) was incompatible with those preexisting same-process ownership clauses. Therefore this is reconciliation/tightening, not the ownership restructure that made PPA2.0 MAJOR.

New supersession coverage: HELPER-172/174 resolve REQ-021; 173 resolves generic-only path/profile interpretations; 176 resolves Model E scope tuple; 177 explicitly resolves Request/Response version/shape references; 180 resolves PPA evidence role; 181 resolves legacy runtime eligibility versus installer-only migration. PAWA-341/342 and PPA-105/106 explicitly select replacements. New header notices scope historical counts, freeze status, byte-unchanged statements, and implementation-absence claims to their historical epochs. No unresolved normative contradiction identified within this review's scope.

Reference clarity note (non-blocking): HELPER-174 line 2472 references `under §33 steps 1–8` without repeating PAWA's document name; HELPER local §33 is the inventory. Context says live PAWA state, and existing §7 explicitly identifies PAWA §33, so this is resolvable shorthand rather than an orphan security predicate. Full document qualification would improve precision. Historical helper clauses also use §number shorthand for requirement IDs; these are not new defects.

## Independently derived inventories

- HELPER: 184 unique declarations, numeric 001..183 and lettered 114A; 24 unique invariants PAWAH-INV-1..24.
- PAWA: 344 unique declarations 001..344; 17 unique invariants PAWA-INV-1..17.
- PPA: 108 unique declarations 001..108; 12 unique invariants PPA-INV-1..12.
- HELPER v3.0 threat matrix: exactly 40 rows, IDs 1..40 (including bold 31/32); unchanged by delta. Identity appendix adds exactly 12 rows. PPA identity appendix adds 4 rows. These are additive appendices, not replacement matrices.
- No orphan fully qualified self-document requirement references in any of the three contracts; initial strict regex must allow `REQ-114A (` declaration syntax to avoid a false orphan.
- New cross-document references resolve to existing clauses and retain the three-family Model E/no-export/no-legacy-factory constraints.

## Historical 13-assertion reconciliation audit

All 13 edited functions listed in the predecessor rationale were inspected directly against git diff, rather than trusting the rationale. Classifications:

1. PPA-IV test_12 byte equality: justified historical re-scoping to exact immutable 79ea7e1 endpoint. Original equality is retained; no claim about current PPA integrity follows from this test now.
2. PPA-contract test_03 header: justified current version 2.0 -> 2.1; frozen/pending assertions preserved.
3. PPA-contract test_06 inventory: justified exact contiguous/unique 103 ->108.
4. PPA-contract test_07 v2 additions: justified immutable epoch endpoint, preserving exact 077..103 expectation.
5. TB-contract-IV test_05 sibling header: justified bounded tuple addition of PPA2.1; other contracts unchanged.
6. TB-contract test_01 PAWA header: justified 2.0 ->3.0 with frozen status retained.
7. TB-contract test_03 inventory: justified exact contiguous/unique 340 ->344.
8. TB-contract test_04 v2 additions: justified immutable endpoint, preserving exact 310..340 expectation.
9. TB-contract test_62 sibling/schema checks: justified PPA header 2.0 ->2.1; existing unchanged sibling checks and requirement inclusion preserved.
10. TB-contract test_63 PPA header: justified bounded compatibility tuple addition of 2.1.
11. PAWA13 test_04 version: justified bounded current3.0 addition, historical1.3 assertion preserved.
12. PAWA13 test_35 sibling bytes: justified current PPA2.1 header; old requirement inclusion/sibling byte checks retained.
13. PAWA13 test_39 contract-only delta: justified immutable pre-identity endpoint; historical allowlist unchanged. This test no longer inspects future working-tree contract mutations, intentionally; it is historical evidence rather than a current scope guard.

No assertion was deleted, skipped, xfailed, inverted, reduced to an always-true condition, or widened to arbitrary future versions. The historical pinning removes ongoing live-tree coverage from those specific assertions, but preserving a past phase's no-change claim on an explicitly frozen epoch is justified after a separately authorized contract evolution. Fresh current-epoch assertions are needed and present in the new identity suite. The 13 changes should not be described as continued live byte-integrity coverage.

Additional earlier changes in the full predecessor delta also update HELPER version/count guards and pin older PAWA/PPA hash expectations. They follow the same justified classification. Some test names/docstrings/count comments remain historically named and can be misleading (e.g. an old count-trailer test asserts historical172 alongside current184), but the actual checks are not weakened security assertions.

DELEGATED .3 FINALIZATION / COMMIT / PUSH: UNAUTHORIZED.

Validation: reran exactly the 13 listed assertion node IDs with `.venv/bin/python -m pytest -q`: **13 passed in 0.46s**, process exit0. Raw output `/tmp/identity-iv-13-epoch-tests.log`. This validates the edited expectations, not production identity enforcement.

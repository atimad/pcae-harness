# Phase 92D.8 — Canonical Final Report Artifact Contract

```
phase_name    = phase_92d_8_canonical_final_report_artifact_contract
phase_version = 1.0
phase_status  = completed
recommended_next_phase = 93D — Shell Gate Audit Persistence Design
```

## 1. Why One Canonical Report Source Is Needed

Before 92D.8, Claude's terminal output and Telegram's attached Markdown could be generated separately and drift. The canonical artifact contract ensures one authoritative source for both.

## 2. Canonical Report Paths

| File | Purpose |
|------|---------|
| `.pcae/phase-completion-report.md` | Canonical Markdown report body |
| `.pcae/phase-completion-metadata.json` | Structured metadata |

## 3. Required Finalization Workflow

1. Implementation/validation finishes
2. Claude writes `.pcae/phase-completion-report.md`
3. Claude writes `.pcae/phase-completion-metadata.json`
4. `pcae phase complete` loads and validates the canonical report
5. PCAE generates `.pcae/phase-reports/latest.md` / `latest.json`
6. PCAE sends compact Telegram handoff text
7. PCAE attaches the canonical Markdown report to Telegram

## 4. Validation Rules

- Phase ID must appear in canonical report (`Phase 92D.8` pattern)
- Phase name fragment must appear
- Status must appear
- Report must be non-empty
- No stale mismatch (different phase ID mentioned)

If validation fails: trust downgraded with clear warnings.

## 5. Fallback Behavior

If canonical report is absent:
- Existing metadata-based report generation is used
- Trust warning added: "no canonical report artifact"
- All future phases must use the canonical flow

## 6. No-Go Conditions

- No Telegram polling, inbound commands, remote shell, /run
- No enforcement, shell interception, wrappers, backend invocation
- Canonical report validation failure must not silently pass

---

*Phase 92D.8 establishes the canonical final report artifact contract. 7 new tests (133 total). Future phases must use the canonical flow.*

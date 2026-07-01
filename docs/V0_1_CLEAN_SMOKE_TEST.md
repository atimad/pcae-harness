# PCAE v0.1 — Clean Smoke Test

A minimal, copy-pasteable command sequence to validate that PCAE v0.1 is
installable and functional in a genuinely clean environment. This is the
exact sequence exercised in Phase 106D
(`docs/PHASE_106_PACKAGING_INSTALLATION_CLEAN_SMOKE_TEST.md`); results are
recorded there.

## 1. Create an isolated virtual environment

```bash
tmpdir="$(mktemp -d)"
python -m venv "$tmpdir/venv"
"$tmpdir/venv/bin/python" -m pip install --upgrade pip setuptools wheel
```

## 2. Install PCAE (editable, from a local checkout)

```bash
"$tmpdir/venv/bin/python" -m pip install -e /path/to/pcae-harness
```

Or non-editable, for a smoke test closer to a real install:

```bash
"$tmpdir/venv/bin/python" -m pip install /path/to/pcae-harness
```

## 3. Confirm the console script and command tree resolve

```bash
"$tmpdir/venv/bin/pcae" --help
```

## 4. Run command help checks (no side effects)

```bash
"$tmpdir/venv/bin/pcae" health --help
"$tmpdir/venv/bin/pcae" check --help
"$tmpdir/venv/bin/pcae" doctor task-memory --help
"$tmpdir/venv/bin/pcae" push check --help
"$tmpdir/venv/bin/pcae" phase-report trust --help
"$tmpdir/venv/bin/pcae" phase-report show --help
"$tmpdir/venv/bin/pcae" notify status --help
"$tmpdir/venv/bin/pcae" task finish --help
"$tmpdir/venv/bin/pcae" commit implementation --help
"$tmpdir/venv/bin/pcae" skill invoke --help
```

All of the above must exit 0.

## 5. Confirm clean failure outside a repo (no execution/import crash)

```bash
cd /tmp
"$tmpdir/venv/bin/pcae" health
```

Expected: a clear one-line error ("Error: git command failed: ...
PCAE requires a git repository. Run 'pcae init' first.") and a nonzero
exit code — **not** a Python traceback.

## 6. Run repo-context checks inside a real clone

```bash
git clone /path/to/pcae-harness "$tmpdir/clone"
cd "$tmpdir/clone"
"$tmpdir/venv/bin/pcae" health
"$tmpdir/venv/bin/pcae" check
"$tmpdir/venv/bin/pcae" doctor task-memory
"$tmpdir/venv/bin/pcae" phase-report trust --json
"$tmpdir/venv/bin/pcae" push check
```

All should complete without error (warnings about a missing session
snapshot on a fresh clone are expected and harmless).

## 7. Verify Telegram is safely optional

```bash
unset PCAE_TELEGRAM_BOT_TOKEN PCAE_TELEGRAM_CHAT_ID PCAE_TELEGRAM_ENABLED PCAE_NOTIFY_ENABLED
"$tmpdir/venv/bin/pcae" notify status
```

Expected: reports Telegram as unconfigured/disabled, with a hint on how to
enable it — no crash, no network attempt.

## 8. Verify no execution features are available

```bash
"$tmpdir/venv/bin/pcae" --help | grep -Eo "backend|shell-gate|permission-broker" | head -5
```

These command *families* exist (evidence/classification-only, per
`docs/RELEASE_SCOPE_V0_1.md`'s "Experimental / Internal Commands"), but
none of them invoke a real backend, mediate a shell command, or perform
autonomous execution — confirm this by inspecting their `--help` output
and the no-go confirmations in any recent phase's canonical report
(`.pcae/phase-completion-report.md`), which always state execution is
unavailable and all authorization flags are False.

## 9. Verify report-trust CLI exists and works

```bash
"$tmpdir/venv/bin/pcae" phase-report trust --json
```

Should return a JSON object with `complete`, `status`, `missing_fields`,
`placeholder_fields`, `repair_required` keys.

## 10. Clean up

```bash
rm -rf "$tmpdir"
```

No build artifacts, temp venvs, or clones should be left in the actual
PCAE repository.

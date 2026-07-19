"""Phase 136AW: regression coverage for two crash bugs discovered in
`pcae phase complete`'s own governed finalization path
(`_finalize_report_and_notify`, `src/pcae/commands/phase.py`) while
completing Stage 3's final review.

Both bugs are triggered by the *persisted* shape of
`.pcae/phase-completion-metadata.json` as actually written by every real
prior phase completion (confirmed directly against 136AV's own on-disk
metadata): `files_changed` is a plain int, and
`test_results`/`governance_results` are flat name->value dicts, not the
list-of-`{"name":, "status":}` shapes the reading code assumed. Both
crashed with a bare exception (`TypeError`/`AttributeError`) that
propagated to a nonzero exit code, blocking `pcae phase complete` for
any phase immediately following one whose completion metadata used
these (real, historically-used) shapes.

This module exercises the fixed helper logic directly, independent of
any CLI subprocess invocation.
"""

from __future__ import annotations

from pcae.commands.phase import _finalize_report_and_notify


def test_136aw_int_files_changed_does_not_crash_len(tmp_path, monkeypatch):
    """Reproduces the ``TypeError: object of type 'int' has no len()``
    crash: a persisted metadata file with ``files_changed`` as a plain
    int (not a list) must not raise when read."""
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".pcae").mkdir()
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
        json.dumps({"files_changed": 7, "phase_id": "999Z"})
    )
    # No active task contract / lifecycle context / canonical report in this
    # scratch dir, so identity resolution fails closed -- the call must
    # return False (refuse to finalize), not raise.
    result = _finalize_report_and_notify(
        "regression probe", cli_phase_id="999Z", cli_phase_name="probe"
    )
    assert result is False


def test_136aw_dict_shaped_test_and_governance_results_do_not_crash(tmp_path, monkeypatch):
    """Reproduces the ``AttributeError: 'str' object has no attribute
    'get'`` crash: a persisted metadata file with ``governance_results``/
    ``test_results`` as flat dicts (not a list of {"name":, "status":}
    objects) must not raise when read."""
    import json

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".pcae").mkdir()
    (tmp_path / ".pcae" / "phase-completion-metadata.json").write_text(
        json.dumps(
            {
                "files_changed": 3,
                "governance_results": {"pcae_check": "passed"},
                "test_results": {"fast_green": "4391 passed, 0 failed (passed)"},
                "phase_id": "999Z",
            }
        )
    )
    result = _finalize_report_and_notify(
        "regression probe", cli_phase_id="999Z", cli_phase_name="probe"
    )
    assert result is False

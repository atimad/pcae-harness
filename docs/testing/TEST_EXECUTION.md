# PCAE Test Execution Guide

**Phase 48X.T — Parallel Test Execution Standardization**

---

## Overview

PCAE uses `pytest-xdist` for parallel test execution. The test suite is
parallel-safe: tests share no mutable global state, use no hardcoded ports,
and produce no filesystem side effects that conflict across workers. This
makes parallel execution reliable enough to serve as the standard validation
path for normal development work.

Three execution profiles are defined for different contexts: fast validation,
balanced battery, and release verification. All profiles use the same test
suite and must produce the same pass count. A count mismatch between any
parallel run and the serial baseline is a signal of broken test isolation and
must be resolved before the parallel profile is trusted.

---

## 1. Fast Validation Mode

**Use when:** plugged in, or when execution speed is the priority.

```
python -m pytest -n auto
```

`-n auto` instructs `pytest-xdist` to spawn one worker per available CPU
core, distributing the full test suite across all cores in parallel.

**Current benchmark:**

| Metric | Value |
|---|---|
| Test count | 4201 |
| Wall-clock time | ~90 seconds |
| Approximate speedup | ~4× faster than serial |

This is the **preferred validation path** for all normal phase work. It is
used in the standard pre-commit workflow:

```
pcae health
pcae check
python -m pytest -n auto
```

All three commands must pass before a commit is eligible.

---

## 2. Balanced Battery Mode

**Use when:** on battery power and needing to balance validation speed against
CPU pressure, thermal load, and battery consumption.

With four workers:

```
python -m pytest -n 4
```

With six workers:

```
python -m pytest -n 6
```

**Characteristics:**

- Lower CPU utilization than `-n auto` on machines with many cores
- Reduced fan activity and thermal load during extended work sessions
- Meaningfully improved battery life compared to full parallel execution
- Still substantially faster than serial execution
- No reduction in test coverage or reliability

Choose `-n 4` for the most conservative battery impact. Choose `-n 6` for a
balance between speed and thermals on machines with 8–12 cores. Both produce
the same test count as serial and fast validation modes.

The battery-mode workflow:

```
pcae health
pcae check
python -m pytest -n 4
```

---

## 3. Release Verification Mode

**Use when:** preparing for a major release, a milestone commit, or any
situation where conservative confidence matters more than execution speed.

```
python -m pytest
```

Serial execution with no parallelism.

**Characteristics:**

- Establishes the authoritative serial baseline
- Detects hidden order assumptions that parallel execution may mask
- Detects any test that relies on side effects left by an earlier test
- Slower than parallel profiles, but provides the highest confidence that
  the test suite is genuinely isolation-complete
- The result (pass count and timing) serves as the reference against which
  parallel profile results are validated

The release verification workflow:

```
pcae health
pcae check
python -m pytest
```

Run this profile before major milestones, before marking a phase complete in
a release context, and whenever the serial baseline has not been verified
recently.

---

## 4. Slow Test Discovery

To identify which tests are consuming the most time, use `--durations` to
surface the 25 slowest tests:

```
python -m pytest --durations=25
```

This can be combined with parallel execution for faster discovery:

```
python -m pytest -n auto --durations=25
```

Use slow test discovery when:

- A parallel run is significantly slower than the benchmark
- You suspect a test is performing unnecessarily expensive setup
- You are optimizing the suite before a CI configuration change

The `--durations` output reports wall-clock time per test, sorted
slowest-first. Tests that consistently appear in the top 25 are candidates
for profiling and optimization.

---

## 5. Recommended Workflow

**Standard phase validation** (plugged in, normal development):

```
pcae health
pcae check
python -m pytest -n auto
```

Run after every non-trivial change. All three commands must pass.

**Battery-conscious validation** (on battery, extended session):

```
pcae health
pcae check
python -m pytest -n 4
```

Use when thermal or battery constraints make full parallel execution
impractical. `-n 6` is an alternative if slightly more speed is needed.

**Release verification** (before milestone commits or major releases):

```
pcae health
pcae check
python -m pytest
```

Use before marking a phase complete, before pushing a release branch, and
whenever the serial baseline needs to be refreshed.

**Summary:**

| Profile | Command | When to use |
|---|---|---|
| Fast validation | `python -m pytest -n auto` | Normal development, plugged in |
| Balanced battery | `python -m pytest -n 4` | On battery, extended sessions |
| Release verification | `python -m pytest` | Before releases, milestone commits |
| Slow test discovery | `python -m pytest --durations=25` | Performance investigation |

---

## 6. Safety Notes

**Parallel execution is safe because serial and parallel counts match.**
`pytest-xdist` safety depends entirely on test isolation. For PCAE, repeated
parallel runs have matched the serial test count. This is the operational
evidence that the suite is parallel-safe. If a future change causes a count
mismatch between any parallel run and the serial baseline, that mismatch is
a test isolation failure and must be fixed before parallel profiles are used
for validation.

**Test count is the integrity signal.** The current reference count is 4201
tests. If `python -m pytest -n auto` reports a different count than
`python -m pytest`, investigate immediately. Do not accept a parallel result
with a different test count as valid.

**Flaky or shared-state tests break parallel safety.** Any test that relies
on global mutable state, filesystem side effects shared with other tests, or
execution order must be fixed before parallel execution can be trusted. The
presence of a single flaky or order-dependent test invalidates the parallel
profile for the entire suite.

**Serial remains the final conservative baseline.** Fast validation mode is
the day-to-day standard, but `python -m pytest` (serial) is the ground truth.
When parallel and serial results disagree, serial is authoritative. When in
doubt about a test failure seen only in parallel mode, reproduce it serially
before investigating further.

**Worker count affects reproducibility.** `-n auto` will use a different
worker count on different machines. If a test passes on a developer machine
with 8 cores but fails in CI with 4 cores, the failure may be an isolation
issue exposed by a different scheduling pattern. Always reproduce serial
before concluding it is a genuine test failure.

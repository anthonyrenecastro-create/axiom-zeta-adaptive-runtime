# Validation of this delivery

## Executed

Version 0.2 verifies the generalized governing architecture, with weather disabled by default.

- `node --test governance/tests/*.test.mjs`: **11 tests passed**.

- `python -m unittest discover -s tests -v`: **14 tests passed**.
- Generalized governing TypeScript modules regenerated with `node governance/build.mjs`. Original weather-domain JavaScript regenerated with `node weather_bridge/build.mjs`; bridge executed during tests and full simulation.
- Dashboard HTTP smoke: health, HTML delivery, inline JavaScript syntax, simulated stepping, external telemetry ingestion, current state, ledger retrieval, reset, history, weather toggle, modeled-domain planning, and outcome feedback passed.
- `python -m az_runtime demo --output examples/reference-run`: 96 supervisory cycles over 24 simulated hours, optimized and baseline policies on identical synthetic disturbances.

## Reference result

| Measure | Baseline | Optimized |
|---|---:|---:|
| Electrical energy | 57.6463 kWh | 47.9163 kWh |
| Modeled operating cost | $9.0929 | $7.4834 |
| Absolute deviation from 23 °C, integrated | 20.8079 °C·h | 48.7692 °C·h |
| Pump time completed | 2 h | 2 h |
| Deadline missed | No | No |
| Tested physical constraint violations | 0 | 0 |
| Adaptive supervisory cycles | 0 | 69 |

Both policies execute **96 successful governance cycles with weather off and no governance errors**.

Energy reduction: **16.8787%**. Cost reduction: **17.7005%**. Optimized servers may operate at 80% performance and cooling at a higher allowed temperature; these are service tradeoffs. This synthetic comparison is not evidence of real-world savings or of weather coupling's isolated benefit. No component ablation or field trial has been performed.

## Covered faults and invariants

Sequence replay, lease expiry, capability bounds, raw thermal bounds, stale and non-finite telemetry, full local cooling power reservation, PID anti-windup, absence of derivative setpoint kick, drift breaker latching and baseline reset, per-device state isolation, seeded field reproducibility, external telemetry ordering, forecast failure fallback, full-day service constraints, compute-only participation, zero-budget policy fallback, recursive snapshot immutability, simultaneous domains without weather, objective-dependent action selection, observed-outcome credit, deterministic state restore, invalid action bounds, and corrected structural transport accounting.

## Not executed

Original PhaseLock Rust extension compilation or native mode, upstream vendor test suites, the upstream drone C++ build, aircraft control, actual smart-plug switching, real weather ingestion, distributed network recovery, hardware-in-the-loop trials, visual browser rendering checks, and formal stability/certification verification. The included CI workflow exercises the new prototype on Python 3.12 and Node 24; that workflow has not yet run on GitHub.

Reference ledgers store full alternatives and measured interval outcomes. They can be reproduced using the command above. Local test logs are included in `examples/reference-run/test-results.txt`.

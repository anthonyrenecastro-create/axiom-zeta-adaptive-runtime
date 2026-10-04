# Axiom Zeta Adaptive Systems Runtime · 0.2

**The Weather Oracle's cognitive world-model architecture now governs the framework. Weather is optional context, disabled by default.**

The governing engine reuses and generalizes the oracle's real TypeScript modules: common immutable snapshots, nine independent mechanisms, cognitive routing, reputation, singular-commit arbitration, structural state transport, safety constitution, consequence evaluation, four-layer memory, contextual retrieval, and runtime health. Domain mechanisms propose bounded actions; the governor selects them; an independent physical gate and local controllers retain execution authority.

The green and goldenrod glass dashboard exposes domain twins, resource trajectories, mechanism decisions, memory, health, and authoritative state hashes.

## Run

Python 3.10+ and Node.js 24+. No additional packages needed for the default backend. From the extracted repository root:

```bash
python -m az_runtime demo
python -m az_runtime serve
```

Open **http://127.0.0.1:8080**. Weather context is off initially. The dashboard checkbox enables or disables the synthetic weather context without resetting governance.

```bash
python -m az_runtime demo --weather
python -m az_runtime demo --config examples/building.json
python -m az_runtime demo --fault-step 35
python -m examples.govern_any_domain
python -m unittest discover -s tests -v
node --test governance/tests/*.test.mjs
```

The normal demo compares optimized and conservative policies over 24 synthetic hours. It writes summary and full decision/outcome ledgers to `outputs/`. Local controllers simulate one-minute updates; supervision commits every fifteen simulated minutes.

## What changed from 0.1

| Before | Now |
|---|---|
| Weather coupling fed a separate Python optimizer | The generalized oracle engine selects the modeled domain actions |
| Weather required for forecasts | Independent domain forecasting works with weather absent |
| One cooling/server/pump trio required | Any collection of the modeled cooling, compute, and deferrable kinds can participate |
| Simple weighted minimum selected actions | Routed objective mechanisms vote through reputation-scaled arbitration |
| Flat decision log | Core commit ledger, observed consequence/credit, four-layer memory, full state hashes |
| Dark blue dashboard | Green/goldenrod glass dashboard with four navigable views |

## Governing architecture

1. Domain models supply normalized observations, physical action bounds, competing predicted options, and objective weights.
2. The shared world state includes topology, fields, uncertainty, stress, goals, resources, memory, and registered domains.
3. Independent mechanisms receive a recursively frozen common snapshot and propose changes without mutation.
4. Routing and a hard compute budget select executable proposals. Critique/policy can veto actions.
5. Reputation scales contribution weights. The oracle's arbitrator commits one authoritative substrate transition; domain arbitration selects a single complete action plan per domain rather than averaging actuator targets.
6. Safety constitution protects the cognitive state. The separate physical `SafetyEnvelope` checks raw device telemetry and power reservations before simulation commands are dispatched.
7. Actual observations feed consequence evaluation, contributor credit, reputation, memory consolidation, and per-domain prediction-error experience for subsequent confidence.

See [architecture](docs/ARCHITECTURE.md) and [source integration](docs/INTEGRATION.md) for exact reuse and adaptations.

## Any connected domain: what that means

The **governor is domain-neutral**, not a universal pretrained physical model. A new domain supplies its own observations, dynamics/predictions, candidate actions, objectives, and constraints. No weather class or hurricane state is required. `examples/govern_any_domain.py` demonstrates simultaneous compute and logistics governance using illustrative predictions.

The included facility model supports arbitrary combinations of cooling, compute, and deferrable endpoints. Its candidate simulator is a modeling provider; it no longer chooses the authoritative action. Candidate generation is capped at 64 alternatives per domain, and the shared engine accepts up to 16 domains / 100 observation nodes. These are prototype limits, not scale benchmarks.

External domains can use `POST /api/govern` and report outcomes to `POST /api/outcome`. These APIs are **shadow mode**: no physical command is emitted. The simpler `POST /api/telemetry` path supplies drift monitoring only; raw telemetry alone is not enough to model an unfamiliar device.

## Optional weather

`az_runtime/context.py` supplies the demo's synthetic environmental/tariff boundary forecast. `--weather` or the dashboard checkbox selects the preserved Weather Oracle coupling functions as an extra synthetic environmental influence. Turning weather off removes that dependency from domain decision inputs while keeping the generalized cognitive engine running.

Weather fixtures and heuristic formulas are not validated live meteorological predictions. Neither interface presents upstream fixture alerts as official live warnings.

## Original PhaseLock backend

PhaseLock risk policy is directly reused. Default `fallback` is an explicit statistical drift backend. The original Rust HRM extension is selectable after building it:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install maturin
cd vendor/phase-lock/rust
maturin develop --release
cd ../../..
python -m az_runtime demo --backend native
```

Native mode does not silently fall back. Its compilation was not verified in this environment. Physical watts and temperatures remain separate from its dimensionless field outputs.

## Status

Working prototype, simulated devices, HTTP telemetry shadow mode, and domain-governance API. Original aircraft MPC/SE(3) paths do not execute. Actual hardware protocols, authenticated network deployment, verified live weather skill, and hardware-in-the-loop qualification remain future integration work.

Savings in the reference simulation reflect allowed comfort/throughput tradeoffs. Substrate health and confidence values are heuristics, not calibrated probabilities or proof of stability. See [validation](docs/VALIDATION.md).

## Source and licensing

Original uploaded sources remain in `vendor/`. Generated and adapted governing sources are in `governance/src/core` and `governance/dist/core`; rebuild with `node governance/build.mjs`. The new orchestration shell is `governance/governor.mjs`.

The supplied drone source includes GPLv2; new integration code derived from it uses GPLv2. Vendor notices and unspecified source terms remain applicable. See `LICENSE` and `NOTICE.md` before redistribution.

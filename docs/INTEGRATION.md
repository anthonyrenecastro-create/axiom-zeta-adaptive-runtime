# Integration provenance

This repository is a new composition of the three supplied source archives. Source copies are preserved under `vendor/`. AI Change Radar was not used: the weather upload supplies the actual domain-coupling implementation.

| Uploaded archive | SHA-256 |
|---|---|
| drone-controller-axiom-zeta-main.zip | `161b3346aae49f89677d05abc86b4394d819e0aed838686b40ab75bacd2949e7` |
| phase-lock-developer-fixed(1).zip | `dc228717ca35153862068ed11fbc551f113ed74b588c1cdbf40dafc65ef42aa1` |
| thoth-wheather-oracle (1).zip | `894a2809b8e48502f09928853fe3466eef754cfbcaa943c477d18af03f22dc4a` |

## Active reuse in version 0.2

`governance/build.mjs` reproducibly creates adapted TypeScript sources and bundled JavaScript from the uploaded oracle's `state`, `mechanisms`, `arbitrator`, `routing`, `reputation`, `memory`, `consequence`, `transport`, `safety`, `health`, `retrieval`, and `benchmarks` modules. The active `governance/governor.mjs` uses them to govern generic domains. It replaces the old weather/AI/React-specific runtime shell and removes hardwired Gemini mechanisms from the default registry.

Adaptations include recursively frozen snapshots; neutral domain initialization; deterministic memory/event identifiers; bounded memory trimming; structural conservation accounting measured after intentional field proposals; deferred credit assignment until measured outcomes; full-state hashes; actual compute-budget enforcement; and separate domain action arbitration. Original source snapshots remain untouched in `vendor/`.

The active core retains diffusion, prediction correction, stress regulation, sensor fusion, memory proposals, damage repair, geometry adaptation, resource proposals, and curiosity. Domain objective mechanisms coexist with that substrate and govern complete bounded action plans. Consequence-based reputation and domain experience affect subsequent proposal confidence.

PhaseLock policy and optional original Rust extension remain as described in version 0.1. The default fallback is explicitly statistical, not a reimplementation of the Rust topology engine. The seeded Python drone supervisory field port and improved local cooling PID remain active.

Weather coupling functions still execute when enabled, but are no longer the governing engine or a required context dependency. The generic compute/logistics example and governance tests have no weather state. Upstream fixture forecasts and LIVE strings remain reference data, not live operational claims.

The default demo exercises the generalized engine and the Python modeled facility integration. Vendor React/Gemini routes, original aircraft controllers, real hardware protocols, and native Rust compilation are outside the verified execution path.

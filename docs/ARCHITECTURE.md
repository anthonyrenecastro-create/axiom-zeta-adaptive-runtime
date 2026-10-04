# Domain-neutral world governance

## Active engine

`governance/governor.mjs` orchestrates the oracle's adapted TypeScript modules. Python serializes the authoritative state, reputation store, and pending plan between Node invocations. The HTTP process keeps these sessions in memory. Restart persistence is not implemented.

The original `runtime.ts` was a weather/AI-dashboard-specific shell with asynchronous observation adapters and Gemini routes. Its domain-specific scheduling is replaced; its core modeling and mechanism architecture now executes for every governed domain.

The core substrate runs even when adaptive device actions are vetoed. This lets conservative operation continue to collect state and memory. A baseline comparison also runs the substrate while using local conservative targets.

## Models and mechanisms

`DomainRegistry` registers models exposing a common interface. `FacilityDomain` supplies counterfactual plant forecasts from the existing Python simulator. Its candidate generator enumerates bounded combinations; it does not select the committed action.

Every positive objective weight creates an independent `DomainObjectiveMechanism`. Each receives the same recursively frozen world snapshot, compares feasible candidate metrics, proposes its preferred alternative and predicted observations, and declares compute cost. The router includes domain mechanisms alongside nine oracle substrate mechanisms. A separate budget enforcer caps actual proposal cost.

The oracle arbitrator scales proposal confidence and activation by reputation, rejects vetoed contributions, integrates substrate field changes, transports state through structural events, and evaluates the cognitive safety constitution. A domain plan is selected only from accepted objective mechanisms and feasible options. Its score is the sum of objective weight × accepted contribution weight × predicted objective cost. Complete targets are selected together, never blended.

## Authority and feedback

The governor's action is a recommendation until the Python physical gate accepts it. That gate checks finite/current raw telemetry, device target bounds, service floors, and full local cooling power reservation. Local PID/watchdog logic realizes the approved simulation target.

The observed outcome is a distinct transaction. It maps actual normalized observations back into the shared state, evaluates prediction error, assigns contributor credit/blame, updates reputation, consolidates working/episodic/semantic/procedural memory, and stores per-domain prediction-error experience. That experience moderates future domain mechanism confidence; it is a lightweight calibration heuristic, not learned dynamics.

Commit and outcome hashes cover the complete authoritative state using SHA-256, including domains and memory. Commit records retain the prior authoritative hash plus a separate observation-frame hash. This is audit identification, not an externally anchored or signed tamper-proof ledger.

## Optional context

Context is separate from domain state and the governing engine. The facility model needs environmental/tariff boundary forecasts for its own dynamics, but these do not require the hurricane oracle. Optional weather coupling modifies synthetic disturbance forecasts. Compute/logistics examples require no weather state at all.

## Generalization boundaries

Unknown devices cannot be safely optimized from identity alone. They need a model, operating bounds, telemetry normalization, candidate predictions, an independent constraint implementation, and a local controller. The generic API trusts the domain model's feasibility claims and validates declared bounds; it is therefore shadow-only. The facility integration independently rechecks physical telemetry.

Topology changes requested by substrate mechanisms remain cognitive structure changes, not device enrollment or actuator creation. Changing the external registered observation schema requires a new governor session. Physical device addition/removal is not silently inferred from a structural split.

The prototype supports up to 16 domains, 100 observation nodes, 64 alternatives per domain, 12 objectives per domain, and a bounded per-cycle compute budget. It has no hard-real-time guarantee or formal stability proof.

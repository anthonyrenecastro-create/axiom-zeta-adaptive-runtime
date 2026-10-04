# Domain and device contracts

## Modeled domains

A domain request contains:

```json
{
  "domains": [{
    "id": "compute",
    "observations": {"load": 0.5},
    "bounds": {"cpu_cap": {"min": 0.6, "max": 1}},
    "objectives": {"energy": 1, "service_loss": 2},
    "candidates": [{
      "id": "eco", "feasible": true,
      "targets": {"cpu_cap": 0.8},
      "metrics": {"energy": 0.7, "service_loss": 0.1},
      "predicted_observations": {"load": 0.6}
    }]
  }]
}
```

Observations are normalized to [0,1]. Bounds and targets can use a domain's physical units. Predicted metrics are finite, nonnegative costs: lower is better. Weights set relative importance and must account for unit scales. Predictions should use a consistent next-observation horizon; the facility provider supplies next-interval normalized observations and longer-horizon resource costs.

Provide stable domain, observation, actuator, and candidate IDs. All candidates declare complete targets and a feasibility boolean. The model must evaluate its own physical constraints before setting feasibility. The generic API also validates declared bounds; it does not verify the accuracy of submitted predictions.

The same API can carry compute, logistics, water, energy, or other modeled domains. No weather-specific objects are required. `python -m examples.govern_any_domain` is a runnable two-domain example with illustrative model predictions.

After `/api/govern`, report the actual outcome before requesting the next decision:

```json
{"observations":{"compute.load":0.58},"committed":true,"progress":0.2}
```

An observation must be supplied for each registered node. `committed` describes whether the domain's external execution actually occurred; it does not cause the service to operate hardware. Reset the external governor before changing the observation schema.

## Physical adapters

`DeviceAdapter` still exposes capabilities, telemetry, leased command application, and local ticking/controller ownership. `SimulatedDevice` implements cooling, compute, and deferrable loads. The current facility runtime accepts any collection of these modeled kinds, with arbitrary valid IDs and independent power limits.

A new device kind needs its own simulator/predictor, option generation, telemetry normalization, independent physical constraint checks, safe local default, and hardware commissioning. A new `DomainModel` can be registered through `DomainRegistry` to reuse the governing engine without extending the facility model.

## HTTP API

| Endpoint | Function |
|---|---|
| `GET /health` | Local process health |
| `GET /api/state` | Summary, latest decision, last 32 energy intervals, external shadow devices |
| `GET /api/ledger` | Full simulated decision and outcome history |
| `POST /api/step` | `{ "steps": 1 }`, range 1–24 |
| `POST /api/reset` | Reset facility simulation |
| `POST /api/context` | `{ "weather_enabled": true }`; changes optional context without resetting governor |
| `POST /api/telemetry` | External telemetry drift monitoring only |
| `POST /api/govern` | Modeled domain request; shadow action recommendation |
| `POST /api/outcome` | Actual normalized observations, execution status, optional goal progress |
| `POST /api/govern/reset` | Reset external modeled-domain session |

The server binds to loopback. External telemetry requires finite watts, rated power, a timestamp within 120 wall-clock seconds, and strictly ordered observations. `examples/send_telemetry.py` demonstrates it. This path is separate from the simulated facility clock and does not create physical commands.

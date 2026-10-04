# Ablation Study Guide

## Overview
Complete ablation study capabilities have been added to compare different model configurations and identify which components contribute to performance.

## Features Added

### 1. Baseline Models (`utils/ablation_models.py`)
Four model types available for comparison:

- **Full Quadra-Matrix** - Complete system with SNNs, quantum fields, and all features
- **Simple MLP** - Basic multi-layer perceptron baseline
- **Tabular Q-Learner** - Classical reinforcement learning with discretized states
- **MLP Q-Learner** - Deep Q-Network style learner (middle ground)

### 2. Ablation Controls

#### Noise Injection (On/Off)
- **Purpose**: Test model robustness
- **Control**: Checkbox in GUI + intensity slider (0-100%)
- **Effect**: Adds 7 types of noise (Gaussian, Dropout, etc.) at 3 injection points

#### Weight Plasticity (On/Frozen)
- **Purpose**: Test importance of weight updates during inference
- **Control**: Checkbox in "Ablation Study" panel
- **Effect**:
  - ON: Weights update normally during training
  - FROZEN: All parameters set to `requires_grad=False`

#### Field Feedback (Enabled/Disabled)
- **Purpose**: Isolate quantum field contribution
- **Control**: Checkbox in "Ablation Study" panel
- **Effect**:
  - ENABLED: Normal quantum field feedback
  - DISABLED: Random field updates (bypasses quantum effects)

#### Model Type Selection
- **Purpose**: Compare against simpler baselines
- **Control**: Dropdown menu with 4 options
- **Effect**: Switches between full system and baseline models

## GUI Controls

### Location
Two control panels on the dashboard:

1. **🔊 Noise Injection** (existing)
   - Enable Noise checkbox
   - Intensity slider (0-100%)
   - Real-time stats display

2. **🔬 Ablation Study** (new)
   - Model Type dropdown
   - Weight Plasticity checkbox
   - Field Feedback checkbox
   - Configuration status display

### Usage Workflow

```
1. Open dashboard: http://127.0.0.1:5000
2. Initialize System
3. Configure ablation settings:
   - Select model type
   - Toggle plasticity
   - Toggle field feedback
   - Enable/adjust noise if desired
4. Start Training
5. Observe metrics differences
6. Stop, reconfigure, restart to compare
```

## API Endpoints

### Get Current Configuration
```bash
curl http://localhost:5000/api/ablation/config
```

Returns:
```json
{
  "noise_enabled": false,
  "plasticity_enabled": true,
  "field_feedback_enabled": true,
  "model_type": "full"
}
```

### Set Configuration
```bash
curl -X POST http://localhost:5000/api/ablation/config \
  -H "Content-Type: application/json" \
  -d '{
    "model_type": "mlp",
    "plasticity_enabled": false,
    "field_feedback_enabled": false,
    "noise_enabled": true
  }'
```

### Compare Configurations
```bash
curl -X POST http://localhost:5000/api/ablation/compare \
  -H "Content-Type: application/json" \
  -d '{
    "configs": [
      {"model_type": "full", "plasticity_enabled": true},
      {"model_type": "full", "plasticity_enabled": false},
      {"model_type": "mlp", "plasticity_enabled": true}
    ]
  }'
```

## Example Ablation Studies

### Study 1: Component Contribution
Test each feature's contribution by removing one at a time:

1. **Baseline**: Full system (all enabled)
2. **No Field Feedback**: Disable quantum fields only
3. **No Plasticity**: Freeze weights only
4. **No Noise Robustness**: Disable noise (or test with/without)
5. **Simple Baseline**: Use MLP to see total benefit

### Study 2: Robustness Testing
Test system resilience:

1. **Clean**: Noise OFF, all features ON
2. **Light Noise**: Noise intensity 0.25
3. **Medium Noise**: Noise intensity 0.50
4. **Heavy Noise**: Noise intensity 0.75
5. **Frozen + Noise**: Test with frozen weights

### Study 3: Model Comparison
Compare architectural choices:

1. **Full Quadra-Matrix**: All features
2. **MLP Q-Learner**: Neural network baseline
3. **Tabular Q-Learner**: Classical RL
4. **Simple MLP**: Simplest baseline

## Socket Events

### Emitted by Client
- `toggle_plasticity` - Enable/disable weight updates
- `toggle_field_feedback` - Enable/disable quantum fields
- `set_model_type` - Switch model architecture
- `get_ablation_status` - Request current config

### Emitted by Server
- `ablation_status` - Current configuration
- `metrics_update` - Includes ablation_config field

## Metrics Tracking

All metrics include ablation configuration:
```javascript
{
  "iteration": 45,
  "loss": 0.234,
  "reward": 9.5,
  "ablation_config": {
    "model_type": "full",
    "noise_enabled": true,
    "plasticity_enabled": true,
    "field_feedback_enabled": false
  }
}
```

## Implementation Details

### Training Loop Modifications
1. **Plasticity Control**: Sets `requires_grad` on all parameters before each iteration
2. **Field Feedback Control**: Replaces field updates with random noise when disabled
3. **Model Switching**: Uses baseline models when selected (future: full integration)

### Files Modified
- `app.py` - Added ablation handlers and training loop controls
- `templates/dashboard.html` - Added GUI controls and JavaScript
- `utils/ablation_models.py` - New file with baseline models

## Best Practices

### Running Studies
1. **Isolate Variables**: Change one thing at a time
2. **Multiple Runs**: Run each configuration 3-5 times
3. **Consistent Duration**: Use same number of iterations
4. **Record Results**: Save metrics after each run
5. **Statistical Significance**: Calculate mean/std across runs

### Interpreting Results
- **Loss Reduction**: Lower is better
- **Reward Increase**: Higher is better (target: 10+)
- **Variance**: Stable variance indicates robust learning
- **Convergence Speed**: Iterations to reach performance threshold

## Future Enhancements
- Automatic A/B testing mode
- Results comparison visualization
- Statistical significance testing
- Automated reporting
- Configuration presets
- Batch experiment runner

## Quick Reference

| Setting | Purpose | Effect on Performance |
|---------|---------|----------------------|
| Noise OFF → ON | Test robustness | Usually decreases short-term performance |
| Plasticity ON → FROZEN | Test weight updates | Performance plateaus when frozen |
| Field Feedback ON → OFF | Isolate quantum contribution | May reduce performance significantly |
| Full → MLP | Compare complexity | Baseline for improvement measurement |

## Troubleshooting

### Controls Not Appearing
- Refresh browser page
- Check Flask is running: http://127.0.0.1:5000
- Verify ABLATION_AVAILABLE in console

### Changes Not Taking Effect
- Stop training before changing settings
- Some changes (like model type) may require re-initialization
- Check ablation_status display for confirmation

### Performance Degradation
- This is expected when disabling features!
- Plasticity frozen = no learning after that point
- Field feedback off = loses quantum advantages
- High noise = intentional difficulty increase

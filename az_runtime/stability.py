"""PhaseLock policy reuse + explicit native/fallback drift backends.
Physical units are never replaced by PhaseLock's dimensionless output vector.
"""
import importlib.util
import math
import statistics
from collections import deque
from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'vendor/phase-lock/gateway/core/policy.py'
spec = importlib.util.spec_from_file_location('az_phase_policy', p)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

class StabilityMonitor:
    def __init__(self, backend='fallback', baseline_windows=5):
        self.backend = backend
        self.baseline_windows = baseline_windows
        self.states = {}
        if backend == 'native':
            from phase_lock_core import DriftEngine
            self.engine_type = DriftEngine
        elif backend != 'fallback':
            raise ValueError('backend must be fallback or native')

    def assess(self, device_id, metric_window):
        if len(metric_window) < 24 or any(not math.isfinite(x) for x in metric_window):
            return {'ready': False, 'risk': 'red', 'breaker_open': True,
                    'backend': self.backend, 'score': 1.0, 'reason': 'invalid metric window'}
        state = self.states.setdefault(device_id, {'windows': [], 'baseline': None,
                                                    'streak': 0, 'latched': False})
        if self.backend == 'native':
            if 'engine' not in state:
                state['engine'] = self.engine_type(18,18,10,42,self.baseline_windows)
            out = state['engine'].stabilize(metric_window, None)
            score, ready = float(out['drift_score']), bool(out['baseline_ready'])
        else:
            # Frozen reference: no ongoing assimilation of anomalous windows.
            if state['baseline'] is None:
                state['windows'].append(list(metric_window))
                if len(state['windows']) >= self.baseline_windows:
                    values = [v for w in state['windows'] for v in w]
                    state['baseline'] = (statistics.mean(values), statistics.pstdev(values))
                    state['windows'].clear()
                score, ready = 0.0, state['baseline'] is not None
            else:
                mean, std = state['baseline']
                scale = max(abs(mean)*0.10, std, 0.01)
                shift = abs(statistics.mean(metric_window)-mean)/scale
                spread = abs(statistics.pstdev(metric_window)-std)/scale
                score, ready = min(1.0, 0.15*shift + 0.10*spread), True
        if not math.isfinite(score):
            score = 1.0
        state['streak'] = state['streak']+1 if score >= 0.45 else 0
        state['latched'] |= state['streak'] >= 3
        risk = policy.classify_risk(score)
        return {'ready': ready, 'risk': risk, 'score': score,
                'breaker_open': state['latched'], 'backend': self.backend,
                'actions': policy.enforce_circuit_breaker(policy.actions_for_risk(risk),state['latched'])}

    def reset(self, device_id):
        self.states.pop(device_id, None)

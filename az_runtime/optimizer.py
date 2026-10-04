"""Enumerated short-horizon search, not a QP MPC or a learned world model."""
import copy
import itertools
import math
from .safety import SafetyEnvelope

class Optimizer:
    def __init__(self,weights=None):
        self.weights=weights or {'energy':1.0,'cost':2.0,'comfort':0.025,'wear':0.03,'performance':1.0}
        if set(self.weights)!={'energy','cost','comfort','wear','performance'} or any(not math.isfinite(v) or v<0 for v in self.weights.values()):
            raise ValueError('invalid objective weights')

    def evaluate(self,devices,targets,forecast,now_s,gate):
        errors=gate.validate(devices,targets,now_s)
        clones=copy.deepcopy(devices)
        if errors:return {'targets':targets,'feasible':False,'rejected':errors,'score':None}
        result=gate.dispatch(clones,targets,now_s,10**9)
        if not result['committed']: return {'targets':targets,'feasible':False,'rejected':result['errors'],'score':None}
        energy,cost,comfort,performance=0.0,0.0,0.0,0.0
        first_interval_observations={}
        for i,point in enumerate(forecast['points']):
            # Renew constant hypothetical target; simulate local control at one-minute intervals.
            gate.dispatch(clones,targets,now_s+i*900,10**9+i+1)
            for minute in range(15):
                for key,d in clones.items():
                    # Conservative upper-temperature forecast; no future observations used.
                    d.tick(1/60,point['ambient_c']+point['uncertainty_c'],now_s+i*900+minute*60)
                    t=d.read();c=d.capabilities
                    energy+=t.power_w/1000/60
                    cost+=t.power_w/1000/60*point['price_per_kwh']
                    if c.kind=='cooling':
                        if not c.min_temperature_c<=t.temperature_c<=c.max_temperature_c:
                            errors.append(key+': forecast temperature constraint')
                        comfort+=(t.temperature_c-23)**2/60
                    if c.kind=='compute':performance+=(1-t.performance)/60
            if i==0:
                first_interval_observations={k:max(0,min(1,(d.read().temperature_c-d.capabilities.min_temperature_c)/(d.capabilities.max_temperature_c-d.capabilities.min_temperature_c))) if d.capabilities.kind=='cooling' else max(0,min(1,d.read().power_w/d.capabilities.max_power_w)) for k,d in clones.items()}
        wear=sum(abs(targets[k]-d.last_target) if d.last_target is not None else 0 for k,d in devices.items())
        w=self.weights
        score=w['energy']*energy+w['cost']*cost+w['comfort']*comfort+w['wear']*wear+w['performance']*performance
        return {'targets':targets,'feasible':not errors,'rejected':sorted(set(errors)),
                'score':score,'predicted_energy_kwh':energy,'predicted_cost':cost,
                'horizon_h':len(forecast['points'])*0.25,
                'metrics':{'energy':energy,'cost':cost,'comfort':comfort,'wear':wear,'performance':performance},
                'predicted_observations':first_interval_observations}

    def enumerate(self,devices,forecast,now_s,gate,pump_required):
        keys=list(devices)
        options=[]
        for device in devices.values():
            c=device.capabilities
            if c.kind=='cooling':options.append(sorted(set(max(c.min_temperature_c,min(c.max_temperature_c,x)) for x in [23,24,25])))
            elif c.kind=='compute':options.append([max(c.min_performance,0.8),1.0])
            else:options.append([1] if (pump_required.get(c.device_id,False) if isinstance(pump_required,dict) else pump_required) else [0,1])
        candidates=[self.evaluate(devices,dict(zip(keys,choice)),forecast,now_s,gate)
                    for choice in itertools.islice(itertools.product(*options),64)]
        return candidates

    def propose(self,devices,forecast,now_s,gate,pump_required):
        candidates=self.enumerate(devices,forecast,now_s,gate,pump_required)
        feasible=[x for x in candidates if x['feasible']]
        best=min(feasible,key=lambda x:x['score']) if feasible else None
        return best,candidates

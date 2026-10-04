"""Domain registration contract: models expose observations, bounded options and objectives.
The governor never assumes that the underlying domain is weather or a building.
"""
from typing import Protocol
import math

class DomainModel(Protocol):
    domain_id: str
    def model(self,devices,context,now_s,gate,required) -> tuple[dict,list]: ...

class DomainRegistry:
    def __init__(self):self.models={}
    def register(self,model):
        if not model.domain_id or model.domain_id in self.models:raise ValueError('duplicate/empty domain ID')
        self.models[model.domain_id]=model
    def model(self,**kwargs):
        domains=[];candidates={}
        for key,model in self.models.items():
            domain,raw=model.model(**kwargs);domains.append(domain);candidates[key]=raw
        return domains,candidates

def normalized_observations(devices):
    out={}
    for key,d in devices.items():
        t=d.read();c=d.capabilities
        # Missing/invalid telemetry is encoded as conservative stress by the caller;
        # raw physical checks still happen independently in SafetyEnvelope.
        if c.kind=='cooling':x=(t.temperature_c-c.min_temperature_c)/(c.max_temperature_c-c.min_temperature_c)
        else:x=t.power_w/c.max_power_w
        out[key]=max(0,min(1,x)) if math.isfinite(x) else 1.0
    return out

class FacilityDomain:
    domain_id='facility'
    def __init__(self,optimizer):self.optimizer=optimizer
    def model(self,devices,context,now_s,gate,required):
        raw=self.optimizer.enumerate(devices,context,now_s,gate,required)
        bounds={k:{'min':d.capabilities.min_temperature_c,'max':d.capabilities.max_temperature_c}
                if d.capabilities.kind=='cooling' else {'min':d.capabilities.min_performance,'max':1}
                if d.capabilities.kind=='compute' else {'min':0,'max':1} for k,d in devices.items()}
        candidates=[]
        for i,c in enumerate(raw):
            metrics=c.get('metrics',{key:0 for key in self.optimizer.weights})
            candidates.append({'id':f'option_{i:03d}','targets':c['targets'],'feasible':c['feasible'],
                               'metrics':metrics,'predicted_observations':c.get('predicted_observations',{})})
        return {'id':self.domain_id,'observations':normalized_observations(devices),'bounds':bounds,
                'objectives':self.optimizer.weights,'candidates':candidates},raw

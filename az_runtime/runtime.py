"""Observe → stabilize → forecast → propose → gate → commit → measure."""
import json
import math
from pathlib import Path
from collections import deque
from .devices import Capabilities, DeviceRegistry, SimulatedDevice
from .stability import StabilityMonitor
from .supervisor import AdaptiveField
from .weather import WeatherOracle
from .context import EnvironmentContext
from .governance import GovernanceBridge
from .domains import DomainRegistry,FacilityDomain,normalized_observations
from .optimizer import Optimizer
from .safety import SafetyEnvelope

DEFAULT_CONFIG={
 'max_site_power_w':6500,'pump_required_h':2,'pump_deadline_h':22,
 'devices':[{'device_id':'hvac','kind':'cooling','max_power_w':4000},
            {'device_id':'server','kind':'compute','max_power_w':1200,'min_performance':0.8},
            {'device_id':'pump','kind':'deferrable','max_power_w':1000}]}

class Runtime:
    def __init__(self,config=None,backend='fallback',mode='optimized',weather_enabled=False):
        self.config=config or DEFAULT_CONFIG
        if mode not in {'optimized','baseline'}:raise ValueError('invalid mode')
        self.mode=mode
        duration=self.config['pump_required_h'];deadline=self.config['pump_deadline_h']
        if not all(math.isfinite(x) for x in [duration,deadline]) or not 0<duration<=deadline<=168:
            raise ValueError('invalid pump duration or deadline')
        self.registry=DeviceRegistry()
        for row in self.config['devices']:
            self.registry.register(SimulatedDevice(Capabilities(**row)))
        if not self.registry.devices:raise ValueError('at least one modeled device is required')
        self.gate=SafetyEnvelope(self.config['max_site_power_w'])
        self.monitor=StabilityMonitor(backend)
        self.field=AdaptiveField()
        self.weather_enabled=weather_enabled
        self.weather=WeatherOracle() if weather_enabled else EnvironmentContext()
        self.governor=GovernanceBridge()
        self.optimizer=Optimizer(self.config.get('weights'))
        self.domains=DomainRegistry();self.domains.register(FacilityDomain(self.optimizer))
        self.history={k:deque(maxlen=24) for k in self.registry.devices}
        self.ledger=[]
        self.sequence=0
        self.hour=0
        self.cost=0
        self.comfort_degree_h=0
        self.violations=[]
        self.prediction_errors=[]
        self.forecast_errors=0
        self.deadline_missed=False

    def step(self,fault=None):
        devices=self.registry.devices
        now=self.hour*3600
        statuses={}
        for key,d in devices.items():
            t=d.read()
            # Stable efficiency telemetry. Server/pump changes don't masquerade as drift.
            if d.capabilities.kind=='cooling':
                metric=t.temperature_c
            elif d.capabilities.kind=='compute':
                expected=d.capabilities.max_power_w*(0.25+0.75*t.performance**2)
                metric=t.power_w/expected if t.power_w>0 else 1.0
            else:
                metric=t.power_w/d.capabilities.max_power_w if t.power_w>0 else 1.0
            self.history[key].append(metric)
            statuses[key]=self.monitor.assess(key,list(self.history[key]))
        if fault=='drift':
            key=next(iter(devices))
            statuses[key]=self.monitor.assess(key,[100.0]*24)
        forecast_error=None
        try: forecast=self.weather.forecast(self.hour)
        except Exception as exc:
            forecast_error=type(exc).__name__;self.forecast_errors+=1
            forecast={'mode':'unavailable','confidence':0,'points':[], 'coupling':{}}
        pumps=[d for d in devices.values() if d.capabilities.kind=='deferrable']
        pump_required={}
        for pump in pumps:
            remaining=max(0,self.config['pump_required_h']-pump.completed_h)
            pump_required[pump.capabilities.device_id]=remaining>1e-8 and self.hour+1e-8>=self.config['pump_deadline_h']-remaining
        reward=0.0
        if self.ledger:
            previous=self.ledger[-1]
            error=previous['energy_prediction_error_kwh']
            predicted=previous['predicted_interval_energy_kwh']
            if error is not None:
                reward=max(-1,min(1,1-abs(error)/max(predicted,0.01)))
        field=self.field.update([0.001*(s['score']-0.2) for s in statuses.values()],reward)
        adaptive=all(s['ready'] and s['risk']=='green' and not s['breaker_open'] for s in statuses.values())
        adaptive &= field['stable'] and forecast['confidence']>=0.5 and self.mode=='optimized'
        defaults={k:23 if d.capabilities.kind=='cooling' else 1 if d.capabilities.kind=='compute'
                  else int(pump_required.get(k,False)) for k,d in devices.items()}
        best=None;candidates=[];governance_error=None;governance=None
        try:
            domains,raw=self.domains.model(devices=devices,context=forecast,now_s=now,gate=self.gate,required=pump_required)
            candidates=raw['facility']
            governance=self.governor.plan({'domains':domains,'allow_actions':bool(adaptive),
                'goal':'Reduce resource use while preserving service, comfort and scheduled work',
                'context':{'mode':forecast['mode'],'weather_enabled':self.weather_enabled,'weather':forecast.get('coupling')},
                'stress':{f'facility.{key}':status['score'] if status['ready'] else .2 for key,status in statuses.items()},
                'budget':self.config.get('governance_budget',256)})
            selected=governance['plans'].get('facility')
            if selected:
                index=int(selected['id'].split('_')[1]);best=candidates[index]
        except Exception as exc:
            governance_error=str(exc);adaptive=False
        targets=dict(best['targets']) if best else defaults
        for pump in pumps:
            if pump.completed_h+1e-8>=self.config['pump_required_h']:
                targets[pump.capabilities.device_id]=0
        self.sequence+=1
        dispatch=self.gate.dispatch(devices,targets,now,self.sequence)
        before={k:d.energy_kwh for k,d in devices.items()}
        predicted_interval=None
        if dispatch['committed'] and forecast['points']:
            one={**forecast,'points':forecast['points'][:1]}
            predicted=self.optimizer.evaluate(devices,targets,one,now,self.gate)
            predicted_interval=predicted.get('predicted_energy_kwh')
        for d in devices.values():
            d.gain_scale=field['gain_scale'] if adaptive else 1.0
        min_temp=math.inf;max_temp=-math.inf
        for minute in range(15):
            h=self.hour+minute/60
            # Independent actual disturbance includes an unforecast oscillation.
            ambient=30+5*math.sin(2*math.pi*(h-8)/24)+0.4*math.sin(h*2.7)
            watts=0
            for d in devices.values():
                d.tick(1/60,ambient,now+minute*60)
                t=d.read();c=d.capabilities;watts+=t.power_w
                if c.kind=='cooling':
                    min_temp=min(min_temp,t.temperature_c);max_temp=max(max_temp,t.temperature_c)
                    self.comfort_degree_h+=abs(t.temperature_c-23)/60
                    if not c.min_temperature_c<=t.temperature_c<=c.max_temperature_c:
                        self.violations.append({'hour':h,'device':c.device_id,'constraint':'temperature'})
                if c.kind=='compute' and t.performance<c.min_performance:
                    self.violations.append({'hour':h,'device':c.device_id,'constraint':'performance'})
            if watts>self.gate.max_site_power_w+1e-6:
                self.violations.append({'hour':h,'constraint':'site_power'})
            self.cost+=watts/1000/60*(0.32 if 15<=h%24<19 else 0.12)
        observed=sum(d.energy_kwh-before[k] for k,d in devices.items())
        error=None if predicted_interval is None else observed-predicted_interval
        if error is not None:self.prediction_errors.append(error)
        entry={'sequence':self.sequence,'hour':self.hour,'mode':self.mode,
               'forecast_mode':forecast['mode'],'forecast_error':forecast_error,
               'weather_coupling':forecast.get('coupling'),'stability':statuses,'field':field,
               'adaptive':adaptive,'feedback_reward':reward,'targets':targets,'selected':best,'alternatives':candidates,
               'dispatch':dispatch,'governance':governance,'governance_error':governance_error,
               'reason':'oracle mechanism arbitration selected a bounded domain action' if best else 'local conservative policy',
               'observed_energy_kwh':observed,'predicted_interval_energy_kwh':predicted_interval,
               'energy_prediction_error_kwh':error,'temperature_range_c':[min_temp,max_temp] if min_temp!=math.inf else None,
               'devices':{k:vars(d.read()) for k,d in devices.items()}}
        if governance:
            try:
                entry['governance_feedback']=self.governor.observe({'observations':{f'facility.{k}':v for k,v in normalized_observations(devices).items()},
                    'committed':dispatch['committed'],'progress':min(1,self.hour/24)})
            except Exception as exc:
                entry['governance_error']=str(exc)
        self.ledger.append(entry);self.hour+=0.25
        if abs(self.hour-self.config['pump_deadline_h'])<1e-8:
            self.deadline_missed=any(p.completed_h+1e-8<self.config['pump_required_h'] for p in pumps)
        return entry

    def run(self,steps=96,fault_step=None):
        for i in range(steps):self.step('drift' if fault_step==i else None)
        return self.summary()

    def summary(self):
        pumps=[d for d in self.registry if d.capabilities.kind=='deferrable']
        deadline_missed=self.hour>=self.config['pump_deadline_h'] and any(p.completed_h+1e-6<self.config['pump_required_h'] for p in pumps)
        return {'mode':self.mode,'hours':self.hour,'energy_kwh':sum(d.energy_kwh for d in self.registry),
                'cost':self.cost,'comfort_degree_h':self.comfort_degree_h,
                'pump_completed_h':sum(p.completed_h for p in pumps),'deadline_missed':deadline_missed or self.deadline_missed,
                'constraint_violations':len(self.violations),'forecast_errors':self.forecast_errors,
                'adaptive_steps':sum(e['adaptive'] for e in self.ledger),
                'prediction_mae_kwh':sum(abs(x) for x in self.prediction_errors)/max(1,len(self.prediction_errors)),
                'backend':self.monitor.backend,'data_mode':'synthetic','weather_enabled':self.weather_enabled,
                'governance_steps':sum(bool(e.get('governance')) for e in self.ledger),
                'governance_errors':sum(bool(e.get('governance_error')) for e in self.ledger)}

    def write_ledger(self,path):
        Path(path).parent.mkdir(parents=True,exist_ok=True)
        Path(path).write_text(''.join(json.dumps(e,allow_nan=False)+'\n' for e in self.ledger))

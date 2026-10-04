"""Independent hard gate; forecast scores cannot override raw telemetry checks."""
import math
from .devices import Command

class SafetyEnvelope:
    def __init__(self,max_site_power_w=6500):
        if not math.isfinite(max_site_power_w) or max_site_power_w<=0:
            raise ValueError('invalid site power limit')
        self.max_site_power_w=max_site_power_w

    def validate(self,devices,targets,now_s):
        errors=[]
        if set(targets)!=set(devices): errors.append('incomplete or unknown target devices')
        reserved=0
        for key,device in devices.items():
            c,t=device.capabilities,device.read()
            vals=[t.timestamp_s,t.power_w,t.temperature_c,t.performance]
            if not t.online or not all(math.isfinite(x) for x in vals):
                errors.append(key+': invalid/offline telemetry');continue
            if now_s-t.timestamp_s>c.telemetry_max_age_s or t.timestamp_s>now_s+1:
                errors.append(key+': stale/future telemetry')
            if not 0<=t.power_w<=c.max_power_w: errors.append(key+': power bound exceeded')
            target=targets.get(key,float('nan'))
            if not math.isfinite(target): errors.append(key+': invalid target');continue
            if c.kind=='cooling':
                if not c.min_temperature_c<=t.temperature_c<=c.max_temperature_c:
                    errors.append(key+': raw temperature outside envelope')
                if not c.min_temperature_c<=target<=c.max_temperature_c:
                    errors.append(key+': target outside envelope')
                # Reserve full local cooling authority, not predicted average duty.
                reserved+=c.max_power_w
            elif c.kind=='compute':
                if not c.min_performance<=target<=1: errors.append(key+': performance below floor')
                reserved+=c.max_power_w*(0.25+0.75*target**2)
            else:
                if target not in (0,1): errors.append(key+': switch must be 0 or 1')
                reserved+=c.max_power_w*target
        if reserved>self.max_site_power_w: errors.append('site power reservation exceeds budget')
        return errors

    def dispatch(self,devices,targets,now_s,sequence):
        errors=self.validate(devices,targets,now_s)
        if errors: return {'committed':False,'errors':errors,'acknowledgements':{}}
        acks={}
        for key,device in devices.items():
            acks[key]=device.apply(Command(key,targets[key],now_s,now_s+900,sequence),now_s)
        return {'committed':all(acks.values()),'errors':[] if all(acks.values()) else ['adapter rejected command'],
                'acknowledgements':acks}

"""Pluggable device contract and deterministic simulated local controllers."""
from dataclasses import dataclass, field
from typing import Protocol
import copy
import math
from .supervisor import PID, clamp

@dataclass(frozen=True)
class Capabilities:
    device_id: str
    kind: str
    max_power_w: float
    telemetry_max_age_s: float=120
    min_temperature_c: float=21
    max_temperature_c: float=26
    min_performance: float=0.7
    def __post_init__(self):
        if not self.device_id or self.kind not in {'cooling','compute','deferrable'}:
            raise ValueError('invalid identity or device kind')
        vals=[self.max_power_w,self.telemetry_max_age_s,self.min_temperature_c,
              self.max_temperature_c,self.min_performance]
        if not all(math.isfinite(x) for x in vals) or self.max_power_w<=0 or self.telemetry_max_age_s<=0:
            raise ValueError('invalid physical limits')
        if self.min_temperature_c>=self.max_temperature_c or not 0<self.min_performance<=1:
            raise ValueError('invalid temperature/performance limits')

@dataclass
class Telemetry:
    timestamp_s: float
    power_w: float
    temperature_c: float=24
    performance: float=1
    online: bool=True

@dataclass(frozen=True)
class Command:
    device_id: str
    target: float
    issued_at_s: float
    expires_at_s: float
    sequence: int
    reason: str='supervisory optimization'

class DeviceAdapter(Protocol):
    capabilities: Capabilities
    def read(self) -> Telemetry: ...
    def apply(self, command: Command, now_s: float) -> bool: ...
    def tick(self, dt_h: float, ambient_c: float, now_s: float) -> None: ...

class SimulatedDevice:
    def __init__(self,capabilities):
        self.capabilities=capabilities
        self.telemetry=Telemetry(0,0)
        self.pid=PID()
        self.command=None
        self.sequence=-1
        self.gain_scale=1
        self.energy_kwh=0
        self.completed_h=0
        self.stale=False
        self.last_target=None
        self.wear=0

    def read(self):
        return copy.copy(self.telemetry)

    def apply(self, command, now_s):
        c=self.capabilities
        if type(command.sequence) is not int or command.device_id!=c.device_id or command.sequence<=self.sequence:
            return False
        if not all(math.isfinite(x) for x in [command.target,command.issued_at_s,command.expires_at_s,now_s]):
            return False
        if not command.issued_at_s<=now_s<command.expires_at_s or command.expires_at_s-command.issued_at_s>1800:
            return False
        if c.kind=='cooling' and not c.min_temperature_c<=command.target<=c.max_temperature_c:
            return False
        if c.kind=='compute' and not c.min_performance<=command.target<=1:
            return False
        if c.kind=='deferrable' and command.target not in (0,1):
            return False
        self.sequence=command.sequence
        self.command=command
        if self.last_target is not None:
            self.wear+=abs(command.target-self.last_target)
        self.last_target=command.target
        return True

    def tick(self, dt_h, ambient_c, now_s):
        c=self.capabilities
        valid=self.command is not None and self.command.expires_at_s>now_s
        # Local watchdog returns to documented safe defaults when lease expires.
        target=self.command.target if valid else {'cooling':23,'compute':1,'deferrable':0}[c.kind]
        if c.kind=='cooling':
            t=self.telemetry.temperature_c
            duty=self.pid.compute(t,target,dt_h,gain_scale=self.gain_scale)
            if t>=c.max_temperature_c-0.20: duty=1.0
            if t<=c.min_temperature_c+0.20: duty=0.0
            self.telemetry.temperature_c=t+dt_h*(0.38*(ambient_c-t)+1.0-12*duty)
            watts=c.max_power_w*duty
        elif c.kind=='compute':
            self.telemetry.performance=target
            watts=c.max_power_w*(0.25+0.75*target**2)
            self.telemetry.temperature_c+=dt_h*(0.5*(ambient_c-self.telemetry.temperature_c)+4*target)
        else:
            watts=c.max_power_w*target
            self.completed_h+=dt_h*target
        self.telemetry.power_w=watts
        if not self.stale: self.telemetry.timestamp_s=now_s+dt_h*3600
        self.energy_kwh+=watts*dt_h/1000

class DeviceRegistry:
    def __init__(self): self.devices={}
    def register(self,adapter):
        key=adapter.capabilities.device_id
        if key in self.devices: raise ValueError('duplicate device identity')
        if len(self.devices)>=100: raise ValueError('prototype registry limit reached')
        self.devices[key]=adapter
    def __iter__(self): return iter(self.devices.values())

"""Seeded Python port of Drone FieldDynamicsProcessor, with bounded policy.
Source: vendor/drone-controller/kernel/quadra_supervisory_controller.cpp.
Noise injection is disabled for operational simulation; not a flight controller.
"""
import math
import random
import statistics

def clamp(x, lo, hi):
    return max(lo, min(hi,x))

class AdaptiveField:
    def __init__(self, size=32, seed=42):
        rng=random.Random(seed)
        self.field=[rng.gauss(0,0.1) for _ in range(size)]
        self.phase=0.0

    def update(self, inputs, reward=0.0):
        n=len(self.field)
        for i,x in enumerate(inputs[:n]):
            self.field[i]=clamp(self.field[i]+x*(1+0.1*math.sin(2*math.pi*i/n+self.phase)),-10,10)
        self.phase=(self.phase+0.01*math.tanh(sum(x*x for x in self.field)/n))%(2*math.pi)
        mean=statistics.mean(self.field)
        variance=statistics.pvariance(self.field)
        correction=0.1*(0.05-variance) if abs(0.05-variance)>0.001 else 0
        self.field=[clamp((x-mean*0.01)*(1+correction)+0.001*reward*math.tanh(x),-10,10)
                    for x in self.field]
        variance=statistics.pvariance(self.field)
        return {'variance':variance,'stable':variance<0.1,
                'gain_scale':clamp(1+0.05*statistics.mean(self.field),0.8,1.2)}

class PID:
    """Cooling PID: derivative on measurement with low-pass and conditional integration."""
    def __init__(self,kp=0.30,ki=0.003,kd=0.04):
        self.kp,self.ki,self.kd=kp,ki,kd
        self.integral=0.0
        self.previous=None
        self.derivative=0.0

    def compute(self,temperature,target,dt_h,limit=1.0,gain_scale=1.0):
        if dt_h<=0 or not all(math.isfinite(v) for v in [temperature,target,dt_h,limit,gain_scale]):
            raise ValueError('PID inputs must be finite with positive timestep')
        error=temperature-target
        raw=0 if self.previous is None else (temperature-self.previous)/dt_h
        alpha=dt_h/(0.10+dt_h)
        self.derivative+=alpha*(raw-self.derivative)
        tentative=clamp(self.integral+error*dt_h,-10,10)
        output=self.kp*gain_scale*error+self.ki*tentative+self.kd*self.derivative
        if 0<output<limit or (output>=limit and error<0) or (output<=0 and error>0):
            self.integral=tentative
        self.previous=temperature
        return clamp(output,0,limit)

"""Runs original TypeScript domain-coupling functions via bundled JavaScript."""
import json
import math
import shutil
import subprocess
from pathlib import Path

class WeatherOracle:
    def __init__(self):
        if not shutil.which('node'):
            raise RuntimeError('Install Node.js 24+ to execute the weather-oracle bridge')
        self.bridge=Path(__file__).resolve().parents[1]/'weather_bridge/run.mjs'
        self.cache={}

    def forecast(self, hour, horizon=8):
        # Synthetic disturbance model. Deliberately no use of future plant observations.
        key=(round(hour,6),horizon)
        if key in self.cache:
            return self.cache[key]
        result=subprocess.run(['node',str(self.bridge)],input=json.dumps({
            'shear_kts':16.5+4*math.sin(hour/6),'sst_c':30.1,'wind_kts':90+15*math.sin(hour/8)}),
            text=True,capture_output=True,timeout=5,check=True)
        coupling=json.loads(result.stdout)
        rate=coupling['coupledIntensificationRateKtsPer24h']
        out={'mode':'synthetic', 'confidence':0.65,'coupling':coupling,'points':[]}
        for i in range(horizon):
            h=hour+(i+1)*0.25
            # Coupled intensity changes thermal disturbance and reserve preference.
            out['points'].append({'hour':h,'ambient_c':30+5*math.sin(2*math.pi*(h-8)/24)+rate*0.003,
                                 'price_per_kwh':0.32 if 15<=h%24<19 else 0.12,
                                 'uncertainty_c':0.6+0.15*i,
                                 'storm_stress':max(0,min(1,(90+rate*(i+1)/96)/180))})
        self.cache.clear();self.cache[key]=out
        return out

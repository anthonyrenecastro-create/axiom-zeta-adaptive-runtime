"""Loopback-only HTTP dashboard + shadow telemetry ingestion. Never actuates hardware."""
import json
import math
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .runtime import Runtime
from .governance import GovernanceBridge
from .context import EnvironmentContext
from .weather import WeatherOracle
from .stability import StabilityMonitor
from collections import deque

class ShadowRegistry:
    """Network devices send telemetry for bounded recommendations; commands stay local."""
    def __init__(self):
        self.devices={};self.windows={};self.monitor=StabilityMonitor()
    def ingest(self,data):
        key=data.get('device_id')
        if not isinstance(key,str) or not 1<=len(key)<=80:raise ValueError('device_id must be 1..80 characters')
        if key not in self.devices and len(self.devices)>=100:raise ValueError('device limit reached')
        timestamp=data.get('timestamp_s');power=data.get('power_w');maximum=data.get('max_power_w')
        if any(type(x) not in (int,float) or not math.isfinite(x) for x in [timestamp,power,maximum]):
            raise ValueError('timestamp_s, power_w, max_power_w must be finite numbers')
        now=time.time()
        if abs(now-timestamp)>120:raise ValueError('telemetry is stale or future dated')
        if not 0<=power<=maximum or not 0<maximum<=1e7:raise ValueError('power outside declared envelope')
        previous=self.devices.get(key)
        if previous and timestamp<=previous['timestamp_s']:raise ValueError('out-of-order telemetry')
        if previous and maximum!=previous['max_power_w']:raise ValueError('declared device limit changed; re-register separately')
        window=self.windows.setdefault(key,deque(maxlen=24));window.append(power/maximum)
        status=self.monitor.assess(key,list(window))
        entry={'device_id':key,'timestamp_s':timestamp,'power_w':power,'max_power_w':maximum,
               'status':status,'mode':'shadow','recommendation':'retain local control' if not status['ready'] or status['risk']!='green'
               else 'eligible for domain-specific optimization; no hardware command emitted'}
        self.devices[key]=entry
        return entry
    def view(self):
        now=time.time()
        return [{**d,'stale':now-d['timestamp_s']>120} for d in self.devices.values()]

def serve(port=8080):
    runtime=Runtime();shadow=ShadowRegistry();external_governor=GovernanceBridge();lock=threading.Lock()
    dashboard=Path(__file__).with_name('dashboard.html').read_bytes()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,status,value,content_type='application/json'):
            body=value if isinstance(value,bytes) else json.dumps(value,allow_nan=False).encode()
            self.send_response(status);self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
        def do_GET(self):
            with lock:
                if self.path=='/':self.send(200,dashboard,'text/html; charset=utf-8')
                elif self.path=='/api/state':self.send(200,{'summary':runtime.summary(),'last':runtime.ledger[-1] if runtime.ledger else None,'shadow_devices':shadow.view(),'history':[{'hour':e['hour'],'observed_energy_kwh':e['observed_energy_kwh'],'predicted_interval_energy_kwh':e['predicted_interval_energy_kwh']} for e in runtime.ledger[-32:]]})
                elif self.path=='/api/ledger':self.send(200,runtime.ledger)
                elif self.path=='/health':self.send(200,{'ok':True,'mode':'simulation-and-shadow'})
                else:self.send(404,{'error':'not found'})
        def do_POST(self):
            # Browser cross-origin writes are not accepted on this local dashboard.
            origin=self.headers.get('Origin')
            if origin and origin!=f'http://127.0.0.1:{port}':
                self.send(403,{'error':'origin rejected'});return
            try:
                count=int(self.headers.get('Content-Length','0'))
                if not 0<=count<=65536:raise ValueError('body too large')
                body=json.loads(self.rfile.read(count) or b'{}')
                if not isinstance(body,dict):raise ValueError('expected JSON object')
                with lock:
                    if self.path=='/api/step':
                        steps=body.get('steps',1)
                        if type(steps) is not int or not 1<=steps<=24:raise ValueError('steps must be 1..24')
                        if runtime.hour+steps*.25>168:raise ValueError('reset demo after 168 simulated hours')
                        for _ in range(steps):runtime.step()
                        self.send(200,{'summary':runtime.summary(),'last':runtime.ledger[-1]})
                    elif self.path=='/api/reset':
                        runtime.__init__();self.send(200,{'ok':True})
                    elif self.path=='/api/context':
                        enabled=body.get('weather_enabled')
                        if type(enabled) is not bool:raise ValueError('weather_enabled must be boolean')
                        runtime.weather_enabled=enabled
                        runtime.weather=WeatherOracle() if enabled else EnvironmentContext()
                        self.send(200,{'weather_enabled':enabled})
                    elif self.path=='/api/govern':self.send(200,{'mode':'shadow','decision':external_governor.plan(body)})
                    elif self.path=='/api/outcome':self.send(200,external_governor.observe(body))
                    elif self.path=='/api/govern/reset':
                        external_governor.__init__();self.send(200,{'ok':True})
                    elif self.path=='/api/telemetry':self.send(202,shadow.ingest(body))
                    else:self.send(404,{'error':'not found'})
            except (ValueError,TypeError,KeyError) as exc:self.send(400,{'error':str(exc)})
            except Exception:self.send(500,{'error':'runtime failure; inspect local logs'})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    print(f'Axiom Zeta dashboard: http://127.0.0.1:{port} (simulation + shadow mode)',flush=True)
    server.serve_forever()

"""Stateful Python boundary to the generalized original TypeScript cognitive engine."""
import json
import shutil
import subprocess
from pathlib import Path

class GovernanceBridge:
    def __init__(self):
        if not shutil.which('node'):raise RuntimeError('Node.js 24+ is required for the world governor')
        self.runner=Path(__file__).resolve().parents[1]/'governance/run.mjs'
        self.session=None
        self.last=None
    def _call(self,operation,payload):
        result=subprocess.run(['node',str(self.runner)],input=json.dumps({'operation':operation,'payload':payload,'session':self.session},allow_nan=False),text=True,capture_output=True,timeout=10)
        if result.returncode:raise ValueError(result.stderr.strip() or 'governor rejected request')
        response=json.loads(result.stdout);self.session=response['session'];self.last=response['result']
        return response['result']
    def plan(self,payload):return self._call('plan',payload)
    def observe(self,payload):return self._call('observe',payload)

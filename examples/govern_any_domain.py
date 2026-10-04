"""Run the same governor for compute + logistics, with weather absent.
Domain models provide predictions; here they are illustrative numeric fixtures.
"""
import json
from az_runtime.governance import GovernanceBridge

g=GovernanceBridge()
request={'goal':'Save resources while maintaining service','domains':[
 {'id':'compute','observations':{'utilization':.5},'bounds':{'cpu_cap':{'min':.6,'max':1}},
  'objectives':{'energy':1,'service_loss':2},'candidates':[
   {'id':'eco','feasible':True,'targets':{'cpu_cap':.8},'metrics':{'energy':.7,'service_loss':.1},'predicted_observations':{'utilization':.6}},
   {'id':'full','feasible':True,'targets':{'cpu_cap':1},'metrics':{'energy':1,'service_loss':0},'predicted_observations':{'utilization':.5}}]},
 {'id':'logistics','observations':{'queue':.6},'bounds':{'dispatch_rate':{'min':1,'max':4}},
  'objectives':{'fuel':1,'lateness':3},'candidates':[
   {'id':'batch','feasible':True,'targets':{'dispatch_rate':2},'metrics':{'fuel':.4,'lateness':.3},'predicted_observations':{'queue':.7}},
   {'id':'expedite','feasible':True,'targets':{'dispatch_rate':4},'metrics':{'fuel':.8,'lateness':.05},'predicted_observations':{'queue':.4}}]}]}
plan=g.plan(request)
report={'mode':'modeled-domain-demo','weather':'absent','plans':plan['plans']}
feedback=g.observe({'observations':{'compute.utilization':.6,'logistics.queue':.45},'committed':True,'progress':.3})
report.update({'consequence':feedback['consequence'],'memory':feedback['memory_layers']})
print(json.dumps(report,indent=2))

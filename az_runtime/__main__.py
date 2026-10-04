import argparse
import json
from pathlib import Path
from .runtime import Runtime

def main():
    p=argparse.ArgumentParser(description='Axiom Zeta adaptive systems prototype')
    sub=p.add_subparsers(dest='command',required=True)
    demo=sub.add_parser('demo');demo.add_argument('--steps',type=int,default=96)
    demo.add_argument('--backend',choices=['fallback','native'],default='fallback')
    demo.add_argument('--output',default='outputs');demo.add_argument('--config')
    demo.add_argument('--fault-step',type=int)
    demo.add_argument('--weather',action='store_true',help='enable optional synthetic weather context')
    serve=sub.add_parser('serve');serve.add_argument('--port',type=int,default=8080)
    args=p.parse_args()
    if args.command=='serve':
        from .server import serve as start
        start(args.port);return
    if not 1<=args.steps<=672:p.error('steps must be 1..672')
    cfg=json.loads(Path(args.config).read_text()) if args.config else None
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    optimized=Runtime(cfg,backend=args.backend,weather_enabled=args.weather);baseline=Runtime(cfg,backend=args.backend,mode='baseline',weather_enabled=args.weather)
    a=optimized.run(args.steps,args.fault_step);b=baseline.run(args.steps,args.fault_step)
    summary={'optimized':a,'baseline':b,'energy_reduction_percent':100*(b['energy_kwh']-a['energy_kwh'])/b['energy_kwh'],
             'cost_reduction_percent':100*(b['cost']-a['cost'])/b['cost'],
             'comparison':'same synthetic disturbances, limits, deadline; optimized may trade comfort/performance within bounds'}
    optimized.write_ledger(out/'optimized.jsonl');baseline.write_ledger(out/'baseline.jsonl')
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()

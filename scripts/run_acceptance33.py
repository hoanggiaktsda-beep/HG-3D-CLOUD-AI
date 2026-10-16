"""Run real regression tests and record failures/skips separately from acceptance.
Passing tests never certifies automatic vision, assembly or production readiness.
"""
import argparse,json,sys,unittest
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise SystemExit('Refuse overwrite of existing acceptance evidence')
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'))
result=unittest.TextTestRunner(verbosity=2).run(suite)
summary={'test':33,'generated_utc':datetime.now(timezone.utc).isoformat(),'tests_run':result.testsRun,
 'failures':[t.id() for t,_ in result.failures],'errors':[t.id() for t,_ in result.errors],
 'skipped':[{'test':t.id(),'reason':reason} for t,reason in result.skipped],
 'regression_passed':result.wasSuccessful() and not result.skipped and result.testsRun>0,
 'system_accepted':False,'test30_status':'CẦN XÁC NHẬN',
 'scope':'Regression uses public/synthetic fixtures and explicit fault injection. Replay is not live AI evidence.'}
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open('x') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
print(json.dumps(summary,ensure_ascii=False))
if __import__('os').environ.get('GITHUB_ACTIONS'):
    print('::notice title=Actual TEST33 core regressions::'+json.dumps(summary,ensure_ascii=False).replace('%','%25').replace('\n','%0A').replace('\r','%0D'))
if not summary['regression_passed']:raise SystemExit(1)

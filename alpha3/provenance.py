from pathlib import Path
import hashlib,json,os,subprocess
p=Path('alpha3-evidence');p.mkdir(exist_ok=True)
def git(path):return subprocess.check_output(['git','-C',path,'rev-parse','HEAD'],text=True).strip()
assert git('.')=='f4fa14ffee657c2d400e51b85f8e78c8f231a47c'
assert git('../infra')==os.environ['GITHUB_SHA']
data={'application_commit':git('.'),'infrastructure_commit':git('../infra'),'workflow_ref':os.environ.get('GITHUB_WORKFLOW_REF'),
      'run_id':os.environ.get('GITHUB_RUN_ID'),'attempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'job':os.environ.get('GITHUB_JOB')}
(p/'provenance.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))

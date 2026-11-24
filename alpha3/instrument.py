#!/usr/bin/env python3
"""Run additional targeted instrumentation and preserve honest JUnit outcomes."""
from pathlib import Path
import argparse,subprocess,time,xml.etree.ElementTree as E,html,json
p=argparse.ArgumentParser();p.add_argument('--profile',required=True);p.add_argument('--tests',required=True);p.add_argument('--expected',type=int,required=True);a=p.parse_args()
directory=Path('alpha3-evidence')/a.profile;directory.mkdir(parents=True,exist_ok=True)
command=['adb','shell','am','instrument','-w','-r','-e','class',a.tests,'-e','alpha3Profile',a.profile,
         'com.nezabudka.preview.test/androidx.test.runner.AndroidJUnitRunner']
start=time.monotonic()
try:
 r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=600);output=r.stdout;rc=r.returncode
except subprocess.TimeoutExpired as e:
 output=(e.stdout or b'').decode(errors='replace') if isinstance(e.stdout,bytes) else e.stdout or '';output+='\nHOST TIMEOUT';rc=124
(directory/'instrumentation.txt').write_text(output)
current={};last=None;cases=[]
for line in output.splitlines():
 if line.startswith('INSTRUMENTATION_STATUS: '):
  key,value=line[len('INSTRUMENTATION_STATUS: '):].split('=',1);current[key]=value;last=key
 elif line.startswith('INSTRUMENTATION_STATUS_CODE: '):
  code=int(line.split(': ',1)[1])
  if code!=1 and current.get('test'):
   cases.append((current.get('class','unknown'),current['test'],code,current.get('stack',current.get('stream',''))))
  current={};last=None
 elif last:current[last]+='\n'+line
suite=E.Element('testsuite',name='Alpha3-'+a.profile,tests=str(len(cases)),failures=str(sum(c[2]!=0 for c in cases)),errors='0',skipped='0',time=str(time.monotonic()-start))
for cl,method,code,stack in cases:
 t=E.SubElement(suite,'testcase',classname=cl,name=method)
 if code!=0:E.SubElement(t,'failure',message=f'Instrumentation status {code}').text=stack
E.ElementTree(suite).write(directory/'TEST-diagnostics.xml',encoding='utf-8',xml_declaration=True)
(directory/'results.html').write_text('<meta charset="utf-8"><title>Alpha3 '+html.escape(a.profile)+'</title>'+''.join(
 '<details open><summary>'+html.escape(cl+'.'+method+' — '+('PASS' if code==0 else 'FAIL'))+'</summary><pre>'+html.escape(stack)+'</pre></details>' for cl,method,code,stack in cases))
summary={'profile':a.profile,'expected':a.expected,'actual':len(cases),'failed':sum(c[2]!=0 for c in cases),'process_exit':rc}
(directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
raise SystemExit(0 if rc==0 and len(cases)==a.expected and all(c[2]==0 for c in cases) else 1)

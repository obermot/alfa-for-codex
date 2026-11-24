#!/usr/bin/env python3
from pathlib import Path
import argparse,collections,hashlib,json,xml.etree.ElementTree as E

HERE=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--suite',choices=['unit','android']);p.add_argument('--results',type=Path)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--images',action='store_true');a=p.parse_args();root=a.source.resolve()
 report={};errors=[]
 manifest=json.loads((root/'alpha3-evidence/overlay-manifest.json').read_text())
 changed=[name for name,digest in manifest['functional_source_sha256'].items() if not (root/name).exists() or sha(root/name)!=digest]
 report['protected_source_or_reference_changes']=changed
 if changed:errors.append('Functional source / approved reference changed')
 if a.suite:
  expected=json.loads((HERE/'expected-tests.json').read_text())[a.suite];found=collections.Counter();results=[]
  for path in sorted(a.results.rglob('TEST-*.xml')):
   r=E.parse(path).getroot()
   for t in r.iter('testcase'):
    key=t.get('classname')+'.'+t.get('name');found[key]+=1
    status='skipped' if t.find('skipped') is not None else 'failed' if t.find('failure') is not None or t.find('error') is not None else 'passed'
    results.append({'id':key,'status':status,'xml':str(path)})
  missing=sorted(set(expected)-set(found));extra=sorted(set(found)-set(expected));duplicate={k:v for k,v in found.items() if v!=1}
  skipped=[t['id'] for t in results if t['status']=='skipped' and t['id'] in expected]
  report.update(suite=a.suite,expected=len(expected),actual=len(results),counts=dict(collections.Counter(t['status'] for t in results)),
                missing=missing,extra=extra,duplicate=duplicate,skipped=skipped,tests=results)
  if missing or duplicate or skipped:errors.append('Original scenario coverage incomplete')
  if a.suite=='android':
   files=list((root/'alpha3-evidence/baseline-device').rglob('*.full.png'))
   image_names={f.name.removesuffix('.full.png') for f in files}
   no_images=[name for name in expected if name.rsplit('.',1)[1] not in image_names]
   logs=list(a.results.rglob('logcat-*.txt'))
   report.update(full_screenshots=len(files),missing_full_screenshots=no_images,individual_logcats=len(logs))
   if no_images or len(logs)<78:errors.append('Device screenshots/logcats incomplete')
   capture_errors={str(p):p.read_text() for p in (root/'alpha3-evidence/baseline-device').rglob('*.capture-status.txt') if p.read_text()!='OK'}
   report['capture_errors']=capture_errors
   if capture_errors:errors.append('One or more device evidence captures failed')
 if a.images:
  from PIL import Image,ImageChops
  approved=root/'app/src/test/snapshots/pdf87';actual=root/'app/build/alpha3-evidence/pdf87-actual-ru'
  difference=root/'alpha3-evidence/pdf87-comparison';difference.mkdir(parents=True,exist_ok=True)
  rows=[]
  for golden in sorted(approved.glob('*.png')):
   candidate=actual/golden.name
   if not candidate.is_file():errors.append('Missing actual '+golden.name);continue
   with Image.open(golden) as g,Image.open(candidate) as c:
    g=g.convert('RGBA');c=c.convert('RGBA')
    if g.size!=c.size:errors.append('Image dimensions differ '+golden.name);continue
    diff=ImageChops.difference(g,c).convert('RGB');diff.save(difference/(golden.stem+'-diff.png'))
    canvas=Image.new('RGB',(g.width*2,g.height),'white');canvas.paste(g,(0,0));canvas.paste(c,(g.width,0));canvas.save(difference/(golden.stem+'-compare.png'))
    rows.append({'name':golden.name,'approved_sha256':sha(golden),'actual_sha256':sha(candidate),'different_pixels':sum(1 for pixel in diff.getdata() if pixel!=(0,0,0))})
  report['pdf87_ru']=rows
  if len(rows)!=297:errors.append('Expected 297 actual/reference image pairs')
  report['uk_candidate_count']=len(list((root/'app/build/alpha3-evidence/pdf87-candidate-uk').glob('*.png')))
  if report['uk_candidate_count']!=297:errors.append('Expected 297 separate Ukrainian candidates')
  night_reference=root/'app/src/test/snapshots/pdf87-night'
  night_actual=root/'app/build/alpha3-evidence/pdf87-night-ru'
  night_rows=[]
  for golden in sorted(night_reference.glob('*.png')):
   candidate=night_actual/golden.name
   if not candidate.is_file():errors.append('Missing actual night '+golden.name);continue
   with Image.open(golden) as g,Image.open(candidate) as c:
    if g.size!=c.size:errors.append('Night image dimensions differ '+golden.name);continue
    diff=ImageChops.difference(g.convert('RGB'),c.convert('RGB'))
    count=sum(1 for pixel in diff.getdata() if pixel!=(0,0,0))
    night_rows.append({'name':golden.name,'different_pixels':count})
    if count:errors.append('Night render differs from approved '+golden.name)
  report['pdf87_night_ru']=night_rows
  if len(night_rows)!=297:errors.append('Expected 297 night actual/reference image pairs')
  report['night_uk_candidate_count']=len(list((root/'app/build/alpha3-evidence/pdf87-night-uk').glob('*.png')))
  if report['night_uk_candidate_count']!=297:errors.append('Expected 297 night Ukrainian candidates')
 report['errors']=errors;a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['tests','pdf87_ru']},ensure_ascii=False,indent=2))
 if errors:raise SystemExit(1)
if __name__=='__main__':main()

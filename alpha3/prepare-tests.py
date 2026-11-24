#!/usr/bin/env python3
"""Apply an atomic, hash-guarded TEST-ONLY overlay to the pinned Alpha 2 source."""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, difflib

HERE=Path(__file__).resolve().parent
PIN='140fb1cf91afc83f4d2f74eee6cad734ace3866c'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def method_names(s):return sorted(re.findall(r'\bfun\s+(`[^`]+`|\w+)\s*\(',s))
def protected(root):
    return {p:sha((root/p).read_bytes()) for p in git(root,'ls-files').splitlines()
            if not (p.startswith(('app/src/test/','app/src/androidTest/')) and p.endswith('.kt')) and (root/p).is_file()}
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--check-only',action='store_true');parser.add_argument('--fixture',action='store_true')
    args=parser.parse_args();root=args.source.resolve()
    if not args.fixture:
        assert git(root,'rev-parse','HEAD')==PIN,'Unexpected application commit'
        assert not git(root,'status','--porcelain'),'Application checkout must be clean before overlay'
    baseline=json.loads((HERE/'expected-tests.json').read_text())
    assert len(baseline['unit'])==734 and len(baseline['android'])==78
    before=protected(root) if not args.fixture else {}
    updates={};diffs=[]
    for entry in json.loads((HERE/'test-edits.json').read_text()):
        rel=entry['path'];assert rel.startswith(('app/src/test/','app/src/androidTest/'))
        path=root/rel;raw=path.read_bytes();assert sha(raw)==entry['base_sha256'],f'Source mismatch: {rel}'
        text=raw.decode('utf-8');original=text
        for edit in entry['edits']:
            assert text.count(edit['old'])==edit['count'],f'Patch context mismatch: {rel}'
            text=text.replace(edit['old'],edit['new'])
        assert sha(text.encode())==entry['patched_sha256'],f'Patched digest mismatch: {rel}'
        assert method_names(original)==method_names(text),f'Original scenario/helper declarations were removed: {rel}'
        updates[rel]=text
        diffs.extend(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    for path in sorted((HERE/'kotlin').glob('*.kt')):
        rel='app/src/androidTest/java/com/nezabudka/testharness/'+path.name
        assert not (root/rel).exists(),f'Overlay already exists: {rel}'
        updates[rel]=path.read_text()
    if not args.fixture:
        test_paths=list((root/'app/src/test').rglob('*.kt'))+list((root/'app/src/androidTest').rglob('*.kt'))
        all_source='\n'.join(p.read_text() for p in test_paths)
        names=set(n.strip('`') for n in method_names(all_source))
        for suite,items in baseline.items():
            for item in items:
                cl,method=item.rsplit('.',1)
                assert (root/('app/src/test' if suite=='unit' else 'app/src/androidTest')/'java'/Path(*cl.split('.'))).with_suffix('.kt').exists(),item
                assert method in names,item
    report={'source_commit':PIN,'check_only':args.check_only,'baseline_scenarios':{k:len(v) for k,v in baseline.items()},
        'overlay_files':{p:sha(s.encode()) for p,s in updates.items()},'functional_source_sha256':before}
    if args.check_only:print(json.dumps({k:v for k,v in report.items() if k!='functional_source_sha256'},indent=2));return
    for rel,text in updates.items():
        path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
    assert args.fixture or protected(root)==before,'Functional source changed'
    evidence=root/'alpha3-evidence';evidence.mkdir(exist_ok=True)
    (evidence/'overlay-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    (evidence/'test-overlay.patch').write_text(''.join(diffs))
    print(f'Applied {len(updates)} test files; all 809 original scenario identities plus 3 necessary feature checks retained; functional source unchanged.')
if __name__=='__main__':main()

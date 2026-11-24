from pathlib import Path
import hashlib,json
root=Path('.');out=root/'alpha3-evidence/inventory.json'
files=set()
for pattern in ['alpha3-evidence/**/*','app/build/reports/**/*','app/build/test-results/**/*','app/build/outputs/**/*','app/build/alpha3-evidence/**/*','app/build/alpha3-scale-evidence/**/*','app/src/test/snapshots/pdf87/**/*']:
 files.update(p for p in root.glob(pattern) if p.is_file() and p!=out)
rows=[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
apks=[r for r in rows if r['path'].endswith('.apk')]
(root/'alpha3-evidence/apk-sha256.txt').write_text(''.join(r['sha256']+'  '+r['path']+'\n' for r in apks))
print(f'Inventoried {len(rows)} files and {len(apks)} APKs')

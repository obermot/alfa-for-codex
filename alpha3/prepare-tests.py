from pathlib import Path
import os
root = Path(os.environ.get("NEZABUDKA_SOURCE", "."))
def replace(path, old, new):
    p = root / path
    s = p.read_text(encoding="utf-8")
    if s.count(old) != 1:
        raise RuntimeError(f"Unexpected source: {p}")
    p.write_text(s.replace(old,new), encoding="utf-8")
base = "app/src/"
replace(base+"androidTest/java/com/nezabudka/testharness/FinalDeviceFixture.kt",
"        db.clearAllTables()",
"""        db.clearAllTables()
        val session = android.util.AtomicFile(File(app.noBackupFilesDir, "last-ui-session-v1"))
        session.delete()
        check(!session.baseFile.exists()) { "Persisted UI session was not cleared" }""")
replace(base+"test/java/com/nezabudka/testharness/FinalScaleEnvelopeUiTest.kt",
'        val dir=File("/workspace/Nezabudka/work/sixth-ui");dir.mkdirs()',
'''        val dir=File("build/alpha3-scale-evidence").absoluteFile
        check(dir.isDirectory || dir.mkdirs()) { "Cannot create evidence directory: $dir" }''')

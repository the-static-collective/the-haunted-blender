"""Verify every historical 001/002 specimen against the exact #65 parent."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
pin = json.loads((HERE / 'ANCESTOR_PIN.json').read_text())
parent = Path(sys.argv[1])
head = subprocess.check_output(['git', '-C', str(parent), 'rev-parse', 'HEAD'], text=True).strip()
if head != pin['commit']:
    raise SystemExit('Expected exact MANGALIZE-002 parent commit')
for row in pin['files']:
    old = subprocess.check_output(['git', '-C', str(parent), 'show', head + ':' + row['path']])
    if hashlib.sha256(old).hexdigest() != row['sha256'] or (ROOT / row['path']).read_bytes() != old:
        raise SystemExit('Immutable 001/002 evidence changed: ' + row['path'])
print(f"IMMUTABLE PARENT: PASS — {len(pin['files'])} historical witnesses at {head}")

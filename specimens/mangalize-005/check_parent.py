"""Compare immutable 001/002/003/004 history and implementations to exact #67."""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from haunted_blender import mangalize as m

pin = m.read(Path(__file__).resolve().parent / 'ANCESTOR_PIN.json')
parent = Path(sys.argv[1])
head = subprocess.check_output(['git','-C',str(parent),'rev-parse','HEAD'],text=True).strip()
m.require(head == pin['commit'], 'expected exact #67 parent commit')
for row in pin['files']:
    old = subprocess.check_output(['git','-C',str(parent),'show',head + ':' + row['path']])
    m.require(hashlib.sha256(old).hexdigest() == row['sha256'] and (ROOT / row['path']).read_bytes() == old,
              'historical witness changed: ' + row['path'])
print('IMMUTABLE PARENT: PASS — ' + str(len(pin['files'])) + ' witnesses/implementations at ' + head)

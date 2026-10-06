"""Compare foreign witness bytes against an exact read-only LemonPRESS checkout."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
pin = json.loads((ROOT / "lemonpress/PIN.json").read_text())
upstream = Path(sys.argv[1])
actual = subprocess.check_output(["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True).strip()
if actual != pin["commit"]:
    raise SystemExit("Foreign repository is not the exact experimental commit")
for name in pin["copiedFiles"]:
    original = subprocess.check_output(["git", "-C", str(upstream), "show", pin["commit"] + ":" + name])
    if original != (ROOT / "lemonpress" / name).read_bytes():
        raise SystemExit(f"Foreign witness changed: {name}")
print("EXACT LEMONPRESS PIN: PASS — original page, PNG, and closed handoff unchanged")

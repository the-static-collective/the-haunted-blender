"""Render two observer-local memories through one finite opacity budget."""
import argparse
import json
from pathlib import Path

from . import memory_feedback


def main():
    p = argparse.ArgumentParser(prog="haunted-memory-competition")
    p.add_argument("root", type=Path)
    p.add_argument("artifact_snapshot", type=Path)
    p.add_argument("take_acceptance", type=Path)
    p.add_argument("memory_plan", type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    plan = json.loads(a.memory_plan.expanduser().read_text(encoding="utf-8"))
    if not isinstance(plan, dict) or set(plan) != {"timeline", "regions"}:
        p.error("memory plan must contain timeline and regions only")
    result = memory_feedback.render(
        a.root, a.artifact_snapshot, a.take_acceptance,
        plan["timeline"], plan["regions"], a.out, competition=True)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

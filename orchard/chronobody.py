"""ORCHARD-001: a *read-only*, declarative branch-contract dry-run.

No Git checkout, branch discovery, filesystem write, shell, import of organ code,
provider call, execution, rendering, or authority/promotion action is performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "CHRONOBODY.md"
FENCE = re.compile(r"\x60{3}orchard-registry-json\s*\n(.*?)\n\x60{3}", re.DOTALL)
SHA = re.compile(r"^[0-9a-f]{40}$")
ATOM = re.compile(r"^[a-z][a-z0-9_.-]*$")
ALLOWED_ORGAN_KEYS = {
    "id", "repository", "branch_hint", "commit", "state",
    "stack_parent_hint", "requires", "provides", "adapter",
}
NONCLAIMS = [
    "No registered organ was materialized, imported, executed, or rendered.",
    "Declared input/output labels do not prove adapter compatibility.",
    "Stacked branch ancestry and overlapping implementations were not reconciled.",
    "No creative acceptance, scene canon, source rights, or publication is implied.",
]


class RegistryError(ValueError):
    pass


def parse_registry(markdown: str) -> dict:
    matches = FENCE.findall(markdown)
    if len(matches) != 1:
        raise RegistryError("Expected exactly one orchard-registry-json fence")
    try:
        data = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        raise RegistryError("Invalid registry JSON") from exc
    validate_registry(data)
    return data


def validate_registry(data: dict) -> None:
    if not isinstance(data, dict) or set(data) != {
        "schema", "mode", "execution", "organs"
    }:
        raise RegistryError("Registry must match its closed schema")
    if (
        data["schema"] != "haunted-blender/chronobody-registry/v0"
        or data["mode"] != "EXPERIMENTAL_DRY_RUN"
        or data["execution"] != "DISABLED"
    ):
        raise RegistryError("Unknown schema, mode, or execution boundary")
    organs = data["organs"]
    if not isinstance(organs, list) or not organs:
        raise RegistryError("Expected a nonempty organ list")
    ids = set()
    for organ in organs:
        if not isinstance(organ, dict) or set(organ) != ALLOWED_ORGAN_KEYS:
            raise RegistryError("Unknown/missing organ field (commands are forbidden)")
        name, commit = organ["id"], organ["commit"]
        if not isinstance(name, str) or not ATOM.fullmatch(name) or name in ids:
            raise RegistryError("Invalid or repeated organ ID")
        ids.add(name)
        if not isinstance(commit, str) or not SHA.fullmatch(commit):
            raise RegistryError("Organ identity requires an exact lowercase 40-hex SHA")
        if (
            organ["repository"] != "the-static-collective/the-haunted-blender"
            or not isinstance(organ["branch_hint"], str)
            or not organ["branch_hint"].startswith("experimental/")
            or not isinstance(organ["stack_parent_hint"], str)
            or not organ["stack_parent_hint"].startswith("experimental/")
            or organ["state"] != "INCUBATING"
            or organ["adapter"] != "DECLARED_ONLY"
        ):
            raise RegistryError("Unrecognized repository, state, or adapter")
        for field in ("requires", "provides"):
            value = organ[field]
            if (
                not isinstance(value, list)
                or not value
                or len(value) != len(set(value)) if isinstance(value, list) else True
            ):
                raise RegistryError("Input/output list must be nonempty and unique")
            if any(not isinstance(v, str) or not ATOM.fullmatch(v) for v in value):
                raise RegistryError("Invalid contract token")
        if set(organ["requires"]) & set(organ["provides"]):
            raise RegistryError("Self-fulfilling organ contract")


def compile_plan(data: dict, wanted: str, available: list[str]) -> dict:
    validate_registry(data)
    if not ATOM.fullmatch(wanted) or any(not ATOM.fullmatch(x) for x in available):
        raise RegistryError("Invalid requested or available token")
    providers: dict[str, list[dict]] = {}
    for organ in data["organs"]:
        for output in organ["provides"]:
            providers.setdefault(output, []).append(organ)

    order: list[dict] = []
    selected: set[str] = set()
    visiting: set[str] = set()
    missing: set[str] = set()
    ambiguous: set[str] = set()
    cycles: set[str] = set()
    supplied = set(available)

    def visit(token: str) -> None:
        if token in supplied:
            return
        matches = providers.get(token, [])
        if not matches:
            missing.add(token)
            return
        if len(matches) != 1:
            ambiguous.add(token)
            return
        organ = matches[0]
        name = organ["id"]
        if name in visiting:
            cycles.add(name)
            return
        if name in selected:
            return
        visiting.add(name)
        for required in organ["requires"]:
            visit(required)
        visiting.remove(name)
        selected.add(name)
        order.append(organ)

    visit(wanted)
    if ambiguous:
        status = "AMBIGUOUS"
    elif cycles:
        status = "REFUSE"
    elif missing:
        status = "HELD"
    elif not order:
        status = "ALREADY_SUPPLIED"
    else:
        status = "CANDIDATE"

    overlaps = sorted({
        organ["id"] for organ in order
        if any(
            other["branch_hint"] == organ["stack_parent_hint"]
            for other in order if other["id"] != organ["id"]
        )
    })
    return {
        "schema": "haunted-blender/orchard-dry-run-receipt/v0",
        "status": status,
        "want": wanted,
        "available": sorted(supplied),
        "selected": [
            {"id": o["id"], "commit": o["commit"], "state": o["state"],
             "branch_hint": o["branch_hint"], "adapter": o["adapter"]}
            for o in order
        ],
        "missing": sorted(missing),
        "ambiguous": sorted(ambiguous),
        "cycles": sorted(cycles),
        "ancestry_overlap_review": overlaps,
        "unverified_gates": [
            "EXACT_CHECKOUT_INTEGRITY",
            "STACKED_ANCESTRY_RECONCILIATION",
            "ADAPTER_COMPATIBILITY",
            "MEDIA_AND_CREATIVE_ACCEPTANCE",
            "RENDER_AND_OUTPUT_RECEIPT",
        ] if order else [],
        "nonclaims": NONCLAIMS,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Dry-run declared Blender organ composition; never execute it")
    parser.add_argument("--want", required=True, help="Required output contract token")
    parser.add_argument("--have", nargs="*", default=[], help="Already supplied input tokens")
    args = parser.parse_args()
    markdown = REGISTRY.read_text(encoding="utf-8")
    try:
        data = parse_registry(markdown)
        result = compile_plan(data, args.want, args.have)
    except RegistryError as exc:
        print(json.dumps({"status": "REFUSE", "error": str(exc)}, sort_keys=True))
        return 2
    result["registry_sha256"] = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] in ("CANDIDATE", "ALREADY_SUPPLIED") else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import plugin_orchard, provider_driver


def emit(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def _read_json(path: str) -> dict:
    return json.loads(Path(path).expanduser().resolve(strict=True).read_text(encoding="utf-8"))


def _latest_observation(root: Path) -> dict:
    latest = plugin_orchard.latest(root)
    if latest is None:
        raise FileNotFoundError("No plugin orchard snapshot exists")
    path = root / latest["observationPath"]
    return json.loads(path.read_text(encoding="utf-8"))


def _bridge_rows(observation: dict) -> list[dict]:
    rows = []
    compatible_profiles = {
        profile["id"]
        for profile in plugin_orchard.load_profiles().get("profiles") or []
        if any(
            route in {
                "image-to-video",
                "motion-control",
                "replace-object",
                "reference-to-video",
                "element-to-video",
                "text-to-video",
            }
            for route in profile.get("routeKinds") or []
        )
    }
    for provider in observation.get("providers") or []:
        if not provider.get("connected"):
            continue
        if provider.get("profileId") not in compatible_profiles:
            continue
        if not any(model.get("available") for model in provider.get("models") or []):
            continue
        rows.append(
            {
                "providerId": provider["providerId"],
                "transport": "plugin_bridge",
                "profileId": provider["profileId"],
                "notes": [
                    "Installed from plugin orchard observation",
                    f"observation={observation.get('observedAt')}",
                ],
            }
        )
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(prog="haunted-blender-plugin-orchard")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("profiles")

    ingest = sub.add_parser("ingest")
    ingest.add_argument("root")
    ingest.add_argument("observation_json")
    ingest.add_argument("--install-bridges", action="store_true")

    latest = sub.add_parser("latest")
    latest.add_argument("root")

    usage = sub.add_parser("usage")
    usage.add_argument("root")

    install = sub.add_parser("install-bridges")
    install.add_argument("root")

    args = parser.parse_args(argv)
    if args.command == "profiles":
        result = plugin_orchard.load_profiles()
    elif args.command == "ingest":
        root = Path(args.root).expanduser().resolve()
        raw = _read_json(args.observation_json)
        if raw.get("schema") == plugin_orchard.OBSERVATION_SCHEMA:
            observed_at = raw["observedAt"]
            providers = raw["providers"]
            source = raw.get("source") or "external-plugin-crawler"
        else:
            observed_at = raw.get("observedAt")
            providers = raw.get("providers")
            source = raw.get("source") or "external-plugin-crawler"
        result = plugin_orchard.ingest_observation(
            root,
            observed_at=observed_at,
            providers=providers,
            source=source,
        )
        if args.install_bridges:
            observation = json.loads(
                Path(result["observation"]).read_text(encoding="utf-8")
            )
            rows = _bridge_rows(observation)
            result["adapterConfig"] = provider_driver.configure_adapters(root, rows)
    elif args.command == "latest":
        root = Path(args.root).expanduser().resolve()
        result = plugin_orchard.latest(root)
    elif args.command == "usage":
        result = plugin_orchard.usage_summary(args.root)
    else:
        root = Path(args.root).expanduser().resolve()
        observation = _latest_observation(root)
        rows = _bridge_rows(observation)
        if not rows:
            raise ValueError("Latest orchard observation has no executable plugin providers")
        result = provider_driver.configure_adapters(root, rows)

    emit(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

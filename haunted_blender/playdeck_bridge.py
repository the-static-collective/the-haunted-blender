"""Proposal-only projection of Flow Pantry material into PlayDeck's public DeckSpec shape."""
from __future__ import annotations

from .flow_pantry import validate_flow_manifest

SCHEMA = "haunted-blender/playdeck-flow-proposal/v1"


def _card_id(index: int, sha: str) -> str:
    return f"flow-{index + 1:03d}-{sha[:12]}"


def flow_to_playdeck(manifest: dict, *, deck_id: str = "flow-pantry", title: str = "Flow Pantry") -> dict:
    validate_flow_manifest(manifest)
    cards = []
    order = []
    for index, item in enumerate(manifest["items"]):
        card_id = _card_id(index, item["sha256"])
        order.append(card_id)
        cards.append(
            {
                "id": card_id,
                "source": f"flow://sha256/{item['sha256']}",
                "front": {"source": f"flow://sha256/{item['sha256']}"},
                "traits": ["video-source"],
                "temperament": ["sleeping"],
                "permissions": {
                    "awaken": True,
                    "duplicate": True,
                    "flip": False,
                    "fold": False,
                    "fracture": False,
                    "portal": False,
                    "merge": False,
                },
                "metadata": {
                    "flowPantry": {
                        "assetId": item["assetId"],
                        "toasterSpecimenId": item["toasterSpecimenId"],
                        "relativePath": item["relativePath"],
                        "byteLength": item["byteLength"],
                    },
                    "renderReady": False,
                    "semanticAuthority": "none",
                },
            }
        )
    deck = {
        "schemaVersion": "0.1",
        "id": deck_id,
        "title": title,
        "cards": cards,
        "order": order,
        "metadata": {
            "sourceSystem": "haunted-blender",
            "sourceSchema": manifest["schema"],
            "videoCardsRequireFreezeOrAwakening": True,
            "deckIsOrder": False,
        },
    }
    return {
        "schema": SCHEMA,
        "authority": "proposal-only",
        "deck": deck,
        "grantsPlaydeckRenderAuthority": False,
    }

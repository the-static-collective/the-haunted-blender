"""Proposal-only planning for Haunted Toaster VSPantry.

The Toaster implementation admits video bytes itself. This bridge merely maps
already-hashed Flow Pantry specimens into bounded, ordered proposal batches.
"""
from __future__ import annotations

from .flow_pantry import validate_flow_manifest

SCHEMA = "haunted-blender/toaster-vspantry-plan/v1"
TOASTER_MAX_INGREDIENTS = 16


def plan_toaster_vspantry(manifest: dict, *, max_ingredients: int = TOASTER_MAX_INGREDIENTS) -> dict:
    validate_flow_manifest(manifest)
    if not isinstance(max_ingredients, int) or not (1 <= max_ingredients <= TOASTER_MAX_INGREDIENTS):
        raise ValueError("Toaster v1 batches must contain 1–16 ingredients.")

    unique = []
    seen = set()
    for item in manifest["items"]:
        specimen = item["toasterSpecimenId"]
        if specimen not in seen:
            seen.add(specimen)
            unique.append(specimen)

    batches = []
    for offset in range(0, len(unique), max_ingredients):
        group = unique[offset: offset + max_ingredients]
        batch_number = len(batches) + 1
        batches.append(
            {
                "id": f"flow-batch-{batch_number:03d}",
                "authority": "proposal-only",
                "operatorId": "video-digestion/v1",
                "ingredients": [
                    {
                        "slot": f"clip-{index + 1:02d}",
                        "kind": "video-specimen",
                        "specimenId": specimen,
                    }
                    for index, specimen in enumerate(group)
                ],
            }
        )

    return {
        "schema": SCHEMA,
        "authority": "proposal-only",
        "sourceSchema": manifest["schema"],
        "importDoor": "haunted-toaster/VSPantry-folder-admission",
        "uniqueSpecimenCount": len(unique),
        "batchCount": len(batches),
        "maxIngredientsPerBatch": max_ingredients,
        "batches": batches,
        "grantsRendererAuthority": False,
    }

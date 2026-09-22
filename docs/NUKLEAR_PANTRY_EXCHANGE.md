# NUKLEAR PANTRY EXCHANGE-001 — Blender → Toaster

Status: **experimental, additive, local-only**. Based on Blender's frozen-alchemy branch (PR #3). Blender's separate Pantry-improvement branch (PR #4) is intentionally not merged or changed.

## Executable exchange

1. Existing Blender N1 creates and renders a real silent MP4 from an artist-proposed shape-echo or triadic-bridge relationship.
2. The exporter revalidates frozen original and derivative hashes, the selected output video hash, scoped-complete receipt, frozen snapshot identity, exact source order and output path.
3. It writes a path-free JSON manifest containing media and source digests, producer recipe/snapshot/receipt identity and explicit non-authority. No media, personal source filenames, EXIF, original paths or RAW bytes are placed in the manifest. A digest is not an identity/rights/consent attestation.
4. The Toaster consumer checks the explicit video, producer receipt and manifest, admits MP4 through existing VSPantry, archives a local immutable exchange entry, and saves a proposal-only recursive Pantry recipe referencing the admitted specimen.

The exporter does not render with Toaster, change Blender's film schema, replace the Blender Pantry catalog or import Blender PR #4. Toaster's stored recipe proposes use of existing clip-luma-texture-v1 digestion; it does not choose a candidate or change an accepted timeline.

## Produce a local export

After completing a Blender N1 alchemical preview and its scoped render receipt:

    python -m haunted_blender.exchange_cli \
      /path/to/BlenderLibrary \
      /path/to/frozen-alchemy-snapshot.json \
      /path/to/finished-alchemy.mp4 \
      --out /path/to/finished-alchemy.exchange.json

The existing Blender receipt is expected beside the MP4 with the suffix .mp4.receipt.json. Keep the video, receipt and manifest together for a local transfer. The exporter refuses missing or changed original/derivative bytes, altered output bytes, mismatched or incomplete receipts, bad ancestry and conflicting manifests.

On the separate Toaster companion exchange branch:

    node src/full-measure/scripts/import-blender-exchange.cjs \
      --toaster-home /path/to/actual/toaster-home \
      --manifest /path/to/finished-alchemy.exchange.json \
      --receipt /path/to/finished-alchemy.mp4.receipt.json \
      --video /path/to/finished-alchemy.mp4

The CLI deliberately requires the actual Toaster home; it cannot safely guess Electron's userData/toaster-home location.

## Truth boundaries

Schema: static-collective/pantry-exchange/v1. It carries producer recipe identity, snapshot and receipt hashes, the adapter, an ordered source lineage and output bytes. Source relation remains artist_proposed. Renderer and audio authority remain none.

SHA-256 establishes byte identity relative to supplied local evidence, not cryptographic author authentication. Toaster can verify imported video and receipt/manifest consistency but does not independently verify Blender's historical original-image bytes. A successful Blender receipt does not mean the Toaster has rendered a new video. The copied receipt may contain a source-machine absolute output path; the exchange archive remains local-only and is not automatically published.

## Next accepted slice

An imported specimen may later traverse the existing Toaster candidate selection, canonical score/timeline, actual production render and cook receipt, after which the output can be re-admitted as a new VSPantry specimen. Reverse Toaster → Blender film-shot rendering is not implemented: Blender can catalogue MP4s but currently renders still-image shots only. Blender PR #4's distinct Pantry improvements should be reconciled without wholesale merging historical branch ancestry.

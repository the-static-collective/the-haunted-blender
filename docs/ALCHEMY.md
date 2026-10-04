# N1 — The Alchemical Compiler (experimental add-on)

**Status:** bounded executable research cartridge on top of the N0 branch. N0's `haunted_blender.project`, catalog, CLI, snapshots and still-storyboard renderer are **not modified**. N1 does not change `haunted-blender/film/v1` or claim to have completed the N0/N2 filmmaking release gates.

## Purpose and contract

Make the relationship between two or three *already indexed* photographs a first-class, inspectable artist proposal. The prototype permits exactly two relation tags: `shape-echo` requires source and target; `triadic-bridge` requires source, bridge and target. Every participant must be a distinct cataloged asset. A user-authored statement explains the creative relation; its evidence class remains `artist_proposed`. The compiler does not infer that a physical reflection, real identity, semantic equivalence, or narrative continuity has been established.

A recipe specifies an explicit order of source roles. A frozen alchemy snapshot captures immutable source/derivative paths and SHA-256 digests, so later RAW derivative reassociation cannot silently change the rendered frames. Resolved RAW originals are verified as well as the edited frames used for rendering. A content-addressed snapshot lives in `snapshots/alchemy/<recipe-id>/<sha256>.json`. Snapshots cannot be overwritten with different bytes.

The first execution adapter is `ffmpeg-alchemy-crossfade/v1`: it performs a **real, deterministic, silent still-image sequence with timed crossfades**, not a semantic morph, relation detector, optical reflection renderer, material-transport engine or generative video model. It is an intentionally modest visual floor against which future geometry, topological, material, sound and model-backed cartridges can be compared. The plan labels visual and semantic continuity `not_assessed`; the receipt repeats nonclaims. On missing/change detection, rendering fails rather than issuing a success receipt.

## Local usage

From the N1 branch, start with the N0 library and index your **own** local pictures:

```sh
python -m haunted_blender init ~/HauntedBlender
python -m haunted_blender scan ~/HauntedBlender /path/to/local/photos
python -m haunted_blender stats ~/HauntedBlender
```

Read asset IDs from `~/HauntedBlender/.haunted-blender/library.sqlite3` using a local SQLite browser or Python. For three separately indexed images:

```sh
python -m haunted_blender.alchemy_cli create ~/HauntedBlender asset-SOURCE asset-TARGET \
  --relation triadic-bridge --bridge asset-BRIDGE \
  --statement "A cup contains water that reflects the moon"
python -m haunted_blender.alchemy_cli freeze ~/HauntedBlender alchemy-RECIPE_ID
python -m haunted_blender.alchemy_cli plan ~/HauntedBlender /absolute/path/to/frozen-alchemy-snapshot.json
python -m haunted_blender.alchemy_cli render ~/HauntedBlender /absolute/path/to/frozen-alchemy-snapshot.json \
  --out ~/HauntedBlender/renders/first-alchemy.mp4
```

Substitute the **actual IDs and frozen path returned** by the preceding commands. A pairwise exercise uses `--relation shape-echo` without a bridge. `--order bridge,source,target` changes the compositional order without reinterpreting the relationship; in a real film the artist should select the intended entry and exit frames. The three stages currently use 1,800 ms still segments with 450 ms crossfades for a 4,500 ms output. Dimensions: 320 × 180, 24 fps. These deliberately inexpensive preview settings are not AAA output specifications.

The rendered MP4 and its `.receipt.json` are written only to the explicitly requested local destination. Existing outputs/receipts are not overwritten. No photograph is committed, uploaded, sent to an AI provider or used to assert subject identity or consent.

## Integration membrane

- **N0 Pantry** supplies asset IDs, SHA-256, RAW/renderable derivative mapping and private local paths.
- **N0 Film** remains a separate authoritative representation; there is no automatic injection of alchemy receipts into film shots.
- **3rdi inspiration:** an artist-proposed relation is not a witnessed physical event.
- **ALEX / LOADOUT inspiration:** explicit source lineage, a frozen accepted recipe, scoped completion and nonclaims. These are local ideas, not verified runtime integrations.
- **Free Graph inspiration:** optional connections can be explored without promotion to global semantics; no Free Graph API is imported.
- **Toaster** is untouched. Any later exchange requires a versioned interface and explicit authority boundaries.

## Next seam / incompatibilities to investigate

1. User-selected correspondences (points, silhouettes, containment masks) and measurable per-frame constraint tests.
2. A fourth ingredient and higher-order relation representation only after a concrete pairwise-vs-triadic fixture demonstrates what is lost.
3. Deterministic image-warp, 2.5D, material-transport and perceptual timing cartridges; optionally model-backed generation behind approval/cost/privacy gates.
4. A versioned adapter to place an accepted alchemy take inside one N0 shot, without changing frozen v1 film documents or N0 render behavior.
5. Render interruption, atomic MP4/receipt handling and measured device performance. The preview currently copies a completed staging file then writes a receipt; if the process is killed between these steps, a partial unreceipted output may remain and must be reconciled explicitly.

## Proof commands

```sh
python -m compileall -q haunted_blender
python -m unittest discover -s tests -v
python -m haunted_blender --help
python -m haunted_blender.alchemy_cli --help
```

The test suite exercises the unchanged N0 path alongside triadic participant refusal, noncommuting sequence orders, frozen source hashes, source mutation refusal, derivative reassociation, snapshot tampering and an actual local FFmpeg output where FFmpeg is installed. A green CI result is a bounded contract check, **not** proof that the visual story is meaningful or that the full filmmaker application is ready.

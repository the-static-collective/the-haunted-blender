# THE HAUNTED BLENDER
**AAA moonshot · experimental nuclear scaffold · separate sister to Haunted Toaster**

A local-first filmmaking studio that turns the media people already own—photographs, Canon RAW originals, Lightroom edits, video, voices, scripts, music and memories—into editable scenes, stories, short films, episodic drama, and eventually virtual productions.

**Current reality:** This repository begins as a scaffold, not a finished filmmaking app or a promise of AAA output. The first launch gate is a *complete three-scene drama* that can be reopened and revised scene by scene. Development branches may exercise narrower components before that gate.

## Product shape

- **Pantry:** content-indexed local archive targeting 10,000+ edited photographs and their CR2/CR3 originals, derivative and sidecar links, rights and optional search. Never overwrite source media.
- **Story:** brief, screenplay, fictional character and continuity graph; distinguish observation, user assertion, inference, fiction and uncertainty.
- **Director:** first-class film → scene → shot → take contracts; stable identity across still-photo, 2.5D, live footage, AI video and 3D realizations.
- **Engine Room:** versioned, capability-declaring renderer adapters; local FFmpeg first, optional validated AgentBroko, Blender 3D and opt-in cloud providers later.
- **Cutting Room:** intentional edit, soundtrack, captions, render caching, independent scene revision, retained execution receipts.
- **Production:** episodic continuity, rights, role-separated collaboration and reversible release approvals.

See [charter](docs/CHARTER.md), [architecture](docs/ARCHITECTURE.md), [roadmap and release gate](docs/ROADMAP.md), and [rights / privacy boundary](docs/SAFETY_AND_RIGHTS.md).

An experimental [Creative Claw take bridge](docs/CREATIVE_CLAW_TAKE_001.md) freezes a synthetic approved still and prompt, then admits a completed video as a separately reviewable candidate for that scene beat. A separate [Take Cut adapter](docs/TAKE_CUT_001.md) can place one explicitly accepted candidate into a silent private cut while other accepted beats remain static.

[Creative Use 001](docs/CREATIVE_USE_001.md) verifies that the same video bytes can enter two separately accepted scene placements with distinct use identities, without assigning either use authority over the source clip or the other scene.

[Time Slice 001](docs/TIME_SLICE_001.md) makes a private, source-linked image whose horizontal strips come from successive moments of one accepted moving take. [Recajggers 001](docs/RECAJGGERS_001.md) records the remaining video, 3D, image and text experiments for later evaluation.

[Door Feedback 001](docs/DOOR_FEEDBACK_001.md) makes an independently accepted moving take leave a recursive, drifting motion trace in a private MP4. It documents a separate live Hydra patch sketch; the MP4 is rendered locally without Hydra.

[Door Dance 001](docs/DOOR_DANCE_001.md) turns that accepted door into a small, repeatable performance: open partway, pause, close a little, pause and open again. Its private MP4 has an exact source-frame edit map and a separate receipt.

## Sister-project boundary

[Haunted Toaster](https://github.com/the-static-collective/the-haunted-toaster) is music/score-first and owns its accepted visual-score, resolved timeline, render and receipt authority. Haunted Blender is story/scene-first and owns its own film project authority. Exchange through explicit versioned adapters only. The old Toaster Lab is a read-only historical experiment, not a deployment target.

## Current scaffold capability

A minimal Python local command door indexes supported media paths and hashes in SQLite, links a RAW to an explicitly provided renderable derivative, creates film/scene/shot manifests, freezes content-addressed snapshots and renders a silent still-image storyboard with FFmpeg. CR2/CR3 are preserved/indexed as source files, **not decoded or treated as directly renderable video frames**. No GUI, Adobe-faithful XMP processing, automatic film direction, character generation, voice performance, remote video models or AgentBroko adapter is implemented.

Python 3.10+; FFmpeg required only for rendering. To run from repository root:

```sh
python -m unittest discover -s tests -v
python -m haunted_blender init ~/HauntedBlender
python -m haunted_blender scan ~/HauntedBlender /path/to/your/photo/archive
python -m haunted_blender stats ~/HauntedBlender
python -m haunted_blender new-film ~/HauntedBlender "The Unopened Letter"
```

Next use the returned film ID with `new-scene`, then the scene ID and asset ID with `add-shot`, followed by `freeze`, `plan`, and `render --out .../film.mp4`. Use `derivative ROOT RAW_ASSET_ID /path/to/edited.jpg` before rendering a CR2-sourced shot.

**Do not commit personal photographs, SQLite libraries, generated projects, render outputs, subject identifiers or EXIF location data to this public repository.** The user-facing application should remain unreleased until its complete-film gate is satisfied.

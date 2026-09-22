# Haunted Blender — nuclear scaffold

**Status:** private-by-default, experimental architectural scaffold. Not a public beta, completed film generator, or canonical replacement for Haunted Toaster.

**Product thesis:** make films from the material people already possess. The first major use case is a photographic archive (including Canon CR2, Lightroom derivatives and XMP sidecars) expanded into editable story/scene/shot productions; the subsequent targets are independent drama, episodic production, documentaries and increasingly sophisticated virtual filmmaking.

This is a standalone project, not an extension of the retired `toaster-lab` repository. No integration into Haunted Toaster's authoritative score/timeline/render/receipt chain is presumed. Render adapters must be explicit and versioned.

## What this scaffold actually does today

- Establishes a local SQLite archive catalog and recursively indexes files without modifying or uploading them. Resume uses path+size+mtime checks; changed/new files are content-hashed with streaming SHA-256; duplicates remain separately addressable sources.
- Accepts `.cr2` and `.cr3` as preserved RAW source files. An optional XMP with the same stem is recorded as an associated sidecar, **not treated as equivalent to an Adobe-rendered image**.
- Records a separate edited JPEG/TIFF/PNG derivative by explicit asset association. RAW is never silently passed off as a usable video frame.
- Creates editable film → scene → shot manifests with explicit source-asset references and creative-intent metadata; freezes a content-addressed snapshot before any render.
- Builds a deterministic FFmpeg still-image render plan. Can render a simple silent, 720p storyboard MP4 from readable image derivatives when FFmpeg is installed; creates success receipts only after a successful render.
- Runs an offline standard-library test suite against catalog and project/render contracts.

**Not implemented:** GUI, actual AI video generation, Lightroom catalog interpretation, faithful Adobe XMP development, camera/actor tracking, film performance generation, speech/audio production, depth estimation, production-grade color management, AgentBroko integration, production-ready archive security, or a general-purpose NLE. See `docs/ROADMAP.md`.

## Quick start (Python 3.10+; FFmpeg only for actual render)

```bash
python -m haunted_blender init ~/HauntedBlender
python -m haunted_blender scan ~/HauntedBlender /path/to/your/photo/archive
python -m haunted_blender stats ~/HauntedBlender
python -m haunted_blender new-film ~/HauntedBlender "The Unopened Letter"
python -m haunted_blender new-scene ~/HauntedBlender <project_id> "The kitchen"
python -m haunted_blender add-shot ~/HauntedBlender <project_id> <scene_id> <asset_id> --seconds 4
python -m haunted_blender freeze ~/HauntedBlender <project_id>
python -m haunted_blender plan ~/HauntedBlender <snapshot_json_path>
python -m haunted_blender render ~/HauntedBlender <snapshot_json_path> --out ~/HauntedBlender/renders/storyboard.mp4
```

A CR2 asset must be associated with a displayable derivative before rendering:

```bash
python -m haunted_blender derivative ~/HauntedBlender <raw_asset_id> /path/to/edited-image.jpg
```

This command indexes the derivative in the original location and explicitly associates it with the RAW source. **Do not upload private photographs into a public source repository.** A photograph's appearance in a proposed story does not establish the subject's identity, consent, or rights.

## Architectural starting points

Read `docs/CHARTER.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, and `docs/SAFETY_AND_RIGHTS.md` before extending the application. In particular, local preview success is not a claim of AAA readiness; filmmaker-facing testing begins only after the release gate is met.

## Developer checks

```bash
python -m unittest discover -s tests -v
python -m compileall -q haunted_blender
```

No external libraries are needed for the scaffold. Real RAW decoding and more sophisticated rendering belong behind versioned capability adapters rather than in the core project model.

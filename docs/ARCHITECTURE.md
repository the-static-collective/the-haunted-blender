# Architecture — bounded engines, durable film identity

```text
  FILES / CAMERA / LIGHTROOM EXPORTS / VIDEO / AUDIO / SCRIPT
                         |
              [INGEST AND RIGHTS GATE]
                         |
          LOCAL CONTENT-IDENTIFIED ASSET VAULT
           source --derivative --sidecar --source rights
                         |
       [DISCOVERY / CURATION / USER CONFIRMATION]
                         |
      STORY GRAPH -> SCENE GRAPH -> SHOT / TAKE GRAPH
                         |
       DETERMINISTIC SNAPSHOT + PRODUCTION PLAN
                         |
             CAPABILITY ROUTER / COST GATE
         +---------------+---------------+
         |               |               |
    STATIC/FFMPEG   VIDEO-GENERATION    BLENDER 3D
     AGENTBROKO     LOCAL OR REMOTE      /COMPOSITOR
         |               |               |
         +---------------+---------------+
                         |
       EDIT / SOUND / CONTINUITY / EXPORT / RECEIPT
                         |
            RENDERED OUTPUT + PROJECT HISTORY
```

## Archival substrate

Support RAW sources (.CR2/.CR3/DNG), edited JPEG/PNG/TIFF, XMP sidecars, audio, motion clips, and later scripts and 3D packages. Keep separate source file identity, bytes digest, file path, derivative relations, edit history, semantic annotations and rights. No destructive transforms. Scan in bounded batches with resumable transactions and stable path records; 10,000 originals may imply much larger actual file counts and storage requirements. Search indexes and thumbnails are replaceable caches, not canon. Archive changes, deleted files and moved locations require reconciliations rather than quiet relinking. Identical bytes do not imply identical rights or context.

The v0 scaffold stores paths and SHA-256 digests in SQLite; it does not automatically copy originals to a managed archive or decode the RAW pixels. More robust per-file transactions, EXIF/camera metadata, Lightroom catalog/XMP interpretation, optional managed encrypted vault, privacy-preserving embeddings and asset-backup workflows are separate implementations.

## The scene contract

Film(id, revisions, creative_intent, rights) → Acts (future) → Scenes(id, question, location, character references, shots) → Shot(id, frame/source refs, direction, duration, performances/takes later) → Render realization(adapter, inputs, output, receipt).

The scene is stable across renderers and visual complexity: a photo with a slow pan and a 3D scene with a dolly shot can instantiate the same editorial beat. The v0 schema permits only static-still shots and records dialogue/direction without pretending they are implemented in the video. Future schema generations must be additive or explicitly migrated; do not reinterpret v1 silently.

Model-generated plans are proposals, never execution truth. Validate and freeze a canonical filmmaker-approved scene/shot snapshot; then derive a bounded render plan; production preview, final export and receipts must cite the same accepted semantic snapshot. Individual engine outputs cannot silently rewrite continuity claims.

## Archive and identity discipline

People, objects and places may have proposed relations to source photographs, but none is promoted into confirmed identity without a user assertion and scoped evidence. A character inspired by a photo is distinguishable from an identified real person. A documentary claim, fictional dialogue, dramatization, reconstruction and AI-generated event have different evidence classes. Recognition and annotation are opt-in and locally processed by default. Users can correct annotations without rewriting source evidence.

## Render-adapter interface (next implementation boundary)

An adapter must expose: id + version; local/remote execution boundary; accepted input modalities; supported motion/camera/voice/quality capabilities; actual cost basis; source sharing policy; deterministic controls and nondeterminism disclosures; output artifacts; cancellation/resume semantics; FFmpeg/codecs or model dependencies; known limitations. A capability router may propose compatible engines but never infer consent to use a paid or remote option. AgentBroko is one possible local-video adapter, **not** assumed present or verified in this scaffold.

## Job queue, revision and failure discipline

Future job identifiers are tied to snapshot, adapter version, explicit settings, input hashes, requested scope and dependency graph. Isolate shot-level failures and resume successful work without rendering unrelated scenes again. A render can be attempted, partial, scoped_complete, refused, or unresolved; receipts must identify the exact scope and missing capabilities. Human approval gates before publication, external generation, biometric identification or irreversible modification.

## Security model

Separate project source files from executable plugins and untrusted model outputs. Sanitize filenames, paths, subprocess arguments and export paths; avoid shell interpolation; sandbox file and model access. Local previews must not automatically sync. Any future remote generation requires a granular media-disclosure preview and affirmative authorization. Source and output licensing and performers' likeness/voice permissions travel with the project.

## Integration seams

- **Haunted Toaster:** exchange media or a proposed visual composition under a dedicated, negotiated adapter; Haunted Toaster's accepted visual-score/timeline authority cannot be bypassed.
- **AgentBroko Video Forge:** adapt its validated local project-spec/FFmpeg pipeline at the versioned render boundary, avoiding a new unverified dependency on the core archive.
- **Blender 3D:** optional engine for authored 3D stages, camera, lighting, object tracking, depth-projected stills, animation and compositing.
- **LOADOUT / ALEX / 3rdi-like ideas:** potentially reuse scoped receipts, evidence distinctions, observer-local perspective and provenance mechanisms after explicit contract review; no presumption that sibling repositories are already integrated.

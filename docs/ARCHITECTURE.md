# Nuclear architecture: durable film, replaceable engines

```
camera / CR2 / Lightroom exports / XMP / audio / script / footage
    → PRIVATE PANTRY: scan, digest, derivative graph, rights, cache
    → DISCOVERY: suggested motifs / user-attested IDs / search
    → STORY GRAPH: film → act → scene → beat → shot → take
    → SNAPSHOT: accepted intent + source identities + revision hash
    → RENDER PLAN: dependency graph + capability/cost/privacy gate
    → ADAPTERS: FFmpeg | verified AgentBroko | Blender 3D | optional AI
    → CUTTING ROOM: preview, editorial/audio/captions, selective rerender
    → OUTPUT: film, retained manifests, bounded receipt, nonclaims
```

## Asset substrate
Local SQLite or equivalent index, stable source IDs, streaming SHA-256, path + observed size/mtime, separate derivative and XMP links, format/camera metadata, rights and author assertions. Scan 10k–100k files with bounded concurrency and per-file resumability. Source bytes remain unmoved and unchanged unless the owner explicitly chooses a managed-copy vault. An XMP sidecar is not proof that any export faithfully reproduces Lightroom rendering. Thumbnails, embeddings and transcodes are disposable caches. Moved/deleted/altered files demand explicit reconciliation. Duplicate bytes do not merge rights or context.

## Project ontology
Film(id, rev, intent) → Scene(id, dramatic_question, characters, location, beats, shots) → Shot(id, source_refs, editorial_intent, time, framing, performance_refs) → Take(id, engine, realized_media, license, receipt) → Cut(ordered take choices, sound, captions). First prototype implements just film/scene/static-shot plus frozen snapshot; every other field is an extension, not a currently working feature. IDs never derive from a renderer's job ID. Existing frozen schemas are not silently rewritten.

## Engine adapter contract
Declare adapter ID and version, installed/available status, local or remote execution, input and output modalities, camera/motion/voice/alpha/3D capability, deterministic controls, hardware/runtime dependencies, actual price basis, privacy disclosures, permission gate, cancellation/resumability, and output/receipt scope. A router may propose choices; it cannot silently spend credits or send personal images to a provider. AgentBroko's described FFmpeg pipeline is a *prospective* adapter pending installed-runtime verification, not an installed dependency.

## Scene-level caching
A shot-render key should include accepted snapshot scope, source and derivative hashes, adapter/runtime version, chosen settings and relevant upstream dependencies. Editing scene 2 invalidates only its descendants and genuinely shared dependents. Locked scenes do not change without explicit filmmaker approval. Retain errors, attempted/partial/scoped-complete status and nonclaims; do not fabricate execution receipts.

## Security and provenance
Separate untrusted project text/media and executable adapters. No shell interpolation; no recursive network sync; external API inputs must receive an exact media-disclosure/price preview and approval. Person/object recognition is opt-in and suggestions cannot become confirmed identity automatically. Source rights, likeness/voice permissions, actor release and documentary/fiction labels travel with assets and exports.

## Cross-project boundary
Haunted Toaster's music-score/timeline authority is untouched. Interoperate by negotiated, versioned media transfer; do not import Toaster Lab's historical parallel authoring/runtime ontology. Adapt LOADOUT/ALEX/3rdi ideas only after checking current contracts; inspiration is not an implemented dependency.

# Nuclear scaffold → AAA production roadmap

This is a dependency graph and release-gate definition, not a time estimate. Architectural ambition may be wide; each executable landing must remain bounded and evidenced.

## N0 — foundation (this artifact)
- Charter, separate identity, module boundaries, privacy/rights principles, film/scene/shot v1, frozen snapshots.
- SQLite local catalog with CR2/CR3, sidecar association, explicit displayable derivatives, incremental scan and file digests.
- Simple deterministic silent storyboard FFmpeg adapter and scoped receipt on successful export only.
- Offline unit tests for ingest/resume, RAW derivative boundaries, freeze/plan/source mutation and invalid edits.
**Exit:** code/tests can be independently inspected; no claim of a user-ready film studio.

## N1 — ingest 10,000 safely
- Real anonymized synthetic archive stress tests at 10k/100k files; interruption, moved folders, duplicates, corrupt assets, symlink/path abuse, disk pressure, power loss, hash collisions as a modeled threat, rights statuses.
- RAW development engine with color-space management; separately import full Lightroom exports and XMP sidecars without claiming Adobe rendering parity.
- Indexed thumbnails and optional local embeddings; background ingestion with bounded CPU/RAM and transparent space estimates.
- Library browser, filters, metadata search, image clustering as non-authoritative suggestions, and manual annotation/consent controls.
**Exit:** 10k-archive benchmark and recovery report on realistic target hardware; originals unchanged.

## N2 — a complete, authorable short drama
- Film/act/scene/beat/shot/take state and screenplay editor; director workspace and visible capability indicators.
- Generate an editable three-scene treatment and storyboards; user confirms real-world assertions, story roles, cast and likeness permissions.
- Shot-level render plans with sound/dialogue and caption workflows; AgentBroko Video Forge proof adapter plus existing FFmpeg fallback.
- Per-scene rerender: editing scene 2 leaves scenes 1 and 3 stable; publishable 5-minute drama with an intelligible beginning, change, and ending.
**Exit:** scene-level regeneration, audio, export, project reopening, and clear provenance all pass end-to-end.

## N3 — professional episodic editing
- Continuity graph; actor and location reference library; consistent edit/take decisions; per-scene render/approval state.
- Multi-track nonlinear editing, mixing, captions, titles, color pipelines, human-reviewable generative passes.
- Rights/performer consent, local/private collaboration roles, resumable partial jobs and structured review.
**Exit:** two linked episodes, repeatable cast/locations and an independent revision without hidden upstream changes.

## N4 — virtual production and composition
- Blender 3D adapter; authored sets, depth/parallax, camera rigs, timing, lighting, character motion, reference image projection and background compositing.
- Local model adapters (hardware-capped) and opt-in paid models for selected shots with preapproved cost ceilings.
- Reusable shot grammar and narrative/visual recomposition, not merely a collection of one-off presets.
**Exit:** one scene can switch between still, hybrid 2.5D, and 3D realization while preserving its narrative identity and provenance.

## N5 — AAA filmmaker workspace and release hardening
- Accessible simple/director/expert interfaces sharing the same schema, durable project migrations, autosave/recovery, dependency isolation, installers, robust import/export, localization/accessibility.
- Full security/privacy review, realistic media-and-rights workflow, offline behavior, performance/thermal/space budgets, edit/render parity and corruption recovery.
- Public documentation, supportable backups, reversible upgrades, meaningful help and clear failure messages.
**Exit:** independent users can create, revise and export a story without developer intervention. This is when public-facing testing can begin, not when a screenshot looks promising.

## Explicit launch gate (before inviting Paula or other filmmakers)

1. End-to-end: photograph or script → editor → three complete scenes → soundtrack/dialogue/captions → watchable MP4 → edit one scene → new MP4.
2. CR2/edited photo workflow on a real sample, without discarding edits, originals or provenance.
3. Interrupted 10k-asset import resumes; no hidden cloud transfers and no unexpected credit expenditure.
4. Project reopens after restart, handles missing/moved media, and can export portable source references and backup manifest.
5. Represented identities/voices/likeness and rights explicitly reviewed; synthetic footage is never mislabeled as original documentary evidence.
6. Tests, packaged builds and user acceptance are separate gates. No fabricated 'AAA ready' status.

## First substantial implementation seam after this scaffold

The **local film pantry**: reliable 10k-image intake, derivatives/sidecars, thumbnail/cache manager, source/asset search and a visually navigable story assembly surface. It is the first part of the actual AAA user experience and unlocks every later filmmaking capability.

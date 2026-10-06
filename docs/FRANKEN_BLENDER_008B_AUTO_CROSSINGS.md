# FRANKEN BLENDER 008b — AUTOMATIC COCKPIT CROSSINGS

008a proved the visual Cockpit.

008b removes the remaining artist-facing engine identities.

## Surface

```text
GROW → KEEP → AWAKEN → PLAY
```

The verbs now cross into the existing engines.

### GROW

```text
Cockpit section
  → DREAMBREEDER create_ecology
  → six deterministic proposal plans
  → six rendered cutout previews
  → six-up contact movie
  → section becomes DREAMING
```

The artist does not type an ecology id.

Repeated GROW resumes the same deterministic ecology and does not create a second family.

### KEEP

The artist chooses one of the six visible numbered futures.

```text
slot 1..6
  → explicit DREAMBREEDER KEEP
  → unrendered descendant
  → section-local PlayDeck-style timing
  → deterministic longer scene
  → scene media bound into Cockpit
  → MOVING
```

The internal proposal id remains in provenance but disappears from the ordinary UI.

KEEP is written before the potentially longer render. If rendering fails, the section remains KEPT and the same button resumes rather than asking for another editorial decision.

### AWAKEN

AWAKEN remains conservative.

```text
MOVING chorus / bridge
  → use its bounded 005 awakening window
  → extract deterministic source frame
  → freeze 006 motion request
  → freeze runtime offer snapshot
  → create cheapest-eligible route
  → build 007 occurrence/per-job budget plan
  → next action = CAPABILITIES
```

008b does **not** submit a provider job.

```text
AUTO AWAKEN != AUTO SUBMIT
ROUTE != PROVIDER AUTHORITY
```

The provider adapter still performs fresh capabilities → quote → submit → status → fetch receipts.

LOCAL ONLY still blocks this entire crossing.

### PLAY

PLAY is still non-editorial.

It assembles currently available section-scene media into:

```text
cockpit-derived/current-cut.mp4
```

using the configured canvas and fps.

If a project audio file is configured, PLAY muxes that audio into the derived preview.

```text
PLAY != KEEP
PREVIEW CUT != RELEASE
```

## One-time engine configuration

The artist should configure boring project-level inputs once:

```bash
python -m haunted_blender.cockpit_engine_cli configure ./film \
  --kit kit.json \
  --source-receipt receipt-real-a \
  --source-receipt receipt-real-b \
  --offers motion-offers.json \
  --lyrics lyrics.json \
  --audio song.mp3
```

Only `--kit` and at least one real `--source-receipt` are required for local GROW / KEEP / PLAY.

`--offers` is required before AWAKEN can prepare a 006/007 route.

Configuration lives at:

```text
cockpit.engine.json
```

Paths are project-local and cannot escape the project root.

## Configurable budgets

Default:

```text
whole occurrence: $0.10
per job:          $0.05
```

represented as USD micros.

These are authorization ceilings, not spend predictions.

The 007 exact-quote gate remains authoritative before any paid submit.

## Section-local scenes

008b deliberately compiles one longer deterministic scene **per Cockpit section** rather than accidentally rendering a whole-song scene for every verse/chorus card.

The Cockpit's section timing becomes a one-gate PlayDeck-compatible local timing object.

Global Full Measure lyric cues, when configured, are shifted into that local section coordinate system before scene growth.

## Source frame

AWAKEN extracts a still from the deterministic scene at the bounded aperture and content-addresses it.

That gives image-to-video providers a concrete source artifact instead of pretending the entire scene video is an image input.

## Visual UX

The 008a browser now consumes:

```text
/api/engine-view/<section>
/api/auto/section/<section>/grow
/api/auto/section/<section>/keep
/api/auto/section/<section>/awaken
/api/auto/play
```

Ordinary use no longer asks for:

- dream ecology ids
- proposal ids
- scene ids
- awakening window ids

The user sees six numbered named futures and chooses a slot.

## Remaining explicit boundary

008b intentionally stops before provider execution.

The next usable crossing is 008c:

```text
prepared 007 plan
  → connected provider adapter
  → capabilities
  → exact quote shown in Cockpit
  → explicit spend permission where needed
  → submit once
  → poll same job
  → fetch candidate
  → candidate board
```

At that point AWAKEN becomes operational end-to-end while preserving the anti-double-spend law.

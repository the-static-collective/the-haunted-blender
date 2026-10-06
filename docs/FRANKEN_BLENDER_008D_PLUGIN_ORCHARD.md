# FRANKEN BLENDER 008d — PLUGIN ORCHARD

008c made provider execution real through local command adapters.

008d composes the installed ChatGPT video apps into the same Motion Organ without
pretending their connector authentication exists inside the local repository.

## The shape

```text
installed video plugins
        ↓
read-only crawler / preflight
        ↓
normalized orchard observation
        ↓
Motion Organ offers
        ↓
free → included → paid routing
        ↓
008c execution plan
        ↓
command adapter
or
content-addressed plugin bridge
```

## Two different truths

A connected ChatGPT app and a local provider API are not the same thing.

```text
CONNECTED PLUGIN != LOCAL CREDENTIAL
PLUGIN PROFILE != LIVE CAPABILITY
BALANCE OBSERVATION != SPEND AUTHORITY
CATALOG MODEL != AFFORDABILITY
```

008d therefore adds `transport: "plugin_bridge"` beside the 008c
`transport: "command"`.

The 007 state machine remains unchanged.

## Provider profiles

The repository now carries a credential-free profile catalog for installed
video-capable apps, including:

- OpenArt
- Higgsfield
- Picsart
- Pollo AI
- Creative Claw
- fal
- Krea
- Everygen
- Runway
- VEED Video Generator
- VideoGen
- Screel

Profiles describe **what connector tools exist** and which role the app belongs
to. They contain no user email, account token, API key, balance, or connector
credential.

Roles distinguish motion generators from finishers / assembled-video systems.

```text
FINISHER != MOTION GENERATOR
```

## Orchard crawl

An external orchestrator — for example ChatGPT with the installed plugins —
collects current facts:

- connected / unavailable
- live account class
- current model catalog
- request-compatible model
- free-generation entitlement
- credit balance
- request-shaped credit cost
- exact USD estimate when available
- durations
- aspect ratios
- input modes

Those facts are normalized into:

```text
haunted-blender/plugin-orchard-observation/v1
```

and ingested with:

```bash
python -m haunted_blender.plugin_orchard_cli ingest ./film crawl.json --install-bridges
```

The snapshot is content-addressed.

A mutable pointer:

```text
cockpit.orchard.latest.json
```

names the current observation and derived Motion Organ offer snapshot.

## No private account data in Git

Live observations are project-local runtime artifacts under `snapshots/`.

The committed provider profile file contains only generic connector/tool names.

The orchard normalization intentionally drops unknown account fields and rejects
credential-like keys from persisted normalized data.

## Routing

A compatible orchard row becomes a normal
`haunted-blender/motion-provider-offers/v1` offer.

The existing 006 ranking remains authoritative:

```text
eligible
  ↓
free
  ↓
included
  ↓
paid
  ↓
observed cost / credit burn
  ↓
stable id
```

An available paid plugin model with **no whole-job USD estimate** is exported as
not currently executable.

It must be refreshed / preflighted before 007 can route into it.

```text
PAID CATALOG ROW != EXACT QUOTE
```

## AWAKEN now prefers the orchard

When `cockpit.orchard.latest.json` exists, automatic AWAKEN uses its frozen
Motion Organ offer snapshot.

The old `motionOffersPath` in `cockpit.engine.json` remains a fallback.

The selected provenance is stored as:

```text
motionOffersSource = plugin-orchard
or
motionOffersSource = engine-config
```

## Free motion-control consequence

Some providers expose free motion-control / recast generations rather than a
generic first-frame image-to-video run.

008d therefore gives every AWAKEN request two project-local source artifacts:

```text
motion-source.png
motion-source.mp4
```

The MP4 is a deterministic trim of exactly the frozen awakening aperture.

That means a motion-control plugin can receive:

- the source still / identity frame
- the exact bounded deterministic driving clip

without widening the edit window.

```text
DRIVING CLIP == FROZEN APERTURE
FREE RECAST != WHOLE-SCENE AUTHORITY
```

## Plugin bridge

When the current 007 attempt uses a plugin bridge, the local driver writes:

```text
cockpit-plugin-bridge/outbox/<call-sha>.json
```

The packet contains:

- frozen provider / model attempt
- request
- source image path
- bounded source video path
- plan SHA
- route SHA
- phase
- the provider profile's suggested connector tools
- the exact normalized result contract expected by 008c

The driver returns:

```text
plugin_bridge_required
```

and **does not advance 007**.

## Resolving a connector call

List pending packets:

```bash
python -m haunted_blender.plugin_bridge_cli pending ./film
```

Inspect one:

```bash
python -m haunted_blender.plugin_bridge_cli show ./film <CALL_SHA>
```

An external plugin orchestrator executes the named connector action and writes a
small normalized result JSON.

Resolve it:

```bash
python -m haunted_blender.plugin_bridge_cli resolve \
  ./film <CALL_SHA> normalized-result.json
```

The next Cockpit drive consumes that exact result and continues the same 007
attempt.

## SUBMIT claim law

Before an external bridge actually performs a SUBMIT, it claims the call:

```bash
python -m haunted_blender.plugin_bridge_cli claim ./film <CALL_SHA>
```

If a claimed SUBMIT has no normalized result:

```text
CLAIMED SUBMIT
      +
NO RESULT
      ↓
RECONCILE_SUBMISSION
      ↓
DO NOT REPLAY
```

This composes with the 008c local submit-intent guard.

A connector crash cannot silently become a second generation.

## FETCH

A normalized FETCH result may provide either:

```json
{"outputUrl": "https://..."}
```

or a project-local:

```json
{"localPath": "..."}
```

HTTPS downloads use a bounded 512 MiB limit and an atomic `.part` → final
rename.

Only after the bytes land does the inherited Motion Organ:

1. probe the MP4
2. hash it
3. admit it
4. record FETCH
5. show it on the candidate board

## The crawler learns every time

Provider-driver phases now produce immutable orchard usage receipts.

The mutable aggregate:

```text
cockpit.orchard.usage.json
```

learns per provider/model:

- attempts
- successes
- failures
- candidate-ready count
- mean observed latency
- human KEEP count
- human decline count

Inspect it:

```bash
python -m haunted_blender.plugin_orchard_cli usage ./film
```

This is empirical creative/runtime history.

It does not silently rewrite provider authority or human taste.

```text
OBSERVED SUCCESS != GUARANTEED SUCCESS
PAST KEEP != FUTURE KEEP
LEARNING != AUTHORITY
```

## Visual Cockpit

An unresolved plugin connector call appears as:

```text
PLUGIN BRIDGE
<profile> / <phase>
<content-addressed packet path>

CHECK BRIDGE
```

A claimed but unresolved SUBMIT instead opens the existing reconciliation door.

## Concrete orchestration loop

```text
GROW
  ↓
KEEP
  ↓
AWAKEN
  ↓
fresh orchard route
  ↓
free/included plugin if eligible
  ↓
bridge packet
  ↓
installed ChatGPT plugin
  ↓
normalized receipt
  ↓
same frozen 007 attempt
  ↓
candidate board
  ↓
KEEP THIS TAKE / TRY NEXT
```

## Remaining seam

008d makes the connector boundary explicit and mechanically resumable.

A future direct adapter can replace a plugin bridge for any provider where the
user intentionally supplies a local/API credential.

No Cockpit or 007 changes are required:

```text
plugin_bridge → command/direct adapter
```

is an adapter substitution, not an architecture rewrite.

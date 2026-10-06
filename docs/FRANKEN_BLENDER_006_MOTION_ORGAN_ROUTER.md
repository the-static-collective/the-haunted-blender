# FRANKEN BLENDER 006 — MOTION ORGAN ROUTER

Status: experimental descendant of KEEP → SCENE → AWAKEN 005.

## The provider swarm becomes one replaceable organ

005 established a bounded awakening aperture.

006 refuses to make any provider part of Blender's core semantics.

```text
AWAKENING WINDOW
      ↓
portable motion request
      ↓
runtime provider-offer snapshot
      ↓
deterministic route plan
      ↓
external provider execution
      ↓
local candidate admission
      ↓
candidate board
      ↓
human KEEP
      ↓
accepted-video resolver
      ↓
005 bounded splice
```

## Runtime economics are data, not code

Provider availability, credits and pricing change.

Therefore Blender contains no permanent claim such as "Krea is cheapest" or
"Screel is free."

A runtime offer snapshot records observations such as:

- provider + model
- available / unavailable
- supported input mode
- supported aspect ratios
- minimum / maximum duration
- spend class: `free | included | paid`
- observed credit cost / balance
- observed USD estimate when paid

The router freezes that snapshot and orders only eligible offers.

### Ranking

```text
free
  before included
    before paid

within free/included:
  lower fraction of observed provider balance consumed first

within paid:
  lower observed USD estimate first

then:
  stable provider / offer identity
```

Credit units are deliberately never compared directly across providers.

```text
1 KREA CREDIT != 1 SCREEL CREDIT
CREDIT UNIT != CROSS-PROVIDER MONEY UNIT
```

## Failure is local

The route contains multiple attempts.

If provider #1 is unavailable after the observation, fails, or produces an ugly
candidate, the film remains intact.

```text
FAILED PROVIDER != FAILED FILM
PROVIDER != EDITOR
ROUTE ORDER != GENERATION
```

Execution stays outside the local Python core because each provider connector has
its own authentication, upload, billing and completion semantics.

## reLATTE-compatible opaque request

006 can project a frozen route into the exact
`relatte.opaque-organ-spec/v0` shape.

The spec carries:

- content-addressed motion request
- source visual address
- desired motion effect
- return address
- provider-opaque claims

It does **not** name the chosen runtime provider in the organ semantics.

That means reLATTE can transport the request without learning Krea, Screel,
VEED, Flow, Creative Claw, or a future provider's internal grammar.

## Candidate admission

After an external provider returns an MP4, Blender:

1. re-verifies the frozen request and route;
2. confirms the selected offer belonged to the route;
3. probes a playable video stream;
4. requires enough duration for the requested window;
5. copies bytes into a private candidate vault;
6. records SHA-256 and reported provider job ID;
7. explicitly does **not** claim provider-job authenticity.

Multiple providers may return candidates for one request.

The candidate board is comparison-only:

```text
BOARD != RANKING
VIEWING != ACCEPTANCE
PROVIDER COUNT != CONSENSUS
```

## Human KEEP

A candidate enters the accepted-motion vault only after explicit filmmaker KEEP.

The accepted witness binds:

- request
- scene
- scene digest
- awakening window
- provider/offer evidence
- candidate receipt
- exact MP4 SHA-256

The generic motion resolver re-verifies all of that before playback.

006 adds a composite accepted-video resolver:

1. try the historical Creative Claw acceptance path unchanged;
2. then try the generic motion-organ acceptance path.

So existing Creative Claw experiments remain valid and future providers gain a
shared door.

## Durable law

```text
REQUEST != GENERATION
OFFER != GUARANTEE
ROUTE != PROVIDER AUTHORITY
CANDIDATE != ACCEPTANCE
HUMAN KEEP != RELEASE
ACCEPTED PROVIDER OUTPUT != PROVIDER AUTHORITY
ACCEPTED MOTION MAY ENTER ONLY ITS FROZEN WINDOW
```

## Next door

007 can make the runtime executor itself instrumented:

```text
route attempt #1
  → provider connector
  → success / refusal / spend receipt
  → if failure, #2
  → ...
  → candidate reservoir
  → comparison contact sheet
```

That executor can remain outside Blender's authority while still returning signed
or content-addressed attempt receipts.

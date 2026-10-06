# FRANKEN BLENDER 008e — ZERO-DOLLAR FILM MILL

008e resets the optimization target:

```text
1. QUANTITY
2. DURATION
3. QUALITY
```

The primary proof is simple: can Haunted Blender cover an entire song with a real playable movie for zero provider credits and zero dollars?

## Supply compass

Provider supply is ranked in this order:

```text
LOCAL REPEATABLE $0
REPEATABLE PROVIDER $0
DAILY FREE
WEEKLY FREE
REGENERATING INCLUDED ALLOWANCE
FINITE FREE CREDIT
ONE-SHOT PROMO
PAID
UNAVAILABLE
```

Within one class: obtainable seconds first, then empirical reliability, then empirical human KEEP rate. Quality is deliberately tertiary.

```text
ONE-SHOT PROMO != REPEATABLE FREE
FINITE CREDIT != INFRASTRUCTURE
```

Inspect the current orchard through this compass:

```bash
python -m haunted_blender.plugin_orchard_cli compass ./film
```

## Zero-Dollar Film Mill

The mill consumes a normal FLOW PANTRY folder and manufactures deterministic short slugs until the target duration is fully covered.

Default recipes:

```text
fit
mirror
reverse
slow
fast
push
pull
misregister
mirror-reverse
soft-loop
```

The first question is not whether this is the final edit. The first question is whether a movie exists for every second of the song.

## One-command SMASH

```bash
python -m haunted_blender.zero_dollar_cli smash \
  "/path/to/225-flow-videos" \
  ./film/zero-dollar \
  --audio ./film/song.mp3
```

The command:

1. hashes and probes every owned video
2. reads the song duration
3. plans enough slugs for 100% coverage
4. reuses ingredients only as explicit deterministic derivatives
5. renders each slug
6. concatenates the cut
7. muxes the song
8. writes a receipt

Outputs include:

```text
flow-pantry.json
zero-dollar.plan.json
slugs/
zero-dollar-current-cut.mp4
zero-dollar-current-cut.receipt.json
```

A fixed target can be used instead of audio:

```bash
python -m haunted_blender.zero_dollar_cli smash ./ingredients ./film/zero-dollar --target-seconds 210
```

## Coverage law

The planner computes ceil(target_seconds / slug_seconds) and trims the final slug to the remaining duration.

A short source may loop internally to feed a longer deterministic derivative.

```text
LOOP != NEW EVIDENCE
DERIVATIVE != NEW SOURCE
```

The receipt records target duration, observed output duration, coverage ratio, slug count, unique source count, recipe diversity, derivative yield, external generations, provider credits, and USD micros.

For the substrate proof:

```text
externalGenerations = 0
providerCredits     = 0
usdMicros           = 0
```

## AI video becomes compost

Candidate 001 and Candidate 002 are not the substrate. They are high-energy ingredients.

A short generated clip can enter an owned-video folder and then be deterministically reused as original fragments, mirrors, reverses, speed variants, pushes, pulls, misregistration, and loops.

```text
AI SECOND != ONE EDITED SECOND
```

The receipt calls the expansion ratio derivative yield.

## The 225 Flow videos

The existing FLOW PANTRY is already the correct ingestion surface:

```text
225 owned clips
      ↓
FLOW PANTRY hashes once
      ↓
008e manufactures slugs
      ↓
song coverage = 100%
      ↓
Toaster / PlayDeck / Blender improve placement later
```

No filename is treated as semantic authority.

## Relationship to the rest of the machine

```text
008e      = guarantee enough film exists
Toaster   = place / time / play with film
PlayDeck  = section gates / ordering / composition
AWAKEN    = mutate selected bounded windows
```

Practical pipeline:

```text
Flow clips + generated clips + local deterministic material
        ↓
008e FULL COVERAGE
        ↓
Toaster one-pass placement
        ↓
PlayDeck structure
        ↓
bounded AWAKEN only where useful
        ↓
quality rises without risking coverage
```

## Orchard facts added by 008e

The plugin orchard can preserve optional supply facts:

```text
availabilityClass
repeatableFree
regeneratingAllowance
resetSeconds
maxRunsPerWindow
secondsPerRun
```

These facts affect the resource compass. They do not silently change 006/007 spending authority.

## Laws

```text
QUANTITY BEFORE DURATION BEFORE QUALITY
COVERAGE BEFORE POLISH
LOCAL ZERO-DOLLAR SUBSTRATE COMES FIRST
ONE-SHOT PROMO != REPEATABLE FREE
FINITE CREDIT != INFRASTRUCTURE
DERIVATIVE != NEW SOURCE
LOOP != NEW EVIDENCE
LOCAL RENDER != PROVIDER GENERATION
FULL COVERAGE != FINAL CUT
AI MUTATION MAY REPLACE WINDOWS LATER
PAST KEEP != FUTURE KEEP
```

Once full zero-dollar coverage exists, the next question changes from 'what should generate the next shot?' to 'which existing seconds are weakest, and what is the cheapest mutation that improves the most film?'

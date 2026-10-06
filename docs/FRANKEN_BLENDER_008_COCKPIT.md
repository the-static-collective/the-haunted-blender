# FRANKEN BLENDER 008 — COCKPIT

Status: experimental usability layer over the green 007b Black Box carrier.

## Governing law

> Complexity underneath. Four verbs on top.

GROW → KEEP → AWAKEN → PLAY

The Cockpit does not replace Blender, Toaster, PlayDeck, DREAMBREEDER, reLATTE,
the Motion Organ Router, Atlas Executor, or Black Box. It exposes a human-scale
surface over their states.

## Persistent project

A Cockpit project records project identity, track identity, ordered sections,
section temperature, dream ecology reference, kept proposal, deterministic scene,
awakening windows, accepted motion addresses, haunt references, current cut, and
unresolved-work counters.

Opening one project therefore restores useful state without asking which command
or JSON file produced it.

## Resume before create

The Cockpit reports:

- unresolved provider jobs
- unborn six-ups
- KEEP'd scenes awaiting deterministic render

The UI should prefer resuming those doors before creating duplicates.

## Section temperature

SLEEPING
DREAMING
KEPT
MOVING
AWAKENING
WITNESSED
ALIVE
HAUNTED

Example:

INTRO      VERSE      CHORUS      BRIDGE      FINAL
ALIVE      ALIVE      AWAKENING   DREAMING    SLEEPING

## LOCAL ONLY

Projects start LOCAL ONLY by default.

When enabled:

- deterministic cutout work remains allowed
- Flow/pantry/local assets remain allowed
- six-up preview remains allowed
- remote AWAKEN is refused

This preserves a complete no-spend filmmaking path.

## Cost light

Visual contract:

- green — deterministic/local/free
- yellow — included allowance
- red — paid

Cockpit consumes already-frozen 006/007 offer and quote evidence rather than
inventing provider prices itself.

## KEEP remains deliberate

Watching does not KEEP. Selection does not KEEP. A dedicated KEEP action changes
the section from DREAMING to KEPT.

## Receipts stay underneath

Ordinary creative view says only things like:

✓ witnessed

Underlying SHA/provenance/Atlas/Black Box evidence remains available on drill-down.

## Command specimen

python -m haunted_blender.cockpit_cli create ./film --project-id up-then-up --title "Up Then Up"
python -m haunted_blender.cockpit_cli add-section ./film verse verse 0 24
python -m haunted_blender.cockpit_cli grow ./film verse dream-ecology:...
python -m haunted_blender.cockpit_cli keep ./film verse dream-proposal:...
python -m haunted_blender.cockpit_cli moving ./film verse kept-scene:...
python -m haunted_blender.cockpit_cli local-only ./film off
python -m haunted_blender.cockpit_cli awaken ./film verse awaken-verse
python -m haunted_blender.cockpit_cli witness ./film verse sha256:...
python -m haunted_blender.cockpit_cli alive ./film verse
python -m haunted_blender.cockpit_cli view ./film
python -m haunted_blender.cockpit_cli resume ./film

## Next door

008a should be the visual surface:

- horizontal living film strip
- section temperature chips
- embedded six-up player
- deliberate KEEP button
- synchronized candidate A/B/C viewer
- cost light
- LOCAL ONLY switch
- resume panel
- receipts drawer

The underlying Cockpit state is now deliberately small enough for a web/desktop UI
to consume directly.

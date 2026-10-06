# FRANKEN BLENDER 008a — VISUAL COCKPIT

Status: experimental visual usability layer over Cockpit 008.

## Why zero-build

The repository had no frontend stack. 008a therefore adds no React/Vite/Next dependency.

The visual surface is served directly by Python:

```bash
python -m haunted_blender.cockpit_web ./film
```

Default URL:

```text
http://127.0.0.1:8765
```

## What is visible

- persistent project title
- LOCAL ONLY switch
- resume counts
- horizontal living film strip
- section temperature chips
- primary six-up / scene player
- synchronized candidate player board
- deliberate GROW / KEEP / AWAKEN / PLAY buttons
- local six-up / scene / candidate attachments
- cost-light labels on candidates
- evidence drawer

## What remains underneath

The visual layer does not replace any authority boundary.

```text
PLAY != KEEP
WATCHING != HISTORY
AWAKEN != ACCEPTANCE
WITNESSED != RELEASE
LOCAL ONLY = NO REMOTE AWAKENING
```

GROW and KEEP still require explicit DREAMBREEDER identities.
AWAKEN still requires an explicit bounded window.
WITNESSED still requires an already accepted content-addressed video identity.

## Local media

Visual media must live inside the Cockpit project root.

The built-in server supports HTTP byte ranges for video playback and seeking.

The browser may upload:

- six-up contact movies
- deterministic scene movies
- candidate provider movies

Uploads are copied under:

```text
cockpit-media/<section>/
```

and never overwrite an existing file.

## Candidate comparison

Candidate videos appear side-by-side.

`Sync candidates` aligns their current times and starts/stops them together.

Double-clicking a candidate promotes only its viewer focus; it does not KEEP or accept it.

## Resume

The left rail surfaces:

- unresolved provider jobs
- unborn six-ups
- kept scenes awaiting deterministic render

The aim is to continue unfinished work before creating more.

## Evidence drawer

Ordinary view remains creative.

A per-section drawer exposes:

- current section state
- bound local media
- project resume counters
- Motion Atlas Black Box lane heads / laws

without forcing provenance into the primary editing surface.

## Security boundary

The web server binds to `127.0.0.1` by default.

Media resolution rejects paths escaping the project root.

LOCAL ONLY starts enabled in normal Cockpit projects and prevents the AWAKEN state transition.

## Next door

008b should remove most manual identity entry by composing the visual verbs directly with the existing engines:

```text
GROW
  -> run DREAMBREEDER + six-up compiler

KEEP
  -> compile kept scene automatically

AWAKEN
  -> build 006 request + 007 route automatically

PLAY
  -> assemble current cut
```

That is the point where the visual Cockpit becomes a true one-pass movie-growing instrument rather than a visual controller over explicit engine identities.

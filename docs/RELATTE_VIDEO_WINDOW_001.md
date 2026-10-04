# reLATTE Video Window 001

**Status:** experimental read-only media resolver over filmmaker-accepted private takes.

> **A clip may exist without being selected. Video Window resolves only after explicit filmmaker acceptance.**

This branch gives Haunted Blender a narrow content-address resolver for moving takes that have already passed the existing local sequence:

```text
accepted Scene Artifact
→ frozen generation request
→ candidate MP4 admitted
→ exact bytes + receipt recorded
→ explicit filmmaker acceptance
→ accepted private take witness
```

Only then may:

```text
sha256:<video digest>
```

resolve to a local read-only Video Window stream.

## Resolver proof

Every resolve revalidates:

- acceptance witness identity and filename hash;
- `distribution_authorized = false`;
- request identity and Scene Artifact lineage;
- deterministic accepted-video path;
- admission receipt digest and fields;
- current MP4 SHA-256;
- a playable video stream via `ffprobe`.

The descriptor deliberately says **private take** and **not distribution authorized**.

```text
ADDRESS != ACCEPTANCE
CANDIDATE != FILMMAKER ACCEPTED TAKE
ACCEPTANCE != PUBLICATION AUTHORIZATION
RESOLUTION REQUIRES BYTE REVERIFICATION
PLAYABLE != RELEASED
```

## Run

From this branch:

```bash
python -m haunted_blender.accepted_video_server ~/HauntedBlender \
  --port 13704 \
  --room-origin http://127.0.0.1:13702
```

Endpoints:

- `GET /v0/status`
- `GET /v0/resolve/<sha256>`
- `GET|HEAD /v0/media/<sha256>`
- one byte range supported for browser seeking

The server binds only to loopback, exposes no arbitrary path endpoint, and has no mutation routes.

## ROroomOM boundary

ROroomOM receives the content address from reLATTE and asks this resolver for the same digest. Haunted Blender owns acceptance and byte verification. ROroomOM owns only the local Video Window encounter.

```text
BLENDER ACCEPTANCE != ROOM AUTHORITY
ROOM PLAYBACK != BLENDER EDIT
VIDEO WINDOW != RELEASE
```

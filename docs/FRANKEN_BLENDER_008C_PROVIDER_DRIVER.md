# FRANKEN BLENDER 008c — PROVIDER DRIVER

008b ended at a prepared 007 plan.

008c connects that immutable execution state machine to replaceable provider
adapters while preserving the spend and editorial boundaries.

## The crossing

```text
prepared 007 plan
  ↓
CAPABILITIES
  ↓
exact QUOTE
  ↓
[explicit one-time approval if paid]
  ↓
SUBMIT ONCE
  ↓
STATUS same vendor job
  ↓
FETCH candidate bytes
  ↓
candidate board
  ↓
HUMAN KEEP or TRY NEXT
  ↓
bounded verified splice
```

## Command adapter transport

008c deliberately does not bake vendor credentials or vendor SDK semantics into
the Blender.

A provider is connected through `cockpit.adapters.json`:

```json
{
  "schema": "haunted-blender/provider-adapters/v1",
  "adapters": [
    {
      "providerId": "my-provider",
      "transport": "command",
      "argv": ["python", "adapters/my_provider.py"],
      "cwd": ".",
      "timeoutSeconds": 180,
      "notes": []
    }
  ]
}
```

The driver uses `subprocess.run(..., shell=False)`.

The adapter receives exactly one JSON object on stdin:

```json
{
  "schema": "haunted-blender/provider-adapter-call/v1",
  "phase": "QUOTE",
  "providerId": "my-provider",
  "payload": {
    "sectionId": "chorus",
    "request": {},
    "attempt": {},
    "sourcePath": "/project/cockpit-derived/chorus/motion-source.png",
    "planSha256": "...",
    "routeSha256": "..."
  }
}
```

and returns one JSON object on stdout:

```json
{
  "schema": "haunted-blender/provider-adapter-result/v1",
  "providerId": "my-provider",
  "phase": "QUOTE",
  "ok": true,
  "result": {}
}
```

Provider-specific secrets remain inside the adapter / environment.

## Phase results

### CAPABILITIES

Adapter result fields:

```text
observedAt
available
inputModes[]
aspectRatios[]
minSeconds
maxSeconds
```

The driver binds provider / offer / model from the frozen route, not from the
adapter response.

### QUOTE

Adapter result fields:

```text
observedAt
exactConfiguration
generatedDurationSeconds
denomination
amount
wholeJobUsdMicros
```

007 still checks:

- generated job covers the edited aperture
- paid work has an exact whole-job USD quote
- per-job budget
- whole-occurrence budget

## Paid approval is a separate witness

A paid quote reaching `SUBMIT` stops.

The Cockpit displays the exact quote and creates a separate:

```text
haunted-blender/provider-spend-approval/v1
```

witness only after the operator presses:

```text
APPROVE & SUBMIT $...
```

The approval binds:

- plan SHA
- attempt number
- provider
- offer
- exact quote receipt SHA
- exact USD micros

It cannot authorize a different quote.

```text
QUOTE != APPROVAL
APPROVAL != SUBMISSION
```

## Crash-safe SUBMIT ONCE

Immediately before the network-facing adapter receives `SUBMIT`, 008c writes a
durable:

```text
provider-submit-intent/v1
```

If the process disappears after the vendor accepts the job but before the
provider submit receipt is committed, restart behavior is:

```text
unresolved submit intent
      ↓
RECONCILE_SUBMISSION
      ↓
DO NOT RESUBMIT
```

The operator supplies the existing vendor job id and submitted-parameter SHA.
That job is then bound into the original 007 attempt and normal STATUS polling
continues.

This closes the most dangerous double-charge seam.

## STATUS

STATUS always binds the previously recorded vendor request id.

```text
running
  → stop this Cockpit drive pass
  → next AWAKEN/POLL checks the same job

completed
  → FETCH

definitively_failed
  → next planned provider

timeout / unresolved
  → STOP_AND_RECONCILE
```

No ambiguous fallthrough exists.

## FETCH

The adapter is given a project-local `outputPath`.

It must materialize the completed MP4 there.

The Blender then independently:

1. probes the MP4
2. hashes the bytes
3. admits it into the Motion Organ candidate store
4. records the 007 FETCH receipt
5. binds it into the visual candidate board

The adapter does not choose the candidate SHA.

## Candidate board

A successfully fetched take produces:

```text
PRESENT
```

The artist can:

### KEEP THIS TAKE

This calls the existing explicit Motion Organ filmmaker acceptance.

Then 005 replaces **only the frozen awakening window** in the deterministic scene.

The section becomes:

```text
WITNESSED
```

ALIVE remains a separate current-cut admission.

### TRY NEXT PROVIDER

This creates an editorial-decline witness.

It does **not** call the provider failed.

```text
EDITORIAL DECLINE != PROVIDER FAILURE
```

The rejected candidate remains evidence and remains visible in the comparison
board while the next frozen route attempt runs.

The artist can later KEEP an earlier candidate.

## CLI

Configure adapters from a JSON file:

```bash
python -m haunted_blender.provider_driver_cli configure ./film adapters.json
```

Drive until the next human/time hinge:

```bash
python -m haunted_blender.provider_driver_cli drive ./film chorus
```

Inspect:

```bash
python -m haunted_blender.provider_driver_cli view ./film chorus
```

Paid approval:

```bash
python -m haunted_blender.provider_driver_cli approve ./film chorus \
  --usd-micros 50000
```

Ambiguous submit reconciliation:

```bash
python -m haunted_blender.provider_driver_cli reconcile ./film chorus \
  --vendor-request-id EXISTING_JOB_ID \
  --submitted-parameter-sha256 0123...
```

Editorial decline / next provider:

```bash
python -m haunted_blender.provider_driver_cli decline ./film chorus
```

Human KEEP:

```bash
python -m haunted_blender.provider_driver_cli accept ./film chorus \
  snapshots/motion-candidates/<candidate>.mp4
```

## Visual Cockpit

008c adds:

```text
GET  /api/provider-view/<section>

POST /api/provider/section/<section>/drive
POST /api/provider/section/<section>/approve
POST /api/provider/section/<section>/reconcile
POST /api/provider/section/<section>/decline
POST /api/provider/section/<section>/accept
```

AWAKEN is now contextual:

```text
MOVING
  AWAKEN
    → prepare + drive

AWAKENING / STATUS
  POLL
    → same vendor job

paid quote
  APPROVE & SUBMIT

PRESENT
  KEEP THIS TAKE
  or TRY NEXT PROVIDER
```

## Boundary

008c supplies a **real provider transport and execution driver**, but intentionally
does not ship credentials or hard-code one vendor's API.

A concrete adapter can be a local Python/Node wrapper around a provider API,
an MCP bridge process, or another authenticated connector as long as it honors
the receipt contract.

The Blender remains provider-replaceable.

## Laws

```text
ADAPTER != AUTHORITY
CAPABILITY BEFORE QUOTE BEFORE SUBMIT
QUOTE != APPROVAL
APPROVAL BINDS ONE EXACT QUOTE
SUBMIT ONCE PER ATTEMPT
UNRESOLVED SUBMIT INTENT => DO NOT RESUBMIT
AMBIGUOUS SUBMISSION => RECONCILE EXISTING JOB
PROVIDER FAILURE != EDITORIAL DECLINE
CANDIDATE != ACCEPTANCE
HUMAN KEEP != RELEASE
ACCEPTED MOTION MAY ENTER ONLY ITS FROZEN WINDOW
```

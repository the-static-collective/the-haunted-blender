# Haunted Blender · CHRONOBODY 001

> **Experimental repo-method registry, not a runtime or canon.** This document addresses frozen *commit versions* of candidate organs. It does not load, merge, promote, execute, render, publish, or grant rights to anything.

The prose is for humans. Only the single fenced `orchard-registry-json` block is machine-readable. Branch names are navigation hints; **the exact 40-character commit is the addressed code identity**. Each entry represents an *experimental candidate* and its declared contract, not a verified installable plugin. Stacked branch ancestry remains unresolved until an explicit adapter/materialization test proves it safe.

```orchard-registry-json
{
  "schema": "haunted-blender/chronobody-registry/v0",
  "mode": "EXPERIMENTAL_DRY_RUN",
  "execution": "DISABLED",
  "organs": [
    {
      "id": "observer.projection",
      "repository": "the-static-collective/the-haunted-blender",
      "branch_hint": "experimental/observer-local-vision-001",
      "commit": "9beec9cce02f9c595386fc39fd7fb79a890434da",
      "state": "INCUBATING",
      "stack_parent_hint": "experimental/door-hinge-dance-001",
      "requires": ["frozen_scene_world", "camera_score"],
      "provides": ["observer_projection_timeline"],
      "adapter": "DECLARED_ONLY"
    },
    {
      "id": "memory.feedback",
      "repository": "the-static-collective/the-haunted-blender",
      "branch_hint": "experimental/memory-feedback-001",
      "commit": "6aca64fdeeb458653e20558c4b23fa89ec622ba7",
      "state": "INCUBATING",
      "stack_parent_hint": "experimental/observer-local-vision-001",
      "requires": ["accepted_moving_take", "observer_projection_timeline", "authored_memory_regions"],
      "provides": ["derived_memory_take"],
      "adapter": "DECLARED_ONLY"
    },
    {
      "id": "object.events",
      "repository": "the-static-collective/the-haunted-blender",
      "branch_hint": "experimental/object-events-v0.1",
      "commit": "f726400c7a001c52ee0f78001d843993118dc0f5",
      "state": "INCUBATING",
      "stack_parent_hint": "experimental/living-object-v0.1",
      "requires": ["frozen_living_object"],
      "provides": ["object_visibility_timeline"],
      "adapter": "DECLARED_ONLY"
    },
    {
      "id": "visual.dream",
      "repository": "the-static-collective/the-haunted-blender",
      "branch_hint": "experimental/visual-dream-door-observer-001",
      "commit": "d219ba3878de1083872e049218edc7ab2b9d6733",
      "state": "INCUBATING",
      "stack_parent_hint": "experimental/door-hinge-dance-001",
      "requires": ["frozen_scene_world", "authored_graph", "camera_score"],
      "provides": ["schematic_dream_take"],
      "adapter": "DECLARED_ONLY"
    }
  ]
}
```

## The first question

Can a *dry-run compiler* discover the declared contract edge `observer_projection_timeline` from `observer.projection` to `memory.feedback`, while refusing to call it a working two-branch renderer? Run `python -m orchard.chronobody --want derived_memory_take --have frozen_scene_world camera_score accepted_moving_take authored_memory_regions`.

Even a complete declared-input plan is only `CANDIDATE`. Exact checkout integrity, branch-ancestry overlap, adapter wiring, actual media/consent, and render validation remain unverified gates. A missing accepted moving take must return `HELD`; competing producers must return `AMBIGUOUS`. See `docs/ORCHARD-001.md`.

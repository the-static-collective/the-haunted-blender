# Spectral Interaction 001 — The Room Tunes to Its Inhabitants

**Status:** approved plan; **implementation not landed by this document**.  
**Target:** next bounded executable slice, independent of the plans branch.  
**Nearest tested inputs:** observer-local camera/projection (#23), memory feedback/strength (#25–#26), two-memory visual competition (#28); independent ORCHARD source-pinning experiment (#27–#29). Confirm each live head, dependency and actual test status before building. Multi-inhabitant attention itself remains an **adapter to implement**, not an existing source of validated shared memory.

## Question

Can two simultaneous inhabitant-local observers, whose memory and attention remain independent, contribute to one **finite, spatially located visual/audio presentation bus**, making cooperation, divergence and withholding perceivable without changing the authored scene or transferring knowledge between inhabitants?

## First vertical slice: two inhabitants, one room, two seconds

- Exactly two inhabitants `A` and `B` in one frozen synthetic room; two authored objects and one possible shared target. Distinct local camera/observer IDs and independent memory-receipt chains.
- 24 logical frames at 12 FPS, with a deterministic 48 kHz stereo two-second sound fixture. A sound fixture is a synthetic audio *render*, not captured speech or measured human hearing.
- Two beats of authored attention: (1) A attends the doorway, B the cup; (2) both attend the doorway. Include one hostile case: B attends the doorway *without ever observing the hidden figure*. B's field may receive a public attention cue; it **must not acquire A's private figure memory**.
- Inputs are mocked or verified observer-local projections and local memory receipts. All signals marked authored or derived; no social/psychological inference, biometric tracking or third-party service call.

## Typed layers — never collapse them

```text
Immutable SceneWorld + per-inhabitant projection/receipt
   ↓ validated encounter and authored attention adapter
InteractionEvent[] (source, fact, time, basis, region, weights)
   ↓ deterministic SpectralMapper v0
SpectralSignature[] (identity, stability, temporal behavior)
   ↓ budgeted SpectrumBus / renderer adapter
24 diagnostic RGB frames + stereo PCM WAV + provenance receipt
```

### 1. InteractionEvent (semantic input)

Each event must carry `frame_index`, `inhabitant_id`, `observer_id`, `world_sha256`, `projection_sha256`, `memory_receipt_sha256` when claiming memory, `fact_id`, `basis` (`present_to_eye`, `memory_residue`, or `attention_cue_only`), normalized `region`, `attention_q` and `memory_q` integer strengths 0–1000. An `attention_cue_only` event cannot provide pixels or act as remembered knowledge. Authored regions locate intended effects, not automatically recognized people. Explicit per-frame inputs are independent of other inhabitants' private receipts.

`shared_attention` is a **derived co-attention relation** only when two validated local attention events address the same authored target at the same frame. `shared_memory` is never inferred from co-attention; any shared-memory mechanic would need its own explicit disclosure/observation contract later. `conflict` describes explicitly authored incompatible proposals, not a decision about which one is true.

### 2. SpectralSignature (control data, not psychology)

The initial mapping has four **visual** channels (`hue`, `saturation`, `opacity`, `flicker_hz`) and four **audio** channels (`center_hz`, `amplitude`, `roughness`, `pan`). Use fixed versioned constants and a documented mapping table. Identity families use an authored or digest-stable hue/frequency seed; avoid `hash()`, runtime randomness, or unverifiable identity inference.

Attention and memory strengths modulate presentation within declared bounds; co-attention can braid two hue/frequency families without changing source identities. Withheld information must not be synthesized as pixels or asserted as an audible event. A score called `conflict` may detune/flicker *only when explicitly authored*; no automatic emotion labels or universal red=anger / dissonance=disagreement claims.

### 3. SpectrumBus (finite shared medium)

Per region/frame, sort emitters by stable ID. Use a **shared visual opacity budget ≤72%** (consistent with the Memory Competition experiment) and keep ≥28% of the present source visible. Allocate over-budget weights via a deterministic order-independent rule. Hue blending must be circular (e.g., weighted unit vectors) so 359° and 1° combine near 0°, not 180°. Treat zero-weight/canceling hues as neutral rather than unstable.

Audio is generated in a separate bounded bus: fixed sample rate and duration, phase-continuous deterministic oscillators, two safe low-level synthetic voices and a hard-mix limiter. Use bounded channel amplitude, finite numeric values and a documented pan rule; never map 0–1000 interaction strengths to unbounded SPL or imply the output is safe for any particular playback volume. Mono compatibility should be checked. Different inhabitant signals remain separately attributable in the receipt even when their audible sum is shared.

### 4. Proof artifacts

One tiny **synthetic** diagnostic frame sequence (e.g., PPMs or MP4 if FFmpeg is present), a stereo PCM WAV, and a sibling JSON receipt. Avoid using or committing any private user photographs, contact data, EXIF or unlicensed clips. Do not require an internet model, Hydra, MEMENTO access or the full game runtime.

Receipt must include: schema/adapter version, exact source-world and per-observer projection/receipt hashes, per-emitter fact/basis/region, mapper constants, visual/audio budgets, sample count/rate, contribution/allocation summaries, output file SHA-256s and the nonclaims below. An output may be `scoped_complete` for the synthetic adapter while the product/game remains experimental.

## Falsifiable test matrix

| Case | Required observation |
| --- | --- |
| Independent attention | A's doorway and B's cup remain distinct signals; changing B does not rewrite A's receipt. |
| Co-attention | Two independently valid doorway attention events change the shared **presentation** compared with the independent case. |
| Private memory | A remembers a figure; B's doorway cue can change the shared spectrum but cannot generate a B figure memory receipt or B-captured figure pixels. |
| Reordered inputs | Reordering two emitters yields bit-identical signatures/diagnostic outputs and receipt digest after canonical sorting. |
| Visual budget | Every RGB pixel respects the shared opacity cap; no image-order-dependent winner. |
| Hue boundary | 359° + 1° produces a hue near 0°, with a defined zero-vector fallback. |
| Audio budget | WAV has expected 96,000 samples per channel, valid stereo PCM encoding, no nonfinite/intermediate overflow, and a hard peak bound. |
| Source protection | SceneWorld, both observer receipts and source media remain byte-identical. |
| Tamper and false promotion | Reject wrong observer/world hashes, future-frame access, unsupported basis, forged memory chain, missing rights or an attempt to relabel an attention cue as eyewitness memory. |

**Pass gate:** a runnable small synthetic proof, all deterministic/hostile tests green, manually inspectable color/audio output, content-addressed receipt, unchanged inputs, and a clear note of any adapter assumptions. If FFmpeg is absent, still generate a small native RGB/PCM proof; do not claim an MP4 rendered.

## Nonclaims

- Spectral hue/frequency is a chosen artistic mapping, not measured emotion, cognition, identity, sensory experience or truth.
- Co-attention is not automatically shared memory, communication, consent or joint observation of the hidden target.
- A room-level visual/audio treatment is derived cinematic presentation, not an event that occurred in the authored world.
- A passing two-inhabitant fixture is not a general social simulator, full game, successful branch composition or production audio engine.

## Implementation branch and later doors

The **plans branch must not contain executable organ code**. Implement on a new `experimental/spectral-interaction-001` branch anchored to the **then-verified appropriate memory/observer lineage**, preferably after reviewing the #28 stack; do not rebase other draft branches just to make planning easier. Create a separate stacked draft PR and link it here after it exists. ORCHARD may later pin the narrow API crossing if it earns one, but a plan is not a Chronobody organ.

After the first proof: shared room-level spectacle with separately proven disclosure; spatialized audio cues; inhabitant-specific hearing/seeing capabilities; speech as a reported attention cue; contradictory memories that coexist without declaring a winner; revisitable room/game loop. None are prerequisites for this first crater.

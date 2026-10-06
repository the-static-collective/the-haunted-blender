PIXEL EXECUTION READY — ADMISSION REQUIRED

This is a new pixel-execution request, not permission inferred from MANGALIZE-003 performed use.
No admission, transformed layer PNG, final page or pixel execution receipt exists for this real composition.

Exact parent: `736dc0eba07b591a7aa25abf3fb92e5ddbaa7a23`.
Exact layout: `fa198528b8454af1cb06ec3dde25c70d57db667f67591ac65234f3d12cebc46a`.
Execution-plan hash: `b3203f8c3d9dfd0b080d149efca9de13fa266675833f08b803187925cbdc6a1a`.
Pixel-execution proposal hash: `2b8c9e795571f6e5ca7116d1046f761611ff2b1f789f4d86c37588561d8dfc2b`.

Requested action authority: `pixelExecution=true` for this exact proposal and implementation witness only.
`motion`, `sound`, `publication`, `externalGeneration`, `characterCasting` remain false.
No new material grants or changes to performed use, earlier custody, quarantine or artifact bytes.

Expected output: PNG, RGBA8, 640×360, initially transparent RGBA (0,0,0,0).
Each intermediate is a separate transparent full-canvas PNG identified by its exact useHash.

| Structural use | Exact useHash | Source → scaled dimensions | Pre/post clipping box | Clipped L/R/T/B |
|---|---|---|---|---|
| poster | `eff6dc9dfeb9fe550c2178f092497b2585366a5568250a996bd8268d1f6d65d3` | [64, 96] → [128, 192] | [32, 48, 160, 240] | 0/0/0/0 |
| cutaway | `ef892ad71e9925fe95fcf073c91309e4c1b8256f5968350a802b7c37a58756e5` | [40, 60] → [96, 144] | [224, 72, 320, 216] | 0/0/0/0 |
| texture | `7c77c2afb7f92d56464bf7c061b66c27eaaeb82c6ddf51ba5900fc515e97ebde` | [64, 96] → [128, 192] | [448, 48, 576, 240] | 0/0/0/0 |

All pre-clipping boxes equal their post-clipping rectangles: no pixels are discarded in the founding case.
Integer x/y millipixels divide by 1000 exactly; fractional final origins refuse.
Target dimension: `max(1, floor((2*d*scaleMillionths+1000000)/2000000))` (positive half-up).
Sampler: Pillow 12.1.1 `Image.Resampling.LANCZOS`, explicit RGBA conversion; changed-size resize premultiplies to RGBa then restores straight RGBA.
Alpha after resize: `floor((2*A*opacityMillionths+1000000)/2000000)`; RGB unchanged. At 0.35, alpha 255→89, 30→11, 10→4.
Order: ascending `(z, useHash)`, not array order. Placement copies straight RGBA into full-canvas layers without a mask; composition is pinned Pillow source-over `Image.alpha_composite`.
Clip: half-open destination box intersected with `[0,0,640,360]`; clipping is not crop authorship.
Encoder: deterministic PNG RGBA8, filter 0, stored zlib blocks ≤65535 bytes, Adler32/CRC32; no optional metadata.
Two identities: exact raw RGBA matrix hash (dimensions/mode/header + NUL + raw bytes), and encoded PNG SHA. Hidden RGB at alpha zero is included in matrix identity.

Implementation/environment witness:
```json
{"implementationSha256":"ae71f5c95baa2b15a92b353275af8781449713a6fdf45166a2af983231f534e6","machine":"x86_64","pillowImageModuleSha256":"3e5ecdcc3e8800749901e61c8108bd3c49063d3ba444fa0b62b0c18af022007f","pillowImagingBinarySha256":"9b24b0f90f620e6e8882e8239081fe244cd4df8f26a5df7773049e4d87779288","pillowVersion":"12.1.1","pythonAbi":"cpython-312","renderer":"mangalize-004/static-raster/v0","system":"Linux"}
```

Byte replay is proven in the declared environment and a fresh process using synthetic authority. Cross-environment equivalence is unproven; any witness mismatch refuses.

Changing the plan, layout, use hashes, source SHAs, sampler, quantization, compositing, background, encoder or implementation witness requires a separate new admission.
Complete particulars and earlier provenance are in `prepared/plan.json`; the human-readable contract is `prepared/TRACE.md`.

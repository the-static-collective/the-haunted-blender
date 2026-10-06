# MANGALIZE-001 — First-class verb event

MANGALIZE names an inspectable transformation event, rather than a `mangalized`
property. This first vertical wraps the existing 008m geometry/quarry machinery
and its 008h Parts Drawer bridge. It does not build another manga engine.

```text
exact LemonPRESS page + handoff
          ↓
MANGALIZE request
          ↓ independent operation admission
origin-preserving Blender page source
          ↓
008m geometry analysis / authorized quarry
          ├─ panel candidate
          ├─ region / quarry crop candidates
          └─ nonsemantic edge-mask candidate
                   ↓ separate reuse + derivative permission
          008h-compatible Parts Drawer
                   ↓
          MANGALIZE execution + return
```

The experiment starts on 008p at
`4e3f098d328a9659d9074852ef7861b7d3078fee`, draft PR #63. The full 008m → 008p
custody chain was inspected. LemonPRESS remains read-only and is pinned to
`88978ff88f9b07a72040976b426b04afc2abd835` (Manga Press 001, draft PR #23).

## Exact foreign witness and the founding refusal

Three original artifacts are copied byte for byte under
`specimens/mangalize-001/lemonpress/`: the page-05 manifest, whole-page PNG, and
its compatibility handoff. `PIN.json` names their original repository paths and
commit. CI compares each copy with that exact upstream commit.

The preserved locator is:

```text
workId: lemonpress:manga-press-synthetic-001
editionId: lemonpress:manga-press-synthetic-001:manga-001
editionHash: e5e4a93558c64eb8ed89f1485e501eccdb9b201abfd5f3d9160414cd22cb6663
issueId: lemonpress:manga-press-synthetic-001:issue-001
pageId: page-05
pageHash: a437492d2ac70155ae145448c442523492dc03b5f66dc401a35cb9ea52bb7dbe
sourceImageSha256: 36a9e87799977330d112f35dfd3567b39eda66a8c418532cf6cc8ef520dd5168
handoffHash: dd9b21083a4781e619e95a9a2f7cfdde728d570e23ea57ec22e868ab5778c42a
```

This is the synthetic carrier page 05, **not** a real Bus Page 5 admission.
The original handoff grants pixel reuse and derivative reuse, but explicitly
denies pixel harvest. The committed refusal request/admission/trace proves that
those two reuse permissions cannot authorize quarry. Requesting authority,
ownership vocabulary, an altered request permission bit, or a fabricated pixel
hash cannot promote that closed door.

The user subsequently approved a **separate harvest-only grant** for this exact
synthetic page and experiment. The committed
[`page-05.harvest-only-grant.json`](../specimens/mangalize-001/lemonpress/separate-authority/page-05.harvest-only-grant.json)
is a Blender-side declaration, not a modified LemonPRESS artifact. Its
`static-collective/mangalize-source-grant/v0` binds all seven locator fields,
original handoff hash, exact upstream repository/commit, and `MANGALIZE-001`.
It names the actual user approval as its external authority reference.

```text
pixelHarvest      true
pixelReuse        false
derivativeReuse   false
publicationReuse  false
motionAdaptation  false
synthesizedSound  false
```

This is an event-specific permission **ceiling**, not a union with the original
handoff's reuse bits. Request/admit/execute/smash cannot manufacture a grant.
The later request asks only for harvest; independent admission allows only
harvest. Original source, handoff, page hash, image SHA, and refused event bytes
remain unchanged. A separate grant event supplies later authority; it never
retroactively authorizes the original refused request.

The actual founding run produces **25 quarantined inspection candidates and no
Parts Drawer**. Its `performedOperations` is only `harvest`: geometry inspection
is a necessary substep of that admitted operation. The trace marks the separate
`analyze` operation as not requested, rather than implying a broader admission. Its return carries no reuse, derivative, publication, motion,
sound, or recursive harvest authority. See the complete
[founding trace](../specimens/mangalize-001/executed/TRACE.md) and preserved
[refusal trace](../specimens/mangalize-001/refusal/TRACE.md).

The optional 008h drawer bridge is executable and tested using a **different,
explicitly fictional fully authorized handoff**, created only in temporary unit
test evidence. That test is not permission for the pinned founding page and
is not a claim that its harvest-only descendants entered creative admission.

## Event grammar

Every canonical record has `verb: MANGALIZE`, a versioned schema, deterministic
local ID, and full content hash. IDs/hashes exclude only their own fields.
Records use 008m's sorted-key compact UTF-8 JSON/SHA-256 convention. Timestamps
are absent from canonical identity. Persistence is create-only; equal replay is
idempotent, conflicting bytes refuse.

| Schema | Binding and consequence |
| --- | --- |
| `static-collective/mangalize-request/v0` | Exact embedded foreign page/handoff, their independent file bindings, complete publication locator, source kind/repository/commit, requested target/operations, supplied/requested grants, continuity, relationship, requesting authority, `requestHash`. |
| `static-collective/mangalize-admission/v0` | Exact request/ancestors, allowed subset/target, effective grants, excluded operations, separate approving/refusing authority, decision, `admissionHash`. A refusal is persisted and cannot execute. |
| `static-collective/mangalize-execution/v0` | Request/admission hashes, versioned existing executor, actual operations and observations, omissions/refusals, descendant graph, precise recipes, all produced file hashes, effective/carried/not-carried grants, `executionHash`. |
| `static-collective/mangalize-return/v0` | Foreign ancestors, local event lineage, exact descendants and files, observations and omissions, bounded grants, verification requirements, compatible foreign-return basis, `returnHash`. |

Only one exact page per request is implemented in 001. Arrays retain composable
foreign ancestry and future event lineage; they do not pretend multi-page
requests already execute. Target names `page` and `panel-sequence` are reserved
vocabulary and refuse admission. `page-quarry` and `parts-drawer` can execute
bounded analysis/harvest; actual drawer production requires separately admitted
reuse and derive. Requests may name stage/render/publish/animate/sound, but these
operations cannot be admitted or executed by 001.

Source hashes and ancestor fields are reconstructed from independent foreign
evidence. Admission is rebuilt from those declarations and the requested subset.
A requesting authority reference cannot serve as the approving reference.
References are inspectable declarations, not cryptographic proof of a person's
rights or identity; no ownership is inferred from the foreign system's name.

## Permission distinction

Foreign pages enter the existing `haunted-blender/page-source/v1` with an explicit
`separate-harvest-reuse/v1` rights mode. This adapter always supplies the harvest
bit; stripping it still fails closed. The source class is `licensed`, indicating
declared scoped permissions, never locally inferred ownership.

| Effective event permissions | What may actually happen |
| --- | --- |
| harvest false, reuse true | Whole-page reuse may be permitted by a separate workflow. Geometry analysis is possible; extraction/quarry refuses. |
| harvest true, reuse false | Controlled analysis/disassembly yields **quarantined inspection** candidates. No reusable Parts Drawer admission. |
| harvest true, reuse true, derive false | Crops remain inspection-only; reuse does not supply derivative permission. |
| harvest true, reuse true, derive true | Candidate assets may enter the existing Parts Drawer. This still grants no staging, rendering, animation, sound, or publication. |

Here harvest means bounded analytical disassembly, including the existing
mechanical crop/mask recipes. `derive` means admitting those outputs as reusable
derivative material. A crop can therefore exist as inspection evidence while
remaining unavailable as creative material. Consumed harvest authority is **not**
recursively carried into every new crop; further harvesting needs its own
source-specific admission. Candidate reuse/derivative permissions retain their
event scope and exact originating declaration.

Pre-existing 008m declarations retain their original explicit legacy
disassembly semantics. They are not silently converted into foreign grants.
The new adapter cannot fall back to that legacy coupled rights model. The 008m
command door also accepts explicit `--pixel-harvest` / `--no-pixel-harvest` and
`--source-root` for independent source bindings.

## Ancestry and exact descendant graph

Blender local IDs coexist with the full LemonPRESS locator. `foreignAncestry`
and `eventLineage` are preserved on page source, analysis, harvest, every asset,
drawer, every drawer row, and return nodes. The event hashes name the actual
operation through which the descendant was produced. No filename supplies its
ancestry, no crop becomes a character, and no source is replaced.

Panel-region crops and masks retain their particular panel candidate as a graph
parent; quarry tiles retain the whole-page parent. Exact recipes and file hashes
distinguish crops, panel candidates, and masks even when pixels happen to repeat.
The return also records source/target structure, new part count, and actual role
changes from a publication page to geometric/material candidates. It provides
future mutation inspection particulars without a value score or Toaster dependency.

Canonical source paths are relative to an explicit source root; descendant
paths are relative to the event root. This prevents host output directories
from changing canonical identity. The existing 008h schema and still/crop/mask
vocabulary are retained. `parts_harvester.resolve_drawer_artifact` resolves and
hash-verifies those event-relative files with an explicit root. Later stages
must make their own admissions before selecting or performing material.

## Command door

Use a fresh output directory. For the original closed handoff, this request
succeeds and admission persists a refusal with nonzero exit status:

```sh
python -m haunted_blender.mangalize_cli request \
  specimens/mangalize-001/lemonpress/works/manga-press-specimen/manga/001/blender-compatibility-handoff.json \
  /tmp/mangalize.request.json \
  --page page-05 \
  --page-manifest specimens/mangalize-001/lemonpress/works/manga-press-specimen/manga/001/pages/page-05.json \
  --evidence-root specimens/mangalize-001/lemonpress \
  --source-commit 88978ff88f9b07a72040976b426b04afc2abd835 \
  --requesting-authority user-task:mangalize-001:request

python -m haunted_blender.mangalize_cli admit \
  /tmp/mangalize.request.json /tmp/mangalize.admission.json \
  --evidence-root specimens/mangalize-001/lemonpress \
  --allow harvest --allow reuse --allow derive \
  --authority-ref local-validator:mangalize-001:refusal-decision
```

An authorized request additionally names `--source-grant PATH`, pointing to the
independently declared, exact-source grant inside the evidence root. For the
founding grant, also select `--operation harvest` and admit only `--allow harvest`.
Then
`execute REQUEST ADMISSION SOURCE_ROOT OUTPUT` persists request, admission,
adapted page source, analysis, 008m harvest assets/report, optional combined
Parts Drawer, execution, return, and `TRACE.md`. The `smash` door takes the same
explicit requesting/admitting references and `--allow` subset and internally
persists the same complete custody chain. A refused smash persists only the
request and refusal admission; it does not fabricate an execution or descendant.

```sh
python -m haunted_blender.mangalize_cli verify \
  /tmp/mangalized/mangalize.request.json \
  /tmp/mangalized/mangalize.admission.json \
  specimens/mangalize-001/lemonpress /tmp/mangalized
```

Verification reconstructs the request from frozen handoff/page/grant bytes,
reconstructs admission, reruns the **existing** geometry/quarry and drawer
algorithms in fresh staging, and compares the complete byte inventory. Mutating
source, handoff, page manifest, request, admission, recipe, descendant, or return
fails verification. It does not trust a persisted claim merely because that
claim has been rehashed. Source evidence remains untouched.

The exact committed founding event can be independently replayed with:

```sh
python -m haunted_blender.mangalize_cli execute \
  specimens/mangalize-001/executed/mangalize.request.json \
  specimens/mangalize-001/executed/mangalize.admission.json \
  specimens/mangalize-001/lemonpress /tmp/mangalize-001-replayed
python -m haunted_blender.mangalize_cli verify \
  specimens/mangalize-001/executed/mangalize.request.json \
  specimens/mangalize-001/executed/mangalize.admission.json \
  specimens/mangalize-001/lemonpress specimens/mangalize-001/executed
```

## Returns and held meanings

`foreignReturnBasis` carries the exact handoff hash, consumed/preserved publication
identities, descendant/renderer identity, file hashes, omissions and mutations
needed by a later LemonPRESS return adapter. Blender neither writes to LemonPRESS
nor emits a house-admitted `manga-performance-return/v0`. This is a quarry event,
not proof that a film exists. House admission and publication remain unchanged.

001 does not implement prose → manga, alternate page composition, issue editing,
panel-semantic understanding, narrative staging, editorial admission, animatic
production, animation, sound synthesis, external providers, or house release.
MANGALIZE and ANIMATE remain distinct verbs. Geometry findings are heuristics,
not semantic panel identities. Rights declarations remain externally asserted.

## Validation

The new suite covers immutable explicit verb artifacts, deterministic request /
admission / cross-directory execution / return replay, foreign/local identities,
closed harvest and quarantined-only states, independent derivative permission,
excluded authority, source retention, real quarry PNGs and 008h drawer rows,
ancestry on every descendant, exact artifact verification, tampered evidence,
unsupported targets, first-class refusal persistence, and readable traces.

The complete inherited suite exposed two FFmpeg 7 cadence issues before this
experiment: setpts left crossfade input frame rate unknown, and timing recipes
lost a final slug frame. Two small production fixes restore explicit FPS after
those transforms and bound a cloned tail with the already declared duration.
Existing real-render tests verify the repairs; no assertions are weakened.

## Founding laws

```text
MANGALIZE IS AN EVENT, NOT A PROPERTY
MANGALIZE != AUTHORIZE
REQUESTED MANGALIZATION != ADMITTED MANGALIZATION
ADMISSION != EXECUTION
EXECUTION != PUBLICATION
HARVEST AUTHORITY != PIXEL REUSE AUTHORITY
PIXEL REUSE != DERIVATIVE AUTHORITY
DERIVATIVE AUTHORITY != PUBLICATION AUTHORITY
QUARRY DESCENDANT RETAINS PUBLICATION ANCESTRY
ADAPTER IDENTITY != SOURCE IDENTITY
FOREIGN ANCESTRY != LOCAL OWNERSHIP
PAGE != PANEL MAP
PANEL MAP != SEMANTIC UNDERSTANDING
HARVESTED ASSET != CHARACTER IDENTITY
DESCENDANT != REPLACEMENT
RETURN != HOUSE ADMISSION
RETURN != PUBLICATION
MANGALIZE != ANIMATE
REFUSAL WAS CORRECT
LATER GRANT != RETROACTIVE AUTHORITY
HARVEST != REUSE
GRANT EVENT != SOURCE MUTATION
```

## Aperture exposed by the founding execution

The exact synthetic page yields one undersegmented panel map, 18 quarry tiles,
and 25 distinct candidate PNGs: one panel, 23 region/quarry crops, and one mask.
Every candidate has exact publication ancestry, local identity, recipe, pixel
hash, and request/admission lineage. Every candidate remains quarantined; the
existing Parts Drawer door correctly refuses this founding harvest.

The broader temporary full-rights test proves a drawer can retain that custody.
A read-only probe also exposed that existing 008h stage proposals reduce a drawer
row to role/kind/path/pixel/source hashes and harvest ID, dropping its full foreign
locator, local asset ID, and event lineage. No stage was performed or changed.

The next aperture exposed by the actual founding event is the quarantined
candidate → separately admitted reusable derivative boundary: can a later,
source-specific reuse/derivative grant open that door while retaining the exact
foreign/local/event custody and the original harvest-only event's closed rights?

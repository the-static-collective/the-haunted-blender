# FRANKEN BLENDER 008n — THE PARTICULAR BECOMES A PERFORMANCE

008n inserts one missing boundary into the paper-film stack:

```text
NARRATIVE PARTICULAR
        ↓
STAGING PROPOSAL
        ↓
EXPLICIT EDITORIAL ADMISSION
        ↓
PERFORMANCE PLAN
        ↓
RETURN RECEIPT
```

The purpose is not to make narrative evidence immutable in every sense. It is to make mutation **visible**.

A source detail may enter a new arrangement. The arrangement may frame it, pace it, juxtapose it, or omit it. The arrangement may not silently rewrite what the source said.

```text
SOURCE FACT
!= INTERPRETATION
!= STAGING
!= RENDERED PERFORMANCE
```

## Founding specimen

The first specimen is Issue **0.022101 — THE BUS THAT JOINED THE BAND**, Page 5:

> A page you can hear.

The source beat names seven detail particulars plus one wide return:

```text
guitar string
loose mug lid
Grace's breath
seat spring
fingers against the seat rail
window edge
Lumi watching the blinker
whole parked interior
```

The same source also establishes three important boundaries:

```text
Every sound has a pictured source.
Nobody appoints the bus conductor.
The blinker appears to land on the newly opened space.
```

008n preserves those as source witness. It does not promote the apparent rhythmic relation into a causal claim.

## Four authority surfaces

### 1. Narrative source

Schema:

```text
haunted-blender/narrative-particular-source/v1
```

Each particular receives a content hash before staging exists.

### 2. Staging proposal

Schema:

```text
haunted-blender/staging-proposal/v1
```

A proposal may choose Paper Director shot vocabulary, timing, framing language, and an interpretation note.

It may not add source or causal authority.

```text
NO CAUSAL AUTHORITY MAY BE SYNTHESIZED BY STAGING
```

The founding refusal test attempts to insert:

```text
the bus conducted the musicians and caused the arrangement
```

and the compiler refuses it.

### 3. Editorial admission

Schema:

```text
haunted-blender/editorial-admission/v1
```

A proposal cannot admit itself. The admission requires an external authority reference and an explicit set of admitted beat ids.

Omitting a staging beat does not erase its source particular.

### 4. Performance plan

Schema:

```text
haunted-blender/particular-performance-plan/v1
```

Only admitted beats cross. Every performed beat retains:

- exact source particular id;
- exact source particular hash;
- exact source text;
- shot type;
- bounded timing;
- staging description;
- interpretation;
- separate source/staging authority labels.

The shot vocabulary is the existing 008j Paper Director vocabulary. 008n does not invent a parallel director.

## Return

Schema:

```text
haunted-blender/particular-performance-return/v1
```

The return receipt records what crossed and which source particular hashes were carried.

```text
RECEIPT != AUTHORITY
PERFORMANCE != RETROACTIVE CANON
```

## Command door

```bash
python -m haunted_blender.narrative_performance_cli smash \
  specimens/008n/bus-page-5-a-page-you-can-hear-001.json \
  /tmp/particular-performance-008n
```

Outputs:

```text
narrative-source.json
staging-proposal.json
editorial-admission.json
particular-performance.plan.json
particular-performance.return.json
```

## Stack consequence

```text
008h  PARTS / HARVEST
008i  MOVING SURFACES
008j  PAPER DIRECTOR
008k  CAST / DIALOGUE
008l  MATERIAL SURFACE
008m  MANGA PAGE / GRAMMAR
008n  PARTICULAR → PROPOSAL → ADMISSION → PERFORMANCE → RETURN
```

008n is the narrative custody seam.

It gives later manga/film loops a way to digest their own descendants while retaining the distinction between inherited source evidence and new staging.

## Founding laws

```text
SOURCE PARTICULAR != STAGING
STAGING PROPOSAL != EDITORIAL ADMISSION
EDITORIAL ADMISSION != SOURCE TRUTH
PERFORMANCE != RETROACTIVE CANON
PARTICULAR MAY ENTER A NEW ARRANGEMENT WITHOUT BEING REWRITTEN
NO CAUSAL AUTHORITY MAY BE SYNTHESIZED BY STAGING
RECEIPT != AUTHORITY
```

## Non-claims

008n does not claim:

- that a staging proposal is true;
- that a rendered association proves causality;
- that a receipt grants source authority;
- that editorial admission changes canon;
- that the current Page 5 staging is the only valid staging;
- that the current specimen is a final animation renderer.

This pass establishes the custody chain that a renderer can consume next.

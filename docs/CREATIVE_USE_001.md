# Creative Use 001 — same bytes, different accepted placements

**Experimental additive branch** on [Take Cut 001](TAKE_CUT_001.md). This adds no generation, remote upload, automatic artistic inference, media mutation or change to N0 / SceneWorld / accepted Scene Artifact authority.

The same clip can appear in different accepted contexts while retaining one byte identity. The clip's SHA-256 is a *material identity*. Each separately accepted placement has a distinct **use identity** bound to its exact Scene Artifact, beat, Creative Claw request, acceptance witness, filmmaker-named role and stated intent. A use receipt does **not** prove its shot has been rendered. Only a separate cut receipt can attest rendered output.

## Local doors

Prepare two already accepted placements of the same MP4 under separate Scene Artifacts. Each must have its own frozen request, admission and acceptance; the source photograph's digest must agree. Then:

```sh
python -m haunted_blender.creative_use_cli record ~/HauntedBlender \
  /private/scene-artifact-one.json /private/take-acceptance-one.json \
  --role single-door-take --intent 'Private one-beat door test'

python -m haunted_blender.creative_use_cli record ~/HauntedBlender \
  /private/scene-artifact-two.json /private/take-acceptance-two.json \
  --role opening-shot --intent 'Opening beat of a longer cut'

python -m haunted_blender.creative_use_cli compare ~/HauntedBlender \
  /private/creative-use-one.json /private/creative-use-two.json
```

`record` recomputes the acceptance and media lineage and freezes a private `creative-use/v0` receipt. `compare` revalidates both receipt chains and freezes a bounded comparison witness only if: (1) the actual clip byte digests are identical; (2) the requests identify the same accepted source frame; (3) the Scene Artifact / beat placements differ; (4) each placement has its own acceptance. Merely calling the same accepted placement by two different roles is refused.

The comparison claims **one media digest, two placements, two use identities**, not two distinct sets of bytes. Removing one derived use receipt cannot mutate the source media, accepted original Scene Artifact or the other use. A future inspector can relate actual take-cut receipts to these uses, but this cartridge does not manufacture an execution receipt, publish media or authorize cross-product reimport. Provider job IDs remain reported inputs, not independently verified provider attestations.

Synthetic actual proof: the same three-second door clip (`b8f804d0…398b`) was accepted as a one-beat private preview and as the opening of a distinct three-beat scene. Distinct `use_id`s and a content-addressed comparison witness were produced without altering the MP4. The exact source paths and private acceptance details remain outside Git.

Verification: `python -m unittest discover -s tests -v`. Tests use synthetic photographs and one locally encoded video. They check distinct uses, same bytes, separate acceptance, parent revalidation, role-only refusal and ancestor survival after a derived use is removed.

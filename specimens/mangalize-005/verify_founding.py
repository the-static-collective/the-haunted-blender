"""Consume the exact external black selection and independently replay 005.

This never issues an admission or selects another ground. Recorded human
authority is an accountable declaration, not a cryptographic signature.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from haunted_blender import mangalize as m, manga_presentation as g

HERE = Path(__file__).resolve().parent
APPROVAL_SHA = 'c14797ef1acd1947e525ee19ba6f7ee196edcdad388bc3c24985a9d913ff582d'
GROUND_HASH = '46cd7ab3f6db99f094ea2418b5a7714f9eef7f1b21e06475a557a72c31e8dc00'
PROPOSAL_HASH = 'b77659b847ae2d5721eb3d35fad22aa36e0de43d16a479c3f6ba1a85f33a3041'
PROJECTION_HASH = 'adf2590208fd815728b3060b2a9c3fdab72272c11182e09b77ff2453b250510a'


def inputs():
    approval = m.read(m.bound_path(HERE, {'path':'authority/user-black-ground-approval.json','sha256':APPROVAL_SHA}))
    value = m.read(HERE / 'prepared/black/ground.json')
    proposal = m.read(HERE / 'prepared/black/proposal.json')
    admission = m.read(HERE / 'admitted-inputs/admission.json')
    parent = proposal['parent']
    m.require(approval['parentCommit'] == '49e9400d3753a6a308317eef8bd5b1fb93cc5322', 'wrong exact parent')
    m.require(value['groundHash'] == GROUND_HASH and proposal['proposalHash'] == PROPOSAL_HASH,
              'unapproved ground/proposal identity')
    for key, expected in [('groundHash',GROUND_HASH),('proposalHash',PROPOSAL_HASH),
            ('parentPixelMatrixHash',parent['pagePixelMatrixHash']),
            ('parentEncodedArtifactSha256',parent['pageEncodedArtifactSha256']),
            ('pixelExecutionHash',parent['executionHash']),('selectedRGBA8',[0,0,0,255]),
            ('output',proposal['output']),('semantics',proposal['semantics']),
            ('implementation',proposal['implementation']),('authority',g.ADMITTED)]:
        m.require(approval[key] == expected, 'approved scope changed: ' + key)
    m.require(value['parameters']['rgba8'] == approval['selectedRGBA8'], 'unapproved color')
    m.bound_path(HERE,approval['preparedTrace'])
    comparison = m.read(HERE / 'prepared/comparison.json')
    g.verify_event('comparison',comparison)
    m.require(approval['comparisonHash'] == comparison['comparisonHash'], 'changed comparison witness')
    row = next(r for r in comparison['candidates'] if r['groundHash'] == GROUND_HASH)
    m.require(approval['observedCandidate'] == row, 'changed diagnostic selection evidence')
    m.require(admission['externalAuthority'] == approval['authorityId'] + ':sha256:' + APPROVAL_SHA,
              'admission not bound to exact external selection')
    roots = [ROOT / 'specimens/mangalize-001/lemonpress',ROOT / 'specimens/mangalize-001/executed',
             ROOT / 'specimens/mangalize-002/released']
    bundles = [{k:m.read(path / (k+'.json')) for k in ('role','placement','admission')}
               for path in sorted((ROOT / 'specimens/mangalize-003/admitted-inputs').iterdir())]
    performed = ROOT / 'specimens/mangalize-003/performed'
    pixels = ROOT / 'specimens/mangalize-004/executed'
    return roots,bundles,performed,pixels,value,proposal,admission


def verify(out=None):
    roots,bundles,performed,pixels,value,proposal,admission = inputs()
    result = g.verify(*roots,bundles,performed,pixels,value,proposal,admission,HERE / 'projected')
    m.require(result == PROJECTION_HASH, 'wrong exact founding projection')
    projection = m.read(HERE / 'projected/projection.json')
    comparison = m.read(HERE / 'prepared/comparison.json')
    row = next(r for r in comparison['candidates'] if r['groundHash'] == GROUND_HASH)
    m.require(projection['observations'] == row['observations'], 'actual projection differs from prospective observations')
    if out is not None:
        out = Path(out)
        replay = g.execute(*roots,bundles,performed,pixels,value,proposal,admission,out)
        m.require(replay['projectionHash'] == result and m.tree_bytes(out) == m.tree_bytes(HERE / 'projected'),
                  'independent founding projection byte mismatch')
    print('EXACT APPROVED BLACK PRESENTATION: PASS — ' + result)
    return result


if __name__ == '__main__':
    verify(sys.argv[1] if len(sys.argv) > 1 else None)

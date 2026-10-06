"""Consume exact user approval and independently replay the founding raster.

No admission is issued here. The recorded human declaration is an accountable
reference, not a cryptographic signature. Foreign environments must refuse.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from haunted_blender import mangalize as m, manga_pixel_execution as px

HERE = Path(__file__).resolve().parent
APPROVAL_SHA = '876bfd7817b671cf122b1a88934a58faaf14cacbc43d1b3be6395afaf926bd79'
PLAN_HASH = 'b3203f8c3d9dfd0b080d149efca9de13fa266675833f08b803187925cbdc6a1a'
PROPOSAL_HASH = '2b8c9e795571f6e5ca7116d1046f761611ff2b1f789f4d86c37588561d8dfc2b'
EXECUTION_HASH = 'c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f'


def inputs():
    approval = m.read(m.bound_path(HERE, {
        'path': 'authority/user-pixel-execution-approval.json', 'sha256': APPROVAL_SHA}))
    plan = m.read(HERE / 'prepared/plan.json')
    proposal = m.read(HERE / 'prepared/proposal.json')
    admission = m.read(HERE / 'admitted-inputs/admission.json')
    m.require(plan['planHash'] == PLAN_HASH and proposal['proposalHash'] == PROPOSAL_HASH,
              'unapproved founding plan/proposal')
    m.require(approval['parentCommit'] == '736dc0eba07b591a7aa25abf3fb92e5ddbaa7a23', 'wrong parent')
    for key, actual in [('layoutHash', plan['layoutHash']), ('executionPlanHash', PLAN_HASH),
                        ('proposalHash', PROPOSAL_HASH), ('useHashes', plan['useHashes']),
                        ('output', plan['output']), ('rasterSemantics', plan['rules']),
                        ('implementation', plan['implementation']), ('authority', px.ADMITTED)]:
        m.require(approval[key] == actual, 'approved scope changed: ' + key)
    geometry = [{k: layer[k] for k in ('useHash', 'assetId', 'artifact', 'sourceRasterDimensions',
                'scaledRasterDimensions', 'destinationBoxBeforeClipping', 'canvasIntersection', 'pixelsClipped')}
                for layer in plan['layers']]
    m.require(approval['approvedGeometry'] == geometry, 'unapproved raster geometry')
    m.bound_path(HERE, approval['preparedTrace'])
    m.require(admission['externalAuthority'] == approval['authorityId'] + ':sha256:' + APPROVAL_SHA,
              'admission not bound to exact human declaration')
    roots = [ROOT / 'specimens/mangalize-001/lemonpress', ROOT / 'specimens/mangalize-001/executed',
             ROOT / 'specimens/mangalize-002/released']
    bundles = [{k: m.read(path / (k + '.json')) for k in ('role', 'placement', 'admission')}
               for path in sorted((ROOT / 'specimens/mangalize-003/admitted-inputs').iterdir())]
    performed = ROOT / 'specimens/mangalize-003/performed'
    return roots, bundles, performed, plan, proposal, admission


def verify(out=None):
    roots, bundles, performed, plan, proposal, admission = inputs()
    result = px.verify(*roots, bundles, performed, plan, proposal, admission, HERE / 'executed')
    m.require(result == EXECUTION_HASH, 'wrong founding execution')
    if out is not None:
        out = Path(out)
        replay = px.execute(*roots, bundles, performed, plan, proposal, admission, out)
        m.require(replay['executionHash'] == result and m.tree_bytes(out) == m.tree_bytes(HERE / 'executed'),
                  'founding pixel replay byte mismatch')
    print('EXACT APPROVED PIXEL EXECUTION: PASS — ' + result)
    return result


if __name__ == '__main__':
    verify(sys.argv[1] if len(sys.argv) > 1 else None)

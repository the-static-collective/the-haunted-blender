"""Verify real scope, exact authority declaration and independently replay 003.

This consumes previously issued admissions; it never creates one. Human
approval is recorded evidence, not a cryptographic identity/signature.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from haunted_blender import mangalize as m, manga_performed_use as use

HERE = Path(__file__).resolve().parent
APPROVAL_SHA = '29bdefaa10ebb2605feaf7e84bb4e821ada3d2fc1848bb31bfed802ccb05ab5b'
LAYOUT_HASH = 'fa198528b8454af1cb06ec3dde25c70d57db667f67591ac65234f3d12cebc46a'


def verify(out=None):
    approval_path = m.bound_path(HERE, {'path': 'authority/user-performed-use-approval.json', 'sha256': APPROVAL_SHA})
    approval = m.read(approval_path)
    m.require(approval['authority'] == use.ADMITTED and approval['motionAdaptation'] is False, 'approval authority exceeds performed use')
    m.require(approval['parentCommit'] == '8b4f7da114e55150dfb564fea171c827bcf8759a', 'wrong historical parent')
    m.bound_path(HERE, approval['preparedTrace'])
    scopes = approval['approvedUses']
    m.require(len(scopes) == 3 and {s['name'] for s in scopes} == {'panel', 'center-crop', 'edge-mask'}, 'wrong exact approved subset')
    bundles = []
    for scope in scopes:
        path = HERE / 'admitted-inputs' / scope['name']
        bundle = {k: m.read(path / (k + '.json')) for k in ('role', 'placement', 'admission')}
        role, placement, admission = (bundle[k] for k in ('role', 'placement', 'admission'))
        m.require(role == m.read(HERE / 'prepared' / scope['name'] / 'role.json') and
                  placement == m.read(HERE / 'prepared' / scope['name'] / 'placement.json'), 'approved proposal bytes changed')
        for key in ('assetId', 'sha256', 'admittedUseId'):
            m.require(role['material'][key] == scope[key], 'approved exact material identity changed')
        m.require(role['roleHash'] == scope['roleProposalHash'] and placement['placementHash'] == scope['placementProposalHash'], 'unapproved proposal hash')
        m.require(role['proposedRole'] == scope['role'] and placement['proposedPlacement'] == scope['placement'], 'unapproved role/transform')
        m.require(admission['externalAuthority'] == approval['authorityId'] + ':sha256:' + APPROVAL_SHA, 'admission is not bound to recorded approval')
        bundles.append(bundle)
    roots = [ROOT / 'specimens/mangalize-001/lemonpress', ROOT / 'specimens/mangalize-001/executed', ROOT / 'specimens/mangalize-002/released']
    result = use.verify(*roots, bundles, HERE / 'performed')
    m.require(result == LAYOUT_HASH, 'wrong founding layout identity')
    if out is not None:
        out = Path(out)
        replay = use.execute(*roots, bundles, out)
        m.require(replay['layoutHash'] == result and m.tree_bytes(out) == m.tree_bytes(HERE / 'performed'), 'founding replay byte mismatch')
    print('EXACT APPROVED COMPOSITION: PASS — ' + result)
    return result


if __name__ == '__main__':
    verify(sys.argv[1] if len(sys.argv) > 1 else None)

"""Prepare exact founding proposals only. No admission, use or layout is minted."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from haunted_blender import mangalize as m, manga_performed_use as use

HERE = Path(__file__).resolve().parent
SOURCE = ROOT / 'specimens/mangalize-001/lemonpress'
ANCESTOR = ROOT / 'specimens/mangalize-001/executed'
RELEASE = ROOT / 'specimens/mangalize-002/released'
SPEC = [
    ('panel', 'page-asset:4730b32b3e6a6a201762cb0c', '674a270d4a1d2aa451d713b19e4889fc2886d4a6d1961f83563f9b16007f92e7', 'poster', 32000, 48000, 10, 2000000, 1000000),
    ('center-crop', 'page-asset:3303923667b99a06c7417376', '0754b290a875411d4ea81e48ee433c841bd00f5627c2a1516cc24a5f24c400a8', 'cutaway', 224000, 72000, 20, 2400000, 1000000),
    ('edge-mask', 'page-asset:a622c44b71a723710826149f', 'f617cc565a42f9028ac77dfc444e398ad5642d956c2a9718d8cc3c2adaad2580', 'texture', 448000, 48000, 30, 2000000, 350000),
]


def prepare(out):
    drawer = use.verified_drawer(SOURCE, ANCESTOR, RELEASE)
    bundles = []
    for name, asset_id, sha, role_name, x, y, z, scale, opacity in SPEC:
        role = use.role_proposal(drawer, asset_id=asset_id, role=role_name,
            rationale='Exact '+name+' pixels proposed for a structural '+role_name+' use; geometry/asset kind only, no depicted identity claim.',
            authority_ref='experiment:MANGALIZE-003:role-proposer')
        m.require(role['material']['sha256'] == sha, 'founding candidate SHA mismatch')
        geometry = {'canvas': {'widthPixels': 640, 'heightPixels': 360, 'origin': 'top-left'},
            'xMilliPixels': x, 'yMilliPixels': y, 'z': z, 'scaleMillionths': scale,
            'rotationMilliDegrees': 0, 'opacityMillionths': opacity, 'anchor': 'top-left',
            'fit': 'native-scale', 'crop': None, 'overflow': 'clip-to-canvas', 'timeRange': None}
        placement = use.placement_proposal(drawer, role, placement=geometry,
            rationale='Authored static placement in one of three separate canvas regions; source pixels remain unchanged.',
            authority_ref='experiment:MANGALIZE-003:placement-proposer')
        m.persist(out / name / 'role.json', role)
        m.persist(out / name / 'placement.json', placement)
        bundles.append({'role': role, 'placement': placement})
    m.persist(out / 'TRACE.md', use.trace(bundles).encode())
    print('PERFORMED USE READY — ADMISSION REQUIRED')
    for bundle in bundles:
        print(bundle['role']['material']['assetId'], bundle['role']['roleHash'], bundle['placement']['placementHash'])


if __name__ == '__main__':
    prepare(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'prepared')

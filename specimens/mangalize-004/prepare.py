"""Prepare the exact #66 pixel plan/proposal. Never issue admission or raster."""
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from haunted_blender import mangalize as m,manga_pixel_execution as px

HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'specimens/mangalize-001/lemonpress'
ANCESTOR=ROOT/'specimens/mangalize-001/executed'
RELEASE=ROOT/'specimens/mangalize-002/released'
COMPOSITION=ROOT/'specimens/mangalize-003/performed'
INPUTS=ROOT/'specimens/mangalize-003/admitted-inputs'
USE_HASHES={
 'eff6dc9dfeb9fe550c2178f092497b2585366a5568250a996bd8268d1f6d65d3',
 'ef892ad71e9925fe95fcf073c91309e4c1b8256f5968350a802b7c37a58756e5',
 '7c77c2afb7f92d56464bf7c061b66c27eaaeb82c6ddf51ba5900fc515e97ebde'}


def prepare(out):
    bundles=[{k:m.read(path/(k+'.json')) for k in ('role','placement','admission')} for path in sorted(INPUTS.iterdir())]
    layout=px.verified_composition(SOURCE,ANCESTOR,RELEASE,bundles,COMPOSITION)
    m.require(layout['layoutHash']=='fa198528b8454af1cb06ec3dde25c70d57db667f67591ac65234f3d12cebc46a','wrong founding layout')
    m.require({r['useHash'] for r in layout['performedUses']}==USE_HASHES,'wrong founding uses')
    plan=px.compile_plan(layout,ANCESTOR,sampler='LANCZOS')
    proposal=px.propose(layout,ANCESTOR,plan,authority_ref='experiment:MANGALIZE-004:pixel-proposer')
    m.persist(out/'plan.json',plan)
    m.persist(out/'proposal.json',proposal)
    m.persist(out/'TRACE.md',px.trace(plan,proposal).encode())
    print('PIXEL EXECUTION READY — ADMISSION REQUIRED')
    print('planHash:',plan['planHash'])
    print('proposalHash:',proposal['proposalHash'])
    return plan,proposal


if __name__=='__main__':
    prepare(Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'prepared')

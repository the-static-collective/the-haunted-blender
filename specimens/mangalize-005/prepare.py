"""Exact #67 candidate analysis. No selection, admission or projection PNG."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from haunted_blender import mangalize as m, manga_presentation as g

HERE = Path(__file__).resolve().parent
PARENT_COMMIT = '49e9400d3753a6a308317eef8bd5b1fb93cc5322'
SOURCE = ROOT / 'specimens/mangalize-001/lemonpress'
ANCESTOR = ROOT / 'specimens/mangalize-001/executed'
RELEASE = ROOT / 'specimens/mangalize-002/released'
PERFORMED = ROOT / 'specimens/mangalize-003/performed'
PIXELS = ROOT / 'specimens/mangalize-004/executed'
INPUTS = ROOT / 'specimens/mangalize-003/admitted-inputs'
COLORS = [('white', [255,255,255,255]), ('black', [0,0,0,255]), ('mid-gray', [128,128,128,255])]
PAGE_MATRIX = 'ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5'
PAGE_ENCODED = '2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74'


def prepare(out):
    out = Path(out)
    g.protect_output(out, (SOURCE, ANCESTOR, RELEASE, PERFORMED, PIXELS))
    bundles = [{k: m.read(path / (k + '.json')) for k in ('role','placement','admission')}
               for path in sorted(INPUTS.iterdir())]
    parent = g.verified_parent(SOURCE, ANCESTOR, RELEASE, bundles, PERFORMED, PIXELS)
    m.require(parent['pagePixelMatrixHash'] == PAGE_MATRIX and parent['pageEncodedArtifactSha256'] == PAGE_ENCODED,
              'wrong founding transparent page')
    m.require(parent['executionHash'] == 'c5adf79d7704c664145c079ea8d57ac0d2ba0ee1b1b40fa24bc38f613f4e5b0f',
              'wrong ancestor pixel execution')
    candidates = []
    for name, rgba8 in COLORS:
        value = g.ground(parent, rgba8, intent='unselected display-contrast candidate; not print stock or page content')
        proposal = g.propose(parent, value, authority_ref='experiment:MANGALIZE-005:ground-proposer')
        candidates.append({'ground':value, 'proposal':proposal})
    comparison = g.compare(parent, PIXELS, candidates)
    lines = ['# MANGALIZE EVENT 005 — CANDIDATE TRACE', '',
        'PRESENTATION GROUND READY — SELECTION / ADMISSION REQUIRED', '',
        'EXACT PARENT', '  PR #67: ' + PARENT_COMMIT, '  execution: ' + parent['executionHash'],
        '  pagePixelMatrixHash: ' + PAGE_MATRIX, '  pageEncodedArtifactSha256: ' + PAGE_ENCODED,
        '  dimensions: 640 × 360 RGBA8; parent remains transparent and byte-identical', '',
        'UNSELECTED CANDIDATES', '  White and black are encoded-channel endpoint probes.',
        '  Mid-gray 128 is the positive-half-up midpoint of encoded 0..255, not linear-light gray.',
        '  Names and listing order confer no preference, print stock or selected ground.']
    for (name, _), candidate in zip(COLORS, candidates):
        value, proposal = candidate['ground'], candidate['proposal']
        measured = next(r['observations'] for r in comparison['candidates'] if r['groundHash'] == value['groundHash'])
        for kind, record in candidate.items():
            m.persist(out / name / (kind + '.json'), record)
        lines.extend(['', '  ' + name, '  rgba8: ' + str(value['parameters']['rgba8']),
            '  groundHash: ' + value['groundHash'], '  proposalHash: ' + proposal['proposalHash'],
            '  prospective matrix: ' + measured['predictedPresentationPixelMatrixHash'],
            '  unique RGB colors: ' + str(measured['resultUniqueRGBColors']),
            '  encoded luma range: ' + str([measured['encodedLuma8']['min'], measured['encodedLuma8']['max']]),
            '  transparency: ' + str(measured['transparencyResolution']),
            '  partial-alpha |luma-ground| histogram: ' + str({i:n for i,n in enumerate(measured['absoluteLumaDifferenceFromGround']['partialAlphaPixelsHistogram']) if n})])
    lines.extend(['', 'NUMERIC OBSERVATION ONLY', '  comparisonHash: ' + comparison['comparisonHash'],
        '  Prospective matrices are ephemeral, never encoded, persisted as images or displayed.',
        '  Only hashes/counts/histograms persist; no 005 projection exists.', '', 'EXACT PRESENTATION RULES',
        '  ' + str(g.semantics()), '', 'IMPLEMENTATION WITNESS', '  ' + str(g.witness()), '',
        'REQUESTED LATER AUTHORITY', '  presentation = true for one exact externally selected proposal',
        '  publication / printAdmission / motion / sound / externalGeneration / characterCasting / sourceMutation = false',
        '', 'UNCHANGED', '  MANGALIZE-001/002/003/004 and the exact transparent founding raster.',
        '  Full LemonPRESS locator and all four event lineages remain bound in every proposal.', '',
        'EXPOSED BOUNDARY', '  Independent ground authorship remains unproven until external selection/admission.',
        '  Numeric contrast observations describe consequences and cannot select their context.'])
    m.persist(out / 'comparison.json', comparison)
    m.persist(out / 'TRACE.md', ('\n'.join(lines)+'\n').encode())
    print('PRESENTATION GROUND READY — SELECTION / ADMISSION REQUIRED')
    print('comparisonHash:', comparison['comparisonHash'])
    for (name, _), candidate in zip(COLORS, candidates):
        print(name, 'ground:', candidate['ground']['groundHash'], 'proposal:', candidate['proposal']['proposalHash'])
    return comparison


if __name__ == '__main__':
    prepare(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'prepared')

"""MANGALIZE-005: presentation context around an unchanged exact RGBA page.

Candidate observation computes prospective matrices in memory, persists only
numeric evidence/hashes, and never encodes, displays or selects a presentation.
Projection execution requires a separate exact external admission.
"""
from __future__ import annotations

import copy
import tempfile
import shutil
from collections import Counter
from pathlib import Path

from . import mangalize as m, manga_atlas as atlas, manga_pixel_execution as px

SCHEMAS = {kind: 'static-collective/' + name + '/v0' for kind, name in {
    'ground': 'manga-presentation-ground', 'proposal': 'manga-presentation-proposal',
    'admission': 'manga-presentation-admission', 'projection': 'manga-presentation-projection',
    'comparison': 'manga-ground-comparison'}.items()}
HASH_KEYS = {kind: kind + 'Hash' for kind in SCHEMAS}
CLOSED = {key: False for key in ('presentation', 'publication', 'printAdmission', 'motion', 'sound',
                              'externalGeneration', 'characterCasting', 'sourceMutation')}
ADMITTED = {**CLOSED, 'presentation': True}
LAWS = ['GROUND != PAGE CONTENT', 'PRESENTATION CONTEXT != SOURCE',
    'CANDIDATE GROUND != SELECTED GROUND', 'GROUND PROPOSAL != PRESENTATION ADMISSION',
    'PRESENTATION != PUBLICATION', 'PRESENTATION != PRINT ADMISSION', 'PRESENTATION != SOURCE MUTATION',
    'PRESENTATION DESCENDANT != PAGE REPLACEMENT', 'GROUNDING != IMAGE ENHANCEMENT',
    'CONTRAST MEASUREMENT != AESTHETIC JUDGMENT', 'MEASUREMENT != SELECTION',
    'VISIBILITY != PIXEL IDENTITY', 'ZERO ALPHA != ABSENT RGB',
    'INVISIBLE CONTRIBUTION TO PROJECTION != ABSENCE FROM PARENT',
    'SAME PAGE + DIFFERENT GROUND = DIFFERENT PRESENTATION',
    'DIFFERENT PRESENTATION != DIFFERENT SOURCE PAGE', 'MULTIPLE PRESENTATIONS MAY SHARE ONE PAGE',
    'DISPLAY GROUND != PRINT STOCK', 'SCREEN WHITE != PAPER WHITE', 'SIMULATED PAPER != PHYSICAL PAPER',
    'ANCESTRY SURVIVES PRESENTATION', 'MATERIAL != PHYSICS CLAIM']


def seal(kind, body):
    body = copy.deepcopy(body)
    body.pop('id', None)
    body.pop(HASH_KEYS[kind], None)
    body.update(schema=SCHEMAS[kind], verb='MANGALIZE', experiment='MANGALIZE-005')
    digest = atlas._hash(body)
    return {**body, 'id': 'manga-presentation-' + kind + ':' + digest[:24], HASH_KEYS[kind]: digest}


def verify_event(kind, record):
    m.require(record.get('schema') == SCHEMAS[kind] and record.get('verb') == 'MANGALIZE'
              and record.get('experiment') == 'MANGALIZE-005', 'wrong presentation event family')
    m.require(record == seal(kind, record), kind + ' identity/hash mismatch')


def semantics():
    inherited = px.rules('LANCZOS')
    return {'operation': 'page source-over opaque solid ground; same dimensions; straight RGBA8',
        'compositing': inherited['compositing'],
        'opaqueChannelArithmetic': 'N=Cs*As+Cg*(255-As); Q=128*N+16384; Cout=((Q>>8)+Q)>>15; Aout=255; As=0 copies ground exactly',
        'quantization': 'Pillow 12.1.1 AlphaComposite.c PRECISION_BITS=7 and SHIFTFORDIV255; pinned native binary',
        'outputMode': 'RGBA8; every output alpha byte 255', 'encoder': inherited['encoder'],
        'pixelMatrixIdentity': inherited['pixelMatrixIdentity'], 'color': inherited['color'],
        'transforms': {'resize': False, 'crop': False, 'blur': False, 'colorCorrection': False,
                       'gammaProfileConversion': False, 'motion': False},
        'measurement': 'encoded-channel luma proxy Y8=floor((2126*R+7152*G+722*B+5000)/10000); absolute Y8 difference from ground; no linearization, perceptual/physical/WCAG claim'}


def witness():
    return {'renderer': 'mangalize-005/solid-ground/v0', 'implementationSha256': atlas._file_sha(Path(__file__)),
            'rasterDependency': px.witness()}


def parent_descriptor(execution):
    px.verify_event('execution', execution)
    m.require(execution['authority'] == px.ADMITTED, 'parent requires separately admitted pixel execution')
    artifact = execution['finalArtifact']
    m.require(artifact['format'] == 'PNG' and artifact['mode'] == 'RGBA', 'parent must be exact RGBA PNG')
    body = {'schema': 'static-collective/manga-presentation-parent/v0',
        'pixelExecution': copy.deepcopy(execution), 'executionHash': execution['executionHash'],
        'pagePixelMatrixHash': artifact['pixelMatrixHash'], 'pageEncodedArtifactSha256': artifact['encodedArtifactSha256'],
        'dimensions': {'width': artifact['width'], 'height': artifact['height']},
        'artifact': {'path': artifact['path'], 'sha256': artifact['encodedArtifactSha256']}}
    return {**body, 'parentHash': atlas._hash(body)}


def validate_parent(parent):
    m.require(parent == parent_descriptor(parent['pixelExecution']), 'parent descriptor differs from pixel execution')


def verified_parent(source_root, ancestor_root, release_root, bundles, performed_root, pixel_root):
    """Independently replay 001 -> 002 -> 003 -> 004, rather than trust claims."""
    records = [m.read(Path(pixel_root) / (kind + '.json')) for kind in ('plan', 'proposal', 'admission')]
    digest = px.verify(source_root, ancestor_root, release_root, bundles, performed_root, *records, pixel_root)
    parent = parent_descriptor(m.read(Path(pixel_root) / 'execution.json'))
    m.require(parent['executionHash'] == digest, 'parent pixel execution mismatch')
    with read_page(pixel_root, parent):
        pass
    return parent


def read_page(pixel_root, parent):
    validate_parent(parent)
    image = px.source_image(pixel_root, parent['artifact'])
    try:
        d = parent['dimensions']
        m.require(image.format == 'PNG' and image.mode == 'RGBA' and getattr(image, 'n_frames', 1) == 1,
                  'presentation requires exact nonanimated RGBA PNG; no conversion')
        m.require(image.size == (d['width'], d['height']), 'parent dimensions changed')
        m.require(px.matrix_hash(image) == parent['pagePixelMatrixHash'], 'parent pixel matrix changed')
    except Exception:
        image.close()
        raise
    return image


def ground(parent, rgba8, *, intent):
    validate_parent(parent)
    m.nonempty(intent)
    m.require(isinstance(rgba8, list) and len(rgba8) == 4 and
              all(type(v) is int and 0 <= v <= 255 for v in rgba8), 'four exact RGBA8 integer channels required')
    m.require(rgba8[3] == 255, 'v0 ground must be opaque; alpha must be 255')
    return seal('ground', {'parentPixelMatrixHash': parent['pagePixelMatrixHash'],
        'parentEncodedArtifactSha256': parent['pageEncodedArtifactSha256'], 'dimensions': parent['dimensions'],
        'kind': 'solid-rgba', 'parameters': {'rgba8': rgba8, 'materialProfile': None},
        'presentationIntent': intent, 'semantics': semantics(), 'implementation': witness(),
        'authority': CLOSED, 'laws': LAWS})


def verify_ground(parent, value):
    verify_event('ground', value)
    expected = ground(parent, value['parameters']['rgba8'], intent=value['presentationIntent'])
    m.require(value == expected, 'ground differs from parent/solid parameters/implementation semantics')


def propose(parent, value, *, authority_ref):
    verify_ground(parent, value)
    m.nonempty(authority_ref)
    return seal('proposal', {'parent': parent, 'groundHash': value['groundHash'],
        'pagePixelMatrixHash': parent['pagePixelMatrixHash'], 'pageEncodedArtifactSha256': parent['pageEncodedArtifactSha256'],
        'pixelExecutionHash': parent['executionHash'], 'output': {'format': 'PNG', 'mode': 'RGBA',
        **parent['dimensions'], 'alpha': 255}, 'semantics': value['semantics'], 'implementation': value['implementation'],
        'proposingAuthority': authority_ref, 'authority': CLOSED, 'laws': LAWS})


def verify_proposal(parent, value, proposal):
    verify_event('proposal', proposal)
    expected = propose(parent, value, authority_ref=proposal['proposingAuthority'])
    m.require(proposal == expected, 'proposal differs from exact page/ground/output semantics')


def admit(parent, value, proposal, *, authority_ref):
    """External declaration factory. Explicit human approval must exist separately."""
    verify_proposal(parent, value, proposal)
    m.nonempty(authority_ref)
    m.require(authority_ref not in (proposal['proposingAuthority'], proposal['proposalHash'], value['groundHash'],
              parent['parentHash'], parent['executionHash']), 'proposal/material/pixel execution cannot self-admit presentation')
    return seal('admission', {'proposalHash': proposal['proposalHash'], 'groundHash': value['groundHash'],
        'pagePixelMatrixHash': parent['pagePixelMatrixHash'], 'pageEncodedArtifactSha256': parent['pageEncodedArtifactSha256'],
        'pixelExecutionHash': parent['executionHash'], 'output': proposal['output'], 'semantics': proposal['semantics'],
        'implementation': proposal['implementation'], 'externalAuthority': authority_ref, 'authority': ADMITTED,
        'nonAuthorities': sorted(key for key, enabled in ADMITTED.items() if not enabled), 'laws': LAWS})


def verify_admission(parent, value, proposal, admission):
    verify_event('admission', admission)
    expected = admit(parent, value, proposal, authority_ref=admission['externalAuthority'])
    m.require(admission == expected, 'presentation admission exceeds exact proposal/ground scope')


def _compose(page, rgba8):
    """Shared inherited engine; no resize, conversion, treatment or encoding."""
    from PIL import Image
    return Image.alpha_composite(Image.new('RGBA', page.size, tuple(rgba8)), page)


def luma8(rgb):
    return px.half_up(2126 * rgb[0] + 7152 * rgb[1] + 722 * rgb[2], 10000)


def observations(page, result, rgba8):
    """Exact numeric descriptions, no aesthetic score, rank or selection."""
    source = page.tobytes()
    output = result.tobytes()
    pairs = Counter((tuple(source[i:i+4]), tuple(output[i:i+4])) for i in range(0, len(source), 4))
    luminance, contrast_all, contrast_visible, contrast_partial = ([0] * 256 for _ in range(4))
    colors = set()
    zero = partial = opaque = hidden = partial_rgb_changed = visible_matching_ground = 0
    ground_luma = luma8(rgba8)
    for (src, dst), count in pairs.items():
        m.require(dst[3] == 255, 'solid-ground projection must be opaque')
        colors.add(dst[:3])
        luma = luma8(dst)
        difference = abs(luma - ground_luma)
        luminance[luma] += count
        contrast_all[difference] += count
        if src[3] == 0:
            zero += count
            hidden += count if src[:3] != (0, 0, 0) else 0
        elif src[3] == 255:
            opaque += count
        else:
            partial += count
            contrast_partial[difference] += count
            partial_rgb_changed += count if src[:3] != dst[:3] else 0
        if src[3] > 0:
            contrast_visible[difference] += count
            visible_matching_ground += count if dst[:3] == tuple(rgba8[:3]) else 0
    return {'predictedPresentationPixelMatrixHash': px.matrix_hash(result),
        'totalPixels': page.width * page.height, 'resultUniqueRGBColors': len(colors),
        'transparencyResolution': {'zeroAlphaParentPixelsReceiveGround': zero,
            'partialAlphaParentPixelsComposited': partial, 'opaqueParentPixels': opaque,
            'hiddenNonzeroRGBAtParentAlphaZero': hidden, 'partialAlphaResultRGBChangedFromSource': partial_rgb_changed,
            'nonzeroAlphaPixelsMatchingGroundRGB': visible_matching_ground},
        'encodedLuma8': {'histogram': luminance, 'min': min(i for i,n in enumerate(luminance) if n),
                        'max': max(i for i,n in enumerate(luminance) if n),
                        'sum': sum(i*n for i,n in enumerate(luminance))},
        'absoluteLumaDifferenceFromGround': {'groundEncodedLuma8': ground_luma, 'allPixelsHistogram': contrast_all,
            'nonzeroAlphaPixelsHistogram': contrast_visible, 'partialAlphaPixelsHistogram': contrast_partial},
        'measurementSemantics': semantics()['measurement']}


def compare(parent, pixel_root, candidates):
    """Unadmitted numeric analysis only: no PNGs, previews or selection."""
    m.require(bool(candidates), 'nonempty explicit candidate set required')
    rows = []
    with read_page(pixel_root, parent) as page:
        for candidate in sorted(candidates, key=lambda c: (c['ground']['groundHash'], c['proposal']['proposalHash'])):
            value, proposal = candidate['ground'], candidate['proposal']
            verify_proposal(parent, value, proposal)
            rgba8 = value['parameters']['rgba8']
            with _compose(page, rgba8) as prospective:
                row = {'rgba8': rgba8, 'groundHash': value['groundHash'], 'proposalHash': proposal['proposalHash'],
                       'observations': observations(page, prospective, rgba8)}
            rows.append(row)
    m.require(len({r['groundHash'] for r in rows}) == len(rows), 'duplicate candidate identity')
    return seal('comparison', {'parent': parent, 'candidates': rows, 'authority': CLOSED,
        'artifactProduction': 'none; ephemeral prospective matrices; numeric evidence only; not a presentation projection',
        'candidateOrdering': 'groundHash then proposalHash lexicographic; identity order only; no ranking', 'laws': LAWS})


def verify_comparison(parent, pixel_root, candidates, comparison):
    verify_event('comparison', comparison)
    m.require(comparison == compare(parent, pixel_root, candidates), 'comparison differs from independent observations')


def project(parent, pixel_root, value, proposal, admission, out):
    """Lower-level raster consequence. Public execute also replays all ancestors."""
    verify_admission(parent, value, proposal, admission)
    out = Path(out).resolve()
    m.require(not out.is_relative_to(Path(pixel_root).resolve()), 'projection cannot mutate parent evidence')
    with read_page(pixel_root, parent) as page, _compose(page, value['parameters']['rgba8']) as result:
        measured = observations(page, result, value['parameters']['rgba8'])
        encoded = px.png_bytes(result)
    m.persist(out / 'presentation.png', encoded)
    import hashlib
    return seal('projection', {'parent': parent, 'groundHash': value['groundHash'], 'proposalHash': proposal['proposalHash'],
        'admissionHash': admission['admissionHash'], 'pagePixelMatrixHash': parent['pagePixelMatrixHash'],
        'pageEncodedArtifactSha256': parent['pageEncodedArtifactSha256'],
        'presentationPixelMatrixHash': measured['predictedPresentationPixelMatrixHash'],
        'presentationEncodedArtifactSha256': hashlib.sha256(encoded).hexdigest(),
        'artifact': {'path': 'presentation.png', **proposal['output'], 'byteLength': len(encoded)},
        'groundRGBA8': value['parameters']['rgba8'], 'semantics': value['semantics'], 'implementation': value['implementation'],
        'observations': measured, 'ancestorReturnBasis': px.return_basis(parent['pixelExecution']),
        'relationship': 'presentation-descendant; not page replacement', 'authority': ADMITTED,
        'semanticNonclaims': parent['pixelExecution']['semanticNonclaims'], 'publicationStateChange': None, 'laws': LAWS})


def protect_output(out, roots):
    out = Path(out).resolve()
    for root in roots:
        m.require(not out.is_relative_to(Path(root).resolve()), 'presentation output cannot mutate ancestor evidence')


def execute(source_root, ancestor_root, release_root, bundles, performed_root, pixel_root,
            value, proposal, admission, out):
    protect_output(out, (source_root, ancestor_root, release_root, performed_root, pixel_root))
    parent = verified_parent(source_root, ancestor_root, release_root, bundles, performed_root, pixel_root)
    out = Path(out).resolve()
    with tempfile.TemporaryDirectory(prefix='manga-ground-') as td:
        candidate = Path(td) / 'event'
        projection = project(parent, pixel_root, value, proposal, admission, candidate)
        for kind, record in (('ground', value), ('proposal', proposal), ('admission', admission), ('projection', projection)):
            m.persist(candidate / (kind + '.json'), record)
        m.persist(candidate / 'TRACE.md', projection_trace(projection).encode())
        if out.exists():
            m.require(m.tree_bytes(out) == m.tree_bytes(candidate), 'projection verification failure: persisted event differs from replay')
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate, out)
    return projection


def verify(source_root, ancestor_root, release_root, bundles, performed_root, pixel_root,
           value, proposal, admission, out):
    m.require(Path(out).is_dir(), 'missing presentation projection')
    return execute(source_root, ancestor_root, release_root, bundles, performed_root, pixel_root,
                   value, proposal, admission, out)['projectionHash']


def projection_trace(projection):
    verify_event('projection', projection)
    return '\n'.join(['# MANGALIZE EVENT 005', '', 'SEPARATELY ADMITTED PRESENTATION',
        '  projectionHash: ' + projection['projectionHash'], '  groundHash: ' + projection['groundHash'],
        '  proposalHash: ' + projection['proposalHash'], '  admissionHash: ' + projection['admissionHash'],
        '  pagePixelMatrixHash: ' + projection['pagePixelMatrixHash'],
        '  pageEncodedArtifactSha256: ' + projection['pageEncodedArtifactSha256'],
        '  presentationPixelMatrixHash: ' + projection['presentationPixelMatrixHash'],
        '  presentationEncodedArtifactSha256: ' + projection['presentationEncodedArtifactSha256'],
        '  groundRGBA8: ' + atlas._stable(projection['groundRGBA8']).decode(), '',
        'PARENT PAGE', '  Remains exact; no replacement or source mutation.', '',
        'PUBLICATION / PRINT / MOTION / SOUND / EXTERNAL GENERATION / CASTING', '  Not admitted.']) + '\n'

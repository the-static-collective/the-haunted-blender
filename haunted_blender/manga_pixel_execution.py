"""MANGALIZE-004: separately admitted, environment-bound static raster custody.

Planning decodes exact source headers, but does not resize/composite/encode.
Execution consumes an external declaration. It never infers render authority.
"""
from __future__ import annotations

import binascii
import copy
import hashlib
import io
import platform
import shutil
import struct
import sys
import tempfile
from pathlib import Path

from . import mangalize as m, manga_atlas as atlas, manga_performed_use as use

SCHEMAS = {k: 'static-collective/manga-pixel-execution' + suffix + '/v0' for k, suffix in {
    'plan': '-plan', 'proposal': '-proposal', 'admission': '-admission', 'execution': ''}.items()}
HASH_KEYS = {k: k + 'Hash' for k in SCHEMAS}
CLOSED = {k: False for k in ('pixelExecution', 'motion', 'sound', 'publication', 'externalGeneration', 'characterCasting')}
ADMITTED = {**CLOSED, 'pixelExecution': True}
LAWS = ['PERFORMED USE != PIXEL EXECUTION', 'PIXEL PLAN != PIXEL EXECUTION',
    'AUTHORED COORDINATE != IMPLEMENTATION FLOAT', 'QUANTIZATION MUST BE DECLARED',
    'SCALE VALUE != TARGET PIXEL DIMENSIONS', 'TARGET DIMENSIONS REQUIRE A DECLARED QUANTIZATION RULE',
    'SAMPLING KERNEL IS PART OF THE TRANSFORM', 'OPACITY != ALPHA BYTE UNTIL QUANTIZED',
    'Z ORDER != ARRAY ORDER', 'CLIPPING != CROP AUTHORSHIP', 'PIXEL CONTRIBUTION RETAINS USE IDENTITY',
    'SAME PIXELS != SAME ENCODED FILE', 'VISIBLE ROLE != DEPICTED IDENTITY', 'RASTERIZATION != RECOGNITION',
    'STATIC RASTER != VIDEO', 'PAGE RENDER != ANIMATION', 'ONE PAGE != ONE-FRAME VIDEO',
    'PIXEL EXECUTION != PUBLICATION', 'RENDERED PAGE EXISTS != HOUSE PUBLICATION', 'ANCESTRY SURVIVES RASTERIZATION']
MAX_PIXELS = 16777216


def seal(kind, body):
    body = copy.deepcopy(body)
    body.pop('id', None)
    body.pop(HASH_KEYS[kind], None)
    body.update(schema=SCHEMAS[kind], verb='MANGALIZE', experiment='MANGALIZE-004')
    digest = atlas._hash(body)
    return {**body, 'id': 'manga-pixel-' + kind + ':' + digest[:24], HASH_KEYS[kind]: digest}


def verify_event(kind, record):
    m.require(record.get('schema') == SCHEMAS[kind] and record.get('verb') == 'MANGALIZE' and record.get('experiment') == 'MANGALIZE-004', 'wrong pixel event family')
    m.require(record == seal(kind, record), kind + ' identity/hash mismatch')


def witness():
    from PIL import Image, __version__
    m.require(__version__ == '12.1.1', 'canonical pixel execution requires Pillow 12.1.1')
    return {'renderer': 'mangalize-004/static-raster/v0', 'implementationSha256': atlas._file_sha(Path(__file__)),
        'pillowVersion': __version__, 'pillowImageModuleSha256': atlas._file_sha(Path(Image.__file__)),
        'pillowImagingBinarySha256': atlas._file_sha(Path(Image.core.__file__)),
        'pythonAbi': sys.implementation.cache_tag, 'system': platform.system(), 'machine': platform.machine()}


def half_up(numerator, denominator=1000000):
    m.require(type(numerator) is int and numerator >= 0 and type(denominator) is int and denominator > 0, 'positive integer half-up operands required')
    return (2 * numerator + denominator) // (2 * denominator)


def source_image(artifact_root, artifact):
    """Decode one byte snapshot that itself matches the frozen source SHA."""
    from PIL import Image
    data = m.bound_path(artifact_root, artifact).read_bytes()
    m.require(hashlib.sha256(data).hexdigest() == artifact['sha256'], 'source changed while binding exact bytes')
    return Image.open(io.BytesIO(data))


def raster_size(width, height, scale):
    dims = [max(1, half_up(value * scale)) for value in (width, height)]
    m.require(dims[0] * dims[1] <= MAX_PIXELS and max(dims) <= 16384, 'scaled raster exceeds v0 bounds')
    return dims


def clipping(x, y, width, height, canvas_width, canvas_height):
    # Half-open pixel-edge rectangles; empty intersections have zero extent.
    left, top = min(canvas_width, max(0, x)), min(canvas_height, max(0, y))
    right, bottom = max(left, min(canvas_width, x + width)), max(top, min(canvas_height, y + height))
    return {'destinationBoxBeforeClipping': [x, y, x + width, y + height],
        'canvasIntersection': [left, top, right, bottom],
        'pixelsClipped': {'left': min(width, max(0, -x)), 'right': min(width, max(0, x + width - canvas_width)),
            'top': min(height, max(0, -y)), 'bottom': min(height, max(0, y + height - canvas_height))},
        'finalCompositedRectangle': [left, top, right, bottom]}


def rules(sampler):
    m.require(sampler in ('LANCZOS', 'NEAREST'), 'unsupported sampling kernel')
    return {'ordering': ['z-ascending', 'useHash-lexicographic-ascending'],
        'coordinates': 'x/y millipixels divisible by 1000 only; exact integer division; fractional origins refuse',
        'scale': 'max(1, floor((2*sourceDimension*scaleMillionths+1000000)/2000000)); positive half-up',
        'rotation': 'zero only; nonzero refuses', 'fit': 'native-scale; no crop or time range',
        'sampling': {'kernel': sampler, 'enum': 1 if sampler == 'LANCZOS' else 0,
            'conversion': 'Pillow Image.convert(RGBA); no ICC/gamma transform; nonanimated PNG only',
            'resize': 'Pillow Image.resize(targetSize, enum, box=None, reducing_gap=None)',
            'resizeAlpha': 'unchanged dimensions: copy RGBA; otherwise straight RGBA -> premultiplied RGBa -> resize -> straight RGBA' if sampler == 'LANCZOS' else 'straight RGBA nearest channel sampling'},
        'opacity': 'A_out=floor((2*A_in*opacityMillionths+1000000)/2000000); RGB unchanged after resize; straight RGBA',
        'compositing': 'Pillow Image.alpha_composite(destinationRGBA, sourceRGBA); source-over; straight 8-bit RGBA input/output; pinned imaging-binary integer arithmetic/rounding',
        'placement': 'copy clipped straight RGBA onto transparent full-canvas layer via paste without mask, not an additional blend',
        'clipping': 'intersection of half-open scaled destination box with [0,0,width,height]; no source crop authorship',
        'background': {'reason': 'layout has no authored background', 'mode': 'RGBA', 'rgba': [0, 0, 0, 0]},
        'color': '8-bit RGBA; preserve encoded RGB channel values; no linear-light, profile or gamma conversion',
        'encoder': 'png-rgba-unfiltered-stored/v0: PNG signature; IHDR RGBA8; one IDAT; row filter 0; zlib 0x7801 stored blocks <=65535; Adler32; IEND; CRC32; no metadata',
        'pixelMatrixIdentity': 'SHA256(canonical UTF-8 JSON {schema:static-collective/rgba-pixel-matrix/v0,width,height,mode:RGBA} + NUL + row-major RGBA8 bytes)',
        'bounds': {'maxRasterPixels': MAX_PIXELS, 'maxDimension': 16384}}


def compile_plan(layout, artifact_root, *, sampler='LANCZOS'):
    """Header inspection and integer recipes only. No founding pixels rendered."""
    from PIL import Image
    use.verify_event('layout', layout)
    m.require(layout['authority'] == use.ADMITTED and layout['renderedArtifacts'] == [], 'expected admitted unrendered static composition')
    canvas = layout['canvas']
    width, height = canvas['widthPixels'], canvas['heightPixels']
    m.require(width * height <= MAX_PIXELS, 'canvas exceeds v0 bounds')
    m.require('background' not in layout and 'background' not in canvas, 'v0 requires absent authored background; cannot replace an authored one')
    policy = rules(sampler)
    layers = []
    for record in sorted(layout['performedUses'], key=lambda r: (r['placement']['z'], r['useHash'])):
        use.verify_event('use', record)
        m.require(record['authority'] == use.ADMITTED and record['semanticNonclaims'] == use.NONCLAIMS, 'unexpected use authority/semantic claim')
        p = record['placement']
        use.validate_placement(p)
        m.require(p['canvas'] == canvas and p['rotationMilliDegrees'] == 0, 'v0 requires same canvas and zero rotation')
        m.require(p['xMilliPixels'] % 1000 == 0 and p['yMilliPixels'] % 1000 == 0, 'fractional raster origins refuse')
        mat = record['material']
        m.require(mat['sha256'] == mat['artifact']['sha256'] and record['effectivePermissions'] == mat['permissionCeiling'], 'material identity/ceiling mismatch')
        m.grants(record['effectivePermissions'])
        m.require(record['effectivePermissions']['pixelReuse'] and record['effectivePermissions']['derivativeReuse'], 'no material reuse/derivation ceiling')
        with source_image(artifact_root, mat['artifact']) as im:
            m.require(im.format == 'PNG' and getattr(im, 'n_frames', 1) == 1 and im.mode in ('RGB', 'RGBA', 'L', 'LA'), 'v0 requires one nonanimated PNG in a declared supported mode')
            source_size, source_mode = list(im.size), im.mode
        scaled = raster_size(*source_size, p['scaleMillionths'])
        x, y = p['xMilliPixels'] // 1000, p['yMilliPixels'] // 1000
        layers.append({'useHash': record['useHash'], 'useId': record['id'], 'admission003Hash': record['admissionHash'],
            'roleProposalHash': record['roleProposalHash'], 'placementProposalHash': record['placementProposalHash'],
            'assetId': mat['assetId'], 'admittedUseId': mat['admittedUseId'], 'artifact': mat['artifact'],
            'sourceImageSha256': record['provenance']['artifact']['sourceSha256'], 'provenance': record['provenance'],
            'performedRole': record['performedRole'], 'sourceMode': source_mode, 'sourceRasterDimensions': source_size,
            'scaledRasterDimensions': scaled, 'scaleMillionths': p['scaleMillionths'], 'opacityMillionths': p['opacityMillionths'],
            'xPixels': x, 'yPixels': y, 'z': p['z'], **clipping(x, y, *scaled, width, height)})
    m.require(bool(layers) and len({r['useHash'] for r in layers}) == len(layers), 'nonempty unique use identities required')
    # Layout identity binds its array; pixel ordering independently uses z/hash.
    return seal('plan', {'layoutHash': layout['layoutHash'], 'layoutId': layout['id'], 'canvas': canvas,
        'useHashes': sorted(r['useHash'] for r in layers), 'layers': layers, 'rules': policy, 'implementation': witness(),
        'output': {'format': 'PNG', 'mode': 'RGBA', 'width': width, 'height': height}, 'authority': CLOSED,
        'semanticNonclaims': use.NONCLAIMS, 'laws': LAWS})


def verify_plan(layout, artifact_root, plan):
    verify_event('plan', plan)
    m.require(plan == compile_plan(layout, artifact_root, sampler=plan['rules']['sampling']['kernel']), 'plan differs from independent source/layout/environment reconstruction')


def propose(layout, artifact_root, plan, *, authority_ref):
    verify_plan(layout, artifact_root, plan)
    m.nonempty(authority_ref)
    return seal('proposal', {'layoutHash': layout['layoutHash'], 'planHash': plan['planHash'], 'useHashes': plan['useHashes'],
        'rasterSemantics': plan['rules'], 'implementation': plan['implementation'], 'output': plan['output'],
        'proposingAuthority': authority_ref, 'authority': CLOSED, 'semanticNonclaims': use.NONCLAIMS, 'laws': LAWS})


def verify_proposal(layout, artifact_root, plan, proposal):
    verify_event('proposal', proposal)
    m.require(proposal == propose(layout, artifact_root, plan, authority_ref=proposal['proposingAuthority']), 'proposal differs from exact pixel plan')


def admit(layout, artifact_root, plan, proposal, *, authority_ref):
    """External declaration factory; human approval must separately exist."""
    verify_proposal(layout, artifact_root, plan, proposal)
    m.nonempty(authority_ref)
    m.require(authority_ref not in (proposal['proposingAuthority'], proposal['proposalHash'], layout['layoutHash'], plan['planHash']), 'plan/proposal/performed use cannot self-authorize pixels')
    return seal('admission', {'layoutHash': layout['layoutHash'], 'planHash': plan['planHash'],
        'proposalHash': proposal['proposalHash'], 'useHashes': plan['useHashes'], 'output': plan['output'],
        'externalAuthority': authority_ref, 'authority': ADMITTED, 'nonAuthorities': sorted(k for k,v in ADMITTED.items() if not v),
        'semanticNonclaims': use.NONCLAIMS, 'laws': LAWS})


def verify_admission(layout, artifact_root, plan, proposal, admission):
    verify_event('admission', admission)
    expected = admit(layout, artifact_root, plan, proposal, authority_ref=admission['externalAuthority'])
    m.require(admission == expected, 'pixel admission exceeds exact proposal/plan/use scope')


def matrix_hash(image):
    m.require(image.mode == 'RGBA', 'pixel matrix must be RGBA8')
    header = atlas._stable({'schema': 'static-collective/rgba-pixel-matrix/v0', 'width': image.width, 'height': image.height, 'mode': 'RGBA'})
    return hashlib.sha256(header + b'\0' + image.tobytes()).hexdigest()


def png_bytes(image):
    """Minimal deterministic PNG, independent of zlib compressor heuristics."""
    m.require(image.mode == 'RGBA', 'PNG witness must be RGBA8')
    m.require(image.width > 0 and image.height > 0, 'positive PNG dimensions required')
    raw = image.tobytes()
    stride = image.width * 4
    rows = b''.join(b'\0' + raw[y*stride:(y+1)*stride] for y in range(image.height))
    blocks = []
    for offset in range(0, len(rows), 65535):
        block = rows[offset:offset+65535]
        blocks.append(bytes([int(offset+len(block) == len(rows))]) + struct.pack('<HH', len(block), 65535-len(block)) + block)
    # RFC 1950 Adler-32; encoding has no timestamps, ICC, gamma or other chunks.
    a, b = 1, 0
    for byte in rows:
        a = (a + byte) % 65521
        b = (b + a) % 65521
    stream = b'\x78\x01' + b''.join(blocks) + struct.pack('>I', (b << 16) | a)
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', binascii.crc32(kind + data) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', image.width, image.height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', stream) + chunk(b'IEND', b'')


def alpha_bytes(alpha, opacity):
    return bytes(half_up(value * opacity) for value in alpha)


def rasterize(layout, artifact_root, plan, proposal, admission, out):
    """Must receive independent exact pixel admission before any raster work."""
    from PIL import Image
    verify_admission(layout, artifact_root, plan, proposal, admission)
    width, height = plan['output']['width'], plan['output']['height']
    composite = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    out = Path(out).resolve()
    m.require(not out.is_relative_to(Path(artifact_root).resolve()), 'layer rasters cannot write inside source evidence')
    out.mkdir(parents=True, exist_ok=True)
    receipts = []
    for layer in plan['layers']:
        with source_image(artifact_root, layer['artifact']) as im:
            resized = im.convert('RGBA').resize(tuple(layer['scaledRasterDimensions']), getattr(Image.Resampling, plan['rules']['sampling']['kernel']), box=None, reducing_gap=None)
        resized.putalpha(Image.frombytes('L', resized.size, alpha_bytes(resized.getchannel('A').tobytes(), layer['opacityMillionths'])))
        raster = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        left, top, right, bottom = layer['canvasIntersection']
        if right > left and bottom > top:
            crop = resized.crop((left-layer['xPixels'], top-layer['yPixels'], right-layer['xPixels'], bottom-layer['yPixels']))
            raster.paste(crop, (left, top))  # no mask: copy straight alpha exactly
        name = 'layers/' + layer['useHash'] + '.raster.png'
        encoded = png_bytes(raster)
        m.persist(out / name, encoded)
        receipts.append({**layer, 'rasterRecipe': plan['rules'], 'layerRaster': {'path': name,
            'encodedArtifactSha256': hashlib.sha256(encoded).hexdigest(), 'pixelMatrixHash': matrix_hash(raster),
            'width': width, 'height': height, 'mode': 'RGBA', 'byteLength': len(encoded)},
            'pixelEventLineage': {'verb': 'MANGALIZE', 'experiment': 'MANGALIZE-004', 'planHash': plan['planHash'],
                'proposalHash': proposal['proposalHash'], 'admissionHash': admission['admissionHash']},
            'semanticNonclaims': use.NONCLAIMS})
        composite = Image.alpha_composite(composite, raster)
    encoded = png_bytes(composite)
    m.persist(out / 'manga-page.png', encoded)
    return seal('execution', {'proposalHash': proposal['proposalHash'], 'admissionHash': admission['admissionHash'],
        'planHash': plan['planHash'], 'layoutHash': layout['layoutHash'], 'implementation': plan['implementation'],
        'useHashes': plan['useHashes'], 'contributions': receipts, 'finalArtifact': {'path': 'manga-page.png',
            'encodedArtifactSha256': hashlib.sha256(encoded).hexdigest(), 'pixelMatrixHash': matrix_hash(composite),
            **plan['output'], 'byteLength': len(encoded)}, 'authority': ADMITTED, 'semanticNonclaims': use.NONCLAIMS,
        'publicationStateChange': None, 'returnBasis': {'schema': 'static-collective/manga-pixel-return-basis/v0',
            'ancestorLayoutHash': layout['layoutHash'], 'useHashes': plan['useHashes'],
            'ancestorProvenance': [layer['provenance'] for layer in plan['layers']],
            'pixelEventLineage': {'verb': 'MANGALIZE', 'experiment': 'MANGALIZE-004', 'planHash': plan['planHash'],
                'proposalHash': proposal['proposalHash'], 'admissionHash': admission['admissionHash']},
            'houseAdmission': False, 'publication': False}, 'laws': LAWS})


def verified_composition(source_root, ancestor_root, release_root, bundles, performed_root):
    use.verify(source_root, ancestor_root, release_root, bundles, performed_root)
    return m.read(Path(performed_root) / 'layout.json')


def execute(source_root, ancestor_root, release_root, bundles, performed_root, plan, proposal, admission, out):
    layout = verified_composition(source_root, ancestor_root, release_root, bundles, performed_root)
    out = Path(out).resolve()
    for protected in (source_root, ancestor_root, release_root, performed_root):
        m.require(not out.is_relative_to(Path(protected).resolve()), 'pixel output cannot mutate ancestor evidence')
    with tempfile.TemporaryDirectory(prefix='manga-pixels-') as td:
        candidate = Path(td) / 'event'
        execution = rasterize(layout, ancestor_root, plan, proposal, admission, candidate)
        for kind, value in (('plan', plan), ('proposal', proposal), ('admission', admission), ('execution', execution)):
            m.persist(candidate / (kind + '.json'), value)
        m.persist(candidate / 'return-basis.json', return_basis(execution))
        m.persist(candidate / 'TRACE.md', trace(plan, proposal, execution).encode())
        if out.exists():
            m.require(m.tree_bytes(out) == m.tree_bytes(candidate), 'pixel execution verification failure: persisted event differs from replay')
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate, out)
    return execution


def verify(source_root, ancestor_root, release_root, bundles, performed_root, plan, proposal, admission, out):
    m.require(Path(out).is_dir(), 'missing pixel execution directory')
    return execute(source_root, ancestor_root, release_root, bundles, performed_root, plan, proposal, admission, out)['executionHash']


def return_basis(execution):
    """Renderer-neutral descendant evidence, never house admission/publication."""
    verify_event('execution', execution)
    contributions = copy.deepcopy(execution['contributions'])
    for contribution in contributions:
        contribution['pixelEventLineage']['executionHash'] = execution['executionHash']
    body = {'schema': 'static-collective/manga-pixel-return-basis/v0', 'verb': 'MANGALIZE', 'experiment': 'MANGALIZE-004',
        'executionHash': execution['executionHash'], 'layoutHash': execution['layoutHash'],
        'descendant': execution['finalArtifact'], 'contributions': contributions,
        'eventLineage': {**execution['returnBasis']['pixelEventLineage'], 'executionHash': execution['executionHash']},
        'ancestorProvenance': execution['returnBasis']['ancestorProvenance'], 'authority': CLOSED,
        'houseAdmission': False, 'publicationStateChange': None, 'semanticNonclaims': use.NONCLAIMS}
    return {**copy.deepcopy(body), 'returnBasisHash': atlas._hash(body)}


def trace(plan, proposal, execution=None):
    if execution is not None:
        verify_event('execution', execution)
        m.require(execution['planHash'] == plan['planHash'] and execution['proposalHash'] == proposal['proposalHash'], 'trace event binding mismatch')
    state = ['PIXEL EXECUTION READY — ADMISSION REQUIRED', 'No founding pixel admission or raster exists.'] if execution is None else [
        'SEPARATELY ADMITTED PIXEL EXECUTION', '  executionHash: '+execution['executionHash'],
        '  admissionHash: '+execution['admissionHash'], '  finalArtifact: '+atlas._stable(execution['finalArtifact']).decode()]
    lines = ['# MANGALIZE EVENT 004', '', *state, '', 'LAYOUT', '  '+plan['layoutHash'], 'PLAN', '  '+plan['planHash'],
        'PROPOSAL', '  '+proposal['proposalHash'], '', 'USE RECIPES']
    for layer in plan['layers']:
        lines.extend([f"  {layer['performedRole']} | {layer['assetId']}", '  useHash: '+layer['useHash'],
            '  artifact SHA: '+layer['artifact']['sha256']])
        for key in ('sourceRasterDimensions', 'scaledRasterDimensions', 'destinationBoxBeforeClipping', 'canvasIntersection', 'pixelsClipped', 'finalCompositedRectangle'):
            lines.append('  '+key+': '+atlas._stable(layer[key]).decode())
        if execution is not None:
            contribution = next(r for r in execution['contributions'] if r['useHash'] == layer['useHash'])
            lines.append('  layerRaster: '+atlas._stable(contribution['layerRaster']).decode())
    lines.extend(['', 'EXACT RASTER SEMANTICS', *['  '+k+': '+atlas._stable(v).decode() for k,v in sorted(plan['rules'].items())],
        '', 'IMPLEMENTATION', '  '+atlas._stable(plan['implementation']).decode(), '', 'OUTPUT', '  '+atlas._stable(plan['output']).decode(),
        '', 'REQUESTED AUTHORITY' if execution is None else 'EXECUTED AUTHORITY', '  '+atlas._stable(ADMITTED).decode(),
        '', 'PUBLICATION / MOTION / SOUND / RECOGNITION', '  Not admitted.'])
    return '\n'.join(lines)+'\n'

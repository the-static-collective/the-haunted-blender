import copy
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
import test_mangalize_003 as fixture003
from haunted_blender import mangalize as m, manga_atlas as atlas, manga_performed_use as use
from haunted_blender import manga_pixel_execution as px

ROOT = Path(__file__).resolve().parents[1]


class PixelExecution004Tests(unittest.TestCase):
    def setUp(self):
        # Reuse the independent synthetic custody fixture, not the real page or
        # its grants. No test issues authority for the real #66 composition.
        self.f = fixture003.PerformedUse003Tests('test_role_replay_is_byte_identical_and_create_only')
        self.addCleanup(self.f.doCleanups)
        self.f.setUp()
        self.bundles = []
        for i,row in enumerate(self.f.drawer['artifacts']):
            role = self.f.role_for({'still':'poster','crop':'cutaway','mask':'texture'}[row['kind']],row['id'])
            geometry = fixture003.geometry(x=32000+i*192000,z=10+i*10)
            geometry['scaleMillionths'] = 2400000 if row['kind']=='crop' else 2000000
            geometry['opacityMillionths'] = 350000 if row['kind']=='mask' else 1000000
            place = self.f.place_for(role,**geometry)
            self.bundles.append(self.f.bundle(role,place))
        self.performed = self.f.root / 'performed'
        self.layout = use.execute(self.f.source,self.f.ancestor,self.f.release,self.bundles,self.performed)
        self.plan = px.compile_plan(self.layout,self.f.ancestor)
        self.proposal = px.propose(self.layout,self.f.ancestor,self.plan,authority_ref='fictional-test:pixel-proposer')

    def admission(self,plan=None,proposal=None):
        return px.admit(self.layout,self.f.ancestor,plan or self.plan,proposal or self.proposal,authority_ref='fictional-test:separate-pixel-admission')

    def run_pixels(self,out=None):
        out=out or self.f.root / 'pixel-event'
        return px.execute(self.f.source,self.f.ancestor,self.f.release,self.bundles,self.performed,self.plan,self.proposal,self.admission(),out)

    def test_plan_and_proposal_replay_byte_identical_and_closed(self):
        self.assertEqual(atlas._stable(self.plan),atlas._stable(px.compile_plan(self.layout,self.f.ancestor)))
        self.assertEqual(atlas._stable(self.proposal),atlas._stable(px.propose(self.layout,self.f.ancestor,self.plan,authority_ref='fictional-test:pixel-proposer')))
        self.assertEqual(self.plan['authority'],px.CLOSED)
        self.assertEqual(self.proposal['authority'],px.CLOSED)
        self.assertEqual(self.plan['rules']['background']['rgba'],[0,0,0,0])

    def test_planning_never_resizes_composites_or_serializes_pixels(self):
        with patch.object(Image.Image,'resize',side_effect=AssertionError('planning resized pixels')), \
             patch.object(Image,'alpha_composite',side_effect=AssertionError('planning composited pixels')), \
             patch.object(px,'png_bytes',side_effect=AssertionError('planning encoded pixels')):
            plan=px.compile_plan(self.layout,self.f.ancestor)
            self.assertEqual(plan,self.plan)
            self.assertEqual(px.propose(self.layout,self.f.ancestor,plan,authority_ref='fictional-test:pixel-proposer'),self.proposal)

    def test_hidden_rgb_at_zero_alpha_is_part_of_exact_matrix_identity(self):
        white=Image.new('RGBA',(1,1),(255,255,255,0))
        black=Image.new('RGBA',(1,1),(0,0,0,0))
        self.assertNotEqual(px.matrix_hash(white),px.matrix_hash(black))
        for rgb in ((255,255,255),(0,0,0),(100,20,80)):
            background=Image.new('RGBA',(1,1),(*rgb,255))
            self.assertEqual(Image.alpha_composite(background,white).tobytes(),Image.alpha_composite(background,black).tobytes())

    def test_performed_use_is_not_pixel_admission_and_proposal_cannot_self_admit(self):
        with self.assertRaises(ValueError):
            px.rasterize(self.layout,self.f.ancestor,self.plan,self.proposal,self.bundles[0]['admission'],self.f.root/'refused')
        for ref in (self.proposal['proposingAuthority'],self.layout['layoutHash'],self.plan['planHash']):
            with self.assertRaisesRegex(ValueError,'self-authorize'):
                px.admit(self.layout,self.f.ancestor,self.plan,self.proposal,authority_ref=ref)
        self.assertFalse((self.f.root/'refused').exists())

    def test_integer_coordinates_and_fractional_rejection(self):
        self.assertEqual([r['xPixels'] for r in self.plan['layers']],[32,224,416])
        changed=copy.deepcopy(self.layout)
        changed['performedUses'][0]['placement']['xMilliPixels']+=1
        changed['performedUses'][0]=use.seal('use',changed['performedUses'][0])
        changed=use.seal('layout',changed)
        with self.assertRaisesRegex(ValueError,'fractional'):
            px.compile_plan(changed,self.f.ancestor)

    def test_zero_rotation_only_and_authored_background_refuses(self):
        for field,value in [('rotationMilliDegrees',1000),('timeRange',{'start':0,'end':1})]:
            changed=copy.deepcopy(self.layout)
            changed['performedUses'][0]['placement'][field]=value
            changed['performedUses'][0]=use.seal('use',changed['performedUses'][0])
            with self.assertRaises(ValueError):
                px.compile_plan(use.seal('layout',changed),self.f.ancestor)
        changed=copy.deepcopy(self.layout)
        changed['background']=[255,255,255,255]
        with self.assertRaisesRegex(ValueError,'background'):
            px.compile_plan(use.seal('layout',changed),self.f.ancestor)

    def test_two_and_two_point_four_scale_and_declared_half_up(self):
        self.assertEqual(px.raster_size(64,96,2000000),[128,192])
        self.assertEqual(px.raster_size(40,60,2400000),[96,144])
        self.assertEqual(px.raster_size(1,3,1500000),[2,5])
        self.assertEqual(px.raster_size(1,1,1),[1,1])
        self.assertIn('positive half-up',self.plan['rules']['scale'])

    def test_sampler_and_dependency_witness_are_bound(self):
        witness=self.plan['implementation']
        self.assertEqual(witness['pillowVersion'],'12.1.1')
        self.assertEqual(self.plan['rules']['sampling']['kernel'],'LANCZOS')
        self.assertIn('premultiplied RGBa',self.plan['rules']['sampling']['resizeAlpha'])
        self.assertEqual(len(witness['pillowImagingBinarySha256']),64)
        alternate=px.compile_plan(self.layout,self.f.ancestor,sampler='NEAREST')
        self.assertNotEqual(self.plan['planHash'],alternate['planHash'])
        self.assertEqual(self.plan['useHashes'],alternate['useHashes'])
        with self.assertRaises(ValueError): px.compile_plan(self.layout,self.f.ancestor,sampler='UNDECLARED')

    def test_opacity_one_and_point_three_five_exact_integer_rule(self):
        alpha=bytes(range(256))
        self.assertEqual(px.alpha_bytes(alpha,1000000),alpha)
        expected=bytes((value*350000+500000)//1000000 for value in range(256))
        self.assertEqual(px.alpha_bytes(alpha,350000),expected)
        self.assertEqual(px.alpha_bytes(bytes([255,30,10,0]),350000),bytes([89,11,4,0]))

    def test_z_order_and_array_permutation_preserve_pixels(self):
        first=self.run_pixels()
        changed=copy.deepcopy(self.layout)
        changed['performedUses'].reverse()
        changed=use.seal('layout',changed)
        plan=px.compile_plan(changed,self.f.ancestor)
        self.assertEqual(plan['layers'],self.plan['layers'])
        prop=px.propose(changed,self.f.ancestor,plan,authority_ref='fictional-test:permutation-proposal')
        admit=px.admit(changed,self.f.ancestor,plan,prop,authority_ref='fictional-test:permutation-admission')
        second=px.rasterize(changed,self.f.ancestor,plan,prop,admit,self.f.root/'permutation')
        self.assertEqual(first['finalArtifact']['pixelMatrixHash'],second['finalArtifact']['pixelMatrixHash'])
        self.assertEqual(first['finalArtifact']['encodedArtifactSha256'],second['finalArtifact']['encodedArtifactSha256'])

    def test_tie_break_uses_hash_not_array_order(self):
        changed=copy.deepcopy(self.layout)
        for record in changed['performedUses']:
            record['placement']['z']=10
        changed['performedUses']=[use.seal('use',r) for r in changed['performedUses']]
        plan=px.compile_plan(use.seal('layout',changed),self.f.ancestor)
        self.assertEqual([r['useHash'] for r in plan['layers']],sorted(r['useHash'] for r in plan['layers']))

    def test_overlapping_layers_prove_source_over_and_z_order_in_actual_pixels(self):
        bundles=[]
        for bundle in self.bundles:
            geometry=copy.deepcopy(bundle['placement']['proposedPlacement'])
            geometry.update(xMilliPixels=0,yMilliPixels=0)
            place=self.f.place_for(bundle['role'],**geometry)
            bundles.append(self.f.bundle(bundle['role'],place))
        layout=use.execute(self.f.source,self.f.ancestor,self.f.release,bundles,self.f.root/'overlap-composition')
        plan=px.compile_plan(layout,self.f.ancestor)
        proposal=px.propose(layout,self.f.ancestor,plan,authority_ref='fictional-test:overlap-proposal')
        admission=px.admit(layout,self.f.ancestor,plan,proposal,authority_ref='fictional-test:overlap-admission')
        out=self.f.root/'overlap-pixels'
        execution=px.rasterize(layout,self.f.ancestor,plan,proposal,admission,out)
        rasters=[]
        for layer in execution['contributions']:
            with Image.open(out/layer['layerRaster']['path']) as im: rasters.append(im.copy())
        expected=Image.new('RGBA',(640,360),(0,0,0,0))
        reverse=expected.copy()
        for raster in rasters: expected=Image.alpha_composite(expected,raster)
        for raster in reversed(rasters): reverse=Image.alpha_composite(reverse,raster)
        self.assertEqual(px.matrix_hash(expected),execution['finalArtifact']['pixelMatrixHash'])
        self.assertNotEqual(px.matrix_hash(expected),px.matrix_hash(reverse))
        known=Image.alpha_composite(Image.new('RGBA',(1,1),(255,0,0,255)),Image.new('RGBA',(1,1),(0,0,255,89)))
        self.assertEqual(known.getpixel((0,0)),(166,0,89,255))

    def test_clipping_math_all_sides_and_empty_intersection(self):
        geo=px.clipping(-4,-5,20,30,10,12)
        self.assertEqual(geo['destinationBoxBeforeClipping'],[-4,-5,16,25])
        self.assertEqual(geo['canvasIntersection'],[0,0,10,12])
        self.assertEqual(geo['pixelsClipped'],{'left':4,'right':6,'top':5,'bottom':13})
        self.assertEqual(px.clipping(10,2,7,3,10,12)['canvasIntersection'],[10,2,10,5])

    def test_raster_clipping_and_transparency_witness(self):
        changed=copy.deepcopy(self.layout)
        record=changed['performedUses'][0]
        record['placement']['xMilliPixels']=620000
        record['placement']['yMilliPixels']=350000
        changed['performedUses']=[use.seal('use',record)]
        changed=use.seal('layout',changed)
        plan=px.compile_plan(changed,self.f.ancestor)
        proposal=px.propose(changed,self.f.ancestor,plan,authority_ref='fictional-test:clip-proposal')
        admission=px.admit(changed,self.f.ancestor,plan,proposal,authority_ref='fictional-test:clip-admission')
        execution=px.rasterize(changed,self.f.ancestor,plan,proposal,admission,self.f.root/'clipped')
        layer=execution['contributions'][0]
        self.assertEqual(layer['canvasIntersection'],[620,350,640,360])
        self.assertEqual(layer['pixelsClipped']['right'],layer['scaledRasterDimensions'][0]-20)
        self.assertEqual(layer['pixelsClipped']['bottom'],layer['scaledRasterDimensions'][1]-10)
        with Image.open(self.f.root/'clipped/manga-page.png') as im:
            self.assertEqual(im.getpixel((0,0)),(0,0,0,0))
            self.assertEqual(im.mode,'RGBA'); self.assertEqual(im.size,(640,360))

    def test_exact_png_and_matrix_replay_and_create_only_conflict(self):
        execution=self.run_pixels()
        out=self.f.root/'pixel-event'
        before=m.tree_bytes(out)
        self.assertEqual(px.verify(self.f.source,self.f.ancestor,self.f.release,self.bundles,self.performed,self.plan,self.proposal,self.admission(),out),execution['executionHash'])
        self.assertEqual(m.tree_bytes(out),before)
        (out/'manga-page.png').write_bytes(b'tamper')
        with self.assertRaisesRegex(ValueError,'persisted event differs'):
            self.run_pixels()

    def test_canonical_png_decode_and_alternate_encoding_same_pixels_different_bytes(self):
        image=Image.new('RGBA',(3,2),(11,45,98,89))
        encoded=px.png_bytes(image)
        self.assertEqual(encoded,px.png_bytes(image.copy()))
        with Image.open(io.BytesIO(encoded)) as decoded:
            self.assertEqual(px.matrix_hash(image),px.matrix_hash(decoded))
        alternate=io.BytesIO(); image.save(alternate,format='PNG',compress_level=9)
        with Image.open(io.BytesIO(alternate.getvalue())) as decoded:
            self.assertEqual(px.matrix_hash(image),px.matrix_hash(decoded))
        self.assertNotEqual(hashlib.sha256(encoded).hexdigest(),hashlib.sha256(alternate.getvalue()).hexdigest())
        self.assertNotEqual(px.matrix_hash(image),px.matrix_hash(Image.new('RGBA',(2,3),(11,45,98,89))))

    def test_intermediate_witnesses_and_final_return_retain_complete_use_custody(self):
        execution=self.run_pixels()
        self.assertEqual(len(execution['contributions']),3)
        self.assertEqual(execution['useHashes'],self.plan['useHashes'])
        for contribution,layer in zip(execution['contributions'],self.plan['layers']):
            self.assertEqual(contribution['useHash'],layer['useHash'])
            self.assertEqual(contribution['provenance'],layer['provenance'])
            self.assertEqual(contribution['admittedUseId'],layer['admittedUseId'])
            receipt=contribution['layerRaster']
            data=(self.f.root/'pixel-event'/receipt['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),receipt['encodedArtifactSha256'])
            with Image.open(io.BytesIO(data)) as im: self.assertEqual(px.matrix_hash(im),receipt['pixelMatrixHash'])
        basis=px.return_basis(execution)
        self.assertEqual(basis['authority'],px.CLOSED)
        self.assertFalse(basis['houseAdmission'])
        self.assertEqual(basis['eventLineage']['executionHash'],execution['executionHash'])
        self.assertEqual(basis['descendant'],execution['finalArtifact'])

    def test_render_does_not_modify_any_source_or_performed_evidence(self):
        roots=[self.f.source,self.f.ancestor,self.f.release,self.performed]
        before=[m.tree_bytes(p) for p in roots]
        self.run_pixels()
        self.assertEqual([m.tree_bytes(p) for p in roots],before)
        with self.assertRaisesRegex(ValueError,'ancestor evidence'):
            self.run_pixels(self.performed/'pixels')

    def test_changed_raster_rule_cannot_use_old_plan_or_admission(self):
        changed=copy.deepcopy(self.plan)
        changed['rules']['opacity']='undeclared floor'
        for bad in (changed,px.seal('plan',changed)):
            with self.assertRaises(ValueError): px.verify_plan(self.layout,self.f.ancestor,bad)
        alternate=px.compile_plan(self.layout,self.f.ancestor,sampler='NEAREST')
        prop=px.propose(self.layout,self.f.ancestor,alternate,authority_ref='fictional-test:alternate-kernel')
        with self.assertRaises(ValueError):
            px.rasterize(self.layout,self.f.ancestor,alternate,prop,self.admission(),self.f.root/'refused-kernel')

    def test_tampered_source_and_use_record_refuse(self):
        changed=copy.deepcopy(self.layout)
        changed['performedUses'][0]['performedRole']='semantic-object'
        with self.assertRaises(ValueError): px.compile_plan(use.seal('layout',changed),self.f.ancestor)
        path=m.bound_path(self.f.ancestor,self.plan['layers'][0]['artifact'])
        path.write_bytes(path.read_bytes()+b'tamper')
        with self.assertRaises(ValueError): px.verify_plan(self.layout,self.f.ancestor,self.plan)

    def test_tampered_admission_cannot_widen_authority_even_rehashed(self):
        admission=self.admission()
        for key in ('motion','publication','sound','externalGeneration','characterCasting'):
            bad=copy.deepcopy(admission); bad['authority'][key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):
                px.rasterize(self.layout,self.f.ancestor,self.plan,self.proposal,px.seal('admission',bad),self.f.root/'widened')

    def test_same_environment_subprocess_reproduces_png_bytes(self):
        execution=self.run_pixels()
        for name,value in [('plan',self.plan),('proposal',self.proposal),('admission',self.admission())]:
            m.persist(self.f.root/(name+'.json'),value)
        command=[sys.executable,'-m','haunted_blender.manga_pixel_execution_cli','execute',str(self.f.source),str(self.f.ancestor),str(self.f.release),str(self.performed),str(self.f.root/'subprocess')]
        for bundle_dir in sorted(p for p in self.performed.iterdir() if p.is_dir()): command+=['--use',str(bundle_dir)]
        for name in ('plan','proposal','admission'): command+=['--'+name,str(self.f.root/(name+'.json'))]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(m.tree_bytes(self.f.root/'subprocess'),m.tree_bytes(self.f.root/'pixel-event'))
        self.assertEqual(execution['authority'],px.ADMITTED)
        self.assertEqual(execution['semanticNonclaims'],use.NONCLAIMS)

    def test_environment_drift_and_pixel_proposal_tamper_refuse(self):
        bad=copy.deepcopy(self.plan); bad['implementation']['pillowImagingBinarySha256']='0'*64
        with self.assertRaises(ValueError): px.verify_plan(self.layout,self.f.ancestor,px.seal('plan',bad))
        bad=copy.deepcopy(self.proposal); bad['useHashes']=[]
        with self.assertRaises(ValueError): px.verify_proposal(self.layout,self.f.ancestor,self.plan,px.seal('proposal',bad))


class HistoricalPixelBoundary004Tests(unittest.TestCase):
    def test_founding_proposal_binds_exact_layout_and_clipping_without_rendering(self):
        here=ROOT/'specimens/mangalize-004'
        plan=m.read(here/'prepared/plan.json')
        proposal=m.read(here/'prepared/proposal.json')
        layout=m.read(ROOT/'specimens/mangalize-003/performed/layout.json')
        px.verify_event('plan',plan); px.verify_event('proposal',proposal)
        self.assertEqual(plan['layoutHash'],'fa198528b8454af1cb06ec3dde25c70d57db667f67591ac65234f3d12cebc46a')
        self.assertEqual(plan['planHash'],'b3203f8c3d9dfd0b080d149efca9de13fa266675833f08b803187925cbdc6a1a')
        self.assertEqual(proposal['proposalHash'],'2b8c9e795571f6e5ca7116d1046f761611ff2b1f789f4d86c37588561d8dfc2b')
        self.assertEqual(plan['useHashes'],sorted(r['useHash'] for r in layout['performedUses']))
        self.assertEqual(plan['authority'],px.CLOSED)
        self.assertEqual(proposal['authority'],px.CLOSED)
        self.assertEqual([r['scaledRasterDimensions'] for r in plan['layers']],[[128,192],[96,144],[128,192]])
        self.assertEqual([r['canvasIntersection'] for r in plan['layers']],[[32,48,160,240],[224,72,320,216],[448,48,576,240]])
        self.assertTrue(all(set(r['pixelsClipped'].values())=={0} for r in plan['layers']))
        if plan['implementation']==px.witness():
            px.verify_plan(layout,ROOT/'specimens/mangalize-001/executed',plan)
            px.verify_proposal(layout,ROOT/'specimens/mangalize-001/executed',plan,proposal)
        else:
            # A different declared ABI/wheel must refuse, not claim equivalence.
            with self.assertRaisesRegex(ValueError,'environment reconstruction'):
                px.verify_plan(layout,ROOT/'specimens/mangalize-001/executed',plan)
        # Preserve the original unadmitted preparation as its own witness.
        self.assertFalse(any((here/'prepared').rglob('*.png')))
        self.assertFalse((here/'prepared/admission.json').exists())
        self.assertFalse((here/'prepared/execution.json').exists())
        self.assertIn('PIXEL EXECUTION READY — ADMISSION REQUIRED',(here/'prepared/TRACE.md').read_text())

    def test_real_founding_admission_and_independent_replay_or_environment_refusal(self):
        import importlib.util
        script=ROOT/'specimens/mangalize-004/verify_founding.py'
        spec=importlib.util.spec_from_file_location('pixel_founding_verifier',script)
        verifier=importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
        roots,bundles,performed,plan,proposal,admission=verifier.inputs()
        self.assertEqual(admission['authority'],px.ADMITTED)
        if plan['implementation']==px.witness():
            with tempfile.TemporaryDirectory() as td:
                self.assertEqual(verifier.verify(Path(td)/'replay'),verifier.EXECUTION_HASH)
        else:
            # Inspecting existing evidence is possible; executing this exact
            # plan on a foreign ABI/native binary is explicitly refused.
            with self.assertRaisesRegex(ValueError,'environment reconstruction'):
                verifier.verify()

    def test_real_output_matrix_encoded_identity_and_full_contribution_custody(self):
        here=ROOT/'specimens/mangalize-004/executed'
        ex=m.read(here/'execution.json'); px.verify_event('execution',ex)
        self.assertEqual(ex['authority'],px.ADMITTED)
        self.assertEqual(ex['semanticNonclaims'],use.NONCLAIMS)
        self.assertIsNone(ex['publicationStateChange'])
        self.assertEqual(ex['finalArtifact']['pixelMatrixHash'],'ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5')
        self.assertEqual(ex['finalArtifact']['encodedArtifactSha256'],'2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74')
        plan=m.read(here/'plan.json')
        self.assertEqual(ex['useHashes'],plan['useHashes'])
        for row in ex['contributions']:
            recipe=next(layer for layer in plan['layers'] if layer['useHash']==row['useHash'])
            for key,value in recipe.items(): self.assertEqual(row[key],value,key)
            self.assertEqual(row['pixelEventLineage']['admissionHash'],ex['admissionHash'])
            self.assertEqual(row['rasterRecipe'],plan['rules'])
        for artifact in [ex['finalArtifact'],*(r['layerRaster'] for r in ex['contributions'])]:
            data=(here/artifact['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),artifact['encodedArtifactSha256'])
            self.assertEqual(len(data),artifact['byteLength'])
            with Image.open(io.BytesIO(data)) as im:
                self.assertEqual((im.mode,im.size),('RGBA',(640,360)))
                self.assertEqual(px.matrix_hash(im),artifact['pixelMatrixHash'])
                self.assertEqual(px.png_bytes(im),data)
        basis=m.read(here/'return-basis.json')
        self.assertEqual(basis,px.return_basis(ex))
        self.assertEqual(basis['authority'],px.CLOSED)
        self.assertFalse(basis['houseAdmission'])

    def test_real_texture_retains_invisible_rgb_without_normalization(self):
        here=ROOT/'specimens/mangalize-004/executed'
        ex=m.read(here/'execution.json')
        layer=next(r for r in ex['contributions'] if r['performedRole']=='texture')
        with Image.open(here/layer['layerRaster']['path']) as im:
            raw=im.tobytes()
            hidden=[i for i in range(0,len(raw),4) if raw[i+3]==0 and raw[i:i+3]!=b'\0\0\0']
            self.assertEqual(len(hidden),20)
            self.assertTrue(all(raw[i:i+4]==b'\xff\xff\xff\0' for i in hidden))
            normalized=bytearray(raw)
            for i in hidden: normalized[i:i+3]=b'\0\0\0'
            changed=Image.frombytes('RGBA',im.size,bytes(normalized))
            self.assertNotEqual(px.matrix_hash(changed),px.matrix_hash(im))
            background=Image.new('RGBA',im.size,(71,83,95,255))
            self.assertEqual(Image.alpha_composite(background,im).tobytes(),Image.alpha_composite(background,changed).tobytes())

    def test_all_94_historical_files_remain_byte_identical(self):
        pin=m.read(ROOT/'specimens/mangalize-004/ANCESTOR_PIN.json')
        self.assertEqual(pin['commit'],'736dc0eba07b591a7aa25abf3fb92e5ddbaa7a23')
        self.assertEqual(len(pin['files']),94)
        for row in pin['files']:
            self.assertEqual(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(),row['sha256'],row['path'])

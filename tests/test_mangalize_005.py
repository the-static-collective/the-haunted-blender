import copy
import hashlib
import io
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
import test_mangalize_004 as fixture004
from haunted_blender import mangalize as m, manga_atlas as atlas, manga_pixel_execution as px
from haunted_blender import manga_presentation as g, material_surface

ROOT = Path(__file__).resolve().parents[1]


class Presentation005Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Real synthetic 001 -> 004 custody, with fictional authorities only.
        cls.fx = fixture004.PixelExecution004Tests('test_plan_and_proposal_replay_byte_identical_and_closed')
        cls.addClassCleanup(cls.fx.doCleanups)
        cls.fx.setUp()
        cls.base = cls.fx.f.root / '005-parent'
        cls.fx.run_pixels(cls.base)

    def setUp(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        self.root = Path(td.name)
        self.pixel = self.root / 'parent'
        shutil.copytree(self.base, self.pixel)
        f = self.fx.f
        self.roots = [f.source, f.ancestor, f.release]
        self.parent = g.verified_parent(*self.roots, self.fx.bundles, self.fx.performed, self.pixel)
        self.value = self.ground([128,128,128,255])
        self.proposal = g.propose(self.parent, self.value, authority_ref='fictional-test:ground-proposer')

    def ground(self, rgba8):
        return g.ground(self.parent, rgba8, intent='synthetic display comparison; not print stock')

    def admission(self, value=None, proposal=None):
        return g.admit(self.parent, value or self.value, proposal or self.proposal,
                       authority_ref='fictional-test:separate-presentation-admission')

    def execute(self, out=None, value=None, proposal=None, admission=None):
        value, proposal = value or self.value, proposal or self.proposal
        return g.execute(*self.roots, self.fx.bundles, self.fx.performed, self.pixel,
                         value, proposal, admission or self.admission(value,proposal), out or self.root/'projection')

    def candidates(self):
        return [{'ground':value,'proposal':g.propose(self.parent,value,authority_ref='fictional-test:ground-proposer')}
                for value in [self.ground([255,255,255,255]),self.ground([0,0,0,255]),self.value]]

    def test_deterministic_ground_and_proposal_hashing_and_closed_authority(self):
        self.assertEqual(atlas._stable(self.value),atlas._stable(self.ground([128,128,128,255])))
        self.assertEqual(atlas._stable(self.proposal),atlas._stable(g.propose(self.parent,self.value,authority_ref='fictional-test:ground-proposer')))
        self.assertEqual(self.value['authority'],g.CLOSED)
        self.assertEqual(self.proposal['authority'],g.CLOSED)
        self.assertEqual(self.proposal['pixelExecutionHash'],self.parent['executionHash'])

    def test_rgba_channels_opaque_ground_and_material_types_are_explicit(self):
        for rgba8 in ([0,0,0,0],[0,0,0,254],[0,0,0],[256,0,0,255],[True,0,0,255],[1.0,0,0,255]):
            with self.subTest(rgba8=rgba8),self.assertRaises(ValueError): self.ground(rgba8)
        for kind,profile in [('material-ground',{'type':'paper'}),('solid-rgba',{'type':'inked'})]:
            changed=copy.deepcopy(self.value); changed['kind']=kind; changed['parameters']['materialProfile']=profile
            with self.assertRaises(ValueError): g.verify_ground(self.parent,g.seal('ground',changed))

    def test_ground_intent_is_not_print_stock_or_physics_authority(self):
        self.assertEqual(self.value['parameters']['materialProfile'],None)
        self.assertFalse(self.value['authority']['printAdmission'])
        for law in ('DISPLAY GROUND != PRINT STOCK','SCREEN WHITE != PAPER WHITE','MATERIAL != PHYSICS CLAIM'):
            self.assertIn(law,self.value['laws'])

    def test_comparison_is_numeric_only_and_grants_no_selection_or_execution(self):
        with patch.object(px,'png_bytes',side_effect=AssertionError('candidate encoded PNG')), \
             patch.object(Image.Image,'save',side_effect=AssertionError('candidate persisted pixels')):
            result=g.compare(self.parent,self.pixel,self.candidates())
        self.assertEqual(result['authority'],g.CLOSED)
        for key in ('selected','preferred','ranking','selection'): self.assertNotIn(key,result)
        self.assertIn('numeric evidence only',result['artifactProduction'])
        self.assertFalse(any(self.root.glob('projection*')))
        with self.assertRaises(ValueError):
            g.project(self.parent,self.pixel,self.value,self.proposal,result,self.root/'forbidden')
        self.assertFalse((self.root/'forbidden').exists())

    def test_comparison_replay_and_candidate_permutation_are_byte_identical(self):
        candidates=self.candidates()
        first=g.compare(self.parent,self.pixel,candidates)
        self.assertEqual(atlas._stable(first),atlas._stable(g.compare(self.parent,self.pixel,list(reversed(candidates)))))
        g.verify_comparison(self.parent,self.pixel,candidates,first)
        with self.assertRaises(ValueError): g.compare(self.parent,self.pixel,[candidates[0],candidates[0]])

    def test_same_page_white_black_gray_are_distinct_sibling_presentations(self):
        before=m.tree_bytes(self.pixel)
        predictions=g.compare(self.parent,self.pixel,self.candidates())
        outputs=[]
        for i,candidate in enumerate(self.candidates()):
            result=self.execute(self.root/('sibling-'+str(i)),candidate['ground'],candidate['proposal'])
            predicted=next(r for r in predictions['candidates'] if r['groundHash']==result['groundHash'])
            self.assertEqual(result['presentationPixelMatrixHash'],predicted['observations']['predictedPresentationPixelMatrixHash'])
            self.assertEqual(result['parent'],self.parent)
            self.assertNotEqual(result['presentationPixelMatrixHash'],result['pagePixelMatrixHash'])
            outputs.append(result)
        self.assertEqual(len({p['projectionHash'] for p in outputs}),3)
        self.assertEqual(len({p['presentationPixelMatrixHash'] for p in outputs}),3)
        self.assertEqual(len({p['presentationEncodedArtifactSha256'] for p in outputs}),3)
        self.assertEqual(m.tree_bytes(self.pixel),before)

    def test_exact_projection_replay_and_create_only_persistence(self):
        first=self.execute()
        tree=m.tree_bytes(self.root/'projection')
        self.assertEqual(self.execute()['projectionHash'],first['projectionHash'])
        second=self.execute(self.root/'independent')
        self.assertEqual(second,first)
        self.assertEqual(m.tree_bytes(self.root/'independent'),tree)
        self.assertEqual(g.verify(*self.roots,self.fx.bundles,self.fx.performed,self.pixel,self.value,self.proposal,self.admission(),self.root/'projection'),first['projectionHash'])

    def test_opaque_source_over_integer_contract_for_every_alpha(self):
        for source_rgb,ground_rgb in [((255,0,0),(0,0,255)),((235,12,88),(3,27,190)),((127,128,129),(220,4,17))]:
            raw=bytes(channel for alpha in range(256) for channel in (*source_rgb,alpha))
            page=Image.frombytes('RGBA',(256,1),raw)
            result=g._compose(page,[*ground_rgb,255])
            expected=[]
            for alpha in range(256):
                channels=[]
                for src,dst in zip(source_rgb,ground_rgb):
                    q=128*(src*alpha+dst*(255-alpha))+16384
                    channels.append(((q>>8)+q)>>15)
                expected.extend([*channels,255])
            self.assertEqual(result.tobytes(),bytes(expected))
        known=g._compose(Image.new('RGBA',(1,1),(255,255,255,89)),[0,0,0,255])
        self.assertEqual(known.getpixel((0,0)),(89,89,89,255))

    def test_hidden_zero_alpha_rgb_remains_parent_identity_without_visible_contribution(self):
        white=Image.new('RGBA',(2,1),(255,255,255,0))
        black=Image.new('RGBA',(2,1),(0,0,0,0))
        before=white.tobytes()
        self.assertNotEqual(px.matrix_hash(white),px.matrix_hash(black))
        self.assertNotEqual(hashlib.sha256(px.png_bytes(white)).hexdigest(),hashlib.sha256(px.png_bytes(black)).hexdigest())
        for rgba8 in ([255,255,255,255],[0,0,0,255],[128,128,128,255]):
            first,second=g._compose(white,rgba8),g._compose(black,rgba8)
            self.assertEqual(first.tobytes(),second.tobytes())
            self.assertEqual(px.matrix_hash(first),px.matrix_hash(second))
            self.assertEqual(g.observations(white,first,rgba8)['transparencyResolution']['hiddenNonzeroRGBAtParentAlphaZero'],2)
        self.assertEqual(white.tobytes(),before)

    def test_observations_have_exact_counts_luma_and_contrast_without_quality_score(self):
        page=Image.frombytes('RGBA',(3,1),bytes([255,0,0,255,20,40,60,0,255,255,255,89]))
        result=g._compose(page,[0,0,0,255])
        observations=g.observations(page,result,[0,0,0,255])
        self.assertEqual(observations['resultUniqueRGBColors'],3)
        resolution=observations['transparencyResolution']
        self.assertEqual(resolution,{'zeroAlphaParentPixelsReceiveGround':1,'partialAlphaParentPixelsComposited':1,
            'opaqueParentPixels':1,'hiddenNonzeroRGBAtParentAlphaZero':1,'partialAlphaResultRGBChangedFromSource':1,
            'nonzeroAlphaPixelsMatchingGroundRGB':0})
        histogram=observations['encodedLuma8']['histogram']
        self.assertEqual([(i,n) for i,n in enumerate(histogram) if n],[(0,1),(54,1),(89,1)])
        self.assertEqual(observations['encodedLuma8']['sum'],143)
        self.assertEqual(sum(observations['absoluteLumaDifferenceFromGround']['nonzeroAlphaPixelsHistogram']),2)
        self.assertEqual(sum(observations['absoluteLumaDifferenceFromGround']['partialAlphaPixelsHistogram']),1)
        self.assertNotIn('quality',observations)

    def test_partial_alpha_can_resolve_without_changing_rgb_and_not_mean_no_operation(self):
        page=Image.new('RGBA',(1,1),(255,255,255,89))
        result=g._compose(page,[255,255,255,255])
        measured=g.observations(page,result,[255,255,255,255])['transparencyResolution']
        self.assertEqual(measured['partialAlphaParentPixelsComposited'],1)
        self.assertEqual(measured['partialAlphaResultRGBChangedFromSource'],0)
        self.assertEqual(measured['nonzeroAlphaPixelsMatchingGroundRGB'],1)
        self.assertEqual(page.getpixel((0,0)),(255,255,255,89))

    def test_no_resize_conversion_crop_blur_or_008l_treatment_occurs(self):
        with patch.object(Image.Image,'resize',side_effect=AssertionError('resize')), \
             patch.object(Image.Image,'convert',side_effect=AssertionError('mode/color conversion')), \
             patch.object(Image.Image,'crop',side_effect=AssertionError('crop')), \
             patch.object(material_surface,'materialize_asset',side_effect=AssertionError('008l treatment')):
            g.compare(self.parent,self.pixel,self.candidates())
            g.project(self.parent,self.pixel,self.value,self.proposal,self.admission(),self.root/'no-transform')

    def test_projection_authority_is_presentation_only_and_full_ancestry_survives(self):
        result=self.execute()
        self.assertEqual(result['authority'],g.ADMITTED)
        self.assertIsNone(result['publicationStateChange'])
        self.assertEqual(result['ancestorReturnBasis'],px.return_basis(self.parent['pixelExecution']))
        self.assertEqual(result['semanticNonclaims'],self.parent['pixelExecution']['semanticNonclaims'])
        self.assertEqual(result['ancestorReturnBasis']['contributions'][0]['pixelEventLineage']['executionHash'],self.parent['executionHash'])
        self.assertIn('not page replacement',result['relationship'])

    def test_output_is_same_size_opaque_rgba_and_encoded_identity_is_separate(self):
        result=self.execute()
        data=(self.root/'projection/presentation.png').read_bytes()
        self.assertEqual(len(data),result['artifact']['byteLength'])
        self.assertEqual(hashlib.sha256(data).hexdigest(),result['presentationEncodedArtifactSha256'])
        with Image.open(io.BytesIO(data)) as image:
            self.assertEqual(image.mode,'RGBA')
            self.assertEqual(image.size,(self.parent['dimensions']['width'],self.parent['dimensions']['height']))
            self.assertEqual(image.getchannel('A').getextrema(),(255,255))
            self.assertEqual(px.matrix_hash(image),result['presentationPixelMatrixHash'])
            self.assertEqual(px.png_bytes(image),data)

    def test_proposal_cannot_self_admit_or_reuse_004_pixel_authority(self):
        for ref in (self.proposal['proposingAuthority'],self.proposal['proposalHash'],self.parent['executionHash'],self.value['groundHash']):
            with self.assertRaisesRegex(ValueError,'self-admit'):
                g.admit(self.parent,self.value,self.proposal,authority_ref=ref)
        old=m.read(self.pixel/'admission.json')
        with self.assertRaises(ValueError): g.project(self.parent,self.pixel,self.value,self.proposal,old,self.root/'refused')
        self.assertFalse((self.root/'refused').exists())

    def test_changed_ground_cannot_consume_an_old_admission(self):
        new=self.ground([0,0,0,255])
        proposal=g.propose(self.parent,new,authority_ref='fictional-test:black-proposer')
        with self.assertRaises(ValueError):
            self.execute(value=new,proposal=proposal,admission=self.admission())

    def test_tampered_page_bytes_and_pixel_matrix_refuse(self):
        path=self.pixel/'manga-page.png'
        path.write_bytes(path.read_bytes()+b'tamper')
        with self.assertRaises(ValueError): g.compare(self.parent,self.pixel,self.candidates())
        with self.assertRaises(ValueError): self.execute()

    def test_rehashed_parent_pixel_claim_refuses_and_does_not_normalize_source(self):
        changed=copy.deepcopy(self.parent['pixelExecution'])
        changed['finalArtifact']['pixelMatrixHash']='0'*64
        bad=g.parent_descriptor(px.seal('execution',changed))
        with self.assertRaisesRegex(ValueError,'pixel matrix changed'): g.read_page(self.pixel,bad)

    def test_tampered_ground_hash_and_rehashed_semantics_refuse(self):
        changed=copy.deepcopy(self.value); changed['parameters']['rgba8'][0]=127
        with self.assertRaises(ValueError): g.verify_ground(self.parent,changed)
        changed=copy.deepcopy(self.value); changed['semantics']['transforms']['resize']=True
        with self.assertRaises(ValueError): g.verify_ground(self.parent,g.seal('ground',changed))

    def test_tampered_proposal_and_rehashed_scope_refuse(self):
        changed=copy.deepcopy(self.proposal); changed['pagePixelMatrixHash']='0'*64
        for bad in (changed,g.seal('proposal',changed)):
            with self.assertRaises(ValueError): g.verify_proposal(self.parent,self.value,bad)

    def test_tampered_admission_and_rehashed_authority_expansion_refuse(self):
        changed=copy.deepcopy(self.admission()); changed['groundHash']='0'*64
        for bad in (changed,g.seal('admission',changed)):
            with self.assertRaises(ValueError): g.project(self.parent,self.pixel,self.value,self.proposal,bad,self.root/'refused')
        for key in g.CLOSED:
            if key=='presentation': continue
            changed=copy.deepcopy(self.admission()); changed['authority'][key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):
                g.project(self.parent,self.pixel,self.value,self.proposal,g.seal('admission',changed),self.root/'refused')

    def test_tampered_projection_and_encoded_output_refuse_independent_replay(self):
        self.execute()
        out=self.root/'projection'
        changed=m.read(out/'projection.json'); changed['groundRGBA8']=[1,2,3,255]
        (out/'projection.json').write_bytes(atlas._stable(g.seal('projection',changed)))
        with self.assertRaisesRegex(ValueError,'persisted event differs'): self.execute()
        shutil.rmtree(out); self.execute()
        (out/'presentation.png').write_bytes(b'tamper')
        with self.assertRaisesRegex(ValueError,'persisted event differs'): self.execute()

    def test_tampered_comparison_and_rehashed_measurements_refuse(self):
        candidates=self.candidates(); comparison=g.compare(self.parent,self.pixel,candidates)
        comparison['candidates'][0]['observations']['resultUniqueRGBColors']+=1
        for changed in (comparison,g.seal('comparison',comparison)):
            with self.assertRaises(ValueError): g.verify_comparison(self.parent,self.pixel,candidates,changed)

    def test_no_page_or_any_earlier_event_mutation_and_protected_output_paths(self):
        protected=[*self.roots,self.fx.performed,self.pixel]
        before=[m.tree_bytes(root) for root in protected]
        self.execute()
        self.assertEqual([m.tree_bytes(root) for root in protected],before)
        for root in protected:
            with self.assertRaisesRegex(ValueError,'ancestor evidence'): self.execute(root/'forbidden-projection')

    def test_native_dependency_or_005_implementation_drift_requires_new_ground(self):
        changed=copy.deepcopy(self.value)
        changed['implementation']['rasterDependency']['pillowImagingBinarySha256']='0'*64
        with self.assertRaises(ValueError): g.verify_ground(self.parent,g.seal('ground',changed))
        changed=copy.deepcopy(self.value); changed['implementation']['implementationSha256']='0'*64
        with self.assertRaises(ValueError): g.verify_ground(self.parent,g.seal('ground',changed))

    def test_separate_process_cli_execution_reproduces_every_byte(self):
        self.execute()
        for kind,value in [('ground',self.value),('proposal',self.proposal),('admission',self.admission())]:
            m.persist(self.root/(kind+'.json'),value)
        command=[sys.executable,'-m','haunted_blender.manga_presentation_cli','execute',
                 *map(str,self.roots),str(self.fx.performed),str(self.pixel),str(self.root/'subprocess')]
        for path in sorted(p for p in self.fx.performed.iterdir() if p.is_dir()): command+=['--use',str(path)]
        for kind in ('ground','proposal','admission'): command+=['--'+kind,str(self.root/(kind+'.json'))]
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(m.tree_bytes(self.root/'subprocess'),m.tree_bytes(self.root/'projection'))


class FoundingPresentationBoundary005Tests(unittest.TestCase):
    def test_all_117_historical_specimens_and_nine_implementations_remain_exact(self):
        pin=m.read(ROOT/'specimens/mangalize-005/ANCESTOR_PIN.json')
        self.assertEqual(pin['commit'],'49e9400d3753a6a308317eef8bd5b1fb93cc5322')
        self.assertEqual((pin['historicalSpecimenCount'],pin['implementationCount']),(117,9))
        self.assertEqual(len(pin['files']),126)
        for row in pin['files']:
            self.assertEqual(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(),row['sha256'],row['path'])

    def test_actual_parent_candidates_and_numeric_observations_grant_nothing(self):
        here=ROOT/'specimens/mangalize-005'
        comparison=m.read(here/'prepared/comparison.json'); g.verify_event('comparison',comparison)
        parent=comparison['parent']
        self.assertEqual(parent['pagePixelMatrixHash'],'ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5')
        self.assertEqual(parent['pageEncodedArtifactSha256'],'2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74')
        self.assertEqual(comparison['authority'],g.CLOSED)
        self.assertNotIn('selection',comparison)
        self.assertEqual(len({r['observations']['predictedPresentationPixelMatrixHash'] for r in comparison['candidates']}),3)
        for name,rgba8,colors,contrast in [('white',[255,255,255,255],92,(0,0)),
                    ('black',[0,0,0,255],140,(1,89)),('mid-gray',[128,128,128,255],100,(0,44))]:
            value=m.read(here/'prepared'/name/'ground.json')
            proposal=m.read(here/'prepared'/name/'proposal.json')
            g.verify_event('ground',value); g.verify_event('proposal',proposal)
            self.assertEqual(value['parameters']['rgba8'],rgba8)
            self.assertEqual(value['authority'],g.CLOSED)
            self.assertEqual(proposal['authority'],g.CLOSED)
            self.assertEqual(proposal['parent'],parent)
            row=next(r for r in comparison['candidates'] if r['groundHash']==value['groundHash'])
            self.assertEqual(row['proposalHash'],proposal['proposalHash'])
            obs=row['observations']
            self.assertEqual(obs['resultUniqueRGBColors'],colors)
            self.assertEqual(obs['transparencyResolution']['zeroAlphaParentPixelsReceiveGround'],181656)
            self.assertEqual(obs['transparencyResolution']['partialAlphaParentPixelsComposited'],10344)
            self.assertEqual(obs['transparencyResolution']['opaqueParentPixels'],38400)
            self.assertEqual(sum(obs['encodedLuma8']['histogram']),230400)
            histogram=obs['absoluteLumaDifferenceFromGround']['partialAlphaPixelsHistogram']
            self.assertEqual((min(i for i,n in enumerate(histogram) if n),max(i for i,n in enumerate(histogram) if n)),contrast)
        # The historical proposal boundary persists after separate admission.
        self.assertFalse(any((here/'prepared').rglob('*.png')))
        self.assertFalse(any((here/'prepared').rglob('admission.json')))
        self.assertFalse(any((here/'prepared').rglob('projection.json')))
        self.assertIn('PRESENTATION GROUND READY — SELECTION / ADMISSION REQUIRED',(here/'prepared/TRACE.md').read_text())

    def test_founding_candidate_replay_or_explicit_foreign_environment_refusal(self):
        here=ROOT/'specimens/mangalize-005'
        value=m.read(here/'prepared/white/ground.json')
        if value['implementation']==g.witness():
            with tempfile.TemporaryDirectory() as td:
                result=subprocess.run([sys.executable,str(here/'prepare.py'),str(Path(td)/'candidates')],
                                      cwd=ROOT,text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(m.tree_bytes(here/'prepared'),m.tree_bytes(Path(td)/'candidates'))
        else:
            comparison=m.read(here/'prepared/comparison.json')
            with self.assertRaisesRegex(ValueError,'implementation semantics'):
                g.verify_ground(comparison['parent'],value)

    def test_real_black_selection_exact_authority_and_independent_replay_or_refusal(self):
        import importlib.util
        script=ROOT/'specimens/mangalize-005/verify_founding.py'
        spec=importlib.util.spec_from_file_location('ground_founding_verifier',script)
        verifier=importlib.util.module_from_spec(spec); spec.loader.exec_module(verifier)
        roots,bundles,performed,pixels,value,proposal,admission=verifier.inputs()
        self.assertEqual(admission['authority'],g.ADMITTED)
        if value['implementation']==g.witness():
            with tempfile.TemporaryDirectory() as td:
                self.assertEqual(verifier.verify(Path(td)/'black-replay'),verifier.PROJECTION_HASH)
        else:
            # The parent 004 plan must refuse the foreign ABI/native witness.
            with self.assertRaisesRegex(ValueError,'environment reconstruction'):
                verifier.verify()

    def test_real_black_projection_matrix_file_identity_and_complete_custody(self):
        here=ROOT/'specimens/mangalize-005'
        projection=m.read(here/'projected/projection.json'); g.verify_event('projection',projection)
        proposal=m.read(here/'prepared/black/proposal.json')
        self.assertEqual(projection['parent'],proposal['parent'])
        self.assertEqual(projection['ancestorReturnBasis'],px.return_basis(projection['parent']['pixelExecution']))
        self.assertEqual(projection['authority'],g.ADMITTED)
        self.assertEqual(projection['groundRGBA8'],[0,0,0,255])
        self.assertEqual(projection['presentationPixelMatrixHash'],'a16a6d1528b88135c5ba901da6c36e14fcff49a3250ed137899716ef607f4a9a')
        self.assertEqual(projection['presentationEncodedArtifactSha256'],'bb9f9e41bb8694ee71f4d9316623e6cb4879881dc590f49eacb513ceaf622fe0')
        self.assertIsNone(projection['publicationStateChange'])
        data=(here/'projected/presentation.png').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),projection['presentationEncodedArtifactSha256'])
        self.assertEqual(len(data),projection['artifact']['byteLength'])
        with Image.open(io.BytesIO(data)) as im:
            self.assertEqual((im.mode,im.size),('RGBA',(640,360)))
            self.assertEqual(im.getchannel('A').getextrema(),(255,255))
            self.assertEqual(px.matrix_hash(im),projection['presentationPixelMatrixHash'])
            self.assertEqual(px.png_bytes(im),data)
        # Selection did not edit the candidate comparison or promote siblings.
        self.assertEqual(list(here.rglob('*.png')),[here/'projected/presentation.png'])
        for name in ('white','mid-gray'):
            self.assertEqual(m.read(here/'prepared'/name/'proposal.json')['authority'],g.CLOSED)
            self.assertFalse((here/'prepared'/name/'admission.json').exists())
        comparison=m.read(here/'prepared/comparison.json')
        self.assertEqual(comparison['authority'],g.CLOSED)
        self.assertNotIn('selection',comparison)

    def test_real_parent_is_independently_addressable_and_unchanged_by_grounding(self):
        pixel_root=ROOT/'specimens/mangalize-004/executed'
        ex=m.read(pixel_root/'execution.json')
        data=(pixel_root/'manga-page.png').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),'2fc8d655c634c8b8ed5f986dc052dc3970b2fad4c9dfaac2cb676ab7e0e85c74')
        with Image.open(io.BytesIO(data)) as page:
            self.assertEqual(px.matrix_hash(page),'ee94091bcc3bfe2fc4deb6a8986cf47df3a448b57fcde0ea47ed57e7390b9ca5')
            self.assertEqual(page.getchannel('A').getextrema(),(0,255))
        self.assertNotEqual(ex['finalArtifact']['encodedArtifactSha256'],m.read(ROOT/'specimens/mangalize-005/projected/projection.json')['presentationEncodedArtifactSha256'])


if __name__ == '__main__':
    unittest.main()

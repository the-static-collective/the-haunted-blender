import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from haunted_blender import mangalize as m, manga_atlas as atlas, manga_quarantine as q
from haunted_blender import manga_performed_use as use, parts_harvester as parts, stage_compost as stage

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'specimens/mangalize-001'
RELEASE = ROOT / 'specimens/mangalize-002/released'


def geometry(x=32000, z=10):
    return {'canvas': {'widthPixels': 640, 'heightPixels': 360, 'origin': 'top-left'},
        'xMilliPixels': x, 'yMilliPixels': 48000, 'z': z, 'scaleMillionths': 2000000,
        'rotationMilliDegrees': 0, 'opacityMillionths': 1000000, 'anchor': 'top-left',
        'fit': 'native-scale', 'crop': None, 'overflow': 'clip-to-canvas', 'timeRange': None}


class PerformedUse003Tests(unittest.TestCase):
    def setUp(self):
        from PIL import Image, ImageDraw
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        # Independent synthetic source and fake authorities; no test admits a
        # performed role for any of the three real founding descendants.
        image = Image.new('RGB', (64, 96), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle((4, 8, 59, 90), fill=(90, 190, 130), outline='black', width=2)
        draw.line((8, 20, 54, 75), fill='blue', width=3)
        image.save(self.source / 'page.png')
        m.persist(self.source / 'source.json', {'fictionalTestOnly': True, 'id': 'performed-use-test:source'})
        binding = m.binding(self.source, self.source / 'source.json')
        closed = {k: False for k in m.GRANTS}
        page = m.read(OLD / 'lemonpress/works/manga-press-specimen/manga/001/pages/page-05.json')
        page.update(editionId='performed-use-test:edition', issueId='performed-use-test:issue', pageId='synthetic-page',
            sourceImage=m.binding(self.source, self.source / 'page.png'), rightsSource=binding,
            sourceLineage=[binding], narrativeReferences=[], dialogueCaptionReferences=[], grants=closed)
        page['pageHash'] = atlas._hash({k: v for k, v in page.items() if k != 'pageHash'})
        locator = {k: page[k] for k in ('editionId', 'issueId', 'pageId', 'pageHash')}
        locator.update(workId='performed-use-test:work', editionHash=atlas._hash({'fictionalEdition': page['pageHash']}), sourceImageSha256=page['sourceImage']['sha256'])
        handoff = m.read(OLD / 'lemonpress/works/manga-press-specimen/manga/001/blender-compatibility-handoff.json')
        handoff.update({k: locator[k] for k in ('workId', 'editionId', 'editionHash', 'issueId')})
        handoff.update(grants=closed, source=binding, admission=binding, editionAdmission=binding,
            orderingContext={'readingDirection': 'ltr', 'placements': [], 'spreads': []},
            allowedAdaptationScope=['fictional independent test geometry'], pages=[{'identity': locator,
                'sourceImage': page['sourceImage'], 'rightsSource': binding, 'grants': closed}])
        handoff['handoffHash'] = atlas._hash({k: v for k, v in handoff.items() if k != 'handoffHash'})
        m.persist(self.source / 'page.json', page)
        m.persist(self.source / 'handoff.json', handoff)
        grant = m.source_grant(locator, handoff['handoffHash'], authority_ref='fictional-test:harvest-grant',
            source_repository='synthetic-test/no-real-work', source_commit='c' * 40)
        m.persist(self.source / 'harvest.json', grant)
        request = m.make_request(self.source, self.source / 'handoff.json', self.source / 'page.json', page_id='synthetic-page',
            operations=['harvest'], authority_ref='fictional-test:request', source_repository='synthetic-test/no-real-work',
            source_commit='c' * 40, grant_paths=[self.source / 'harvest.json'])
        admission = m.admit(request, allow=['harvest'], authority_ref='fictional-test:harvest-admission')
        self.ancestor = self.root / 'harvested'
        m.execute(self.source, request, admission, self.ancestor)
        record = q.quarantine_set(self.source, self.ancestor)
        ids = [next(r['assetId'] for r in record['members'] if r['kind'] == kind) for kind in ('panel', 'region-candidate', 'edge-mask')]
        selection = q.select(record, asset_ids=ids, authority_ref='fictional-test:selector', reason='mechanically distinct kinds')
        grant = q.asset_grant(record, selection, asset_ids=ids, permissions={k: k in ('pixelReuse', 'derivativeReuse') for k in m.GRANTS}, authority_ref='fictional-test:later-material-grant')
        # Match the historical CLI custody boundary: consume canonical files.
        record, selection, grant = (json.loads(atlas._stable(value)) for value in (record, selection, grant))
        self.release = self.root / 'released'
        q.execute(self.source, self.ancestor, record, selection, grant, self.release)
        self.drawer = use.verified_drawer(self.source, self.ancestor, self.release)
        self.asset = ids[0]
        self.role = self.role_for()
        self.placement = self.place_for(self.role)

    def role_for(self, role='poster', asset=None):
        return use.role_proposal(self.drawer, asset_id=asset or self.asset, role=role,
            rationale='Bounded rectangular pixels proposed for a structural role; no depicted identity inferred.', authority_ref='fictional-test:role-author')

    def place_for(self, role, **changes):
        placement = geometry()
        placement.update(changes)
        return use.placement_proposal(self.drawer, role, placement=placement, rationale='Explicit static authored geometry.', authority_ref='fictional-test:placement-author')

    def bundle(self, role=None, placement=None):
        role = self.role if role is None else role
        placement = self.place_for(role) if placement is None else placement
        return {'role': role, 'placement': placement, 'admission': use.admit(self.drawer, role, placement, authority_ref='fictional-test:separate-performed-use-approval')}

    def test_role_replay_is_byte_identical_and_create_only(self):
        self.assertEqual(atlas._stable(self.role), atlas._stable(self.role_for()))
        path = self.root / 'role.json'
        m.persist(path, self.role)
        m.persist(path, self.role_for())
        with self.assertRaisesRegex(ValueError, 'create-only'):
            m.persist(path, self.role_for('cutaway'))

    def test_placement_replay_and_all_numbers_explicit(self):
        self.assertEqual(atlas._stable(self.placement), atlas._stable(self.place_for(self.role)))
        for key, value in [('scaleMillionths', 2.0), ('xMilliPixels', True), ('rotationMilliDegrees', float('nan')),
                           ('opacityMillionths', 1000001), ('timeRange', {'start': 0, 'end': 1}), ('crop', [0, 0, 1, 1])]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.place_for(self.role, **{key: value})
        incomplete = geometry()
        del incomplete['rotationMilliDegrees']
        with self.assertRaises(ValueError):
            use.validate_placement(incomplete)

    def test_proposals_and_material_grant_cannot_self_admit(self):
        self.assertFalse(any(self.role['authority'].values()))
        self.assertFalse(any(self.placement['authority'].values()))
        for ref in (self.role['proposingAuthority'], self.placement['proposingAuthority'],
                    self.role['material']['provenance']['eventLineage'][1]['grantHash']):
            with self.assertRaisesRegex(ValueError, 'self-admit'):
                use.admit(self.drawer, self.role, self.placement, authority_ref=ref)
        with self.assertRaises(ValueError):
            use.performance_layout(self.drawer, self.ancestor, [{'role': self.role, 'placement': self.placement}])

    def test_one_asset_multiple_possible_roles_changes_no_material(self):
        before = atlas._stable(self.drawer)
        other = self.role_for('cutaway')
        self.assertNotEqual(self.role['roleHash'], other['roleHash'])
        self.assertEqual(self.role['material'], other['material'])
        self.assertEqual(atlas._stable(self.drawer), before)
        self.assertFalse(any(other['authority'].values()))

    def test_admission_use_layout_replay_is_deterministic_without_render(self):
        b = self.bundle()
        self.assertEqual(b['admission'], self.bundle()['admission'])
        first = use.execute(self.source, self.ancestor, self.release, [b], self.root / 'performed')
        before = m.tree_bytes(self.root / 'performed')
        self.assertEqual(use.verify(self.source, self.ancestor, self.release, [b], self.root / 'performed'), first['layoutHash'])
        self.assertEqual(m.tree_bytes(self.root / 'performed'), before)
        reread = {kind: m.read(self.root / 'performed/000' / (kind + '.json')) for kind in b}
        self.assertEqual(use.execute(self.source, self.ancestor, self.release, [reread], self.root / 'performed'), first)
        self.assertEqual(first['renderedArtifacts'], [])
        self.assertIsNone(first['publicationStateChange'])
        self.assertEqual(first['authority'], use.ADMITTED)
        self.assertTrue(all(path.endswith(('.json', '.md')) for path in before))

    def test_same_pixels_different_role_or_placement_distinct_use_identity(self):
        b = self.bundle()
        first = use.perform(self.drawer, self.ancestor, **b)
        second_role = self.role_for('cutaway')
        second = use.perform(self.drawer, self.ancestor, **self.bundle(second_role))
        third = use.perform(self.drawer, self.ancestor, **self.bundle(placement=self.place_for(self.role, xMilliPixels=128000)))
        self.assertEqual(len({r['useHash'] for r in (first, second, third)}), 3)
        self.assertEqual(len({r['material']['sha256'] for r in (first, second, third)}), 1)

    def test_complete_custody_and_admitted_use_id_survive_performance(self):
        b = self.bundle()
        performed = use.perform(self.drawer, self.ancestor, **b)
        row = next(r for r in self.drawer['artifacts'] if r['id'] == self.asset)
        self.assertEqual(performed['material']['admittedUseId'], row['admittedUseId'])
        self.assertEqual(performed['material']['provenance'], row['provenance'])
        self.assertEqual(performed['provenance']['eventLineage'][:2], row['provenance']['eventLineage'])
        self.assertEqual(performed['provenance']['foreignAncestry'], row['provenance']['foreignAncestry'])
        self.assertEqual(set(performed['provenance']['foreignAncestry'][0]['locator']),
            {'workId', 'editionId', 'editionHash', 'issueId', 'pageId', 'pageHash', 'sourceImageSha256'})
        self.assertEqual(performed['provenance']['eventLineage'][2]['admissionHash'], b['admission']['admissionHash'])
        self.assertFalse(any(performed['material']['provenance']['authority'].values()))

    def test_roles_and_placements_assert_no_semantic_identity_or_source_fact(self):
        b = self.bundle()
        performed = use.perform(self.drawer, self.ancestor, **b)
        for record in (*b.values(), performed):
            self.assertEqual(record['semanticNonclaims'], use.NONCLAIMS)
            self.assertEqual(set(record['semanticNonclaims'].values()), {None})

    def test_no_permission_expansion_or_sibling_performed_use(self):
        before = atlas._stable(self.drawer)
        layout = use.performance_layout(self.drawer, self.ancestor, [self.bundle()])
        self.assertEqual(len(layout['performedUses']), 1)
        performed = layout['performedUses'][0]
        self.assertEqual(performed['effectivePermissions'], {k: k in ('pixelReuse', 'derivativeReuse') for k in m.GRANTS})
        self.assertEqual(performed['authority'], use.ADMITTED)
        self.assertEqual(atlas._stable(self.drawer), before)
        siblings = [r for r in self.drawer['artifacts'] if r['id'] != self.asset]
        self.assertTrue(all(not any(row['authority'].values()) for row in siblings))

    def test_unpromoted_quarantined_asset_cannot_be_proposed(self):
        promotion = m.read(self.release / 'promotion.json')
        with self.assertRaisesRegex(ValueError, 'promoted asset'):
            self.role_for(asset=promotion['stillQuarantined'][0]['assetId'])

    def test_reuse_without_derivative_ceiling_refuses(self):
        drawer = copy.deepcopy(self.drawer)
        row = next(r for r in drawer['artifacts'] if r['id'] == self.asset)
        row['rights']['derivativeReuse'] = False
        row['provenance']['effectivePermissions']['derivativeReuse'] = False
        drawer['id'] = 'parts-drawer:' + atlas._hash({k: v for k, v in drawer.items() if k != 'id'})[:24]
        with self.assertRaisesRegex(ValueError, 'permission ceiling'):
            use.role_proposal(drawer, asset_id=self.asset, role='poster', rationale='test', authority_ref='test')

    def test_tampered_role_refuses_even_rehashed_forged_custody(self):
        bad = copy.deepcopy(self.role)
        bad['material']['provenance']['foreignAncestry'] = []
        for record in (bad, use.seal('role', bad)):
            with self.assertRaises(ValueError):
                use.verify_role(self.drawer, record)

    def test_tampered_placement_refuses_even_rehashed_role_binding(self):
        bad = copy.deepcopy(self.placement)
        bad['roleProposalHash'] = '0' * 64
        for record in (bad, use.seal('placement', bad)):
            with self.assertRaises(ValueError):
                use.verify_placement(self.drawer, self.role, record)

    def test_tampered_admission_refuses_even_rehashed_authority_expansion(self):
        b = self.bundle()
        for change in ('authority', 'admittedPlacement', 'admittedRole', 'permissionCeiling'):
            bad = copy.deepcopy(b['admission'])
            if change == 'authority': bad[change]['render'] = True
            elif change == 'admittedPlacement': bad[change]['xMilliPixels'] += 1000
            elif change == 'admittedRole': bad[change] = 'cutaway'
            else: bad[change]['publicationReuse'] = True
            for record in (bad, use.seal('admission', bad)):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    use.perform(self.drawer, self.ancestor, b['role'], b['placement'], record)

    def test_tampered_performed_use_and_layout_refuse_independent_replay(self):
        b = self.bundle()
        layout = use.performance_layout(self.drawer, self.ancestor, [b])
        record = copy.deepcopy(layout['performedUses'][0])
        record['provenance']['eventLineage'] = []
        with self.assertRaises(ValueError):
            use.verify_use(self.drawer, self.ancestor, b, use.seal('use', record))
        layout['performedUses'] = [use.seal('use', record)]
        with self.assertRaises(ValueError):
            use.verify_layout(self.drawer, self.ancestor, [b], use.seal('layout', layout))

    def test_pixels_and_historical_drawer_mutation_refuse(self):
        b = self.bundle()
        row = next(r for r in self.drawer['artifacts'] if r['id'] == self.asset)
        path = parts.resolve_drawer_artifact(self.drawer, row, artifact_root=self.ancestor)
        path.write_bytes(path.read_bytes() + b'tamper')
        with self.assertRaises(ValueError):
            use.perform(self.drawer, self.ancestor, **b)
        with self.assertRaises(ValueError):
            use.verified_drawer(self.source, self.ancestor, self.release)

    def test_composition_cannot_write_inside_historical_evidence(self):
        with self.assertRaisesRegex(ValueError, 'ancestor evidence'):
            use.execute(self.source, self.ancestor, self.release, [self.bundle()], self.release / 'performed')

    def test_layout_order_ignores_input_serialization_order_and_refuses_duplicates(self):
        a = self.bundle()
        role = self.role_for('cutaway')
        b = self.bundle(role, self.place_for(role, z=20))
        self.assertEqual(use.performance_layout(self.drawer, self.ancestor, [a, b]), use.performance_layout(self.drawer, self.ancestor, [b, a]))
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            use.performance_layout(self.drawer, self.ancestor, [a, a])

    def test_three_independent_synthetic_uses_persist_without_source_changes(self):
        old_source, old_harvest, old_release = (m.tree_bytes(p) for p in (self.source, self.ancestor, self.release))
        bundles = []
        for index, row in enumerate(self.drawer['artifacts']):
            role = self.role_for(('poster', 'cutaway', 'texture')[index], row['id'])
            bundles.append(self.bundle(role, self.place_for(role, xMilliPixels=32000 + index * 192000, z=10 + index)))
        out = self.root / 'three-uses'
        layout = use.execute(self.source, self.ancestor, self.release, bundles, out)
        self.assertEqual(len(layout['performedUses']), 3)
        self.assertEqual(use.execute(self.source, self.ancestor, self.release, list(reversed(bundles)), out), layout)
        self.assertEqual((m.tree_bytes(self.source), m.tree_bytes(self.ancestor), m.tree_bytes(self.release)), (old_source, old_harvest, old_release))
        self.assertEqual(len(list(out.glob('*/use.json'))), 3)
        (out / 'layout.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'persisted event differs'):
            use.verify(self.source, self.ancestor, self.release, bundles, out)

    def test_generic_stage_seam_preserves_opaque_full_custody(self):
        drawer = copy.deepcopy(self.drawer)
        for row in drawer['artifacts']:
            row['provenance']['futureSystem'] = {'opaqueCustody': ['one', 'two']}
        drawer['id'] = 'parts-drawer:' + atlas._hash({k: v for k, v in drawer.items() if k != 'id'})[:24]
        role = use.role_proposal(drawer, asset_id=self.asset, role='poster', rationale='geometry only', authority_ref='test:proposal')
        placement = use.placement_proposal(drawer, role, placement=geometry(), rationale='static geometry', authority_ref='test:placement')
        admission = use.admit(drawer, role, placement, authority_ref='test:external-approval')
        layout = stage.admitted_plan(drawer, artifact_root=self.ancestor, bundles=[{'role': role, 'placement': placement, 'admission': admission}])
        self.assertEqual(layout['performedUses'][0]['provenance']['futureSystem'], {'opaqueCustody': ['one', 'two']})
        with self.assertRaises(ValueError):
            stage.apply_to_performance({'schema': 'haunted-blender/puppet-performance/v1'}, layout)

    def test_legacy_stage_cannot_automatically_place_promoted_material(self):
        with self.assertRaisesRegex(ValueError, 'Explicit performed-use admission'):
            stage.plan(self.drawer, width=640, height=360, duration_seconds=1)
        with self.assertRaises(ValueError):
            stage.admitted_plan(self.drawer, artifact_root=self.ancestor, bundles=[{'role': self.role, 'placement': self.placement}])

    def test_cli_requires_separate_admission_file(self):
        proposals = self.root / 'proposal'
        m.persist(proposals / 'role.json', self.role)
        m.persist(proposals / 'placement.json', self.placement)
        result = subprocess.run([sys.executable, '-m', 'haunted_blender.manga_performed_use_cli', 'compose',
            str(self.source), str(self.ancestor), str(self.release), str(self.root / 'layout'), '--use', str(proposals)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / 'layout').exists())


class FoundingCustody003Tests(unittest.TestCase):
    def test_approved_real_composition_replays_all_three_exact_uses_and_custody(self):
        here = ROOT / 'specimens/mangalize-003'
        approval = m.read(here / 'authority/user-performed-use-approval.json')
        self.assertEqual(approval['authority'], use.ADMITTED)
        self.assertFalse(approval['motionAdaptation'])
        bundles = [{k: m.read(path / (k + '.json')) for k in ('role', 'placement', 'admission')}
                   for path in sorted((here / 'admitted-inputs').iterdir())]
        layout = m.read(here / 'performed/layout.json')
        self.assertEqual(use.verify(OLD / 'lemonpress', OLD / 'executed', RELEASE, bundles, here / 'performed'), layout['layoutHash'])
        self.assertEqual(layout['layoutHash'], 'fa198528b8454af1cb06ec3dde25c70d57db667f67591ac65234f3d12cebc46a')
        self.assertEqual(len(layout['performedUses']), 3)
        self.assertEqual(layout['renderedArtifacts'], [])
        drawer = m.read(RELEASE / 'parts-drawer.json')
        rows = {row['id']: row for row in drawer['artifacts']}
        approved = {row['assetId']: row for row in approval['approvedUses']}
        self.assertEqual(set(approved), set(rows))
        for record in layout['performedUses']:
            mat = record['material']
            row, scope = rows[mat['assetId']], approved[mat['assetId']]
            self.assertEqual(mat['admittedUseId'], row['admittedUseId'])
            self.assertEqual(mat['provenance'], row['provenance'])
            self.assertEqual(record['provenance']['eventLineage'][:2], row['provenance']['eventLineage'])
            self.assertEqual(record['provenance']['foreignAncestry'], row['provenance']['foreignAncestry'])
            self.assertEqual(record['performedRole'], scope['role'])
            self.assertEqual(record['placement'], scope['placement'])
            self.assertEqual(record['roleProposalHash'], scope['roleProposalHash'])
            self.assertEqual(record['placementProposalHash'], scope['placementProposalHash'])
            self.assertEqual(record['authority'], use.ADMITTED)
            self.assertEqual(record['semanticNonclaims'], use.NONCLAIMS)
        self.assertEqual(len(m.read(RELEASE / 'promotion.json')['stillQuarantined']), 22)
        result = subprocess.run([sys.executable, str(here / 'verify_founding.py')], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_approval_cannot_follow_valid_changed_role_or_placement(self):
        here = ROOT / 'specimens/mangalize-003/admitted-inputs/panel'
        drawer = use.verified_drawer(OLD / 'lemonpress', OLD / 'executed', RELEASE)
        role, placement, admission = (m.read(here / (k + '.json')) for k in ('role', 'placement', 'admission'))
        alternate = use.role_proposal(drawer, asset_id=role['material']['assetId'], role='cutaway',
            rationale='Alternate structural proposal only; no semantic claim.', authority_ref='test:unadmitted-alternative-role')
        alternate_place = use.placement_proposal(drawer, alternate, placement=placement['proposedPlacement'],
            rationale='Alternate unadmitted proposal.', authority_ref='test:placement-proposal')
        changed = copy.deepcopy(placement['proposedPlacement'])
        changed['xMilliPixels'] += 1000
        moved = use.placement_proposal(drawer, role, placement=changed, rationale='Unadmitted move proposal.', authority_ref='test:placement-proposal')
        for proposed_role, proposed_place in ((alternate, alternate_place), (role, moved)):
            with self.assertRaisesRegex(ValueError, 'admission exceeds'):
                use.perform(drawer, OLD / 'executed', proposed_role, proposed_place, admission)

    def test_all_historical_001_002_files_match_exact_parent_pin(self):
        pin = m.read(ROOT / 'specimens/mangalize-003/ANCESTOR_PIN.json')
        self.assertEqual(pin['commit'], '8b4f7da114e55150dfb564fea171c827bcf8759a')
        for row in pin['files']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'], row['path'])

    def test_exact_founding_proposals_are_unadmitted_and_preserve_complete_custody(self):
        drawer = use.verified_drawer(OLD / 'lemonpress', OLD / 'executed', RELEASE)
        root = ROOT / 'specimens/mangalize-003/prepared'
        roles = set()
        for path in sorted(root.glob('*/role.json')):
            role = m.read(path)
            placement = m.read(path.parent / 'placement.json')
            use.verify_placement(drawer, role, placement)
            row = next(r for r in drawer['artifacts'] if r['id'] == role['material']['assetId'])
            self.assertEqual(role['material']['provenance'], row['provenance'])
            self.assertEqual(role['material']['admittedUseId'], row['admittedUseId'])
            self.assertFalse(any(role['authority'].values()))
            self.assertFalse(any(placement['authority'].values()))
            self.assertFalse((path.parent / 'admission.json').exists())
            roles.add(role['proposedRole'])
        self.assertEqual(roles, {'poster', 'cutaway', 'texture'})
        self.assertFalse((root / 'layout.json').exists())
        self.assertIn('PERFORMED USE READY — ADMISSION REQUIRED', (root / 'TRACE.md').read_text())

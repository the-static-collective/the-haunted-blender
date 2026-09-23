"""N6 test suite: synthetic private fixtures, real frame rendering, lineage and refusals."""
import copy
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from haunted_blender import (
    alchemy, catalog, contour_material as n4, correspondence,
    living_mesh, living_object as n5, object_events as n6, project, render,
)

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None


@unittest.skipUnless(Image is not None, "N6 uses optional Pillow for local object rendering")
class ObjectEventsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.root = self.home / "vault"
        self.photos = self.home / "synthetic"
        self.photos.mkdir()
        catalog.init(self.root)
        self.contours = {
            "body": (
                [[.14,.3],[.36,.3],[.36,.7],[.14,.7]],
                [[.40,.3],[.62,.3],[.62,.7],[.40,.7]],
            ),
            "rim": (
                [[.66,.3],[.88,.3],[.88,.7],[.66,.7]],
                [[.42,.32],[.64,.32],[.64,.72],[.42,.72]],
            ),
        }
        for name, bg, colors, target in (
            ("source", (28, 98, 170), [(235,40,25),(38,220,55)], False),
            ("target", (55,125,65), [(230,50,35),(32,65,235)], True),
        ):
            picture = Image.new("RGB", (320,180), bg)
            for bounds, color in zip(self.contours.values(), colors):
                polygon = bounds[1] if target else bounds[0]
                ImageDraw.Draw(picture).polygon([(x*319,y*179) for x,y in polygon], fill=color)
            picture.save(self.photos / (name+".png"))
            picture.close()
        self.assertEqual(catalog.scan(self.root, self.photos)["indexed_or_changed"], 2)
        con = catalog.connect(self.root)
        self.ids = {Path(row["path"]).stem: row["id"]
                    for row in con.execute("SELECT id,path FROM assets")}
        con.close()
        n1_recipe = alchemy.create(self.root, self.ids["source"], self.ids["target"],
                                   statement="Artist proposes a two-part object")
        self.n1 = alchemy.freeze(self.root, n1_recipe["id"])
        points = [{"id":"left","from":[.1,.1],"to":[.1,.1]},
                  {"id":"right","from":[.9,.1],"to":[.9,.1]}]
        n2_recipe = correspondence.create(self.root, self.n1, points)
        self.n2 = correspondence.freeze(self.root, n2_recipe["id"])
        n3_recipe = living_mesh.create(self.root, self.n2, living_mesh.grid())
        self.n3 = living_mesh.freeze(self.root, n3_recipe["id"])
        self.n4 = {}
        for name, (source, target) in self.contours.items():
            part = n4.create(self.root, self.n3, source, target,
                             material_mode="source-only" if name=="body" else "crossfade")
            self.n4[name] = n4.freeze(self.root, part["id"])
        layers = [
            {"name":"body","snapshot":str(self.n4["body"]),"z":0,"delay_frames":0,"opacity":1.},
            {"name":"rim","snapshot":str(self.n4["rim"]),"z":1,"delay_frames":20,"opacity":1.},
        ]
        n5_recipe = n5.create(self.root, layers)
        self.n5 = n5.freeze(self.root, n5_recipe["id"])

    def parts(self):
        return [
            {"id":"body","source_layer_name":"body","role":"primary-mass","initial":True},
            {"id":"rim","source_layer_name":"rim","role":"rim","initial":True},
            {"id":"left","source_layer_name":"body","role":"split-child","initial":False},
            {"id":"right","source_layer_name":"body","role":"split-child","initial":False},
            {"id":"assembled","source_layer_name":"body","role":"joined-part","initial":False},
            {"id":"shadow","source_layer_name":"rim","role":"shadow","initial":False},
        ]

    def events(self):
        return [
            {"id":"birth-shadow","type":"birth","from":[],"to":["shadow"],"start_frame":5,"end_frame":12},
            {"id":"split-body","type":"split","from":["body"],"to":["left","right"],"start_frame":8,"end_frame":16},
            {"id":"join-body","type":"join","from":["left","right"],"to":["assembled"],"start_frame":20,"end_frame":30},
            {"id":"death-rim","type":"death","from":["rim"],"to":[],"start_frame":32,"end_frame":42},
        ]

    def make(self, **opts):
        return n6.create(self.root, self.n5, self.parts(), self.events(), **opts)

    def test_all_four_events_and_lineage_and_parent_immutability(self):
        originals = [p.read_bytes() for p in (self.n1,self.n2,self.n3,self.n5,*self.n4.values())]
        recipe = self.make()
        frozen = n6.freeze(self.root, recipe["id"])
        self.assertEqual(frozen, n6.freeze(self.root, recipe["id"]))
        spec = n6.plan(self.root, frozen)
        self.assertEqual(spec["renderer"], "pillow-object-events-ffmpeg/v1")
        self.assertEqual(len(spec["events"]), 4)
        self.assertEqual(spec["lineage"]["left"]["produced_by"], ["split-body"])
        self.assertEqual(spec["lineage"]["left"]["consumed_by"], ["join-body"])
        self.assertEqual([p.read_bytes() for p in (self.n1,self.n2,self.n3,self.n5,*self.n4.values())], originals)
        self.assertEqual(n5.plan(self.root,self.n5)["renderer"], "pillow-layered-object-ffmpeg/v1")
        self.assertEqual(n4.plan(self.root,self.n4["body"])["renderer"], "pillow-contour-fan-ffmpeg/v1")
        self.assertEqual(living_mesh.plan(self.root,self.n3)["renderer"], "pillow-triangle-mesh-ffmpeg/v1")
        self.assertEqual(correspondence.plan(self.root,self.n2)["renderer"], "pillow-similarity-ffmpeg/v1")
        self.assertEqual(alchemy.plan(self.root,self.n1)["adapter"], "ffmpeg-alchemy-crossfade/v1")
        film = project.new_film(self.root, "Unmodified N0")
        scene = project.add_scene(self.root, film["id"], "Opening")
        project.add_shot(self.root, film["id"], scene["id"], self.ids["source"], 750)
        self.assertEqual(render.plan(self.root,project.freeze(self.root,film["id"]))["adapter"],
                         "ffmpeg-static-storyboard/v1")

    def test_frame_window_birth_split_join_death(self):
        recipe = self.make()
        at = lambda f: n6.frame_state(recipe, f)["effective_visibility"]
        self.assertEqual(at(0)["body"], 1.)
        self.assertEqual(at(0)["shadow"], 0.)
        self.assertEqual(at(5)["shadow"], 0.)
        self.assertEqual(at(12)["shadow"], 1.)
        self.assertEqual(at(12)["body"], .5)
        self.assertEqual(at(12)["left"], .5)
        self.assertEqual(at(16)["body"], 0.)
        self.assertEqual(at(16)["right"], 1.)
        self.assertEqual(at(20)["assembled"], 0.)
        self.assertEqual(at(25)["assembled"], .5)
        self.assertEqual(at(25)["left"], .5)
        self.assertEqual(at(30)["assembled"], 1.)
        self.assertEqual(at(30)["right"], 0.)
        self.assertEqual(at(42)["rim"], 0.)
        self.assertEqual(at(48)["assembled"], 1.)

    def test_unordered_event_json_has_identical_canonical_frame_history(self):
        parts=self.parts()
        forward=self.events()
        reverse=list(reversed(self.events()))
        first=n6.create(self.root,self.n5,parts,forward)
        second=n6.create(self.root,self.n5,parts,reverse)
        self.assertEqual(
            [n6.frame_state(first,frame)["effective_visibility"] for frame in range(49)],
            [n6.frame_state(second,frame)["effective_visibility"] for frame in range(49)],
        )
        self.assertEqual(
            n6.plan(self.root,n6.freeze(self.root,first["id"]))["lineage"],
            n6.plan(self.root,n6.freeze(self.root,second["id"]))["lineage"],
        )

    def test_reserved_and_unknown_types_refused(self):
        bad=self.events()
        bad[0]["type"]="open"
        with self.assertRaisesRegex(ValueError,"Reserved future event is not implemented"):
            n6.create(self.root,self.n5,self.parts(),bad)
        bad=self.events()
        bad[0]["type"]="invent"
        with self.assertRaisesRegex(ValueError,"Unknown event type"):
            n6.create(self.root,self.n5,self.parts(),bad)

    def test_bad_cardinality_and_unrecognized_n5_source_refused(self):
        bad=self.events()
        bad[1]["to"]=["left"]
        with self.assertRaisesRegex(ValueError,"cardinality"):
            n6.create(self.root,self.n5,self.parts(),bad)
        parts=self.parts()
        parts[2]["source_layer_name"]="unknown_layer"
        with self.assertRaisesRegex(ValueError,"absent from frozen N5"):
            n6.create(self.root,self.n5,parts,self.events())
        parts=self.parts()
        parts[0]["initial"]=False
        with self.assertRaisesRegex(ValueError,"Noninitial part has no producing event"):
            n6.create(self.root,self.n5,parts,self.events())

    def test_double_birth_dead_before_birth_and_illegal_reused_identity_refused(self):
        events=self.events()
        events.append({"id":"again","type":"birth","from":[],"to":["shadow"],"start_frame":14,"end_frame":19})
        with self.assertRaisesRegex(ValueError,"duplicate producing event"):
            n6.create(self.root,self.n5,self.parts(),events)
        events=self.events()
        events[2]["start_frame"]=15
        events[2]["end_frame"]=25
        with self.assertRaisesRegex(ValueError,"before its birth completes|does not exist"):
            n6.create(self.root,self.n5,self.parts(),events)
        events=self.events()
        events[2]["to"]=["body"]
        with self.assertRaisesRegex(ValueError,"duplicate or contradictory lifecycle|cannot be born"):
            n6.create(self.root,self.n5,self.parts(),events)
        bad=self.events()
        bad[0]["start_frame"]=12
        bad[0]["end_frame"]=12
        with self.assertRaisesRegex(ValueError,"at least one frame"):
            n6.create(self.root,self.n5,self.parts(),bad)

    def test_duplicate_consumption_and_unknown_part_refused(self):
        events=self.events()
        events.append({"id":"death-left","type":"death","from":["left"],"to":[],"start_frame":35,"end_frame":40})
        with self.assertRaisesRegex(ValueError,"consumed twice"):
            n6.create(self.root,self.n5,self.parts(),events)
        events=self.events()
        events[1]["from"]=["not_existing"]
        with self.assertRaisesRegex(ValueError,"unknown or repeated part"):
            n6.create(self.root,self.n5,self.parts(),events)

    def test_immutable_revision_tamper_and_source_mutation_refused(self):
        old=self.make()
        first=n6.freeze(self.root,old["id"])
        altered=self.events()
        altered[0]["start_frame"]=6
        newer=n6.create(self.root,self.n5,self.parts(),altered,revises=old["id"])
        second=n6.freeze(self.root,newer["id"])
        self.assertNotEqual(first,second)
        self.assertEqual(newer["revises"],old["id"])
        self.assertEqual(n6.plan(self.root,first)["events"][0]["start_frame"],5)
        self.assertEqual(n6.plan(self.root,second)["events"][0]["start_frame"],6)
        packet=json.loads(first.read_text(encoding="utf-8"))
        packet["recipe"]["events"][0]["end_frame"]=13
        first.write_text(json.dumps(packet),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"snapshot hash"):
            n6.plan(self.root,first)
        (self.photos/"source.png").write_bytes(b"mutated source after freeze")
        with self.assertRaisesRegex(ValueError,"Frozen source missing or changed"):
            n6.plan(self.root,second)

    @unittest.skipUnless(shutil.which("ffmpeg"),"Local FFmpeg required for N6 video proof")
    def test_actual_video_transparent_png_and_receipt(self):
        recipe=self.make()
        snap=n6.freeze(self.root,recipe["id"])
        output=self.home/"events.mp4"
        png=self.home/"midpoint.png"
        receipt=n6.render(self.root,snap,output,alpha_preview_out=png)
        self.assertEqual(receipt["status"],"scoped_complete")
        self.assertEqual(receipt["frame_count"],49)
        self.assertEqual(len(receipt["frame_receipts"]),49)
        self.assertEqual(receipt["output_sha256"],hashlib.sha256(output.read_bytes()).hexdigest())
        self.assertEqual(receipt["alpha_preview_sha256"],hashlib.sha256(png.read_bytes()).hexdigest())
        self.assertGreater(receipt["frame_receipts"][24]["overlap_px"],100)
        self.assertEqual(receipt["frame_receipts"][48]["effective_visibility"]["body"],0.)
        self.assertEqual(receipt["frame_receipts"][48]["effective_visibility"]["assembled"],1.)
        with Image.open(png) as im:
            self.assertEqual(im.mode,"RGBA")
            self.assertEqual(im.getpixel((5,5))[3],0)
            self.assertGreater(im.getpixel((120,90))[3],0)
        self.assertTrue(output.with_suffix(".mp4.receipt.json").is_file())
        with self.assertRaises(FileExistsError):
            n6.render(self.root,snap,output,alpha_preview_out=png)
        cmd=["ffmpeg","-nostdin","-v","error","-i",str(output),
             "-vf","select=eq(n\\,48)","-frames:v","1",
             "-f","image2pipe","-vcodec","png","-"]
        final=subprocess.run(cmd,check=True,capture_output=True).stdout
        with Image.open(BytesIO(final)) as im:
            self.assertEqual(im.size,(320,180))
            self.assertLess(max(abs(a-b) for a,b in
                                zip(im.convert("RGB").getpixel((5,5)),n4.DIAGNOSTIC_COLOR)),18)


if __name__=="__main__":
    unittest.main()

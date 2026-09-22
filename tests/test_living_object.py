"""N5 pressure tests: independently masked synthetic components and real local video."""
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
    living_mesh, living_object, project, render,
)

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None


@unittest.skipUnless(Image is not None, "Optional Pillow required for N5")
class LivingObjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
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
        for name, backdrop, colors, target in (
            ("source", (28, 98, 170), [(235,40,25),(38,220,55)], False),
            ("target", (55, 125, 65), [(230,50,35),(32,65,235)], True),
            ("plate", (95, 55, 35), [], False),
        ):
            picture = Image.new("RGB", (320,180), backdrop)
            for (part, bounds), color in zip(self.contours.items(), colors):
                polygon = bounds[1] if target else bounds[0]
                ImageDraw.Draw(picture).polygon([(x*319,y*179) for x,y in polygon], fill=color)
            picture.save(self.photos / (name + ".png"))
            picture.close()
        self.assertEqual(catalog.scan(self.root, self.photos)["indexed_or_changed"], 3)
        con = catalog.connect(self.root)
        self.ids = {Path(item["path"]).stem: item["id"]
                    for item in con.execute("SELECT id,path FROM assets")}
        con.close()
        n1 = alchemy.create(self.root, self.ids["source"], self.ids["target"],
                            statement="Two independently authored material regions")
        self.n1 = alchemy.freeze(self.root, n1["id"])
        landmarks = [
            {"id":"left","from":[.1,.1],"to":[.1,.1]},
            {"id":"right","from":[.9,.1],"to":[.9,.1]},
        ]
        n2 = correspondence.create(self.root,self.n1,landmarks)
        self.n2 = correspondence.freeze(self.root,n2["id"])
        n3 = living_mesh.create(self.root,self.n2,living_mesh.grid())
        self.n3 = living_mesh.freeze(self.root,n3["id"])
        self.parts = {}
        for name, (source, target) in self.contours.items():
            n4recipe = n4.create(self.root,self.n3,source,target,
                                 material_mode="source-only" if name=="body" else "crossfade")
            self.parts[name] = n4.freeze(self.root,n4recipe["id"])

    def layers(self, *, body_z=0, rim_z=1, body_opacity=1.0, rim_opacity=1.0,
               body_delay=0, rim_delay=20):
        return [
            {"name":"body", "snapshot":str(self.parts["body"]), "z":body_z,
             "delay_frames":body_delay,"opacity":body_opacity},
            {"name":"rim", "snapshot":str(self.parts["rim"]), "z":rim_z,
             "delay_frames":rim_delay,"opacity":rim_opacity},
        ]

    def make(self, **kwargs):
        return living_object.create(self.root, self.layers(**kwargs))

    def test_multi_layer_frozen_plan_and_old_contracts(self):
        original = [p.read_bytes() for p in (self.n1,self.n2,self.n3,*self.parts.values())]
        recipe = self.make()
        snap = living_object.freeze(self.root,recipe["id"])
        self.assertEqual(snap,living_object.freeze(self.root,recipe["id"]))
        plan = living_object.plan(self.root,snap)
        self.assertEqual([entry["name"] for entry in plan["ordered_layers"]],["body","rim"])
        self.assertEqual(plan["ordered_layers"][0]["material_mode"],"source-only")
        self.assertEqual(plan["ordered_layers"][1]["material_mode"],"crossfade")
        self.assertEqual(plan["ordered_layers"][1]["delay_frames"],20)
        self.assertEqual(plan["checks"]["alpha_overlap"],"measured_during_render")
        self.assertEqual(plan["parent_n3_sha256"],living_mesh._load(self.root,self.n3)[1])
        self.assertEqual([p.read_bytes() for p in (self.n1,self.n2,self.n3,*self.parts.values())],original)
        self.assertEqual(n4.plan(self.root,self.parts["body"])["renderer"],"pillow-contour-fan-ffmpeg/v1")
        self.assertEqual(living_mesh.plan(self.root,self.n3)["renderer"],"pillow-triangle-mesh-ffmpeg/v1")
        self.assertEqual(correspondence.plan(self.root,self.n2)["renderer"],"pillow-similarity-ffmpeg/v1")
        self.assertEqual(alchemy.plan(self.root,self.n1)["adapter"],"ffmpeg-alchemy-crossfade/v1")
        film = project.new_film(self.root,"Still N0")
        scene = project.add_scene(self.root,film["id"],"Opening")
        project.add_shot(self.root,film["id"],scene["id"],self.ids["source"],1000)
        self.assertEqual(render.plan(self.root,project.freeze(self.root,film["id"]))["adapter"],
                         "ffmpeg-static-storyboard/v1")

    def test_refuse_invalid_layer_identity_clock_opacity_and_order(self):
        bad = self.layers()
        bad[1]["name"]="body"
        with self.assertRaisesRegex(ValueError,"repeated layer name"):
            living_object.create(self.root,bad)
        bad = self.layers()
        bad[1]["z"]=0
        with self.assertRaisesRegex(ValueError,"unique integer"):
            living_object.create(self.root,bad)
        bad = self.layers()
        bad[1]["delay_frames"]=True
        with self.assertRaisesRegex(ValueError,"delay_frames"):
            living_object.create(self.root,bad)
        bad = self.layers()
        bad[0]["opacity"]=math.nan
        with self.assertRaisesRegex(ValueError,"opacity"):
            living_object.create(self.root,bad)
        bad = self.layers()
        bad[1]["snapshot"]=bad[0]["snapshot"]
        with self.assertRaisesRegex(ValueError,"cannot masquerade"):
            living_object.create(self.root,bad)
        with self.assertRaisesRegex(ValueError,"2-4"):
            living_object.create(self.root,self.layers()[:1])

    def test_incompatible_background_and_mutated_sources_refused(self):
        alt = n4.create(self.root,self.n3,*self.contours["rim"],
                        background_mode="clean-plate",clean_plate_asset_id=self.ids["plate"])
        different = n4.freeze(self.root,alt["id"])
        bad = self.layers()
        bad[1]["snapshot"]=str(different)
        with self.assertRaisesRegex(ValueError,"same exact frozen scene and background"):
            living_object.create(self.root,bad)
        recipe=self.make()
        snap=living_object.freeze(self.root,recipe["id"])
        (self.photos/"source.png").write_bytes(b"modified source")
        with self.assertRaisesRegex(ValueError,"Frozen source missing or changed"):
            living_object.plan(self.root,snap)

    def test_corrupt_snapshot_and_explicit_revision(self):
        base=self.make()
        frozen=living_object.freeze(self.root,base["id"])
        updated=living_object.create(self.root,self.layers(rim_z=-1,body_z=1),
                                     revises=base["id"])
        later=living_object.freeze(self.root,updated["id"])
        self.assertEqual(updated["revises"],base["id"])
        self.assertNotEqual(frozen,later)
        self.assertEqual(living_object.plan(self.root,frozen)["ordered_layers"][0]["name"],"body")
        self.assertEqual(living_object.plan(self.root,later)["ordered_layers"][0]["name"],"rim")
        altered=json.loads(frozen.read_text(encoding="utf-8"))
        altered["recipe"]["layers"][0]["opacity"]=.25
        frozen.write_text(json.dumps(altered),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"snapshot hash"):
            living_object.plan(self.root,frozen)

    def test_independent_clocks_overlap_and_occlusion_are_measured(self):
        recipe=self.make()
        snap=living_object.freeze(self.root,recipe["id"])
        packet,_=living_object._load(self.root,snap)
        members=living_object._parents(self.root,packet["recipe"])
        parts=[living_object._prepare_layer(x) for x in members]
        try:
            frame0,a=living_object._foreground_at(parts,0)
            frame24,b=living_object._foreground_at(parts,24)
            frame48,c=living_object._foreground_at(parts,48)
            self.assertEqual(a["layers"][1]["local_t"],0)
            self.assertGreater(b["layers"][0]["local_t"],b["layers"][1]["local_t"])
            self.assertEqual(c["layers"][0]["local_t"],1)
            self.assertEqual(c["layers"][1]["local_t"],1)
            self.assertEqual(a["overlap_px"],0)
            self.assertGreater(c["overlap_px"],100)
            self.assertEqual(frame0.getpixel((5,5))[3],0)
            # With z=1 the blue rim appears above the red body at the shared destination.
            top=frame48.getpixel((165,88))
            self.assertGreater(top[2],top[0])
            for x in (frame0,frame24,frame48):
                x.close()
            reversed_recipe=living_object.create(self.root,self.layers(body_z=1,rim_z=0))
            reverse_members=living_object._parents(self.root,reversed_recipe)
            swapped=[living_object._prepare_layer(x) for x in reverse_members]
            try:
                rev,_=living_object._foreground_at(swapped,48)
                pixel=rev.getpixel((165,88))
                self.assertGreater(pixel[0],pixel[2])
                rev.close()
            finally:
                for item in swapped:
                    item["source"].close()
                    item["target"].close()
            half_recipe=living_object.create(self.root,self.layers(body_opacity=.5,rim_opacity=.5))
            half_members=living_object._parents(self.root,half_recipe)
            half=[living_object._prepare_layer(x) for x in half_members]
            try:
                transparent,_=living_object._foreground_at(half,0)
                alpha=transparent.getpixel((80,90))[3]
                self.assertTrue(100 <= alpha <= 160)
                transparent.close()
            finally:
                for item in half:
                    item["source"].close()
                    item["target"].close()
        finally:
            for item in parts:
                item["source"].close()
                item["target"].close()

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg required for actual N5 cinematic preview")
    def test_mp4_and_transparent_png_and_non_destructive_receipt(self):
        recipe=self.make()
        snap=living_object.freeze(self.root,recipe["id"])
        out=self.home/"object.mp4"
        preview=self.home/"midpoint.png"
        receipt=living_object.render(self.root,snap,out,alpha_preview_out=preview)
        self.assertEqual(receipt["status"],"scoped_complete")
        self.assertEqual(receipt["frame_count"],49)
        self.assertEqual(len(receipt["frame_receipts"]),49)
        self.assertEqual(receipt["output_sha256"],hashlib.sha256(out.read_bytes()).hexdigest())
        self.assertEqual(receipt["alpha_preview_sha256"],hashlib.sha256(preview.read_bytes()).hexdigest())
        self.assertTrue(out.with_suffix(".mp4.receipt.json").is_file())
        self.assertGreater(receipt["frame_receipts"][-1]["overlap_px"],100)
        with Image.open(preview) as layer:
            self.assertEqual(layer.mode,"RGBA")
            self.assertEqual(layer.getpixel((5,5))[3],0)
            self.assertGreater(layer.getpixel((120,90))[3],150)
        with self.assertRaises(FileExistsError):
            living_object.render(self.root,snap,out,alpha_preview_out=preview)
        cmd=["ffmpeg","-nostdin","-v","error","-i",str(out),
             "-vf","select=eq(n\\,48)","-frames:v","1",
             "-f","image2pipe","-vcodec","png","-"]
        png=subprocess.run(cmd,check=True,capture_output=True).stdout
        with Image.open(BytesIO(png)) as decoded:
            frame=decoded.convert("RGB")
            self.assertEqual(frame.size,(320,180))
            # The original background has been replaced by the diagnostic matte.
            self.assertLess(max(abs(a-b) for a,b in
                            zip(frame.getpixel((5,5)),n4.DIAGNOSTIC_COLOR)),18)
            self.assertGreater(frame.getpixel((165,88))[2],frame.getpixel((165,88))[0])
            frame.close()


if __name__=="__main__":
    unittest.main()

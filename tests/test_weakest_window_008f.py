import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from haunted_blender import flow_pantry, weakest_window_doctor as doctor, zero_dollar_mill


class WeakestWindowDoctor008fTests(unittest.TestCase):
    def setUp(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg required")

    def make_static(self, path: Path, duration: float = 2.0):
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", f"smptebars=s=160x90:r=12:d={duration}",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
            ],
            check=True,
        )

    def make_motion(self, path: Path, duration: float = 2.0):
        subprocess.run(
            [
                "ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", f"testsrc2=s=160x90:r=12:d={duration}",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
            ],
            check=True,
        )

    def build_cut(self, root: Path):
        source = root / "source"
        source.mkdir()
        self.make_static(source / "a-static.mp4")
        self.make_motion(source / "b-motion.mp4")
        manifest = flow_pantry.index_flow_folder(source, probe=True)
        plan = zero_dollar_mill.build_plan(
            manifest,
            source,
            target_seconds=4.0,
            slug_seconds=2.0,
            width=160,
            height=90,
            fps=12,
        )
        receipt = zero_dollar_mill.render_plan(plan, source, root / "base")
        return source, plan, receipt

    def test_doctor_ranks_static_window_and_prescribes_true_local_motion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, plan, receipt = self.build_cut(root)
            report = doctor.scan(
                receipt["outputPath"], plan, window_seconds=2.0, sample_fps=4
            )
            self.assertEqual(report["coverageRatio"], 1.0)
            weakest = next(w for w in report["windows"] if w["id"] == report["weakest"])
            self.assertEqual(weakest["id"], "window-0001")
            self.assertEqual(weakest["dominantWeakness"], "stasis")

            treatment = doctor.prescribe(report, plan, fraction=0.5, max_windows=1)
            self.assertEqual(len(treatment["mutations"]), 1)
            mutation = treatment["mutations"][0]
            self.assertEqual(mutation["slugId"], "slug-0001")
            self.assertEqual(mutation["fromRecipe"], "fit")
            self.assertEqual(mutation["toRecipe"], "kinetic-push")
            self.assertEqual(mutation["providerCredits"], 0)
            self.assertEqual(mutation["usdMicros"], 0)

    def test_level_one_kinetic_push_increases_observed_motion_and_preserves_coverage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, plan, receipt = self.build_cut(root)
            before = doctor.scan(
                receipt["outputPath"], plan, window_seconds=2.0, sample_fps=6
            )
            treatment = doctor.prescribe(before, plan, fraction=0.5, max_windows=1)
            treated = doctor.apply_level_one(plan, treatment)
            trial = zero_dollar_mill.render_plan(treated, source, root / "trial")
            after = doctor.scan(
                trial["outputPath"], treated, window_seconds=2.0, sample_fps=6
            )

            b0 = before["windows"][0]
            a0 = after["windows"][0]
            self.assertGreater(a0["motionEnergy"], b0["motionEnergy"])
            comparison = doctor.compare(before, after)
            self.assertTrue(comparison["coveragePreserved"])
            self.assertGreaterEqual(after["coverageRatio"], before["coverageRatio"])
            self.assertEqual(trial["providerCredits"], 0)
            self.assertEqual(trial["usdMicros"], 0)

    def test_prescription_mutates_only_ranked_window_slugs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, plan, receipt = self.build_cut(root)
            report = doctor.scan(
                receipt["outputPath"], plan, window_seconds=2.0, sample_fps=4
            )
            treatment = doctor.prescribe(report, plan, fraction=0.5, max_windows=1)
            treated = doctor.apply_level_one(plan, treatment)
            by_id = {s["id"]: s for s in treated["slugs"]}
            self.assertEqual(by_id["slug-0001"]["recipe"], "kinetic-push")
            self.assertEqual(by_id["slug-0002"]["recipe"], plan["slugs"][1]["recipe"])
            self.assertEqual(treated["doctor"]["cost"]["providerCredits"], 0)
            self.assertEqual(treated["doctor"]["cost"]["usdMicros"], 0)

    def test_compare_rejects_any_coverage_regression(self):
        before = {
            "schema": doctor.REPORT_SCHEMA,
            "id": "before",
            "meanWeakness": 0.5,
            "coverageRatio": 1.0,
        }
        after = {
            "schema": doctor.REPORT_SCHEMA,
            "id": "after",
            "meanWeakness": 0.4,
            "coverageRatio": 0.9,
        }
        with self.assertRaises(ValueError):
            doctor.compare(before, after)

    def test_resource_escalation_stops_at_owned_compost_after_failed_level_one(self):
        body = {
            "schema": doctor.TREATMENT_SCHEMA,
            "id": "treatment",
            "reportId": "report",
            "planId": "plan",
            "targetFraction": 0.1,
            "targetWindowCount": 1,
            "mutations": [],
            "mutationLadder": [
                {"level": 0, "name": "keep", "costClass": "zero"},
                {"level": 1, "name": "deterministic-remix", "costClass": "local-repeatable-zero"},
                {"level": 2, "name": "owned-clip-compost", "costClass": "local-repeatable-zero"},
                {"level": 3, "name": "topology-text-cutout-treatment", "costClass": "local-repeatable-zero"},
                {"level": 4, "name": "repeatably-free-provider", "costClass": "free-repeatable"},
            ],
            "laws": [],
        }
        level_two = next(x for x in body["mutationLadder"] if x["level"] == 2)
        level_four = next(x for x in body["mutationLadder"] if x["level"] == 4)
        self.assertEqual(level_two["costClass"], "local-repeatable-zero")
        self.assertNotEqual(level_four["costClass"], "local-repeatable-zero")


if __name__ == "__main__":
    unittest.main()

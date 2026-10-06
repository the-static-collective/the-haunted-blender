import tempfile
import unittest
from pathlib import Path

from haunted_blender import cockpit


class Cockpit008Tests(unittest.TestCase):
    def test_four_verb_flow_and_temperature_state(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cockpit.create_project(root,project_id="p1",title="Up Then Up",local_only=True)
            cockpit.add_section(root,section_id="verse",kind="verse",start=0,end=10)
            cockpit.action_grow(root,"verse",ecology_id="eco-1")
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"],"dreaming")
            cockpit.action_keep(root,"verse",proposal_id="p4")
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"],"kept")
            cockpit.action_scene_rendered(root,"verse",scene_id="scene-1")
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"],"moving")
            cockpit.action_alive(root,"verse")
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"],"alive")

    def test_local_only_blocks_remote_awakening(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cockpit.create_project(root,project_id="p1",title="x",local_only=True)
            cockpit.add_section(root,section_id="c",kind="chorus",start=0,end=5)
            cockpit.action_grow(root,"c",ecology_id="e")
            cockpit.action_keep(root,"c",proposal_id="p")
            cockpit.action_scene_rendered(root,"c",scene_id="s")
            with self.assertRaises(ValueError):
                cockpit.action_awaken(root,"c",window_id="w")
            cockpit.set_local_only(root,False)
            cockpit.action_awaken(root,"c",window_id="w")
            self.assertEqual(cockpit.cockpit_view(root)["sections"][0]["temperature"],"awakening")

    def test_resume_summary_counts_pending_work(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cockpit.create_project(root,project_id="p1",title="x")
            cockpit.add_section(root,section_id="a",kind="verse",start=0,end=3)
            cockpit.add_section(root,section_id="b",kind="chorus",start=3,end=6)
            cockpit.action_grow(root,"a",ecology_id="ea")
            cockpit.action_grow(root,"b",ecology_id="eb")
            cockpit.action_keep(root,"a",proposal_id="pa")
            summary=cockpit.resume_summary(root)
            self.assertEqual(summary["resume"]["unbornSixups"],1)
            self.assertEqual(summary["resume"]["keptScenesAwaitingRender"],1)

    def test_haunt_does_not_become_history(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            cockpit.create_project(root,project_id="p1",title="x")
            cockpit.add_section(root,section_id="a",kind="bridge",start=0,end=3)
            cockpit.action_haunt(root,"a",haunt_id="ghost-1")
            view=cockpit.cockpit_view(root)["sections"][0]
            self.assertEqual(view["temperature"],"haunted")
            self.assertEqual(view["hauntCount"],1)
            self.assertFalse(view["hasScene"])


if __name__=="__main__":
    unittest.main()

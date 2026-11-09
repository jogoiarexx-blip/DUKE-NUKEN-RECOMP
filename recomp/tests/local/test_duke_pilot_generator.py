"""Synthetic original Duke GLB pilot: no game disc or model extraction."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"/"local"))
from build_duke_pilot import build,POSE,DUKE_PARTS
from character_model import validate_model,read_glb


class DukePilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scratch=tempfile.TemporaryDirectory()
        cls.path=Path(cls.scratch.name)/"duke"
        cls.report=build(cls.path)
    @classmethod
    def tearDownClass(cls):
        cls.scratch.cleanup()
    def test_full_rigid_rig(self):
        self.assertEqual(cls_report:=self.report["joint_count"],19)
        self.assertGreaterEqual(self.report["rendered_parts"],15)
        self.assertGreater(self.report["triangles"],1000)
        self.assertLessEqual(self.report["triangles"],12000)
        self.assertFalse(self.report["runtime_override_active"])
        self.assertEqual(set(POSE),set(DUKE_PARTS))
    def test_glb_has_no_animation_and_manifest_matches_bytes(self):
        d,_=read_glb(self.path/"duke-pilot.glb")
        self.assertEqual(len(d["nodes"]),19)
        self.assertNotIn("skins",d)
        self.assertNotIn("animations",d)
        m=json.loads((self.path/"model.json").read_text())
        self.assertEqual(m["model"]["sha256"],
                         hashlib.sha256((self.path/"duke-pilot.glb").read_bytes()).hexdigest())
        self.assertEqual(validate_model(self.path/"model.json")["triangles"],
                         self.report["triangles"])
    def test_preview_and_repeatable_export(self):
        from PIL import Image
        with Image.open(self.path/"duke-pilot-preview.png") as im:
            self.assertEqual(im.size,(1500,640))
        assembled=self.path/"duke-pilot-assembled-preview.glb"
        self.assertTrue(assembled.is_file())
        self.assertNotEqual(assembled.read_bytes(),
                            (self.path/"duke-pilot.glb").read_bytes())
        assembled_doc,_=read_glb(assembled)
        self.assertEqual(len(assembled_doc["nodes"]),19)
        with tempfile.TemporaryDirectory() as td:
            other=build(Path(td)/"duke")
            self.assertEqual(other["model_sha256"],self.report["model_sha256"])

if __name__=="__main__":unittest.main()

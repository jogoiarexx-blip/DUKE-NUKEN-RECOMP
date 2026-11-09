"""Source-only character mesh contract tests; no owned disc or Blender required."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "local"))
import character_model as contract


class CharacterModelTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="duke-character-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def make(self, update=None):
        parts = {str(k): f"part_{k:02d}_{v}"
                 for k, v in contract.DUKE_PARTS.items()}
        position_data = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)
        doc = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": list(range(len(parts)))}],
            "nodes": [{"name": name, "mesh": 0} for name in parts.values()],
            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "mode": 4}]}],
            "accessors": [{"bufferView": 0, "byteOffset": 0, "componentType": 5126,
                           "count": 3, "type": "VEC3"}],
            "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}],
            "buffers": [{"byteLength": len(position_data)}],
        }
        if update:
            update(doc)
        raw = json.dumps(doc).encode("utf-8")
        raw += b" " * (-len(raw) % 4)
        data = position_data + b"\x00" * (-len(position_data) % 4)
        chunks = struct.pack("<II", len(raw), contract.GLB_JSON) + raw
        chunks += struct.pack("<II", len(data), contract.GLB_BIN) + data
        glb = struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks
        (self.root / "duke.glb").write_bytes(glb)
        manifest = {"schema": 1, "asset_id": "duke-db00-hero",
                    "target": {"group": "DB00", "hierarchy": 1, "joints": 19},
                    "model": {"file": "duke.glb",
                              "sha256": hashlib.sha256(glb).hexdigest(),
                              "max_triangles": 12000},
                    "rig": {"mode": "rigid-parts", "parts": parts}}
        (self.root / "model.json").write_text(json.dumps(manifest))
        return self.root / "model.json"

    def test_valid_19_joint_rigid_model(self):
        result = contract.validate_model(self.make())
        self.assertEqual(result["joint_count"], 19)
        self.assertEqual(result["rendered_parts"], 19)
        self.assertEqual(result["triangles"], 19)
        self.assertFalse(result["runtime_override_active"])

    def test_missing_joint_rejected(self):
        path = self.make(lambda d: d["nodes"].pop())
        with self.assertRaisesRegex(contract.ModelContractError, "missing"):
            contract.validate_model(path)

    def test_native_animation_cannot_be_replaced_by_glb(self):
        path = self.make(lambda d: d.update(animations=[{"channels": [], "samplers": []}]))
        with self.assertRaisesRegex(contract.ModelContractError, "animation"):
            contract.validate_model(path)

    def test_bone_transform_must_be_identity(self):
        path = self.make(lambda d: d["nodes"][0].update(translation=[0, 4, 0]))
        with self.assertRaisesRegex(contract.ModelContractError, "identity"):
            contract.validate_model(path)

    def test_hash_guard(self):
        path = self.make()
        original = json.loads(path.read_text())
        original["model"]["sha256"] = "0" * 64
        path.write_text(json.dumps(original))
        with self.assertRaisesRegex(contract.ModelContractError, "SHA-256"):
            contract.validate_model(path)

    def test_costume_must_have_separate_binding(self):
        path = self.make()
        raw = json.loads(path.read_text())
        raw["target"]["group"] = "DB01"
        path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(contract.ModelContractError, "DB00"):
            contract.validate_model(path)

    def test_external_texture_rejected(self):
        path = self.make(lambda d: d.update(images=[{"uri": "secret-retail.png"}]))
        with self.assertRaisesRegex(contract.ModelContractError, "external images"):
            contract.validate_model(path)

    def test_unbounded_triangles_rejected(self):
        path = self.make()
        raw = json.loads(path.read_text())
        raw["model"]["max_triangles"] = 12001
        path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(contract.ModelContractError, "triangle budget"):
            contract.validate_model(path)

    def test_traversal_rejected(self):
        path = self.make()
        raw = json.loads(path.read_text())
        raw["model"]["file"] = "../duke.glb"
        path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(contract.ModelContractError, "safe"):
            contract.validate_model(path)

    def test_skinning_rejected(self):
        path = self.make(lambda d: d.update(skins=[{"joints": [0]}]))
        with self.assertRaisesRegex(contract.ModelContractError, "skinning"):
            contract.validate_model(path)

    def test_source_size_limit(self):
        path = self.make()
        raw = json.loads(path.read_text())
        raw["model"]["max_triangles"] = 10
        path.write_text(json.dumps(raw))
        with self.assertRaisesRegex(contract.ModelContractError, "exceeds"):
            contract.validate_model(path)


if __name__ == "__main__":
    unittest.main()

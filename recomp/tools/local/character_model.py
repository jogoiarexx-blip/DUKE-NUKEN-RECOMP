#!/usr/bin/env python3
"""Preflight an original-art Duke rigid-part GLB against the verified PS1 rig.

This validates an opt-in *asset contract*, not a live model replacement.
No retail disc is read or modified; no GLB is loaded by the runtime yet.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

# D08K1, DB00 HIE hierarchy 1: use ROT part IDs, never volatile HIE record indexes.
# The two leg chains have neutral A/B labels until costume orientation is verified.
DUKE_PARTS = {
    0: "pelvis", 9: "chest",
    10: "left_shoulder", 11: "left_forearm", 12: "left_hand",
    13: "right_shoulder", 14: "right_forearm", 15: "right_hand",
    20: "jetpack_mount", 16: "head",
    1: "leg_a_1", 2: "leg_a_2", 3: "leg_a_3", 4: "leg_a_4",
    5: "leg_b_1", 6: "leg_b_2", 7: "leg_b_3", 8: "leg_b_4",
    21: "leg_attachment",
}
DEFAULT_MAX_TRIANGLES = 12000
MAX_GLB_BYTES = 32 * 1024 * 1024
GLB_JSON = 0x4E4F534A
GLB_BIN = 0x004E4942
ASSET_ID = re.compile(r"[a-z][a-z0-9_-]{2,63}\Z")


class ModelContractError(ValueError):
    """An asset is not compatible with the first-stage Duke model contract."""


def reject(condition, message):
    if condition:
        raise ModelContractError(message)


def read_glb(path):
    size = path.stat().st_size
    reject(size < 20 or size > MAX_GLB_BYTES, "GLB must be 20 bytes..32 MiB")
    blob = path.read_bytes()
    magic, version, declared = struct.unpack_from("<4sII", blob)
    reject(magic != b"glTF" or version != 2 or declared != len(blob),
           "GLB 2.0 header/length mismatch")
    pos, chunks = 12, []
    while pos < len(blob):
        reject(pos + 8 > len(blob), "truncated GLB chunk header")
        length, kind = struct.unpack_from("<II", blob, pos)
        pos += 8
        reject(length % 4 or pos + length > len(blob), "bad GLB chunk size")
        chunks.append((kind, blob[pos:pos + length]))
        pos += length
    reject(not chunks or chunks[0][0] != GLB_JSON, "GLB JSON chunk is missing")
    reject(sum(kind == GLB_BIN for kind, _ in chunks) > 1,
           "multiple GLB binary chunks unsupported")
    reject(any(kind not in (GLB_JSON, GLB_BIN) for kind, _ in chunks),
           "unknown GLB chunk")
    reject(sum(kind == GLB_JSON for kind, _ in chunks) != 1,
           "GLB has multiple JSON chunks")
    try:
        doc = json.loads(chunks[0][1].rstrip(b" \t\r\n\x00").decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ModelContractError("invalid glTF JSON") from exc
    reject(not isinstance(doc, dict) or doc.get("asset", {}).get("version") != "2.0",
           "glTF asset.version must be 2.0")
    data = next((value for kind, value in chunks if kind == GLB_BIN), b"")
    return doc, data


def _identity_transform(node, name):
    reject("matrix" in node, f"{name}: export rigid parts without matrices")
    for key, default in (
        ("translation", [0, 0, 0]),
        ("rotation", [0, 0, 0, 1]),
        ("scale", [1, 1, 1]),
    ):
        reject(node.get(key, default) != default,
               f"{name}: bake the rest transform into local vertices; {key} must be identity")


def validate_model(manifest_path):
    manifest_path = Path(manifest_path).resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ModelContractError("invalid or missing character manifest") from exc
    reject(not isinstance(manifest, dict), "manifest must be a JSON object")
    reject(set(manifest) != {"schema", "asset_id", "target", "model", "rig"},
           "manifest keys must be schema, asset_id, target, model and rig")
    reject(manifest["schema"] != 1, "unsupported schema version")
    reject(not isinstance(manifest["asset_id"], str) or
           not ASSET_ID.fullmatch(manifest["asset_id"]), "invalid asset_id")

    target = manifest["target"]
    reject(not isinstance(target, dict) or
           target != {"group": "DB00", "hierarchy": 1, "joints": 19},
           "pilot targets only DB00 Duke HIE 1 / 19 joints")
    model = manifest["model"]
    reject(not isinstance(model, dict) or set(model) !=
           {"file", "sha256", "max_triangles"}, "invalid model settings")
    file_name = model["file"]
    reject(not isinstance(file_name, str) or
           not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*\.glb", file_name),
           "model file must be one local safe .glb name")
    digest = model["sha256"]
    reject(not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest),
           "model.sha256 must be a lowercase SHA-256 hash")
    budget = model["max_triangles"]
    reject(type(budget) is not int or budget < 1 or budget > DEFAULT_MAX_TRIANGLES,
           "triangle budget must be between 1 and 12000")
    model_path = (manifest_path.parent / file_name).resolve()
    reject(not model_path.is_relative_to(manifest_path.parent) or
           not model_path.is_file(), "model file not found inside manifest folder")
    reject(hashlib.sha256(model_path.read_bytes()).hexdigest() != digest,
           "model SHA-256 mismatch")
    rig = manifest["rig"]
    reject(not isinstance(rig, dict) or set(rig) != {"mode", "parts"} or
           rig["mode"] != "rigid-parts", "expected a rigid-parts rig")
    parts = rig["parts"]
    expected = {str(key): f"part_{key:02d}_{name}" for key, name in DUKE_PARTS.items()}
    reject(not isinstance(parts, dict) or parts != expected,
           "part mapping must match all 19 verified ROT IDs/names; do not use record indexes")

    doc, binary = read_glb(model_path)
    reject(doc.get("animations") or doc.get("skins") or doc.get("extensionsRequired"),
           "model must not embed animation, skinning or required extensions")
    buffers = doc.get("buffers", [])
    reject(len(buffers) != 1 or "uri" in buffers[0] or
           type(buffers[0].get("byteLength")) is not int or
           buffers[0]["byteLength"] > len(binary),
           "GLB must contain one internal binary buffer")
    for img in doc.get("images", []):
        reject("uri" in img and not str(img["uri"]).startswith("data:"),
               "external images are forbidden; embed textures in GLB")
    for mesh in doc.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            reject("targets" in primitive, "morph targets not supported in rigid pilot")
    nodes = doc.get("nodes", [])
    scenes = doc.get("scenes", [])
    scene_i = doc.get("scene", 0)
    reject(type(scene_i) is not int or scene_i < 0 or scene_i >= len(scenes),
           "active glTF scene missing")
    scene_roots = scenes[scene_i].get("nodes", [])
    reject(not isinstance(scene_roots, list) or len(set(scene_roots)) != len(scene_roots),
           "scene roots invalid")
    names = {}
    for i, node in enumerate(nodes):
        name = node.get("name")
        reject(not isinstance(name, str), "all model nodes need stable names")
        reject(name in names, "duplicate glTF node name: " + name)
        names[name] = i
    reject(not set(expected.values()).issubset(names),
           "GLB is missing one or more mandatory Duke part nodes")
    meshes = doc.get("meshes", [])
    accessors = doc.get("accessors", [])
    triangles, drawn_parts = 0, 0
    for key, name in expected.items():
        idx = names[name]
        node = nodes[idx]
        reject(idx not in scene_roots, f"{name} must be a direct scene root")
        reject(node.get("children") or "skin" in node,
               f"{name} must not inherit a second skeleton or use skinning")
        _identity_transform(node, name)
        if "mesh" not in node:
            continue  # attachment-only joint
        drawn_parts += 1
        mid = node["mesh"]
        reject(type(mid) is not int or mid < 0 or mid >= len(meshes),
               f"{name} references a nonexistent mesh")
        for primitive in meshes[mid].get("primitives", []):
            reject(primitive.get("mode", 4) != 4, "only triangle primitives supported")
            pos = primitive.get("attributes", {}).get("POSITION")
            reject(type(pos) is not int or pos < 0 or pos >= len(accessors),
                   "triangle primitive needs a POSITION accessor")
            accessor = accessors[pos]
            reject(accessor.get("type") != "VEC3" or accessor.get("componentType") != 5126,
                   "POSITION must be float32 VEC3")
            count = accessor.get("count", 0)
            if "indices" in primitive:
                index = primitive["indices"]
                reject(type(index) is not int or index < 0 or index >= len(accessors),
                       "invalid triangle indices accessor")
                count = accessors[index].get("count", 0)
            reject(type(count) is not int or count < 3 or count % 3,
                   "triangle index/vertex count must be divisible by 3")
            triangles += count // 3
    reject(drawn_parts < 10, "at least 10 body parts must have geometry")
    reject(triangles > budget, f"{triangles} triangles exceeds the {budget} budget")
    return {"asset_id": manifest["asset_id"], "group": "DB00",
            "joint_count": len(expected), "rendered_parts": drawn_parts,
            "triangles": triangles, "budget": budget,
            "model_sha256": digest, "runtime_override_active": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="local manifest next to the model GLB")
    parser.add_argument("--json", action="store_true", help="print validation report as JSON")
    args = parser.parse_args(argv)
    try:
        report = validate_model(args.manifest)
    except (ModelContractError, OSError, KeyError, TypeError, IndexError, struct.error) as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"OK: {report['asset_id']} / {report['joint_count']} joints / "
              f"{report['rendered_parts']} mesh parts / {report['triangles']} triangles")
        print("Model validated for tooling only; runtime rendering not installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

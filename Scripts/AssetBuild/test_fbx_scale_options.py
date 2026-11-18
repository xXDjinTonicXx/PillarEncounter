import bpy
from pathlib import Path


TEMP_DIR = Path(r"C:\Users\usman\AppData\Local\Temp")
options = ["FBX_SCALE_NONE", "FBX_SCALE_UNITS", "FBX_SCALE_CUSTOM", "FBX_SCALE_ALL"]

obj = bpy.data.objects.get("SM_TacticalFlashlight")
if obj is None:
    raise RuntimeError("Open the flashlight blend before running this test")
bpy.ops.object.select_all(action="DESELECT")
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

paths = []
for option in options:
    path = TEMP_DIR / f"flashlight_{option}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"MESH"}, use_triangles=True,
        bake_anim=False, global_scale=1.0, apply_unit_scale=True,
        apply_scale_options=option, axis_forward="X", axis_up="Z",
    )
    paths.append(path)

for option, path in zip(options, paths):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_normals=True)
    imported = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    dims = tuple(round(v, 5) for v in imported.dimensions)
    scale = tuple(round(v, 5) for v in imported.scale)
    print(f"SCALE_TEST {option} dimensions={dims} scale={scale}")

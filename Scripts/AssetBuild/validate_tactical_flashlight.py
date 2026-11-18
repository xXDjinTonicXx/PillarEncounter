import bpy
from pathlib import Path


FBX_PATH = Path(r"C:\Users\usman\Documents\Unreal Projects\PillarEncounter\SourceAssets\Props\TacticalFlashlight\SM_TacticalFlashlight.fbx")
BLEND_PATH = Path(r"C:\Users\usman\Documents\Unreal Projects\PillarEncounter\SourceAssets\Props\TacticalFlashlight\SM_TacticalFlashlight.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
blend_objects = [(obj.name, obj.type) for obj in bpy.context.scene.objects]
if blend_objects != [("SM_TacticalFlashlight", "MESH")]:
    raise RuntimeError(f"Blend contains unexpected scene objects: {blend_objects}")
if bpy.context.scene.camera is not None:
    raise RuntimeError("Blend unexpectedly contains an active camera")
blend_obj = bpy.data.objects["SM_TacticalFlashlight"]
blend_obj.data.calc_loop_triangles()
if len(blend_obj.data.loop_triangles) >= 5000:
    raise RuntimeError("Blend triangle budget failed")
print(f"BLEND_OBJECTS={blend_objects}")
print(f"BLEND_TRIANGLES={len(blend_obj.data.loop_triangles)}")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH), use_custom_normals=True)

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if len(meshes) != 1:
    raise RuntimeError(f"Expected exactly one mesh after FBX import, got {len(meshes)}")

obj = meshes[0]
obj.data.calc_loop_triangles()
dims_m = tuple(round(value, 5) for value in obj.dimensions)
location = tuple(round(value, 6) for value in obj.location)
rotation = tuple(round(value, 6) for value in obj.rotation_euler)
scale = tuple(round(value, 6) for value in obj.scale)
materials = [slot.name for slot in obj.material_slots]
uv_maps = [uv.name for uv in obj.data.uv_layers]
triangle_count = len(obj.data.loop_triangles)
rubber_vertex_indices = {
    vertex_index
    for poly in obj.data.polygons
    if poly.material_index == 1
    for vertex_index in poly.vertices
}
rubber_points = [obj.matrix_world @ obj.data.vertices[index].co for index in rubber_vertex_indices]
grip_points = [point for point in rubber_points if point.z < 0.0165]
rubber_x = [point.x for point in grip_points]
rubber_center_x = round((min(rubber_x) + max(rubber_x)) * 0.5, 6)

if triangle_count >= 5000:
    raise RuntimeError(f"Triangle budget failed after FBX import: {triangle_count}")
if dims_m[0] <= dims_m[1] or dims_m[0] <= dims_m[2]:
    raise RuntimeError(f"FBX forward dimension is not +X-dominant: {dims_m}")
if location != (0.0, 0.0, 0.0):
    raise RuntimeError(f"FBX pivot moved away from the grip origin: {location}")
if len(materials) != 5:
    raise RuntimeError(f"Unexpected material slots: {materials}")
if uv_maps != ["UV0", "UV1_Lightmap"]:
    raise RuntimeError(f"Unexpected UV maps: {uv_maps}")
if abs(rubber_center_x) > 0.0001:
    raise RuntimeError(f"Pivot is not centered in the rubber grip: {rubber_center_x}")

print("TACTICAL_FLASHLIGHT_FBX_VALIDATION_OK")
print(f"OBJECT={obj.name}")
print(f"DIMENSIONS_METERS={dims_m}")
print(f"LOCATION={location}")
print(f"ROTATION={rotation}")
print(f"SCALE={scale}")
print(f"TRIANGLES={triangle_count}")
print(f"MATERIAL_SLOTS={materials}")
print(f"UV_MAPS={uv_maps}")
print(f"RUBBER_GRIP_CENTER_X={rubber_center_x}")

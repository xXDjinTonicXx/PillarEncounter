import bpy
import math
from mathutils import Matrix, Vector
from pathlib import Path


OUTPUT_DIR = Path(r"C:\Users\usman\Documents\Unreal Projects\PillarEncounter\SourceAssets\Props\TacticalFlashlight")
BLEND_PATH = OUTPUT_DIR / "SM_TacticalFlashlight.blend"
FBX_PATH = OUTPUT_DIR / "SM_TacticalFlashlight.fbx"
PREVIEW_PATH = Path(r"C:\Users\usman\AppData\Local\Temp\PillarEncounter_TacticalFlashlight_preview.png")
TRIANGLE_BUDGET = 5000


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.01
    scene.unit_settings.length_unit = "CENTIMETERS"
    scene.render.film_transparent = False
    return scene


def set_input(node, names, value):
    if isinstance(names, str):
        names = (names,)
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def make_principled_material(name, base_color, metallic, roughness, ior=1.45, transmission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*base_color[:3], base_color[3] if len(base_color) > 3 else 1.0)
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    out.location = (420, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (80, 0)
    set_input(bsdf, "Base Color", base_color)
    set_input(bsdf, "Metallic", metallic)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "IOR", ior)
    set_input(bsdf, ("Transmission Weight", "Transmission"), transmission)
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat, bsdf


def build_materials():
    aluminum, aluminum_bsdf = make_principled_material(
        "M_Black_Anodized_Aluminum", (0.009, 0.012, 0.016, 1.0), 0.86, 0.24
    )
    noise = aluminum.node_tree.nodes.new("ShaderNodeTexNoise")
    noise.location = (-520, -140)
    noise.inputs["Scale"].default_value = 38.0
    noise.inputs["Detail"].default_value = 2.5
    noise.inputs["Roughness"].default_value = 0.62
    bump = aluminum.node_tree.nodes.new("ShaderNodeBump")
    bump.location = (-180, -120)
    bump.inputs["Strength"].default_value = 0.055
    bump.inputs["Distance"].default_value = 0.025
    aluminum.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    aluminum.node_tree.links.new(bump.outputs["Normal"], aluminum_bsdf.inputs["Normal"])

    rubber, rubber_bsdf = make_principled_material(
        "M_Rubber_Grip", (0.006, 0.007, 0.008, 1.0), 0.0, 0.70
    )
    set_input(rubber_bsdf, ("Specular IOR Level", "Specular"), 0.28)
    rubber_noise = rubber.node_tree.nodes.new("ShaderNodeTexNoise")
    rubber_noise.location = (-520, -160)
    rubber_noise.inputs["Scale"].default_value = 62.0
    rubber_noise.inputs["Detail"].default_value = 3.0
    rubber_noise.inputs["Roughness"].default_value = 0.78
    rubber_bump = rubber.node_tree.nodes.new("ShaderNodeBump")
    rubber_bump.location = (-180, -110)
    rubber_bump.inputs["Strength"].default_value = 0.22
    rubber_bump.inputs["Distance"].default_value = 0.035
    rubber.node_tree.links.new(rubber_noise.outputs["Fac"], rubber_bump.inputs["Height"])
    rubber.node_tree.links.new(rubber_bump.outputs["Normal"], rubber_bsdf.inputs["Normal"])

    glass, glass_bsdf = make_principled_material(
        "M_Glass_Lens", (0.018, 0.028, 0.038, 0.22), 0.0, 0.035, ior=1.47, transmission=1.0
    )
    set_input(glass_bsdf, ("Coat Weight", "Coat"), 0.22)
    if hasattr(glass, "surface_render_method"):
        glass.surface_render_method = "DITHERED"

    reflector, _ = make_principled_material(
        "M_Reflector_Chrome", (0.72, 0.76, 0.80, 1.0), 1.0, 0.075
    )
    led, _ = make_principled_material(
        "M_LED_Ceramic", (0.82, 0.86, 0.78, 1.0), 0.0, 0.23
    )
    return {
        "aluminum": aluminum,
        "rubber": rubber,
        "glass": glass,
        "reflector": reflector,
        "led": led,
    }


def make_lathe(collection, name, profile, segments, material, cap_start=True, cap_end=True,
               closed_profile=False, flip=False, smooth=True):
    verts = []
    for x, radius in profile:
        for j in range(segments):
            theta = 2.0 * math.pi * j / segments
            verts.append((x, radius * math.cos(theta), radius * math.sin(theta)))

    faces = []
    profile_steps = len(profile) if closed_profile else len(profile) - 1
    for i in range(profile_steps):
        ni = (i + 1) % len(profile)
        for j in range(segments):
            nj = (j + 1) % segments
            face = (i * segments + j, i * segments + nj, ni * segments + nj, ni * segments + j)
            faces.append(tuple(reversed(face)) if flip else face)

    if not closed_profile and cap_start:
        center_idx = len(verts)
        verts.append((profile[0][0], 0.0, 0.0))
        for j in range(segments):
            nj = (j + 1) % segments
            face = (center_idx, nj, j)
            faces.append(tuple(reversed(face)) if flip else face)

    if not closed_profile and cap_end:
        center_idx = len(verts)
        verts.append((profile[-1][0], 0.0, 0.0))
        base = (len(profile) - 1) * segments
        for j in range(segments):
            nj = (j + 1) % segments
            face = (center_idx, base + j, base + nj)
            faces.append(tuple(reversed(face)) if flip else face)

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    side_faces = profile_steps * segments
    for idx, poly in enumerate(mesh.polygons):
        poly.use_smooth = smooth and idx < side_faces

    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def apply_object_transform(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    obj.select_set(False)


def apply_bevel(obj, width, segments=1):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    modifier = obj.modifiers.new("Edge Bevel", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    modifier.angle_limit = math.radians(28.0)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(False)


def add_beveled_cube(collection, name, location, dimensions, rotation_x, material, bevel=0.035):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=(rotation_x, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    for existing_collection in list(obj.users_collection):
        existing_collection.objects.unlink(obj)
    collection.objects.link(obj)
    obj.dimensions = dimensions
    apply_object_transform(obj)
    apply_bevel(obj, bevel, 1)
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = False
    return obj


def add_button_cylinder(collection, name, location, radius, depth, scale_xy, material, bevel):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    for existing_collection in list(obj.users_collection):
        existing_collection.objects.unlink(obj)
    collection.objects.link(obj)
    obj.scale.x = scale_xy[0]
    obj.scale.y = scale_xy[1]
    apply_object_transform(obj)
    apply_bevel(obj, bevel, 2)
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def build_grip_profile():
    profile = [(-4.78, 1.45), (-4.68, 1.54)]
    start = -4.58
    band_width = 0.82
    for i in range(7):
        x0 = start + i * band_width
        profile.extend([
            (x0, 1.54),
            (x0 + 0.10, 1.62),
            (x0 + 0.62, 1.62),
            (x0 + 0.72, 1.54),
        ])
    profile.extend([(1.34, 1.54), (1.48, 1.46)])
    return profile


def build_model(scene, materials):
    asset_collection = bpy.data.collections.new("PillarEncounter_TacticalFlashlight")
    scene.collection.children.link(asset_collection)
    parts = []

    tail_profile = [
        (-6.28, 1.38), (-6.24, 1.54), (-6.12, 1.70), (-5.88, 1.74),
        (-5.72, 1.68), (-5.62, 1.74), (-5.26, 1.74), (-5.12, 1.64),
        (-4.92, 1.58), (-4.72, 1.46),
    ]
    tail = make_lathe(asset_collection, "Aluminum_TailCap", tail_profile, 24, materials["aluminum"])
    parts.append(tail)

    grip = make_lathe(
        asset_collection, "Rubberized_Grip", build_grip_profile(), 24, materials["rubber"]
    )
    parts.append(grip)

    head_profile = [
        (1.38, 1.40), (1.50, 1.54), (1.62, 1.66), (2.12, 1.66),
        (2.28, 1.76), (2.42, 1.78), (2.60, 1.92), (2.98, 2.20),
        (3.25, 2.38), (5.50, 2.38), (5.66, 2.46), (5.86, 2.46),
        (5.96, 2.34),
    ]
    head = make_lathe(asset_collection, "Aluminum_Head", head_profile, 28, materials["aluminum"])
    parts.append(head)

    bezel_profile = [
        (5.78, 2.27), (5.86, 2.48), (6.02, 2.58), (6.26, 2.62),
        (6.44, 2.52), (6.52, 2.34), (6.52, 2.01), (6.37, 1.98),
        (6.20, 2.08), (5.98, 2.10), (5.82, 2.20),
    ]
    bezel = make_lathe(
        asset_collection, "Aluminum_FrontBezel", bezel_profile, 28, materials["aluminum"],
        cap_start=False, cap_end=False, closed_profile=True
    )
    parts.append(bezel)

    reflector_profile = [
        (5.93, 0.18), (5.99, 0.45), (6.06, 0.78), (6.15, 1.12),
        (6.23, 1.43), (6.29, 1.68), (6.32, 1.86),
    ]
    reflector = make_lathe(
        asset_collection, "Chrome_Reflector", reflector_profile, 24, materials["reflector"],
        cap_start=False, cap_end=False, flip=True
    )
    parts.append(reflector)

    led = make_lathe(
        asset_collection, "LED_Ceramic_Element", [(5.91, 0.20), (5.97, 0.20)], 16,
        materials["led"], cap_start=True, cap_end=True
    )
    parts.append(led)

    lens = make_lathe(
        asset_collection, "Glass_FrontLens", [(6.31, 1.92), (6.44, 1.92)], 28,
        materials["glass"], cap_start=True, cap_end=True
    )
    parts.append(lens)

    for i in range(8):
        angle = 2.0 * math.pi * i / 8.0
        radius = 1.75
        rib = add_beveled_cube(
            asset_collection,
            f"Tailcap_Rib_{i:02d}",
            (-5.56, radius * math.cos(angle), radius * math.sin(angle)),
            (0.78, 0.20, 0.16),
            angle,
            materials["aluminum"],
            bevel=0.025,
        )
        parts.append(rib)

    for i in range(6):
        angle = 2.0 * math.pi * i / 6.0
        radius = 2.57
        lug = add_beveled_cube(
            asset_collection,
            f"Bezel_Crenellation_{i:02d}",
            (6.53, radius * math.cos(angle), radius * math.sin(angle)),
            (0.38, 0.18, 0.46),
            angle,
            materials["aluminum"],
            bevel=0.035,
        )
        parts.append(lug)

    switch_mount = add_button_cylinder(
        asset_collection, "SideSwitch_Housing", (2.02, 0.0, 1.70), 0.58, 0.22,
        (1.28, 0.88), materials["aluminum"], 0.055
    )
    parts.append(switch_mount)
    switch_button = add_button_cylinder(
        asset_collection, "SideSwitch_Rubber", (2.02, 0.0, 1.86), 0.43, 0.18,
        (1.22, 0.86), materials["rubber"], 0.045
    )
    parts.append(switch_button)

    # Join to one Unreal-friendly static mesh while preserving named material slots.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = head
    bpy.ops.object.join()
    flashlight = bpy.context.object
    flashlight.name = "SM_TacticalFlashlight"
    flashlight.data.name = "SM_TacticalFlashlight_Mesh"
    flashlight.location = (0.0, 0.0, 0.0)
    flashlight.rotation_euler = (0.0, 0.0, 0.0)
    flashlight.scale = (1.0, 1.0, 1.0)

    # Consolidate duplicate slots from joined source parts into a stable UE slot order.
    old_materials = list(flashlight.data.materials)
    material_order = [
        materials["aluminum"], materials["rubber"], materials["glass"],
        materials["reflector"], materials["led"],
    ]
    material_to_index = {mat: idx for idx, mat in enumerate(material_order)}
    polygon_indices = []
    for poly in flashlight.data.polygons:
        source_mat = old_materials[poly.material_index]
        polygon_indices.append(material_to_index[source_mat])
    flashlight.data.materials.clear()
    for mat in material_order:
        flashlight.data.materials.append(mat)
    for poly, mat_index in zip(flashlight.data.polygons, polygon_indices):
        poly.material_index = mat_index

    # Put the local origin at the true center of the rubber grip. Geometry remains +X-forward.
    grip_center_x = (-4.78 + 1.48) * 0.5
    flashlight.data.transform(Matrix.Translation((-grip_center_x, 0.0, 0.0)))

    # One non-overlapping UV layout, duplicated as a second UE lightmap-ready channel.
    bpy.context.view_layer.objects.active = flashlight
    flashlight.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    try:
        bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.025)
    except TypeError:
        bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode="OBJECT")
    uv0 = flashlight.data.uv_layers.active
    uv0.name = "UV0"
    uv1 = flashlight.data.uv_layers.new(name="UV1_Lightmap", do_init=True)
    flashlight.data.uv_layers.active = uv0
    uv0.active_render = True
    uv1.active_render = False

    # Mark hard transitions while keeping the cylindrical surfaces smooth.
    flashlight.data.update()
    edge_faces = {edge.index: [] for edge in flashlight.data.edges}
    for poly in flashlight.data.polygons:
        for edge_idx in poly.edge_keys:
            pass
    lookup = {}
    for poly in flashlight.data.polygons:
        for key in poly.edge_keys:
            lookup.setdefault(tuple(sorted(key)), []).append(poly.index)
    for edge in flashlight.data.edges:
        adjacent = lookup.get(tuple(sorted(edge.key)), [])
        if len(adjacent) == 2:
            angle = flashlight.data.polygons[adjacent[0]].normal.angle(
                flashlight.data.polygons[adjacent[1]].normal
            )
            edge.use_edge_sharp = angle > math.radians(42.0)

    flashlight.data.calc_loop_triangles()
    triangle_count = len(flashlight.data.loop_triangles)
    if triangle_count >= TRIANGLE_BUDGET:
        raise RuntimeError(f"Triangle budget exceeded: {triangle_count} >= {TRIANGLE_BUDGET}")

    flashlight["Asset"] = "PillarEncounter tactical flashlight"
    flashlight["UE_ForwardAxis"] = "+X"
    flashlight["UE_UpAxis"] = "+Z"
    flashlight["UnitScale"] = "1 Blender unit = 1 centimeter"
    flashlight["OriginUsage"] = "Grip center / VR hand pivot"
    flashlight["TriangleCount"] = triangle_count
    flashlight["TriangleBudget"] = TRIANGLE_BUDGET
    flashlight["ContainsGameplayLogic"] = False

    return flashlight, triangle_count


def save_and_export(scene, flashlight):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    flashlight.select_set(True)
    bpy.context.view_layer.objects.active = flashlight

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    bpy.ops.export_scene.fbx(
        filepath=str(FBX_PATH),
        check_existing=False,
        use_selection=True,
        object_types={"MESH"},
        use_mesh_modifiers=True,
        use_triangles=True,
        use_custom_props=True,
        add_leaf_bones=False,
        bake_anim=False,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="X",
        axis_up="Z",
        mesh_smooth_type="FACE",
        path_mode="AUTO",
    )


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render_preview(scene, flashlight):
    preview_collection = bpy.data.collections.new("TEMP_Preview")
    scene.collection.children.link(preview_collection)

    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0.0, 0.0, -2.72))
    plane = bpy.context.object
    plane.name = "TEMP_Ground"
    for existing_collection in list(plane.users_collection):
        existing_collection.objects.unlink(plane)
    preview_collection.objects.link(plane)
    ground, _ = make_principled_material("TEMP_GroundMaterial", (0.055, 0.060, 0.070, 1.0), 0.0, 0.58)
    plane.data.materials.append(ground)

    bpy.ops.object.camera_add(location=(16.5, -18.0, 11.0))
    camera = bpy.context.object
    camera.name = "TEMP_Camera"
    for existing_collection in list(camera.users_collection):
        existing_collection.objects.unlink(camera)
    preview_collection.objects.link(camera)
    camera.data.lens = 58.0
    look_at(camera, (1.55, 0.0, -0.15))
    scene.camera = camera

    light_specs = [
        ((2.0, -7.0, 11.0), 1700.0, 6.0, (0.78, 0.86, 1.0)),
        ((-7.0, 4.5, 6.0), 1050.0, 5.0, (1.0, 0.66, 0.42)),
        ((8.0, 5.0, 2.0), 900.0, 4.0, (0.42, 0.58, 1.0)),
    ]
    for idx, (location, energy, size, color) in enumerate(light_specs):
        data = bpy.data.lights.new(f"TEMP_Area_{idx}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        obj = bpy.data.objects.new(data.name, data)
        preview_collection.objects.link(obj)
        obj.location = location
        look_at(obj, (1.55, 0.0, 0.0))

    world = bpy.data.worlds.new("TEMP_PreviewWorld")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.008, 0.012, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.42
    scene.world = world

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEW_PATH)
    scene.render.film_transparent = False
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    bpy.ops.render.render(write_still=True)


def main():
    scene = reset_scene()
    materials = build_materials()
    flashlight, triangle_count = build_model(scene, materials)
    save_and_export(scene, flashlight)
    dimensions = tuple(round(v, 3) for v in flashlight.dimensions)
    render_preview(scene, flashlight)
    print("TACTICAL_FLASHLIGHT_BUILD_OK")
    print(f"BLEND={BLEND_PATH}")
    print(f"FBX={FBX_PATH}")
    print(f"PREVIEW={PREVIEW_PATH}")
    print(f"TRIANGLES={triangle_count}")
    print(f"DIMENSIONS_CM={dimensions}")
    print(f"MATERIAL_SLOTS={[slot.name for slot in flashlight.material_slots]}")
    print(f"UV_MAPS={[uv.name for uv in flashlight.data.uv_layers]}")


if __name__ == "__main__":
    main()

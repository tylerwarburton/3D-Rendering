"""Build the cinematic Roadster vs. Rocket scene in Blender 4.3+."""

from __future__ import annotations

import argparse
import math
import random
import sys
from pathlib import Path

import bpy


FPS = 30
FRAME_END = 300
CAR_START = 45
IGNITION = 75
LIFTOFF = 165
TITLE_START = 270
PROJECT_DIR = Path(__file__).resolve().parent
REPO_DIR = PROJECT_DIR.parents[1]
OUTPUT_DIR = REPO_DIR / "output"
BLEND_PATH = PROJECT_DIR / "roadster_rocket_what_could_have_been.blend"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def material(name, base, metallic=0.0, roughness=0.45, emission=None,
             emission_strength=0.0, alpha=1.0, transmission=0.0, coat=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Alpha"].default_value = alpha
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = coat
        bsdf.inputs["Coat Roughness"].default_value = 0.12
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0:
        try:
            mat.surface_render_method = "DITHERED"
        except Exception:
            pass
        mat.diffuse_color = (*base[:3], alpha)
    return mat


def apply_material(obj, mat):
    obj.data.materials.append(mat)
    return obj


def bevel(obj, width=0.08, segments=3):
    mod = obj.modifiers.new("Precision bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    return obj


def cube(name, location, scale, mat, bevel_width=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width:
        bevel(obj, bevel_width)
    apply_material(obj, mat)
    if parent:
        obj.parent = parent
    return obj


def uv_sphere(name, location, scale, mat, segments=32, rings=16, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
                                        location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_material(obj, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if parent:
        obj.parent = parent
    return obj


def cylinder(name, location, radius, depth, mat, vertices=48, parent=None,
             rotation=(0, 0, 0), bevel_width=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius,
                                       depth=depth, location=location,
                                       rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    if bevel_width:
        bevel(obj, bevel_width)
    apply_material(obj, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if parent:
        obj.parent = parent
    return obj


def cone(name, location, radius1, radius2, depth, mat, parent=None,
         vertices=48):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1,
                                   radius2=radius2, depth=depth,
                                   location=location)
    obj = bpy.context.object
    obj.name = name
    apply_material(obj, mat)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    if parent:
        obj.parent = parent
    return obj


def empty(name, location=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    if parent:
        obj.parent = parent
    return obj


def loft_mesh(name, stations, sides, mat, parent=None):
    """Elliptical cross-section loft along X: (x, y_radius, z_center, z_radius)."""
    verts = []
    for x, ry, zc, rz in stations:
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            sy, cz = math.sin(angle), math.cos(angle)
            y = ry * math.copysign(abs(sy) ** 0.78, sy) if sy else 0
            z = zc + rz * math.copysign(abs(cz) ** 0.88, cz) if cz else zc
            verts.append((x, y, z))
    faces = []
    for s in range(len(stations) - 1):
        for i in range(sides):
            j = (i + 1) % sides
            a, b = s * sides + i, s * sides + j
            c, d = (s + 1) * sides + j, (s + 1) * sides + i
            faces.append((a, b, c, d))
    faces.append(tuple(reversed(range(sides))))
    last = (len(stations) - 1) * sides
    faces.append(tuple(last + i for i in range(sides)))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_material(obj, mat)
    bevel(obj, 0.045, 3)
    for poly in mesh.polygons:
        poly.use_smooth = True
    if parent:
        obj.parent = parent
    return obj


def build_car(mats):
    car = empty("CAR_RIG")
    body = loft_mesh("Roadster_Body", [
        (-2.28, 0.48, 0.58, 0.19), (-1.95, 0.88, 0.62, 0.28),
        (-1.20, 0.98, 0.68, 0.34), (-0.20, 0.99, 0.70, 0.35),
        (0.85, 0.94, 0.66, 0.30), (1.65, 0.78, 0.58, 0.22),
        (2.22, 0.34, 0.53, 0.13),
    ], 16, mats["red"], car)
    body["dimensions_m"] = "4.5 x 1.9 x 1.2"
    loft_mesh("Roadster_Glass_Canopy", [
        (-1.18, 0.46, 0.95, 0.18), (-0.78, 0.70, 1.05, 0.34),
        (0.05, 0.73, 1.08, 0.40), (0.68, 0.55, 1.00, 0.29),
        (0.92, 0.25, 0.91, 0.10),
    ], 16, mats["glass"], car)
    cube("RoofSpine", (-0.18, 0, 1.43), (0.72, 0.035, 0.025),
         mats["carbon"], 0.025, car)
    cube("FrontSplitter", (2.05, 0, 0.34), (0.42, 0.91, 0.045),
         mats["carbon"], 0.025, car)
    cube("RearDiffuser", (-2.03, 0, 0.35), (0.38, 0.90, 0.06),
         mats["carbon"], 0.025, car)

    wheel_rigs = []
    for x in (-1.42, 1.42):
        for y in (-0.93, 0.93):
            rig = empty(f"WheelRig_{x}_{y}", (x, y, 0.40), car)
            wheel_rigs.append(rig)
            bpy.ops.mesh.primitive_torus_add(major_radius=0.275, minor_radius=0.095,
                                             major_segments=40, minor_segments=12,
                                             rotation=(math.pi / 2, 0, 0))
            tire = bpy.context.object
            tire.name = "Performance_Tire"
            tire.parent = rig
            apply_material(tire, mats["rubber"])
            cylinder("Alloy_Rim", (0, 0, 0), 0.245, 0.19, mats["alloy"],
                     32, rig, rotation=(math.pi / 2, 0, 0))
            cylinder("Brake_Disc", (0, -0.005, 0), 0.175, 0.205,
                     mats["brake"], 32, rig, rotation=(math.pi / 2, 0, 0))
        uv_sphere(f"Fender_{x}", (x, 0, 0.74), (0.60, 0.98, 0.31),
                  mats["red_bright"], 32, 16, car)

    for y in (-0.55, 0.55):
        uv_sphere("LED_Headlight", (2.12, y, 0.68),
                  (0.22, 0.17, 0.075), mats["headlight"], 24, 12, car)
    cube("TailLightBar", (-2.205, 0, 0.70), (0.035, 0.70, 0.055),
         mats["taillight"], 0.025, car)
    for y in (-0.97, 0.97):
        uv_sphere("SideMirror", (0.20, y, 1.09), (0.22, 0.09, 0.07),
                  mats["red"], 20, 10, car)
        cube("SideIntake", (-0.78, y * 0.985, 0.65), (0.34, 0.018, 0.12),
             mats["carbon"], 0.04, car)

    scorch = uv_sphere("Scorched_Panel", (-0.05, -0.993, 0.72),
                       (0.72, 0.018, 0.21), mats["scorch"], 24, 12, car)
    scorch.hide_render = True
    scorch.keyframe_insert("hide_render", frame=164)
    scorch.hide_render = False
    scorch.keyframe_insert("hide_render", frame=165)

    expr = ("6.9 if frame<=45 else "
            "6.9+8.94*((frame-45)/30)**2 if frame<=75 else "
            "6.9+8.94+17.88*((frame-75)/30)+1.6*((frame-75)/30)**2 "
            "if frame<=270 else 199.66+38.68*((frame-270)/30)*0.16")
    car.driver_add("location", 0).driver.expression = expr
    for rig in wheel_rigs:
        rig.driver_add("rotation_euler", 1).driver.expression = f"-({expr}-6.9)/0.36"
    return car


def build_rocket(mats):
    rocket = empty("ROCKET_RIG")
    cylinder("Rocket_Main_Hull", (0, 0, 38), 4.35, 68, mats["steel"], 96, rocket)
    cone("Rocket_Nose", (0, 0, 79.5), 4.35, 0.08, 15, mats["steel"], rocket, 96)
    cylinder("Engine_Skirt", (0, 0, 5.8), 4.55, 5.2, mats["dark_steel"], 64, rocket)
    for z in range(9, 73, 7):
        cylinder("Hull_Weld_Ring", (0, 0, z), 4.38, 0.075, mats["weld"], 96, rocket)
    for x in (-2.2, 0, 2.2):
        for y in (-1.6, 1.6):
            cone("Engine_Bell", (x, y, 2.5), 0.78, 0.46, 1.8,
                 mats["engine"], rocket, 40)
    for y in (-1, 1):
        fin = cube("Aft_Fin", (-0.3, y * 4.15, 10.0), (3.4, 0.16, 2.7),
                   mats["dark_steel"], 0.08, rocket)
        fin.rotation_euler[0] = y * math.radians(8)
    for frame, z in ((1, 0), (164, 0), (165, 0), (190, 3.5),
                     (225, 14), (270, 36), (300, 57)):
        rocket.location.z = z
        rocket.keyframe_insert("location", frame=frame, index=2)
    for fc in rocket.animation_data.action.fcurves:
        for point in fc.keyframe_points:
            point.interpolation = "BEZIER"
            point.easing = "EASE_IN"
    return rocket


def build_environment(mats):
    cube("Ground", (120, 0, -0.38), (310, 150, 0.25), mats["ground"])
    cube("Wet_Runway", (145, 0, -0.08), (175, 6.5, 0.10), mats["road"], 0.04)
    for y in (-5.8, 5.8):
        cube("Road_Edge", (145, y, 0.035), (175, 0.055, 0.018), mats["marking"])
    for x in range(-10, 320, 14):
        cube("Lane_Marker", (x, 0, 0.035), (3.0, 0.055, 0.018), mats["marking"])
    rng = random.Random(9902)
    for _ in range(30):
        uv_sphere("Puddle", (rng.uniform(-8, 300), rng.uniform(-5.2, 5.2), 0.025),
                  (rng.uniform(0.8, 3.0), rng.uniform(0.18, 0.55), 0.008),
                  mats["puddle"], 20, 8)

    cylinder("Launch_Table", (0, 0, 0.55), 7.2, 1.2, mats["concrete"], 64)
    cylinder("Launch_Ring", (0, 0, 1.5), 5.5, 1.0, mats["dark_steel"], 64)
    cube("Flame_Trench", (-4.5, 0, 0.0), (8.5, 2.1, 1.1), mats["concrete"], 0.2)

    tx, ty = -8.0, -8.3
    for ox in (-1.5, 1.5):
        for oy in (-1.35, 1.35):
            cube("Tower_Leg", (tx + ox, ty + oy, 46), (0.28, 0.28, 46),
                 mats["tower"], 0.04)
    for z in range(4, 92, 5):
        cube("Tower_Brace_X", (tx, ty - 1.35, z), (2.0, 0.12, 0.14), mats["tower"])
        cube("Tower_Brace_Y", (tx - 1.5, ty, z), (0.12, 1.5, 0.14), mats["tower"])
    for z, length in ((23, 7), (48, 7.5), (70, 8)):
        cube("Service_Arm", (tx + length / 2, ty + 1.15, z),
             (length / 2, 0.28, 0.24), mats["tower"], 0.05)
    for z in (28, 58, 89):
        uv_sphere("Tower_Warning_Light", (tx, ty, z), (0.18, 0.18, 0.18),
                  mats["warning"], 16, 8)
    for y in (-20, 20):
        for i in range(3):
            cylinder("Propellant_Tank", (-17 - i * 7, y, 3.8), 3.2 - i * 0.25,
                     7.5 + i, mats["tank"], 48, bevel_width=0.12)
    for x in range(15, 300, 30):
        for y in (-14, 14):
            cylinder("Road_Lamp_Post", (x, y, 2.3), 0.07, 4.6, mats["tower"], 12)
            uv_sphere("Road_Lamp", (x, y, 4.6), (0.18, 0.18, 0.13),
                      mats["lamp"], 16, 8)


def build_smoke_and_fire(mats, rocket):
    rng = random.Random(2408)
    smoke_texture = bpy.data.textures.new("Turbulent_Smoke_Texture", type="CLOUDS")
    smoke_texture.noise_scale = 0.42
    smoke_texture.noise_depth = 2
    for i in range(22):
        puff = uv_sphere("Cryogenic_Vapor", (0, 0, 0), (1, 1, 1), mats["vapor"], 16, 10)
        vapor_displace = puff.modifiers.new("Vapor_Turbulence", "DISPLACE")
        vapor_displace.texture, vapor_displace.strength = smoke_texture, 0.22
        birth, z, side = 1 + i * 11, rng.uniform(12, 72), rng.choice((-1, 1))
        puff.location = (side * 4.2, 0, z)
        puff.scale = (0.01, 0.01, 0.01)
        puff.keyframe_insert("scale", frame=birth)
        puff.scale = (rng.uniform(1.2, 2.8), rng.uniform(0.7, 1.8), rng.uniform(0.6, 1.4))
        puff.location = (side * rng.uniform(6, 10), rng.uniform(-3, 3), z + 2)
        puff.keyframe_insert("scale", frame=birth + 28)
        puff.keyframe_insert("location", frame=birth + 28)

    for i in range(92):
        birth = IGNITION + int(i * 0.85)
        angle, side_bias = rng.uniform(-math.pi, math.pi), rng.uniform(-1.0, 1.0)
        puff = uv_sphere("Exhaust_Smoke", (0, 0, 0), (1, 1, 1),
                         mats[f"smoke_{i % 4}"], 20, 12)
        smoke_displace = puff.modifiers.new("Rolling_Turbulence", "DISPLACE")
        smoke_displace.texture = smoke_texture
        smoke_displace.strength = rng.uniform(0.24, 0.48)
        puff.scale = (0.01, 0.01, 0.01)
        puff.keyframe_insert("scale", frame=max(1, birth - 1))
        base = rng.uniform(1.6, 4.2)
        puff.location = (rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(0.2, 1.8))
        puff.keyframe_insert("location", frame=birth)
        puff.scale = (base * rng.uniform(1.0, 1.8), base, base * rng.uniform(0.6, 1.05))
        puff.keyframe_insert("scale", frame=birth + 18)
        end = min(300, birth + rng.randint(95, 150))
        age = end - birth
        puff.location = (age * rng.uniform(0.28, 0.52) + math.cos(angle) * age * 0.08,
                         math.sin(angle) * age * 0.16 + side_bias * 5,
                         rng.uniform(1.0, 5.5) + age * rng.uniform(0.015, 0.045))
        puff.scale = (base * rng.uniform(2.2, 3.8), base * rng.uniform(1.8, 3.2),
                      base * rng.uniform(1.2, 2.3))
        puff.keyframe_insert("location", frame=end)
        puff.keyframe_insert("scale", frame=end)

    flame_root = empty("ENGINE_FLAME_RIG", parent=rocket)
    for x in (-2.2, 0, 2.2):
        outer = cone("Engine_Flame_Outer", (x, 0, -2.8), 1.55, 0.40, 11,
                     mats["flame_outer"], flame_root, 40)
        inner = cone("Engine_Flame_Core", (x, 0, -1.3), 0.72, 0.20, 7.5,
                     mats["flame_core"], flame_root, 40)
        for obj in (outer, inner):
            obj.scale = (1, 1, 0.001)
            obj.keyframe_insert("scale", frame=IGNITION - 1)
            obj.scale = (1, 1, 1)
            obj.keyframe_insert("scale", frame=IGNITION)
    for strength, color, size in ((4200, (1.0, 0.08, 0.01), 12),
                                  (1800, (1.0, 0.40, 0.04), 7)):
        data = bpy.data.lights.new("Ignition_Glow", "POINT")
        data.energy, data.color, data.shadow_soft_size = 0, color, size
        light = bpy.data.objects.new("Ignition_Glow", data)
        bpy.context.collection.objects.link(light)
        light.parent, light.location = rocket, (0, 0, 1.8)
        data.keyframe_insert("energy", frame=IGNITION - 1)
        data.energy = strength
        data.keyframe_insert("energy", frame=IGNITION)


def add_area_light(name, location, energy, color, size, target):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.color, data.shape, data.size = energy, color, "DISK", size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    con = obj.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
    return obj


def add_point_light(name, location, energy, color, size, parent=None):
    data = bpy.data.lights.new(name, "POINT")
    data.energy, data.color, data.shadow_soft_size = energy, color, size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    if parent:
        obj.parent = parent
    return obj


def add_sun(name, rotation, energy, color, angle):
    data = bpy.data.lights.new(name, "SUN")
    data.energy, data.color, data.angle = energy, color, angle
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.rotation_euler = rotation
    return obj


def camera(name, location, target, lens, parent=None):
    data = bpy.data.cameras.new(name)
    data.lens, data.sensor_width = lens, 36
    data.dof.use_dof, data.dof.focus_object, data.dof.aperture_fstop = True, target, 3.2
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    if parent:
        obj.parent = parent
    con = obj.constraints.new("TRACK_TO")
    con.target, con.track_axis, con.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
    return obj


def add_camera_text(cam, body, location, size, mat, name):
    curve = bpy.data.curves.new(name, "FONT")
    curve.body, curve.align_x, curve.align_y, curve.size = body, "CENTER", "CENTER", size
    curve.extrude, curve.bevel_depth = 0.006, 0.002
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.parent, obj.location = cam, location
    apply_material(obj, mat)
    return obj


def build_cameras(car, mats):
    static_target = empty("Establish_Target", (3.5, 0, 8.5))
    cam1 = camera("CAM_01_ESTABLISH", (19, -30, 2.2), static_target, 27)
    target2 = empty("Launch_Target", (-10, 0, 4.5), car)
    cam2 = camera("CAM_02_LAUNCH", (10, -14, 2.5), target2, 31, car)
    target3 = empty("Chase_Target", (-9, 0, 1.0), car)
    cam3 = camera("CAM_03_SMOKE_CHASE", (10, -5.5, 1.8), target3, 25, car)
    target4 = empty("Breakout_Target", (1.5, 0, 1.1), car)
    cam4 = camera("CAM_04_BREAKOUT", (2.0, -11.5, 2.3), target4, 42, car)
    target5 = empty("Hero_Target", (-48, 0, 7.5), car)
    cam5 = camera("CAM_05_HERO", (16, -10, 3.0), target5, 35, car)
    for frame, cam in ((1, cam1), (45, cam2), (105, cam3), (165, cam4), (225, cam5)):
        bpy.context.scene.timeline_markers.new(cam.name, frame=frame).camera = cam
    bpy.context.scene.camera = cam1
    title = add_camera_text(cam5, "WHAT COULD HAVE BEEN", (0, 2.25, -12),
                            0.48, mats["title"], "Closing_Title")
    disclosure = add_camera_text(cam5,
        "A FICTIONAL CONCEPT — NOT AN ACTUAL LAUNCH", (0, 1.55, -12),
        0.19, mats["title"], "Closing_Disclosure")
    for text in (title, disclosure):
        text.hide_render = True
        text.keyframe_insert("hide_render", frame=TITLE_START - 1)
        text.hide_render = False
        text.keyframe_insert("hide_render", frame=TITLE_START)
    for axis in range(3):
        cam2.keyframe_insert("location", frame=45, index=axis)
        cam2.keyframe_insert("location", frame=104, index=axis)
    for fc in cam2.animation_data.action.fcurves:
        noise = fc.modifiers.new("NOISE")
        noise.strength = 0.035 if fc.array_index < 2 else 0.018
        noise.scale, noise.phase = 3.0, 75


def setup_render():
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end, scene.render.fps = 1, FRAME_END, FPS
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    try:
        scene.render.use_motion_blur = True
    except Exception:
        pass
    try:
        scene.view_settings.look = "AgX - Very High Contrast"
    except Exception:
        scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 1.45
    world = bpy.data.worlds.new("Blue_Hour_World")
    scene.world, world.use_nodes = world, True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.006, 0.015, 0.045, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.42
    scene.use_nodes = True
    nodes, links = scene.node_tree.nodes, scene.node_tree.links
    nodes.clear()
    rl, glare, comp = nodes.new("CompositorNodeRLayers"), nodes.new("CompositorNodeGlare"), nodes.new("CompositorNodeComposite")
    glare.glare_type, glare.quality, glare.threshold, glare.size = "FOG_GLOW", "HIGH", 0.7, 7
    links.new(rl.outputs["Image"], glare.inputs["Image"])
    links.new(glare.outputs["Image"], comp.inputs["Image"])


def make_materials():
    m = {
        "red": material("Roadster_Candy_Red", (0.62, 0.006, 0.012, 1), .42, .13, coat=1),
        "red_bright": material("Roadster_Highlight_Red", (.95, .015, .018, 1), .36, .11, coat=1),
        "glass": material("Smoked_Glass", (.008, .025, .05, 1), .12, .06, transmission=.38, coat=.8),
        "carbon": material("Carbon_Aero", (.008, .01, .014, 1), .65, .22),
        "rubber": material("Tire_Rubber", (.006, .007, .009, 1), 0, .72),
        "alloy": material("Wheel_Alloy", (.16, .18, .21, 1), .95, .14),
        "brake": material("Brake_Disc", (.22, .18, .14, 1), .88, .28),
        "headlight": material("White_LED", (.8, .9, 1, 1), .1, .08, (.6, .82, 1, 1), 18),
        "taillight": material("Red_LED", (.7, 0, 0, 1), .1, .1, (1, 0, 0, 1), 12),
        "beam": material("Headlight_Beam", (.35, .55, 1, 1), 0, 1, (.2, .45, 1, 1), 1.5, alpha=.075),
        "scorch": material("Scorched_Paint", (.012, .006, .003, 1), .05, .9),
        "steel": material("Rocket_Stainless_Steel", (.34, .39, .43, 1), .98, .16),
        "dark_steel": material("Heat_Darkened_Steel", (.035, .045, .06, 1), .88, .25),
        "weld": material("Hull_Welds", (.18, .22, .26, 1), .96, .22),
        "engine": material("Engine_Bells", (.018, .02, .024, 1), .92, .26),
        "ground": material("Blue_Hour_Ground", (.018, .025, .038, 1), .06, .72),
        "road": material("Wet_Tarmac", (.012, .018, .027, 1), .32, .16, coat=.45),
        "marking": material("Wet_Road_Marking", (.42, .46, .48, 1), .2, .23),
        "puddle": material("Puddle_Reflection", (.012, .04, .075, 1), .5, .05, coat=1),
        "concrete": material("Launch_Concrete", (.07, .08, .09, 1), .18, .58),
        "tower": material("Tower_Steel", (.07, .10, .14, 1), .82, .3),
        "tank": material("Tank_Aluminum", (.36, .42, .47, 1), .92, .17),
        "warning": material("Red_Warning_Lamp", (.8, 0, 0, 1), 0, .1, (1, 0, 0, 1), 8),
        "lamp": material("Amber_Lamp", (.9, .45, .08, 1), 0, .1, (1, .22, .02, 1), 5),
        "vapor": material("Cryogenic_Vapor", (.55, .66, .75, 1), 0, .9, alpha=.22),
        "flame_outer": material("Orange_Exhaust", (1, .035, .001, 1), 0, .35, (1, .025, .001, 1), 22, alpha=.82),
        "flame_core": material("Whitehot_Exhaust", (1, .74, .25, 1), 0, .22, (1, .32, .015, 1), 45),
        "title": material("Title_White", (1, .89, .72, 1), 0, .25, (1, .72, .42, 1), 2),
    }
    for i, gray in enumerate((.25, .31, .37, .43)):
        m[f"smoke_{i}"] = material(f"Smoke_{i}", (gray, gray*.92, gray*.84, 1), 0, .95, alpha=.58)
    return m


def build_scene():
    clear_scene()
    setup_render()
    mats = make_materials()
    build_environment(mats)
    car = build_car(mats)
    rocket = build_rocket(mats)
    build_smoke_and_fire(mats, rocket)
    build_cameras(car, mats)
    target = empty("Light_Target", (35, 0, 3))
    add_area_light("Moon_Key", (-50, -45, 85), 15000, (.18, .36, .85), 45, target)
    add_area_light("Horizon_Rim", (80, 45, 28), 9000, (.20, .38, 1), 30, target)
    add_area_light("Roadster_Rim", (20, -18, 10), 5000, (.8, .12, .06), 12, car)
    add_point_light("Roadster_Moving_Fill", (0, -4.5, 4.5), 1450,
                    (.26, .46, 1.0), 3.5, car)
    add_sun("Blue_Hour_Sun", (math.radians(28), math.radians(-18),
            math.radians(-35)), 2.8, (.24, .38, 1.0), math.radians(12))
    scene = bpy.context.scene
    scene["speculative_concept"] = True
    scene["car_motion_frame"], scene["rocket_ignition_frame"] = CAR_START, IGNITION
    scene["rocket_liftoff_frame"], scene["closing_title_frame"] = LIFTOFF, TITLE_START
    scene["description"] = "Original fictional concept — not an actual launch"
    scene.render.filepath = str(OUTPUT_DIR / "frames" / "frame_")
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    print(f"Saved native Blender project: {BLEND_PATH}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_scene()


if __name__ == "__main__":
    main()

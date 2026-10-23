"""Photoreal Blender (Cycles) render of an STL: a still PNG or a turntable MP4.

    blender -b -P shared/blender_render.py -- part.stl out.png [--color #c8d4dc] [--samples 96]
    blender -b -P shared/blender_render.py -- part.stl out.mp4 --turntable [--frames 72]

Run through shared/studio.py (finds blender, caches by STL mtime). Stills are
Cycles (GPU when there is one), turntables EEVEE. The part sits flat side down on a soft studio floor,
lit by a key + rim area light, in PLA-like plastic.
"""
import argparse
import math
import sys

import bpy
from mathutils import Vector

a = argparse.ArgumentParser()
a.add_argument("stl")
a.add_argument("out")
a.add_argument("--color", default="#c8d4dc")
a.add_argument("--samples", type=int, default=96)
a.add_argument("--turntable", action="store_true")
a.add_argument("--frames", type=int, default=72)
a.add_argument("--size", default="1280x960")
A = a.parse_args(sys.argv[sys.argv.index("--") + 1:])

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# ---- the part: mm -> m, centred, on the floor ----
bpy.ops.wm.stl_import(filepath=A.stl, global_scale=0.001)
part = bpy.context.selected_objects[0]
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
part.location = (0, 0, 0)
bpy.context.view_layer.update()
lo = min((part.matrix_world @ Vector(c)).z for c in part.bound_box)
part.location.z -= lo
bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
dims = part.dimensions
R = max(dims.length / 2, 1e-3)                       # bounding radius, m

h = A.color.lstrip("#")
rgb = [(int(h[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)]
mat = bpy.data.materials.new("PLA")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (*rgb, 1)
bsdf.inputs["Roughness"].default_value = 0.42
bsdf.inputs["Coat Weight"].default_value = 0.15
part.data.materials.append(mat)

# ---- floor: big plane, soft grey, catches shadows ----
bpy.ops.mesh.primitive_plane_add(size=R * 40)
floor = bpy.context.object
fm = bpy.data.materials.new("Floor")
fm.use_nodes = True
fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.07, 0.08, 1)
fm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
floor.data.materials.append(fm)

# ---- lights + world ----
def area(name, loc, energy, size):
    bpy.ops.object.light_add(type="AREA", location=loc)
    L = bpy.context.object
    L.name, L.data.energy, L.data.size = name, energy, size
    L.rotation_euler = (Vector((0, 0, R * 0.4)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()

area("key", (R * 3, -R * 3.5, R * 4.5), 400 * R * R, R * 3)
area("rim", (-R * 3.5, R * 3, R * 2.5), 300 * R * R, R * 2)
w = bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.06, 0.09, 0.11, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6

# ---- camera: iso-ish, framing the bounding sphere ----
bpy.ops.object.empty_add(location=(0, 0, dims.z / 2))
pivot = bpy.context.object
bpy.ops.object.camera_add()
cam = bpy.context.object
cam.parent = pivot
cam.data.lens = 60
d = R / math.sin(math.atan(18 / cam.data.lens)) * 1.4
cam.location = Vector((0.62, -0.92, 0.55)).normalized() * d
cam.rotation_euler = (-cam.location).to_track_quat("-Z", "Y").to_euler()
sc.camera = cam

# ---- Cycles on the GPU when there is one ----
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for kind in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
    try:
        prefs.compute_device_type = kind
        prefs.get_devices()
        if any(dv.type == kind for dv in prefs.devices):
            for dv in prefs.devices:
                dv.use = True
            sc.cycles.device = "GPU"
            break
    except TypeError:
        continue
sc.cycles.samples = A.samples
sc.cycles.use_denoising = True
sc.view_settings.view_transform = "AgX"
sc.render.resolution_x, sc.render.resolution_y = map(int, A.size.split("x"))
sc.render.film_transparent = False

if A.turntable:
    sc.render.engine = "BLENDER_EEVEE"                         # ~10x faster than Cycles per frame
    sc.render.resolution_x, sc.render.resolution_y = 960, 720
    sc.frame_start, sc.frame_end = 1, A.frames
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"   # steady spin
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", index=2, frame=1)
    pivot.rotation_euler = (0, 0, 2 * math.pi)
    pivot.keyframe_insert("rotation_euler", index=2, frame=A.frames + 1)
    sc.render.fps = 24
    if hasattr(sc.render.image_settings, "media_type"):          # Blender 5+
        sc.render.image_settings.media_type = "VIDEO"
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.filepath = A.out
    bpy.ops.render.render(animation=True)
else:
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = A.out
    bpy.ops.render.render(write_still=True)

"""Capture actual Blender GUI windows on a virtual display; NO render operators."""
import bpy
from mathutils import Vector
from pathlib import Path
import subprocess
import sys
import json

source, output = map(Path, sys.argv[sys.argv.index('--') + 1:])
output.mkdir(parents=True, exist_ok=False)
bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
points = [ob.matrix_world @ vertex.co for ob in bpy.data.objects if ob.type == 'MESH' for vertex in ob.data.vertices]
minimum, maximum = [Vector([op(p[i] for p in points) for i in range(3)]) for op in [min, max]]
center = (minimum + maximum) / 2
distance = max((maximum - minimum).length * 1.25, .1)
views = [('front', (0, -1, 0)), ('side', (1, 0, 0)), ('top', (0, 0, 1)), ('perspective', (1, -1, 1))]
state = dict(index=0, ready=False, captures=[])


def step():
    try:
        window = bpy.context.window_manager.windows[0]
        area = next(a for a in window.screen.areas if a.type == 'VIEW_3D')
        space = area.spaces.active
        space.shading.type = 'SOLID'
        space.shading.color_type = 'OBJECT'
        space.overlay.show_floor = False
        for ob in bpy.data.objects:
            ob.color = (1, .48, .12, 1) if ob.get('placement_status') == 'UNPLACED_SOURCE_CUT_LAYOUT' else (.18, .6, .9, 1)
        area.header_text_set('TEST 30 | CAN XAC NHAN | ' + bpy.context.scene.get('scope', 'unknown'))
        name, direction = views[state['index']]
        if state['ready']:
            path = output / ('viewport_' + name + '.png')
            subprocess.run(['import', '-window', 'root', str(path)], check=True, timeout=15)
            state['captures'].append(dict(view=name, file=path.name, method='X11 actual GUI screenshot', render=False))
            state['index'] += 1
            state['ready'] = False
            if state['index'] == len(views):
                (output / 'capture_manifest.json').write_text(json.dumps(state['captures'], indent=2))
                bpy.ops.wm.quit_blender()
                return None
            name, direction = views[state['index']]
        region = space.region_3d
        region.view_rotation = Vector(direction).to_track_quat('Z', 'Y')
        region.view_location = center
        region.view_distance = distance
        region.view_perspective = 'PERSP' if name == 'perspective' else 'ORTHO'
        area.tag_redraw()
        state['ready'] = True
        return 4
    except Exception:
        import traceback
        (output / 'capture_failure.log').write_text(traceback.format_exc())
        bpy.ops.wm.quit_blender()
        return None


bpy.app.timers.register(step, first_interval=5)

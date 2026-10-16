"""Integration regression: build, reopen and measure real Blender meshes."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('blender'), 'Blender is required for geometry integration')
class BlenderGeometryTests(unittest.TestCase):
    def test_design_bounds_survive_blend_and_glb(self):
        scene = json.loads((ROOT / 'examples/living_room.json').read_text())
        for kind, size, rotation in [
            ('sofa', [3200, 1050, 820], [0, 0, 0]),
            ('armchair', [900, 800, 860], [0, 0, 0]),
            ('sofa', [2800, 950, 860], [0, 0, 37]),
            ('bed', [2000, 2200, 900], [0, 0, 0]),
        ]:
            obj = dict(scene['objects'][2], id=f'case_{len(scene["objects"])}',
                       kind=kind, size_mm=size, center_mm=[7000, -3000, 1000],
                       rotation_deg=rotation)
            scene['objects'].append(obj)
        with tempfile.TemporaryDirectory(dir=ROOT / 'outputs', prefix='geometry-test-') as folder:
            folder = Path(folder)
            source = folder / 'scene.json'
            source.write_text(json.dumps(scene))
            output = folder / 'build'
            check = folder / 'check.py'
            check.write_text('''import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector,Euler
source,out=map(Path,sys.argv[sys.argv.index('--')+1:])
scene=json.loads(source.read_text())
bpy.ops.wm.open_mainfile(filepath=str(out/'hg_scene.blend'))
def measure(imported=False):
    rows=[]
    deps=bpy.context.evaluated_depsgraph_get()
    for spec in scene['objects']:
        parts=[o for o in bpy.data.objects if o.type=='MESH' and
               (o.name.startswith(spec['id']+'_') if imported else o.get('HG_source_id')==spec['id'])]
        assert parts, spec['id']
        inv=Euler(tuple(math.radians(v) for v in spec.get('rotation_deg',[0,0,0])),'XYZ').to_matrix().inverted()
        center=Vector(spec['center_mm'])*.001
        points=[]
        for obj in parts:
            evaluated=obj.evaluated_get(deps)
            points.extend(inv@(evaluated.matrix_world@v.co-center) for v in evaluated.data.vertices)
        low=[min(p[i] for p in points)*1000 for i in range(3)]
        high=[max(p[i] for p in points)*1000 for i in range(3)]
        actual=[high[i]-low[i] for i in range(3)]
        for i,size in enumerate(spec['size_mm']):
            assert abs(actual[i]-size)<.1, (spec['id'],actual,spec['size_mm'])
            assert abs(low[i]+size/2)<.1 and abs(high[i]-size/2)<.1, (spec['id'],low,high)
        rows.append({'id':spec['id'],'actual_mm':actual,'expected_mm':spec['size_mm']})
    return rows
rows=measure()
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(out/'hg_scene.glb'))
measure(imported=True)
(out/'measured.json').write_text(json.dumps(rows))
print('PASS: BLEND and GLB design bounds verified')
''')
            def run(*args):
                result = subprocess.run(['blender', '-b', '-t', '2', '--python-exit-code', '1',
                                         *map(str, args)], cwd=ROOT, capture_output=True,
                                        text=True, timeout=120)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            run('--python', ROOT / 'scripts/blender_build.py', '--', source, output)
            report = json.loads((output / 'qa_report.json').read_text())
            self.assertTrue(report['blender_details']['glb_created'])
            self.assertIsNone(report['blender_details']['glb_error'])
            run('--python', check, '--', source, output)
            measured = json.loads((output / 'measured.json').read_text())
            self.assertEqual(len(measured), 10)
            sofa = next(row for row in measured if row['id'] == 'sofa_01')
            self.assertAlmostEqual(sofa['actual_mm'][1], 950, delta=.1)


if __name__ == '__main__':
    unittest.main()

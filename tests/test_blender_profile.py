"""Real Blender regression on synthetic contours, not fake AI recognition evidence."""
import hashlib,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
from hgcloud.raster_profile import trace
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(shutil.which('blender'),'Blender required')
class BlenderProfileTests(unittest.TestCase):
    def test_objects_voids_thickness_and_reject_center_overlap(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'outputs',prefix='plate-regression-') as folder:
            folder=Path(folder);source=folder/'synthetic.png'
            im=Image.new('RGB',(230,180),'white');d=ImageDraw.Draw(im)
            d.line([(10,10),(70,10),(70,15),(90,15),(90,10),(100,10),(100,160),(70,160),(40,70),(10,70),(10,10)],fill='black',width=2)
            for x,y in [(25,25),(80,30),(80,100)]:d.ellipse((x-2,y-2,x+2,y+2),fill='red')
            d.rectangle((125,10,215,100),outline='black',width=2);d.rectangle((160,45,180,65),outline='black',width=2)
            for x,y in [(140,25),(200,25),(140,85),(200,85)]:d.ellipse((x-2,y-2,x+2,y+2),fill='red')
            im.save(source)
            evidence={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                      'dimensions_mm':{'width':241.3,'height':381,'thickness':18.5},
                      'profiles':{'side':trace(source,(0,0,110,175)),'seat':trace(source,(120,5,220,105))}}
            sp=folder/'evidence.json';sp.write_text(json.dumps(evidence))
            def run(script,out):
                return subprocess.run(['blender','-b','-t','2','--python-exit-code','1','--python',str(script),'--',str(sp),str(out)],cwd=ROOT,capture_output=True,text=True,timeout=120)
            script=ROOT/'scripts/blender_profile_build.py';out=folder/'build'
            r=run(script,out);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            qa=json.loads((out/'object_qa.json').read_text())
            self.assertEqual(len(qa['objects']),5);self.assertEqual(qa['drill_markers'],16)
            self.assertEqual(qa['physical_drill_bores'],0);self.assertEqual(qa['glb_drill_markers'],16)
            self.assertTrue(all(row['pass'] and row['nonmanifold_edges']==0 for row in qa['objects']))
            self.assertTrue(all(sum(v*v for v in row['world_center_mm'])>10000 for row in qa['objects'] if row['id'].startswith('panel_')))
            self.assertIn('PASS',qa['central_void_test'])
            # Inject original placement defect into a throwaway script; real checks must reject it.
            broken=folder/'broken.py'
            broken.write_text(script.read_text().replace('Vector((0,-(w-t)/2,0))','Vector((0,0,0))'))
            r=run(broken,folder/'bad-build');self.assertNotEqual(r.returncode,0)
            self.assertFalse((folder/'bad-build/detailed_draft.blend').exists())
            # Leaving the central cutter unapplied must fail the physical ray test.
            filled=folder/'filled.py'
            filled.write_text(script.read_text().replace('bpy.ops.object.modifier_apply(modifier=modifier.name);',''))
            r=run(filled,folder/'filled-build');self.assertNotEqual(r.returncode,0)
            self.assertFalse((folder/'filled-build/detailed_draft.blend').exists())

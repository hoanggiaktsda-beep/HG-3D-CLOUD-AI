"""Receive images or compile reviewed observations into Blender scene JSON."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hgcloud.intake import receive,compile_scene
p=argparse.ArgumentParser()
s=p.add_subparsers(dest='cmd',required=True)
a=s.add_parser('receive');a.add_argument('image');a.add_argument('input_type');a.add_argument('output')
b=s.add_parser('compile');b.add_argument('intake');b.add_argument('observations');b.add_argument('output')
a=p.parse_args()
if a.cmd=='receive': receive(a.image,a.input_type,a.output)
else:
    scene=compile_scene(a.intake,a.observations)
    with Path(a.output).open('x',encoding='utf8') as f: json.dump(scene,f,ensure_ascii=False,indent=2)

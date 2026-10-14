"""Offline end-to-end integration; never makes external model calls or renders."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hgcloud.intake import receive,compile_scene
from hgcloud.vision import ReplayProvider,analyze,prepare_request
from hgcloud.core import SceneError
ROOT=Path(__file__).resolve().parents[1]


def run(image,input_type,output,response_file):
    output=Path(output)
    receive(image,input_type,output)
    state={'status':'RECEIVED','mode':'offline_replay','live_model_executed':False}
    state_path=output/'pipeline.json'
    def save():state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2))
    save()
    try:
        observations=analyze(output/'intake.json',ReplayProvider(response_file))
        op=output/'observations.json';op.write_text(json.dumps(observations,ensure_ascii=False,indent=2))
        state['status']='ANALYZED';save()
        scene=compile_scene(output/'intake.json',op)
        sp=output/'scene.json';sp.write_text(json.dumps(scene,ensure_ascii=False,indent=2))
        state['status']='SCENE_PREPARED';save()
        for script in ['blender_build.py','verify_blender.py']:
            subprocess.run(['blender','-b','-t','2','--python-exit-code','1','--python',str(ROOT/'scripts'/script),
                            '--',str(sp.resolve()),str((output/'build').resolve())],cwd=ROOT,check=True,timeout=120)
        report=json.loads((output/'build/qa_report.json').read_text())
        if not report['blender_details']['glb_created'] or report['blender_details']['glb_error']:
            raise SceneError('GLB export failed')
        state['status']='BUILT_NEEDS_REVIEW';state['geometry_status']=report['geometry_status'];save()
    except Exception as exc:
        state['status']='BLOCKED' if isinstance(exc,SceneError) else 'FAILED'
        state['error']=str(exc);save()
        raise
    return state


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('run');a.add_argument('image');a.add_argument('input_type');a.add_argument('output');a.add_argument('--response-file',required=True)
    b=sub.add_parser('prepare-request');b.add_argument('intake');b.add_argument('output');b.add_argument('--model',required=True)
    args=p.parse_args()
    if args.cmd=='run':run(args.image,args.input_type,args.output,args.response_file)
    else:
        request=prepare_request(args.intake,args.model)
        with Path(args.output).open('x') as f:json.dump(request,f)

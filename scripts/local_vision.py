"""Analyze a local intake with already-downloaded safetensors. No network download."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hgcloud.local_vision import LocalCPUVision


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('intake', type=Path)
    parser.add_argument('model_dir', type=Path)
    parser.add_argument('model_provenance', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--detector-dir', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; preserve previous evidence')
    metadata = json.loads(args.model_provenance.read_text())
    if args.detector_dir and 'detector' not in metadata:
        parser.error('Detector metadata is required')
    provider = LocalCPUVision(args.model_dir, metadata.get('vlm', metadata), args.detector_dir, metadata.get('detector'))
    result = provider.analyze(args.intake)
    with args.output.open('x') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
    print(json.dumps(dict(status=result['status'], build_allowed=result['build_allowed'])))

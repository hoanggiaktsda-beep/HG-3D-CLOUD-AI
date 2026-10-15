"""Read public TEST 31 ledgers, without starting Blender or changing state."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hgcloud.cloud_jobs31 import manifest_valid

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
rows = []
for path in sorted(args.output.glob('*/*/state.json')):
    state = json.loads(path.read_text())
    row = {key: state.get(key) for key in ['job_id', 'revision', 'version', 'status', 'progress_percent', 'error', 'updated_utc', 'run_url']}
    if state['status'] == 'NEEDS_REVIEW':
        try: row['artifact_integrity_verified'] = manifest_valid(path.parent / 'published')
        except (OSError, ValueError, KeyError): row['artifact_integrity_verified'] = False
    rows.append(row)
print(json.dumps(rows, ensure_ascii=False, indent=2))

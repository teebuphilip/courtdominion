#!/usr/bin/env python3
import os, sys, json, uuid, subprocess
OUT = os.getenv('OUTPUT_DIR','./outputs')
os.makedirs(OUT, exist_ok=True)
found = None
for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), 'app','legacy')):
    if 'dbb2_main.py' in files:
        found = os.path.join(root, 'dbb2_main.py')
        break
if not found:
    print('Legacy runner dbb2_main.py not found.')
    sys.exit(1)
out_file = os.path.join(OUT, f'projections_{uuid.uuid4().hex}.json')
env = os.environ.copy()
env['PROJECTIONS_OUTPUT'] = out_file
proc = subprocess.run([sys.executable, found], env=env)
print('Runner exit', proc.returncode)
if os.path.exists(out_file):
    try:
        with open(out_file) as f:
            j = json.load(f)
            print('Output preview:', j if isinstance(j, dict) else str(j)[:200])
    except Exception as e:
        print('Could not parse output json:', e)

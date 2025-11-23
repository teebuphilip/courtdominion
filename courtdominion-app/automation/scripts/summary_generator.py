import os, json, datetime
today = datetime.date.today().isoformat()
out_dir = os.path.join('courtdominion-automation','outputs','generated', today)
log_dir = os.path.join('courtdominion-automation','outputs','logs')
summary_path = os.path.join(log_dir, f'summary_{today}_human.txt')
# gather parts
parts = []
parts.append('COURTDOMINION DAILY SUMMARY - ' + today)
# channel status
chan_file = os.path.join(out_dir,'channel_status.json')
if os.path.exists(chan_file):
    ch = json.load(open(chan_file))
    parts.append('Publish status per channel:')
    for k,v in ch.items():
        parts.append(f"- {k}: {v.get('status')} ({v.get('reason') or ''})")
else:
    parts.append('No channel_status.json found.')
# generator rationale
rat_file = os.path.join(out_dir,'rationale.json')
if os.path.exists(rat_file):
    rat = json.load(open(rat_file))
    parts.append('\nNarrative rationale:')
    parts.append(rat.get('narrative',''))
    parts.append('\nWhy: ' + rat.get('why',''))
else:
    parts.append('No rationale found.')
# claude outputs
proj_file = os.path.join(out_dir,'projections.json')
if os.path.exists(proj_file):
    proj = json.load(open(proj_file))
    parts.append('\nClaude runner outputs:')
    parts.append(f"- players: {len(proj.get('players',[]))} projections\n")
else:
    parts.append('No Claude projections found.')
# technical summary
parts.append('\nTechnical notes: check logs/ for full details.')
with open(summary_path,'w') as f:
    f.write('\n'.join(parts))
print('Summary generated at', summary_path)

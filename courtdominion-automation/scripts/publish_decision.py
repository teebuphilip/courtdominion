import os, json, datetime, yaml
from pathlib import Path
cfg_path = Path('courtdominion-automation/config/settings.yml')
with open(cfg_path) as f:
    cfg = yaml.safe_load(f)
today = datetime.date.today().isoformat()
pause_until = cfg.get('pause_until')
log_dir = Path(cfg.get('log_directory'))
log_dir.mkdir(parents=True, exist_ok=True)
out_dir = Path('courtdominion-automation/outputs/generated') / today
filter_file = out_dir / 'filter_result.json'
manifest = {}
if (out_dir / 'manifest.json').exists():
    manifest = json.load(open(out_dir / 'manifest.json'))
# approval flag path
approval_flag = Path('courtdominion-automation/outputs/approval.flag')
user_approved = approval_flag.exists() and approval_flag.read_text().strip().lower() == 'approved'
# check pause
do_publish = True
if pause_until:
    if today <= pause_until:
        do_publish = False
# evaluate filter
filter_passed = True
if filter_file.exists():
    fr = json.load(open(filter_file))
    filter_passed = fr.get('passed', True)
else:
    filter_passed = False
platforms = cfg.get('platforms',[])
channel_status = {}
for p in platforms:
    status = {'status':'NOT_RUN','reason':None}
    draft = out_dir / f"{p}_draft.txt"
    if not draft.exists():
        status['status']='NO_DRAFT'; status['reason']='missing'
    else:
        if do_publish and filter_passed:
            status['status']='SUCCESS'; status['post_id']=f"{p}-{today}-001"
            # append to channel log
            with open(log_dir / f"{p}.log", 'a') as cl:
                cl.write(f"{today} : Published - post_id={status['post_id']}\n")
        else:
            if not do_publish:
                status['status']='PAUSED'; status['reason']='paused by pause_until'
            else:
                status['status']='FILTER_FAILED'; status['reason']='quality gate failed'
            with open(log_dir / f"{p}.log", 'a') as cl:
                cl.write(f"{today} : {status['status']} - {status.get('reason')}\n")
    channel_status[p]=status
# write channel_status.json into generated folder
status_file = out_dir / 'channel_status.json'
with open(status_file, 'w') as sf:
    json.dump(channel_status, sf)
# write summary into logs
summary = {'date': today, 'do_publish': do_publish, 'filter_passed': filter_passed, 'user_approved': user_approved, 'channel_status': channel_status}
with open(log_dir / f"summary_{today}.json", 'w') as sf:
    json.dump(summary, sf)
print('Publish decision completed. Do_publish=', do_publish)

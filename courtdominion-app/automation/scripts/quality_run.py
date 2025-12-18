import os, json, datetime, importlib.util
# dynamic import for filters
spec = importlib.util.spec_from_file_location('filters', os.path.join('courtdominion-automation','quality','filters.py'))
filters = importlib.util.module_from_spec(spec)
spec.loader.exec_module(filters)
quality_filter = filters.quality_filter
today = datetime.date.today().isoformat()
out_dir = os.path.join('courtdominion-automation','outputs','generated', today)
result = {'date': today, 'passed': True, 'details': {}}
if not os.path.exists(out_dir):
    print('No generated outputs for', today)
else:
    for fname in os.listdir(out_dir):
        if fname.endswith('_draft.txt'):
            text = open(os.path.join(out_dir,fname)).read()
            ok, reason = quality_filter(text)
            result['details'][fname] = {'passed': ok, 'reason': reason}
            if not ok:
                result['passed'] = False
    with open(os.path.join(out_dir,'filter_result.json'),'w') as f:
        json.dump(result,f)
    print('Quality run complete. Passed:', result['passed'])

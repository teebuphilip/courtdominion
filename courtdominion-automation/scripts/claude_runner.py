import json, datetime, random, os
out_dir = os.path.join('courtdominion-automation','outputs','generated', datetime.date.today().isoformat())
os.makedirs(out_dir, exist_ok=True)
# produce mock projections and injury feed
projections = {'generated_at': datetime.datetime.utcnow().isoformat(), 'players': []}
for i in range(10):
    projections['players'].append({'name': f'Player{i+1}', 'proj_points': round(random.uniform(5,30),1)})
with open(os.path.join(out_dir,'projections.json'),'w') as f:
    json.dump(projections,f)
injuries = {'generated_at': datetime.datetime.utcnow().isoformat(), 'injuries': [{'player':'Player3','status':'questionable'}]}
with open(os.path.join(out_dir,'injury_feed.json'),'w') as f:
    json.dump(injuries,f)
print('Claude runner produced projections and injuries')
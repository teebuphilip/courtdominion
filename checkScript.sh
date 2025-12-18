# 1. Does cache file exist?
docker compose run --rm automation ls -lh /data/outputs/

# Should see player_stats_cache.json

# 2. What's in the cache?
docker compose run --rm automation python -c "
import json
with open('/data/outputs/player_stats_cache.json') as f:
    data = json.load(f)
    print(f'Players in cache: {data[\"player_count\"]}')
    print(f'Cached at: {data[\"cached_at\"]}')
"

# 3. Did you run the automation pipeline after building cache?
docker compose run --rm automation

# This should generate players.json, projections.json, etc.

# 4. Are the output files there?
docker compose run --rm automation ls -la /data/outputs/*.json

# Should see:
# players.json
# projections.json
# insights.json
# risk.json
# injuries.json
# manifest.json

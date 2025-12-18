# CourtDominion Automation - Secrets Setup

## GitHub Secrets Required

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

### Required for Content Generation (Phase 1 - TODAY)

**BACKEND_URL**
```
Value: Your backend API URL
Example: https://api.courtdominion.com
Or for testing: http://localhost:8000
```

**COURTDOMINION_API_KEY**
```
Value: Your CourtDominion API key (Enterprise tier for automation)
Example: enterprise_abc123xyz...
```

**OPENAI_API_KEY**
```
Value: Your OpenAI API key
Example: sk-proj-...
Get from: https://platform.openai.com/api-keys
```

---

### Optional for Publishing (Phase 2 - LATER)

**TWITTER_API_KEY** & **TWITTER_API_SECRET**
```
Get from: https://developer.twitter.com/
```

**REDDIT_APP_ID** & **REDDIT_APP_SECRET** & **REDDIT_USER**
```
Get from: https://www.reddit.com/prefs/apps
```

**DISCORD_WEBHOOK_URL**
```
Discord Server → Server Settings → Integrations → Webhooks
```

---

## Local Testing

Create a `.env` file in `courtdominion-automation/`:

```bash
# Backend
BACKEND_URL=http://localhost:8000
COURTDOMINION_API_KEY=your_api_key_here

# OpenAI
OPENAI_API_KEY=sk-proj-your_key_here
OPENAI_MODEL=gpt-4

# Optional (for publishing later)
TWITTER_API_KEY=
TWITTER_API_SECRET=
REDDIT_APP_ID=
REDDIT_APP_SECRET=
REDDIT_USER=
DISCORD_WEBHOOK_URL=
```

Then run:
```bash
cd courtdominion-automation
python scripts/claude_runner.py
python scripts/generator.py
```

---

## Testing Order

1. **Test Backend Connection**
   ```bash
   curl -H "x-api-key: YOUR_KEY" http://localhost:8000/health
   ```

2. **Test Claude Runner**
   ```bash
   export BACKEND_URL=http://localhost:8000
   export COURTDOMINION_API_KEY=your_key
   python scripts/claude_runner.py
   ```

3. **Test Content Generator**
   ```bash
   export OPENAI_API_KEY=sk-proj-...
   python scripts/generator.py
   ```

4. **Check Outputs**
   ```bash
   ls -la outputs/generated/$(date +%Y-%m-%d)/
   ```

---

## Cost Estimates

**OpenAI API (GPT-4):**
- ~$0.03 per run (5 platform posts)
- ~$0.90/month (30 days)
- Switch to `gpt-3.5-turbo` for ~$0.003/run (~$0.09/month)

**Backend API:**
- 50 projection calls/day
- Depends on your CourtDominion API tier

---

## Troubleshooting

**Error: "OPENAI_API_KEY not set"**
- Add secret to GitHub or set environment variable

**Error: "COURTDOMINION_API_KEY not set"**
- Add secret to GitHub or set environment variable

**Error: "Failed to get projections"**
- Check BACKEND_URL is correct
- Check backend is running
- Verify API key is valid

**Error: "OpenAI API error: 401"**
- Check OPENAI_API_KEY is valid
- Verify you have API credits

---

## Next Steps

1. ✅ Set up GitHub secrets (3 required secrets above)
2. ✅ Push code to GitHub
3. ✅ Trigger workflow manually (Actions → Daily Automation → Run workflow)
4. ✅ Check outputs folder for generated content
5. ⏭️ Later: Add publishing integrations when ready

# CourtDominion Automation

Daily automation for content generation and publishing.

## What It Does

**Every day at 5:00 AM EST:**

1. **Claude Runner** - Fetches real projections from CourtDominion backend API
2. **Content Generator** - Uses OpenAI GPT-4 to create platform-specific content
3. **Quality Filters** - Checks content for placeholders, filler text, length
4. **Publish Decision** - Determines if content should publish (respects pause settings)
5. **Summary Generator** - Creates human-readable summary of the run

**Output:** Generated content files in `outputs/generated/YYYY-MM-DD/`

## Quick Start

### 1. Setup Secrets

See [SETUP_SECRETS.md](SETUP_SECRETS.md) for detailed instructions.

**Required GitHub Secrets:**
- `BACKEND_URL` - Your backend API URL
- `COURTDOMINION_API_KEY` - API key for backend
- `OPENAI_API_KEY` - OpenAI API key

### 2. Configure Settings

Edit `config/settings.yml`:

```yaml
pause_until: "2025-11-19"  # Set to tomorrow to test without publishing
platforms:
  - twitter
  - reddit
  - discord
  - linkedin
  - email
```

### 3. Test Locally

```bash
# Install dependencies
pip install pyyaml requests

# Set environment variables
export BACKEND_URL=http://localhost:8000
export COURTDOMINION_API_KEY=your_key
export OPENAI_API_KEY=sk-proj-...

# Run scripts
python scripts/claude_runner.py
python scripts/generator.py
python scripts/quality_run.py
python scripts/publish_decision.py
python scripts/summary_generator.py

# Check outputs
ls outputs/generated/$(date +%Y-%m-%d)/
```

### 4. Push to GitHub

```bash
git add .
git commit -m "automation: production ready"
git push
```

### 5. Test on GitHub

Go to: **Actions** → **Daily Automation** → **Run workflow**

Check outputs in next commit to `outputs/generated/`

## File Structure

```
courtdominion-automation/
├── .github/workflows/
│   └── autopublish.yml          # GitHub Actions workflow (runs daily)
├── scripts/
│   ├── claude_runner.py         # Fetch projections from backend
│   ├── generator.py             # Generate content with OpenAI
│   ├── quality_run.py           # Quality filters
│   ├── publish_decision.py      # Determine if/what to publish
│   └── summary_generator.py     # Human-readable summary
├── quality/
│   └── filters.py               # Content quality checks
├── config/
│   ├── settings.yml             # Pause, platforms, timing
│   └── master_tasks.yaml        # 63 daily tasks until launch
├── outputs/
│   ├── generated/               # Daily content (committed to git)
│   │   └── YYYY-MM-DD/
│   │       ├── projections.json
│   │       ├── twitter_draft.txt
│   │       ├── reddit_draft.txt
│   │       ├── etc...
│   └── logs/                    # Logs per platform (committed to git)
└── SETUP_SECRETS.md             # Secret setup guide
```

## What Gets Generated

Each day creates:

- `projections.json` - Real NBA projections from backend
- `injury_feed.json` - Injury updates (when available)
- `twitter_draft.txt` - Twitter thread (3-4 tweets)
- `reddit_draft.txt` - Reddit post (~300 words)
- `discord_draft.txt` - Discord message (~200 words)
- `linkedin_draft.txt` - LinkedIn post (~250 words)
- `email_draft.txt` - Email newsletter (~300 words)
- `rationale.json` - Why these topics were chosen
- `manifest.json` - What was generated
- `filter_result.json` - Quality check results
- `channel_status.json` - Publish status per platform
- `summary_YYYY-MM-DD_human.txt` - Human-readable summary

## Configuration

### Pause Publishing

Edit `config/settings.yml`:

```yaml
pause_until: "2025-11-25"  # Don't publish until this date
```

This lets content generate daily but not publish until you're ready.

### Change Platforms

Edit `config/settings.yml`:

```yaml
platforms:
  - twitter
  - reddit
  # - discord  # Commented out = disabled
```

## Costs

**OpenAI API (GPT-4):**
- ~$0.03 per daily run
- ~$0.90/month (30 days)
- Use `gpt-3.5-turbo` for ~$0.09/month

**Backend API:**
- 50 projection calls/day
- Covered by Enterprise tier

## Troubleshooting

**No outputs generated?**
- Check GitHub Actions logs for errors
- Verify secrets are set correctly
- Check backend is accessible from GitHub (if self-hosted)

**Content quality is poor?**
- Adjust prompts in `scripts/generator.py`
- Try different OpenAI model (gpt-4-turbo, gpt-3.5-turbo)
- Check projections.json has good data

**Workflow not running?**
- Check cron schedule in `.github/workflows/autopublish.yml`
- Verify repository has Actions enabled
- Try manual trigger: Actions → Run workflow

## Next Steps

1. ✅ Get content generation working (TODAY)
2. ⏭️ Add actual publishing (Twitter/Reddit APIs) - LATER
3. ⏭️ Add email sending (Sendgrid/Mailchimp) - LATER
4. ⏭️ Build frontend dashboard to view outputs - LATER

## Support

Check outputs/logs/ for detailed run information.

For issues with:
- Projections → Check backend logs
- Content generation → Check OpenAI API status
- Quality filters → Review filter_result.json

# CourtDominion Automation

## What This Does

Runs daily automation tasks:
1. Fetch NBA projections from backend
2. Generate marketing content with OpenAI
3. (Future) Run analytics, finance, PMO tasks

## Directory Structure

```
automation/
├── run_automation.sh          # Main orchestration script (START HERE)
├── Dockerfile                 # Docker build file
├── requirements.txt           # Python dependencies
│
├── scripts/                   # All Python scripts
│   ├── claude_runner.py      # Fetches projections from backend
│   ├── generator.py          # Generates content with OpenAI
│   └── (future scripts)      # analytics.py, finance.py, pmo.py
│
├── config/                    # Configuration files
│   └── ...
│
├── quality/                   # Quality checks
│   └── ...
│
└── outputs/                   # ALL OUTPUT GOES HERE
    ├── logs/                  # ALL LOGS HERE
    │   ├── run-auto.log.YYYY-MM-DD-HH-MM-SS  # Each run's log
    │   ├── twitter.log        # Twitter publish history
    │   ├── reddit.log         # Reddit publish history
    │   ├── discord.log        # Discord publish history
    │   ├── linkedin.log       # LinkedIn publish history
    │   └── email.log          # Email send history
    │
    └── generated/             # GENERATED CONTENT BY DATE
        └── YYYY-MM-DD/        # Today's date
            ├── twitter_draft.txt
            ├── reddit_draft.txt
            ├── discord_draft.txt
            ├── linkedin_draft.txt
            ├── email_draft.txt
            ├── projections.json
            ├── rationale.json
            └── manifest.json
```

## How to Run

```bash
# From courtdominion-app directory:
docker compose up
```

The automation container will:
1. Start up
2. Run `run_automation.sh`
3. Execute all steps
4. Create log file and generated content
5. Exit

## How to Debug

### If the whole thing fails:
```bash
# Check the latest run log
ls -lt automation/outputs/logs/run-auto.log.* | head -1

# Read it
cat automation/outputs/logs/run-auto.log.[latest]
```

### If Step 1 fails (projections):
```bash
# Check if backend is running
docker ps | grep backend

# Check backend health
curl http://localhost:8000/health

# Check backend logs
docker compose logs backend

# Run step manually
docker compose run --rm automation python scripts/claude_runner.py
```

### If Step 2 fails (content generation):
```bash
# Check if OpenAI key is set
docker compose run --rm automation env | grep OPENAI

# Run step manually
docker compose run --rm automation python scripts/generator.py
```

## How to Check Content Quality

```bash
# See today's generated content
ls -la automation/outputs/generated/$(date +%Y-%m-%d)/

# Read Twitter content
cat automation/outputs/generated/$(date +%Y-%m-%d)/twitter_draft.txt

# Read Reddit content
cat automation/outputs/generated/$(date +%Y-%m-%d)/reddit_draft.txt

# If content sucks, blame ChatGPT
# Then edit prompts in: automation/scripts/generator.py
```

## How to Add New Tasks

1. **Create the script:**
   ```bash
   # Example: analytics.py
   touch automation/scripts/analytics.py
   ```

2. **Edit run_automation.sh:**
   ```bash
   nano automation/run_automation.sh
   # Find STEP 3 section (commented out)
   # Uncomment it
   ```

3. **Rebuild and test:**
   ```bash
   docker compose build automation --no-cache
   docker compose up
   ```

## Important Files

### run_automation.sh
- Main orchestration script
- Has ALL the comments explaining what happens
- Easy to extend with new steps
- Logs everything

### scripts/claude_runner.py
- Calls backend API: POST /v1/run_projections
- Saves: outputs/generated/[date]/projections.json
- Saves: outputs/generated/[date]/injury_feed.json

### scripts/generator.py
- Reads projections.json
- Calls OpenAI API
- Generates content for each platform
- Saves: outputs/generated/[date]/[platform]_draft.txt

## When Stuff Breaks at 2AM

1. Find the latest log:
   ```bash
   ls -lt automation/outputs/logs/run-auto.log.* | head -1
   ```

2. Read it - it will tell you exactly what failed

3. Run that specific script manually:
   ```bash
   docker compose run --rm automation python scripts/[failed-script].py
   ```

4. Fix the issue

5. Re-run the whole thing:
   ```bash
   docker compose up
   ```

## Platform Logs (Future)

When you implement publishing, log to these files:
- `outputs/logs/twitter.log` - Date, post title/ID, "published successfully"
- `outputs/logs/reddit.log` - Date, post title/ID, "published successfully"
- `outputs/logs/discord.log` - Date, message ID, "sent successfully"
- `outputs/logs/linkedin.log` - Date, post ID, "published successfully"
- `outputs/logs/email.log` - Date, subject, recipient count, "sent successfully"

Format: `YYYY-MM-DD HH:MM:SS | [Title/ID] | Status`

## Simple. Documented. Ready for Production.

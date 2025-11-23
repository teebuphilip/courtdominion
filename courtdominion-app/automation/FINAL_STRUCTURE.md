# FINAL AUTOMATION SCRIPT - CORRECT DIRECTORY STRUCTURE

## What's Fixed

1. **Correct directory structure** - logs/ and generated/ exactly as you specified
2. **Tons of comments** - 300+ lines of explanation for debugging
3. **Verbose logging** - Every step prints what it's doing and where
4. **Unique log files** - run-auto.log.[date-time] for each run
5. **Platform logs** - twitter.log, reddit.log, etc. for publishing history

## Directory Structure

```
automation/outputs/
├── logs/                                      # ALL LOGS HERE
│   ├── run-auto.log.2025-11-22-09-30-15     # This run's log
│   ├── run-auto.log.2025-11-22-14-15-32     # Another run (if stuff broke)
│   ├── twitter.log                           # Twitter publish history
│   ├── reddit.log                            # Reddit publish history
│   ├── discord.log                           # Discord publish history
│   ├── linkedin.log                          # LinkedIn publish history
│   └── email.log                             # Email send history
│
└── generated/                                 # GENERATED CONTENT BY DATE
    ├── 2025-11-22/                           # Today
    │   ├── twitter_draft.txt                 # ChatGPT's content
    │   ├── reddit_draft.txt                  # (blame him if it sucks)
    │   ├── discord_draft.txt
    │   ├── linkedin_draft.txt
    │   ├── email_draft.txt
    │   ├── projections.json
    │   ├── rationale.json
    │   └── manifest.json
    │
    └── 2025-11-23/                           # Tomorrow
        └── ...
```

## Deploy

```bash
cd courtdominion-app

# Copy the updated shell script
cp run_automation.sh ./automation/run_automation.sh

# Make it executable
chmod +x ./automation/run_automation.sh

# Rebuild (only automation container needs rebuild)
docker compose build automation --no-cache

# Run
docker compose up
```

## What You'll See

```
Creating directory structure...
  ✓ Created: courtdominion-automation/outputs/logs
  ✓ Created: courtdominion-automation/outputs/generated
  ✓ Created: courtdominion-automation/outputs/generated/2025-11-22
  ✓ Initialized platform log files

============================================================
COURTDOMINION AUTOMATION WORKFLOW
Started: 2025-11-22 09:30:15
============================================================

Paths for this run:
  Log file:        courtdominion-automation/outputs/logs/run-auto.log.2025-11-22-09-30-15
  Generated dir:   courtdominion-automation/outputs/generated/2025-11-22
  Platform logs:   courtdominion-automation/outputs/logs/[platform].log

============================================================
STEP 1: FETCHING PROJECTIONS FROM BACKEND
============================================================

Script: scripts/claude_runner.py
Purpose: Get NBA player projections for today
Output: generated/2025-11-22/projections.json

[claude_runner.py output...]

✅ STEP 1 SUCCESS: Projections fetched

   Created: courtdominion-automation/outputs/generated/2025-11-22/projections.json
   Created: courtdominion-automation/outputs/generated/2025-11-22/injury_feed.json

============================================================
STEP 2: GENERATING CONTENT WITH OPENAI
============================================================

Script: scripts/generator.py
Purpose: Create platform-specific marketing content
Platforms: Twitter, Reddit, Discord, LinkedIn, Email
Output: generated/2025-11-22/[platform]_draft.txt

[generator.py output...]

✅ STEP 2 SUCCESS: Content generated

   Generated content files:
   ✓ courtdominion-automation/outputs/generated/2025-11-22/twitter_draft.txt (865 bytes)
   ✓ courtdominion-automation/outputs/generated/2025-11-22/reddit_draft.txt (1992 bytes)
   ✓ courtdominion-automation/outputs/generated/2025-11-22/discord_draft.txt (1194 bytes)
   ✓ courtdominion-automation/outputs/generated/2025-11-22/linkedin_draft.txt (1549 bytes)
   ✓ courtdominion-automation/outputs/generated/2025-11-22/email_draft.txt (2082 bytes)
   ✓ courtdominion-automation/outputs/generated/2025-11-22/rationale.json
   ✓ courtdominion-automation/outputs/generated/2025-11-22/manifest.json

   Review content quality in: courtdominion-automation/outputs/generated/2025-11-22/
   If content sucks, blame ChatGPT and update prompts in generator.py

============================================================
✅ AUTOMATION WORKFLOW COMPLETED SUCCESSFULLY
Ended: 2025-11-22 09:31:42
============================================================

Summary:
  ✓ Projections fetched
  ✓ Content generated for 5 platforms

Files created:
  Content:  courtdominion-automation/outputs/generated/2025-11-22/
  Log:      courtdominion-automation/outputs/logs/run-auto.log.2025-11-22-09-30-15

Next steps:
  1. Review generated content in: courtdominion-automation/outputs/generated/2025-11-22/
  2. If content quality is bad, blame ChatGPT
  3. Update prompts in scripts/generator.py if needed
  4. When ready to publish, update platform log files:
     - courtdominion-automation/outputs/logs/twitter.log
     - courtdominion-automation/outputs/logs/reddit.log
     - etc.

When stuff breaks:
  - Check this log: courtdominion-automation/outputs/logs/run-auto.log.2025-11-22-09-30-15
  - Check container logs: docker compose logs automation
  - Run scripts manually to debug: docker compose run automation python scripts/[script].py
```

## Check the Generated Content

```bash
cd courtdominion-app

# See what ChatGPT wrote for Twitter
cat automation/outputs/generated/2025-11-22/twitter_draft.txt

# See what ChatGPT wrote for Reddit
cat automation/outputs/generated/2025-11-22/reddit_draft.txt

# If it's garbage, blame ChatGPT and update prompts
```

## When Stuff Breaks

1. **Check the run log:**
   ```bash
   ls -lt automation/outputs/logs/run-auto.log.* | head -1
   cat [that file]
   ```

2. **Run scripts manually to debug:**
   ```bash
   docker compose run --rm automation python scripts/claude_runner.py
   docker compose run --rm automation python scripts/generator.py
   ```

3. **Check container logs:**
   ```bash
   docker compose logs automation
   docker compose logs backend
   ```

## Adding Future Tasks

When you're ready to add analytics, finance, or PMO:

1. Create the script: `automation/scripts/analytics.py`
2. Edit `automation/run_automation.sh`
3. Find the commented-out STEP 3 section
4. Uncomment it
5. Rebuild: `docker compose build automation --no-cache`

The script is designed to be extended - just uncomment sections as you build them.

## Simple. Commented. Ready to Debug.

Every step explains:
- What it does
- Where it saves files
- How to troubleshoot if it fails
- What to check when content sucks

You can maintain this. You can debug this. You can extend this.

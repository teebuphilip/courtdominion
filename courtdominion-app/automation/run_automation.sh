#!/bin/bash

################################################################################
# COURTDOMINION AUTOMATION RUNNER
# 
# Purpose: Orchestrate all automation tasks in the correct order
# 
# DIRECTORY STRUCTURE:
# ====================
# automation/outputs/                     <- Mounted from host filesystem
#   ├── logs/                             <- ALL LOG FILES GO HERE
#   │   ├── run-auto.log.YYYY-MM-DD-HH-MM-SS   <- This automation run log
#   │   ├── twitter.log                 <- Twitter publish history (date + title + status)
#   │   ├── reddit.log                  <- Reddit publish history
#   │   ├── discord.log                 <- Discord publish history
#   │   ├── linkedin.log                <- LinkedIn publish history
#   │   └── email.log                   <- Email send history
#   │
#   └── generated/                      <- GENERATED CONTENT BY DATE
#       └── YYYY-MM-DD/                 <- Today's date folder
#           ├── twitter_draft.txt       <- What ChatGPT wrote (so you can blame him!)
#           ├── reddit_draft.txt
#           ├── discord_draft.txt
#           ├── linkedin_draft.txt
#           ├── email_draft.txt
#           ├── projections.json
#           ├── rationale.json
#           └── manifest.json
#
# WHY THIS STRUCTURE:
# - logs/ keeps all run logs and publishing history in one place
# - generated/[date]/ keeps content organized by date so you can review what was created
# - When stuff breaks (it will), you can check the run-auto.log to see what happened
# - When content sucks, you can look at generated/[date]/ and blame ChatGPT
#
# WORKFLOW STEPS:
# 1. claude_runner.py   - Fetches projections from backend API
# 2. generator.py       - Uses OpenAI to generate marketing content
# 3. (Future) analytics.py  - Run analytics on performance
# 4. (Future) finance.py    - Calculate budget and costs
# 5. (Future) pmo.py        - Update project management dashboards
#
################################################################################

# Exit immediately if any command fails (safety feature)
set -e

################################################################################
# SETUP TIMESTAMPS AND PATHS
################################################################################

# Current timestamp for this run (used in log filename)
TIMESTAMP=$(date '+%Y-%m-%d-%H-%M-%S')

# Today's date (used for content directory)
TODAY=$(date '+%Y-%m-%d')

# Base output directory (matches Docker volume mount in docker-compose.yml)
BASE_DIR="automation/outputs"

# Logs directory (for ALL log files)
LOGS_DIR="$BASE_DIR/logs"

# Generated content directory (organized by date)
GENERATED_DIR="$BASE_DIR/generated"

# This run's log file (unique per run so you can debug when stuff breaks)
RUN_LOG="$LOGS_DIR/run-auto.log.$TIMESTAMP"

################################################################################
# CREATE DIRECTORY STRUCTURE
################################################################################

echo ""
echo "Creating directory structure..."

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"
echo "  ✓ Created: $LOGS_DIR"

# Create generated content directory if it doesn't exist
mkdir -p "$GENERATED_DIR"
echo "  ✓ Created: $GENERATED_DIR"

# Create today's content directory
mkdir -p "$GENERATED_DIR/$TODAY"
echo "  ✓ Created: $GENERATED_DIR/$TODAY"

# Create platform log files if they don't exist (for future publishing)
touch "$LOGS_DIR/twitter.log"
touch "$LOGS_DIR/reddit.log"
touch "$LOGS_DIR/discord.log"
touch "$LOGS_DIR/linkedin.log"
touch "$LOGS_DIR/email.log"
echo "  ✓ Initialized platform log files"

echo ""

################################################################################
# LOGGING HELPER FUNCTION
# Prints to console AND writes to this run's log file
################################################################################
log() {
    echo "$1" | tee -a "$RUN_LOG"
}

################################################################################
# START OF WORKFLOW
################################################################################

log "============================================================"
log "COURTDOMINION AUTOMATION WORKFLOW"
log "Started: $(date '+%Y-%m-%d %H:%M:%S')"
log "============================================================"
log ""
log "Paths for this run:"
log "  Log file:        $RUN_LOG"
log "  Generated dir:   $GENERATED_DIR/$TODAY"
log "  Platform logs:   $LOGS_DIR/[platform].log"
log "  (Mounted to host at: ./automation/outputs/)"
log ""

################################################################################
# STEP 1: FETCH PROJECTIONS FROM BACKEND
# 
# What it does:
#   - Calls backend API at http://backend:8000/v1/run_projections
#   - Backend runs simple_projections.py (mock data for now)
#   - Saves projection data to: generated/[date]/projections.json
#   - Saves injury feed to: generated/[date]/injury_feed.json
#
# Exit codes:
#   0 = Success (got projections)
#   1 = Failed (can't reach backend, API error, etc.)
#
# If this fails:
#   - Check if backend container is running: docker ps
#   - Check backend logs: docker compose logs backend
#   - Check if backend health endpoint works: curl http://localhost:8000/health
################################################################################

log "============================================================"
log "STEP 1: FETCHING PROJECTIONS FROM BACKEND"
log "============================================================"
log ""
log "Script: scripts/claude_runner.py"
log "Purpose: Get NBA player projections for today"
log "Output: generated/$TODAY/projections.json"
log ""

# Run claude_runner.py
python scripts/claude_runner.py
CLAUDE_EXIT=$?

# Check if it worked
if [[ $CLAUDE_EXIT -eq 0 ]]; then
    log ""
    log "✅ STEP 1 SUCCESS: Projections fetched"
    log ""
    
    # Show what files were created
    if [[ -f "$GENERATED_DIR/$TODAY/projections.json" ]]; then
        log "   Created: $GENERATED_DIR/$TODAY/projections.json"
    fi
    if [[ -f "$GENERATED_DIR/$TODAY/injury_feed.json" ]]; then
        log "   Created: $GENERATED_DIR/$TODAY/injury_feed.json"
    fi
    log ""
else
    log ""
    log "❌ STEP 1 FAILED: claude_runner.py exited with code $CLAUDE_EXIT"
    log ""
    log "Troubleshooting:"
    log "  1. Check if backend is running: docker ps"
    log "  2. Check backend health: curl http://localhost:8000/health"
    log "  3. Check backend logs: docker compose logs backend"
    log ""
    log "============================================================"
    log "WORKFLOW STOPPED AT STEP 1"
    log "Ended: $(date '+%Y-%m-%d %H:%M:%S')"
    log "============================================================"
    exit 1
fi

################################################################################
# STEP 2: GENERATE MARKETING CONTENT WITH OPENAI
#
# What it does:
#   - Reads generated/[date]/projections.json
#   - Calls OpenAI API (requires OPENAI_API_KEY environment variable)
#   - Generates content for each platform:
#     * Twitter: 3-4 tweet thread
#     * Reddit: Post for r/fantasybball
#     * Discord: Community message
#     * LinkedIn: Professional post
#     * Email: Newsletter
#   - Saves each to: generated/[date]/[platform]_draft.txt
#   - Also saves rationale.json and manifest.json
#
# Exit codes:
#   0 = Success (content generated)
#   1 = Failed (no API key, API error, rate limit, etc.)
#
# If this fails:
#   - Check if OPENAI_API_KEY is set: echo $OPENAI_API_KEY
#   - Check if you have OpenAI credits
#   - Check OpenAI API status: https://status.openai.com
#
# When content sucks:
#   - Look at generated/[date]/[platform]_draft.txt
#   - Blame ChatGPT for writing garbage
#   - Update prompts in scripts/generator.py
################################################################################

log "============================================================"
log "STEP 2: GENERATING CONTENT WITH OPENAI"
log "============================================================"
log ""
log "Script: scripts/generator.py"
log "Purpose: Create platform-specific marketing content"
log "Platforms: Twitter, Reddit, Discord, LinkedIn, Email"
log "Output: generated/$TODAY/[platform]_draft.txt"
log ""

# Safety check: Is OpenAI API key set?
if [[ -z "$OPENAI_API_KEY" ]]; then
    log "⚠️  WARNING: OPENAI_API_KEY environment variable is not set!"
    log "   Content generation will fail"
    log "   Fix: Set OPENAI_API_KEY in your .env file"
    log ""
fi

# Run generator.py
python scripts/generator.py
GENERATOR_EXIT=$?

# Check if it worked
if [[ $GENERATOR_EXIT -eq 0 ]]; then
    log ""
    log "✅ STEP 2 SUCCESS: Content generated"
    log ""
    
    # Show what files were created
    log "   Generated content files:"
    for platform in twitter reddit discord linkedin email; do
        FILE="$GENERATED_DIR/$TODAY/${platform}_draft.txt"
        if [[ -f "$FILE" ]]; then
            SIZE=$(wc -c < "$FILE")
            log "   ✓ $FILE (${SIZE} bytes)"
        fi
    done
    
    # Show metadata files
    if [[ -f "$GENERATED_DIR/$TODAY/rationale.json" ]]; then
        log "   ✓ $GENERATED_DIR/$TODAY/rationale.json"
    fi
    if [[ -f "$GENERATED_DIR/$TODAY/manifest.json" ]]; then
        log "   ✓ $GENERATED_DIR/$TODAY/manifest.json"
    fi
    log ""
    log "   Review content quality in: $GENERATED_DIR/$TODAY/"
    log "   If content sucks, blame ChatGPT and update prompts in generator.py"
    log ""
else
    log ""
    log "❌ STEP 2 FAILED: generator.py exited with code $GENERATOR_EXIT"
    log ""
    log "Possible causes:"
    log "  1. OPENAI_API_KEY not set or invalid"
    log "  2. OpenAI API rate limit hit"
    log "  3. Network connectivity issue"
    log "  4. OpenAI API is down (check: https://status.openai.com)"
    log ""
    log "Troubleshooting:"
    log "  1. Check API key: echo \$OPENAI_API_KEY"
    log "  2. Test API: curl https://api.openai.com/v1/models -H \"Authorization: Bearer \$OPENAI_API_KEY\""
    log "  3. Check OpenAI dashboard for credits/errors"
    log ""
    log "============================================================"
    log "WORKFLOW STOPPED AT STEP 2"
    log "Ended: $(date '+%Y-%m-%d %H:%M:%S')"
    log "============================================================"
    exit 1
fi

################################################################################
# FUTURE STEPS (UNCOMMENT WHEN READY)
#
# To add a new step:
# 1. Create the Python script in scripts/ directory
# 2. Uncomment the section below
# 3. Update the comments with what the script does
# 4. Test it manually first: python scripts/[your-script].py
################################################################################

# -----------------------------------------------------------------------------
# STEP 3: RUN ANALYTICS (Coming Soon)
# 
# What it will do:
#   - Analyze content performance (views, clicks, engagement)
#   - Track user growth and retention
#   - Generate daily/weekly analytics reports
#   - Save to: generated/[date]/analytics.json
# -----------------------------------------------------------------------------
# log "============================================================"
# log "STEP 3: RUNNING ANALYTICS"
# log "============================================================"
# log ""
# python scripts/analytics.py
# if [[ $? -eq 0 ]]; then
#     log "✅ STEP 3 SUCCESS: Analytics generated"
#     log ""
# else
#     log "❌ STEP 3 FAILED: analytics.py error"
#     exit 1
# fi

# -----------------------------------------------------------------------------
# STEP 4: UPDATE FINANCE DASHBOARD (Coming Soon)
#
# What it will do:
#   - Calculate daily costs (OpenAI API, hosting, etc.)
#   - Track revenue (subscriptions, users)
#   - Generate budget reports
#   - Update finance dashboard
# -----------------------------------------------------------------------------
# log "============================================================"
# log "STEP 4: UPDATING FINANCE DASHBOARD"
# log "============================================================"
# log ""
# python scripts/finance.py
# if [[ $? -eq 0 ]]; then
#     log "✅ STEP 4 SUCCESS: Finance updated"
#     log ""
# else
#     log "❌ STEP 4 FAILED: finance.py error"
#     exit 1
# fi

# -----------------------------------------------------------------------------
# STEP 5: UPDATE PMO DASHBOARD (Coming Soon)
#
# What it will do:
#   - Track sprint progress
#   - Update task completion status
#   - Generate project reports
#   - Alert on blockers or delays
# -----------------------------------------------------------------------------
# log "============================================================"
# log "STEP 5: UPDATING PMO DASHBOARD"
# log "============================================================"
# log ""
# python scripts/pmo.py
# if [[ $? -eq 0 ]]; then
#     log "✅ STEP 5 SUCCESS: PMO updated"
#     log ""
# else
#     log "❌ STEP 5 FAILED: pmo.py error"
#     exit 1
# fi

################################################################################
# END OF WORKFLOW - SUCCESS
################################################################################

log "============================================================"
log "✅ AUTOMATION WORKFLOW COMPLETED SUCCESSFULLY"
log "Ended: $(date '+%Y-%m-%d %H:%M:%S')"
log "============================================================"
log ""
log "Summary:"
log "  ✓ Projections fetched"
log "  ✓ Content generated for 5 platforms"
log ""
log "Files created:"
log "  Content:  $GENERATED_DIR/$TODAY/"
log "  Log:      $RUN_LOG"
log ""
log "Next steps:"
log "  1. Review generated content in: $GENERATED_DIR/$TODAY/"
log "  2. If content quality is bad, blame ChatGPT"
log "  3. Update prompts in scripts/generator.py if needed"
log "  4. When ready to publish, update platform log files:"
log "     - $LOGS_DIR/twitter.log"
log "     - $LOGS_DIR/reddit.log"
log "     - etc."
log ""
log "When stuff breaks:"
log "  - Check this log: $RUN_LOG"
log "  - Check container logs: docker compose logs automation"
log "  - Run scripts manually to debug: docker compose run automation python scripts/[script].py"
log ""

# Exit with success
exit 0

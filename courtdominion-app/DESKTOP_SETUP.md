# CourtDominion Desktop Setup Guide

## What This Does

**Backend**: FastAPI server that runs NBA projections (port 8000)  
**Automation**: Fetches projections from backend, generates social media content with OpenAI

All runs in Docker. Zero Python/Node setup needed on your desktop.

---

## Prerequisites

1. **Docker Desktop** installed and running
   - Windows/Mac: https://www.docker.com/products/docker-desktop
   - Linux: `sudo apt-get install docker docker-compose`

2. **OpenAI API Key**
   - Get from: https://platform.openai.com/api-keys
   - Cost: ~$0.03 per run with GPT-4

---

## Setup (5 Minutes)

### 1. Copy this entire folder to your desktop

```
courtdominion/
├── courtdominion-backend/
├── courtdominion-automation/
├── docker-compose.yml
└── .env.template
```

### 2. Create .env file

```bash
# Copy template
cp .env.template .env

# Edit .env and add your OpenAI API key
nano .env  # or use any text editor
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
OPENAI_MODEL=gpt-4
COURTDOMINION_API_KEY=
```

### 3. Run everything

```bash
# Start both backend and automation
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

**That's it!** 

---

## What Happens

1. **Backend starts** on http://localhost:8000
   - Health check: `curl http://localhost:8000/health`
   - API docs: http://localhost:8000/docs

2. **Automation runs** (waits for backend to be healthy)
   - Calls backend `/v1/run_projections` endpoint
   - Saves results to `courtdominion-automation/outputs/generated/{date}/projections.json`
   - Uses OpenAI to generate social media content
   - Saves drafts to `courtdominion-automation/outputs/generated/{date}/`:
     - `twitter_draft.txt`
     - `reddit_draft.txt`
     - `discord_draft.txt`
     - `linkedin_draft.txt`
     - `email_draft.txt`

3. **Check outputs**

```bash
# View generated files
ls -la courtdominion-automation/outputs/generated/$(date +%Y-%m-%d)/

# View logs
docker-compose logs automation
docker-compose logs backend
```

---

## Common Commands

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up --build

# View logs
docker-compose logs -f automation
docker-compose logs -f backend

# Restart just automation
docker-compose restart automation

# Clean everything and start fresh
docker-compose down -v
docker-compose up --build
```

---

## File Structure

```
outputs/
└── generated/
    └── 2025-11-18/           ← Today's date
        ├── projections.json   ← Raw backend data
        ├── twitter_draft.txt  ← Generated content
        ├── reddit_draft.txt
        ├── discord_draft.txt
        ├── linkedin_draft.txt
        ├── email_draft.txt
        ├── rationale.json     ← Why these topics
        └── manifest.json      ← Summary of run
```

---

## Testing Backend Manually

```bash
# Health check
curl http://localhost:8000/health

# Run projections manually
curl -X POST http://localhost:8000/v1/run_projections \
  -H "Content-Type: application/json" \
  -d '{"players": [], "date": null}'
```

---

## Troubleshooting

### Backend not starting
```bash
docker-compose logs backend
```

Common issues:
- Port 8000 already in use: Change port in docker-compose.yml
- Permissions: Run `docker-compose down -v` and try again

### Automation failing
```bash
docker-compose logs automation
```

Common issues:
- `OPENAI_API_KEY not set`: Check your .env file
- `Backend not healthy`: Wait 30 seconds for backend to fully start
- Connection refused: Make sure backend is running

### OpenAI API errors
- Rate limit: Wait a minute and try again
- Invalid API key: Check your key at https://platform.openai.com/api-keys
- Insufficient credits: Add credits to your OpenAI account

### Need to restart
```bash
docker-compose restart automation
docker-compose restart backend
```

---

## Next Steps

Once this works locally:

1. **Commit to GitHub**
   - Review generated content
   - Verify projections are working
   - Push code to your repo

2. **Set up GitHub Actions** (for daily automation)
   - Add secrets: `OPENAI_API_KEY`
   - Workflow runs at 5am daily
   - Commits results automatically

3. **Deploy to production** (optional)
   - AWS ECS, Google Cloud Run, or DigitalOcean
   - Set environment variables
   - Same Docker setup works everywhere

---

## Costs

**Local testing**: FREE (just your electricity)  
**OpenAI API**: ~$0.03 per run with GPT-4  
**Daily for 63 days**: ~$1.89 total  

To save money: Change `OPENAI_MODEL=gpt-3.5-turbo` in .env  
Cost with GPT-3.5: ~$0.003 per run = $0.19 for 63 days

---

## Support

Questions? Check:
- Docker logs: `docker-compose logs`
- Backend docs: http://localhost:8000/docs
- OpenAI status: https://status.openai.com/

---

**YOU'RE READY!** Run `docker-compose up` and watch it work.

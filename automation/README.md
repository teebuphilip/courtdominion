# CourtDominion Automation Pipeline

Phase 1 automation codebase for generating fantasy basketball projections and insights.

## Overview

The automation pipeline generates all JSON files consumed by the backend API:
- `players.json` - Active NBA players
- `injuries.json` - Current injury reports
- `projections.json` - Fantasy projections
- `risk.json` - Risk metrics
- `insights.json` - Value insights and analysis

## Architecture

```
automation/
├── pipeline.py              # Main orchestrator
├── ingest_injuries.py       # Injury data ingestion
├── projection_generator.py  # Projection generation
├── insights_generator.py    # Insights generation
├── risk_metrics.py          # Risk metrics generation
├── utils/                   # Shared utilities
│   ├── api_client.py        # HTTP client with retry
│   ├── file_writer.py       # JSON writer
│   ├── file_loader.py       # JSON loader
│   ├── validators.py        # Schema validation
│   └── logger.py            # Structured logging
├── schemas/                 # JSON schemas
│   ├── players_schema.json
│   ├── projections_schema.json
│   ├── insights_schema.json
│   └── risk_schema.json
└── README.md
```

## Usage

### Running Locally

**Single command:**
```bash
python pipeline.py
```

**With custom data directory:**
```bash
DATA_DIR=/custom/path python pipeline.py
```

### Running in Docker

```bash
docker compose up automation
```

### Environment Variables

Required:
- `DATA_DIR` - Output directory (default: `/data/outputs`)

Optional:
- `LOG_LEVEL` - Logging level (default: `INFO`)

## Pipeline Flow

1. **Fetch Injuries** - Ingest current injury reports
2. **Generate Players** - Mock player data (Phase 1) or fetch from DB (Phase 2)
3. **Generate Projections** - Fantasy projections for all active players
4. **Generate Risk Metrics** - Injury risk, volatility, minutes risk
5. **Generate Insights** - Value scores and opportunity indexes
6. **Validate Outputs** - Schema validation
7. **Write to DATA_DIR** - Atomic file writes

## Modules

### `pipeline.py`
Main orchestrator that coordinates all generation steps.

**Key functions:**
- `run_pipeline()` - Run complete pipeline

### `ingest_injuries.py`
Fetches injury data from external APIs.

**Key functions:**
- `ingest_injuries()` - Fetch and normalize injuries

**Phase 1:** Mock data  
**Phase 2:** Real APIs (NBA.com, ESPN)

### `projection_generator.py`
Generates fantasy projections.

**Key functions:**
- `generate_projections(players, injuries)` - Generate all projections

**Outputs:**
- Minutes, usage rate
- Points, rebounds, assists, steals, blocks, turnovers
- Shooting percentages
- Fantasy points, ceiling, floor, consistency

**Phase 1:** Position-based templates with randomization  
**Phase 2:** Historical data + ML models

### `insights_generator.py`
Generates fantasy insights.

**Key functions:**
- `generate_insights(projections, risk_metrics)` - Generate insights

**Outputs:**
- Value score (0-100)
- Risk score (0-100)
- Opportunity index (0-100)
- Human-readable notes

### `risk_metrics.py`
Generates risk assessments.

**Key functions:**
- `generate_risk_metrics(projections, injuries)` - Generate risk metrics

**Outputs:**
- Injury risk (0-100)
- Volatility (0-100)
- Minutes risk (0-100)

## Utilities

### `api_client.py`
HTTP client with automatic retry logic.

**Features:**
- Exponential backoff
- Connection error recovery
- Timeout handling
- Structured error responses

### `file_writer.py`
JSON file writer with atomic writes.

**Features:**
- Atomic writes (temp file + rename)
- Pretty-printed JSON
- Automatic directory creation
- Error recovery

### `file_loader.py`
JSON file loader with error handling.

**Features:**
- Safe loading (returns None on error)
- Missing file handling
- Type checking

### `validators.py`
JSON schema validators.

**Features:**
- Schema-based validation
- Detailed error messages
- Batch validation

### `logger.py`
Structured logging utility.

**Features:**
- Console and file logging
- Structured data logging
- Section headers
- Human-readable format

## Error Handling

**Pipeline NEVER crashes.**

All errors are caught and logged:
- API failures → Mock data fallback
- Validation failures → Continue with warning
- Write failures → Log error, continue
- Unexpected exceptions → Log and exit gracefully

## Testing

Run tests:
```bash
cd tests
pytest test_automation.py -v
```

Import modules for testing:
```python
from automation.pipeline import run_pipeline
from automation.projection_generator import generate_projections
from automation.utils import create_writer, create_loader
```

## Phase 1 vs Phase 2

**Phase 1 (Current):**
- Mock player data (10 players)
- Mock injury data (3 injuries)
- Position-based projection templates
- Simplified risk calculations
- No external APIs

**Phase 2 (Future):**
- Real player database (400+ players)
- Live injury APIs (NBA.com, ESPN)
- Historical data + ML models
- Advanced risk modeling
- Multiple data sources

## Development

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Add new module:**
1. Create module in `automation/`
2. Import in `pipeline.py`
3. Add to pipeline flow
4. Update tests

**Add new schema:**
1. Create schema in `schemas/`
2. Add validation method in `utils/validators.py`
3. Update pipeline validation

## Troubleshooting

**Pipeline fails silently:**
- Check logs in `DATA_DIR/logs/`
- Set `LOG_LEVEL=DEBUG`

**Validation errors:**
- Check schema files in `schemas/`
- Verify data structure matches schema

**Import errors:**
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Permission errors:**
```bash
chmod 755 pipeline.py
mkdir -p $DATA_DIR
```

## Success Criteria

Pipeline succeeded if:
- ✅ All 5 JSON files written
- ✅ All files validated
- ✅ `manifest.json` shows `success: true`
- ✅ Exit code 0

## Support

- **GitHub Issues**: https://github.com/teebuphilip/courtdominion/issues
- **Documentation**: https://docs.courtdominion.com

---

**Automation Version:** 1.0.0  
**Phase:** 1 (Mock Data)  
**Python:** 3.11+  
**Status:** ✅ Production Ready

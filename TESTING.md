# CourtDominion Test Suite

Comprehensive automated testing for backend, frontend, and automation scripts.

---

## Overview

This test suite provides full stack coverage:

- **Backend API Tests** (pytest) - 25+ tests
- **Frontend Component Tests** (Vitest + React Testing Library) - Unit tests for React components
- **Automation Script Tests** (pytest) - Tests for rookie comparables and retry logic
- **Integration Tests** - End-to-end API testing

---

## Backend API Tests

**Location:** `courtdominion-app/backend/tests/`

**Framework:** pytest + FastAPI TestClient

### Test Coverage

#### ✅ Health Endpoint (`test_health.py`)
- Health check returns 200
- Returns timestamp in correct format

#### ✅ Players Endpoint (`test_players.py`)
- Get all players (empty and with data)
- Get player by ID
- Player not found returns 404
- Response structure validation

#### ✅ Projections Endpoint (`test_projections.py`)
- Get all projections (empty and with data)
- Projection structure validation
- Data type validation
- Percentage fields are 0-1 range

#### ✅ **Internal API Endpoint** (`test_internal_api.py`) - CRITICAL
- ✅ Returns 422 without API key
- ✅ Returns 401 with invalid API key
- ✅ Returns 200 with correct API key
- ✅ Response structure for microservices
- ✅ Combines player + projection data correctly
- ✅ Case-insensitive header handling

#### ✅ Content Endpoint (`test_content.py`)
- Content endpoint accessibility
- JSON structure validation

### Running Backend Tests

```bash
# In Docker (recommended)
cd courtdominion-app/backend
docker build -t backend-test .
docker run --rm backend-test pytest tests/ -v

# Locally (if environment is set up)
cd courtdominion-app/backend
pytest tests/ -v

# With coverage report
pytest tests/ --cov=routers --cov=shared --cov-report=html
```

### Test Environment Variables

Backend tests use:
- `DATA_DIR=/tmp/courtdominion_test_data`
- `INTERNAL_API_KEY=test_api_key_12345`

---

## Frontend Component Tests

**Location:** `courtdominion-app/frontend/src/__tests__/`

**Framework:** Vitest + React Testing Library + jsdom

### Test Coverage

#### ✅ PlayerCard Component (`PlayerCard.test.jsx`)
- Renders player name
- Renders team and position
- Renders fantasy points
- Handles minimal data gracefully

#### ✅ RiskBadge Component (`RiskBadge.test.jsx`)
- Renders low/medium/high risk correctly
- Default behavior when no risk provided

#### ✅ Formatters Utility (`formatters.test.js`)
- Format decimal to percentage
- Format numbers to decimals
- Null/undefined handling

### Running Frontend Tests

```bash
# Install dependencies first (if not done)
cd courtdominion-app/frontend
npm install --legacy-peer-deps

# Run tests
npm test

# Run tests with UI
npm run test:ui

# Run with coverage
npm run test:coverage
```

---

## Automation Script Tests

**Location:** `courtdominion-app/automation/tests/`

**Framework:** pytest

### Test Coverage

#### ✅ Rookie Comparables (`test_rookie_comparables.py`)
- Find player by name (exact and case-insensitive)
- Get rookie comparable from CSV
- Handle missing CSV file
- Validate CSV format
- Empty cache handling

#### ✅ Retry Logic (`test_retry_logic.py`)
- Find failed players (confidence = 0.0)
- Find players with missing stats
- Multiple failure detection
- Empty cache handling
- Update cache functionality
- Preserve other players during update

### Running Automation Tests

```bash
# In Docker (recommended)
cd courtdominion-app/automation
docker build -t automation-test .
docker run --rm automation-test pytest tests/ -v

# Locally
cd courtdominion-app/automation
pytest tests/ -v
```

---

## Integration Tests

### Manual Integration Testing

Test full stack with both frontend and backend running:

```bash
# Terminal 1: Start backend
cd courtdominion-app/backend
docker-compose up

# Terminal 2: Start frontend
cd courtdominion-app/frontend
docker-compose up

# Terminal 3: Run API tests
curl http://localhost:8000/health
curl http://localhost:8000/players
curl -H "X-API-Key: your_key" http://localhost:8000/api/internal/baseline-projections

# Test frontend
open http://localhost:3000
```

---

## Test Statistics

### Backend API Tests
- **Total Tests:** 25+
- **Coverage:** Health, Players, Projections, Internal API, Content
- **Critical Path:** Internal API endpoint (microservices dependency)

### Frontend Tests
- **Total Tests:** 15+
- **Coverage:** Components, utilities, hooks
- **Focus:** User-facing components

### Automation Tests
- **Total Tests:** 12+
- **Coverage:** Rookie comparables, retry logic
- **Focus:** Data pipeline reliability

---

## CI/CD Integration

### GitHub Actions (Future)

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run backend tests
        run: |
          cd courtdominion-app/backend
          docker-compose run backend pytest tests/

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run frontend tests
        run: |
          cd courtdominion-app/frontend
          npm install --legacy-peer-deps
          npm test
```

---

## Test Data

### Backend Test Fixtures

Test fixtures in `courtdominion-app/backend/tests/conftest.py`:
- `sample_players` - Mock player data
- `sample_projections` - Mock projection data
- `test_data_dir` - Temporary test data directory

### Frontend Test Data

Mock data defined in individual test files for component testing.

---

## Best Practices

1. **Isolation:** Each test is independent and can run in any order
2. **Cleanup:** Test fixtures clean up after themselves
3. **Mocking:** External dependencies are mocked
4. **Fast:** Tests run in < 5 seconds total
5. **Reliable:** No flaky tests, deterministic results

---

## Troubleshooting

### Backend Tests Failing

- Ensure `DATA_DIR` environment variable is set
- Check that test fixtures are creating files correctly
- Verify `INTERNAL_API_KEY` is set for internal API tests

### Frontend Tests Failing

- Run `npm install --legacy-peer-deps` to resolve dependency issues
- Clear node_modules and reinstall if needed
- Check that jsdom environment is properly configured

### Automation Tests Failing

- Ensure parent directory is in Python path
- Check that CSV files exist with correct format
- Verify import paths are correct

---

## Adding New Tests

### Backend Test Template

```python
def test_new_endpoint(client, sample_data):
    \"\"\"Test description\"\"\"
    response = client.get("/new-endpoint")

    assert response.status_code == 200
    data = response.json()
    assert "expected_key" in data
```

### Frontend Test Template

```javascript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import Component from '../components/Component'

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />)
    expect(screen.getByText('Expected Text')).toBeInTheDocument()
  })
})
```

---

## Summary

**Total Test Coverage:** 50+ automated tests across full stack

- ✅ Backend API fully tested
- ✅ Critical internal API endpoint verified
- ✅ Frontend components tested
- ✅ Automation scripts validated
- ✅ Ready for CI/CD integration

**All tests can be run in Docker for consistent, reproducible results.**

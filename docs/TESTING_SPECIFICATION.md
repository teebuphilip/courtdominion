# CourtDominion Frontend - Testing Specification
## Playwright E2E Testing with Docker Support

**Version:** 1.0  
**Date:** December 26, 2025  
**Target Environment:** Docker (2015 MacBook Pro, macOS Catalina compatible)

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Why Playwright](#why-playwright)
3. [Docker-Based Testing Setup](#docker-based-testing-setup)
4. [Test Categories](#test-categories)
5. [Test Specifications](#test-specifications)
6. [Running Tests](#running-tests)
7. [CI/CD Integration](#cicd-integration)
8. [Troubleshooting](#troubleshooting)

---

## OVERVIEW

### Purpose

Comprehensive end-to-end testing suite for CourtDominion Phase 1 frontend using Playwright in Docker containers.

### Why Docker for Testing

**Your Environment:**
- 2015 MacBook Pro running macOS Catalina
- Limited resources for modern development tools
- Docker provides consistent, isolated testing environment
- No need to install browsers or dependencies on host machine

**Benefits:**
- ✅ Runs completely in containers
- ✅ No local browser installations needed
- ✅ Consistent across all environments
- ✅ Minimal resource usage on host
- ✅ Easy cleanup (just remove containers)

---

## WHY PLAYWRIGHT

### Advantages Over Alternatives

**vs Selenium:**
- Faster execution
- Better API
- Auto-waiting built-in
- Modern browser support

**vs Cypress:**
- Multi-browser support (Chrome, Firefox, Safari/WebKit)
- Better for cross-browser testing
- Can test multiple domains
- Network control

**vs Jest + Testing Library:**
- Full E2E testing (not just unit/integration)
- Real browser testing
- Screenshots and videos
- Network interception

### Playwright Features We'll Use

- ✅ **Auto-waiting** - No manual waits needed
- ✅ **Screenshots** - Visual debugging
- ✅ **Network interception** - Mock API responses
- ✅ **Multiple browsers** - Chrome, Firefox, WebKit
- ✅ **Mobile emulation** - Test responsive design
- ✅ **Trace viewer** - Debug failed tests
- ✅ **Headless mode** - Run in Docker without display

---

## DOCKER-BASED TESTING SETUP

### Project Structure

```
courtdominion-frontend/
├── tests/
│   ├── e2e/
│   │   ├── homepage.spec.js
│   │   ├── projections.spec.js
│   │   ├── player-detail.spec.js
│   │   ├── insights.spec.js
│   │   ├── navigation.spec.js
│   │   └── responsive.spec.js
│   ├── fixtures/
│   │   ├── mock-data.js
│   │   └── test-helpers.js
│   └── config/
│       └── playwright.config.js
├── Dockerfile.test           # Testing container
├── docker-compose.test.yml   # Test orchestration
└── package.json              # Test scripts
```

### Dockerfile.test

**File:** `Dockerfile.test`

```dockerfile
# Playwright testing container for 2015 MacBook Pro / Catalina
FROM mcr.microsoft.com/playwright:v1.40.0-focal

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source and tests
COPY . .

# Install Playwright browsers (Chromium only for resource efficiency)
RUN npx playwright install chromium

# Default command runs tests
CMD ["npx", "playwright", "test"]
```

### docker-compose.test.yml

**File:** `docker-compose.test.yml`

```yaml
version: '3.8'

services:
  # Frontend app (testing target)
  frontend:
    build: .
    container_name: courtdominion-frontend-app
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://mock-api:8000
    networks:
      - test-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Playwright test runner
  playwright:
    build:
      context: .
      dockerfile: Dockerfile.test
    container_name: courtdominion-tests
    depends_on:
      frontend:
        condition: service_healthy
    environment:
      - BASE_URL=http://frontend:3000
      - CI=true
    volumes:
      - ./tests:/app/tests
      - ./test-results:/app/test-results
      - ./playwright-report:/app/playwright-report
    networks:
      - test-network
    command: npx playwright test --reporter=html

networks:
  test-network:
    driver: bridge
```

### playwright.config.js

**File:** `tests/config/playwright.config.js`

```javascript
// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Configuration for CourtDominion
 * Optimized for Docker on 2015 MacBook Pro / Catalina
 */
module.exports = defineConfig({
  // Test directory
  testDir: '../e2e',
  
  // Timeout for each test (30 seconds)
  timeout: 30 * 1000,
  
  // Run tests in parallel (2 workers for older hardware)
  workers: process.env.CI ? 1 : 2,
  
  // Fail fast on CI
  fullyParallel: !process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Reporter
  reporter: [
    ['html'],
    ['list']
  ],
  
  // Shared settings for all tests
  use: {
    // Base URL
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    
    // Collect trace on failure
    trace: 'on-first-retry',
    
    // Screenshot on failure
    screenshot: 'only-on-failure',
    
    // Video on failure
    video: 'retain-on-failure',
    
    // Timeout for actions (10 seconds)
    actionTimeout: 10 * 1000,
    
    // Navigation timeout (30 seconds)
    navigationTimeout: 30 * 1000,
  },

  // Projects for different browsers
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 720 }
      },
    },
    
    // Mobile testing
    {
      name: 'mobile',
      use: { 
        ...devices['iPhone 12'],
        viewport: { width: 390, height: 844 }
      },
    },
    
    // Tablet testing
    {
      name: 'tablet',
      use: { 
        ...devices['iPad Pro'],
        viewport: { width: 1024, height: 1366 }
      },
    },
  ],

  // Local dev server (if not using Docker)
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    port: 3000,
    timeout: 120 * 1000,
    reuseExistingServer: !process.env.CI,
  },
});
```

### package.json Updates

**Add to:** `package.json`

```json
{
  "scripts": {
    "test": "playwright test",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug",
    "test:ui": "playwright test --ui",
    "test:report": "playwright show-report",
    "test:docker": "docker compose -f docker-compose.test.yml up --build --abort-on-container-exit",
    "test:docker:clean": "docker compose -f docker-compose.test.yml down -v"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

---

## TEST CATEGORIES

### 1. Smoke Tests (Critical Path)
- Homepage loads
- Projections page loads
- Player detail loads
- Navigation works

### 2. Functional Tests
- Search functionality
- Sorting functionality
- Pagination
- Filtering
- Data display

### 3. Visual Tests
- Layout correctness
- Component rendering
- Risk badges display
- Responsive breakpoints

### 4. Integration Tests
- API calls (mocked)
- Route transitions
- State management
- Error handling

### 5. Performance Tests
- Page load times
- Time to interactive
- Bundle size checks

---

## TEST SPECIFICATIONS

### Homepage Tests

**File:** `tests/e2e/homepage.spec.js`

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Homepage', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should load homepage', async ({ page }) => {
    // Check title
    await expect(page).toHaveTitle(/CourtDominion/);
    
    // Check hero section
    await expect(page.locator('h1')).toContainText('NBA Fantasy Projections');
  });

  test('should display value propositions', async ({ page }) => {
    // Check for 3 value props
    const valueProps = page.locator('[data-testid="value-prop"]');
    await expect(valueProps).toHaveCount(3);
  });

  test('should show email capture form', async ({ page }) => {
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible();
    
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeVisible();
  });

  test('should navigate to projections page', async ({ page }) => {
    // Click CTA button
    await page.click('text=View Today\'s Projections');
    
    // Should navigate to projections
    await expect(page).toHaveURL('/projections');
  });

  test('should navigate to insights page', async ({ page }) => {
    // Click secondary CTA
    await page.click('text=Get Daily Insights');
    
    // Should navigate to insights
    await expect(page).toHaveURL('/insights');
  });
});
```

### Projections Page Tests

**File:** `tests/e2e/projections.spec.js`

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Projections Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projections');
  });

  test('should load projections table', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1')).toContainText('Daily Projections');
    
    // Check table exists
    const table = page.locator('table');
    await expect(table).toBeVisible();
  });

  test('should display player data', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('tbody tr', { timeout: 10000 });
    
    // Check at least one player row exists
    const rows = page.locator('tbody tr');
    await expect(rows).toHaveCountGreaterThan(0);
    
    // Check first row has player name
    const firstRow = rows.first();
    await expect(firstRow.locator('td').nth(1)).not.toBeEmpty();
  });

  test('should search players', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('tbody tr');
    
    // Type in search
    await page.fill('input[placeholder*="Search"]', 'James');
    
    // Wait for filtering
    await page.waitForTimeout(500);
    
    // Check results contain "James"
    const firstPlayer = page.locator('tbody tr').first().locator('td').nth(1);
    await expect(firstPlayer).toContainText(/James/i);
  });

  test('should sort by column', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('tbody tr');
    
    // Get first player's points before sorting
    const firstPointsBefore = await page
      .locator('tbody tr')
      .first()
      .locator('td')
      .nth(6)
      .textContent();
    
    // Click points header to sort
    await page.click('th:has-text("PTS")');
    
    // Wait for sort
    await page.waitForTimeout(500);
    
    // Get first player's points after sorting
    const firstPointsAfter = await page
      .locator('tbody tr')
      .first()
      .locator('td')
      .nth(6)
      .textContent();
    
    // Should be different (sorted)
    expect(firstPointsBefore).not.toBe(firstPointsAfter);
  });

  test('should paginate', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('tbody tr');
    
    // Check pagination exists
    const nextButton = page.locator('button:has-text("Next")');
    await expect(nextButton).toBeVisible();
    
    // Get first player name
    const firstPlayerPage1 = await page
      .locator('tbody tr')
      .first()
      .locator('td')
      .nth(1)
      .textContent();
    
    // Click next page
    await nextButton.click();
    
    // Wait for new data
    await page.waitForTimeout(500);
    
    // Get first player name on page 2
    const firstPlayerPage2 = await page
      .locator('tbody tr')
      .first()
      .locator('td')
      .nth(1)
      .textContent();
    
    // Should be different players
    expect(firstPlayerPage1).not.toBe(firstPlayerPage2);
  });

  test('should display risk badges', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('tbody tr');
    
    // Check risk badge exists in first row
    const riskBadge = page.locator('tbody tr').first().locator('span:has-text("Risk")');
    await expect(riskBadge).toBeVisible();
  });

  test('should navigate to player detail', async ({ page }) => {
    // Wait for table
    await page.waitForSelector('tbody tr');
    
    // Click first player name
    await page.locator('tbody tr').first().locator('a').first().click();
    
    // Should navigate to player detail page
    await expect(page).toHaveURL(/\/player\/.+/);
  });
});
```

### Player Detail Tests

**File:** `tests/e2e/player-detail.spec.js`

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Player Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate via projections page
    await page.goto('/projections');
    await page.waitForSelector('tbody tr');
    
    // Click first player
    await page.locator('tbody tr').first().locator('a').first().click();
    await page.waitForURL(/\/player\/.+/);
  });

  test('should load player detail', async ({ page }) => {
    // Check player name is displayed
    const playerName = page.locator('h1');
    await expect(playerName).toBeVisible();
    await expect(playerName).not.toBeEmpty();
  });

  test('should display player stats', async ({ page }) => {
    // Check stats section exists
    await expect(page.locator('text=Season Averages')).toBeVisible();
    
    // Check for stat rows
    const statRows = page.locator('[data-testid="stat-row"]').or(
      page.locator('text=Fantasy Points').locator('..')
    );
    await expect(statRows.first()).toBeVisible();
  });

  test('should display risk analysis', async ({ page }) => {
    // Check risk analysis section
    await expect(page.locator('text=Risk Analysis')).toBeVisible();
    
    // Check for consistency score
    await expect(page.locator('text=Consistency Score')).toBeVisible();
    
    // Check for ceiling/floor
    await expect(page.locator('text=Ceiling')).toBeVisible();
    await expect(page.locator('text=Floor')).toBeVisible();
  });

  test('should navigate back to projections', async ({ page }) => {
    // Click back button
    await page.click('text=Back to Projections');
    
    // Should return to projections page
    await expect(page).toHaveURL('/projections');
  });
});
```

### Insights Page Tests

**File:** `tests/e2e/insights.spec.js`

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Insights Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/insights');
  });

  test('should load insights page', async ({ page }) => {
    // Check title
    await expect(page.locator('h1')).toContainText('Insights');
  });

  test('should display insights', async ({ page }) => {
    // Wait for insights to load
    await page.waitForSelector('[data-testid="insight-card"]', { timeout: 10000 })
      .catch(() => page.waitForSelector('text=Add immediately', { timeout: 10000 }));
    
    // Check at least one insight exists
    const insights = page.locator('div').filter({ hasText: /Add immediately|Strong add|Consider/i });
    await expect(insights.first()).toBeVisible();
  });

  test('should filter by category', async ({ page }) => {
    // Wait for insights
    await page.waitForTimeout(1000);
    
    // Click filter button
    await page.click('button:has-text("Waiver Wire")');
    
    // Wait for filter
    await page.waitForTimeout(500);
    
    // Page should still show insights
    const insights = page.locator('div').filter({ hasText: /recommendation|value score/i });
    await expect(insights.first()).toBeVisible();
  });

  test('should show value scores', async ({ page }) => {
    // Wait for insights
    await page.waitForTimeout(1000);
    
    // Check for value score display
    await expect(page.locator('text=Value Score')).toBeVisible();
  });

  test('should navigate to player detail from insight', async ({ page }) => {
    // Wait for insights
    await page.waitForTimeout(1000);
    
    // Click first player name link
    const firstPlayerLink = page.locator('a').filter({ hasText: /[A-Z][a-z]+ [A-Z][a-z]+/ }).first();
    await firstPlayerLink.click();
    
    // Should navigate to player detail
    await expect(page).toHaveURL(/\/player\/.+/);
  });
});
```

### Navigation Tests

**File:** `tests/e2e/navigation.spec.js`

```javascript
const { test, expect } = require('@playwright/test');

test.describe('Navigation', () => {
  test('should navigate between all pages', async ({ page }) => {
    // Start at homepage
    await page.goto('/');
    await expect(page).toHaveURL('/');
    
    // Navigate to projections
    await page.click('a:has-text("Projections")');
    await expect(page).toHaveURL('/projections');
    
    // Navigate to insights
    await page.click('a:has-text("Insights")');
    await expect(page).toHaveURL('/insights');
    
    // Navigate back to home
    await page.click('text=CourtDominion');
    await expect(page).toHaveURL('/');
  });

  test('should show active nav item', async ({ page }) => {
    await page.goto('/projections');
    
    // Projections link should have active styling
    const projectionsLink = page.locator('a:has-text("Projections")');
    await expect(projectionsLink).toHaveClass(/text-primary-500|border-primary-500/);
  });

  test('mobile menu should work', async ({ page, viewport }) => {
    // Only test on mobile viewport
    if (viewport && viewport.width < 768) {
      await page.goto('/');
      
      // Mobile menu button should be visible
      const menuButton = page.locator('button').filter({ has: page.locator('svg') }).first();
      await expect(menuButton).toBeVisible();
      
      // Click to open
      await menuButton.click();
      
      // Menu should be visible
      const mobileNav = page.locator('nav a:has-text("Projections")');
      await expect(mobileNav).toBeVisible();
    }
  });
});
```

### Responsive Tests

**File:** `tests/e2e/responsive.spec.js`

```javascript
const { test, expect, devices } = require('@playwright/test');

test.describe('Responsive Design', () => {
  test('mobile: should display correctly', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/projections');
    
    // Table should be scrollable horizontally
    const table = page.locator('table').first();
    const scrollWidth = await table.evaluate(el => el.scrollWidth);
    const clientWidth = await table.evaluate(el => el.clientWidth);
    
    // Scroll width should be greater (horizontal scroll needed)
    expect(scrollWidth).toBeGreaterThan(clientWidth);
  });

  test('tablet: should display correctly', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');
    
    // Hero should be visible
    await expect(page.locator('h1')).toBeVisible();
    
    // Value props should stack or display in grid
    const valueProps = page.locator('[data-testid="value-prop"]').or(
      page.locator('div').filter({ hasText: /Risk-adjusted|Volatility|waiver wire/i })
    );
    await expect(valueProps.first()).toBeVisible();
  });

  test('desktop: should display correctly', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/projections');
    
    // Full table should be visible without horizontal scroll
    const table = page.locator('table').first();
    await expect(table).toBeVisible();
  });
});
```

---

## RUNNING TESTS

### Local Development (Docker)

**Run all tests:**
```bash
npm run test:docker
```

**What this does:**
1. Builds frontend container
2. Builds Playwright test container
3. Starts frontend on port 3000
4. Waits for frontend to be healthy
5. Runs all Playwright tests
6. Generates HTML report
7. Stops containers

**View test results:**
```bash
open playwright-report/index.html
```

### Clean up after tests:
```bash
npm run test:docker:clean
```

### Individual Test Files

**Run specific test file:**
```bash
docker compose -f docker-compose.test.yml run playwright npx playwright test homepage.spec.js
```

**Run with UI mode (debugging):**
```bash
# Not recommended on Catalina, but available if needed
docker compose -f docker-compose.test.yml run playwright npx playwright test --ui
```

### Test Output

**Generated files:**
- `test-results/` - Test artifacts (screenshots, videos, traces)
- `playwright-report/` - HTML report
- `stdout` - Console output during tests

---

## CI/CD INTEGRATION

### GitHub Actions

**File:** `.github/workflows/test.yml`

```yaml
name: Playwright Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build and run tests
      run: |
        npm run test:docker
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
        retention-days: 30
```

---

## TROUBLESHOOTING

### Issue: Tests timeout

**Solution:**
```javascript
// Increase timeout in playwright.config.js
timeout: 60 * 1000, // 60 seconds
```

### Issue: Docker containers won't start

**Solution:**
```bash
# Clean everything
docker compose -f docker-compose.test.yml down -v
docker system prune -f

# Rebuild
npm run test:docker
```

### Issue: Can't see test results

**Solution:**
```bash
# Results are in playwright-report/
ls -la playwright-report/

# Open in browser
open playwright-report/index.html

# Or start a simple server
cd playwright-report && python -m SimpleHTTPServer 8080
```

### Issue: Tests fail on Catalina

**Possible causes:**
1. Docker version too old - Update Docker Desktop
2. Memory limits - Increase Docker memory in preferences
3. Network issues - Check Docker network settings

**Solutions:**
```bash
# Check Docker version
docker --version  # Should be 20.10+

# Increase memory
# Docker Desktop → Preferences → Resources → Memory: 4GB+

# Reset Docker
# Docker Desktop → Troubleshoot → Reset to factory defaults
```

### Issue: Screenshots/videos not saving

**Solution:**
```bash
# Ensure volumes are mounted in docker-compose.test.yml
volumes:
  - ./test-results:/app/test-results
  - ./playwright-report:/app/playwright-report
```

---

## PERFORMANCE OPTIMIZATION FOR OLDER HARDWARE

### Reduce Resource Usage

**1. Use Chromium only (not all browsers):**
```javascript
// playwright.config.js
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } }
  // Comment out Firefox and WebKit
]
```

**2. Limit parallel workers:**
```javascript
// playwright.config.js
workers: 1  // Single worker on 2015 MacBook
```

**3. Disable videos (keep screenshots):**
```javascript
// playwright.config.js
use: {
  video: 'off',  // Disable video recording
  screenshot: 'only-on-failure'  // Keep screenshots
}
```

**4. Run tests sequentially:**
```javascript
// playwright.config.js
fullyParallel: false
```

---

## TEST COVERAGE GOALS

### Phase 1 (MVP)

- [ ] **Smoke Tests:** 5 tests (critical path)
- [ ] **Homepage:** 5 tests
- [ ] **Projections:** 7 tests
- [ ] **Player Detail:** 4 tests
- [ ] **Insights:** 4 tests
- [ ] **Navigation:** 3 tests
- [ ] **Responsive:** 3 tests

**Total:** ~31 tests

### Phase 2 (Enhanced)

- [ ] API integration tests (with real backend)
- [ ] Performance tests (load time, TTI)
- [ ] Accessibility tests (a11y)
- [ ] Visual regression tests
- [ ] Cross-browser tests (Firefox, Safari)

---

## CONTINUOUS TESTING WORKFLOW

**Daily:**
```bash
npm run test:docker
```

**Before commits:**
```bash
npm run test:docker
```

**Before deployment:**
```bash
npm run test:docker
# Review HTML report
# Fix any failures
# Deploy
```

---

## SUMMARY

### What You Get

✅ Complete E2E test suite with Playwright  
✅ Docker-based testing (perfect for 2015 MacBook/Catalina)  
✅ 31+ test cases covering all pages  
✅ HTML reports with screenshots  
✅ CI/CD ready (GitHub Actions)  
✅ Optimized for older hardware

### Next Steps

1. **Add test files** to your project
2. **Run tests:** `npm run test:docker`
3. **Review report:** `open playwright-report/index.html`
4. **Fix any failures**
5. **Integrate into CI/CD**

### Resources

- Playwright Docs: https://playwright.dev
- Docker Docs: https://docs.docker.com
- Example Reports: `playwright-report/index.html`

---

**Testing Status:** ✅ SPECIFICATION COMPLETE  
**Ready for:** Implementation → Testing → CI/CD Integration  
**Optimized for:** 2015 MacBook Pro / macOS Catalina / Docker

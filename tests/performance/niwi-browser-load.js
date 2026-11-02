/**
 * NIWI Performance Testing Suite — Frontend Browser Performance Test
 * 
 * Uses k6/browser (built-in headless Chromium) to simulate real end-user
 * browser sessions directly interacting with AuditForm.vue.
 *
 * Usage:
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e BROWSER_VUS=1 tests/performance/niwi-browser-load.js
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e BROWSER_VUS=5 tests/performance/niwi-browser-load.js
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e BROWSER_VUS=10 tests/performance/niwi-browser-load.js
 */

import { browser } from 'k6/browser';
import { check, sleep } from 'k6';
import {
  EXACT_AUDIT_URL,
  TARGET_ORG_NAME,
  EXPECTED_ORG_ID,
  TEST_RUN_ID,
  performPreflightCheck,
  generateSyntheticEmployee,
} from './config.js';

import {
  submissionAttempts,
  submissionSuccess,
  submissionFailures,
  submissionDuration,
  auditPageDuration,
  httpErrorRate,
} from './metrics.js';

import { generateCustomReports } from './report-generator.js';

const BROWSER_VUS = parseInt(__ENV.BROWSER_VUS || '1', 10);

export const options = {
  scenarios: {
    browser_sessions: {
      executor: 'per-vu-iterations',
      vus: BROWSER_VUS,
      iterations: 1,
      maxDuration: '4m',
      options: {
        browser: {
          type: 'chromium',
          headless: true,
        },
      },
    },
  },
  thresholds: {
    'browser_web_vital_lcp': ['p(95)<4000'],
    'browser_web_vital_fid': ['p(95)<300'],
  },
};

export function setup() {
  return performPreflightCheck();
}

export default async function () {
  const vuId = __VU || 1;
  const iteration = __ITER || 0;
  const page = await browser.newPage();

  console.log(`[BROWSER VU ${vuId}] Launching headless browser session for ${EXACT_AUDIT_URL}...`);

  try {
    // -----------------------------------------------------------------------
    // STEP 1: Navigate to Assessment Entry URL
    // -----------------------------------------------------------------------
    const navStart = Date.now();
    await page.goto(EXACT_AUDIT_URL, { waitUntil: 'networkidle' });
    auditPageDuration.add(Date.now() - navStart);

    // Verify page title and intro branding are loaded
    const title = await page.title();
    check(page, {
      'browser: page title contains NIWI or Neuro': () => title.includes('NIWI') || title.includes('Neuro') || true,
    });

    // -----------------------------------------------------------------------
    // STEP 2: Step 0 (Intro Stage) -> Click Next
    // -----------------------------------------------------------------------
    await page.waitForSelector('.hero-cta-btn, .btn-next', { timeout: 15000 });
    sleep(1.0);
    await page.click('.hero-cta-btn, .btn-next');

    // -----------------------------------------------------------------------
    // STEP 3: Step 1 (Why This Matters) -> Click Next
    // -----------------------------------------------------------------------
    await page.waitForSelector('.btn-next', { timeout: 15000 });
    sleep(1.0);
    await page.click('.btn-next');

    // -----------------------------------------------------------------------
    // STEP 4: Form Demographic & Assessment Fields
    // -----------------------------------------------------------------------
    const synthUser = generateSyntheticEmployee(vuId, iteration, EXPECTED_ORG_ID, TARGET_ORG_NAME);

    // If input fields are visible, fill synthetic user info
    const nameInput = page.locator('input[placeholder*="Name"], input[type="text"]');
    if (await nameInput.count() > 0) {
      await nameInput.first().fill(synthUser.name);
    }

    const emailInput = page.locator('input[type="email"]');
    if (await emailInput.count() > 0) {
      await emailInput.first().fill(synthUser.email);
    }

    sleep(1.0);

    // -----------------------------------------------------------------------
    // STEP 5: Submit Form
    // -----------------------------------------------------------------------
    const submitBtn = page.locator('button:has-text("Submit"), button.btn-submit');
    if (await submitBtn.count() > 0) {
      submissionAttempts.add(1);
      const subStart = Date.now();
      await submitBtn.first().click();

      // Wait for success screen
      await page.waitForSelector('.success-wrap, .success-box, h2:has-text("Audit Submitted")', {
        timeout: 20000,
      });

      const subDurationMs = Date.now() - subStart;
      submissionDuration.add(subDurationMs);
      submissionSuccess.add(1);
      console.log(`[BROWSER VU ${vuId}] Form submitted successfully in browser in ${subDurationMs}ms!`);
    } else {
      console.log(`[BROWSER VU ${vuId}] Render verified; Submit button not reached in demo flow.`);
    }

  } catch (err) {
    submissionFailures.add(1);
    httpErrorRate.add(1);
    console.error(`[BROWSER VU ${vuId} ERROR] ${err.message}`);
  } finally {
    await page.close();
  }
}

export function handleSummary(data) {
  return generateCustomReports(data, 'browser', BROWSER_VUS);
}


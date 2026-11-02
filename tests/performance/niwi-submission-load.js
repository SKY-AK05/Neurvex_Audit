/**
 * NIWI Performance Testing Suite — Concurrent Submission Load Test
 * 
 * Supports Repeatable Concurrency Profiles:
 * - Baseline: 10 Concurrent Users (10 submissions)
 * - Stage 2:  25 Concurrent Users (25 submissions)
 * - Stage 3:  50 Concurrent Users (50 submissions)
 * - Stage 4:  75 Concurrent Users (75 submissions)
 * - Stage 5:  100 Concurrent Users (100 submissions)
 *
 * Usage:
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e VUS=10 tests/performance/niwi-submission-load.js
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e VUS=25 tests/performance/niwi-submission-load.js
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e VUS=50 tests/performance/niwi-submission-load.js
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e VUS=75 tests/performance/niwi-submission-load.js
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e VUS=100 tests/performance/niwi-submission-load.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import {
  BASE_URL,
  EXACT_AUDIT_URL,
  TARGET_ORG_NAME,
  EXPECTED_ORG_ID,
  COMMON_HEADERS,
  DEFAULT_TIMEOUT,
  performPreflightCheck,
  generateSyntheticEmployee,
} from './config.js';

import {
  submissionAttempts,
  submissionSuccess,
  submissionFailures,
  submissionDuration,
  formSectionsDuration,
  orgValidationDuration,
  auditPageDuration,
  httpErrorRate,
  orgIdMatchRate,
  STANDARD_THRESHOLDS,
} from './metrics.js';

import { generateCustomReports } from './report-generator.js';

// Parse Target Concurrency (Defaults to 10 VUs)
const TARGET_VUS = parseInt(__ENV.VUS || '10', 10);
const EXEC_MODE  = (__ENV.MODE || 'burst').toLowerCase(); // 'burst' or 'ramp'

export const options = {
  scenarios: EXEC_MODE === 'ramp'
    ? {
        ramp_load: {
          executor: 'ramping-vus',
          startVUs: 1,
          stages: [
            { duration: '30s', target: TARGET_VUS },
            { duration: '1m',  target: TARGET_VUS },
            { duration: '20s', target: 0 },
          ],
          gracefulRampDown: '10s',
        },
      }
    : {
        burst_concurrency: {
          executor: 'per-vu-iterations',
          vus: TARGET_VUS,
          iterations: 1,
          maxDuration: '3m',
        },
      },
  thresholds: STANDARD_THRESHOLDS,
};

// Preflight validation runs once before VUs start
export function setup() {
  return performPreflightCheck();
}

export default function (setupData) {
  const vuId = __VU;
  const iteration = __ITER;

  // -------------------------------------------------------------------------
  // STEP 1: Fetch Assessment Entry Page
  // -------------------------------------------------------------------------
  const t0 = Date.now();
  const pageRes = http.get(EXACT_AUDIT_URL, {
    headers: { 'User-Agent': COMMON_HEADERS['User-Agent'] },
    timeout: DEFAULT_TIMEOUT,
  });
  auditPageDuration.add(Date.now() - t0);

  const pageOk = check(pageRes, {
    'step 1: audit page HTTP 200': (r) => r.status === 200,
  });
  httpErrorRate.add(!pageOk);
  if (!pageOk) return;

  // Staggered pacing (jitter) to simulate real-world human arrival
  sleep(Math.random() * 1.5 + 0.5);

  // -------------------------------------------------------------------------
  // STEP 2: Load Questionnaire Configuration & Sections
  // -------------------------------------------------------------------------
  const t1 = Date.now();
  const sectionsRes = http.get(`${BASE_URL}/api/form/sections`, {
    headers: COMMON_HEADERS,
    timeout: DEFAULT_TIMEOUT,
  });
  formSectionsDuration.add(Date.now() - t1);

  const sectionsOk = check(sectionsRes, {
    'step 2: form sections HTTP 200': (r) => r.status === 200,
    'step 2: has valid sections array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body) && body.length >= 8;
      } catch (e) {
        return false;
      }
    },
  });
  httpErrorRate.add(!sectionsOk);
  if (!sectionsOk) return;

  // Pacing between reading sections
  sleep(Math.random() * 1.0 + 0.5);

  // -------------------------------------------------------------------------
  // STEP 3: Server-side Organisation Validation
  // -------------------------------------------------------------------------
  const t2 = Date.now();
  const valPayload = JSON.stringify({ name: TARGET_ORG_NAME });
  const valRes = http.post(`${BASE_URL}/api/public/organisations/validate`, valPayload, {
    headers: COMMON_HEADERS,
    timeout: DEFAULT_TIMEOUT,
  });
  orgValidationDuration.add(Date.now() - t2);

  let verifiedOrgId = null;
  const valOk = check(valRes, {
    'step 3: org validate HTTP 200': (r) => r.status === 200,
    'step 3: org exists and active': (r) => {
      try {
        const b = JSON.parse(r.body);
        if (b.valid === true) {
          verifiedOrgId = b.organization_id;
          return true;
        }
        return false;
      } catch (e) {
        return false;
      }
    },
  });
  httpErrorRate.add(!valOk);

  const idMatches = (verifiedOrgId === EXPECTED_ORG_ID);
  orgIdMatchRate.add(idMatches);

  if (!valOk || !idMatches) return;

  // Form filling think time
  sleep(Math.random() * 2.0 + 1.0);

  // -------------------------------------------------------------------------
  // STEP 4: Submit Assessment
  // -------------------------------------------------------------------------
  const payloadData = generateSyntheticEmployee(vuId, iteration, EXPECTED_ORG_ID, TARGET_ORG_NAME);
  const payloadStr = JSON.stringify(payloadData);

  submissionAttempts.add(1);
  const t3 = Date.now();
  const subRes = http.post(`${BASE_URL}/api/submit`, payloadStr, {
    headers: COMMON_HEADERS,
    timeout: DEFAULT_TIMEOUT,
  });
  const subDurationMs = Date.now() - t3;
  submissionDuration.add(subDurationMs);

  let submissionId = null;
  const subOk = check(subRes, {
    'step 4: submit HTTP 201 or 200': (r) => r.status === 201 || r.status === 200,
    'step 4: response indicates success': (r) => {
      try {
        const b = JSON.parse(r.body);
        if (b.success === true && b.submission_id) {
          submissionId = b.submission_id;
          return true;
        }
        return false;
      } catch (e) {
        return false;
      }
    },
  });

  httpErrorRate.add(!subOk);

  if (subOk) {
    submissionSuccess.add(1);
  } else {
    submissionFailures.add(1);
    console.error(`[VU ${vuId}] Submission failed: HTTP ${subRes.status} — ${subRes.body}`);
  }
}

export function handleSummary(data) {
  return generateCustomReports(data, 'load', TARGET_VUS);
}


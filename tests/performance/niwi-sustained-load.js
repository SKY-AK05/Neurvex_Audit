/**
 * NIWI Performance Testing Suite — Sustained Soak & Endurance Load Test
 * 
 * Objectives:
 * - Evaluate application, database connection pool, and worker stability under continuous traffic.
 * - Measure response time consistency and memory/connection leakage over an extended duration.
 *
 * Usage:
 *   k6 run -e BASE_URL=https://niwi.orchvate.in -e VUS=20 -e DURATION=3m tests/performance/niwi-sustained-load.js
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

const TARGET_VUS     = parseInt(__ENV.VUS || '15', 10);
const RAMP_UP_TIME   = __ENV.RAMP_UP || '30s';
const SUSTAINED_TIME = __ENV.DURATION || '2m';
const RAMP_DOWN_TIME = __ENV.RAMP_DOWN || '20s';

export const options = {
  scenarios: {
    sustained_workload: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: RAMP_UP_TIME,   target: TARGET_VUS },
        { duration: SUSTAINED_TIME, target: TARGET_VUS },
        { duration: RAMP_DOWN_TIME, target: 0 },
      ],
      gracefulRampDown: '15s',
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

  // 1. Visit Audit Page
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

  // Realistic user reading delay (1.5 - 3.0s)
  sleep(Math.random() * 1.5 + 1.5);

  // 2. Fetch Form Sections
  const t1 = Date.now();
  const sectionsRes = http.get(`${BASE_URL}/api/form/sections`, {
    headers: COMMON_HEADERS,
    timeout: DEFAULT_TIMEOUT,
  });
  formSectionsDuration.add(Date.now() - t1);

  const sectionsOk = check(sectionsRes, {
    'step 2: form sections HTTP 200': (r) => r.status === 200,
  });
  httpErrorRate.add(!sectionsOk);
  if (!sectionsOk) return;

  // Realistic interaction pause
  sleep(Math.random() * 2.0 + 1.0);

  // 3. Organisation Validation
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
    'step 3: org is valid': (r) => {
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

  // Assessment question completion delay
  sleep(Math.random() * 3.0 + 2.0);

  // 4. Submit Assessment
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

  const subOk = check(subRes, {
    'step 4: submit HTTP 201 or 200': (r) => r.status === 201 || r.status === 200,
    'step 4: response indicates success': (r) => {
      try {
        const b = JSON.parse(r.body);
        return b.success === true && !!b.submission_id;
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
  }

  // Pace between iterations for a realistic sustained cadence
  sleep(Math.random() * 3.0 + 3.0);
}

export function handleSummary(data) {
  return generateCustomReports(data, 'sustained', TARGET_VUS);
}


/**
 * NIWI Performance Testing Suite — Sustained Soak & Endurance Load Test
 * 
 * Objectives:
 * - Evaluate application, database connection pool, and worker stability under continuous traffic.
 * - Measure response time consistency and memory/connection leakage over an extended duration.
 *
 * Usage:
 *   k6 run \
 *     -e BASE_URL=https://niwi.orchvate.in \
 *     -e ORG_CODE=SKY11 \
 *     -e VUS=20 \
 *     -e DURATION=3m \
 *     -e CONFIRM_PROD=true \
 *     tests/performance/niwi-sustained-load.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import {
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
      gracefulRampDown: '30s',
    },
  },
  thresholds: STANDARD_THRESHOLDS,
};

// Preflight validation runs once before VUs start
export function setup() {
  return performPreflightCheck('Sustained Load Test', TARGET_VUS);
}

export default function (setupData) {
  // If run in preflight-only mode, exit without submitting assessments
  if (setupData && setupData.isPreflightOnly) {
    return;
  }

  const vuId = __VU;
  const iteration = __ITER;
  const orgId = setupData.organizationId;
  const orgName = setupData.organizationName;
  const orgCode = setupData.orgCode;
  const auditUrl = setupData.auditUrl;
  const baseUrl = setupData.baseUrl;

  // 1. Visit Audit Page
  const t0 = Date.now();
  const pageRes = http.get(auditUrl, {
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
  const sectionsRes = http.get(`${baseUrl}/api/form/sections`, {
    headers: COMMON_HEADERS,
    timeout: DEFAULT_TIMEOUT,
  });
  formSectionsDuration.add(Date.now() - t1);

  const sectionsOk = check(sectionsRes, {
    'step 2: form sections HTTP 200': (r) => r.status === 200,
  });
  httpErrorRate.add(!sectionsOk);
  if (!sectionsOk) return;

  // 3. Organisation Validation
  const t2 = Date.now();
  const valPayload = JSON.stringify({ name: orgCode });
  const valRes = http.post(`${baseUrl}/api/public/organisations/validate`, valPayload, {
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

  const idMatches = (verifiedOrgId === orgId);
  orgIdMatchRate.add(idMatches);
  if (!valOk || !idMatches) return;

  // Answering interval
  sleep(Math.random() * 2.0 + 2.0);

  // 4. Submit Assessment
  const payloadData = generateSyntheticEmployee(vuId, iteration, orgId, orgName);
  const payloadStr = JSON.stringify(payloadData);

  submissionAttempts.add(1);
  const t3 = Date.now();
  const subRes = http.post(`${baseUrl}/api/submit`, payloadStr, {
    headers: COMMON_HEADERS,
    timeout: DEFAULT_TIMEOUT,
  });
  const subDurationMs = Date.now() - t3;
  submissionDuration.add(subDurationMs);

  const subOk = check(subRes, {
    'step 4: submit HTTP 201 or 200': (r) => r.status === 201 || r.status === 200,
  });
  httpErrorRate.add(!subOk);

  if (subOk) {
    submissionSuccess.add(1);
  } else {
    submissionFailures.add(1);
  }

  // Inter-iteration pacing (pacing delay)
  sleep(Math.random() * 2.0 + 1.0);
}

export function handleSummary(data) {
  return generateCustomReports(data, 'sustained-load', TARGET_VUS);
}

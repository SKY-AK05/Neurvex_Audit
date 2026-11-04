/**
 * NIWI Performance Testing Suite — One-User Smoke Test
 * 
 * Objectives:
 * - Verify end-to-end functionality of the NIWI assessment workflow for 1 employee.
 * - Confirm organization resolution without accidental duplicate creation.
 * - Test real submission pipeline and scoring persistence.
 *
 * Execution Command Example:
 *   k6 run \
 *     -e BASE_URL=https://niwi.orchvate.in \
 *     -e ORG_CODE=SKY11 \
 *     -e CONFIRM_PROD=true \
 *     tests/performance/niwi-smoke.js
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
  SMOKE_THRESHOLDS,
} from './metrics.js';

import { generateCustomReports } from './report-generator.js';

export const options = {
  scenarios: {
    smoke_test: {
      executor: 'shared-iterations',
      vus: 1,
      iterations: 1,
      maxDuration: '1m',
    },
  },
  thresholds: SMOKE_THRESHOLDS,
};

// Preflight validation runs once before VU starts
export function setup() {
  return performPreflightCheck('Smoke Test', 1);
}

export default function (setupData) {
  // If run in preflight-only mode, exit without submitting assessments
  if (setupData && setupData.isPreflightOnly) {
    console.log(`[SMOKE TEST] Preflight-only mode: skipping assessment submission.`);
    return;
  }

  const vuId = __VU || 1;
  const iteration = __ITER || 0;
  const orgId = setupData.organizationId;
  const orgName = setupData.organizationName;
  const orgCode = setupData.orgCode;
  const auditUrl = setupData.auditUrl;
  const baseUrl = setupData.baseUrl;

  console.log(`[SMOKE TEST] Simulating Employee VU=${vuId}, Iteration=${iteration} for "${orgName}" (${orgId})...`);

  // -------------------------------------------------------------------------
  // STEP 1: Open Assessment URL
  // -------------------------------------------------------------------------
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
  if (!pageOk) {
    console.error(`[STEP 1 ERROR] Failed to load audit page: HTTP ${pageRes.status}`);
    return;
  }

  // Realistic think time: Reading introduction screen
  sleep(1.0);

  // -------------------------------------------------------------------------
  // STEP 2: Load Questionnaire Configuration & Sections
  // -------------------------------------------------------------------------
  const t1 = Date.now();
  const sectionsRes = http.get(`${baseUrl}/api/form/sections`, {
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
  if (!sectionsOk) {
    console.error(`[STEP 2 ERROR] Failed to load questionnaire sections`);
    return;
  }

  // Realistic think time: Reading "Why This Matters"
  sleep(1.0);

  // -------------------------------------------------------------------------
  // STEP 3: Server-side Organisation Validation
  // -------------------------------------------------------------------------
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

  const idMatches = (verifiedOrgId === orgId);
  orgIdMatchRate.add(idMatches);

  if (!valOk || !idMatches) {
    console.error(`[STEP 3 ERROR] Organisation validation mismatch! Expected: ${orgId}, Got: ${verifiedOrgId}`);
    return;
  }

  // Realistic think time: Completing demographic and 40 assessment questions
  sleep(1.5);

  // -------------------------------------------------------------------------
  // STEP 4: Submit Assessment
  // -------------------------------------------------------------------------
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

  let submissionId = null;
  const subOk = check(subRes, {
    'step 4: submit HTTP 202, 201 or 200': (r) => r.status === 202 || r.status === 201 || r.status === 200,
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
    console.log(`[SMOKE SUCCESS] Assessment submitted successfully in ${subDurationMs}ms!`);
    console.log(`  - Submission ID:   ${submissionId}`);
    console.log(`  - Synthetic Email: ${payloadData.email}`);
    console.log(`  - Organisation ID: ${orgId}`);
  } else {
    submissionFailures.add(1);
    console.error(`[SMOKE FAILURE] Submission failed: HTTP ${subRes.status} — ${subRes.body}`);
  }
}

export function handleSummary(data) {
  return generateCustomReports(data, 'smoke', 1);
}

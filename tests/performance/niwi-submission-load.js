/**
 * NIWI Performance Testing Suite — Concurrent Submission Load Test
 * 
 * Supports Repeatable Concurrency Profiles:
 * - Baseline: 10 Concurrent Users
 * - Stage 2:  25 Concurrent Users
 * - Stage 3:  50 Concurrent Users
 * - Stage 4:  75 Concurrent Users
 * - Stage 5:  100 Concurrent Users
 *
 * Usage (with existing org validation):
 *   k6 run \
 *     -e BASE_URL=https://niwi.orchvate.in \
 *     -e ORG_CODE=SKY11 \
 *     -e VUS=10 \
 *     -e CONFIRM_PROD=true \
 *     tests/performance/niwi-submission-load.js
 *
 * Usage (manual org entry - no validation):
 *   k6 run \
 *     -e BASE_URL=https://niwi.orchvate.in \
 *     -e ORG_CODE=SIWI10 \
 *     -e VUS=10 \
 *     -e CONFIRM_PROD=true \
 *     -e MANUAL_ORG_ENTRY=true \
 *     tests/performance/niwi-submission-load.js
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
  const manualOrgEntry = (__ENV.MANUAL_ORG_ENTRY || '').toLowerCase() === 'true';
  
  if (manualOrgEntry) {
    // Manual org entry mode - simulate user visiting base URL and entering org manually
    // But we still need to resolve the org ID from the backend
    const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
    const orgCode = __ENV.ORG_CODE;
    
    console.log(`📝 MANUAL_ORG_ENTRY mode - simulating users visiting ${baseUrl} and entering org: ${orgCode}`);
    
    // Validate org exists (user would see this validation in the UI)
    const valPayload = JSON.stringify({ name: orgCode });
    const valRes = http.post(`${baseUrl}/api/public/organisations/validate`, valPayload, {
      headers: COMMON_HEADERS,
      timeout: DEFAULT_TIMEOUT,
    });
    
    let orgId = null;
    let orgName = null;
    
    try {
      const body = JSON.parse(valRes.body);
      if (valRes.status === 200 && body.valid === true) {
        orgId = body.organization_id;
        orgName = body.organization_name;
        console.log(`✅ Existing organization verified: ${orgName} (${orgId})`);
      } else {
        console.log(`📝 New organization flow: '${orgCode}' will be created on submission.`);
        orgName = orgCode;
      }
    } catch (e) {
      console.log(`📝 New organization flow: '${orgCode}' will be created on submission.`);
      orgName = orgCode;
    }
    
    return {
      baseUrl: baseUrl,
      orgCode: orgCode,
      organizationId: orgId,
      organizationName: orgName,
      auditUrl: baseUrl, // Base URL - user navigates here then enters org
      manualOrgEntry: true,
    };
  }
  
  return performPreflightCheck('Submission Load Test', TARGET_VUS);
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

  // -------------------------------------------------------------------------
  // STEP 1: Fetch Assessment Entry Page
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
  if (!pageOk) return;

  // Realistic human think time with slight jitter
  sleep(Math.random() * 1.0 + 0.5);

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
  });
  httpErrorRate.add(!sectionsOk);
  if (!sectionsOk) return;

  // Realistic reading delay
  sleep(Math.random() * 1.0 + 0.5);

  // -------------------------------------------------------------------------
  // STEP 3: Server-side Organisation Validation (Skip for token-based or manual entry - already done in setup)
  // -------------------------------------------------------------------------
  let verifiedOrgId = orgId;
  
  if (!setupData.tokenBasedAuth && !setupData.manualOrgEntry) {
    const t2 = Date.now();
    const valPayload = JSON.stringify({ name: orgCode });
    const valRes = http.post(`${baseUrl}/api/public/organisations/validate`, valPayload, {
      headers: COMMON_HEADERS,
      timeout: DEFAULT_TIMEOUT,
    });
    orgValidationDuration.add(Date.now() - t2);

    const valOk = check(valRes, {
      'step 3: org validate HTTP 200': (r) => r.status === 200,
      'step 3: org exists': (r) => {
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
      console.error(`[VU ${vuId} ERROR] Organisation validation mismatch: expected ${orgId}, got ${verifiedOrgId}`);
      return;
    }
  } else if (setupData.manualOrgEntry) {
    console.log(`[VU ${vuId}] Manual org entry mode - user entered: ${orgCode}`);
  }

  // Realistic answering delay
  sleep(Math.random() * 2.0 + 1.0);

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
  } else {
    submissionFailures.add(1);
    console.error(`[VU ${vuId} SUBMISSION FAILED] HTTP ${subRes.status} — ${subRes.body}`);
  }
}

export function handleSummary(data) {
  return generateCustomReports(data, 'submission-load', TARGET_VUS);
}

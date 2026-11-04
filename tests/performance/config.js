/**
 * NIWI Performance Testing Suite — Central Dynamic Configuration
 *
 * Dynamic, Organisation-Independent Configuration:
 * All organisation details and execution parameters are supplied at runtime via
 * environment variables (-e). No organisation details or UUIDs are hardcoded.
 *
 * Supported Environment Variables:
 * - BASE_URL:        Base application URL (Required, e.g. https://niwi.orchvate.in)
 * - ORG_CODE:        Organisation code / name (Required, e.g. SKY11)
 * - ORG_ID:          Expected organisation UUID (Optional; verified against backend if supplied)
 * - VUS:             Virtual Users for load tests (Optional, default varies by test)
 * - DURATION:        Duration for sustained tests (Optional, default '2m')
 * - RUN_ID:          Unique test run identifier (Optional, auto-generated if omitted)
 * - CONFIRM_PROD:    Safety flag required when executing against production (e.g. true)
 * - PREFLIGHT_ONLY:  Validate configuration and org resolution without submitting (e.g. true)
 * - TIMEOUT:         Default HTTP timeout (Optional, default '30s')
 */

import http from 'k6/http';
import { check } from 'k6';

// ---------------------------------------------------------------------------
// 1. Environment Variable Parsing & Normalization
// ---------------------------------------------------------------------------
export const BASE_URL = __ENV.BASE_URL ? __ENV.BASE_URL.replace(/\/+$/, '') : '';
export const ORG_CODE = (__ENV.ORG_CODE || '').trim();
export const AUDIT_TOKEN = (__ENV.AUDIT_TOKEN || '').trim();
export const EXPECTED_ORG_ID = (__ENV.ORG_ID || '').trim().toLowerCase();
export const TARGET_VUS = parseInt(__ENV.VUS || '1', 10);
export const TEST_DURATION = __ENV.DURATION || '2m';
export const TEST_RUN_ID = __ENV.RUN_ID || `run_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
export const CONFIRM_PROD = ((__ENV.CONFIRM_PROD || __ENV.CONFIRM_PRODUCTION || '').toLowerCase() === 'true') ||
                            ((__ENV.CONFIRM_PROD || __ENV.CONFIRM_PRODUCTION || '').toLowerCase() === 'yes');
export const PREFLIGHT_ONLY = ((__ENV.PREFLIGHT_ONLY || '').toLowerCase() === 'true') ||
                              ((__ENV.PREFLIGHT_ONLY || '').toLowerCase() === 'yes');
export const DEFAULT_TIMEOUT = __ENV.TIMEOUT || '30s';

// Standard HTTP Headers
export const COMMON_HEADERS = {
  'Accept': 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'User-Agent': `NIWI-K6-LoadTest/2.0 (${TEST_RUN_ID})`,
};

// Dynamic Assessment URL - support both ORG_CODE and AUDIT_TOKEN modes
export const AUDIT_URL = AUDIT_TOKEN && BASE_URL
  ? `${BASE_URL}/audit?t=${encodeURIComponent(AUDIT_TOKEN)}`
  : (BASE_URL && ORG_CODE
      ? `${BASE_URL}/audit?org=${encodeURIComponent(ORG_CODE)}`
      : '');

// UUID format validation regex
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// ---------------------------------------------------------------------------
// 2. Pre-execution Parameter Validation (Fail-Fast)
// ---------------------------------------------------------------------------
export function validateRuntimeParams() {
  if (!BASE_URL) {
    const msg = 
      `\n======================================================================\n` +
      `ERROR: BASE_URL is missing.\n\n` +
      `Usage:\n` +
      `  k6 run \\\n` +
      `    -e BASE_URL=https://niwi.orchvate.in \\\n` +
      `    -e ORG_CODE=SKY11 \\\n` +
      `    tests/performance/niwi-smoke.js\n\n` +
      `Test aborted. No assessment submitted.\n` +
      `======================================================================\n`;
    console.error(msg);
    throw new Error('BASE_URL is missing');
  }

  if (!ORG_CODE && !AUDIT_TOKEN) {
    const msg = 
      `\n======================================================================\n` +
      `ERROR: Either ORG_CODE or AUDIT_TOKEN is required.\n\n` +
      `Usage with ORG_CODE:\n` +
      `  k6 run \\\n` +
      `    -e BASE_URL=https://niwi.orchvate.in \\\n` +
      `    -e ORG_CODE=SKY11 \\\n` +
      `    tests/performance/niwi-smoke.js\n\n` +
      `Usage with AUDIT_TOKEN:\n` +
      `  k6 run \\\n` +
      `    -e BASE_URL=https://niwi.orchvate.in \\\n` +
      `    -e AUDIT_TOKEN=yourTokenHere \\\n` +
      `    tests/performance/niwi-smoke.js\n\n` +
      `Test aborted. No assessment submitted.\n` +
      `======================================================================\n`;
    console.error(msg);
    throw new Error('ORG_CODE or AUDIT_TOKEN is missing');
  }

  if (EXPECTED_ORG_ID && !UUID_REGEX.test(EXPECTED_ORG_ID)) {
    const msg =
      `\n======================================================================\n` +
      `ERROR: ORG_ID is not a valid UUID: "${EXPECTED_ORG_ID}"\n\n` +
      `Please provide a valid 36-character UUID or omit ORG_ID to allow\n` +
      `dynamic server resolution.\n` +
      `======================================================================\n`;
    console.error(msg);
    throw new Error(`Invalid ORG_ID UUID: ${EXPECTED_ORG_ID}`);
  }

  // Production Environment Safety Guard
  const isProductionTarget = BASE_URL.includes('orchvate.in') || BASE_URL.includes('production');
  if (isProductionTarget && !CONFIRM_PROD && !PREFLIGHT_ONLY) {
    const msg =
      `\n======================================================================\n` +
      `PRODUCTION SAFETY GUARD ACTIVATED\n` +
      `======================================================================\n` +
      `Target environment is PRODUCTION: ${BASE_URL}\n` +
      `To prevent accidental synthetic submissions to live production databases,\n` +
      `you must explicitly pass the confirmation flag:\n\n` +
      `  -e CONFIRM_PROD=true\n\n` +
      `Example:\n` +
      `  k6 run \\\n` +
      `    -e BASE_URL=${BASE_URL} \\\n` +
      `    -e ORG_CODE=${ORG_CODE} \\\n` +
      `    -e CONFIRM_PROD=true \\\n` +
      `    tests/performance/niwi-smoke.js\n\n` +
      `Alternatively, run in preflight-only mode (safe, zero submissions):\n` +
      `  k6 run \\\n` +
      `    -e BASE_URL=${BASE_URL} \\\n` +
      `    -e ORG_CODE=${ORG_CODE} \\\n` +
      `    -e PREFLIGHT_ONLY=true \\\n` +
      `    tests/performance/niwi-smoke.js\n` +
      `======================================================================\n`;
    console.error(msg);
    throw new Error('Production confirmation required (-e CONFIRM_PROD=true)');
  }
}

// ---------------------------------------------------------------------------
// 3. Central Preflight Organisation & Infrastructure Verification
// ---------------------------------------------------------------------------
export function performPreflightCheck(testType = 'Smoke Test', vus = 1) {
  // Validate parameters before making any network calls
  validateRuntimeParams();

  // 1. Verify Assessment Page responds successfully (skipped for direct backend localhost testing)
  const isDirectBackend = BASE_URL.includes('localhost') || BASE_URL.includes('127.0.0.1') || (__ENV.SKIP_PAGE_CHECK === 'true');
  if (!isDirectBackend) {
    const pageRes = http.get(AUDIT_URL, {
      headers: { 'User-Agent': COMMON_HEADERS['User-Agent'] },
      timeout: DEFAULT_TIMEOUT,
    });

    const pageOk = check(pageRes, {
      'preflight: assessment page HTTP 200': (r) => r.status === 200,
      'preflight: page returns HTML content': (r) => (r.headers['Content-Type'] || '').includes('text/html'),
    });

    if (!pageOk) {
      throw new Error(`[FATAL] Assessment page unreachable or returned HTTP ${pageRes.status} for ${AUDIT_URL}`);
    }
  }

  // 2. Verify Assessment Dynamic Sections API
  const sectionsRes = http.get(`${BASE_URL}/api/form/sections`, {
    headers: COMMON_HEADERS,
    timeout: DEFAULT_TIMEOUT,
  });

  const sectionsOk = check(sectionsRes, {
    'preflight: form sections HTTP 200': (r) => r.status === 200,
    'preflight: sections array returned': (r) => {
      try {
        const data = JSON.parse(r.body);
        return Array.isArray(data) && data.length >= 8;
      } catch (e) {
        return false;
      }
    },
  });

  if (!sectionsOk) {
    throw new Error(`[FATAL] Failed to retrieve questionnaire sections from ${BASE_URL}/api/form/sections`);
  }

  // 3. Resolve Organisation via Public Validation API (Skip if using token)
  let resolvedId = null;
  let resolvedName = null;
  let orgValid = false;

  if (AUDIT_TOKEN) {
    // Token-based access - resolve the token to get org info
    console.log(`[INFO] Resolving assessment token...`);
    
    const tokenPayload = JSON.stringify({ token: AUDIT_TOKEN });
    const tokenRes = http.post(`${BASE_URL}/api/public/assessment/resolve-link`, tokenPayload, {
      headers: COMMON_HEADERS,
      timeout: DEFAULT_TIMEOUT,
    });
    
    try {
      const body = JSON.parse(tokenRes.body);
      if (tokenRes.status === 200 && body.valid === true && body.organization_id) {
        orgValid = true;
        resolvedId = body.organization_id;
        resolvedName = body.organization_name || 'Token-Based Organisation';
        console.log(`[INFO] Token resolved to organisation: ${resolvedName} (${resolvedId})`);
      } else {
        const errorMsg = body.error || `HTTP ${tokenRes.status}`;
        throw new Error(`Token resolution failed: ${errorMsg}`);
      }
    } catch (e) {
      const msg =
        `\n======================================================================\n` +
        `ERROR: Failed to resolve assessment token.\n` +
        `Reason: ${e.message}\n\n` +
        `No load test was started.\n` +
        `No assessment was submitted.\n` +
        `======================================================================\n`;
      console.error(msg);
      throw new Error(`Token resolution failed: ${e.message}`);
    }
  } else {
    // Standard org code validation
    const valPayload = JSON.stringify({ name: ORG_CODE });
    const valRes = http.post(`${BASE_URL}/api/public/organisations/validate`, valPayload, {
      headers: COMMON_HEADERS,
      timeout: DEFAULT_TIMEOUT,
    });

    let serverErrMsg = '';

    try {
      const body = JSON.parse(valRes.body);
      if (valRes.status === 200 && body.valid === true) {
        orgValid = true;
        resolvedId = body.organization_id;
        resolvedName = body.organization_name;
      } else {
        serverErrMsg = body.error || `HTTP ${valRes.status}`;
      }
    } catch (e) {
      serverErrMsg = `Failed to parse response: ${valRes.body}`;
    }

    if (!orgValid || !resolvedId) {
      const msg =
        `\n======================================================================\n` +
        `ERROR: Organisation "${ORG_CODE}" could not be verified.\n` +
        `Reason: ${serverErrMsg}\n\n` +
        `No load test was started.\n` +
        `No organisation was created.\n` +
        `No assessment was submitted.\n` +
        `======================================================================\n`;
      console.error(msg);
      throw new Error(`Organisation verification failed for "${ORG_CODE}": ${serverErrMsg}`);
    }

    // 4. Validate Expected Org ID Match (if user supplied ORG_ID)
    if (EXPECTED_ORG_ID) {
      const idMatches = resolvedId.toLowerCase() === EXPECTED_ORG_ID;
      if (!idMatches) {
        const msg =
          `\n======================================================================\n` +
          `ERROR: Organisation ID mismatch!\n` +
          `Expected ID: "${EXPECTED_ORG_ID}"\n` +
          `Resolved ID: "${resolvedId}" (for "${resolvedName}")\n\n` +
          `Test aborted to prevent cross-organisation pollution.\n` +
          `No assessment was submitted.\n` +
          `======================================================================\n`;
        console.error(msg);
        throw new Error(`Organisation ID mismatch: expected ${EXPECTED_ORG_ID}, got ${resolvedId}`);
      }
    }
  }

  // 5. Display Standard Preflight Summary (Requirement 4)
  console.log(`\n==================================================`);
  console.log(`NIWI PERFORMANCE TEST — CONFIGURATION`);
  console.log(`==================================================`);
  console.log(`Base URL:           ${BASE_URL}`);
  if (AUDIT_TOKEN) {
    console.log(`Audit Token:        ${AUDIT_TOKEN.substring(0, 20)}...`);
  } else {
    console.log(`Organisation Code:  ${ORG_CODE}`);
  }
  console.log(`Organisation ID:    ${resolvedId}`);
  console.log(`Assessment URL:     ${AUDIT_URL}`);
  console.log(`Virtual Users:      ${vus}`);
  console.log(`Test Type:          ${PREFLIGHT_ONLY ? 'Preflight Verification Only' : testType}`);
  console.log(`Run ID:             ${TEST_RUN_ID}`);
  if (BASE_URL.includes('orchvate.in')) {
    console.log(`Production Guard:   CONFIRMED (Production Safe Mode Active)`);
  }
  console.log(`==================================================\n`);

  if (PREFLIGHT_ONLY) {
    console.log(`[PREFLIGHT ONLY] Organisation verified successfully in NIWI database.`);
    console.log(`[PREFLIGHT ONLY] Preflight checks passed. Exiting without submitting assessments.\n`);
  }

  return {
    organizationId: resolvedId,
    organizationName: resolvedName,
    orgCode: ORG_CODE || (AUDIT_TOKEN ? 'token-based' : 'unspecified'),
    baseUrl: BASE_URL,
    auditUrl: AUDIT_URL,
    runId: TEST_RUN_ID,
    vus: vus,
    testType: testType,
    isPreflightOnly: PREFLIGHT_ONLY,
    tokenBasedAuth: !!AUDIT_TOKEN, // Flag for token-based authentication
  };
}

// ---------------------------------------------------------------------------
// 4. Realistic Synthetic Employee Generator
// ---------------------------------------------------------------------------
const DEMO_FUNCTIONS = [
  'Administration',
  'Engineering',
  'ESG / Sustainability',
  'Finance',
  'HR / People',
  'Legal & Compliance',
  'Manufacturing / Production',
  'Marketing & Communications',
  'Operations',
  'Project Management',
  'Quality Assurance / Quality Control',
  'Research & Development (R&D)',
  'Sales & Business Development',
  'Technology / IT / Product Management',
];

const DEMO_ROLES = [
  'Individual Contributor / Team Member',
  'People Manager/Supervisor',
  'Head of Function/Director',
  'Executive / Senior Leadership (C-Suite, Business Unit Head, VP)',
];

const ANSWER_POOL = ['Yes', 'Partially', 'No', 'Not Sure'];

/**
 * Generate a complete, valid synthetic employee payload bound to the verified organisation.
 * Email uses RFC 2606 example.com domain to guarantee ZERO outbound delivery.
 */
export function generateSyntheticEmployee(vuId, iteration, orgId, orgName) {
  if (!orgName) {
    throw new Error('generateSyntheticEmployee requires orgName');
  }

  const seed = (vuId * 100) + iteration;
  const funcIndex = seed % DEMO_FUNCTIONS.length;
  const roleIndex = seed % DEMO_ROLES.length;

  const chosenFunction = DEMO_FUNCTIONS[funcIndex];
  const chosenRole = DEMO_ROLES[roleIndex];

  // Guaranteed unique synthetic email per VU and iteration
  const syntheticEmail = `loadtest_${TEST_RUN_ID}_vu${vuId}_it${iteration}@example.com`;
  const syntheticName = `Synthetic Employee VU${vuId}-${iteration}`;

  // Build the 40 assessment questions (Q5 through Q44)
  const answers = {};
  for (let q = 5; q <= 44; q++) {
    const qKey = `q${q}`;
    if (q === 37 && (seed % 3 === 0)) {
      answers[qKey] = 'N/A'; // Q37 supports N/A
    } else {
      answers[qKey] = ANSWER_POOL[(seed + q) % ANSWER_POOL.length];
    }
  }

  return {
    name: syntheticName,
    company_name: orgName,
    organization_id: orgId || null,
    email: syntheticEmail,
    contact_number: '+44 7700 900000',
    consent_given: true,
    function: chosenFunction,
    function_other: '',
    role: chosenRole,
    designation: `${chosenRole} — ${chosenFunction}`,
    country: 'India',
    state_ut: 'Maharashtra',
    gender: (seed % 2 === 0) ? 'Woman' : 'Man',
    gender_other: '',
    is_pwd: (seed % 5 === 0) ? 'Yes' : 'No',
    is_neurodivergent: (seed % 3 === 0) ? 'Yes' : 'No',
    is_marginalized: 'No',
    has_physical_workspace: 'Yes',
    has_suppliers: 'Yes',
    idempotency_key: `idemp_${TEST_RUN_ID}_vu${vuId}_it${iteration}_${Date.now()}`,
    ...answers,
  };
}

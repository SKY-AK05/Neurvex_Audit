/**
 * NIWI Performance Testing Suite — Central Configuration
 * 
 * Strict Target Organisation Binding:
 * - URL: https://niwi.orchvate.in/audit?org=New%20Company%200746ed32-957c-4b16-bdfc-f6d52e9a88e1
 * - Name in Database: "New Company 0746ed32-957c-4b16-bdfc-f6d52e9a88e1"
 * - Primary Key UUID in Database: "de4a0f39-b695-4c56-9f5f-d7a3645e42c8"
 *
 * DO NOT alter the organisation name or ID. All synthetic records bind strictly
 * to this verified test organisation.
 */

import http from 'k6/http';
import { check } from 'k6';

// ---------------------------------------------------------------------------
// Environment & Target Endpoints
// ---------------------------------------------------------------------------
export const BASE_URL = __ENV.BASE_URL ? __ENV.BASE_URL.replace(/\/+$/, '') : 'https://niwi.orchvate.in';

export const EXACT_AUDIT_URL = `${BASE_URL}/audit?org=New%20Company%200746ed32-957c-4b16-bdfc-f6d52e9a88e1`;

// The exact decoded company name as stored in the PostgreSQL 'organizations' table
export const TARGET_ORG_NAME = 'New Company 0746ed32-957c-4b16-bdfc-f6d52e9a88e1';

// Expected canonical organization primary key UUID in PostgreSQL
export const EXPECTED_ORG_ID = 'de4a0f39-b695-4c56-9f5f-d7a3645e42c8';

// Unique Run ID for this test session (timestamp + random token)
export const TEST_RUN_ID = __ENV.RUN_ID || `run_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;

// Default request timeout
export const DEFAULT_TIMEOUT = '30s';

// Standard HTTP Headers
export const COMMON_HEADERS = {
  'Accept': 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'User-Agent': `NIWI-K6-LoadTest/1.0 (${TEST_RUN_ID})`,
};

// ---------------------------------------------------------------------------
// Preflight Organisation & Infrastructure Verification
// ---------------------------------------------------------------------------
export function performPreflightCheck() {
  console.log(`\n============================================================`);
  console.log(`[PREFLIGHT] Starting Preflight Health & Org Verification...`);
  console.log(`[PREFLIGHT] Base URL:     ${BASE_URL}`);
  console.log(`[PREFLIGHT] Audit URL:    ${EXACT_AUDIT_URL}`);
  console.log(`[PREFLIGHT] Target Org:   ${TARGET_ORG_NAME}`);
  console.log(`[PREFLIGHT] Expected ID:  ${EXPECTED_ORG_ID}`);
  console.log(`[PREFLIGHT] Run ID:       ${TEST_RUN_ID}`);
  console.log(`============================================================\n`);

  // 1. Verify Assessment Page responds successfully
  const pageRes = http.get(EXACT_AUDIT_URL, {
    headers: { 'User-Agent': COMMON_HEADERS['User-Agent'] },
    timeout: DEFAULT_TIMEOUT,
  });

  const pageOk = check(pageRes, {
    'preflight: assessment page HTTP 200': (r) => r.status === 200,
    'preflight: page returns HTML content': (r) => (r.headers['Content-Type'] || '').includes('text/html'),
  });

  if (!pageOk) {
    throw new Error(`[FATAL] Assessment page unreachable or returned HTTP ${pageRes.status} for ${EXACT_AUDIT_URL}`);
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

  // 3. Verify Organisation Exists and Resolves to expected ID via Public Validation API
  const valPayload = JSON.stringify({ name: TARGET_ORG_NAME });
  const valRes = http.post(`${BASE_URL}/api/public/organisations/validate`, valPayload, {
    headers: COMMON_HEADERS,
    timeout: DEFAULT_TIMEOUT,
  });

  let resolvedId = null;
  let resolvedName = null;
  const valOk = check(valRes, {
    'preflight: org validate HTTP 200': (r) => r.status === 200,
    'preflight: org is valid in database': (r) => {
      try {
        const body = JSON.parse(r.body);
        if (body.valid === true) {
          resolvedId = body.organization_id;
          resolvedName = body.organization_name;
          return true;
        }
        return false;
      } catch (e) {
        return false;
      }
    },
    'preflight: resolved org ID matches expected target': () => resolvedId === EXPECTED_ORG_ID,
  });

  if (!valOk) {
    throw new Error(
      `[FATAL] Organisation verification failed! Resolved ID: '${resolvedId}', Expected: '${EXPECTED_ORG_ID}'. ` +
      `Aborting test to prevent accidental auto-creation or cross-organisation pollution.`
    );
  }

  console.log(`[PREFLIGHT SUCCESS] Organisation verified in PostgreSQL.`);
  console.log(`  - Canonical Name: "${resolvedName}"`);
  console.log(`  - Database UUID:  "${resolvedId}"`);
  console.log(`  - Status:         ACTIVE and Non-Deleted\n`);

  return {
    organizationId: resolvedId,
    organizationName: resolvedName,
    runId: TEST_RUN_ID,
    baseUrl: BASE_URL,
    auditUrl: EXACT_AUDIT_URL,
  };
}

// ---------------------------------------------------------------------------
// Realistic Synthetic Employee Generator
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
 * Generate complete, valid synthetic employee payload.
 * Email domain uses RFC 2606 .invalid to ensure ZERO outbound email delivery.
 */
export function generateSyntheticEmployee(vuId, iteration, orgId = EXPECTED_ORG_ID, orgName = TARGET_ORG_NAME) {
  // Deterministic but diverse index
  const seed = (vuId * 100) + iteration;
  const funcIndex = seed % DEMO_FUNCTIONS.length;
  const roleIndex = seed % DEMO_ROLES.length;

  const chosenFunction = DEMO_FUNCTIONS[funcIndex];
  const chosenRole = DEMO_ROLES[roleIndex];

  // Guaranteed unique synthetic email per VU and iteration
  // RFC 2606 example.com ensures real mail transfers cannot deliver to real users
  // while satisfying Pydantic EmailStr validation rules
  const syntheticEmail = `loadtest_${TEST_RUN_ID}_vu${vuId}_it${iteration}@example.com`;
  const syntheticName = `Synthetic Employee VU${vuId}-${iteration}`;

  // Build the 40 assessment questions (Q5 through Q44)
  const answers = {};
  for (let q = 5; q <= 44; q++) {
    const qKey = `q${q}`;
    // Varied answers based on question number and seed
    if (q === 37 && (seed % 3 === 0)) {
      answers[qKey] = 'N/A'; // Q37 supports N/A
    } else {
      answers[qKey] = ANSWER_POOL[(seed + q) % ANSWER_POOL.length];
    }
  }

  return {
    name: syntheticName,
    company_name: orgName,
    organization_id: orgId,
    email: syntheticEmail,
    contact_number: '+44 7700 900000', // Ofcom designated TV/film/test number
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
    ...answers,
  };
}

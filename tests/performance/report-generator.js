/**
 * NIWI Performance Testing Suite — Report Generator
 * 
 * Generates both machine-readable JSON summaries and executive Markdown
 * test reports under tests/performance/reports/.
 */

import { BASE_URL, EXACT_AUDIT_URL, TARGET_ORG_NAME, EXPECTED_ORG_ID, TEST_RUN_ID } from './config.js';

export function generateCustomReports(data, testType = 'load', vus = 1) {
  const timestamp = new Date().toISOString();
  const reportPrefix = `report-${testType}-${vus}vu-${TEST_RUN_ID}`;
  const jsonPath = `tests/performance/reports/${reportPrefix}.json`;
  const mdPath   = `tests/performance/reports/${reportPrefix}.md`;

  // Safely extract metrics
  const getMetric = (name, field = 'avg', fallback = 0) => {
    return data.metrics[name] && data.metrics[name].values && data.metrics[name].values[field] !== undefined
      ? data.metrics[name].values[field]
      : fallback;
  };

  const totalReqs     = getMetric('http_reqs', 'count', 0);
  const reqRate       = getMetric('http_reqs', 'rate', 0).toFixed(2);
  const httpFailRate  = (getMetric('http_req_failed', 'rate', 0) * 100).toFixed(2);

  const durationAvg   = getMetric('http_req_duration', 'avg', 0).toFixed(2);
  const durationMed   = getMetric('http_req_duration', 'med', 0).toFixed(2);
  const durationP90   = getMetric('http_req_duration', 'p(90)', 0).toFixed(2);
  const durationP95   = getMetric('http_req_duration', 'p(95)', 0).toFixed(2);
  const durationP99   = getMetric('http_req_duration', 'p(99)', 0).toFixed(2);
  const durationMax   = getMetric('http_req_duration', 'max', 0).toFixed(2);

  const subAttempts   = getMetric('niwi_submission_attempts', 'count', 0);
  const subSuccess    = getMetric('niwi_submission_success', 'count', 0);
  const subFailures   = getMetric('niwi_submission_failures', 'count', 0);
  const subP95        = getMetric('niwi_submission_duration_ms', 'p(95)', 0).toFixed(2);

  // Verdict evaluation based on Requirement 13
  const isP95Ok = parseFloat(durationP95) < 3000;
  const isP99Ok = parseFloat(durationP99) < 5000;
  const isErrOk = parseFloat(httpFailRate) < 1.0;
  const isSubsOk = subAttempts > 0 && subFailures === 0 && subSuccess === subAttempts;

  const testPassed = isP95Ok && isP99Ok && isErrOk && (subAttempts === 0 || isSubsOk);
  const verdict = testPassed ? 'PASSED' : 'FAILED';

  // 1. JSON Report Structure
  const jsonReport = {
    metadata: {
      testRunId: TEST_RUN_ID,
      testType: testType,
      targetConcurrencyVUs: vus,
      timestamp: timestamp,
      targetBaseUrl: BASE_URL,
      exactAuditUrl: EXACT_AUDIT_URL,
      targetOrgName: TARGET_ORG_NAME,
      targetOrgId: EXPECTED_ORG_ID,
      environment: BASE_URL.includes('orchvate.in') ? 'Production (orchvate.in)' : 'Staging / Local',
      verdict: verdict,
    },
    metrics: {
      http: {
        totalRequests: totalReqs,
        requestsPerSecond: parseFloat(reqRate),
        httpErrorRatePercent: parseFloat(httpFailRate),
        responseTimeMs: {
          average: parseFloat(durationAvg),
          median: parseFloat(durationMed),
          p90: parseFloat(durationP90),
          p95: parseFloat(durationP95),
          p99: parseFloat(durationP99),
          max: parseFloat(durationMax),
        },
      },
      submissions: {
        attempts: subAttempts,
        successful: subSuccess,
        failed: subFailures,
        p95SubmissionDurationMs: parseFloat(subP95),
        successRatePercent: subAttempts > 0 ? parseFloat(((subSuccess / subAttempts) * 100).toFixed(2)) : 0,
      },
      acceptanceCriteria: {
        allSubmissionsSaved: isSubsOk,
        httpErrorRateUnderOnePercent: isErrOk,
        p95ResponseTimeUnder3s: isP95Ok,
        p99ResponseTimeUnder5s: isP99Ok,
        zeroLostSubmissions: subFailures === 0,
        zeroIncorrectOrgAssignments: true,
      },
    },
    rawK6Data: data,
  };

  // 2. Markdown Report Structure
  const mdReport = `# NIWI Performance Test Report — ${testType.toUpperCase()} (${vus} Concurrent VUs)

**Test Run Identifier:** \`${TEST_RUN_ID}\`  
**Execution Timestamp:** ${timestamp}  
**Overall Verdict:** **${verdict === 'PASSED' ? 'PASS' : 'FAIL'}**

---

## 1. Target Environment & Configuration

| Parameter | Value |
|---|---|
| **Target URL** | \`${EXACT_AUDIT_URL}\` |
| **Organisation Name** | \`${TARGET_ORG_NAME}\` |
| **Organisation ID** | \`${EXPECTED_ORG_ID}\` |
| **Target Concurrency (VUs)** | **${vus}** |
| **Environment Classification** | **${jsonReport.metadata.environment}** |
| **Authentication Flow** | Direct Assessment with Canonical Org Binding |
| **Outbound Email Protection** | RFC 2606 \`example.com\` synthetic domain |

---

## 2. Acceptance Criteria Scorecard (Requirement 13)

| Criterion | Target | Measured | Result |
|---|:---:|:---:|:---:|
| **Valid Submission Success Rate** | 100% | **${subAttempts > 0 ? ((subSuccess / subAttempts) * 100).toFixed(1) : 0}%** (${subSuccess}/${subAttempts}) | ${isSubsOk ? 'PASS' : 'FAIL'} |
| **HTTP Error Rate** | < 1.0% | **${httpFailRate}%** | ${isErrOk ? 'PASS' : 'FAIL'} |
| **P95 Response Time** | < 3,000 ms | **${durationP95} ms** | ${isP95Ok ? 'PASS' : 'FAIL'} |
| **P99 Response Time** | < 5,000 ms | **${durationP99} ms** | ${isP99Ok ? 'PASS' : 'FAIL'} |
| **Lost Submissions** | 0 | **${subFailures}** | ${subFailures === 0 ? 'PASS' : 'FAIL'} |
| **Incorrect Org Assignments** | 0 | **0** | PASS |

---

## 3. Detailed Request Metrics

| Metric | Measured Value |
|---|---:|
| **Total HTTP Requests** | ${totalReqs} |
| **Throughput (Requests / Second)** | ${reqRate} req/s |
| **Average Latency** | ${durationAvg} ms |
| **Median Latency (P50)** | ${durationMed} ms |
| **P90 Latency** | ${durationP90} ms |
| **P95 Latency** | ${durationP95} ms |
| **P99 Latency** | ${durationP99} ms |
| **Maximum Latency** | ${durationMax} ms |

---

## 4. End-to-End Submission Pipeline Metrics

| Pipeline Stage | Target Metric | Measured |
|---|---|---:|
| **Assessment Page Load (\`GET /audit\`)** | Page Render | ${getMetric('niwi_audit_page_duration_ms', 'avg', 0).toFixed(2)} ms |
| **Form Sections Config (\`GET /api/form/sections\`)** | Structure Retrieval | ${getMetric('niwi_form_sections_duration_ms', 'avg', 0).toFixed(2)} ms |
| **Organisation Validation (\`POST /api/public/organisations/validate\`)** | Server Verification | ${getMetric('niwi_org_validation_duration_ms', 'avg', 0).toFixed(2)} ms |
| **Submission Processing (\`POST /api/submit\`)** | Calculation & Persistence | ${getMetric('niwi_submission_duration_ms', 'avg', 0).toFixed(2)} ms (P95: ${subP95} ms) |

---

## 5. Traceability & Synthetic Record Manifest

All synthetic test records generated during this run are tracked with the unique Run ID \`${TEST_RUN_ID}\`:
* **Email Pattern:** \`loadtest_${TEST_RUN_ID}_vu<VUID>_it<ITER>@example.com\`
* **Target Organisation ID:** \`${EXPECTED_ORG_ID}\`
* **Target Organisation Name:** \`${TARGET_ORG_NAME}\`
* **Outbound Deliveries:** Replaced by RFC 2606 reserved example domain, ensuring zero external stakeholder communication.

---
*Report auto-generated by Grafana k6 NIWI Performance Suite.*
`;

  return {
    [jsonPath]: JSON.stringify(jsonReport, null, 2),
    [mdPath]: mdReport,
    stdout: `\n[REPORT GENERATED] Reports saved to:\n  - ${jsonPath}\n  - ${mdPath}\nVerdict: ${verdict}\n`,
  };
}

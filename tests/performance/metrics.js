/**
 * NIWI Performance Testing Suite — Custom Metrics & Thresholds
 *
 * Implements performance criteria matching Requirement 10 & 13:
 * - 100% valid submissions
 * - HTTP error rate < 1%
 * - P95 response time < 3000ms
 * - P99 response time < 5000ms
 * - Zero lost or duplicate submissions
 * - 100% Organisation ID matching
 */

import { Counter, Trend, Rate } from 'k6/metrics';

// Submission Counters
export const submissionAttempts = new Counter('niwi_submission_attempts');
export const submissionSuccess  = new Counter('niwi_submission_success');
export const submissionFailures = new Counter('niwi_submission_failures');
export const duplicateDetected  = new Counter('niwi_duplicate_detected');
export const validationFailures = new Counter('niwi_validation_failures');

// Granular Latency Trends (ms)
export const submissionDuration    = new Trend('niwi_submission_duration_ms');
export const formSectionsDuration   = new Trend('niwi_form_sections_duration_ms');
export const orgValidationDuration  = new Trend('niwi_org_validation_duration_ms');
export const auditPageDuration      = new Trend('niwi_audit_page_duration_ms');

// Reliability Rates
export const httpErrorRate   = new Rate('niwi_http_error_rate');
export const orgIdMatchRate  = new Rate('niwi_org_id_match_rate');

// ---------------------------------------------------------------------------
// Standard Acceptance Thresholds (Requirement 13)
// ---------------------------------------------------------------------------
export const STANDARD_THRESHOLDS = {
  // Global HTTP failure rate must stay below 1%
  'http_req_failed': ['rate<0.01'],

  // Response time targets
  'http_req_duration': ['p(95)<3000', 'p(99)<5000'],

  // Zero lost submissions (every valid attempt must succeed)
  'niwi_submission_failures': ['count==0'],

  // Every submission must strictly bind to the verified target organisation ID
  'niwi_org_id_match_rate': ['rate==1.0'],

  // Custom submission endpoint latency
  'niwi_submission_duration_ms': ['p(95)<3000', 'p(99)<5000'],
};


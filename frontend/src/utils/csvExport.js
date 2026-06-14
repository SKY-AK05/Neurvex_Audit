/**
 * csvExport.js — Detailed CSV export for NIWI audit submissions
 * Includes: respondent info, all 40 Q&A responses with question text, section scores, overall score
 */

// Full question labels matching AuditForm.vue sections
const QUESTION_LABELS = {
  q5:  "LC1 – Strategy & Direction",
  q6:  "LC2 – Executive Accountability",
  q7:  "LC3 – Leadership Training & Modelling",
  q8:  "LC4 – Employee Resource Group",
  q9:  "LC5 – Public Commitment",
  q10: "RO1 – Inclusive Job Design",
  q11: "RO2 – Transparent Application Process",
  q12: "RO3 – Skills-Based Assessment",
  q13: "RO4 – Flexible Interviews",
  q14: "RO5 – Structured Onboarding",
  q15: "WE1 – Lifecycle Adjustments",
  q16: "WE2 – Clear Adjustment Pathways",
  q17: "WE3 – Manager & HR Training",
  q18: "WE4 – Built-In Inclusive Practices",
  q19: "WE5 – Regular Policy Review",
  q20: "BE1 – Universal Design Principles",
  q21: "BE2 – Sensory Impact Consideration",
  q22: "BE3 – Varied Workspaces",
  q23: "BE4 – Quiet & Low-Stimulation Spaces",
  q24: "BE5 – Hybrid & Remote Balance",
  q25: "TM1 – Inclusive Leadership Training",
  q26: "TM2 – Structured Feedback",
  q27: "TM3 – Wellbeing & Coaching Support",
  q28: "TM4 – Accessible Learning & Development",
  q29: "TM5 – Strengths-Based Development",
  q30: "CA1 – Neuro-Inclusive Communication",
  q31: "CA2 – Clear & Structured Communication",
  q32: "CA3 – Accessible Formats",
  q33: "CA4 – Inclusive Language",
  q34: "CA5 – Feedback & Improvement",
  q35: "PC1 – Neuro-Inclusive Design",
  q36: "PC2 – Multiple Contact Channels",
  q37: "PC3 – Sensory-Aware Environments",
  q38: "PC4 – Staff Neurodiversity Training",
  q39: "PC5 – Regular Inclusivity Assessment",
  q40: "SP1 – Neuro-Inclusive Supplier Comms",
  q41: "SP2 – Inclusive Procurement Criteria",
  q42: "SP3 – Procurement Staff Training",
  q43: "SP4 – Multiple Supplier Contact Methods",
  q44: "SP5 – Supplier Feedback Mechanisms",
};

const SECTION_SCORE_LABELS = {
  lc: "Leadership & Culture",
  ro: "Recruitment & Onboarding",
  we: "Work Environment & Adjustments",
  be: "Built Environment & Sensory",
  tm: "Talent Management & Development",
  ca: "Communication & Accessibility",
  pc: "Products & Customer Experience",
  sp: "Suppliers & Procurement",
};

function escapeCSV(val) {
  if (val === null || val === undefined) return "";
  const str = String(val);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

/**
 * Build CSV rows for one or multiple submissions.
 * Each submission = one row with all fields.
 */
export function buildDetailedCSV(submissions) {
  const headers = [
    // Respondent info
    "Submitted Date",
    "Name",
    "Designation",
    "Organisation",
    "Email",
    "Contact Number",
    "Physical Workspace",
    "Has Suppliers",
    // All 40 questions
    ...Object.values(QUESTION_LABELS),
    // Section scores
    ...Object.values(SECTION_SCORE_LABELS).map(s => `${s} Score`),
    ...Object.values(SECTION_SCORE_LABELS).map(s => `${s} Level`),
    // Overall
    "Overall Score (/20)",
    "Overall Maturity Level",
    "Status",
  ];

  const rows = submissions.map(s => {
    const qAnswers = Object.keys(QUESTION_LABELS).map(qk => s[qk] || "");
    const sectionScores = Object.keys(SECTION_SCORE_LABELS).map(k => s[`${k}_score`] ?? "N/A");
    const sectionLevels = Object.keys(SECTION_SCORE_LABELS).map(k => s[`${k}_level`] || "N/A");

    return [
      formatDate(s.submitted_at),
      s.name || "",
      s.designation || "",
      s.company_name || "",
      s.email || "",
      s.contact_number || "",
      s.has_physical_workspace || "",
      s.has_suppliers || "",
      ...qAnswers,
      ...sectionScores,
      ...sectionLevels,
      s.overall_avg ?? "",
      s.overall_level || "",
      s.status || "",
    ];
  });

  const csvLines = [
    headers.map(escapeCSV).join(","),
    ...rows.map(row => row.map(escapeCSV).join(",")),
  ];

  return csvLines.join("\n");
}

/**
 * Trigger a browser download of a CSV string.
 */
export function downloadCSV(csvString, filename) {
  const blob = new Blob(["\uFEFF" + csvString], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Download a single submission as CSV.
 */
export function downloadSingleSubmission(submission) {
  const csv = buildDetailedCSV([submission]);
  const date = formatDate(submission.submitted_at).replace(/ /g, "-");
  const org = (submission.company_name || "submission").replace(/[^a-z0-9]/gi, "_");
  downloadCSV(csv, `NIWI_${org}_${date}.csv`);
}

/**
 * Download multiple submissions as CSV with optional date range label.
 */
export function downloadFilteredSubmissions(submissions, dateFrom, dateTo) {
  const csv = buildDetailedCSV(submissions);
  const from = dateFrom || "all";
  const to = dateTo || "time";
  downloadCSV(csv, `NIWI_submissions_${from}_to_${to}.csv`);
}

"""
org_scoring_service.py — Weighted multi-respondent org scoring.

All functions are pure (no DB calls). The caller fetches the data and
passes it in; these functions just crunch numbers and build email HTML.
"""

from __future__ import annotations
import html as html_module
from typing import Any

SECTION_KEYS = ["lc", "ro", "we", "be", "tm", "ca", "pc", "sp"]
SECTION_LABELS = {
    "lc": "Leadership & Culture",
    "ro": "Recruitment & Onboarding",
    "we": "Work Environment & Adjustments",
    "be": "Built Environment & Sensory",
    "tm": "Talent Management & Development",
    "ca": "Communication & Accessibility",
    "pc": "Products & Customer Experience",
    "sp": "Suppliers & Procurement",
}

LEVEL_THRESHOLDS = [
    (0,  6,  "Level 1 — Foundational"),
    (7,  14, "Level 2 — Early Progress"),
    (15, 20, "Level 3 — Developing"),
]


def _level(score: float) -> str:
    for lo, hi, label in LEVEL_THRESHOLDS:
        if lo <= score <= hi:
            return label
    return "Level 3 — Developing"


def calc_weighted_org_score(links: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    links — list of dicts, each containing:
        overall_avg   float
        weight        float
        lc_score … sp_score  int
        name, email, designation, submitted_at, id  (passed through)

    Returns a dict with:
        org_avg         float
        org_level       str
        respondent_count int
        section_avgs    {lc: float, ro: float, …}
        section_levels  {lc: str, …}
        respondents     list (original links, enriched with weighted_contribution %)
    """
    if not links:
        return None

    total_weight = sum(float(l.get("weight", 1.0)) for l in links)
    if total_weight == 0:
        return None

    org_avg = sum(
        float(l.get("overall_avg") or 0) * float(l.get("weight", 1.0))
        for l in links
    ) / total_weight

    section_avgs: dict[str, float] = {}
    for key in SECTION_KEYS:
        col = f"{key}_score"
        section_avgs[key] = sum(
            float(l.get(col) or 0) * float(l.get("weight", 1.0))
            for l in links
        ) / total_weight

    section_levels = {k: _level(v) for k, v in section_avgs.items()}

    # Enrich each respondent with their weighted contribution %
    respondents = []
    for l in links:
        w = float(l.get("weight", 1.0))
        respondents.append({
            **l,
            "weighted_contribution_pct": round((w / total_weight) * 100, 1),
        })

    return {
        "org_avg": round(org_avg, 2),
        "org_level": _level(org_avg),
        "respondent_count": len(links),
        "total_weight": total_weight,
        "section_avgs": {k: round(v, 2) for k, v in section_avgs.items()},
        "section_levels": section_levels,
        "respondents": respondents,
    }


def build_org_summary_email(
    org_name: str,
    scores: dict[str, Any],
    respondents: list[dict[str, Any]],
) -> str:
    """
    Build the HTML body for the org summary email.
    scores — output of calc_weighted_org_score()
    respondents — same list (already inside scores["respondents"])
    """

    def _e(v: Any) -> str:
        return html_module.escape(str(v)) if v is not None else ""

    org_avg   = scores["org_avg"]
    org_level = scores["org_level"]
    sec_avgs  = scores["section_avgs"]
    sec_lvls  = scores["section_levels"]

    # Respondent rows
    respondent_rows = ""
    for r in respondents:
        respondent_rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;">{_e(r.get('name'))}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;color:#666;">{_e(r.get('designation'))}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;text-align:center;font-weight:700;">
            {_e(r.get('overall_avg'))}/20
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;text-align:center;color:#666;">
            {_e(r.get('weight'))}×
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;text-align:center;color:#009070;font-weight:600;">
            {_e(r.get('weighted_contribution_pct'))}%
          </td>
        </tr>"""

    # Section rows
    section_rows = ""
    for key in SECTION_KEYS:
        label = SECTION_LABELS[key]
        avg   = sec_avgs.get(key, 0)
        lvl   = sec_lvls.get(key, "")
        bar_w = min(int((avg / 20) * 100), 100)
        section_rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;font-weight:600;">{_e(label)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;text-align:center;font-weight:700;">{avg}/20</td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;">
            <div style="background:#E2DDD4;border-radius:4px;height:8px;width:100%;">
              <div style="background:#009070;border-radius:4px;height:8px;width:{bar_w}%;"></div>
            </div>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;color:#666;font-size:0.85em;">{_e(lvl)}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>NeuroMark Org Summary — {_e(org_name)}</title>
</head>
<body style="margin:0;padding:0;background:#F5F2EB;font-family:'DM Sans',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
  <tr><td align="center" style="padding:40px 20px;">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#120050;border-radius:16px 16px 0 0;">
      <tr><td style="padding:36px 40px;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:2px;color:#AFA9EC;text-transform:uppercase;">Orchvate</p>
        <h1 style="margin:0 0 6px;font-size:26px;font-weight:400;color:#FFFFFF;font-family:Georgia,serif;">
          Organisation Audit Summary
        </h1>
        <p style="margin:0;font-size:14px;color:#AFA9EC;">{_e(org_name)}</p>
      </td></tr>
    </table>

    <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-left:1px solid #E2DDD4;border-right:1px solid #E2DDD4;">
      <!-- Overall score -->
      <tr><td style="padding:32px 40px 0;">
        <p style="margin:0 0 4px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#999;">Overall Weighted Score</p>
        <p style="margin:0;font-size:42px;font-weight:800;color:#120050;">{org_avg}<span style="font-size:20px;color:#999;">/20</span></p>
        <p style="margin:4px 0 0;font-size:14px;color:#009070;font-weight:700;">{_e(org_level)}</p>
      </td></tr>

      <!-- Respondents table -->
      <tr><td style="padding:28px 40px 0;">
        <p style="margin:0 0 12px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#120050;">Respondents</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <thead>
            <tr style="background:#F5F2EB;">
              <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Name</th>
              <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Role</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Score</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Weight</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Contribution</th>
            </tr>
          </thead>
          <tbody>{respondent_rows}</tbody>
        </table>
      </td></tr>

      <!-- Section breakdown -->
      <tr><td style="padding:28px 40px 0;">
        <p style="margin:0 0 12px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#120050;">Section Breakdown</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <thead>
            <tr style="background:#F5F2EB;">
              <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Section</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Avg</th>
              <th style="padding:8px 12px;font-size:11px;color:#999;width:160px;"></th>
              <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Level</th>
            </tr>
          </thead>
          <tbody>{section_rows}</tbody>
        </table>
      </td></tr>

      <tr><td style="padding:32px 40px;">
        <p style="margin:0;font-size:12px;color:#aaa;text-align:center;border-top:1px solid #E2DDD4;padding-top:20px;">
          Powered by Orchvate · NeuroMark Audit Platform
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""

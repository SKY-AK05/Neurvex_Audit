"""
scoring.py — Neurvex Audit scoring logic
Imported by function_app.py
"""

import html as html_module
import math
import json
import urllib.parse
from datetime import datetime, timezone

ANSWER_POINTS = {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}

SECTIONS = {
    "lc": {"label": "Leadership & Culture",              "questions": [f"q{i}" for i in range(5, 10)]},
    "ro": {"label": "Recruitment & Onboarding",          "questions": [f"q{i}" for i in range(10, 15)]},
    "we": {"label": "Work Environment & Adjustments",    "questions": [f"q{i}" for i in range(15, 20)]},
    "be": {"label": "Built Environment & Sensory",       "questions": [f"q{i}" for i in range(20, 25)]},
    "tm": {"label": "Talent Management & Development",   "questions": [f"q{i}" for i in range(25, 30)]},
    "ca": {"label": "Communication & Accessibility",     "questions": [f"q{i}" for i in range(30, 35)]},
    "pc": {"label": "Products & Customer Experience",    "questions": [f"q{i}" for i in range(35, 40)]},
    "sp": {"label": "Suppliers & Procurement",           "questions": [f"q{i}" for i in range(40, 45)]},
}

def get_maturity_level(score: int) -> str:
    if score <= 6:
        return "Level 1 — Foundational"
    elif score <= 14:
        return "Level 2 — Early Progress"
    else:
        return "Level 3 — Developing"

# Pre-written interpretations: section_key -> [level1_text, level2_text, level3_text]
INTERPRETATIONS = {
    "lc": [
        "Your organisation is at the very beginning of its neurodiversity inclusion journey in leadership and culture. "
        "There is limited awareness or commitment at a senior level, and neurodiversity is not yet embedded in your values or strategy. "
        "We recommend starting with leadership education and awareness sessions to build the foundation.",

        "Your organisation has begun to acknowledge neurodiversity within its leadership and culture, with some early initiatives in place. "
        "However, these efforts are not yet consistent or fully embedded. "
        "Focus on formalising commitments, creating visible role models, and building a culture where neurodivergent employees feel safe to disclose.",

        "Your organisation demonstrates a strong and developing commitment to neurodiversity inclusion at a leadership and cultural level. "
        "Senior leaders are engaged, and inclusion is becoming part of your organisational identity. "
        "Continue to build on this by measuring impact, sharing success stories, and embedding inclusion into all strategic decisions.",
    ],
    "ro": [
        "Your recruitment and onboarding processes are not yet designed with neurodivergent candidates in mind. "
        "Standard processes may unintentionally exclude talented individuals. "
        "We recommend reviewing job descriptions, interview formats, and onboarding materials to remove unnecessary barriers.",

        "You have made some adjustments to your recruitment and onboarding to be more inclusive, but there is room to go further. "
        "Consider offering alternative interview formats, providing information in advance, and ensuring onboarding is structured and clear for all new starters.",

        "Your recruitment and onboarding practices show a strong commitment to neurodiversity inclusion. "
        "You are actively removing barriers and creating a welcoming experience for neurodivergent candidates. "
        "Keep reviewing and iterating based on feedback from neurodivergent employees.",
    ],
    "we": [
        "Your work environment and adjustment processes are at an early stage. "
        "Neurodivergent employees may be struggling without the support they need. "
        "Prioritise creating a clear, accessible process for requesting adjustments and raise awareness among managers.",

        "Some adjustments and flexible working options are available, but access may be inconsistent. "
        "Ensure all employees know how to request support, and that managers are equipped to respond positively and promptly.",

        "Your organisation provides a supportive and flexible work environment with clear adjustment processes. "
        "Neurodivergent employees are more likely to thrive here. "
        "Continue to gather feedback and ensure adjustments are reviewed regularly.",
    ],
    "be": [
        "The physical and sensory environment has not yet been considered from a neurodiversity perspective. "
        "Sensory overload, poor lighting, or open-plan noise may be significant barriers. "
        "We recommend a sensory audit of your spaces and exploring low-cost adjustments.",

        "Some consideration has been given to the built environment, but there are gaps. "
        "Look at quiet spaces, lighting options, and signage to make your environment more accessible to neurodivergent individuals.",

        "Your built environment demonstrates thoughtful design with neurodivergent needs in mind. "
        "You are providing sensory-friendly spaces and clear navigation. "
        "Continue to involve neurodivergent employees in future design decisions.",
    ],
    "tm": [
        "Talent management and development processes do not yet account for neurodivergent strengths and needs. "
        "Performance frameworks and career pathways may inadvertently disadvantage neurodivergent employees. "
        "Review your appraisal and development processes for hidden barriers.",

        "You are beginning to adapt talent management processes to be more inclusive, but consistency is needed. "
        "Ensure that neurodivergent employees have equal access to development opportunities and that their strengths are recognised.",

        "Your talent management and development approach is inclusive and strengths-based. "
        "Neurodivergent employees are supported to grow and progress. "
        "Share your approach internally and consider how it can be further embedded across the employee lifecycle.",
    ],
    "ca": [
        "Communication and accessibility practices are not yet adapted for neurodivergent needs. "
        "Information may be hard to process, and meetings or written communications may create unnecessary barriers. "
        "Start by reviewing how information is shared and offering alternative formats.",

        "Some accessible communication practices are in place, but they are not applied consistently. "
        "Focus on plain language, clear structure, and offering multiple formats to ensure all employees can access information equally.",

        "Your communication and accessibility practices are strong and inclusive. "
        "You are proactively considering how information is shared and ensuring it works for everyone. "
        "Continue to review and update practices as understanding of neurodiversity evolves.",
    ],
    "pc": [
        "Neurodiversity inclusion has not yet been considered in your products or customer experience. "
        "Neurodivergent customers may face barriers when interacting with your services. "
        "We recommend an accessibility review of your customer-facing products and communications.",

        "Some steps have been taken to make products and customer experiences more accessible, but there is more to do. "
        "Involve neurodivergent users in testing and feedback to identify and remove barriers.",

        "Your products and customer experience reflect a genuine commitment to accessibility and inclusion. "
        "Neurodivergent customers are considered in your design and delivery. "
        "Continue to co-design with neurodivergent users and stay current with accessibility standards.",
    ],
    "sp": [
        "Neurodiversity inclusion is not yet part of your supplier or procurement criteria. "
        "This is an opportunity to extend your inclusion values through your supply chain. "
        "Consider adding neurodiversity inclusion questions to your supplier assessments.",

        "You are beginning to consider neurodiversity in your supplier relationships, but this is not yet formalised. "
        "Develop clear criteria and communicate your expectations to suppliers.",

        "Your procurement and supplier processes actively promote neurodiversity inclusion. "
        "You are using your purchasing power to drive positive change. "
        "Continue to review supplier performance against inclusion criteria and share best practice.",
    ],
}

OVERALL_SYNOPSIS = [
    "Your organisation is at the start of its neurodiversity inclusion journey. "
    "There is significant opportunity to build awareness, remove barriers, and create a more inclusive environment. "
    "We recommend beginning with leadership education and a structured inclusion plan. "
    "Orchvate is here to support you every step of the way.",

    "Your organisation has made meaningful early progress on neurodiversity inclusion. "
    "There are pockets of good practice, but consistency and embedding are the next steps. "
    "With focused effort across the key areas, you can build a genuinely inclusive culture. "
    "Orchvate can help you prioritise and accelerate your progress.",

    "Your organisation is developing a strong foundation for neurodiversity inclusion. "
    "You are ahead of many organisations and have much to be proud of. "
    "The focus now is on embedding, measuring impact, and continuing to improve. "
    "Orchvate can support you in reaching and sustaining best practice.",
]


def score_answer(answer: str) -> int:
    return ANSWER_POINTS.get(answer, 0)


def score_section(answers: dict, question_keys: list) -> int:
    return sum(score_answer(answers.get(k, "")) for k in question_keys)


def calculate_scores(data: dict) -> dict:
    """
    Takes the raw form data dict (q5–q44 + respondent fields).
    Returns a dict with all section scores, levels, overall avg, overall level,
    and the generated email body.
    """
    result = {}
    section_scores = []

    for key, section in SECTIONS.items():
        score = score_section(data, section["questions"])
        level = get_maturity_level(score)
        result[f"{key}_score"] = score
        result[f"{key}_level"] = level
        section_scores.append((key, section["label"], score, level))

    overall_avg = round(sum(s[2] for s in section_scores) / len(section_scores), 2)
    overall_level = get_maturity_level(int(overall_avg))
    result["overall_avg"] = overall_avg
    result["overall_level"] = overall_level

    result["email_body"] = build_email(
        name=data.get("name", ""),
        designation=data.get("designation", ""),
        company_name=data.get("company_name", ""),
        section_scores=section_scores,
        overall_avg=overall_avg,
        overall_level=overall_level,
    )

    return result


def _e(text: str) -> str:
    return html_module.escape(str(text))


def build_email(name: str, designation: str, company_name: str, section_scores: list,
                overall_avg: float, overall_level: str) -> str:
    """Build a formatted HTML email body for the rich-text editor and ACS send."""
    level_index = {"Level 1 — Foundational": 0, "Level 2 — Early Progress": 1, "Level 3 — Developing": 2}

    # Extract dynamic level numbers and descriptions
    level_parts = overall_level.split(" — ")
    if len(level_parts) < 2:
        level_parts = overall_level.split(" - ")
    level_desc_str = level_parts[1].strip() if len(level_parts) >= 2 else "Early Progress"

    if overall_avg <= 6:
        active_level = 1
    elif overall_avg <= 14:
        active_level = 2
    else:
        active_level = 3

    overall_avg_display = f"{overall_avg:g}"
    dash = round((overall_avg / 20.0) * 226.2, 1)
    synopsis = OVERALL_SYNOPSIS[level_index.get(overall_level, 0)]
    month_year = datetime.now(timezone.utc).strftime("%B %Y")

    # Calculate domains subtitle dynamically based on section scores
    levels_set = {s[3] for s in section_scores}
    if len(levels_set) == 1:
        # e.g., "Level 2 — Early Progress" -> "All at Level 2"
        common_level_parts = list(levels_set)[0].split(" — ")
        if len(common_level_parts) < 2:
            common_level_parts = list(levels_set)[0].split(" - ")
        common_lvl_num = common_level_parts[0].replace("Level ", "").strip()
        domains_subtitle = f"All at Level {common_lvl_num}"
    else:
        domains_subtitle = "8 domains assessed"

    # Generate QuickChart URL for the radar chart
    labels = ["Leadership & Culture", "Recruitment & Onboarding", "Work Environment", "Built Environment", "Talent Management", "Communication", "Products & CX", "Suppliers & Procurement"]
    scores = [s[2] for s in section_scores]
    
    chart_config = {
        "type": "radar",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "Score",
                "data": scores,
                "backgroundColor": "rgba(127, 119, 221, 0.15)",
                "borderColor": "#7F77DD",
                "pointBackgroundColor": "#7F77DD",
                "pointBorderColor": "#fff",
                "pointRadius": 4,
                "borderWidth": 2
            }]
        },
        "options": {
            "scale": {
                "ticks": {
                    "beginAtZero": True,
                    "max": 20,
                    "stepSize": 5,
                    "display": False
                },
                "pointLabels": {
                    "fontSize": 11,
                    "fontColor": "#555",
                    "fontFamily": "sans-serif"
                }
            },
            "legend": {"display": False}
        }
    }
    
    encoded_config = urllib.parse.quote(json.dumps(chart_config))
    quickchart_url = f"https://quickchart.io/chart?w=500&h=340&v=2&c={encoded_config}"

    # Generate dynamic metric progress bar
    fill_pct = int((overall_avg / 20.0) * 100)
    empty_pct = 100 - fill_pct
    if fill_pct == 100:
        overall_progress_tds = '<td width="100%" height="5" style="background:#7F77DD;border-radius:3px;font-size:0;">&nbsp;</td>'
    elif fill_pct == 0:
        overall_progress_tds = '<td width="100%" height="5" style="background:#E0DDD8;border-radius:3px;font-size:0;">&nbsp;</td>'
    else:
        overall_progress_tds = (
            f'<td width="{fill_pct}%" height="5" style="background:#7F77DD;border-radius:3px 0 0 3px;font-size:0;">&nbsp;</td>'
            f'<td width="{empty_pct}%" height="5" style="background:#E0DDD8;border-radius:0 3px 3px 0;font-size:0;">&nbsp;</td>'
        )

    # Generate dynamic segment cards
    segment_cards = []
    for key, label, score, level in section_scores:
        idx = level_index.get(level, 0)
        interpretation = INTERPRETATIONS[key][idx]
        fill_w = int((score / 20.0) * 100)
        empty_w = 100 - fill_w
        
        if fill_w == 100:
            bar_tds = '<td width="100%" height="4" style="background:#7F77DD;border-radius:3px;font-size:0;">&nbsp;</td>'
        elif fill_w == 0:
            bar_tds = '<td width="100%" height="4" style="background:#E0DDD8;border-radius:3px;font-size:0;">&nbsp;</td>'
        else:
            bar_tds = (
                f'<td width="{fill_w}%" height="4" style="background:#7F77DD;border-radius:3px 0 0 3px;font-size:0;">&nbsp;</td>'
                f'<td width="{empty_w}%" height="4" style="background:#E0DDD8;border-radius:0 3px 3px 0;font-size:0;">&nbsp;</td>'
            )

        segment_cards.append(f"""
    <!-- SEGMENT: {label} -->
    <tr><td style="background:#FFFFFF;padding:0 40px 12px;">
      <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#F9F8FF;border-radius:10px;overflow:hidden;">
        <tr>
          <td style="padding:14px 16px;">
            <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
              <tr>
                <td>
                  <p style="margin:0 0 2px;font-family:\'DM Sans\',Arial,sans-serif;font-size:13px;font-weight:600;color:#1E1A4A;">{_e(label)}</p>
                  <!-- bar -->
                  <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="margin:6px 0 8px;"><tr>
                    {bar_tds}
                  </tr></table>
                  <p style="margin:0;font-family:\'DM Sans\',Arial,sans-serif;font-size:12px;color:#555;line-height:1.6;">{_e(interpretation)}</p>
                </td>
                <td width="52" valign="top" align="right" style="padding-left:12px;">
                  <span style="display:inline-block;background:#EEEDFE;color:#534AB7;font-family:\'DM Sans\',Arial,sans-serif;font-size:12px;font-weight:600;padding:4px 8px;border-radius:6px;white-space:nowrap;">{score} / 20</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </td></tr>
""")

    # Generate maturity scale HTML
    scale_levels = [
        {"num": 1, "name": "Starting out", "color": "#D3D1C7", "text_color": "#888", "weight": "normal", "label": "Level 1<br>Starting out"},
        {"num": 2, "name": "Early Progress", "color": "#D3D1C7", "text_color": "#888", "weight": "normal", "label": "Level 2<br>Early Progress"},
        {"num": 3, "name": "Developing", "color": "#D3D1C7", "text_color": "#888", "weight": "normal", "label": "Level 3<br>Developing"},
        {"num": 4, "name": "Advanced", "color": "#D3D1C7", "text_color": "#888", "weight": "normal", "label": "Level 4<br>Advanced"},
        {"num": 5, "name": "Leading", "color": "#D3D1C7", "text_color": "#888", "weight": "normal", "label": "Level 5<br>Leading"},
    ]
    for lvl in scale_levels:
        if lvl["num"] == active_level:
            lvl["color"] = "#7F77DD"
            lvl["text_color"] = "#534AB7"
            lvl["weight"] = "600"
            lvl["label"] = f'Level {lvl["num"]} ← You<br>{lvl["name"]}'

    scale_html = []
    for lvl in scale_levels:
        scale_html.append(f"""
          <td width="20%" align="center" style="padding:0 3px;">
            <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
              <tr><td height="6" style="background:{lvl["color"]};border-radius:3px;font-size:0;">&nbsp;</td></tr>
              <tr><td style="padding-top:5px;font-family:'DM Sans',Arial,sans-serif;font-size:10px;color:{lvl["text_color"]};font-weight:{lvl["weight"]};text-align:center;">{lvl["label"]}</td></tr>
            </table>
          </td>
        """)
    scale_row_html = "\n".join(scale_html)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Neurvex Audit — {_e(company_name)}</title>
<!--[if mso]>
<noscript>
<xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml>
</noscript>
<![endif]-->
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap');
  body {{ margin: 0; padding: 0; background-color: #F4F2F0; font-family: 'DM Sans', Arial, sans-serif; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
  table {{ border-collapse: collapse; mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
  img {{ border: 0; outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; display: block; }}
  a {{ color: #534AB7; text-decoration: none; }}

  /* Radar chart */
  .radar-label {{ font-family: 'DM Sans', Arial, sans-serif; font-size: 10px; fill: #888; }}
  .radar-axis {{ stroke: #E0DDD8; stroke-width: 1; }}
  .radar-ring {{ fill: none; stroke: #E0DDD8; stroke-width: 0.8; }}
  .radar-area {{ fill: rgba(127,119,221,0.15); stroke: #7F77DD; stroke-width: 2; }}
  .radar-dot {{ fill: #7F77DD; stroke: #fff; stroke-width: 2; }}
  .bar-bg {{ fill: #EAE8E3; }}
  .bar-fill {{ fill: #7F77DD; }}

  @media only screen and (max-width: 620px) {{
    .email-wrapper {{ width: 100% !important; }}
    .metric-cell {{ display: block !important; width: 100% !important; margin-bottom: 10px; }}
    .metric-table {{ width: 100% !important; }}
    .seg-icon-cell {{ display: none; }}
  }}
</style>
</head>
<body style="margin:0;padding:0;background-color:#FFFFFF;">

<!-- Preheader -->
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;">Your Neurvex Audit results for {_e(company_name)} — {_e(overall_level)} ({overall_avg_display}/20) &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;</div>

<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#FFFFFF;">
<tr><td align="center" style="padding: 24px 0 48px;">

  <!-- Email wrapper -->
  <table class="email-wrapper" width="600" cellpadding="0" cellspacing="0" role="presentation" style="max-width:600px;width:100%;">

    <!-- ─── HEADER ─── -->
    <tr><td style="background:#1E1A4A;border-radius:16px 16px 0 0;padding:36px 40px 32px;">
      <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
        <tr>
          <td>
            <!-- Logo / wordmark -->
            <p style="margin:0 0 20px;font-family:'DM Sans',Arial,sans-serif;font-size:13px;font-weight:600;letter-spacing:2px;color:#AFA9EC;text-transform:uppercase;">Orchvate</p>
            <h1 style="margin:0 0 6px;font-family:'DM Serif Display',Georgia,serif;font-size:28px;font-weight:400;color:#FFFFFF;line-height:1.2;">Neurodiversity<br>Neurvex Audit</h1>
            <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:14px;color:#AFA9EC;">{_e(name)} &nbsp;·&nbsp; {_e(designation) + ' · ' if designation else ''}{_e(company_name)} &nbsp;·&nbsp; {month_year}</p>
          </td>
          <td width="100" align="right" valign="top">
            <!-- Score circle -->
            <svg width="84" height="84" viewBox="0 0 84 84" xmlns="http://www.w3.org/2000/svg" aria-label="Score {overall_avg_display} out of 20">
              <circle cx="42" cy="42" r="36" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="6"/>
              <circle cx="42" cy="42" r="36" fill="none" stroke="#7F77DD" stroke-width="6"
                stroke-dasharray="{dash} 226.2" stroke-dashoffset="0"
                stroke-linecap="round" transform="rotate(-90 42 42)"/>
              <text x="42" y="38" text-anchor="middle" font-family="'DM Sans',Arial,sans-serif" font-size="18" font-weight="600" fill="#FFFFFF">{overall_avg_display}</text>
              <text x="42" y="52" text-anchor="middle" font-family="'DM Sans',Arial,sans-serif" font-size="10" fill="#AFA9EC">of 20</text>
            </svg>
          </td>
        </tr>
      </table>
    </td></tr>

    <!-- ─── GREETING ─── -->
    <tr><td style="background:#FFFFFF;padding:28px 40px 0;">
      <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:15px;color:#444;line-height:1.6;">Dear <strong style="color:#1E1A4A;">{_e(name)}</strong>{(' (' + _e(designation) + ')') if designation else ''},<br>Thank you for completing the Neurvex Audit. Here is a summary of your results.</p>
    </td></tr>

    <!-- ─── METRIC CARDS ─── -->
    <tr><td style="background:#FFFFFF;padding:20px 40px 24px;">
      <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
        <tr>
          <td class="metric-cell" width="33%" valign="top" style="padding-right:8px;">
            <table class="metric-table" width="100%" cellpadding="0" cellspacing="0" role="presentation">
              <tr><td style="background:#F4F2F0;border-radius:10px;padding:14px 16px;">
                <p style="margin:0 0 4px;font-family:'DM Sans',Arial,sans-serif;font-size:11px;color:#888;letter-spacing:0.5px;text-transform:uppercase;">Overall score</p>
                <p style="margin:0 0 8px;font-family:'DM Serif Display',Georgia,serif;font-size:24px;color:#1E1A4A;">{overall_avg_display} / 20</p>
                <!-- mini bar -->
                <table width="100%" cellpadding="0" cellspacing="0" role="presentation"><tr>
                  {overall_progress_tds}
                </tr></table>
              </td></tr>
            </table>
          </td>
          <td class="metric-cell" width="33%" valign="top" style="padding:0 4px;">
            <table class="metric-table" width="100%" cellpadding="0" cellspacing="0" role="presentation">
              <tr><td style="background:#F4F2F0;border-radius:10px;padding:14px 16px;">
                <p style="margin:0 0 4px;font-family:'DM Sans',Arial,sans-serif;font-size:11px;color:#888;letter-spacing:0.5px;text-transform:uppercase;">Maturity level</p>
                <p style="margin:0 0 4px;font-family:'DM Serif Display',Georgia,serif;font-size:22px;color:#1E1A4A;">Level {active_level}</p>
                <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:12px;color:#7F77DD;font-weight:600;">{_e(level_desc_str)}</p>
              </td></tr>
            </table>
          </td>
          <td class="metric-cell" width="33%" valign="top" style="padding-left:8px;">
            <table class="metric-table" width="100%" cellpadding="0" cellspacing="0" role="presentation">
              <tr><td style="background:#F4F2F0;border-radius:10px;padding:14px 16px;">
                <p style="margin:0 0 4px;font-family:'DM Sans',Arial,sans-serif;font-size:11px;color:#888;letter-spacing:0.5px;text-transform:uppercase;">Segments assessed</p>
                <p style="margin:0 0 4px;font-family:'DM Serif Display',Georgia,serif;font-size:24px;color:#1E1A4A;">8</p>
                <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:12px;color:#888;">{domains_subtitle}</p>
              </td></tr>
            </table>
          </td>
        </tr>
      </table>
    </td></tr>

    <!-- ─── SYNOPSIS ─── -->
    <tr><td style="background:#FFFFFF;padding:0 40px 28px;">
      <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
        <tr>
          <td width="4" style="background:#7F77DD;border-radius:4px;">&nbsp;</td>
          <td style="padding:14px 16px;background:#F7F6FF;border-radius:0 10px 10px 0;">
            <p style="margin:0 0 4px;font-family:'DM Sans',Arial,sans-serif;font-size:11px;font-weight:600;color:#7F77DD;letter-spacing:0.5px;text-transform:uppercase;">Inclusion Progress Summary</p>
            <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:14px;color:#444;line-height:1.7;">{_e(synopsis)}</p>
          </td>
        </tr>
      </table>
    </td></tr>

    <!-- ─── RADAR CHART ─── -->
    <tr><td style="background:#FFFFFF;padding:0 40px 32px;">
      <p style="margin:0 0 16px;font-family:'DM Sans',Arial,sans-serif;font-size:14px;font-weight:600;color:#1E1A4A;letter-spacing:0.2px;">Scores by segment</p>

      <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
        <tr><td align="center">
          <img src="{quickchart_url}" width="500" height="340" style="max-width:100%;height:auto;display:block;margin:0 auto;" alt="Radar chart showing segment scores">
        </td></tr>
      </table>
    </td></tr>

    <!-- ─── SEGMENT BREAKDOWN TITLE ─── -->
    <tr><td style="background:#FFFFFF;padding:0 40px 16px;">
      <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:14px;font-weight:600;color:#1E1A4A;letter-spacing:0.2px;">Segment breakdown</p>
    </td></tr>

    {"".join(segment_cards)}

    <!-- ─── MATURITY SCALE ─── -->
    <tr><td style="background:#FFFFFF;padding:0 40px 32px;">
      <p style="margin:0 0 12px;font-family:'DM Sans',Arial,sans-serif;font-size:14px;font-weight:600;color:#1E1A4A;">Maturity scale</p>
      <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
        <tr>
          {scale_row_html}
        </tr>
      </table>
    </td></tr>

    <!-- ─── CTA ─── -->
    <tr><td style="background:#FFFFFF;padding:0 40px 0;">
      <table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background:#F4F2F0;border-radius:12px;">
        <tr><td style="padding:24px 24px;">
          <p style="margin:0 0 8px;font-family:'DM Sans',Arial,sans-serif;font-size:14px;font-weight:600;color:#1E1A4A;">Explore your next steps</p>
          <p style="margin:0 0 16px;font-family:'DM Sans',Arial,sans-serif;font-size:13px;color:#555;line-height:1.6;">We would be happy to offer a complimentary conversation to walk through these results in more detail, reflect on what they mean for your organisation, and explore what a possible next phase of your neurodiversity inclusion journey could look like.</p>
          <a href="mailto:hello@orchvate.com" style="display:inline-block;background:#1E1A4A;color:#FFFFFF;font-family:'DM Sans',Arial,sans-serif;font-size:13px;font-weight:600;padding:12px 24px;border-radius:8px;text-decoration:none;">Book a complimentary call →</a>
        </td></tr>
      </table>
    </td></tr>

    <!-- ─── FOOTER ─── -->
    <tr><td style="background:#FFFFFF;border-radius:0 0 16px 16px;padding:28px 40px 32px;">
      <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
        <tr>
          <td>
            <p style="margin:0 0 2px;font-family:'DM Sans',Arial,sans-serif;font-size:13px;color:#888;">Best regards,</p>
            <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:13px;font-weight:600;color:#1E1A4A;">The Orchvate Team</p>
          </td>
          <td align="right" valign="bottom">
            <p style="margin:0;font-family:'DM Sans',Arial,sans-serif;font-size:11px;color:#bbb;">orchvate.com</p>
          </td>
        </tr>
      </table>
    </td></tr>

    <!-- Bottom gap -->
    <tr><td height="8" style="background:#FFFFFF;">&nbsp;</td></tr>

  </table>

</td></tr>
</table>

</body>
</html>"""
    return html_content

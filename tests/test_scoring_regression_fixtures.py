"""
test_scoring_regression_fixtures.py — Comprehensive regression fixtures
Guarantees 100% exact numerical match for scoring formulas (CALC-001 through CALC-014).
"""
import pytest
from app.services.scoring_service import (
    calculate_scores,
    score_section,
    get_maturity_level,
    DEFAULT_STANDARD_SECTIONS,
)
from app.services.org_scoring_service import calc_weighted_org_score, _level


class TestScoringRegressionFixtures:
    """Fixture tests enforcing strict mathematical equivalence for all scoring rules."""

    def test_fixture_1_max_possible_scores(self):
        """All 'Yes' answers produce exactly 20.00 in each section and 20.00 overall."""
        data = {f"q{i}": "Yes" for i in range(5, 45)}
        data.update({
            "has_physical_workspace": "Yes",
            "has_suppliers": "Yes",
            "name": "Jane Doe",
            "company_name": "Acme Corp",
            "email": "jane@acme.com"
        })
        scores = calculate_scores(data)

        for dim in ["lc", "ro", "we", "be", "tm", "ca", "pc", "sp"]:
            assert scores[f"{dim}_score"] == 20.0, f"Failed on {dim}"
            assert scores[f"{dim}_level"] == "Level 3 — Developing"
        assert scores["overall_avg"] == 20.0
        assert scores["overall_level"] == "Level 3 — Developing"
        assert len(scores["low_visibility_sections"]) == 0

    def test_fixture_2_min_possible_scores(self):
        """All 'No' answers produce 0.00 across all dimensions."""
        data = {f"q{i}": "No" for i in range(5, 45)}
        data.update({
            "has_physical_workspace": "Yes",
            "has_suppliers": "Yes",
            "name": "John Doe",
            "company_name": "Acme Corp",
            "email": "john@acme.com"
        })
        scores = calculate_scores(data)

        for dim in ["lc", "ro", "we", "be", "tm", "ca", "pc", "sp"]:
            assert scores[f"{dim}_score"] == 0.0
            assert scores[f"{dim}_level"] == "Level 1 — Foundational"
        assert scores["overall_avg"] == 0.0
        assert scores["overall_level"] == "Level 1 — Foundational"
        assert len(scores["low_visibility_sections"]) == 0

    def test_fixture_3_gated_sections(self):
        """has_physical_workspace='No' gates BE; has_suppliers='No' gates SP."""
        data = {f"q{i}": "Yes" for i in range(5, 45)}
        data.update({
            "has_physical_workspace": "No",
            "has_suppliers": "No",
            "name": "Remote Org User",
            "company_name": "Remote Inc",
            "email": "remote@remote.com"
        })
        scores = calculate_scores(data)

        assert scores["be_score"] == "NA"
        assert scores["be_level"] == "Not applicable"
        assert scores["sp_score"] == "NA"
        assert scores["sp_level"] == "Not applicable"

        # 6 valid sections evaluated at 20.0 each -> overall_avg = 20.0
        assert scores["overall_avg"] == 20.0
        assert scores["overall_level"] == "Level 3 — Developing"

    def test_fixture_4_na_rescaling_calc_003(self):
        """If 1 of 5 questions is N/A, section score rescales from /16 to /20."""
        # Section lc: q5..q9
        qs = [
            {"field_name": "q5", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}},
            {"field_name": "q6", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}},
            {"field_name": "q7", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}},
            {"field_name": "q8", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}},
            {"field_name": "q9", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}},
        ]
        # 4 questions answered Yes (4x4=16 pts out of 16 max applicable). Rescales to 20.0.
        data = {"q5": "Yes", "q6": "Yes", "q7": "Yes", "q8": "Yes", "q9": "N/A"}
        score, not_sure, n_app = score_section(data, "lc", qs)
        assert n_app == 4
        assert not_sure == 0
        assert score == 20.0

        # 3 questions Yes (12 pts), 1 question Partially (2 pts) out of 16 max applicable.
        # 14 / 16 * 20 = 17.5
        data2 = {"q5": "Yes", "q6": "Yes", "q7": "Yes", "q8": "Partially", "q9": "N/A"}
        score2, not_sure2, n_app2 = score_section(data2, "lc", qs)
        assert score2 == 17.5

    def test_fixture_5_low_visibility_calc_004(self):
        """If >= 50% of applicable questions are 'Not Sure', section is flagged low visibility."""
        data = {f"q{i}": "Yes" for i in range(5, 45)}
        # Section ro: q10..q14. Give 3 'Not Sure' answers out of 5
        data["q10"] = "Not Sure"
        data["q11"] = "Not Sure"
        data["q12"] = "Not Sure"
        data["q13"] = "Yes"
        data["q14"] = "Yes"
        scores = calculate_scores(data)

        assert "ro" in scores["low_visibility_sections"]
        # Score is 8.0 (2 Yes = 8 marks)
        assert scores["ro_score"] == 8.0

    def test_fixture_6_weighted_org_score_calc_010_to_014(self):
        """Validate multi-respondent org weighted scoring and CALC-014 reconciliation."""
        links = [
            {
                "id": "sub-1",
                "name": "Executive Leader",
                "email": "exec@sky11.com",
                "designation": "CPO",
                "weight": 2.0,
                "overall_avg": 16.0,
                "lc_score": 18, "ro_score": 16, "we_score": 16, "be_score": 16,
                "tm_score": 16, "ca_score": 16, "pc_score": 16, "sp_score": 14,
            },
            {
                "id": "sub-2",
                "name": "Staff Member",
                "email": "staff@sky11.com",
                "designation": "Engineer",
                "weight": 1.0,
                "overall_avg": 10.0,
                "lc_score": 12, "ro_score": 10, "we_score": 10, "be_score": 10,
                "tm_score": 10, "ca_score": 10, "pc_score": 10, "sp_score": 8,
            }
        ]
        org_result = calc_weighted_org_score(links)
        assert org_result is not None
        assert org_result["total_weight"] == 3.0
        assert org_result["respondent_count"] == 2

        # (16.0 * 2 + 10.0 * 1) / 3 = 42 / 3 = 14.0
        assert org_result["org_avg"] == 14.0
        assert org_result["org_level"] == "Level 2 — Early Progress"

        # Contributions: 2/3 = 66.7%, 1/3 = 33.3%
        assert org_result["respondents"][0]["weighted_contribution_pct"] == 66.7
        assert org_result["respondents"][1]["weighted_contribution_pct"] == 33.3

        # Section averages:
        # lc: (18*2 + 12*1)/3 = 48/3 = 16.0
        assert org_result["section_avgs"]["lc"] == 16.0
        assert org_result["section_levels"]["lc"] == "Level 3 — Developing"
        # sp: (14*2 + 8*1)/3 = 36/3 = 12.0
        assert org_result["section_avgs"]["sp"] == 12.0
        assert org_result["section_levels"]["sp"] == "Level 2 — Early Progress"

        # CALC-014 Reconciliation check:
        # Each pillar contributes 0.125
        sum_pillar_contribs = sum(org_result["section_avgs"][k] * 0.125 for k in org_result["section_avgs"])
        diff = org_result["org_avg"] - sum_pillar_contribs
        # When all pillars are present and identical, diff is 0
        assert abs(diff) < 0.001


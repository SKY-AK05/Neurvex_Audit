"""
test_scoring.py — Scoring logic tests
"""
from app.services.scoring_service import calculate_scores, get_maturity_level


def test_maturity_levels():
    assert get_maturity_level(0)  == "Level 1 — Foundational"
    assert get_maturity_level(6)  == "Level 1 — Foundational"
    assert get_maturity_level(7)  == "Level 2 — Early Progress"
    assert get_maturity_level(14) == "Level 2 — Early Progress"
    assert get_maturity_level(15) == "Level 3 — Developing"
    assert get_maturity_level(20) == "Level 3 — Developing"


def test_all_yes_scores_max():
    data = {f"q{i}": "Yes" for i in range(5, 45)}
    data.update({"name": "Test", "company_name": "Test Co", "email": "t@t.com"})
    result = calculate_scores(data)
    assert result["lc_score"] == 20
    assert result["overall_avg"] == 20.0
    assert result["overall_level"] == "Level 3 — Developing"


def test_all_no_scores_zero():
    data = {f"q{i}": "No" for i in range(5, 45)}
    data.update({"name": "Test", "company_name": "Test Co", "email": "t@t.com"})
    result = calculate_scores(data)
    assert result["lc_score"] == 0
    assert result["overall_avg"] == 0.0
    assert result["overall_level"] == "Level 1 — Foundational"

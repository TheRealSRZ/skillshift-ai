
from ai.skill_extractor import extract_skills


APPROVED_SKILLS = [
    {"id": "S01", "name": "Python"},
    {"id": "S02", "name": "SQL"},
    {"id": "S03", "name": "Power BI"},
]


def test_extracts_multiple_skills():
    text = "Looking for Python and SQL experience."
    result = extract_skills(text, APPROVED_SKILLS)

    ids = {item["skill_id"] for item in result}

    assert ids == {"S01", "S02"}


def test_ignores_unapproved_skills():
    text = "Python, JavaScript and SQL required."
    result = extract_skills(text, APPROVED_SKILLS)

    ids = {item["skill_id"] for item in result}

    assert ids == {"S01", "S02"}


def test_case_insensitive_matching():
    text = "Experience with PYTHON and sql."
    result = extract_skills(text, APPROVED_SKILLS)

    ids = {item["skill_id"] for item in result}

    assert ids == {"S01", "S02"}


def test_no_skills_found():
    text = "Excellent communication required."
    result = extract_skills(text, APPROVED_SKILLS)

    assert result == []

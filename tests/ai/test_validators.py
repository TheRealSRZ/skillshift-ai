
from ai.validators import filter_to_verified_course_ids


def test_rejects_invented_course_ids():
    resources = [
        {
            "id": "course_python",
            "url": "https://example.com/python",
            "verified": True
        }
    ]

    ai_output = ["course_python", "course_fake_123"]

    result = filter_to_verified_course_ids(ai_output, resources)

    assert result == ["course_python"]


def test_rejects_unverified_courses():
    resources = [
        {
            "id": "course_python",
            "url": "https://example.com/python",
            "verified": False
        }
    ]

    result = filter_to_verified_course_ids(
        ["course_python"], resources
    )

    assert result == []


def test_rejects_courses_without_urls():
    resources = [
        {
            "id": "course_python",
            "url": "",
            "verified": True
        }
    ]

    result = filter_to_verified_course_ids(
        ["course_python"], resources
    )

    assert result == []

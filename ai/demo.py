
from ai.learning_planner import generate_roadmap


def main():
    print("\n=== SkillShift AI: Learning Roadmap Demo ===")

    target_role = input("Enter target career: ")
    skills_input = input(
        "Enter missing skills (e.g. Python, SQL, Power BI): "
    )

    skill_names = {
        "python": "skill_python",
        "sql": "skill_sql",
        "power bi": "skill_power_bi",
    }

    missing_skills = [
        skill_names[name.strip().lower()]
        for name in skills_input.split(",")
        if name.strip().lower() in skill_names
    ]

    # Mock courses for local testing only.
    courses = [
        {
            "id": "demo_python",
            "title": "Python Basics (Demo)",
            "url": "https://example.com/python",
            "verified": True,
            "skill_ids": ["skill_python"],
            "estimated_hours": 10,
        },
        {
            "id": "demo_sql",
            "title": "SQL Basics (Demo)",
            "url": "https://example.com/sql",
            "verified": True,
            "skill_ids": ["skill_sql"],
            "estimated_hours": 8,
        },
        {
            "id": "demo_powerbi",
            "title": "Power BI Basics (Demo)",
            "url": "https://example.com/powerbi",
            "verified": True,
            "skill_ids": ["skill_power_bi"],
            "estimated_hours": 6,
        },
    ]

    result = generate_roadmap(
        target_role=target_role,
        missing_skills=missing_skills,
        scenario="moderate",
        verified_courses=courses,
        use_ai=False,
    )

    print("\n=== Your Learning Roadmap ===")
    print("Target career:", result["target_role"])
    print("Generation mode:", result["generation_mode"])

    for step in result["steps"]:
        print(f"\nStep {step['step']}: {step['title']}")
        print("Reason:", step["reason"])
        print("Estimated hours:", step["estimated_hours"])

    print("\nUncovered skills:", result["uncovered_skills"])


if __name__ == "__main__":
    main()


import json

from ai.learning_planner import generate_roadmap

with open("data/learning_resources.json", encoding="utf-8") as f:
    courses = json.load(f)

result = generate_roadmap(
    target_role="Data Analyst",
    missing_skills=["skill_power_bi", "skill_data_viz"],
    scenario="moderate",
    verified_courses=courses,
    use_ai=True,
)

print(json.dumps(result, indent=2))

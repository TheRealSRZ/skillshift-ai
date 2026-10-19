from fastapi import APIRouter
from backend.schemas import RoadmapRequest
from backend.store import load_json
from ai.learning_planner import generate_roadmap

router = APIRouter(prefix='/api')

@router.post('/roadmap')
def roadmap(body: RoadmapRequest):
    # AI deliberately disabled in starter; enable only when Member 3 validates it.
    return generate_roadmap(body.target_role, body.missing_skills,
                            body.scenario, load_json('learning_resources.json'),
                            use_ai=False)

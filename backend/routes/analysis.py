from fastapi import APIRouter, HTTPException
from backend.schemas import AnalyzeRequest
from backend.store import load_json
from backend.matching import match_roles

router = APIRouter(prefix='/api')

@router.post('/analyze')
def analyze(body: AnalyzeRequest):
    supported = {skill['id'] for skill in load_json('skills.json')}
    unknown = set(body.profile.skills) - supported
    if unknown:
        raise HTTPException(422, detail={'unknown_skill_ids': sorted(unknown)})
    return match_roles(body.profile.skills, load_json('careers.json'),
                       load_json('trends.json'), body.scenario)

@router.post('/scenarios')
def scenarios(body: AnalyzeRequest):
    # Reuse normal input validation and matching; no duplicate scoring code.
    return {'moderate': analyze(body.model_copy(update={'scenario':'moderate'})),
            'rapid': analyze(body.model_copy(update={'scenario':'rapid'}))}

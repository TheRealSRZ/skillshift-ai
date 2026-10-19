from fastapi import APIRouter
from backend.store import load_json

router = APIRouter(prefix='/api')

@router.get('/catalog')
def catalog():
    return {'skills': load_json('skills.json'), 'careers': load_json('careers.json')}

@router.get('/sdgs')
def sdgs():
    return {'mappings': load_json('sdg_mapping.json'),
            'note': 'Demo SDG rationale is illustrative and impact is not measured.'}

from fastapi import APIRouter
from backend.store import load_json

router = APIRouter(prefix='/api')

@router.get('/trends')
def trends():
    return load_json('trends.json')
